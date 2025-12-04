"""
Tools for the Named Entity Recognition (NER) Agent.

These tools allow the agent to propose and approve entity types to extract from unstructured data.
"""
from typing import Dict, Any, List

from google.adk.tools import ToolContext

from src.utils.constants import APPROVED_CONSTRUCTION_PLAN
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


# State keys for NER
PROPOSED_ENTITIES = "proposed_entity_types"
APPROVED_ENTITIES = "approved_entity_types"


def get_well_known_types(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gets the approved node labels from the construction plan that represent well-known entity types.
    
    Well-known entities closely correlate with existing node labels in the graph schema.
    For example, if "Product" is a node label, then "Product" is a well-known entity type.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_labels (set of node labels) or error message.
    """
    construction_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    
    if not construction_plan:
        return tool_error(
            "No approved construction plan found. "
            "The NER agent requires an approved construction plan from the structured data phase."
        )
    
    # Approved labels are the keys for each construction plan entry where `construction_type` is "node"
    approved_labels = {
        entry["label"] 
        for entry in construction_plan.values() 
        if entry.get("construction_type") == "node"
    }
    
    logger.info(f"Retrieved well-known types (node labels): {approved_labels}")
    return tool_success("approved_labels", list(approved_labels))


def set_proposed_entities(proposed_entity_types: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Sets the list of proposed entity types to extract from unstructured text.
    
    Entity types should include:
    - Well-known entities: those that match existing node labels from the graph schema
    - Discovered entities: those that appear consistently in the text and support the user's goal
    
    Args:
        proposed_entity_types: List of entity type names (e.g., ["Product", "Review", "Quality Issue"])
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and proposed_entity_types or error message.
    """
    if not proposed_entity_types:
        return tool_error("proposed_entity_types cannot be empty. Propose at least one entity type.")
    
    tool_context.state[PROPOSED_ENTITIES] = proposed_entity_types
    logger.info(f"Set proposed entities: {proposed_entity_types}")
    return tool_success(PROPOSED_ENTITIES, proposed_entity_types)


def get_proposed_entities(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gets the list of proposed entity types to extract from unstructured text.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and proposed_entity_types (may be empty list if not set yet).
    """
    proposed_entities = tool_context.state.get(PROPOSED_ENTITIES, [])
    return tool_success(PROPOSED_ENTITIES, proposed_entities)


def approve_proposed_entities(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Upon approval from user, records the proposed entity types as an approved list of entity types.
    
    Only call this tool if the user has explicitly approved the proposed entity types.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_entity_types or error message.
    """
    if PROPOSED_ENTITIES not in tool_context.state:
        return tool_error(
            "No proposed entity types to approve. "
            "Please set proposed entities first, ask for user approval, then call this tool."
        )
    
    tool_context.state[APPROVED_ENTITIES] = tool_context.state[PROPOSED_ENTITIES]
    logger.info(f"Approved entities: {tool_context.state[APPROVED_ENTITIES]}")
    return tool_success(APPROVED_ENTITIES, tool_context.state[APPROVED_ENTITIES])


def get_approved_entities(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved list of entity types to extract from unstructured text.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_entity_types (may be empty list if not set yet).
    """
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    return tool_success(APPROVED_ENTITIES, approved_entities)

