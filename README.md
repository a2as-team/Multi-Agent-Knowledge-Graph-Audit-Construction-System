# Setu Content Audit - Knowledge Graph System

A multi-agent system for building and auditing knowledge graphs, adapted from Neo4j course materials for art collection use cases.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `.env.example` to `.env` (if not already created)
   - Set `GEMINI_API_KEY` with your Gemini API key
   - Configure Neo4j connection settings if needed

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

