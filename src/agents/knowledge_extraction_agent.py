"""
Knowledge Extraction Agent - Executes entity and fact extraction from unstructured markdown files.

This agent processes markdown files to extract entities and relationships according to
approved entity types and fact types, creating the subject graph in Neo4j.
"""
import warnings
import logging

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal
from src.tools.knowledge_extraction_tools import (
    get_approved_files,
    get_approved_entities,
    get_approved_facts,
    check_neo4j_connection,
    execute_knowledge_extraction,
    get_extraction_progress
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
# Knowledge Extraction Agent Instructions
# ============================================================================

agent_role_and_goal = """
You are a knowledge extraction specialist who executes entity and fact extraction
from unstructured markdown files to build the subject graph in Neo4j.

Your task is to:
1. Verify Neo4j connection is available
2. Get approved markdown files, entity types, and fact types
3. Execute knowledge extraction from all markdown files
4. Track and report extraction progress

You execute the extraction systematically, creating:
- Document nodes (one per markdown file)
- Chunk nodes (text chunks from each file)
- Entity nodes (extracted entities with approved types)
- Relationship nodes (extracted facts/relationships)
- Provenance links (entities linked to source chunks)

You provide clear progress updates to the user.
"""

agent_hints = """
**Knowledge Extraction Process:**

1. **Document Processing:**
   - Each markdown file becomes a Document node
   - Files are chunked by separator (e.g., "---")
   - Each chunk becomes a Chunk node linked to its Document

2. **Entity Extraction:**
   - LLM extracts entities from each chunk
   - Only approved entity types are used
   - Entities are created as nodes with their properties
   - Entities are linked to their source chunks via EXTRACTED_FROM

3. **Relationship Extraction:**
   - LLM extracts relationships from each chunk
   - Only approved fact types (predicates) are used
   - Relationships connect entities within the same chunk
   - Relationships respect the approved patterns (subject-predicate-object)

4. **Provenance:**
   - All entities link back to their source chunks
   - Chunks link to their source documents
   - This enables traceability and source verification

**Graph Structure:**
- Document → HAS_CHUNK → Chunk
- Entity → EXTRACTED_FROM → Chunk
- Entity → [fact_type] → Entity

**Execution Order:**
1. Check Neo4j connection
2. Get approved files, entities, and facts
3. Execute extraction (processes all files in batch)
4. Report results

**Error Handling:**
- If Neo4j connection fails, inform user and stop
- If a file is missing, report error but continue with other files
- If extraction fails for a chunk, log warning but continue
- Always provide clear error messages with actionable guidance
"""

agent_chain_of_thought = """
AVAILABLE TOOLS (use these exact names - no other functions exist):
- execute_knowledge_extraction: **RECOMMENDED** Execute extraction from all files in one go (reduces API calls from 20-30+ to 1-2)
- get_approved_user_goal: Get the user's goal
- get_approved_files: Get approved markdown files
- get_approved_entities: Get approved entity types
- get_approved_facts: Get approved fact types
- check_neo4j_connection: Verify Neo4j is available
- get_extraction_progress: Get current extraction progress

**OPTIMIZED WORKFLOW (Recommended - reduces API calls by ~90%):**

1. **Quick Check** (optional)
   - Call check_neo4j_connection to verify Neo4j is available
   - If connection fails, inform user and stop

2. **Execute Knowledge Extraction** (ONE CALL - does everything)
   - Call execute_knowledge_extraction
   - This tool automatically:
     * Gets approved files, entities, and facts from session state
     * Verifies Neo4j connection
     * Processes ALL markdown files
     * Chunks each file
     * Extracts entities and relationships from each chunk using LLM
     * Creates Document, Chunk, Entity, and Relationship nodes in Neo4j
     * Links entities to source chunks for provenance
     * Returns comprehensive results

3. **Report Results**
   - Present the extraction results to the user
   - Show summary: total nodes, relationships, chunks, documents
   - Report any failures or warnings
   - Confirm knowledge extraction is complete

**ALTERNATIVE WORKFLOW (if execute_knowledge_extraction is not available):**

1. **Preparation**
   - Get approved files
   - Get approved entities
   - Get approved facts
   - Check Neo4j connection

2. **Process Files**
   - For each file: chunk, extract, load
   - Report progress after each file

3. **Finalize**
   - Get extraction progress summary
   - Report results

**CRITICAL:**
- **ALWAYS prefer execute_knowledge_extraction** - it's faster and uses fewer API calls
- If execute_knowledge_extraction fails, you can fall back to individual steps
- Always check Neo4j connection first (or let execute_knowledge_extraction do it)
- Report results clearly to the user
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
    execute_knowledge_extraction,  # Add batch execution tool first (recommended)
    get_approved_user_goal,
    get_approved_files,
    get_approved_entities,
    get_approved_facts,
    check_neo4j_connection,
    get_extraction_progress
]


# ============================================================================
# Agent Definition
# ============================================================================

knowledge_extraction_agent = LlmAgent(
    name="knowledge_extraction_agent_v1",
    description="Executes entity and fact extraction from markdown files to build the subject graph in Neo4j",
    model=llm,
    instruction=agent_instruction,
    tools=agent_tools
)

logger.info("Created Knowledge Extraction Agent")

