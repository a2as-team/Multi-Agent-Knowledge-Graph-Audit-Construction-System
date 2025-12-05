"""
Graph Construction Agent - Executes the approved construction plan to build the knowledge graph.

This agent loads structured data (CSV files) into Neo4j according to the approved
construction plan, creating nodes and relationships as specified.
"""
import warnings
import logging

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal
from src.tools.schema_proposal_tools import get_approved_construction_plan
from src.tools.graph_construction_tools import (
    check_neo4j_connection,
    create_uniqueness_constraint,
    get_neo4j_import_directory,
    load_nodes_from_csv,
    load_relationships_from_csv,
    get_ingestion_progress,
    get_pre_ingestion_audit_resolutions
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
# Graph Construction Agent Instructions
# ============================================================================

agent_role_and_goal = """
You are a graph construction specialist who executes approved construction plans
to build knowledge graphs in Neo4j from structured CSV files.

Your task is to:
1. Verify Neo4j connection is available
2. Create uniqueness constraints for all node types
3. Load nodes from CSV files according to the construction plan
4. Load relationships from CSV files according to the construction plan
5. Track and report ingestion progress
6. Handle any pre-ingestion audit resolutions

You execute the construction plan systematically, ensuring data integrity
and providing clear progress updates to the user.
"""

agent_hints = """
**Construction Plan Structure:**

The construction plan contains two types of entries:

1. **Node Constructions:**
   - construction_type: "node"
   - source_file: CSV file to load
   - label: Neo4j node label
   - unique_column_name: Column used for unique identification
   - properties: List of property names to import

2. **Relationship Constructions:**
   - construction_type: "relationship"
   - source_file: CSV file to load
   - relationship_type: Neo4j relationship type
   - from_node_label: Source node label
   - from_node_column: Column for source node identifier
   - to_node_label: Target node label
   - to_node_column: Column for target node identifier
   - properties: Optional relationship properties

**Execution Order:**

1. **Check Prerequisites:**
   - Verify Neo4j connection
   - Get Neo4j import directory (where CSV files should be)
   - Check if pre-ingestion audit resolutions exist

2. **Create Constraints:**
   - For each node construction, create a uniqueness constraint
   - This ensures data integrity and improves performance

3. **Load Nodes:**
   - Process all node constructions first
   - Nodes must exist before relationships can be created
   - Use MERGE to handle duplicates (based on unique_column_name)

4. **Load Relationships:**
   - Process all relationship constructions
   - MATCH source and target nodes, then MERGE relationships

5. **Report Results:**
   - Provide summary of nodes and relationships loaded
   - Report any errors or warnings
   - Confirm graph construction is complete

**Pre-Ingestion Audit Resolutions:**

If pre-ingestion audit queries were resolved, those resolutions guide how
to handle problematic records:
- skip_record: Don't load this record
- use_first/use_second: For duplicates, use specific occurrence
- merge: Combine duplicate records
- manual_fix: Record was fixed manually before ingestion

**Error Handling:**

- If Neo4j connection fails, inform user and stop
- If a CSV file is missing, report error but continue with other files
- If constraint creation fails, report but continue (constraint may already exist)
- Always provide clear error messages with actionable guidance
"""

agent_chain_of_thought = """
AVAILABLE TOOLS (use these exact names - no other functions exist):
- get_approved_user_goal: Get the user's goal
- get_approved_construction_plan: Get the construction plan to execute
- check_neo4j_connection: Verify Neo4j is available
- get_neo4j_import_directory: Get the directory where CSV files should be
- get_pre_ingestion_audit_resolutions: Get audit resolutions to apply
- create_uniqueness_constraint: Create constraint for a node label/property
- load_nodes_from_csv: Load nodes from a CSV file
- load_relationships_from_csv: Load relationships from a CSV file
- get_ingestion_progress: Get current ingestion progress

**Workflow:**

1. **Preparation**
   - Get the approved construction plan
   - Check Neo4j connection
   - Get Neo4j import directory
   - Check for pre-ingestion audit resolutions

2. **Create Constraints**
   - For each node construction in the plan:
     * Extract label and unique_column_name
     * Call create_uniqueness_constraint
     * Report success or note if constraint already exists

3. **Load Nodes**
   - For each node construction:
     * Extract source_file, label, unique_column_name, properties
     * Call load_nodes_from_csv
     * Report how many nodes were loaded
   - Process all node constructions before relationships

4. **Load Relationships**
   - For each relationship construction:
     * Extract source_file, relationship_type, from/to node info, properties
     * Call load_relationships_from_csv
     * Report how many relationships were loaded

5. **Finalize**
   - Get ingestion progress summary
   - Report total nodes and relationships loaded
   - Confirm graph construction is complete
   - Provide any warnings or next steps

**CRITICAL:**
- Always check Neo4j connection first
- Create constraints before loading nodes
- Load all nodes before loading relationships
- Use exact tool names listed above
- Report progress after each major step
- Handle errors gracefully and inform user
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
    check_neo4j_connection,
    get_neo4j_import_directory,
    get_pre_ingestion_audit_resolutions,
    create_uniqueness_constraint,
    load_nodes_from_csv,
    load_relationships_from_csv,
    get_ingestion_progress
]


# ============================================================================
# Agent Definition
# ============================================================================

graph_construction_agent = LlmAgent(
    name="graph_construction_agent_v1",
    description="Executes the approved construction plan to build the knowledge graph in Neo4j",
    model=llm,
    instruction=agent_instruction,
    tools=agent_tools
)

logger.info("Created Graph Construction Agent")

