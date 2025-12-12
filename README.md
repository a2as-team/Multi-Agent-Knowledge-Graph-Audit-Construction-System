# Multi-Agent Knowledge Graph Audit & Construction System

A comprehensive multi-agent system I developed for building and auditing knowledge graphs from both structured (CSV) and unstructured (Markdown) data sources. This system leverages Google's Agent Development Kit (ADK) with LLM-powered agents to automate the entire knowledge graph lifecycle—from schema design to data validation and entity resolution.

## 🎯 Project Overview

This system addresses the challenge of building validated, auditable knowledge graphs by orchestrating 13 specialized agents that work together to:

- **Automate Schema Design**: Intelligently propose graph schemas from CSV files using LLM-powered analysis
- **Validate Data Quality**: Pre-ingestion validation to catch issues before graph construction
- **Extract Knowledge**: Extract entities and relationships from unstructured text documents
- **Resolve Entities**: Match extracted entities to domain graph nodes using fuzzy matching algorithms
- **Maintain Audit Trails**: Complete tracking of all decisions and modifications for compliance

## ✨ Key Features

### Two-Stage Audit Review System
- **Stage 1 (Blocking)**: Pre-ingestion queries must be resolved before graph construction
- **Stage 2 (Non-Blocking)**: Entity resolution and post-ingestion queries reviewed together at the end
- Ensures data quality while maintaining workflow efficiency

### Multi-Agent Architecture
- **13 Specialized Agents**: Each agent handles a specific aspect of the knowledge graph lifecycle
- **Intelligent Orchestration**: Agents work together with state management and dependency tracking
- **User Verification**: Every critical decision requires user approval before execution

### Dual Data Source Support
- **Structured Data (CSV)**: Automated schema proposal and domain graph construction
- **Unstructured Data (Markdown)**: Entity extraction and subject graph creation
- **Entity Resolution**: Automatic matching between domain and subject graphs

### Complete Audit Trail
- Track all audit queries, resolutions, and graph modifications
- Maintain provenance links from extracted entities to source documents
- Generate comprehensive audit reports

## 🏗️ System Architecture

The system follows a 9-phase workflow:

1. **Planning & Schema Definition**: User intent, file selection, schema proposal
2. **Data Quality Rules**: Custom rule definition for validation
3. **Pre-Ingestion Validation**: Data quality scanning (blocking)
4. **Knowledge Graph Construction**: Domain graph (CSV) and Subject/Lexical graphs (Markdown)
5. **Entity Resolution**: Matching extracted entities to domain nodes
6. **Post-Ingestion Validation**: Quality rule validation
7. **Unified Audit Review**: Review all pending queries together
8. **Query Execution**: Apply approved resolutions to the graph
9. **Final Audit Report**: Comprehensive report generation

See `proposed_architecture.md` for detailed architecture documentation.

## 🛠️ Technology Stack

- **Framework**: Google ADK (Agent Development Kit) 1.5.0
- **LLM**: Gemini 2.5 Flash via LiteLLM 1.73.6
- **Database**: Neo4j 5.28.1
- **UI Framework**: Streamlit 1.39.0
- **String Matching**: RapidFuzz 3.13.0
- **Language**: Python 3.13

## 📦 Installation & Setup

### Prerequisites

- Python 3.13+
- Neo4j 5.x (via Docker or Desktop)
- Gemini API key

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/codergoel/Multi-Agent-Knowledge-Graph-Audit-Construction-System.git
   cd Multi-Agent-Knowledge-Graph-Audit-Construction-System
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Neo4j** (choose one method):

   **Option A: Docker (Recommended)**
   ```bash
   # Linux/macOS
   chmod +x scripts/setup_neo4j.sh
   ./scripts/setup_neo4j.sh
   
   # Windows (PowerShell)
   .\scripts\setup_neo4j.ps1
   
   # Or use Docker Compose
   docker-compose up -d
   ```

   **Option B: Neo4j Desktop**
   - Download from https://neo4j.com/download/
   - Install and create a new database
   - Start the database

4. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j
   ```

## 🚀 Usage

### Testing Individual Agents

Each agent has a dedicated Streamlit UI for interactive testing:

```bash
# User Intent Agent
streamlit run tests/ui/test_user_intent_agent_ui.py

# Schema Proposal Agent
streamlit run tests/ui/test_schema_proposal_agent_ui.py

# Entity Resolution Agent
streamlit run tests/ui/test_entity_resolution_agent_ui.py

# Pre-Ingestion Audit Agent
streamlit run tests/ui/test_pre_ingestion_audit_agent_ui.py

# Graph Construction Agent
streamlit run tests/ui/test_graph_construction_agent_ui.py

# Knowledge Extraction Agent
streamlit run tests/ui/test_knowledge_extraction_agent_ui.py

# ... and more (see tests/ui/ directory)
```

### Unified Workflow

Run the complete unified workflow UI:

```bash
streamlit run tests/ui/unified_workflow_ui.py
```

This provides a single interface to orchestrate all agents sequentially through the complete workflow.

### Architecture Visualization

View interactive architecture diagrams:

```bash
# Open in browser
tests/ui/architecture_diagram.html          # High-level overview
tests/ui/architecture_diagram_detailed.html # Detailed agent-level flow
```

## 📁 Project Structure

```
├── src/
│   ├── agents/              # 13 agent implementations
│   │   ├── user_intent_agent.py
│   │   ├── file_suggestion_agent.py
│   │   ├── schema_proposal_structured_agent.py
│   │   ├── ner_agent.py
│   │   ├── fact_extraction_agent.py
│   │   ├── data_quality_rules_agent.py
│   │   ├── pre_ingestion_audit_agent.py
│   │   ├── graph_construction_agent.py
│   │   ├── knowledge_extraction_agent.py
│   │   ├── entity_resolution_agent.py
│   │   └── ...
│   ├── tools/               # Tool definitions for agents
│   │   ├── file_tools.py
│   │   ├── schema_proposal_tools.py
│   │   ├── graph_construction_tools.py
│   │   ├── entity_resolution_tools.py
│   │   └── ...
│   ├── neo4j/               # Neo4j integration utilities
│   │   ├── neo4j_for_adk.py
│   │   └── cypher_templates.py
│   ├── pipeline/            # Pipeline orchestration
│   │   ├── orchestrator.py
│   │   ├── graph_constructor.py
│   │   └── entity_linker.py
│   └── utils/               # Configuration and helpers
│       ├── config.py
│       ├── constants.py
│       ├── helper.py
│       └── logger.py
├── tests/
│   ├── ui/                  # Streamlit test UIs
│   │   ├── test_*_agent_ui.py
│   │   ├── unified_workflow_ui.py
│   │   └── architecture_diagram*.html
│   └── test_*.py            # Unit tests
├── data/
│   ├── raw/                 # Original test data
│   ├── story1/              # Story 1 test data
│   └── story2/              # Story 2 test data
├── scripts/                 # Setup and utility scripts
│   ├── setup_neo4j.sh
│   ├── setup_neo4j.ps1
│   └── check_neo4j_data.py
└── docs/                    # Documentation
    ├── IMPLEMENTATION_STATUS.md
    ├── KNOWN_ISSUES.md
    └── OLLAMA_SETUP.md
```

## 🔧 Key Components

### Agents

- **User Intent Agent**: Captures and structures user goals for knowledge graph construction
- **File Suggestion Agents**: Recommends relevant CSV/Markdown files for processing
- **Schema Proposal Agent**: Proposes graph schemas using critic pattern with iterative refinement
- **NER Agent**: Identifies entity types to extract from unstructured data
- **Fact Extraction Agent**: Proposes relationship types (subject-predicate-object triples)
- **Data Quality Rules Agent**: Generates custom validation rules based on requirements
- **Pre-Ingestion Audit Agent**: Scans CSV files for data quality issues before ingestion
- **Graph Construction Agent**: Builds domain graph from CSV files with resolution support
- **Knowledge Extraction Agent**: Extracts entities and relationships from Markdown documents
- **Entity Resolution Agent**: Matches extracted entities to domain nodes using fuzzy matching
- **Post-Ingestion Audit Agent**: Validates complete graph against quality rules
- **Audit Query Execution Agent**: Applies approved resolutions to the graph

### Tools

Each agent has specialized tools for:
- **File Operations**: List, sample, and search files
- **Schema Operations**: Propose, critique, and approve schemas
- **Graph Operations**: Create nodes, relationships, and constraints
- **Audit Operations**: Create queries, resolve issues, execute resolutions
- **Entity Resolution**: Find matches, correlate keys, create audit queries

## 🎓 Use Cases

While initially designed for art collection provenance tracking, the system is generic and can be adapted to any knowledge graph use case:

- **Supply Chain Management**: Track suppliers, products, and relationships
- **Social Networks**: Map relationships and connections
- **Recommendation Systems**: Build product/customer graphs
- **Fraud Detection**: Analyze transaction patterns
- **Research Knowledge Graphs**: Connect papers, authors, and concepts
- **Healthcare**: Link patients, treatments, and outcomes
- **E-commerce**: Product catalogs and customer behavior

## 📊 Features in Detail

### Intelligent Schema Proposal
- Analyzes CSV structure to propose optimal graph schema
- Uses critic pattern for iterative refinement
- Handles complex relationships and constraints
- Validates schema completeness and connectivity

### Pre-Ingestion Validation
- Detects duplicate unique identifiers
- Identifies missing required fields
- Validates foreign key references
- Checks data type mismatches
- Blocks ingestion until issues are resolved

### Entity Resolution
- Uses Jaro-Winkler distance for fuzzy matching
- Correlates property keys between entities and domain nodes
- Creates audit queries for user review
- Configurable similarity thresholds (default: 0.7 for entities, 0.8 for keys)
- Maintains provenance links to source documents

### Audit Trail
- Complete history of all decisions
- Links extracted entities to source documents via EXTRACTED_FROM relationships
- Tracks all graph modifications
- Generates comprehensive reports
- Maintains timestamps and user notes

## 🔄 Workflow Example

1. **User Intent**: "I want to build a knowledge graph for art collection provenance"
2. **File Selection**: System suggests relevant CSV and Markdown files
3. **Schema Proposal**: Agent proposes graph structure (Artists, Artworks, Locations, etc.)
4. **Pre-Ingestion Audit**: System scans for duplicate IDs, missing fields, invalid FKs
5. **User Resolution**: User resolves all pre-ingestion issues
6. **Graph Construction**: Domain graph built from CSV with resolutions applied
7. **Knowledge Extraction**: Entities and relationships extracted from Markdown
8. **Entity Resolution**: System matches extracted entities to domain nodes
9. **Post-Ingestion Audit**: Validates graph against quality rules
10. **Unified Review**: User reviews all entity and post-ingestion queries
11. **Execution**: Approved resolutions applied to graph
12. **Final Report**: Comprehensive audit report generated

## 🐛 Known Issues & Limitations

- Free tier Gemini API has rate limits (10 requests/minute)
- System implements retry logic with exponential backoff
- Some Cypher queries use deprecated `id()` function (migration to `elementId()` planned)
- State key collision between pre-ingestion and entity/post-ingestion resolutions (planned fix)

See `docs/KNOWN_ISSUES.md` for detailed information.

## 📝 Development

### Branching Strategy

- `main`: Production-ready code
- `dev`: Integration branch
- `feature/*`: Feature development branches

### Contributing

1. Create a feature branch from `dev`
2. Implement and test your changes
3. Submit a pull request to `dev`

### Testing

- Each agent has a dedicated Streamlit UI for interactive testing
- Manual test cases documented in `tests/MANUAL_TESTS.md`
- Benchmarks available in `tests/benchmarks/`

## 🔐 Environment Variables

Required:
- `GEMINI_API_KEY`: Your Gemini API key
- `NEO4J_URI`: Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USERNAME`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password

Optional:
- `NEO4J_DATABASE`: Database name (default: `neo4j`)
- `NEO4J_IMPORT_DIR`: Import directory path

## 📚 Documentation

- **Architecture**: `proposed_architecture.md` - Complete system architecture
- **Implementation Status**: `docs/IMPLEMENTATION_STATUS.md` - Agent completion status
- **Known Issues**: `docs/KNOWN_ISSUES.md` - Known bugs and solutions
- **Unified Workflow**: `tests/ui/README_UNIFIED_WORKFLOW.md` - Workflow UI guide
- **Architecture Diagrams**: `tests/ui/README_ARCHITECTURE_DIAGRAM.md` - Visualization guide

## 🚧 Roadmap

- [ ] Migrate Cypher queries from `id()` to `elementId()`
- [ ] Separate state keys for different resolution types
- [ ] Implement comprehensive unit test suite
- [ ] Add CI/CD pipeline
- [ ] Performance optimization for large datasets
- [ ] Enhanced error recovery mechanisms

## 📄 License

[Add your license here]

## 👤 Author

Developed by [Your Name]

## 🙏 Acknowledgments

- Google ADK for the agent framework
- Neo4j for graph database technology
- Gemini API for LLM capabilities
- Streamlit for the UI framework

## 📞 Contact

[Add your contact information]

---

For detailed technical documentation, see the comprehensive technical context document and `proposed_architecture.md`.

