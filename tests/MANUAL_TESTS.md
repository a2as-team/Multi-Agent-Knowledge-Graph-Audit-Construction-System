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

## File Suggestion Agent (Unstructured) Manual Tests

**Test UI Location**: `tests/ui/test_file_suggestion_unstructured_agent_ui.py`

**Prerequisites**:
- Approved user goal from User Intent Agent (with unstructured extraction goals)
- Markdown files available in `data/story1/`

**Run the UI**:
```bash
streamlit run tests/ui/test_file_suggestion_unstructured_agent_ui.py
```

---

### Test 1: Initialize with Extended User Goal

**Objective**: Verify that the agent correctly initializes with an extended user goal that includes unstructured data extraction guidance.

**Steps**:
1. In the sidebar, set "Kind of Graph" to: `art collection provenance`
2. In "Graph Description (Extended for Unstructured)", enter:
   ```
   A knowledge graph for art collection provenance which includes all levels from artworks to artists, locations, and mediums, which can support root-cause analysis and content auditing.
   
   Add artist biographies, exhibition histories, and provenance notes to provide deeper context and historical information about artworks and artists.
   ```
3. Click "Initialize Agent"

**Expected Result**:
- ✅ Agent initializes successfully
- ✅ Success message displayed
- ✅ "Approved User Goal" in session state shows the extended description

---

### Test 2: List Available Files

**Objective**: Verify that the agent can list available markdown files.

**Steps**:
1. After initializing the agent, prompt: `What markdown files are available?`
2. Observe the agent's response

**Expected Result**:
- ✅ Agent lists available `.md` files from the data directory
- ✅ Only markdown files are shown (no CSV files)
- ✅ Files include: `artist_bios.md`, `exhibition_histories.md`, `provenance_notes.md`, etc.

---

### Test 3: Suggest Relevant Files Based on Goal

**Objective**: Verify that the agent suggests files relevant to the extended user goal.

**Steps**:
1. Prompt: `Which markdown files would be relevant for my goal of adding artist biographies and exhibition histories?`
2. Review the agent's suggestions

**Expected Result**:
- ✅ Agent suggests files like `artist_bios.md`, `exhibition_histories.md`
- ✅ Agent explains why each file is relevant to the goal
- ✅ Files related to the extended goal (artist info, exhibitions) are prioritized
- ✅ "Suggested Files" appears in session state

---

### Test 4: Sample File Content

**Objective**: Verify that the agent can sample markdown files to understand their content.

**Steps**:
1. Prompt: `Can you sample the artist_bios.md file to see what it contains?`
2. Observe the response

**Expected Result**:
- ✅ Agent samples the file and shows a preview of its content
- ✅ Agent can describe what kind of information the file contains
- ✅ Sample shows markdown-formatted content

---

### Test 5: Approve Suggested Files

**Objective**: Verify that suggested files can be approved.

**Steps**:
1. After the agent suggests files, prompt: `Yes, approve these files`
2. Check the session state

**Expected Result**:
- ✅ Agent confirms approval
- ✅ "Approved Files" in session state matches the suggested files
- ✅ All approved files are markdown (.md) files

---

### Test 6: Modify Suggestions Based on Feedback

**Objective**: Verify that the agent can adjust suggestions based on user feedback.

**Steps**:
1. After initial suggestions, prompt: `Actually, I don't need misc_notes.md. Can you remove it from the suggestions?`
2. Review the updated suggestions
3. Approve the modified list

**Expected Result**:
- ✅ Agent removes the specified file from suggestions
- ✅ Agent presents the updated list
- ✅ When approved, "Approved Files" reflects the modified list

---

### Test 7: Test Markdown-Only Validation

**Objective**: Verify that the agent only accepts markdown files for unstructured data.

**Steps**:
1. Prompt: `Suggest all available files including CSV files`
2. Observe the agent's response

**Expected Result**:
- ✅ Agent only suggests `.md` files
- ✅ Agent may mention that CSV files are for structured data, not unstructured extraction
- ✅ No CSV files appear in the suggested files list

---

### Test 8: Test Session Reset

**Objective**: Verify that resetting the session clears all state properly.

**Steps**:
1. After completing any test, click the "Reset Session" button in the sidebar
2. Observe that the chat history is cleared
3. Check that the session state shows all states as "Not approved yet" or "Not loaded yet"
4. Initialize the agent again and verify it works from a clean state

**Expected Result**:
- ✅ Session state is completely cleared
- ✅ Chat history is empty
- ✅ Agent can be re-initialized and used normally after reset

---

## NER Agent (Named Entity Recognition) Manual Tests

**Test UI Location**: `tests/ui/test_ner_agent_ui.py`

**Prerequisites**:
- Approved user goal (extended for unstructured data)
- Approved markdown files from File Suggestion Agent (Unstructured)
- Approved construction plan from Schema Proposal Agent (Structured)

**Run the UI**:
```bash
streamlit run tests/ui/test_ner_agent_ui.py
```

---

### Test 1: Initialize with Required State

**Objective**: Verify that the agent correctly initializes with all required state.

**Steps**:
1. In the sidebar, configure:
   - **Kind of Graph**: `art collection provenance`
   - **Graph Description**: Extended goal with unstructured extraction guidance
   - **Approved Files**: `artist_bios.md`, `exhibition_histories.md`, `provenance_notes.md`
   - **Node Labels**: `Artist`, `Artwork`, `Location`, `Medium`
2. Click "Initialize Agent"

**Expected Result**:
- ✅ Agent initializes successfully
- ✅ Success message displayed
- ✅ Session state shows all three required inputs

---

### Test 2: Retrieve Well-Known Types

**Objective**: Verify that the agent can access well-known entity types from the construction plan.

**Steps**:
1. After initialization, prompt: `What well-known entity types are available from the graph schema?`
2. Observe the response

**Expected Result**:
- ✅ Agent lists node labels: Artist, Artwork, Location, Medium
- ✅ Agent explains these are from the existing graph schema

---

### Test 3: Sample Files to Understand Content

**Objective**: Verify that the agent samples markdown files before proposing entities.

**Steps**:
1. Prompt: `Sample the artist_bios.md file to see what entities might be mentioned`
2. Review the response

**Expected Result**:
- ✅ Agent samples the file
- ✅ Agent describes what kind of information is in the file
- ✅ Agent may mention potential entity types found

---

### Test 4: Propose Entity Types

**Objective**: Verify that the agent proposes both well-known and discovered entity types.

**Steps**:
1. Prompt: `Propose entity types that could be extracted from the markdown files to support the user goal`
2. Review the proposed entities

**Expected Result**:
- ✅ Agent proposes well-known entities (e.g., Artist, Artwork)
- ✅ Agent proposes discovered entities (e.g., Exhibition, Art Movement, Collector)
- ✅ Proposed entities are relevant to art provenance
- ✅ "Proposed Entity Types" appears in session state
- ✅ Agent explains why each entity type is relevant

---

### Test 5: Approve Proposed Entities

**Objective**: Verify that proposed entities can be approved.

**Steps**:
1. After entities are proposed, prompt: `Yes, approve these entity types`
2. Check the session state

**Expected Result**:
- ✅ Agent confirms approval
- ✅ "Approved Entity Types" in session state matches proposed entities
- ✅ Agent is ready for the next phase (fact extraction)

---

### Test 6: Modify Entity Proposals Based on Feedback

**Objective**: Verify that the agent can adjust proposals based on user feedback.

**Steps**:
1. After initial proposal, prompt: `Remove "Art Movement" and add "Curator" instead`
2. Review the updated proposal
3. Approve the modified list

**Expected Result**:
- ✅ Agent removes the specified entity
- ✅ Agent adds the requested entity
- ✅ Agent presents the updated list
- ✅ When approved, "Approved Entity Types" reflects the modifications

---

### Test 7: Validate Entity Type Relevance

**Objective**: Verify that the agent only proposes entities relevant to the user goal.

**Steps**:
1. Prompt: `Make sure all proposed entities support the goal of tracking art provenance and providing historical context`
2. Review the agent's validation

**Expected Result**:
- ✅ Agent reviews each entity type
- ✅ Agent explains how each supports the user goal
- ✅ Agent may remove or suggest changes to irrelevant entities

---

### Test 8: Test Session Reset

**Objective**: Verify that resetting the session clears all state properly.

**Steps**:
1. After completing any test, click the "Reset Session" button in the sidebar
2. Observe that the chat history is cleared
3. Check that the session state shows all states as "Not set" or "Not proposed yet"
4. Initialize the agent again and verify it works from a clean state

**Expected Result**:
- ✅ Session state is completely cleared
- ✅ Chat history is empty
- ✅ Agent can be re-initialized and used normally after reset

---

## Fact Extraction Agent Manual Tests (with Critic Pattern)

**Test UI Location**: `tests/ui/test_fact_extraction_agent_ui.py`

**Architecture**: This agent uses a **critic pattern** with automatic refinement:
- **Proposal Agent**: Proposes fact types from markdown files
- **Critic Agent**: Validates proposals and provides structured feedback
- **Refinement Loop**: Iterates up to 3 times until fact types are valid

**Prerequisites**:
- Approved user goal (extended for unstructured data)
- Approved markdown files
- **Approved entity types** (from NER Agent)
- **Approved construction plan** (from structured data phase - optional but recommended to avoid redundancy)

**Run the UI**:
```bash
streamlit run tests/ui/test_fact_extraction_agent_ui.py
```

---

### Test 1: Initialize with Construction Plan to Avoid Redundancy

**Objective**: Verify that the agent correctly initializes with approved entity types AND existing relationships from structured data.

**Steps**:
1. In the sidebar, configure:
   - **User Goal**: Extended goal with unstructured extraction guidance
   - **Approved Files**: `artist_bios.md`, `exhibition_histories.md`, `provenance_notes.md`
   - **Approved Entity Types**: `Artist`, `Artwork`, `Location`, `Exhibition`, `Collection`, `ArtMovement`, `Collector`, `Institution`
   - **Approved Construction Plan**: 
     ```
     CREATED_BY | Artwork | Artist
     LOCATED_AT | Artwork | Location
     HAS_MEDIUM | Artwork | Medium
     ```
2. Click "Initialize Agent"

**Expected Result**:
- ✅ Agent initializes successfully
- ✅ Success message displayed
- ✅ Session state shows all four inputs (including construction plan)
- ✅ Approved entity types are available to the agent
- ✅ Existing relationships from structured data are available to avoid redundancy

---

### Test 2: Critic Pattern - Automatic Refinement

**Objective**: Verify that the critic pattern automatically refines fact types through iterations.

**Steps**:
1. Ensure Test 1 is complete (construction plan is initialized)
2. Prompt: `Propose fact types that could be extracted from the markdown files`
3. **Observe the refinement process** (check logs and session state):
   - Proposal Agent proposes initial fact types
   - Critic Agent reviews and may request retry
   - Loop continues automatically until valid or max iterations (3)
4. Review the final proposed facts and critic feedback

**Expected Result**:
- ✅ **Iteration 1**: Proposal Agent proposes facts, Critic validates
- ✅ **If critic finds issues**: 
  - Critic feedback appears in session state with status="retry"
  - Issues are listed (e.g., "Duplicate: ...", "Inverse relationship: ...", "Synonym predicates: ...")
  - Loop automatically continues to Iteration 2
- ✅ **Subsequent iterations**: Proposal Agent addresses feedback
- ✅ **Final iteration**: 
  - Critic validates with status="valid" OR
  - Max iterations (3) reached and user is notified
- ✅ **Critic feedback section** in UI shows:
  - Current status (valid/retry)
  - List of issues (if any)
  - Iteration count (X/3)
- ✅ **Final proposed facts** are clean:
  - No duplicates across files
  - No inverse relationships
  - No synonym predicates
  - No redundancy with structured data

**Performance Check**:
- Expected iterations: 1-3 (depending on initial proposal quality)
- Expected final fact types: 10-15 unique, non-redundant relationships
- Previous (without critic): 21+ fact types with redundancy issues

---

### Test 3: Verify Critic Validation Checks

**Objective**: Verify that the critic agent properly validates all aspects of proposed fact types.

**Steps**:
1. After Test 2 completes, review the critic feedback in session state
2. Check that critic validated these aspects:
   - No duplicate fact types
   - No inverse relationships
   - No synonym predicates
   - No semantic redundancy with existing relationships
   - All entities are approved
   - Predicates are consolidated
   - Facts support user goal

**Expected Result**:
- ✅ Critic feedback shows status="valid" (or lists specific issues if status="retry")
- ✅ If issues were found in earlier iterations, they are resolved in final proposal
- ✅ Final proposed facts pass ALL validation checks:
  - ✅ No exact duplicates (same subject, predicate, object)
  - ✅ No inverse pairs (e.g., NOT both `acquired_by` and `acquired_from`)
  - ✅ No synonyms (e.g., NOT both `featured_art_movement` and `focused_on`)
  - ✅ No semantic overlap with existing CREATED_BY, LOCATED_AT, HAS_MEDIUM
  - ✅ All entities are from approved list
  - ✅ Predicates use lowercase_with_underscores format
- ✅ Batch tool usage (check logs): `add_proposed_facts_batch` used for efficiency
- ✅ Total API calls reduced by 70-80% compared to individual calls

**Critic Validation Quality Check**:
- ✅ Specific, actionable feedback (not vague)
- ✅ Lists exact fact types that have issues
- ✅ Explains why each issue is problematic
- ✅ Suggests how to fix the issues

**Performance Check**:
- Expected fact types: 10-15 unique, canonical, NON-REDUNDANT relationship types
- Previous (without critic): 21+ fact types with redundancy issues

---

### Test 4: Validate Entity Type Usage

**Objective**: Verify that the agent only uses approved entity types.

**Steps**:
1. After initial proposal, prompt: `Make sure all fact types only use approved entity types`
2. Review the agent's validation

**Expected Result**:
- ✅ Agent confirms all subjects/objects are from approved entities
- ✅ Agent does not propose new entity types
- ✅ If any invalid entities were used, agent corrects them

---

### Test 5: Sample Files for Context

**Objective**: Verify that the agent samples files to understand relationships.

**Steps**:
1. Prompt: `Sample the exhibition_histories.md file to see what relationships exist`
2. Observe the response

**Expected Result**:
- ✅ Agent samples the file
- ✅ Agent identifies relationship phrases (e.g., "exhibited in", "featured in", "displayed in")
- ✅ Agent proposes fact types based on observed relationships

---

### Test 6: Approve Proposed Facts

**Objective**: Verify that proposed facts can be approved.

**Steps**:
1. After facts are proposed, prompt: `Yes, approve these fact types`
2. Check the session state

**Expected Result**:
- ✅ Agent confirms approval
- ✅ "Approved Fact Types" in session state matches proposed facts
- ✅ All fact types are valid triples with approved entities

---

### Test 7: Modify Fact Proposals Based on Feedback

**Objective**: Verify that the agent can adjust proposals based on user feedback.

**Steps**:
1. After initial proposal, prompt: `Remove the (Artist, born_in, Location) fact and add (Artwork, loaned_to, Institution) instead`
2. Review the updated proposal
3. Approve the modified list

**Expected Result**:
- ✅ Agent removes the specified fact
- ✅ Agent adds the requested fact
- ✅ Agent presents the updated list
- ✅ When approved, "Approved Fact Types" reflects the modifications

---

### Test 8: Validate Predicate Relevance

**Objective**: Verify that predicates are grounded in the text.

**Steps**:
1. Prompt: `Ensure all predicates actually appear in the markdown files`
2. Review the agent's validation

**Expected Result**:
- ✅ Agent verifies each predicate against the text
- ✅ Agent may sample files to confirm predicate usage
- ✅ Agent removes or modifies predicates that aren't found in text

---

### Test 9: Test Goal Alignment

**Objective**: Verify that fact types support the user's goal.

**Steps**:
1. Prompt: `Do these fact types support the goal of tracking art provenance and providing historical context?`
2. Review the agent's analysis

**Expected Result**:
- ✅ Agent evaluates each fact type against the user goal
- ✅ Agent explains how facts support provenance tracking
- ✅ Agent may suggest additional facts or remove irrelevant ones

---

### Test 10: Duplicate Subject-Object Pairs Validation

**Objective**: Verify that the critic detects when multiple predicates connect the same entity types and flags them unless semantically distinct.

**Steps**:
1. Initialize agent with approved entity types including `Artwork` and `Exhibition`
2. Prompt: `Propose fact types for relationships between Artworks and Exhibitions`
3. Observe if the agent proposes multiple predicates like:
   - `(Artwork, loaned_for, Exhibition)`
   - `(Artwork, featured_in, Exhibition)`
   - `(Artwork, displayed_at, Exhibition)`
4. Check the critic feedback in session state

**Expected Result**:
- ✅ **If multiple predicates connect same entity pair**, critic flags the issue:
  - Example: "Duplicate subject-object pair: (Artwork, loaned_for, Exhibition) and (Artwork, featured_in, Exhibition) - are these truly distinct? If not, consolidate to ONE predicate"
- ✅ **If semantically distinct**, critic accepts with justification:
  - Example: `loaned_for` (temporary ownership) vs `featured_in` (exhibition participation) may be distinct
  - Critic should document WHY they're distinct
- ✅ **If redundant**, proposal agent consolidates to ONE canonical predicate in next iteration
- ✅ Final approved facts have ONE predicate per subject-object pair (unless distinct meanings documented)

**Quality Check**:
- ✅ Critic asks: "Are these truly different relationships?"
- ✅ If distinct, the difference is semantically meaningful (e.g., temporal, ownership, attribution)
- ✅ Generic synonyms are consolidated (e.g., `exhibited_in`, `displayed_in`, `shown_at` → ONE)

---

### Test 11: Orphaned Entity Detection

**Objective**: Verify that the critic detects approved entity types that are not used in any relationship (structured or unstructured).

**Steps**:
1. Initialize agent with:
   - **Approved Entity Types**: `Artist`, `Artwork`, `Location`, `Exhibition`, `Collection`, `Institution`
   - **Approved Construction Plan**: 
     ```
     CREATED_BY | Artwork | Artist
     LOCATED_AT | Artwork | Location
     HAS_MEDIUM | Artwork | Medium
     ```
2. Prompt: `Propose fact types focusing on exhibitions only`
3. Agent proposes facts like:
   - `(Artwork, featured_in, Exhibition)`
   - `(Artist, founded, ArtMovement)`
4. Observe critic feedback

**Expected Result**:
- ✅ Critic identifies orphaned entities:
  - `Collection` - not used in proposed facts or existing relationships
  - `Institution` - not used in proposed facts or existing relationships
- ✅ Critic provides specific feedback:
  - "Orphaned entity: 'Collection' is approved but not used in any relationship (neither structured nor unstructured). Suggestion: Add facts like (Artwork, part_of, Collection) or (Institution, manages, Collection)"
  - "Orphaned entity: 'Institution' appears in neither proposed facts nor existing structured relationships. Suggestion: Add facts like (Artwork, attributed_by, Institution) or (Exhibition, hosted_by, Institution)"
- ✅ Critic status is "retry" if orphaned entities exist
- ✅ In next iteration, proposal agent either:
  - Adds facts using orphaned entities, OR
  - Justifies why entity should remain standalone (rare)
- ✅ Final validation confirms ALL approved entities are connected to the graph

**Quality Check**:
- ✅ No isolated nodes in the final graph structure
- ✅ Every approved entity can be reached through graph traversal
- ✅ Orphan detection covers BOTH structured and unstructured relationships

**Example Valid Resolution**:
After critic feedback, proposal agent adds:
- `(Artwork, part_of, Collection)` - connects Collection
- `(Exhibition, hosted_by, Institution)` - connects Institution
- Critic validates and approves (status="valid")

---

### Test 12: Test Session Reset

**Objective**: Verify that resetting the session clears all state properly.

**Steps**:
1. After completing any test, click the "Reset Session" button in the sidebar
2. Observe that the chat history is cleared
3. Check that the session state shows all states as "Not set" or "Not proposed yet"
4. Initialize the agent again and verify it works from a clean state

**Expected Result**:
- ✅ Session state is completely cleared
- ✅ Chat history is empty
- ✅ Agent can be re-initialized and uses normally after reset

---

### Expected Fact Types for Art Collection

Based on the test data, the agent should propose fact types like:

**Provenance & Ownership:**
- `(Artwork, owned_by, Collection)`
- `(Artwork, owned_by, Collector)`
- `(Collection, held_by, Institution)`
- `(Artwork, loaned_to, Institution)`

**Exhibition & Display:**
- `(Artwork, displayed_at, Exhibition)`
- `(Artwork, exhibited_in, Location)` (if Location is a gallery space)
- `(Exhibition, featured, Artwork)`

**Artistic Context:**
- `(Artist, founded, ArtMovement)`
- `(Artist, associated_with, ArtMovement)`
- `(Artwork, belongs_to, ArtMovement)`

**Historical Connections:**
- `(Artist, created, Artwork)` (may already exist in structured data)
- `(Exhibition, showcased, Artwork)`

---

## Entity Resolution Agent

_Test cases to be added..._

---

## Audit Query Agent

_Test cases to be added..._

