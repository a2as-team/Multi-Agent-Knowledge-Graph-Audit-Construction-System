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
- **Prerequisites:** Requires `approved_user_goal` from User Intent Agent (can be set in sidebar)

### Test Cases

#### ✅ Test 1: File Listing
**Steps:**
1. Initialize agent with `approved_user_goal` in sidebar
2. Enter: `What files are available for import?`

**Expected:**
- Agent uses `get_approved_user_goal` tool
- Agent uses `list_available_files` tool
- Session State shows `all_available_files` with list of file paths
- Agent responds with summary of available files

---

#### ✅ Test 2: File Suggestion Based on User Goal
**Steps:**
1. After Test 1 (files are listed)
2. Enter: `Which files should we use for import?`

**Expected:**
- Agent analyzes files using `sample_file` tool for unclear files
- Agent uses `set_suggested_files` tool with relevant file list
- Session State shows `suggested_files` with CSV/JSON files only
- Agent explains why files are relevant to user goal

---

#### ✅ Test 3: File Approval Workflow
**Steps:**
1. After Test 2 (files are suggested)
2. Enter: `Yes, let's use those files` or `Approve those files`

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

#### ✅ Test 5: File Sampling for Unclear Files
**Steps:**
1. After Test 1 (files are listed)
2. Enter: `Which files are relevant?`

**Expected:**
- Agent uses `sample_file` tool for files it's unsure about
- Agent reads file content (up to 100 lines)
- Agent makes informed suggestions based on file content

---

#### ✅ Test 6: Filtering Structured Files Only
**Prerequisites:** Ensure `data/story1/` contains both CSV and Markdown files
**Steps:**
1. Initialize agent
2. Enter: `Suggest files for import`

**Expected:**
- Agent suggests only CSV/JSON files
- Markdown files are NOT included in suggestions
- Agent explains it focuses on structured data files

---

#### ✅ Test 7: Session State Persistence
**Steps:**
1. Complete Tests 2-3 (approved files exist)
2. Enter: `What files did we approve?`

**Expected:**
- Agent can reference approved files
- Session State shows all keys: `approved_user_goal`, `all_available_files`, `suggested_files`, `approved_files`

---

#### ✅ Test 8: Reset Session
**Steps:**
1. After completing Tests 1-3
2. Click "Reset Session" button

**Expected:**
- Session State is empty `{}`
- All state keys are cleared
- Agent needs to be re-initialized

---

#### ✅ Test 9: Verbose Logging
**Steps:**
1. Enable "Verbose Logging" checkbox
2. Enter any input

**Expected:**
- Terminal/console shows detailed tool calls and agent events
- Tool invocations logged with parameters

---

#### ✅ Test 10: Integration with User Intent Agent
**Prerequisites:** Use realistic `approved_user_goal` (e.g., art collection provenance)
**Steps:**
1. Set `approved_user_goal` in sidebar
2. Enter: `What files should we use?`

**Expected:**
- Agent retrieves `approved_user_goal` using `get_approved_user_goal` tool
- Agent's suggestions align with user goal's `kind_of_graph` and `description`
- Agent explains file relevance in context of user goal

---

#### ✅ Test 11: Multiple Conversation Turns
**Steps:**
1. Enter: `List available files`
2. Enter: `Which ones are relevant?`
3. Enter: `Actually, I also want to include [specific file]`
4. Enter: `Approve the updated list`

**Expected:**
- Agent maintains context across turns
- Agent updates suggestions based on user feedback
- Final approved files reflect all information shared

---

#### ✅ Test 12: Error Handling - Missing Approved User Goal
**Steps:**
1. Initialize agent without `approved_user_goal` (leave fields empty)
2. Try to interact with agent

**Expected:**
- Agent uses `get_approved_user_goal` tool
- Agent receives error that `approved_user_goal` is not set
- Agent prompts user to set goal first

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

_Test cases to be added..._

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

