"""
Tools for the Fact Extraction Agent.

These tools allow the agent to propose and approve fact types (relationship triples)
that can be extracted from unstructured markdown data.
"""
from typing import Dict, Any

from google.adk.tools import ToolContext

from src.utils.constants import APPROVED_ENTITIES, PROPOSED_FACTS, APPROVED_FACTS
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


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
    facts: list,
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

