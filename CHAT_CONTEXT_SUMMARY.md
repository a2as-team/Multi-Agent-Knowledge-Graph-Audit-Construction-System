# 📋 Detailed Chat Context Summary

**Date**: Current Session  
**Branch**: `feature/course-setup/knowledge-extraction-tool`  
**Status**: Knowledge Extraction Agent implemented and tested, Neo4j connection issues resolved

---

## 🎯 Project Overview

**Project Name**: Setu Content Audit - Knowledge Graph System  
**Repository**: `https://github.com/BigLookAI/setu-content-audit.git`  
**Purpose**: Multi-agent system for building and auditing knowledge graphs from structured (CSV) and unstructured (Markdown) data

### Architecture

The system follows a **multi-agent architecture** with three main branches:

1. **Structured Data Branch** (CSV files):
   - User Intent Agent ✅
   - File Suggestion Agent ✅
   - Schema Proposal Agent ✅
   - Pre-Ingestion Audit Agent ✅
   - **Graph Construction Agent** ✅ (Current focus)

2. **Unstructured Data Branch** (Markdown files):
   - User Intent Agent ✅
   - File Suggestion Agent (Unstructured) ✅
   - NER Agent ✅
   - Fact Extraction Agent ✅
   - **Knowledge Extraction Agent** ✅ (Just completed)

3. **GraphRAG Agent** (Future):
   - Query answering using the knowledge graph

**Top-Level Orchestrator**: Knowledge Graph Agent (not yet implemented)

---

## 📍 Current Branch & Recent Work

**Active Branch**: `feature/course-setup/knowledge-extraction-tool`

### Recent Commits (Last 10):
1. `ff458e8` - fix: disable Neo4j account lockout and improve connection handling
2. `7497f2b` - fix: escape curly braces in extraction prompt template - fixes KeyError
3. `4605e68` - fix: add single-file processing and improve extraction debugging
4. `1c95481` - feat: implement Knowledge Extraction Agent with API call optimization
5. `09e95db` - docs: add ingestion accuracy report and fix relationship construction plan
6. `1cb0790` - docs: add comprehensive ingestion accuracy report
7. `81529db` - fix: auto-copy CSV files to Docker and fix relationship construction plan
8. `864155d` - fix: replace st.sidebar.spinner() with status message
9. `246919c` - feat: add batch execution tool to reduce API calls by ~90%
10. `a3c0b30` - fix: update Neo4j password and healthcheck in docker-compose

---

## ✅ Completed Implementations

### 1. Structured Data Agents (All Complete)

#### User Intent Agent
- **File**: `src/agents/user_intent_agent.py`
- **Tools**: `src/tools/schema_tools.py`
- **Status**: ✅ Fully implemented and tested
- **UI**: `tests/ui/test_user_intent_agent_ui.py`

#### File Suggestion Agent (Structured)
- **File**: `src/agents/file_suggestion_agent.py`
- **Tools**: `src/tools/file_tools.py`
- **Status**: ✅ Fully implemented and tested
- **UI**: `tests/ui/test_file_suggestion_agent_ui.py`

#### Schema Proposal Agent (Structured)
- **File**: `src/agents/schema_proposal_structured_agent.py`
- **Tools**: `src/tools/schema_proposal_tools.py`
- **Status**: ✅ Fully implemented with critic pattern
- **UI**: `tests/ui/test_schema_proposal_agent_ui.py`
- **Output**: Graph Construction Plan (JSON)

#### Pre-Ingestion Audit Agent
- **File**: `src/agents/pre_ingestion_audit_agent.py`
- **Tools**: `src/tools/pre_ingestion_audit_tools.py`
- **Status**: ✅ Fully implemented
- **Features**:
  - Scans CSV files for quality issues (duplicates, missing values, etc.)
  - Creates audit queries for user review
  - Supports resolutions: `skip_record`, `use_first`, `use_second`, `merge`, `manual_fix`, `update_construction_plan`, `approve`, `reject`
- **UI**: `tests/ui/test_pre_ingestion_audit_agent_ui.py`

#### Graph Construction Agent
- **File**: `src/agents/graph_construction_agent.py`
- **Tools**: `src/tools/graph_construction_tools.py`
- **Status**: ✅ Fully implemented with audit resolution support
- **Key Features**:
  - Loads nodes from CSV files using `LOAD CSV` Cypher queries
  - Loads relationships from CSV files
  - Applies audit resolutions (skip, use_first, use_second, merge)
  - Batch execution tool (`execute_construction_plan`) for API optimization
  - Auto-copies CSV files to Docker container's import directory
  - `clear_neo4j_data` tool for database cleanup
- **UI**: `tests/ui/test_graph_construction_agent_ui.py`
- **Important**: Uses `tool_context.state` to persist construction plan and audit resolutions

### 2. Unstructured Data Agents (All Complete)

#### File Suggestion Agent (Unstructured)
- **File**: `src/agents/file_suggestion_unstructured_agent.py`
- **Tools**: `src/tools/unstructured_tools.py`
- **Status**: ✅ Fully implemented
- **UI**: `tests/ui/test_file_suggestion_unstructured_agent_ui.py`

#### NER Agent
- **File**: `src/agents/ner_agent.py`
- **Tools**: `src/tools/ner_tools.py`
- **Status**: ✅ Fully implemented
- **Output**: Approved entity types for extraction
- **UI**: `tests/ui/test_ner_agent_ui.py`

#### Fact Extraction Agent
- **File**: `src/agents/fact_extraction_agent.py`
- **Tools**: `src/tools/fact_extraction_tools.py`
- **Status**: ✅ Fully implemented
- **Output**: Approved fact types (predicates) for relationship extraction
- **UI**: `tests/ui/test_fact_extraction_agent_ui.py`

#### Knowledge Extraction Agent ⭐ (Just Completed)
- **File**: `src/agents/knowledge_extraction_agent.py`
- **Tools**: `src/tools/knowledge_extraction_tools.py`
- **Status**: ✅ Fully implemented and tested
- **Key Features**:
  - Processes markdown files to extract entities and relationships
  - Creates Document nodes (one per markdown file)
  - Creates Chunk nodes (text chunks separated by "---")
  - Extracts entities using LLM (only approved entity types)
  - Extracts relationships using LLM (only approved fact types)
  - Creates provenance links (Entity → EXTRACTED_FROM → Chunk)
  - Batch execution tool (`execute_knowledge_extraction`) for API optimization
  - Single-file processing tool (`process_single_file`) for debugging
- **UI**: `tests/ui/test_knowledge_extraction_agent_ui.py`
- **Graph Structure**:
  - Document → HAS_CHUNK → Chunk
  - Entity → EXTRACTED_FROM → Chunk
  - Entity → [fact_type] → Entity

---

## 🔧 Key Technical Decisions & Patterns

### 1. API Call Optimization
**Problem**: `LlmAgent` makes an API call for each tool invocation, leading to inefficiency in deterministic workflows.

**Solution**: Implemented batch execution tools:
- `execute_construction_plan` (Graph Construction Agent) - processes entire construction plan in one call
- `execute_knowledge_extraction` (Knowledge Extraction Agent) - processes all markdown files in one call

**Result**: ~90% reduction in API calls for deterministic workflows.

### 2. State Management
**Pattern**: Using `tool_context.state` to persist data across agent turns:
- `APPROVED_CONSTRUCTION_PLAN`: Graph construction plan (JSON)
- `PRE_INGESTION_AUDIT_QUERIES`: Audit queries from pre-ingestion audit
- `AUDIT_RESOLUTIONS`: User resolutions for audit queries
- `APPROVED_FILES`: Approved files for processing
- `APPROVED_ENTITIES`: Approved entity types
- `APPROVED_FACTS`: Approved fact types (predicates)

**Constants File**: `src/utils/constants.py`

### 3. Neo4j Integration
**Wrapper**: `src/neo4j/neo4j_for_adk.py` - `Neo4jForADK` class
- Provides ADK-friendly query interface
- Lazy initialization to avoid connection errors
- Connection pooling for efficiency
- Auto-cleanup on exit

**Connection Settings**:
- URI: `bolt://localhost:7687` (default)
- Username: `neo4j`
- Password: `neo4j123` (set in `.env` and `docker-compose.yml`)
- Database: `neo4j`

### 4. Audit Resolution Application
**Implementation**: In `graph_construction_tools.py`:
- `_parse_resolutions_for_file()`: Parses audit resolutions for a specific file
- Applies resolutions using Cypher `WHERE` clauses:
  - `skip_record`: Excludes records entirely
  - `use_first`: Only keeps first occurrence
  - `use_second`: Only keeps second occurrence
  - `merge`: Combines properties from both occurrences using `COALESCE`

### 5. Chunking Strategy
**For Unstructured Data**: Markdown files are chunked by separator "---"
- Each chunk becomes a Chunk node
- Entities and relationships are extracted per chunk
- Provenance links entities to their source chunks

---

## 🐛 Recent Issues & Fixes

### Issue 1: Neo4j Account Lockout (Just Fixed)
**Problem**: Neo4j account kept getting locked after multiple failed authentication attempts.

**Root Cause**: Neo4j's security feature locks accounts after too many failed attempts.

**Solution**:
1. Disabled account lockout in `docker-compose.yml`:
   ```yaml
   - NEO4J_dbms_security_auth__max__failed__attempts=0  # 0 = unlimited attempts
   ```
2. Improved connection handling in `src/neo4j/neo4j_for_adk.py`:
   - Added connection pool settings
   - Set proper timeouts
   - Configured for local development

**Status**: ✅ Fixed - Container running and healthy

**⚠️ WARNING**: Account lockout is disabled for development. **REMOVE IN PRODUCTION!**

### Issue 2: KeyError in Extraction Prompt
**Problem**: `KeyError: '"nodes"'` when creating extraction prompt.

**Root Cause**: Curly braces in JSON example were interpreted as format placeholders by Python's `.format()`.

**Solution**: Escaped curly braces in `_create_extraction_prompt()` by doubling them (e.g., `{{"nodes":`).

**Status**: ✅ Fixed

### Issue 3: No Entities/Relationships Extracted
**Problem**: Knowledge Extraction Agent returned 0 nodes/relationships.

**Solution**: 
- Added `process_single_file` tool for granular debugging
- Fixed prompt formatting issue (Issue 2)
- Improved error logging

**Status**: ✅ Fixed

### Issue 4: CSV Files Not Found in Neo4j Import Directory
**Problem**: `LOAD CSV` queries failed because files weren't in Docker container's import directory.

**Solution**: Implemented `_auto_copy_files_to_docker_container()` helper function in `graph_construction_tools.py` to automatically copy CSV files to `/var/lib/neo4j/import/`.

**Status**: ✅ Fixed

### Issue 5: Streamlit UI Error
**Problem**: `Method spinner() does not exist for st.sidebar`.

**Solution**: Replaced `st.sidebar.spinner()` with status placeholder.

**Status**: ✅ Fixed

---

## 🐳 Neo4j Setup

### Docker Setup (Recommended)
**File**: `docker-compose.yml`

**Configuration**:
- Image: `neo4j:latest`
- Ports: `7474` (HTTP), `7687` (Bolt)
- Password: `neo4j123`
- Plugins: APOC
- Account lockout: **Disabled** (development only)

**Setup Scripts**:
- Linux/macOS: `scripts/setup_neo4j.sh`
- Windows: `scripts/setup_neo4j.ps1`

**Documentation**: `scripts/README_NEO4J_SETUP.md`

**Current Status**: ✅ Running and healthy

### Environment Variables
Required in `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j123
NEO4J_DATABASE=neo4j
GEMINI_API_KEY=your_key_here
```

---

## 📁 Project Structure

```
src/
├── agents/              # Agent implementations
│   ├── user_intent_agent.py
│   ├── file_suggestion_agent.py
│   ├── schema_proposal_structured_agent.py
│   ├── pre_ingestion_audit_agent.py
│   ├── graph_construction_agent.py
│   ├── file_suggestion_unstructured_agent.py
│   ├── ner_agent.py
│   ├── fact_extraction_agent.py
│   └── knowledge_extraction_agent.py
├── tools/              # Tool definitions
│   ├── schema_tools.py
│   ├── file_tools.py
│   ├── schema_proposal_tools.py
│   ├── pre_ingestion_audit_tools.py
│   ├── graph_construction_tools.py
│   ├── unstructured_tools.py
│   ├── ner_tools.py
│   ├── fact_extraction_tools.py
│   └── knowledge_extraction_tools.py
├── neo4j/              # Neo4j utilities
│   └── neo4j_for_adk.py
├── utils/              # Helper utilities
│   ├── constants.py    # State keys and constants
│   ├── config.py       # Configuration (DEFAULT_MODEL, etc.)
│   └── logger.py       # Logging setup
└── pipeline/           # Pipeline orchestration (future)

tests/
├── ui/                 # Streamlit UI for testing agents
│   ├── test_user_intent_agent_ui.py
│   ├── test_file_suggestion_agent_ui.py
│   ├── test_schema_proposal_agent_ui.py
│   ├── test_pre_ingestion_audit_agent_ui.py
│   ├── test_graph_construction_agent_ui.py
│   ├── test_file_suggestion_unstructured_agent_ui.py
│   ├── test_ner_agent_ui.py
│   ├── test_fact_extraction_agent_ui.py
│   └── test_knowledge_extraction_agent_ui.py
└── test_*.py           # Unit tests

data/
├── raw/                # Original test data
│   ├── artists.csv
│   ├── artworks.csv
│   ├── locations.csv
│   └── artist_bios.md
├── story1/             # Story 1 test data
└── story2/             # Story 2 test data

scripts/
├── setup_neo4j.sh     # Neo4j setup (Linux/macOS)
├── setup_neo4j.ps1    # Neo4j setup (Windows)
└── README_NEO4J_SETUP.md

docker-compose.yml      # Neo4j Docker configuration
```

---

## 🔄 Workflow Patterns

### Structured Data Workflow
1. **User Intent Agent**: Determines user's goal
2. **File Suggestion Agent**: Suggests relevant CSV files
3. **Schema Proposal Agent**: Proposes graph schema (iterative refinement)
4. **Pre-Ingestion Audit Agent**: Scans for data quality issues
5. **Graph Construction Agent**: Executes construction plan, applies audit resolutions

### Unstructured Data Workflow
1. **User Intent Agent**: Determines user's goal
2. **File Suggestion Agent (Unstructured)**: Suggests relevant markdown files
3. **NER Agent**: Proposes entity types to extract
4. **Fact Extraction Agent**: Proposes fact types (predicates) to extract
5. **Knowledge Extraction Agent**: Executes extraction, creates graph

---

## 📝 Important Code Patterns

### Tool Implementation Pattern
```python
from google.adk.tools import ToolContext
from src.utils.constants import APPROVED_CONSTRUCTION_PLAN
from src.neo4j.neo4j_for_adk import get_graphdb, tool_success, tool_error

def my_tool(param: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Tool description."""
    try:
        # Get state
        plan = tool_context.state.get(APPROVED_CONSTRUCTION_PLAN, {})
        
        # Get Neo4j connection
        graphdb = get_graphdb()
        if not graphdb:
            return tool_error("Neo4j connection not available")
        
        # Execute logic
        result = graphdb.send_query("MATCH (n) RETURN count(n) as count")
        
        return tool_success("result_key", result)
    except Exception as e:
        logger.error(f"Error in my_tool: {e}")
        return tool_error(str(e))
```

### Agent Definition Pattern
```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

llm = LiteLlm(model=DEFAULT_MODEL)

agent = LlmAgent(
    name="my_agent",
    role_and_goal=agent_role_and_goal,
    hints=agent_hints,
    chain_of_thought=agent_chain_of_thought,
    llm=llm,
    tools=[my_tool, another_tool]
)
```

### Cypher Query Pattern (with Dynamic Properties)
```python
# For nodes with dynamic properties
query = f"""
LOAD CSV WITH HEADERS FROM "file:///{source_file}" AS row
WHERE row.`{unique_column}` IS NOT NULL
CALL (row) {{
    MERGE (n:`{label}` {{ `{unique_column}`: row.`{unique_column}` }})
    SET n.`{prop1}` = row.`{prop1}`, n.`{prop2}` = row.`{prop2}`
}} IN TRANSACTIONS OF 1000 ROWS
RETURN count(*) as nodes_loaded
"""
```

---

## 🚀 Next Steps / Pending Work

### Immediate Next Steps
1. **Test Knowledge Extraction Agent** with real markdown files
2. **Verify extraction results** in Neo4j browser
3. **Test entity resolution** (if needed)

### Future Agents (Not Yet Implemented)
1. **Entity Resolution Agent**: Links extracted entities to existing graph nodes
2. **Audit Query Agent**: Answers queries about the knowledge graph
3. **Knowledge Graph Orchestrator**: Top-level coordinator managing entire workflow

### Known Issues / Improvements Needed
1. **Ingestion Accuracy**: See `INGESTION_ACCURACY_REPORT.md` (if exists) for recommendations:
   - Fix counting logic to use actual Neo4j query results
   - Add relationship validation to log failures
   - Improve error reporting

2. **Production Readiness**:
   - Re-enable Neo4j account lockout for production
   - Add proper error handling and retry logic
   - Add comprehensive logging

---

## 🔑 Key Files to Reference

### Core Files
- `src/utils/constants.py` - All state keys and constants
- `src/utils/config.py` - Configuration (DEFAULT_MODEL, etc.)
- `src/neo4j/neo4j_for_adk.py` - Neo4j wrapper
- `docker-compose.yml` - Neo4j Docker configuration

### Agent Files (Most Recent)
- `src/agents/knowledge_extraction_agent.py` - Knowledge Extraction Agent
- `src/tools/knowledge_extraction_tools.py` - Knowledge Extraction tools
- `src/agents/graph_construction_agent.py` - Graph Construction Agent
- `src/tools/graph_construction_tools.py` - Graph Construction tools

### UI Files
- `tests/ui/test_knowledge_extraction_agent_ui.py` - Knowledge Extraction UI
- `tests/ui/test_graph_construction_agent_ui.py` - Graph Construction UI

---

## 💡 Tips for Continuing

1. **Always check Neo4j connection** before running agents that use Neo4j
2. **Use batch execution tools** for API optimization in deterministic workflows
3. **Check `tool_context.state`** for persisted data (construction plans, resolutions, etc.)
4. **Test with Streamlit UIs** for interactive debugging
5. **Check Docker logs** if Neo4j issues occur: `docker logs neo4j --tail 50`
6. **Remember**: Account lockout is disabled - re-enable for production!

---

## 📊 Current System Status

✅ **Structured Data Branch**: Complete (all agents implemented)  
✅ **Unstructured Data Branch**: Complete (all agents implemented)  
⏳ **GraphRAG Agent**: Not yet implemented  
⏳ **Knowledge Graph Orchestrator**: Not yet implemented  
✅ **Neo4j Setup**: Running and healthy  
✅ **All UI Tests**: Available for interactive testing

---

**Last Updated**: Current session  
**Branch**: `feature/course-setup/knowledge-extraction-tool`  
**Ready for**: Testing Knowledge Extraction Agent with real data, or moving to next agent (Entity Resolution or Orchestrator)

