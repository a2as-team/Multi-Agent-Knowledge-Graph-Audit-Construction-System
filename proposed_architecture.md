🏗️ PROPOSED ARCHITECTURE: Unified Audit Review System

📊 System Overview
┌─────────────────────────────────────────────────────────────┐
│          SETU CONTENT AUDIT SYSTEM                          │
│   Multi-Agent Knowledge Graph Construction & Validation     │
│   ⭐ NEW: Unified Audit Review at End                       │
└─────────────────────────────────────────────────────────────┘
GOAL: Build a knowledge graph as "source of truth" 
      with complete user verification and audit trail
      All audit queries reviewed together at the end

🔄 Complete Agent Workflow
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING & SCHEMA DEFINITION                           │
└──────────────────────────────────────────────────────────────────┘
1. USER INTENT AGENT
   ├─ Input: User's natural language goal
   ├─ Output: Structured goal definition
   └─ State: APPROVED_USER_GOAL

2. FILE SUGGESTION AGENT (Structured)
   ├─ Input: User goal, available CSV files
   ├─ Output: Relevant CSV files
   └─ State: APPROVED_FILES (structured)

3. SCHEMA PROPOSAL AGENT (Structured)
   ├─ Input: User goal, CSV files
   ├─ Output: Construction plan (nodes/relationships)
   └─ State: APPROVED_CONSTRUCTION_PLAN

4. FILE SUGGESTION AGENT (Unstructured)
   ├─ Input: User goal, available markdown files
   ├─ Output: Relevant markdown files
   └─ State: APPROVED_FILES (unstructured)

5. NER AGENT
   ├─ Input: User goal, markdown files
   ├─ Output: Entity types to extract
   └─ State: APPROVED_ENTITY_TYPES

6. FACT EXTRACTION AGENT
   ├─ Input: User goal, markdown files, entity types
   ├─ Output: Relationship types to extract
   └─ State: APPROVED_FACT_TYPES

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: DATA QUALITY RULES DEFINITION                          │
└──────────────────────────────────────────────────────────────────┘
7. DATA QUALITY RULES AGENT
   ├─ Input: User requirements, schema, entity/fact types
   ├─ Output: Custom quality rules
   └─ State: DATA_QUALITY_RULES

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: PRE-INGESTION VALIDATION                               │
└──────────────────────────────────────────────────────────────────┘
8. PRE-INGESTION AUDIT AGENT ⭐ MODIFIED
   ├─ Input: CSV/markdown files, schema
   ├─ Scans for:
   │  ├─ Duplicate unique identifiers
   │  ├─ Missing required fields
   │  ├─ Invalid foreign key references
   │  ├─ Data type mismatches
   │  └─ Schema violations
   ├─ Output: Audit queries (stored, NOT shown to user)
   ├─ Behavior: Creates queries, stores in state, continues
   └─ State: PRE_INGESTION_AUDIT_QUERIES

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: KNOWLEDGE GRAPH CONSTRUCTION                           │
└──────────────────────────────────────────────────────────────────┘
9. KG CONSTRUCTION PART I (Domain Graph)
   ├─ Input: Construction plan, CSV files
   ├─ Process:
   │  ├─ Create constraints
   │  ├─ Load nodes from CSV (applies pre-ingestion resolutions if available)
   │  ├─ Create relationships from CSV
   │  └─ Track ingestion actions (audit trail)
   ├─ Output: Domain Graph in Neo4j
   └─ State: INGESTION_AUDIT_TRAIL

10. KG CONSTRUCTION PART II (Subject & Lexical Graphs)
    ├─ Input: Markdown files, entity types, fact types
    ├─ Process:
    │  ├─ Chunk markdown files
    │  ├─ Create Document and Chunk nodes (Lexical Graph)
    │  ├─ Extract entities (guided by NER types)
    │  ├─ Extract relationships (guided by fact types)
    │  ├─ Link entities to chunks (provenance)
    │  └─ Create Subject Graph
    ├─ Output: Subject Graph + Lexical Graph in Neo4j
    └─ State: (updated Neo4j database)

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 5: ENTITY RESOLUTION                                      │
└──────────────────────────────────────────────────────────────────┘
11. ENTITY RESOLUTION AUDIT AGENT ⭐ MODIFIED
    ├─ Input: Domain Graph, Subject Graph
    ├─ Process:
    │  ├─ Find entities with same label in both graphs
    │  ├─ Calculate similarity scores (fuzzy matching)
    │  ├─ Generate match proposals as audit queries
    │  └─ Include evidence: scores, context, alternatives
    ├─ Output: Audit queries (stored, NOT shown to user)
    ├─ Behavior: Creates queries, stores in state, continues
    └─ State: ENTITY_RESOLUTION_AUDIT_QUERIES

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 6: POST-INGESTION VALIDATION                              │
└──────────────────────────────────────────────────────────────────┘
12. POST-INGESTION AUDIT AGENT ⭐ MODIFIED
    ├─ Input: Complete KG, data quality rules
    ├─ Generates audit queries for:
    │  ├─ Required relationship violations
    │  ├─ Temporal constraint violations
    │  ├─ Orphaned nodes
    │  ├─ Unresolved entities (in Subject but not Domain)
    │  ├─ Domain vs Subject inconsistencies
    │  ├─ Custom rule violations
    │  └─ Coverage issues (unused fact types)
    ├─ Output: Audit queries (stored, NOT shown to user)
    ├─ Behavior: Creates queries, stores in state, continues
    └─ State: POST_INGESTION_AUDIT_QUERIES

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 7: UNIFIED AUDIT REVIEW ⭐ NEW                            │
└──────────────────────────────────────────────────────────────────┘
13. UNIFIED AUDIT REVIEW INTERFACE
    ├─ Input: All audit queries from all phases
    ├─ Collects queries from:
    │  ├─ PRE_INGESTION_AUDIT_QUERIES
    │  ├─ ENTITY_RESOLUTION_AUDIT_QUERIES
    │  └─ POST_INGESTION_AUDIT_QUERIES
    ├─ Displays all queries grouped by:
    │  ├─ Type (pre-ingestion, entity resolution, post-ingestion)
    │  ├─ Severity (error, warning, info)
    │  ├─ Status (pending, approved, rejected)
    │  └─ Category (duplicates, missing fields, matches, etc.)
    ├─ User reviews and resolves ALL queries in one place
    ├─ Resolution options vary by query type:
    │  ├─ Pre-ingestion: skip_record, use_first, use_second, merge, manual_fix
    │  ├─ Entity resolution: approve_match, reject_match, manual_match, skip
    │  └─ Post-ingestion: fix_source, accept_as_is, manual_fix, flag_for_investigation
    ├─ Batch actions available:
    │  ├─ Approve all high-confidence matches
    │  ├─ Reject all low-confidence matches
    │  └─ Filter by type/severity
    └─ State: AUDIT_RESOLUTIONS (unified)

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 8: EXECUTION OF APPROVED QUERIES                          │
└──────────────────────────────────────────────────────────────────┘
14. AUDIT QUERY EXECUTION AGENT ⭐ NEW
    ├─ Input: Approved audit resolutions
    ├─ Process:
    │  ├─ Execute pre-ingestion resolutions (if not already applied)
    │  ├─ Execute entity resolution matches (create CORRESPONDS_TO)
    │  ├─ Execute post-ingestion fixes (if applicable)
    │  └─ Track all executions in audit trail
    ├─ Output: Updated knowledge graph
    └─ State: AUDIT_EXECUTION_TRAIL

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 9: FINAL AUDIT REPORT                                     │
└──────────────────────────────────────────────────────────────────┘
15. AUDIT REPORT GENERATION
    ├─ Consolidates all audit trails
    ├─ Generates comprehensive report:
    │  ├─ Pre-ingestion issues resolved
    │  ├─ Ingestion statistics
    │  ├─ Entity resolution decisions
    │  ├─ Post-ingestion issues found
    │  ├─ Outstanding issues
    │  └─ User decisions log
    ├─ Output: Final audit report
    └─ State: FINAL_AUDIT_REPORT

16. KNOWLEDGE GRAPH (Source of Truth)
    ├─ Validated and user-approved
    ├─ Complete provenance
    ├─ Full audit trail
    └─ Ready for use

📦 Session State Structure (Modified)
session_state = {
    # Phase 1: Planning
    "approved_user_goal": {...},
    "approved_files": [...],
    "approved_construction_plan": {...},
    "approved_entity_types": [...],
    "approved_fact_types": {...},
    
    # Phase 2: Quality Rules
    "data_quality_rules": [...],
    
    # Phase 3-6: Audit Queries (collected, not shown yet)
    "pre_ingestion_audit_queries": {
        "pre_ing_001": {
            "query_id": "pre_ing_001",
            "type": "pre_ingestion",
            "category": "duplicate_unique_identifier",
            "status": "pending_review",
            "evidence": {...},
            "cypher_query": "...",
            "user_decision": null,
            "decided_at": null
        }
    },
    
    "entity_resolution_audit_queries": {
        "entity_res_001": {
            "query_id": "entity_res_001",
            "type": "entity_resolution",
            "status": "pending_review",
            "proposed_action": {...},
            "evidence": {...},
            "cypher_query": "...",
            "user_decision": null
        }
    },
    
    "post_ingestion_audit_queries": {
        "post_ing_001": {
            "query_id": "post_ing_001",
            "type": "post_ingestion",
            "category": "missing_required_relationship",
            "status": "pending_review",
            "rule_id": "artwork_must_have_creator",
            "violations": [...],
            "cypher_query": "...",
            "user_decision": null
        }
    },
    
    # Phase 4: Ingestion Tracking
    "ingestion_audit_trail": {...},
    
    # Phase 7: Unified Resolutions
    "audit_resolutions": {
        "pre_ing_001": {
            "resolution": "use_first",
            "notes": "First record is correct",
            "resolved_at": "2024-01-15T10:30:00"
        },
        "entity_res_001": {
            "resolution": "approve_match",
            "notes": "High confidence match",
            "resolved_at": "2024-01-15T10:35:00"
        },
        "post_ing_001": {
            "resolution": "manual_fix",
            "notes": "Will fix in source data",
            "resolved_at": "2024-01-15T10:40:00"
        }
    },
    
    # Phase 8: Execution Trail
    "audit_execution_trail": {
        "pre_ing_001": {
            "executed_at": "2024-01-15T10:45:00",
            "result": "success",
            "nodes_affected": 2
        }
    },
    
    # Phase 9: Final Report
    "final_audit_report": {...}
}

🔄 Key Changes from Current Architecture

1. **Deferred Query Display**
   - ❌ OLD: Queries shown immediately after each agent
   - ✅ NEW: Queries stored in state, shown all together at end

2. **Non-Blocking Agents**
   - ❌ OLD: Agents wait for user resolution before continuing
   - ✅ NEW: Agents create queries and continue, no blocking

3. **Unified Review Interface**
   - ❌ OLD: Separate review interfaces for each query type
   - ✅ NEW: Single interface showing all query types together

4. **Batch Resolution**
   - ❌ OLD: Resolve queries one by one as they appear
   - ✅ NEW: Review and resolve all queries in one session

5. **Execution Phase**
   - ❌ OLD: Queries executed immediately after approval
   - ✅ NEW: All approved queries executed together in dedicated phase

🛠️ Implementation Requirements

**New Components:**
1. Unified Audit Review Interface (UI/Agent)
   - Tool: `get_all_audit_queries()` - collects from all three sources
   - Tool: `resolve_audit_query()` - extended to handle all types
   - Tool: `batch_resolve_queries()` - resolve multiple at once
   - UI: Streamlit interface showing all queries grouped by type

2. Audit Query Execution Agent
   - Tool: `execute_approved_queries()` - runs all approved queries
   - Tool: `get_execution_status()` - tracks execution progress
   - Applies resolutions in correct order (pre-ingestion → entity → post)

**Modified Components:**
1. Pre-Ingestion Audit Agent
   - Remove: Immediate query display/prompting
   - Keep: Query creation and storage
   - Add: Summary message: "Created X audit queries for review"

2. Entity Resolution Audit Agent
   - Remove: Immediate match approval prompt
   - Keep: Match proposal and query creation
   - Add: Summary message: "Created X entity match proposals for review"

3. Post-Ingestion Audit Agent
   - Remove: Immediate issue display
   - Keep: Issue detection and query creation
   - Add: Summary message: "Created X quality issues for review"

**State Keys (Add to constants.py):**
```python
ENTITY_RESOLUTION_AUDIT_QUERIES = "entity_resolution_audit_queries"
POST_INGESTION_AUDIT_QUERIES = "post_ingestion_audit_queries"
AUDIT_EXECUTION_TRAIL = "audit_execution_trail"
```

✅ Benefits

1. **Better User Experience**
   - Review all issues in context
   - See patterns across query types
   - Make informed decisions with full picture

2. **Efficient Workflow**
   - No interruption between agents
   - Batch processing of similar queries
   - Single review session instead of multiple

3. **Complete Overview**
   - See all issues before making decisions
   - Understand impact of resolutions
   - Better prioritization (errors first, then warnings)

4. **Flexible Resolution**
   - Resolve in any order
   - Change decisions before execution
   - Review all before committing

🎯 Success Criteria

- [ ] All three audit query types collected without blocking
- [ ] Unified review interface shows all queries together
- [ ] Queries grouped by type, severity, and status
- [ ] Batch resolution actions available
- [ ] All approved queries execute in correct order
- [ ] Complete audit trail maintained
- [ ] User can review and change decisions before execution

📊 Query Flow Diagram

```
Agent 1 (Pre-Ingestion) → Create Queries → Store in State → Continue
Agent 2 (KG Construction) → Build Graph → Continue
Agent 3 (Entity Resolution) → Create Queries → Store in State → Continue
Agent 4 (Post-Ingestion) → Create Queries → Store in State → Continue
                                                              ↓
                    Unified Audit Review Interface ← Collect All Queries
                                                              ↓
                    User Reviews & Resolves All Queries
                                                              ↓
                    Audit Query Execution Agent → Execute Approved Queries
                                                              ↓
                    Final Audit Report → Complete
```

This architecture provides a streamlined workflow where users see and resolve all audit queries together at the end, providing better context and more efficient decision-making.

