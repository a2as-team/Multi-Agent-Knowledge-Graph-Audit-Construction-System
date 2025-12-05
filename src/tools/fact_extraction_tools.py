"""
Tools for the Fact Extraction Agent.

These tools allow the agent to propose and approve fact types (relationship triples)
that can be extracted from unstructured markdown data.
"""
from typing import Dict, Any, List

from google.adk.tools import ToolContext

from src.utils.constants import (
    APPROVED_ENTITIES, 
    PROPOSED_FACTS, 
    APPROVED_FACTS,
    APPROVED_CONSTRUCTION_PLAN
)
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def get_well_known_relationships(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gets the approved relationship types from the construction plan (structured data phase)
    to avoid proposing redundant fact types in the unstructured data phase.
    
    This tool helps the agent understand what relationships already exist in the graph
    from structured data, so it can focus on discovering NEW relationships that only
    appear in unstructured text.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and existing_relationships list, or empty list if none exist.
        Each relationship contains: relationship_type, from_label, to_label
    
    Example return:
        {
            "status": "success",
            "existing_relationships": [
                {
                    "relationship_type": "CREATED_BY",
                    "from_label": "Artwork",
                    "to_label": "Artist"
                },
                {
                    "relationship_type": "LOCATED_AT",
                    "from_label": "Artwork",
                    "to_label": "Location"
                }
            ]
        }
    """
    construction_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    
    if not construction_plan:
        logger.info("No approved construction plan found - no existing relationships to avoid")
        return tool_success("existing_relationships", [])
    
    # Extract relationship types from construction plan
    existing_relationships = []
    for entry in construction_plan.values():
        if entry.get("construction_type") == "relationship":
            existing_relationships.append({
                "relationship_type": entry.get("relationship_type", ""),
                "from_label": entry.get("from_node_label", ""),
                "to_label": entry.get("to_node_label", "")
            })
    
    logger.info(f"Retrieved {len(existing_relationships)} existing relationships from structured data")
    return tool_success("existing_relationships", existing_relationships)


def add_proposed_fact(
    approved_subject_label: str,
    proposed_predicate_label: str,
    approved_object_label: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Add a proposed type of fact that could be extracted from the markdown files.

    A proposed fact type is a tuple of (subject, predicate, object) where
    the subject and object are approved entity types and the predicate 
    is a proposed relationship label.

    Args:
        approved_subject_label: Approved label of the subject entity type
        proposed_predicate_label: Label of the predicate (relationship type)
        approved_object_label: Approved label of the object entity type
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and proposed_fact_types or error message.
    """
    # Guard against invalid labels
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    
    if not approved_entities:
        return tool_error(
            "No approved entities found. "
            "Please ensure the NER Agent has approved entity types first."
        )
    
    if approved_subject_label not in approved_entities:
        return tool_error(
            f"Approved subject label '{approved_subject_label}' not found in approved entities. "
            f"Available entities: {approved_entities}. Try again with a valid entity type."
        )
    
    if approved_object_label not in approved_entities:
        return tool_error(
            f"Approved object label '{approved_object_label}' not found in approved entities. "
            f"Available entities: {approved_entities}. Try again with a valid entity type."
        )
    
    # Add the fact to the proposed facts dictionary
    current_facts = tool_context.state.get(PROPOSED_FACTS, {})
    current_facts[proposed_predicate_label] = {
        "subject_label": approved_subject_label,
        "predicate_label": proposed_predicate_label,
        "object_label": approved_object_label
    }
    tool_context.state[PROPOSED_FACTS] = current_facts
    
    logger.info(
        f"Added proposed fact: ({approved_subject_label}, {proposed_predicate_label}, {approved_object_label})"
    )
    return tool_success(PROPOSED_FACTS, current_facts)


def add_proposed_facts_batch(
    facts: List[Dict[str, str]],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Add multiple proposed fact types in a single call (EFFICIENT - reduces API calls).
    
    This is the preferred method for adding facts as it batches multiple facts into 
    a single tool call, reducing API calls by 70-80% and preventing rate limit errors.
    
    Args:
        facts: List of dicts, each containing:
               - approved_subject_label: str
               - proposed_predicate_label: str
               - approved_object_label: str
        tool_context: ADK ToolContext containing state and other context
    
    Example:
        facts = [
            {
                "approved_subject_label": "Artist",
                "proposed_predicate_label": "born in",
                "approved_object_label": "Location"
            },
            {
                "approved_subject_label": "Artist",
                "proposed_predicate_label": "created",
                "approved_object_label": "Artwork"
            }
        ]
    
    Returns:
        Dictionary with status, added_count, and total_facts or error message.
    """
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    
    if not approved_entities:
        return tool_error(
            "No approved entities found. "
            "Please ensure the NER Agent has approved entity types first."
        )
    
    current_facts = tool_context.state.get(PROPOSED_FACTS, {})
    added_facts = []
    errors = []
    
    for fact in facts:
        subject = fact.get("approved_subject_label")
        predicate = fact.get("proposed_predicate_label")
        obj = fact.get("approved_object_label")
        
        # Validate required fields
        if not subject or not predicate or not obj:
            errors.append("Missing required field(s) in fact dict")
            continue
        
        # Validate entities
        if subject not in approved_entities:
            errors.append(f"Subject '{subject}' not in approved entities")
            continue
        if obj not in approved_entities:
            errors.append(f"Object '{obj}' not in approved entities")
            continue
        
        # Add fact using predicate as key (allows duplicate subject-object with different predicates)
        fact_key = predicate
        current_facts[fact_key] = {
            "subject_label": subject,
            "predicate_label": predicate,
            "object_label": obj
        }
        added_facts.append(f"({subject}, {predicate}, {obj})")
        logger.info(f"Added proposed fact: ({subject}, {predicate}, {obj})")
    
    tool_context.state[PROPOSED_FACTS] = current_facts
    
    result_message = f"Successfully added {len(added_facts)} fact types. Total facts: {len(current_facts)}"
    
    if errors:
        result_message += f" | Encountered {len(errors)} errors: {', '.join(errors[:3])}"
        if len(errors) > 3:
            result_message += f" and {len(errors) - 3} more..."
    
    return tool_success(PROPOSED_FACTS, {
        "message": result_message,
        "added_count": len(added_facts),
        "total_facts": len(current_facts),
        "errors": errors if errors else None
    })


def remove_proposed_fact(
    proposed_predicate_label: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Remove a specific proposed fact type by its predicate label.
    
    Use this when the critic identifies a fact that should be removed
    (e.g., duplicates, inverse relationships, semantic redundancy).
    
    Args:
        proposed_predicate_label: The predicate label (key) of the fact to remove
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and remaining proposed_facts or error message.
    
    Example:
        remove_proposed_fact("owns", tool_context)
        # Removes the fact with predicate "owns"
    """
    current_facts = tool_context.state.get(PROPOSED_FACTS, {})
    
    if not current_facts:
        return tool_error(
            "No proposed facts exist. Nothing to remove."
        )
    
    if proposed_predicate_label not in current_facts:
        available_predicates = list(current_facts.keys())
        return tool_error(
            f"Fact with predicate '{proposed_predicate_label}' not found. "
            f"Available predicates: {available_predicates}"
        )
    
    # Remove the fact
    removed_fact = current_facts.pop(proposed_predicate_label)
    tool_context.state[PROPOSED_FACTS] = current_facts
    
    logger.info(
        f"Removed proposed fact: ({removed_fact['subject_label']}, "
        f"{removed_fact['predicate_label']}, {removed_fact['object_label']})"
    )
    
    return tool_success(PROPOSED_FACTS, {
        "message": f"Successfully removed fact '{proposed_predicate_label}'. "
                   f"Remaining facts: {len(current_facts)}",
        "removed_fact": removed_fact,
        "remaining_facts": current_facts
    })


def get_proposed_facts(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the proposed types of facts that could be extracted from the markdown files.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and proposed_fact_types (may be empty dict if not set yet).
    """
    proposed_facts = tool_context.state.get(PROPOSED_FACTS, {})
    return tool_success(PROPOSED_FACTS, proposed_facts)


def set_critic_feedback(
    status: str,
    message: str,
    issues: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Sets the critic's structured feedback on the proposed fact types.
    
    Called by the Fact Critic Agent after reviewing the proposed facts.
    
    Args:
        status: Either "valid" (facts are good) or "retry" (need refinement)
        message: Summary message from the critic
        issues: List of specific issues found (empty if status is "valid")
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and critic_feedback.
    """
    feedback = {
        "status": status,
        "message": message,
        "issues": issues if status == "retry" else []
    }
    tool_context.state["critic_feedback"] = feedback
    logger.info(f"Critic feedback set: {status} - {message}")
    if issues:
        logger.info(f"Issues found: {issues}")
    return tool_success("critic_feedback", feedback)


def get_critic_feedback(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Gets the critic's feedback on the proposed fact types.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and critic_feedback (may be empty dict if not set yet).
    """
    feedback = tool_context.state.get("critic_feedback", {})
    return tool_success("critic_feedback", feedback)


def approve_proposed_facts(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Upon user approval, records the proposed fact types as approved fact types.
    
    Only call this tool if the user has explicitly approved the proposed fact types.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_fact_types or error message.
    """
    if PROPOSED_FACTS not in tool_context.state:
        return tool_error(
            "No proposed fact types to approve. "
            "Please set proposed facts first, ask for user approval, then call this tool."
        )
    
    proposed_facts = tool_context.state[PROPOSED_FACTS]
    
    if not proposed_facts:
        return tool_error(
            "No proposed facts found. Use 'add_proposed_fact' to propose fact types first."
        )
    
    tool_context.state[APPROVED_FACTS] = proposed_facts
    logger.info(f"Approved facts: {tool_context.state[APPROVED_FACTS]}")
    return tool_success(APPROVED_FACTS, tool_context.state[APPROVED_FACTS])


def get_approved_facts(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the approved fact types.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_fact_types or empty dict if not yet approved.
    """
    approved_facts = tool_context.state.get(APPROVED_FACTS, {})
    
    if not approved_facts:
        return tool_success(APPROVED_FACTS, {
            "message": "No fact types have been approved yet.",
            "approved_facts": {}
        })
    
    return tool_success(APPROVED_FACTS, approved_facts)

