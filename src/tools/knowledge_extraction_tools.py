"""
Tools for the Knowledge Extraction Agent (Unstructured Data).

These tools execute entity and fact extraction from markdown files using
approved entity types and fact types, creating the subject graph in Neo4j.
"""
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from google.adk.tools import ToolContext

from src.utils.constants import (
    APPROVED_FILES,
    APPROVED_ENTITIES,
    APPROVED_FACTS,
    INGESTION_AUDIT_TRAIL
)
from src.utils.logger import logger
from src.utils.config import DEFAULT_MODEL
from src.tools.file_tools import get_data_directory
from src.neo4j.neo4j_for_adk import get_graphdb, tool_success, tool_error
from google.adk.models.lite_llm import LiteLlm


# Initialize LLM for extraction
try:
    extraction_llm = LiteLlm(model=DEFAULT_MODEL)
    logger.info(f"Initialized extraction LLM with model: {DEFAULT_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize extraction LLM: {e}")
    extraction_llm = None


def _extract_title_from_markdown(markdown_text: str) -> str:
    """
    Extract the title from markdown text (first h1 header).
    
    Args:
        markdown_text: The markdown content
        
    Returns:
        Title string or "Untitled" if not found
    """
    pattern = r'^# (.+)$'
    match = re.search(pattern, markdown_text, re.MULTILINE)
    return match.group(1) if match else "Untitled"


def _chunk_markdown_by_separator(text: str, separator: str = "---") -> List[Dict[str, Any]]:
    """
    Chunk markdown text by separator (e.g., "---").
    If no separator found, treat entire file as one chunk.
    
    Args:
        text: The markdown content
        separator: Separator string to split on
        
    Returns:
        List of chunks with text and metadata
    """
    chunks = []
    
    # Check if separator exists in text
    if separator not in text:
        # No separator found - treat entire file as one chunk
        logger.info(f"No separator '{separator}' found in text. Treating entire file as one chunk.")
        if text.strip():
            chunks.append({
                "chunk_id": "chunk_0",
                "text": text.strip(),
                "chunk_index": 0
            })
        return chunks
    
    # Split by separator
    parts = text.split(separator)
    
    for idx, part in enumerate(parts):
        part = part.strip()
        if part:  # Skip empty chunks
            chunks.append({
                "chunk_id": f"chunk_{idx}",
                "text": part,
                "chunk_index": idx
            })
    
    return chunks


def _create_extraction_schema(
    approved_entities: List[str],
    approved_facts: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """
    Create entity extraction schema from approved entities and facts.
    
    Args:
        approved_entities: List of approved entity type labels
        approved_facts: Dictionary of approved fact types
        
    Returns:
        Schema dictionary for LLM extraction
    """
    # Extract relationship types from fact types (predicate labels)
    relationship_types = [fact["predicate_label"].upper() for fact in approved_facts.values()]
    
    # Create relationship patterns (subject-predicate-object)
    patterns = [
        [fact["subject_label"], fact["predicate_label"].upper(), fact["object_label"]]
        for fact in approved_facts.values()
    ]
    
    return {
        "node_types": approved_entities,
        "relationship_types": relationship_types,
        "patterns": patterns
    }


def _create_extraction_prompt(
    context: str,
    schema: Dict[str, Any],
    chunk_text: str
) -> str:
    """
    Create contextualized prompt for entity and relationship extraction.
    
    Args:
        context: File context (first few lines)
        schema: Entity extraction schema
        chunk_text: The text chunk to extract from
        
    Returns:
        Formatted prompt string
    """
    general_instructions = """
You are a top-tier algorithm designed for extracting
information in structured formats to build a knowledge graph.

Extract the entities (nodes) and specify their type from the following text.
Also extract the relationships between these nodes.

Return result as JSON using the following format:
{{"nodes": [ {{"id": "0", "label": "Person", "properties": {{"name": "John"}}}} ],
"relationships": [{{"type": "KNOWS", "start_node_id": "0", "end_node_id": "1", "properties": {{"since": "2024-08-01"}}}} ]}}

Use only the following node and relationship types (if provided):
{schema}

Assign a unique ID (string) to each node, and reuse it to define relationships.
Do respect the source and target node types for relationship and
the relationship direction.

Make sure you adhere to the following rules to produce valid JSON objects:
- Do not return any additional information other than the JSON in it.
- Omit any backticks around the JSON - simply output the JSON on its own.
- The JSON object must not wrapped into a list - it is its own JSON object.
- Property names must be enclosed in double quotes
"""
    
    context_section = f"""
Consider the following context to help identify entities and relationships:
<context>
{context}
</context>
"""
    
    input_section = f"""
Input text:

{chunk_text}
"""
    
    schema_str = json.dumps(schema, indent=2)
    
    return general_instructions.format(schema=schema_str) + "\n" + context_section + "\n" + input_section


def _extract_entities_and_relationships(
    chunk_text: str,
    context: str,
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract entities and relationships from a text chunk using LLM.
    
    Args:
        chunk_text: The text chunk to extract from
        context: File context for better extraction
        schema: Entity extraction schema
        
    Returns:
        Dictionary with nodes and relationships, or error
    """
    if extraction_llm is None:
        return {"error": "Extraction LLM not available"}
    
    try:
        prompt = _create_extraction_prompt(context, schema, chunk_text)
        
        # Call LLM for extraction (synchronous)
        response = extraction_llm.llm_client.completion(
            model=extraction_llm.model,
            messages=[{"role": "user", "content": prompt}],
            tools=[]
        )
        
        # Parse JSON response
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        # Validate result structure
        if "nodes" not in result:
            result["nodes"] = []
        if "relationships" not in result:
            result["relationships"] = []
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        if 'content' in locals():
            logger.error(f"Response content (first 1000 chars): {content[:1000]}")
        return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": content if 'content' in locals() else None}
    except Exception as e:
        logger.error(f"Error during entity extraction: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e)}


def _file_context(file_path: Path, num_lines: int = 5) -> str:
    """
    Extract the first few lines of a file for context.
    
    Args:
        file_path: Path to the file
        num_lines: Number of lines to extract
        
    Returns:
        Context string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = []
            for _ in range(num_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Could not read file context: {e}")
        return ""


def get_approved_files(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the list of approved markdown files for knowledge extraction.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and approved_files
    """
    approved_files = tool_context.state.get(APPROVED_FILES, [])
    
    if not approved_files:
        return tool_error(
            "No approved files found. "
            "Please ensure the file suggestion agent has been run and files approved."
        )
    
    return tool_success(APPROVED_FILES, approved_files)


def get_approved_entities(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved entity types for extraction.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and approved_entities
    """
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    
    if not approved_entities:
        return tool_error(
            "No approved entity types found. "
            "Please ensure the NER agent has been run and entities approved."
        )
    
    return tool_success(APPROVED_ENTITIES, approved_entities)


def get_approved_facts(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved fact types for extraction.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and approved_facts
    """
    approved_facts = tool_context.state.get(APPROVED_FACTS, {})
    
    if not approved_facts:
        return tool_error(
            "No approved fact types found. "
            "Please ensure the fact extraction agent has been run and facts approved."
        )
    
    return tool_success(APPROVED_FACTS, approved_facts)


def check_neo4j_connection(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Check if Neo4j connection is available and working.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and connection info
    """
    try:
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error(
                "Neo4j connection not available. "
                "Please ensure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set."
            )
        
        # Test connection with a simple query
        result = graphdb.send_query("RETURN 'Neo4j is ready!' as message")
        
        if result["status"] == "error":
            return tool_error(f"Neo4j connection test failed: {result.get('error_message', 'Unknown error')}")
        
        return tool_success("connection_status", {
            "message": "Neo4j connection is ready",
            "database": graphdb.database_name
        })
    except Exception as e:
        return tool_error(f"Error checking Neo4j connection: {str(e)}")


def _process_markdown_file(
    file_path: Path,
    approved_entities: List[str],
    approved_facts: Dict[str, Dict[str, str]],
    graphdb: Any
) -> Dict[str, Any]:
    """
    Process a single markdown file: chunk, extract, and load into Neo4j.
    
    Args:
        file_path: Path to markdown file
        approved_entities: List of approved entity types
        approved_facts: Dictionary of approved fact types
        graphdb: Neo4j connection
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # Extract title
        title = _extract_title_from_markdown(markdown_text)
        
        # Get file context
        context = _file_context(file_path, num_lines=5)
        
        # Create extraction schema
        schema = _create_extraction_schema(approved_entities, approved_facts)
        
        # Chunk the markdown
        chunks = _chunk_markdown_by_separator(markdown_text, separator="---")
        
        logger.info(f"Processing {file_path.name}: {len(chunks)} chunks, title: {title}")
        
        # Create Document node
        escaped_path = str(file_path).replace("'", "''")
        escaped_title = title.replace("'", "''")
        escaped_filename = file_path.name.replace("'", "''")
        
        doc_query = f"""
        MERGE (d:Document {{path: '{escaped_path}'}})
        SET d.title = '{escaped_title}',
            d.source_file = '{escaped_filename}'
        RETURN id(d) as doc_id
        """
        doc_result = graphdb.send_query(doc_query)
        
        if doc_result["status"] == "error":
            return {"error": f"Failed to create Document node: {doc_result.get('error_message')}"}
        
        doc_id = doc_result.get("query_result", [{}])[0].get("doc_id")
        
        # Process each chunk
        total_nodes = 0
        total_relationships = 0
        chunk_results = []
        
        for chunk in chunks:
            # Extract entities and relationships from chunk
            logger.info(f"Extracting from chunk {chunk['chunk_id']} (length: {len(chunk['text'])} chars)")
            extraction_result = _extract_entities_and_relationships(
                chunk["text"],
                context,
                schema
            )
            
            if "error" in extraction_result:
                logger.warning(f"Extraction error in chunk {chunk['chunk_id']}: {extraction_result['error']}")
                chunk_results.append({
                    "chunk_id": chunk["chunk_id"],
                    "error": extraction_result["error"],
                    "nodes_extracted": 0,
                    "relationships_extracted": 0
                })
                continue
            
            nodes = extraction_result.get("nodes", [])
            relationships = extraction_result.get("relationships", [])
            
            logger.info(f"Extracted {len(nodes)} nodes and {len(relationships)} relationships from chunk {chunk['chunk_id']}")
            
            # Create Chunk node
            escaped_chunk_text = chunk["text"][:1000].replace("'", "''")
            escaped_chunk_id = chunk["chunk_id"].replace("'", "''")
            escaped_doc_path = str(file_path).replace("'", "''")
            
            chunk_query = f"""
            MATCH (d:Document {{path: '{escaped_doc_path}'}})
            MERGE (c:Chunk {{chunk_id: '{escaped_chunk_id}', document_path: '{escaped_doc_path}'}})
            SET c.text = '{escaped_chunk_text}',
                c.chunk_index = {chunk["chunk_index"]}
            MERGE (d)-[:HAS_CHUNK]->(c)
            RETURN id(c) as chunk_id
            """
            
            chunk_result = graphdb.send_query(chunk_query)
            
            if chunk_result["status"] == "error":
                logger.warning(f"Failed to create Chunk node: {chunk_result.get('error_message')}")
                chunk_results.append({
                    "chunk_id": chunk["chunk_id"],
                    "error": f"Failed to create Chunk: {chunk_result.get('error_message')}",
                    "nodes_extracted": len(nodes),
                    "relationships_extracted": len(relationships)
                })
                continue
            
            chunk_node_id = chunk_result.get("query_result", [{}])[0].get("chunk_id")
            
            # Create entity nodes and link to chunk
            node_id_map = {}  # Map extraction IDs to Neo4j node IDs
            
            for node_data in nodes:
                node_id = node_data.get("id")
                label = node_data.get("label")
                properties = node_data.get("properties", {})
                
                if not label or label not in approved_entities:
                    logger.debug(f"Skipping node with label '{label}' - not in approved entities")
                    continue
                
                if not properties:
                    logger.debug(f"Skipping node {node_id} - no properties")
                    continue
                
                # Use first property as unique identifier for MERGE
                prop_keys = list(properties.keys())
                first_key = prop_keys[0]
                first_value = properties[first_key]
                
                # Build SET clause for additional properties
                set_clauses = []
                for key, value in properties.items():
                    if key == first_key:
                        continue  # Already in MERGE
                    # Escape single quotes in values
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        set_clauses.append(f"n.`{key}` = '{escaped_value}'")
                    elif isinstance(value, (int, float, bool)):
                        set_clauses.append(f"n.`{key}` = {value}")
                    else:
                        set_clauses.append(f"n.`{key}` = {json.dumps(value)}")
                
                # Escape first value for MERGE
                if isinstance(first_value, str):
                    escaped_first = first_value.replace("'", "''")
                    merge_value = f"'{escaped_first}'"
                elif isinstance(first_value, (int, float, bool)):
                    merge_value = str(first_value)
                else:
                    merge_value = json.dumps(first_value)
                
                set_clause = ""
                if set_clauses:
                    set_clause = "\n            SET " + ", ".join(set_clauses)
                
                escaped_chunk_id = chunk["chunk_id"].replace("'", "''")
                escaped_doc_path = str(file_path).replace("'", "''")
                
                create_node_query = f"""
                MERGE (n:`{label}` {{`{first_key}`: {merge_value}}}){set_clause}
                WITH n
                MATCH (c:Chunk {{chunk_id: '{escaped_chunk_id}', document_path: '{escaped_doc_path}'}})
                MERGE (n)-[:EXTRACTED_FROM]->(c)
                RETURN id(n) as node_id
                """
                
                node_result = graphdb.send_query(create_node_query)
                
                if node_result["status"] == "success":
                    result_data = node_result.get("query_result", [])
                    if result_data:
                        neo4j_node_id = result_data[0].get("node_id")
                        node_id_map[node_id] = neo4j_node_id
                        total_nodes += 1
                        logger.debug(f"Created node: {label} with id {neo4j_node_id}")
                else:
                    logger.warning(f"Failed to create node {label}: {node_result.get('error_message', 'Unknown error')}")
            
            # Create relationships
            for rel_data in relationships:
                rel_type = rel_data.get("type")
                start_id = rel_data.get("start_node_id")
                end_id = rel_data.get("end_node_id")
                properties = rel_data.get("properties", {})
                
                if start_id not in node_id_map or end_id not in node_id_map:
                    logger.debug(f"Skipping relationship {rel_type}: start_id={start_id}, end_id={end_id} not in node_id_map")
                    continue
                
                start_neo4j_id = node_id_map[start_id]
                end_neo4j_id = node_id_map[end_id]
                
                # Create relationship
                set_clauses = []
                for key, value in properties.items():
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        set_clauses.append(f"r.`{key}` = '{escaped_value}'")
                    elif isinstance(value, (int, float, bool)):
                        set_clauses.append(f"r.`{key}` = {value}")
                    else:
                        set_clauses.append(f"r.`{key}` = {json.dumps(value)}")
                
                set_clause = ""
                if set_clauses:
                    set_clause = "\n            SET " + ", ".join(set_clauses)
                
                create_rel_query = f"""
                MATCH (start) WHERE id(start) = {start_neo4j_id}
                MATCH (end) WHERE id(end) = {end_neo4j_id}
                MERGE (start)-[r:`{rel_type}`]->(end){set_clause}
                RETURN id(r) as rel_id
                """
                
                rel_result = graphdb.send_query(create_rel_query)
                
                if rel_result["status"] == "success":
                    total_relationships += 1
                    logger.debug(f"Created relationship: {rel_type}")
                else:
                    logger.warning(f"Failed to create relationship {rel_type}: {rel_result.get('error_message', 'Unknown error')}")
            
            chunk_results.append({
                "chunk_id": chunk["chunk_id"],
                "nodes_extracted": len(nodes),
                "nodes_created": len(node_id_map),
                "relationships_extracted": len(relationships),
                "relationships_created": total_relationships - sum(c.get("relationships_created", 0) for c in chunk_results)
            })
        
        return {
            "file": file_path.name,
            "title": title,
            "chunks_processed": len(chunks),
            "nodes_created": total_nodes,
            "relationships_created": total_relationships,
            "chunk_results": chunk_results
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e), "file": file_path.name}


def process_single_file(
    file_name: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Process a single markdown file for knowledge extraction.
    
    This tool processes one file at a time, which helps with debugging
    and provides better error reporting.
    
    Args:
        file_name: Name of the markdown file to process
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and processing results
    """
    try:
        # 1. Get prerequisites
        approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
        if not approved_entities:
            return tool_error(
                "No approved entity types found. "
                "Please ensure the NER agent has been run and entities approved."
            )
        
        approved_facts = tool_context.state.get(APPROVED_FACTS, {})
        if not approved_facts:
            return tool_error(
                "No approved fact types found. "
                "Please ensure the fact extraction agent has been run and facts approved."
            )
        
        # 2. Check Neo4j connection
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error(
                "Neo4j connection not available. "
                "Please ensure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set."
            )
        
        # Test connection
        test_result = graphdb.send_query("RETURN 'Neo4j is ready!' as message")
        if test_result["status"] == "error":
            return tool_error(f"Neo4j connection test failed: {test_result.get('error_message', 'Unknown error')}")
        
        # 3. Get data directory
        data_dir = get_data_directory()
        file_path = data_dir / file_name
        
        if not file_path.exists():
            return tool_error(f"File not found: {file_name} (looked in {data_dir})")
        
        # 4. Process file
        logger.info(f"Processing single file: {file_name}")
        file_result = _process_markdown_file(
            file_path,
            approved_entities,
            approved_facts,
            graphdb
        )
        
        if "error" in file_result:
            return tool_error(f"Error processing {file_name}: {file_result['error']}")
        
        # 5. Track in audit trail
        audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
        audit_trail.append({
            "action": "knowledge_extraction_single",
            "file": file_name,
            "result": file_result
        })
        tool_context.state[INGESTION_AUDIT_TRAIL] = audit_trail
        
        logger.info(
            f"File {file_name} processed: "
            f"{file_result.get('nodes_created', 0)} nodes, "
            f"{file_result.get('relationships_created', 0)} relationships extracted"
        )
        
        return tool_success("extraction_result", {
            "status": "completed",
            "file": file_name,
            "result": file_result
        })
        
    except Exception as e:
        logger.error(f"Error processing single file: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return tool_error(f"Error processing single file: {str(e)}")


def execute_knowledge_extraction(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Execute knowledge extraction from all approved markdown files in one batch operation.
    
    This tool reduces API calls by processing all files in one go:
    1. Gets approved files, entities, and facts
    2. Processes each markdown file
    3. Chunks content
    4. Extracts entities and relationships using LLM
    5. Creates nodes and relationships in Neo4j
    6. Links to source chunks for provenance
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and comprehensive extraction results
    """
    try:
        # 1. Get prerequisites
        approved_files = tool_context.state.get(APPROVED_FILES, [])
        if not approved_files:
            return tool_error(
                "No approved files found. "
                "Please ensure the file suggestion agent has been run and files approved."
            )
        
        approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
        if not approved_entities:
            return tool_error(
                "No approved entity types found. "
                "Please ensure the NER agent has been run and entities approved."
            )
        
        approved_facts = tool_context.state.get(APPROVED_FACTS, {})
        if not approved_facts:
            return tool_error(
                "No approved fact types found. "
                "Please ensure the fact extraction agent has been run and facts approved."
            )
        
        # 2. Check Neo4j connection
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error(
                "Neo4j connection not available. "
                "Please ensure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set."
            )
        
        # Test connection
        test_result = graphdb.send_query("RETURN 'Neo4j is ready!' as message")
        if test_result["status"] == "error":
            return tool_error(f"Neo4j connection test failed: {test_result.get('error_message', 'Unknown error')}")
        
        # 3. Get data directory
        data_dir = get_data_directory()
        
        # 4. Process all files
        results = {
            "files_processed": [],
            "files_failed": [],
            "total_nodes": 0,
            "total_relationships": 0,
            "total_chunks": 0
        }
        
        logger.info(f"Processing {len(approved_files)} markdown files...")
        
        # Process files sequentially (can be parallelized later)
        for file_name in approved_files:
            file_path = data_dir / file_name
            
            if not file_path.exists():
                results["files_failed"].append({
                    "file": file_name,
                    "error": "File not found"
                })
                continue
            
            # Process file
            file_result = _process_markdown_file(
                file_path,
                approved_entities,
                approved_facts,
                graphdb
            )
            
            if "error" in file_result:
                results["files_failed"].append(file_result)
            else:
                results["files_processed"].append(file_result)
                results["total_nodes"] += file_result.get("nodes_created", 0)
                results["total_relationships"] += file_result.get("relationships_created", 0)
                results["total_chunks"] += file_result.get("chunks_processed", 0)
        
        # 5. Track in audit trail
        audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
        audit_trail.append({
            "action": "knowledge_extraction",
            "files_processed": len(results["files_processed"]),
            "files_failed": len(results["files_failed"]),
            "total_nodes": results["total_nodes"],
            "total_relationships": results["total_relationships"],
            "total_chunks": results["total_chunks"],
            "details": results
        })
        tool_context.state[INGESTION_AUDIT_TRAIL] = audit_trail
        
        # 6. Compile summary
        summary = {
            "status": "completed",
            "files": {
                "processed": len(results["files_processed"]),
                "failed": len(results["files_failed"])
            },
            "extraction": {
                "total_nodes": results["total_nodes"],
                "total_relationships": results["total_relationships"],
                "total_chunks": results["total_chunks"]
            },
            "details": results
        }
        
        logger.info(
            f"Knowledge extraction complete: "
            f"{results['total_nodes']} nodes, {results['total_relationships']} relationships extracted"
        )
        
        return tool_success("extraction_result", summary)
        
    except Exception as e:
        logger.error(f"Error executing knowledge extraction: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return tool_error(f"Error executing knowledge extraction: {str(e)}")


def get_extraction_progress(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the current knowledge extraction progress.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and extraction progress
    """
    audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
    
    extraction_actions = [a for a in audit_trail if a.get("action") in ["knowledge_extraction", "knowledge_extraction_single"]]
    
    return tool_success("extraction_progress", {
        "total_actions": len(extraction_actions),
        "extraction_trail": extraction_actions
    })
