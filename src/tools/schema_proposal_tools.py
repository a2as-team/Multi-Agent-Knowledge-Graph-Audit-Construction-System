"""
Schema proposal tools for the Schema Proposal Agent.

These tools allow the agent to propose node and relationship constructions
for building a knowledge graph from structured data files.
"""
from typing import Dict, Any, List

from google.adk.tools import ToolContext

from src.utils.constants import PROPOSED_CONSTRUCTION_PLAN, APPROVED_CONSTRUCTION_PLAN
from src.utils.logger import logger
from src.tools.file_tools import search_file
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def propose_node_construction(
    approved_file: str,
    proposed_label: str,
    unique_column_name: str,
    proposed_properties: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Propose a node construction for an approved file that supports the user goal.

    The construction will be added to the proposed construction plan dictionary
    using proposed_label as the key.

    The construction entry will be a dictionary with the following keys:
    - construction_type: "node"
    - source_file: the approved file to propose a node construction for
    - label: the proposed label of the node
    - unique_column_name: the name of the column that will be used to uniquely identify constructed nodes
    - properties: A list of property names for the node, derived from column names in the approved file

    Args:
        approved_file: The approved file to propose a node construction for
        proposed_label: The proposed label for constructed nodes (used as key in the construction plan)
        unique_column_name: The name of the column that will be used to uniquely identify constructed nodes
        proposed_properties: column names that should be imported as node properties
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and node_construction or error message.
    """
    # Quick sanity check -- does the approved file have the unique column?
    search_results = search_file(approved_file, unique_column_name, tool_context)
    if search_results["status"] == "error":
        return search_results  # return the error
    if search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(
            f"{approved_file} does not have the column {unique_column_name}. "
            "Check the file content and try again."
        )

    # Get the current construction plan, or an empty one if none exists
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    node_construction_rule = {
        "construction_type": "node",
        "source_file": approved_file,
        "label": proposed_label,
        "unique_column_name": unique_column_name,
        "properties": proposed_properties
    }
    construction_plan[proposed_label] = node_construction_rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    
    logger.info(f"Proposed node construction: {proposed_label} from {approved_file}")
    return tool_success("node_construction", node_construction_rule)


def propose_relationship_construction(
    approved_file: str,
    proposed_relationship_type: str,
    from_node_label: str,
    from_node_column: str,
    to_node_label: str,
    to_node_column: str,
    proposed_properties: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Propose a relationship construction for an approved file that supports the user goal.

    The construction will be added to the proposed construction plan dictionary
    using proposed_relationship_type as the key.

    Args:
        approved_file: The approved file to propose a relationship construction for
        proposed_relationship_type: The proposed label for constructed relationships
        from_node_label: The label of the source node
        from_node_column: The name of the column within the approved file that will be used to uniquely identify source nodes
        to_node_label: The label of the target node
        to_node_column: The name of the column within the approved file that will be used to uniquely identify target nodes
        proposed_properties: column names that should be imported as relationship properties
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and relationship_construction or error message.
    """
    # Quick sanity check -- does the approved file have the from_node_column?
    search_results = search_file(approved_file, from_node_column, tool_context)
    if search_results["status"] == "error":
        return search_results  # return the error if there is one
    if search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(
            f"{approved_file} does not have the from node column {from_node_column}. "
            "Check the content of the file and reconsider the relationship."
        )

    # Quick sanity check -- does the approved file have the to_node_column?
    search_results = search_file(approved_file, to_node_column, tool_context)
    if search_results["status"] == "error" or search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(
            f"{approved_file} does not have the to node column {to_node_column}. "
            "Check the content of the file and reconsider the relationship."
        )

    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    relationship_construction_rule = {
        "construction_type": "relationship",
        "source_file": approved_file,
        "relationship_type": proposed_relationship_type,
        "from_node_label": from_node_label,
        "from_node_column": from_node_column,
        "to_node_label": to_node_label,
        "to_node_column": to_node_column,
        "properties": proposed_properties
    }
    construction_plan[proposed_relationship_type] = relationship_construction_rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    
    logger.info(
        f"Proposed relationship construction: {proposed_relationship_type} "
        f"({from_node_label} -> {to_node_label}) from {approved_file}"
    )
    return tool_success("relationship_construction", relationship_construction_rule)


def remove_node_construction(node_label: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Remove a node construction from the proposed construction plan based on label.

    Args:
        node_label: The label of the node construction to remove
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and confirmation or error message.
    """
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    if node_label not in construction_plan:
        return tool_success("node_construction_removed", "Node construction rule not found. Removal not needed.")

    del construction_plan[node_label]
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    
    logger.info(f"Removed node construction: {node_label}")
    return tool_success("node_construction_removed", node_label)


def remove_relationship_construction(relationship_type: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Remove a relationship construction from the proposed construction plan based on type.

    Args:
        relationship_type: The type of the relationship construction to remove
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and confirmation or error message.
    """
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})

    if relationship_type not in construction_plan:
        return tool_success(
            "relationship_construction_removed",
            "Relationship construction rule not found. Removal not needed."
        )
    
    construction_plan.pop(relationship_type)
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = construction_plan
    
    logger.info(f"Removed relationship construction: {relationship_type}")
    return tool_success("relationship_construction_removed", relationship_type)


def get_proposed_construction_plan(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the proposed construction plan, a dictionary of construction rules.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with the proposed construction plan (may be empty if none proposed yet).
    """
    construction_plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    return tool_success("proposed_construction_plan", construction_plan)


def approve_proposed_construction_plan(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Approve the proposed construction plan, if there is one.
    
    This copies the proposed_construction_plan to approved_construction_plan in state.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_construction_plan or error message.
    """
    if PROPOSED_CONSTRUCTION_PLAN not in tool_context.state:
        return tool_error("No proposed construction plan found. Propose a plan first.")
    
    tool_context.state[APPROVED_CONSTRUCTION_PLAN] = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN)
    
    logger.info("Approved construction plan")
    return tool_success(APPROVED_CONSTRUCTION_PLAN, tool_context.state[APPROVED_CONSTRUCTION_PLAN])


def get_approved_construction_plan(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved construction plan.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_construction_plan or empty dict if not yet approved.
    """
    approved_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    
    if not approved_plan:
        return tool_success(APPROVED_CONSTRUCTION_PLAN, {
            "message": "No construction plan has been approved yet.",
            "approved_construction_plan": {}
        })
    
    return tool_success(APPROVED_CONSTRUCTION_PLAN, approved_plan)

