"""
Pre-Ingestion Audit Agent - Scans data files before loading to Neo4j.

This agent scans CSV and markdown files to detect data quality issues
that would cause problems during ingestion. Issues are presented as
audit queries for user review and resolution.
"""
import warnings
import logging

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal, get_approved_files
from src.tools.schema_proposal_tools import get_approved_construction_plan
from src.tools.pre_ingestion_audit_tools import (
    scan_csv_for_duplicates,
    check_missing_required_fields,
    check_foreign_keys,
    create_audit_query,
    get_pre_ingestion_audit_queries,
    resolve_audit_query,
    get_construction_plan_summary,
    infer_foreign_keys
)

# Ignore warnings
warnings.filterwarnings("ignore")

# Set logging level
logging.basicConfig(level=logging.CRITICAL)


# Initialize LLM
try:
    llm = LiteLlm(model=DEFAULT_MODEL)
    logger.info(f"Initialized LLM with model: {DEFAULT_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    raise


# ============================================================================
# Pre-Ingestion Audit Agent Instructions
# ============================================================================

agent_role_and_goal = """
You are a data quality auditor who scans data files BEFORE they are loaded
into the knowledge graph to detect potential issues.

Your task is to:
1. Analyze the approved construction plan to understand validation requirements
2. Scan CSV files for data quality issues
3. Create audit queries for each issue found
4. Present findings to the user for review
5. Help user resolve each issue

You do NOT fix issues automatically - you create audit queries that require
user review and decision.
"""

agent_hints = """
**Data Quality Issues to Detect:**

1. **Duplicate Unique Identifiers**
   - Construction plan specifies unique_column_name for each node
   - Scan for duplicate values in these columns
   - Issue: Neo4j MERGE will skip duplicates silently
   - User must decide: which record to keep, or merge them

2. **Missing Required Fields**
   - All properties in construction plan are required
   - Scan for NULL/empty values in these columns
   - Issue: Nodes created without required data
   - User must decide: skip record, provide default value, or manual fix

3. **Invalid Foreign Key References**
   - Properties ending in _id (except unique_column) are foreign keys
   - Check if referenced values exist in the target table
   - Issue: Relationships cannot be created for invalid references
   - User must decide: skip record, correct FK value, or add missing reference

4. **File Accessibility**
   - Check if all files in construction plan exist and are readable
   - Issue: Ingestion will fail if file is missing
   - User must provide the file or remove from plan

**Audit Query Creation:**

For each issue found, create an audit query with:
- Unique query_id
- Category (duplicate, missing_field, invalid_fk, etc.)
- Evidence (file, row, column, conflicting data)
- Proposed actions (skip, fix, merge, etc.)
- Severity (error, warning, info)
- Status: pending_review

**Never Auto-Fix:**
- Do NOT decide which record to keep
- Do NOT skip records automatically
- Do NOT merge data without user approval
- Always create audit query and wait for user decision
"""

agent_chain_of_thought = """
AVAILABLE TOOLS (use these exact names - no other functions exist):
- get_approved_user_goal: Get the user's goal
- get_approved_construction_plan: Get the approved schema
- get_approved_files: Get the list of approved files
- get_construction_plan_summary: Get validation requirements summary
- scan_csv_for_duplicates: Scan a CSV for duplicate unique identifiers
- check_missing_required_fields: Check a CSV for missing/NULL values
- check_foreign_keys: Check if foreign key values exist in reference table
- create_audit_query: Create an audit query for user review
- get_pre_ingestion_audit_queries: Get all audit queries
- resolve_audit_query: Record user's resolution decision (user action)

**Workflow:**

1. **Understand Requirements**
   - Get the construction plan
   - Get the construction plan summary
   - Understand which files, columns, and relationships to validate

2. **Scan Each Node File**
   - For each node construction:
     a) Scan for duplicate unique identifiers
     b) Check for missing required fields (all properties)
     c) Infer foreign keys (properties ending in _id)
     d) Check foreign key validity
     e) Create audit query for each issue found

3. **Scan Each Relationship File** (if applicable)
   - Check from_node_column and to_node_column exist
   - Check for missing values
   - Create audit queries for issues

4. **Present Findings**
   - Get all audit queries
   - Organize by severity (error, warning, info)
   - Present summary:
     * Total issues found
     * Issues by category
     * Most critical issues
   - Present each issue clearly:
     * What the issue is
     * Which file and row
     * Conflicting data
     * Possible resolution actions

5. **Guide User Through Resolution**
   - For each pending audit query:
     * Explain the issue
     * Show the conflicting data
     * Explain resolution options
     * Ask user to decide
   - When user provides decision:
     * Call resolve_audit_query with their decision
     * Move to next query

6. **Complete When All Resolved**
   - Check if all queries have been resolved
   - Provide summary of resolutions
   - Confirm ready for ingestion

**CRITICAL:**
- Only use exact tool names listed above
- Always present findings to user clearly
- Never skip audit query creation - every issue needs user review
- Don't proceed to next file until current file's issues are created
- When user says "resolve" or provides decision, call resolve_audit_query
- Organize findings by severity for easier review
"""

# Combine all instruction components
agent_instruction = f"""
{agent_role_and_goal}

{agent_hints}

{agent_chain_of_thought}
"""


# ============================================================================
# Tool List
# ============================================================================

agent_tools = [
    get_approved_user_goal,
    get_approved_construction_plan,
    get_approved_files,
    get_construction_plan_summary,
    scan_csv_for_duplicates,
    check_missing_required_fields,
    check_foreign_keys,
    create_audit_query,
    get_pre_ingestion_audit_queries,
    resolve_audit_query
]


# ============================================================================
# Agent Definition
# ============================================================================

pre_ingestion_audit_agent = LlmAgent(
    name="pre_ingestion_audit_agent_v1",
    description="Scans data files before ingestion to detect quality issues and create audit queries",
    model=llm,
    instruction=agent_instruction,
    tools=agent_tools
)

logger.info("Created Pre-Ingestion Audit Agent")

