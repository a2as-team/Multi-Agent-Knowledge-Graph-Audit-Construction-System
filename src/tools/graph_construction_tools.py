"""
Tools for the Graph Construction Agent.

These tools execute the approved construction plan to build the knowledge graph
in Neo4j from structured CSV files.
"""
import csv
from typing import Dict, Any, List, Optional
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
        
        # Get audit resolutions for this file
        resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
        audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
        
        # Filter resolutions for this file
        file_resolutions = {
            qid: res for qid, res in resolutions.items()
            if audit_queries.get(qid, {}).get("evidence", {}).get("file") == source_file
        }
        
        # Build the LOAD CSV query
        # Note: Neo4j LOAD CSV requires files to be in the import directory
        # Use CALL with row parameter for transaction batching
        query = f"""LOAD CSV WITH HEADERS FROM "file:///{source_file}" AS row
        CALL (row) {{
            MERGE (n:`{label}` {{ `{unique_column_name}`: row.`{unique_column_name}` }})"""
        
        # Add property assignments
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
        audit_trail.append({
            "action": "load_nodes",
            "file": source_file,
            "label": label,
            "nodes_loaded": nodes_loaded,
            "resolutions_applied": len(file_resolutions)
        })
        tool_context.state[INGESTION_AUDIT_TRAIL] = audit_trail
        
        logger.info(f"Loaded {nodes_loaded} nodes from {source_file} with label {label}")
        
        return tool_success("loading_result", {
            "file": source_file,
            "label": label,
            "nodes_loaded": nodes_loaded,
            "resolutions_applied": len(file_resolutions)
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
        
        # Build the LOAD CSV query for relationships
        query = f"""LOAD CSV WITH HEADERS FROM "file:///{source_file}" AS row
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
            "relationships_loaded": relationships_loaded
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

