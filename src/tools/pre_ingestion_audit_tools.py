"""
Tools for the Pre-Ingestion Audit Agent.

These tools scan data files BEFORE loading them into Neo4j to detect
data quality issues that would cause problems during ingestion.
"""
import csv
import uuid
from typing import Dict, Any, List
from pathlib import Path
from google.adk.tools import ToolContext

from src.utils.constants import (
    APPROVED_CONSTRUCTION_PLAN,
    APPROVED_FILES,
    PRE_INGESTION_AUDIT_QUERIES,
    AUDIT_RESOLUTIONS
)
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def scan_csv_for_duplicates(
    file_path: str,
    unique_column: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Scan a CSV file for duplicate values in the unique identifier column.
    
    Args:
        file_path: Path to the CSV file
        unique_column: Name of the column that should have unique values
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and list of duplicate issues found
    """
    try:
        full_path = Path("data/story1") / file_path
        
        if not full_path.exists():
            return tool_error(f"File not found: {file_path}")
        
        # Read CSV and track values
        seen_values = {}
        duplicates = []
        
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if unique_column not in reader.fieldnames:
                return tool_error(
                    f"Column '{unique_column}' not found in {file_path}. "
                    f"Available columns: {reader.fieldnames}"
                )
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                value = row.get(unique_column)
                
                if value in seen_values:
                    # Found duplicate
                    duplicates.append({
                        "duplicate_value": value,
                        "first_occurrence": seen_values[value],
                        "second_occurrence": {
                            "row": row_num,
                            "data": dict(row)
                        }
                    })
                else:
                    seen_values[value] = {
                        "row": row_num,
                        "data": dict(row)
                    }
        
        if duplicates:
            logger.warning(
                f"Found {len(duplicates)} duplicate(s) in {file_path} "
                f"column '{unique_column}'"
            )
            return tool_success("duplicates", {
                "file": file_path,
                "column": unique_column,
                "duplicates_found": len(duplicates),
                "duplicates": duplicates
            })
        else:
            logger.info(f"No duplicates found in {file_path} column '{unique_column}'")
            return tool_success("duplicates", {
                "file": file_path,
                "column": unique_column,
                "duplicates_found": 0,
                "message": "No duplicates found"
            })
            
    except Exception as e:
        return tool_error(f"Error scanning {file_path}: {str(e)}")


def check_missing_required_fields(
    file_path: str,
    required_columns: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Check a CSV file for missing/NULL/empty values in required columns.
    
    Args:
        file_path: Path to the CSV file
        required_columns: List of column names that must have values
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and list of missing value issues
    """
    try:
        full_path = Path("data/story1") / file_path
        
        if not full_path.exists():
            return tool_error(f"File not found: {file_path}")
        
        missing_issues = []
        
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate columns exist
            missing_cols = [col for col in required_columns if col not in reader.fieldnames]
            if missing_cols:
                return tool_error(
                    f"Required columns not found in {file_path}: {missing_cols}"
                )
            
            for row_num, row in enumerate(reader, start=2):
                for col in required_columns:
                    value = row.get(col, "").strip()
                    
                    # Check if value is missing/empty/NULL
                    if not value or value.upper() in ["NULL", "NONE", "NA", "N/A"]:
                        missing_issues.append({
                            "row": row_num,
                            "column": col,
                            "value": value or "EMPTY",
                            "row_data": dict(row)
                        })
        
        if missing_issues:
            logger.warning(
                f"Found {len(missing_issues)} missing value(s) in {file_path}"
            )
            return tool_success("missing_values", {
                "file": file_path,
                "required_columns": required_columns,
                "issues_found": len(missing_issues),
                "issues": missing_issues
            })
        else:
            logger.info(f"All required fields present in {file_path}")
            return tool_success("missing_values", {
                "file": file_path,
                "required_columns": required_columns,
                "issues_found": 0,
                "message": "All required fields present"
            })
            
    except Exception as e:
        return tool_error(f"Error checking {file_path}: {str(e)}")


def check_foreign_keys(
    file_path: str,
    foreign_key_column: str,
    reference_file: str,
    reference_column: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Check if all foreign key values in a file exist in the referenced table.
    
    Args:
        file_path: Path to the CSV file containing foreign keys
        foreign_key_column: Name of the foreign key column
        reference_file: Path to the CSV file being referenced
        reference_column: Name of the unique identifier column in reference file
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and list of invalid foreign key issues
    """
    try:
        source_path = Path("data/story1") / file_path
        ref_path = Path("data/story1") / reference_file
        
        if not source_path.exists():
            return tool_error(f"File not found: {file_path}")
        if not ref_path.exists():
            return tool_error(f"Reference file not found: {reference_file}")
        
        # Load valid reference values
        valid_values = set()
        with open(ref_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reference_column not in reader.fieldnames:
                return tool_error(
                    f"Column '{reference_column}' not found in {reference_file}"
                )
            for row in reader:
                value = row.get(reference_column, "").strip()
                if value:
                    valid_values.add(value)
        
        # Check foreign keys
        invalid_fks = []
        with open(source_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if foreign_key_column not in reader.fieldnames:
                return tool_error(
                    f"Column '{foreign_key_column}' not found in {file_path}"
                )
            
            for row_num, row in enumerate(reader, start=2):
                fk_value = row.get(foreign_key_column, "").strip()
                
                # Skip empty values (will be caught by missing_required check)
                if not fk_value:
                    continue
                
                if fk_value not in valid_values:
                    invalid_fks.append({
                        "row": row_num,
                        "column": foreign_key_column,
                        "invalid_value": fk_value,
                        "reference_file": reference_file,
                        "reference_column": reference_column,
                        "row_data": dict(row)
                    })
        
        if invalid_fks:
            logger.warning(
                f"Found {len(invalid_fks)} invalid foreign key(s) in {file_path}"
            )
            return tool_success("foreign_key_violations", {
                "file": file_path,
                "foreign_key_column": foreign_key_column,
                "reference_file": reference_file,
                "issues_found": len(invalid_fks),
                "issues": invalid_fks
            })
        else:
            logger.info(f"All foreign keys valid in {file_path}")
            return tool_success("foreign_key_violations", {
                "file": file_path,
                "foreign_key_column": foreign_key_column,
                "issues_found": 0,
                "message": "All foreign keys valid"
            })
            
    except Exception as e:
        return tool_error(f"Error checking foreign keys: {str(e)}")


def create_audit_query(
    query_type: str,
    category: str,
    evidence: Dict[str, Any],
    proposed_actions: List[str],
    severity: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Create a pre-ingestion audit query for user review.
    
    An audit query represents an issue found during pre-ingestion scanning
    that requires user review and resolution before proceeding with ingestion.
    
    Args:
        query_type: "pre_ingestion"
        category: Issue category (duplicate_unique_identifier, missing_required_field, invalid_foreign_key)
        evidence: Dict with issue details (file, column, conflicts, etc.)
        proposed_actions: List of possible resolution actions
        severity: "error", "warning", or "info"
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and the created audit query
    """
    # Generate unique query ID
    query_id = f"pre_ing_{category}_{uuid.uuid4().hex[:8]}"
    
    # Get current audit queries
    audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
    
    # Create audit query
    audit_query = {
        "query_id": query_id,
        "type": query_type,
        "category": category,
        "status": "pending_review",
        "severity": severity,
        "evidence": evidence,
        "proposed_actions": proposed_actions,
        "user_decision": None,
        "decided_at": None,
        "decision_notes": None
    }
    
    # Add to state
    audit_queries[query_id] = audit_query
    tool_context.state[PRE_INGESTION_AUDIT_QUERIES] = audit_queries
    
    logger.info(f"Created audit query: {query_id} ({category}, severity: {severity})")
    
    return tool_success("audit_query", {
        "message": f"Created audit query {query_id}",
        "query_id": query_id,
        "query": audit_query
    })


def get_pre_ingestion_audit_queries(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get all pre-ingestion audit queries.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with all audit queries organized by status and severity
    """
    audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
    
    if not audit_queries:
        return tool_success(PRE_INGESTION_AUDIT_QUERIES, {
            "queries": {},
            "total": 0,
            "message": "No audit queries generated yet"
        })
    
    # Organize by status
    by_status = {
        "pending_review": [],
        "approved": [],
        "rejected": []
    }
    
    # Organize by severity
    by_severity = {
        "error": [],
        "warning": [],
        "info": []
    }
    
    # Organize by category
    by_category = {}
    
    for query_id, query in audit_queries.items():
        status = query.get("status", "pending_review")
        severity = query.get("severity", "info")
        category = query.get("category", "unknown")
        
        by_status[status].append(query)
        by_severity[severity].append(query)
        
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(query)
    
    return tool_success(PRE_INGESTION_AUDIT_QUERIES, {
        "queries": audit_queries,
        "total": len(audit_queries),
        "by_status": {k: len(v) for k, v in by_status.items()},
        "by_severity": {k: len(v) for k, v in by_severity.items()},
        "by_category": {k: len(v) for k, v in by_category.items()},
        "organized": {
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category
        }
    })


def resolve_audit_query(
    query_id: str,
    resolution: str,
    notes: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Record user's resolution decision for a pre-ingestion audit query.
    
    Args:
        query_id: ID of the audit query to resolve
        resolution: User's decision (skip_record, use_first, use_second, merge, 
                    manual_fix, update_construction_plan, approve, reject)
        notes: User's notes explaining the decision
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with status and updated audit query
    """
    audit_queries = tool_context.state.get(PRE_INGESTION_AUDIT_QUERIES, {})
    
    if query_id not in audit_queries:
        return tool_error(
            f"Audit query '{query_id}' not found. "
            f"Available queries: {list(audit_queries.keys())}"
        )
    
    # Valid resolutions
    valid_resolutions = [
        "skip_record",
        "use_first",
        "use_second", 
        "merge",
        "manual_fix",
        "update_construction_plan",
        "approve",
        "reject"
    ]
    
    if resolution not in valid_resolutions:
        return tool_error(
            f"Invalid resolution '{resolution}'. "
            f"Must be one of: {', '.join(valid_resolutions)}"
        )
    
    # Update audit query
    audit_queries[query_id]["user_decision"] = resolution
    audit_queries[query_id]["decision_notes"] = notes
    audit_queries[query_id]["decided_at"] = str(logger.handlers[0].formatter.formatTime(
        logger.makeRecord("", 0, "", 0, "", (), None)
    ) if logger.handlers else "unknown")
    audit_queries[query_id]["status"] = "approved" if resolution == "approve" else "rejected" if resolution == "reject" else "resolved"
    
    tool_context.state[PRE_INGESTION_AUDIT_QUERIES] = audit_queries
    
    # Store resolution in AUDIT_RESOLUTIONS for easy lookup during ingestion
    resolutions = tool_context.state.get(AUDIT_RESOLUTIONS, {})
    resolutions[query_id] = {
        "resolution": resolution,
        "notes": notes,
        "resolved_at": audit_queries[query_id]["decided_at"]
    }
    tool_context.state[AUDIT_RESOLUTIONS] = resolutions
    
    logger.info(f"Resolved audit query {query_id}: {resolution}")
    
    return tool_success("resolution", {
        "message": f"Audit query {query_id} resolved as '{resolution}'",
        "query_id": query_id,
        "resolution": resolution,
        "updated_query": audit_queries[query_id]
    })


def get_construction_plan_summary(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get a summary of the construction plan to understand what files and
    columns need to be validated.
    
    Args:
        tool_context: ADK ToolContext
    
    Returns:
        Dictionary with construction plan summary
    """
    construction_plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
    
    if not construction_plan:
        return tool_error("No approved construction plan found")
    
    # Extract validation requirements from construction plan
    node_files = {}
    relationship_files = {}
    
    for key, construction in construction_plan.items():
        if construction.get("construction_type") == "node":
            file = construction.get("source_file")
            node_files[file] = {
                "label": construction.get("label"),
                "unique_column": construction.get("unique_column_name"),
                "properties": construction.get("properties", []),
                "construction_key": key
            }
        elif construction.get("construction_type") == "relationship":
            file = construction.get("source_file")
            if file:  # Some relationships come from node files
                relationship_files[file] = {
                    "relationship_type": construction.get("relationship_type"),
                    "from_column": construction.get("from_node_column"),
                    "to_column": construction.get("to_node_column"),
                    "properties": construction.get("properties", []),
                    "construction_key": key
                }
    
    return tool_success("construction_summary", {
        "node_files": node_files,
        "relationship_files": relationship_files,
        "total_files": len(set(list(node_files.keys()) + list(relationship_files.keys()))),
        "total_nodes": len(node_files),
        "total_relationships": len(relationship_files)
    })


def infer_foreign_keys(
    file_path: str,
    properties: List[str],
    unique_column: str,
    construction_plan: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Infer which properties are foreign keys based on naming convention.
    
    Args:
        file_path: Source file being analyzed
        properties: List of properties/columns
        unique_column: The unique identifier column (exclude this)
        construction_plan: Full construction plan to find reference tables
    
    Returns:
        List of foreign key mappings
    """
    foreign_keys = []
    
    for prop in properties:
        # Skip the unique identifier
        if prop == unique_column:
            continue
        
        # Check if property ends with _id (common FK convention)
        if prop.endswith("_id"):
            # Try to find the referenced table
            # Look for a node construction with this as unique_column
            for key, construction in construction_plan.items():
                if construction.get("construction_type") == "node":
                    if construction.get("unique_column_name") == prop:
                        foreign_keys.append({
                            "fk_column": prop,
                            "reference_file": construction.get("source_file"),
                            "reference_column": prop
                        })
                        break
    
    return foreign_keys

