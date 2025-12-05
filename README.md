# Setu Content Audit - Knowledge Graph System

A multi-agent system for building and auditing knowledge graphs, adapted from Neo4j course materials for art collection use cases.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Neo4j (choose one method):

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
   See `scripts/README_NEO4J_SETUP.md` for detailed instructions.

   **Option B: Neo4j Desktop**
   - Download from https://neo4j.com/download/
   - Install and create a new database
   - Start the database

3. Configure environment variables:
   - Copy `.env.example` to `.env` (if not already created)
   - Set `GEMINI_API_KEY` with your Gemini API key
   - Set Neo4j connection settings:
     ```
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USERNAME=neo4j
     NEO4J_PASSWORD=your_password
     NEO4J_DATABASE=neo4j
     ```

## Testing Individual Agents

Each agent has a Streamlit UI for interactive testing and debugging.

### User Intent Agent

Run the UI:
```bash
streamlit run tests/ui/test_user_intent_agent_ui.py
```

The UI provides:
- Interactive chat interface
- Session state viewer (for debugging)
- Verbose logging toggle
- Reset session functionality

## Project Structure

```
src/
├── agents/          # Agent implementations
├── tools/          # Tool definitions
├── pipeline/       # Pipeline orchestration
├── neo4j/          # Neo4j utilities
└── utils/           # Helper utilities

tests/
├── ui/             # Streamlit UI for testing agents
└── test_*.py       # Unit tests

data/
├── raw/            # Original test data
├── story1/         # Story 1 test data
└── story2/         # Story 2 test data

reference/
└── course/         # Course reference materials
```

## Development Workflow

1. Work on feature branches: `feature/course-setup/<agent-name>`
2. Test using Streamlit UI
3. Merge to `dev` when complete
4. Merge `dev` to `main` after integration testing

