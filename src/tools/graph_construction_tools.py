"""
Tools for the Graph Construction Agent.

These tools execute the approved construction plan to build the knowledge graph
in Neo4j from structured CSV files.
"""
import csv
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path

from google.adk.tools import ToolContext

from src.utils.constants import (
    APPROVED_CONSTRUCTION_PLAN,
    PRE_INGESTION_AUDIT_QUERIES,
    AUDIT_RESOLUTIONS,
    INGESTION_AUDIT_TRAIL
)
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import get_graphdb, tool_success, tool_error


def _parse_resolutions_for_file(
    source_file: str,
    unique_column_name: str,
    tool_context: ToolContext
) -> Tuple[Set[str], Set[str], Set[str], Dict[str, Dict[str, Any]]]:
    """
    Parse audit resolutions for a specific file and extract filtering rules.
    
    Args:
        source_file: The CSV file being loaded
        unique_column_name: The unique identifier column name
        tool_context: ADK ToolContext
    
    Returns:
        Tuple of:
        - skip_values: Set of unique column values to skip entirely
        - use_first_values: Set of unique column values where only first occurrence should be used
        - use_second_values: Set of unique column values where only second occurrence should be used
        - merge_instructions: Dict mapping unique values to merge data from both occurrences
    """
    resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
    audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
    
    skip_values = set()
    use_first_values = set()
    use_second_values = set()
    merge_instructions = {}
    
    # Filter resolutions for this file
    for query_id, resolution_data in resolutions.items():
        query = audit_queries.get(query_id, {})
        evidence = query.get("evidence", {})
        
        # Check if this resolution applies to this file
        if evidence.get("file") != source_file:
            continue
        
        resolution = resolution_data.get("resolution")
        category = query.get("category", "")
        
        # Handle duplicate_unique_identifier resolutions
        if category == "duplicate_unique_identifier":
            # Extract duplicate value - try multiple possible keys
            duplicate_value = (
                evidence.get("duplicate_value") or 
                evidence.get("Duplicate Value") or
                evidence.get("column")  # Sometimes stored here
            )
            
            # Extract occurrence data - evidence keys may vary
            first_occurrence = None
            second_occurrence = None
            
            # Look for keys containing "First" and "Second"
            for key, value in evidence.items():
                if "First" in key or "first" in key.lower():
                    first_occurrence = value
                elif "Second" in key or "second" in key.lower():
                    second_occurrence = value
            
            # Extract row data from occurrences
            first_row_data = {}
            second_row_data = {}
            
            if isinstance(first_occurrence, dict):
                first_row_data = first_occurrence.get("data", first_occurrence)
            elif first_occurrence:
                first_row_data = first_occurrence
            
            if isinstance(second_occurrence, dict):
                second_row_data = second_occurrence.get("data", second_occurrence)
            elif second_occurrence:
                second_row_data = second_occurrence
            
            # Apply resolution
            if duplicate_value:
                duplicate_value_str = str(duplicate_value)
                
                if resolution == "skip_record":
                    # Skip both occurrences
                    skip_values.add(duplicate_value_str)
                elif resolution == "use_first":
                    # Only use first occurrence - skip second
                    use_first_values.add(duplicate_value_str)
                elif resolution == "use_second":
                    # Only use second occurrence - skip first
                    use_second_values.add(duplicate_value_str)
                elif resolution in ["merge_data", "merge"]:
                    # Merge both rows - store merge instructions
                    merge_instructions[duplicate_value_str] = {
                        "first": first_row_data,
                        "second": second_row_data
                    }
        
        # Handle missing_required_field resolutions
        elif category == "missing_required_field":
            # Extract row data - may be in various formats
            row_data = evidence.get("row_data", {})
            if not row_data:
                # Try to find row data in evidence directly
                for key, value in evidence.items():
                    if isinstance(value, dict) and unique_column_name in value:
                        row_data = value
                        break
            
            if resolution == "skip_record":
                # Skip this specific row - identify by unique column value
                unique_value = row_data.get(unique_column_name)
                if unique_value:
                    skip_values.add(str(unique_value))
        
        # Handle invalid_foreign_key resolutions
        elif category == "invalid_foreign_key":
            row_data = evidence.get("row_data", {})
            if not row_data:
                for key, value in evidence.items():
                    if isinstance(value, dict) and unique_column_name in value:
                        row_data = value
                        break
            
            if resolution == "skip_record":
                # Skip this specific row
                unique_value = row_data.get(unique_column_name)
                if unique_value:
                    skip_values.add(str(unique_value))
    
    logger.info(
        f"Parsed resolutions for {source_file}: "
        f"skip={len(skip_values)}, use_first={len(use_first_values)}, "
        f"use_second={len(use_second_values)}, merge={len(merge_instructions)}"
    )
    
    return skip_values, use_first_values, use_second_values, merge_instructions


def get_approved_construction_plan(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved construction plan from session state.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and approved_construction_plan
    """
    construction_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    
    if not construction_plan:
        return tool_error(
            "Approved construction plan not found. "
            "Please ensure the schema proposal agent has been run and approved."
        )
    
    return tool_success(APPROVED_CONSTRUCTION_PLAN, construction_plan)


def get_pre_ingestion_audit_resolutions(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get all pre-ingestion audit resolutions to apply during ingestion.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and audit_resolutions
    """
    resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
    return tool_success("audit_resolutions", resolutions)


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


def create_uniqueness_constraint(
    label: str,
    unique_property_key: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Create a uniqueness constraint for a node label and property key.
    
    Args:
        label: The label of the node
        unique_property_key: The property key that should be unique
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and constraint info
    """
    try:
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error("Neo4j connection not available")
        
        # Use string formatting since Neo4j doesn't support parameterization of labels/property keys
        constraint_name = f"{label}_{unique_property_key}_constraint"
        query = f"""CREATE CONSTRAINT `{constraint_name}` IF NOT EXISTS
        FOR (n:`{label}`)
        REQUIRE n.`{unique_property_key}` IS UNIQUE"""
        
        result = graphdb.send_query(query)
        
        if result["status"] == "error":
            return tool_error(f"Failed to create constraint: {result.get('error_message', 'Unknown error')}")
        
        logger.info(f"Created uniqueness constraint: {constraint_name} for {label}.{unique_property_key}")
        
        return tool_success("constraint", {
            "constraint_name": constraint_name,
            "label": label,
            "property_key": unique_property_key
        })
    except Exception as e:
        return tool_error(f"Error creating uniqueness constraint: {str(e)}")


def get_neo4j_import_directory(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the Neo4j import directory where CSV files should be placed.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and import directory path
    """
    try:
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error("Neo4j connection not available")
        
        result = graphdb.get_import_directory()
        return result
    except Exception as e:
        return tool_error(f"Error getting Neo4j import directory: {str(e)}")


def load_nodes_from_csv(
    source_file: str,
    label: str,
    unique_column_name: str,
    properties: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Load nodes from a CSV file into Neo4j.
    
    Uses LOAD CSV WITH HEADERS and MERGE to create/update nodes based on
    the unique_column_name. Handles pre-ingestion audit resolutions.
    
    Args:
        source_file: Path to CSV file (relative to Neo4j import directory)
        label: Node label to create
        unique_column_name: Column name used for unique identification
        properties: List of property names to import from CSV
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and loading results
    """
    try:
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error("Neo4j connection not available")
        
        # Parse resolutions for this file
        skip_values, use_first_values, use_second_values, merge_instructions = _parse_resolutions_for_file(
            source_file, unique_column_name, tool_context
        )
        
        # Get audit queries and resolutions to extract row identification data for use_first/use_second
        audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
        resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
        
        # Build WHERE clause conditions based on resolutions
        where_conditions = []
        
        # Skip values entirely
        if skip_values:
            skip_list = ", ".join([f"'{v.replace(chr(39), chr(39)+chr(39))}'" for v in skip_values])  # Escape single quotes
            where_conditions.append(f"NOT row.`{unique_column_name}` IN [{skip_list}]")
        
        # For use_first/use_second, identify specific rows to keep based on row data
        keep_conditions = []  # Conditions for rows we want to keep
        
        for query_id, resolution_data in resolutions.items():
            query = audit_queries.get(query_id, {})
            evidence = query.get("evidence", {})
            
            if evidence.get("file") != source_file:
                continue
            
            if query.get("category") != "duplicate_unique_identifier":
                continue
            
            resolution = resolution_data.get("resolution")
            duplicate_value = evidence.get("duplicate_value") or evidence.get("Duplicate Value")
            
            if not duplicate_value or str(duplicate_value) not in use_first_values and str(duplicate_value) not in use_second_values:
                continue
            
            # Find first and second occurrence data
            first_data = {}
            second_data = {}
            for key, value in evidence.items():
                if "First" in key or ("first" in key.lower() and "occurrence" in key.lower()):
                    if isinstance(value, dict):
                        first_data = value.get("data", value)
                    else:
                        first_data = value if isinstance(value, dict) else {}
                elif "Second" in key or ("second" in key.lower() and "occurrence" in key.lower()):
                    if isinstance(value, dict):
                        second_data = value.get("data", value)
                    else:
                        second_data = value if isinstance(value, dict) else {}
            
            # Build condition to identify which row to keep
            if resolution == "use_first" and first_data:
                # Keep rows matching first occurrence's data
                row_conditions = []
                for prop, val in first_data.items():
                    if prop in properties and val:
                        # Escape single quotes in value
                        escaped_val = str(val).replace("'", "''")
                        row_conditions.append(f"row.`{prop}` = '{escaped_val}'")
                if row_conditions:
                    keep_conditions.append("(" + " AND ".join(row_conditions) + ")")
            
            elif resolution == "use_second" and second_data:
                # Keep rows matching second occurrence's data
                row_conditions = []
                for prop, val in second_data.items():
                    if prop in properties and val:
                        escaped_val = str(val).replace("'", "''")
                        row_conditions.append(f"row.`{prop}` = '{escaped_val}'")
                if row_conditions:
                    keep_conditions.append("(" + " AND ".join(row_conditions) + ")")
        
        # Build the LOAD CSV query
        query = f"""LOAD CSV WITH HEADERS FROM "file:///{source_file}" AS row"""
        
        # Add WHERE clause if we have conditions
        if where_conditions or keep_conditions:
            query += "\n        WHERE "
            conditions = []
            if where_conditions:
                conditions.extend(where_conditions)
            if keep_conditions:
                # For use_first/use_second: keep rows matching keep conditions OR rows not in duplicate values
                duplicate_values = use_first_values.union(use_second_values)
                if duplicate_values:
                    dup_list = ", ".join([f"'{v.replace(chr(39), chr(39)+chr(39))}'" for v in duplicate_values])
                    conditions.append(f"({' OR '.join(keep_conditions)} OR NOT row.`{unique_column_name}` IN [{dup_list}])")
                else:
                    conditions.extend(keep_conditions)
            
            query += " AND ".join(conditions)
        
        query += f"""
        CALL (row) {{
            MERGE (n:`{label}` {{ `{unique_column_name}`: row.`{unique_column_name}` }})"""
        
        # Handle merge instructions - combine properties from both occurrences
        if merge_instructions:
            # For merge, use COALESCE to prefer non-null values (allows merging from multiple rows)
            property_assignments = []
            for prop in properties:
                if prop != unique_column_name:
                    property_assignments.append(f"n.`{prop}` = COALESCE(row.`{prop}`, n.`{prop}`)")
            
            if property_assignments:
                query += "\n            SET " + ", ".join(property_assignments)
        else:
            # Normal property assignments
            property_assignments = []
            for prop in properties:
                if prop != unique_column_name:  # Already set in MERGE
                    property_assignments.append(f"n.`{prop}` = row.`{prop}`")
            
            if property_assignments:
                query += "\n            SET " + ", ".join(property_assignments)
        
        query += """
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(*) as nodes_loaded
        """
        
        result = graphdb.send_query(query)
        
        if result["status"] == "error":
            return tool_error(f"Failed to load nodes: {result.get('error_message', 'Unknown error')}")
        
        nodes_loaded = result.get("query_result", [{}])[0].get("nodes_loaded", 0)
        
        # Track in audit trail
        audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
        total_resolutions = len(skip_values) + len(use_first_values) + len(use_second_values) + len(merge_instructions)
        
        audit_trail.append({
            "action": "load_nodes",
            "file": source_file,
            "label": label,
            "nodes_loaded": nodes_loaded,
            "resolutions_applied": total_resolutions,
            "resolution_details": {
                "skipped": len(skip_values),
                "use_first": len(use_first_values),
                "use_second": len(use_second_values),
                "merged": len(merge_instructions)
            }
        })
        tool_context.state[INGESTION_AUDIT_TRAIL] = audit_trail
        
        logger.info(
            f"Loaded {nodes_loaded} nodes from {source_file} with label {label}. "
            f"Applied {total_resolutions} resolutions: "
            f"skip={len(skip_values)}, use_first={len(use_first_values)}, "
            f"use_second={len(use_second_values)}, merge={len(merge_instructions)}"
        )
        
        return tool_success("loading_result", {
            "file": source_file,
            "label": label,
            "nodes_loaded": nodes_loaded,
            "resolutions_applied": total_resolutions,
            "resolution_details": {
                "skipped": len(skip_values),
                "use_first": len(use_first_values),
                "use_second": len(use_second_values),
                "merged": len(merge_instructions)
            }
        })
    except Exception as e:
        return tool_error(f"Error loading nodes from CSV: {str(e)}")


def load_relationships_from_csv(
    source_file: str,
    relationship_type: str,
    from_node_label: str,
    from_node_column: str,
    to_node_label: str,
    to_node_column: str,
    properties: Optional[List[str]],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Load relationships from a CSV file into Neo4j.
    
    Applies pre-ingestion audit resolutions to skip problematic relationship rows.
    
    Args:
        source_file: Path to CSV file (relative to Neo4j import directory)
        relationship_type: Type of relationship to create
        from_node_label: Label of source node
        from_node_column: Column name for source node identifier
        to_node_label: Label of target node
        to_node_column: Column name for target node identifier
        properties: Optional list of relationship properties to import
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and loading results
    """
    try:
        graphdb = get_graphdb()
        if graphdb is None:
            return tool_error("Neo4j connection not available")
        
        # Get audit resolutions for this file (relationships can have skip_record resolutions)
        audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
        resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
        
        # Find rows to skip based on resolutions
        skip_conditions = []
        for query_id, resolution_data in resolutions.items():
            query = audit_queries.get(query_id, {})
            evidence = query.get("evidence", {})
            
            if evidence.get("file") != source_file:
                continue
            
            resolution = resolution_data.get("resolution")
            if resolution == "skip_record":
                # Extract row data to identify which relationship to skip
                row_data = evidence.get("row_data", {})
                if row_data:
                    # Build condition to identify this specific row
                    row_conditions = []
                    if from_node_column in row_data:
                        val = str(row_data[from_node_column]).replace("'", "''")
                        row_conditions.append(f"row.`{from_node_column}` = '{val}'")
                    if to_node_column in row_data:
                        val = str(row_data[to_node_column]).replace("'", "''")
                        row_conditions.append(f"row.`{to_node_column}` = '{val}'")
                    
                    if row_conditions:
                        # Skip this row
                        skip_conditions.append("NOT (" + " AND ".join(row_conditions) + ")")
        
        # Build the LOAD CSV query for relationships
        query = f"""LOAD CSV WITH HEADERS FROM "file:///{source_file}" AS row"""
        
        # Add WHERE clause to skip problematic rows
        if skip_conditions:
            query += "\n        WHERE " + " AND ".join(skip_conditions)
        
        query += f"""
        CALL (row) {{
            MATCH (from:`{from_node_label}` {{ `{from_node_column}`: row.`{from_node_column}` }})
            MATCH (to:`{to_node_label}` {{ `{to_node_column}`: row.`{to_node_column}` }})
            MERGE (from)-[r:`{relationship_type}`]->(to)"""
        
        # Add properties if specified
        if properties:
            property_assignments = [f"r.`{prop}` = row.`{prop}`" for prop in properties]
            query += "\n            SET " + ", ".join(property_assignments)
        
        query += """
        } IN TRANSACTIONS OF 1000 ROWS
        RETURN count(*) as relationships_loaded
        """
        
        result = graphdb.send_query(query)
        
        if result["status"] == "error":
            return tool_error(f"Failed to load relationships: {result.get('error_message', 'Unknown error')}")
        
        relationships_loaded = result.get("query_result", [{}])[0].get("relationships_loaded", 0)
        
        # Track in audit trail
        audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
        audit_trail.append({
            "action": "load_relationships",
            "file": source_file,
            "relationship_type": relationship_type,
            "relationships_loaded": relationships_loaded,
            "resolutions_applied": len(skip_conditions)
        })
        tool_context.state[INGESTION_AUDIT_TRAIL] = audit_trail
        
        logger.info(f"Loaded {relationships_loaded} relationships of type {relationship_type} from {source_file}")
        
        return tool_success("loading_result", {
            "file": source_file,
            "relationship_type": relationship_type,
            "relationships_loaded": relationships_loaded
        })
    except Exception as e:
        return tool_error(f"Error loading relationships from CSV: {str(e)}")


def get_ingestion_progress(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the current ingestion progress and audit trail.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and ingestion progress
    """
    audit_trail = tool_context.state.get(INGESTION_AUDIT_TRAIL, [])
    
    return tool_success("ingestion_progress", {
        "total_actions": len(audit_trail),
        "audit_trail": audit_trail
    })

