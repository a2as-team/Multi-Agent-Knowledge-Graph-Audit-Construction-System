# Manual Test Cases for Agents

This document contains manual test cases for each agent. These tests should be performed before merging to ensure the agent works as expected.

---

## User Intent Agent

### Test Setup
- **UI Location:** `tests/ui/test_user_intent_agent_ui.py`
- **Run:** `streamlit run tests/ui/test_user_intent_agent_ui.py`

### Test Cases

#### ✅ Test 1: Art Collection Use Case (Primary)
**Input:**
```
I'd like an art collection provenance graph which includes all levels from artworks to artists, locations, and mediums, which can support root-cause analysis and content auditing.
```

**Expected:**
- Agent responds and uses `set_perceived_user_goal` tool
- Session State shows `perceived_user_goal` with:
  - `kind_of_graph`: Contains "art collection" or similar (2-3 words)
  - `graph_description`: Mentions artworks, artists, locations, mediums
- User approves: `Approve that goal`
- Session State shows `approved_user_goal` matching `perceived_user_goal`

---

#### ✅ Test 2: Goal Approval Workflow
**Steps:**
1. Set perceived goal (from Test 1)
2. Enter: `Approve that goal`
3. Verify `approved_user_goal` is set in Session State

**Expected:** Approved goal stored correctly

---

#### ✅ Test 3: Error Handling
**Steps:**
1. Reset session
2. Directly enter: `Approve the goal` (without setting perceived goal first)

**Expected:** Agent asks to set perceived goal first, does not approve

---

#### ✅ Test 4: Clarifying Questions
**Input:** `I want a graph`

**Expected:** Agent asks clarifying questions and suggests use cases

---

#### ✅ Test 5: Generic Use Case
**Input:** `I want to build a social network graph for my friends and family`

**Expected:**
- Agent understands non-art-collection use case
- Sets perceived goal with "social network" context
- Can approve successfully

---

#### ✅ Test 6: Session State Persistence
**Steps:**
1. Complete Test 1-2 (approved goal exists)
2. Send: `What is my approved goal?`

**Expected:** Agent references approved goal, state persists

---

#### ✅ Test 7: Reset Session
**Steps:**
1. After completing Tests 1-2
2. Click "Reset Session" button

**Expected:** Session State is empty `{}`, can start fresh

---

### Success Criteria
- ✅ Agent completes without critical errors
- ✅ Tools (`set_perceived_user_goal`, `approve_perceived_user_goal`) work correctly
- ✅ Session state contains `approved_user_goal` with correct structure:
  ```json
  {
    "kind_of_graph": "2-3 words",
    "graph_description": "A few sentences..."
  }
  ```
- ✅ Agent works generically (not hardcoded to art collection)
- ✅ No critical errors in logs

---

## File Suggestion Agent

### Test Setup
- **UI Location:** `tests/ui/test_file_suggestion_agent_ui.py`
- **Run:** `streamlit run tests/ui/test_file_suggestion_agent_ui.py`
- **Prerequisites:** Requires `approved_user_goal` from User Intent Agent (set in sidebar)

### Test Cases

#### ✅ Test 1: File Listing
**Steps:**
1. Initialize agent with `approved_user_goal` in sidebar
2. Enter: `What files are available for import?`

**Expected:**
- Agent uses `get_approved_user_goal` and `list_available_files` tools
- Session State shows `all_available_files` with list of file paths
- Agent responds with summary of available files

---

#### ✅ Test 2: File Suggestion Based on User Goal
**Steps:**
1. After Test 1 (files are listed)
2. Enter: `Which files should we use for import?`

**Expected:**
- Agent uses `sample_file` tool for unclear files
- Agent uses `set_suggested_files` tool with relevant CSV/JSON files only
- Session State shows `suggested_files`
- Agent explains file relevance to user goal

---

#### ✅ Test 3: File Approval Workflow
**Steps:**
1. After Test 2 (files are suggested)
2. Enter: `Yes, let's use those files`

**Expected:**
- Agent uses `approve_suggested_files` tool
- Session State shows `approved_files` matching `suggested_files`
- Agent confirms approval

---

#### ✅ Test 4: Error Handling - Approval Without Suggestions
**Steps:**
1. Reset session
2. Directly enter: `Approve the files` (without suggesting files first)

**Expected:**
- Agent does NOT use `approve_suggested_files` tool
- Agent prompts to suggest files first
- Session State does NOT show `approved_files`

---

#### ✅ Test 5: Filtering Structured Files Only
**Prerequisites:** Ensure `data/story1/` contains both CSV and Markdown files
**Steps:**
1. Initialize agent
2. Enter: `Suggest files for import`

**Expected:**
- Agent suggests only CSV/JSON files
- Markdown files are NOT included in suggestions
- Agent explains it focuses on structured data files

---

#### ✅ Test 6: Session State Persistence
**Steps:**
1. Complete Tests 2-3 (approved files exist)
2. Enter: `What files did we approve?`

**Expected:**
- Agent can reference approved files
- Session State shows all keys: `approved_user_goal`, `all_available_files`, `suggested_files`, `approved_files`

---

#### ✅ Test 7: Reset Session
**Steps:**
1. After completing Tests 1-3
2. Click "Reset Session" button

**Expected:**
- Session State is empty `{}`
- All state keys are cleared
- Agent needs to be re-initialized

---

### Success Criteria
- ✅ Agent completes without critical errors
- ✅ Tools (`get_approved_user_goal`, `list_available_files`, `sample_file`, `set_suggested_files`, `approve_suggested_files`) work correctly
- ✅ Session state contains `approved_files` with correct structure (list of file paths)
- ✅ Agent works generically (not hardcoded to art collection)
- ✅ Agent only suggests CSV/JSON files (structured data)
- ✅ No critical errors in logs

---

## Schema Proposal Agent

### Test Setup
- **UI Location:** `tests/ui/test_schema_proposal_agent_ui.py`
- **Run:** `streamlit run tests/ui/test_schema_proposal_agent_ui.py`
- **Prerequisites:** Requires `approved_user_goal` and `approved_files` (set in sidebar)

### Test Cases

#### ✅ Test 1: Schema Proposal Initial Request
**Steps:**
1. Initialize agent with `approved_user_goal` and `approved_files` in sidebar
2. Enter: `How can these files be imported to construct the knowledge graph?`

**Expected:**
- Agent uses `get_approved_user_goal` and `get_approved_files` tools
- Agent uses `sample_file` and `search_file` tools to analyze files
- Agent proposes node and relationship constructions
- Session State shows `proposed_construction_plan` with nodes and relationships

---

#### ✅ Test 2: Schema Refinement Loop
**Steps:**
1. After Test 1 (schema is proposed)
2. Wait for critic agent feedback
3. Check Session State for `feedback` key

**Expected:**
- Schema Proposal Agent proposes initial schema
- Schema Critic Agent reviews and provides feedback
- If feedback is not "valid", loop continues with refinement
- Maximum 3 iterations allowed

---

#### ✅ Test 3: Node Construction Validation
**Steps:**
1. After schema is proposed
2. Check `proposed_construction_plan` in Session State

**Expected:**
- All node types identified (e.g., Artist, Artwork, Location, Medium)
- Each node has: `construction_type: "node"`, `source_file`, `label`, `unique_column_name`, `properties`
- Unique identifiers correctly identified (e.g., `artist_id`, `artwork_id`)

---

#### ✅ Test 4: Relationship Construction Validation
**Steps:**
1. After schema is proposed
2. Check `proposed_construction_plan` in Session State

**Expected:**
- Relationship types identified (e.g., CREATED, LOCATED_AT, HAS_MEDIUM)
- Each relationship has: `construction_type: "relationship"`, `from_node_label`, `to_node_label`, `from_node_column`, `to_node_column`
- Full relationships preferred over reference relationships when dedicated files exist

---

#### ✅ Test 5: Schema Approval
**Steps:**
1. After schema is proposed and validated
2. Enter: `Yes, approve the schema`

**Expected:**
- Agent uses `approve_proposed_construction_plan` tool
- Session State shows `approved_construction_plan` matching `proposed_construction_plan`
- Agent confirms approval

---

#### ✅ Test 6: Graph Connectivity Validation
**Steps:**
1. After schema is proposed
2. Review the construction plan structure

**Expected:**
- All nodes are connected (no isolated components)
- Artwork node serves as hub connecting to Artist, Location, Medium
- Graph structure supports the user goal

---

#### ✅ Test 7: Error Handling - Approval Without Proposal
**Steps:**
1. Reset session
2. Directly enter: `Approve the schema` (without proposing schema first)

**Expected:**
- Agent does NOT use `approve_proposed_construction_plan` tool
- Agent prompts to propose schema first
- Session State does NOT show `approved_construction_plan`

---

### Success Criteria
- ✅ Agent completes without critical errors
- ✅ Tools (`propose_node_construction`, `propose_relationship_construction`, `get_proposed_construction_plan`, `approve_proposed_construction_plan`) work correctly
- ✅ Session state contains `approved_construction_plan` with correct structure:
  - Nodes with unique identifiers and properties
  - Relationships with proper from/to node mappings
- ✅ Schema refinement loop works (proposal → critique → refinement)
- ✅ All nodes are connected in the graph
- ✅ Agent works generically (not hardcoded to art collection)
- ✅ No critical errors in logs

---

## NER Agent

_Test cases to be added..._

---

## Fact Extraction Agent

_Test cases to be added..._

---

## Entity Resolution Agent

_Test cases to be added..._

---

## Audit Query Agent

_Test cases to be added..._

