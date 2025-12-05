"""
Tools for the Data Quality Rules Agent.

These tools allow the agent to propose and approve custom data quality rules
that will be used to validate the knowledge graph after construction.
"""
from typing import Dict, Any, List
from google.adk.tools import ToolContext

from src.utils.constants import (
    PROPOSED_QUALITY_RULES,
    APPROVED_QUALITY_RULES,
    APPROVED_CONSTRUCTION_PLAN,
    APPROVED_ENTITIES,
    APPROVED_FACTS
)
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def get_schema_context(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the current schema context (construction plan, entities, facts)
    to help the agent understand what rules are applicable.
    
    Args:
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with schema information or error message
    """
    construction_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    entity_types = tool_context.state.get(APPROVED_ENTITIES, [])
    fact_types = tool_context.state.get(APPROVED_FACTS, {})
    
    # Extract node labels and relationship types
    node_labels = []
    relationship_types = []
    
    for key, construction in construction_plan.items():
        if construction.get("construction_type") == "node":
            node_labels.append(construction.get("label"))
        elif construction.get("construction_type") == "relationship":
            relationship_types.append(construction.get("relationship_type"))
    
    # Extract fact relationship types
    fact_relationship_types = list(fact_types.keys()) if fact_types else []
    
    return tool_success("schema_context", {
        "domain_node_labels": node_labels,
        "domain_relationship_types": relationship_types,
        "entity_types": entity_types,
        "fact_relationship_types": fact_relationship_types,
        "total_constructions": len(construction_plan),
        "total_entity_types": len(entity_types),
        "total_fact_types": len(fact_types)
    })


def add_quality_rule(
    rule_id: str,
    rule_type: str,
    description: str,
    severity: str,
    parameters: Dict[str, Any],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Add a proposed data quality rule.
    
    Rule types supported:
    - required_relationship: Entity must have a specific relationship
    - temporal_constraint: Date/time fields must follow logical order
    - cardinality_constraint: Relationship cardinality (one-to-one, one-to-many, etc.)
    - value_constraint: Property value must meet certain criteria
    - orphan_detection: Find nodes with no relationships
    - unresolved_entity: Find entities without domain correspondence
    - custom_cypher: Custom Cypher query for validation
    
    Args:
        rule_id: Unique identifier for the rule
        rule_type: Type of quality rule (from list above)
        description: Human-readable description of what the rule checks
        severity: "error", "warning", or "info"
        parameters: Dict with rule-specific parameters
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with status and updated proposed_quality_rules
    
    Example:
        add_quality_rule(
            "artwork_must_have_creator",
            "required_relationship",
            "Every artwork must have a creator",
            "error",
            {
                "entity_label": "Artwork",
                "relationship_type": "CREATED_BY",
                "target_label": "Artist"
            },
            tool_context
        )
    """
    # Validate severity
    if severity not in ["error", "warning", "info"]:
        return tool_error(
            f"Invalid severity '{severity}'. Must be 'error', 'warning', or 'info'."
        )
    
    # Validate rule type
    valid_rule_types = [
        "required_relationship",
        "temporal_constraint",
        "cardinality_constraint",
        "value_constraint",
        "orphan_detection",
        "unresolved_entity",
        "custom_cypher"
    ]
    
    if rule_type not in valid_rule_types:
        return tool_error(
            f"Invalid rule_type '{rule_type}'. Must be one of: {', '.join(valid_rule_types)}"
        )
    
    # Get current rules
    current_rules = tool_context.state.get(PROPOSED_QUALITY_RULES, {})
    
    # Check for duplicate rule_id
    if rule_id in current_rules:
        return tool_error(
            f"Rule with id '{rule_id}' already exists. Use a different rule_id or remove the existing rule first."
        )
    
    # Create rule
    rule = {
        "rule_id": rule_id,
        "rule_type": rule_type,
        "description": description,
        "severity": severity,
        "parameters": parameters
    }
    
    # Add rule
    current_rules[rule_id] = rule
    tool_context.state[PROPOSED_QUALITY_RULES] = current_rules
    
    logger.info(f"Added quality rule: {rule_id} ({rule_type}, severity: {severity})")
    
    return tool_success(PROPOSED_QUALITY_RULES, {
        "message": f"Successfully added quality rule '{rule_id}'",
        "rule": rule,
        "total_rules": len(current_rules)
    })


def remove_quality_rule(
    rule_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Remove a proposed quality rule by its ID.
    
    Args:
        rule_id: The ID of the rule to remove
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with status and updated proposed_quality_rules
    """
    current_rules = tool_context.state.get(PROPOSED_QUALITY_RULES, {})
    
    if not current_rules:
        return tool_error("No proposed quality rules exist. Nothing to remove.")
    
    if rule_id not in current_rules:
        available_rules = list(current_rules.keys())
        return tool_error(
            f"Rule with id '{rule_id}' not found. "
            f"Available rules: {available_rules}"
        )
    
    # Remove the rule
    removed_rule = current_rules.pop(rule_id)
    tool_context.state[PROPOSED_QUALITY_RULES] = current_rules
    
    logger.info(f"Removed quality rule: {rule_id}")
    
    return tool_success(PROPOSED_QUALITY_RULES, {
        "message": f"Successfully removed rule '{rule_id}'",
        "removed_rule": removed_rule,
        "remaining_rules": len(current_rules)
    })


def get_proposed_quality_rules(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get all proposed quality rules.
    
    Args:
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with status and proposed_quality_rules
    """
    proposed_rules = tool_context.state.get(PROPOSED_QUALITY_RULES, {})
    
    # Organize by severity for better readability
    by_severity = {
        "error": [],
        "warning": [],
        "info": []
    }
    
    for rule_id, rule in proposed_rules.items():
        by_severity[rule.get("severity", "info")].append(rule)
    
    return tool_success(PROPOSED_QUALITY_RULES, {
        "rules": proposed_rules,
        "by_severity": by_severity,
        "total_rules": len(proposed_rules),
        "counts": {
            "error": len(by_severity["error"]),
            "warning": len(by_severity["warning"]),
            "info": len(by_severity["info"])
        }
    })


def approve_quality_rules(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Approve the proposed quality rules.
    
    This moves the rules from PROPOSED_QUALITY_RULES to APPROVED_QUALITY_RULES
    and makes them ready for use in audit agents.
    
    Args:
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with status and approved_quality_rules
    """
    proposed_rules = tool_context.state.get(PROPOSED_QUALITY_RULES, {})
    
    if not proposed_rules:
        return tool_error(
            "No proposed quality rules to approve. Please add rules first."
        )
    
    # Move to approved
    tool_context.state[APPROVED_QUALITY_RULES] = proposed_rules.copy()
    
    logger.info(f"Approved {len(proposed_rules)} quality rules")
    
    return tool_success(APPROVED_QUALITY_RULES, {
        "message": f"Successfully approved {len(proposed_rules)} quality rules",
        "approved_rules": proposed_rules,
        "total_approved": len(proposed_rules)
    })


def get_approved_quality_rules(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get all approved quality rules.
    
    Args:
        tool_context: ADK ToolContext containing state
    
    Returns:
        Dictionary with status and approved_quality_rules
    """
    approved_rules = tool_context.state.get(APPROVED_QUALITY_RULES, {})
    
    if not approved_rules:
        return tool_success(APPROVED_QUALITY_RULES, {
            "rules": {},
            "message": "No quality rules have been approved yet.",
            "total_rules": 0
        })
    
    # Organize by severity
    by_severity = {
        "error": [],
        "warning": [],
        "info": []
    }
    
    for rule_id, rule in approved_rules.items():
        by_severity[rule.get("severity", "info")].append(rule)
    
    return tool_success(APPROVED_QUALITY_RULES, {
        "rules": approved_rules,
        "by_severity": by_severity,
        "total_rules": len(approved_rules),
        "counts": {
            "error": len(by_severity["error"]),
            "warning": len(by_severity["warning"]),
            "info": len(by_severity["info"])
        }
    })

