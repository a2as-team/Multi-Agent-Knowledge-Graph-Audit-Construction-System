# Unified Workflow UI

## Overview

The Unified Workflow UI (`unified_workflow_ui.py`) orchestrates all agents in a sequential workflow according to the proposed architecture. It provides a single interface to run the complete knowledge graph construction and validation pipeline.

## Features

- **Sequential Phase Execution**: Run phases in order with automatic prerequisite checking
- **State Persistence**: State is automatically shared between phases and agents
- **Individual Agent Control**: Initialize and interact with each agent separately
- **Blocking Phase Detection**: Visual indicators for phases that block subsequent phases
- **Pre-Ingestion Query Resolution**: Built-in dashboard for resolving pre-ingestion audit queries
- **Progress Tracking**: Visual status indicators for each phase
- **Chat Interface**: Natural language interaction with each agent

## Running the UI

```bash
streamlit run tests/ui/unified_workflow_ui.py
```

## Workflow Phases

### Phase 1: Planning & Schema Definition
1. **User Intent Agent** - Extract structured goal from natural language
2. **File Suggestion (Structured)** - Suggest relevant CSV files
3. **Schema Proposal** - Propose graph schema from CSV files
4. **File Suggestion (Unstructured)** - Suggest relevant markdown files
5. **NER Agent** - Propose entity types to extract
6. **Fact Extraction** - Propose relationship types to extract

### Phase 2: Data Quality Rules Definition
1. **Data Quality Rules Agent** - Define custom validation rules

### Phase 3: Pre-Ingestion Validation (BLOCKING)
1. **Pre-Ingestion Audit Agent** - Scan files for data quality issues
   - **Note**: This phase blocks Phase 4 until all audit queries are resolved

### Phase 4: Knowledge Graph Construction
1. **KG Construction (Domain Graph)** - Build domain graph from CSV files
2. **KG Construction (Subject/Lexical)** - Extract entities and relationships from markdown

## Usage Guide

### Step 1: Initialize Agents
For each phase, click the "Initialize" button for each agent you want to use.

### Step 2: Interact with Agents
- Use the chat interface to interact with agents naturally
- Use quick action buttons for common tasks:
  - **Pre-Ingestion Audit**: "Scan Files for Issues"
  - **Graph Construction**: "Execute Construction Plan"
  - **Knowledge Extraction**: "Extract Knowledge from Markdown"

### Step 3: Resolve Pre-Ingestion Queries
When Phase 3 generates audit queries:
1. Review queries in the Pre-Ingestion Audit Queries dashboard
2. Click resolution buttons (Skip Record, Use First, Merge, etc.)
3. All queries must be resolved before Phase 4 can proceed

### Step 4: Mark Phases Complete
After completing all agents in a phase, click "Mark Phase X as Completed" to update the workflow status.

## State Management

The UI automatically manages state between phases:
- **APPROVED_USER_GOAL**: From Phase 1, Agent 1
- **APPROVED_FILES**: From Phase 1, Agents 2 & 4
- **APPROVED_CONSTRUCTION_PLAN**: From Phase 1, Agent 3
- **APPROVED_ENTITIES**: From Phase 1, Agent 5
- **APPROVED_FACTS**: From Phase 1, Agent 6
- **APPROVED_QUALITY_RULES**: From Phase 2
- **PRE_INGESTION_AUDIT_QUERIES**: From Phase 3
- **AUDIT_RESOLUTIONS**: From Phase 3 (resolutions)
- **INGESTION_AUDIT_TRAIL**: From Phase 4

## Prerequisites

Each phase checks for required state keys before allowing execution:
- **Phase 2** requires: `APPROVED_CONSTRUCTION_PLAN`, `APPROVED_ENTITIES`, `APPROVED_FACTS`
- **Phase 3** requires: `APPROVED_CONSTRUCTION_PLAN`
- **Phase 4** requires: `APPROVED_CONSTRUCTION_PLAN` and all pre-ingestion queries resolved

## Example Workflow

1. **Phase 1 - User Intent**: "I want to build a knowledge graph for art collection provenance"
2. **Phase 1 - File Suggestion (Structured)**: Approve suggested CSV files
3. **Phase 1 - Schema Proposal**: Review and approve construction plan
4. **Phase 1 - File Suggestion (Unstructured)**: Approve markdown files
5. **Phase 1 - NER Agent**: Approve entity types
6. **Phase 1 - Fact Extraction**: Approve fact types
7. **Phase 2 - Data Quality Rules**: Define validation rules
8. **Phase 3 - Pre-Ingestion Audit**: Scan files and resolve all queries
9. **Phase 4 - Graph Construction**: Build the knowledge graph

## Tips

- **Sequential Execution**: Always run phases in order
- **State Persistence**: State is automatically shared - no manual copying needed
- **Blocking Phases**: Phase 3 blocks Phase 4 - resolve all queries first
- **Verbose Logging**: Enable in sidebar for detailed agent interactions
- **Reset**: Use "Reset All" button to start fresh

## Architecture Alignment

This UI implements the workflow described in `proposed_architecture.md`:
- Two-stage resolution (pre-ingestion blocking, entity/post-ingestion unified)
- State persistence across phases
- Prerequisite checking
- Blocking phase detection

## Future Phases

The UI is designed to easily add:
- **Phase 5**: Entity Resolution Audit
- **Phase 6**: Post-Ingestion Validation
- **Phase 7**: Unified Audit Review
- **Phase 8**: Query Execution
- **Phase 9**: Final Report Generation

Simply add new phase definitions to the `PHASES` dictionary in the code.

