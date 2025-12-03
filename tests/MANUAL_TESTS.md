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

_Test cases to be added..._

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

