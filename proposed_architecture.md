🏗️ PROPOSED ARCHITECTURE: Unified Audit Review System

📊 System Overview
┌─────────────────────────────────────────────────────────────┐
│          SETU CONTENT AUDIT SYSTEM                          │
│   Multi-Agent Knowledge Graph Construction & Validation     │
│   ⭐ NEW: Two-Stage Audit Review                            │
└─────────────────────────────────────────────────────────────┘
GOAL: Build a knowledge graph as "source of truth" 
      with complete user verification and audit trail
      
TWO-STAGE RESOLUTION:
  Stage 1: Pre-ingestion queries resolved immediately (BLOCKS Phase 4)
  Stage 2: Entity + Post-ingestion queries reviewed together at end

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
8. PRE-INGESTION AUDIT AGENT
   ├─ Input: CSV/markdown files, schema
   ├─ Scans for:
   │  ├─ Duplicate unique identifiers
   │  ├─ Missing required fields
   │  ├─ Invalid foreign key references
   │  ├─ Data type mismatches
   │  └─ Schema violations
   ├─ Output: Audit queries (stored in state)
   └─ State: PRE_INGESTION_AUDIT_QUERIES

9. PRE-INGESTION REVIEW INTERFACE ⭐ BLOCKING
   ├─ Input: Pre-ingestion audit queries
   ├─ Behavior: **BLOCKS Phase 4 until all queries resolved**
   ├─ User reviews and resolves pre-ingestion queries:
   │  ├─ skip_record
   │  ├─ use_first, use_second
   │  ├─ merge
   │  ├─ manual_fix
   │  └─ reject (investigate)
   ├─ Output: Resolved pre-ingestion queries
   └─ State: AUDIT_RESOLUTIONS (pre-ingestion only)

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: KNOWLEDGE GRAPH CONSTRUCTION                           │
└──────────────────────────────────────────────────────────────────┘
10. KG CONSTRUCTION PART I (Domain Graph)
    ├─ Input: Construction plan, CSV files, pre-ingestion resolutions
    ├─ **Prerequisite: All pre-ingestion queries must be resolved**
    ├─ Process:
    │  ├─ Create constraints
    │  ├─ Load nodes from CSV (applies pre-ingestion resolutions)
    │  ├─ Create relationships from CSV
    │  └─ Track ingestion actions (audit trail)
    ├─ Output: Domain Graph in Neo4j
    └─ State: INGESTION_AUDIT_TRAIL

11. KG CONSTRUCTION PART II (Subject & Lexical Graphs)
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
12. ENTITY RESOLUTION AUDIT AGENT ⭐ MODIFIED
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
13. POST-INGESTION AUDIT AGENT ⭐ MODIFIED
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
14. UNIFIED AUDIT REVIEW INTERFACE
    ├─ Input: Entity resolution + Post-ingestion audit queries
    ├─ Collects queries from:
    │  ├─ ENTITY_RESOLUTION_AUDIT_QUERIES
    │  └─ POST_INGESTION_AUDIT_QUERIES
    ├─ **Pre-ingestion queries**: Shown as read-only "already processed"
    ├─ Displays queries grouped by:
    │  ├─ Type (entity resolution, post-ingestion)
    │  ├─ Severity (error, warning, info)
    │  ├─ Status (pending, approved, rejected)
    │  └─ Category (matches, violations, inconsistencies, etc.)
    ├─ User reviews and resolves Entity + Post-ingestion queries
    ├─ Resolution options:
    │  ├─ Entity resolution: approve_match, reject_match, manual_match, skip
    │  └─ Post-ingestion: fix_source, accept_as_is, manual_fix, flag_for_investigation
    ├─ Batch actions available:
    │  ├─ Approve all high-confidence matches
    │  ├─ Reject all low-confidence matches
    │  └─ Filter by type/severity
    └─ State: AUDIT_RESOLUTIONS (entity + post-ingestion)

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 8: EXECUTION OF APPROVED QUERIES                          │
└──────────────────────────────────────────────────────────────────┘
15. AUDIT QUERY EXECUTION AGENT ⭐ NEW
    ├─ Input: Approved audit resolutions (entity + post-ingestion)
    ├─ **Note: Pre-ingestion resolutions already applied in Phase 4**
    ├─ Process:
    │  ├─ Execute entity resolution matches (create CORRESPONDS_TO)
    │  ├─ Execute post-ingestion fixes (if applicable)
    │  └─ Track all executions in audit trail
    ├─ Output: Updated knowledge graph
    └─ State: AUDIT_EXECUTION_TRAIL

┌──────────────────────────────────────────────────────────────────┐
│ PHASE 9: FINAL AUDIT REPORT                                     │
└──────────────────────────────────────────────────────────────────┘
16. AUDIT REPORT GENERATION
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

17. KNOWLEDGE GRAPH (Source of Truth)
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
    
    # Phase 3.5: Pre-Ingestion Resolutions (applied in Phase 4)
    "pre_ingestion_resolutions": {
        "pre_ing_001": {
            "resolution": "use_first",
            "notes": "First record is correct",
            "resolved_at": "2024-01-15T10:30:00",
            "applied_in_phase": 4
        }
    },
    
    # Phase 4: Ingestion Tracking
    "ingestion_audit_trail": {...},
    
    # Phase 7: Unified Resolutions (Entity + Post-Ingestion)
    "audit_resolutions": {
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

1. **Two-Stage Resolution**
   - ❌ OLD: All queries shown immediately after each agent
   - ✅ NEW: 
     - **Stage 1**: Pre-ingestion queries resolved immediately (BLOCKS Phase 4)
     - **Stage 2**: Entity + Post-ingestion queries reviewed together at end

2. **Pre-Ingestion Blocking**
   - ❌ OLD: Pre-ingestion queries could be deferred
   - ✅ NEW: Pre-ingestion queries MUST be resolved before KG Construction
   - **Reason**: Avoids re-ingestion if resolved later

3. **Unified Review Interface (Partial)**
   - ❌ OLD: Separate review interfaces for each query type
   - ✅ NEW: Single interface for Entity + Post-ingestion queries
   - Pre-ingestion queries shown as read-only "already processed"

4. **Non-Blocking Agents (Entity + Post)**
   - ❌ OLD: Agents wait for user resolution before continuing
   - ✅ NEW: Entity/Post-ingestion agents create queries and continue
   - Pre-ingestion agent blocks until resolution

5. **Execution Phase**
   - ❌ OLD: Queries executed immediately after approval
   - ✅ NEW: 
     - Pre-ingestion resolutions applied during Phase 4 ingestion
     - Entity + Post-ingestion resolutions executed together in Phase 8

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
   - Keep: Query creation and storage
   - Add: Immediate review interface (BLOCKING)
   - Behavior: Cannot proceed to Phase 4 until all queries resolved

2. Pre-Ingestion Review Interface (NEW)
   - Tool: `get_pre_ingestion_audit_queries()` - get queries
   - Tool: `resolve_audit_query()` - resolve individual query
   - Tool: `check_pre_ingestion_complete()` - verify all resolved
   - UI: Streamlit interface for pre-ingestion queries only
   - Blocks Phase 4 until completion

3. Entity Resolution Audit Agent
   - Remove: Immediate match approval prompt
   - Keep: Match proposal and query creation
   - Add: Summary message: "Created X entity match proposals for review"
   - Behavior: Non-blocking, continues after creating queries

4. Post-Ingestion Audit Agent
   - Remove: Immediate issue display
   - Keep: Issue detection and query creation
   - Add: Summary message: "Created X quality issues for review"
   - Behavior: Non-blocking, continues after creating queries

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

- [ ] Pre-ingestion queries block Phase 4 until resolved
- [ ] Entity + Post-ingestion queries collected without blocking
- [ ] Unified review interface shows Entity + Post-ingestion queries together
- [ ] Pre-ingestion queries shown as read-only in unified review
- [ ] Queries grouped by type, severity, and status
- [ ] Batch resolution actions available
- [ ] Pre-ingestion resolutions applied during Phase 4 ingestion
- [ ] Entity + Post-ingestion resolutions executed in Phase 8
- [ ] Complete audit trail maintained
- [ ] User can review and change decisions before execution

📊 Query Flow Diagram

```
STAGE 1: Pre-Ingestion (BLOCKING)
─────────────────────────────────
Pre-Ingestion Audit Agent → Create Queries → Store in State
                                    ↓
                    Pre-Ingestion Review Interface (BLOCKS)
                                    ↓
                    User Resolves All Pre-Ingestion Queries
                                    ↓
                    ✅ All Resolved → Proceed to Phase 4

STAGE 2: Entity + Post-Ingestion (Non-Blocking)
────────────────────────────────────────────────
KG Construction Part I → Build Domain Graph (uses pre-ingestion resolutions)
KG Construction Part II → Build Subject/Lexical Graphs
                                    ↓
Entity Resolution Agent → Create Queries → Store in State → Continue
Post-Ingestion Agent → Create Queries → Store in State → Continue
                                    ↓
                    Unified Audit Review Interface
                    (Entity + Post-Ingestion queries only)
                                    ↓
                    User Reviews & Resolves Queries
                                    ↓
                    Audit Query Execution Agent → Execute Approved Queries
                                    ↓
                    Final Audit Report → Complete
```

This architecture provides a streamlined workflow with:
- **Pre-ingestion queries**: Resolved immediately (blocks ingestion to avoid re-work)
- **Entity + Post-ingestion queries**: Reviewed together at the end (non-blocking, better context)
- **Efficient execution**: Pre-ingestion resolutions applied during ingestion, others executed together

