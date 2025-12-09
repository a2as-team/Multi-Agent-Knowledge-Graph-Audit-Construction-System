🏗️ FINAL ARCHITECTURE: Content Audit System

📊 System Overview
┌─────────────────────────────────────────────────────────────┐
│          SETU CONTENT AUDIT SYSTEM                          │
│   Multi-Agent Knowledge Graph Construction & Validation     │
└─────────────────────────────────────────────────────────────┘
GOAL: Build a knowledge graph as "source of truth" 
      with complete user verification and audit trail

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
7. DATA QUALITY RULES AGENT ⭐ NEW
   ├─ Input: User requirements, schema, entity/fact types
   ├─ Output: Custom quality rules
   ├─ Rules Types:
   │  ├─ Required relationships
   │  ├─ Temporal constraints
   │  ├─ Cardinality constraints
   │  ├─ Value constraints
   │  └─ Custom business logic
   └─ State: DATA_QUALITY_RULES
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: PRE-INGESTION VALIDATION                               │
└──────────────────────────────────────────────────────────────────┘
8. PRE-INGESTION AUDIT AGENT ⭐ NEW
   ├─ Input: CSV/markdown files, schema
   ├─ Scans for:
   │  ├─ Duplicate unique identifiers
   │  ├─ Missing required fields
   │  ├─ Invalid foreign key references
   │  ├─ Data type mismatches
   │  └─ Schema violations
   ├─ Output: Audit queries (NOT executed)
   └─ State: PRE_INGESTION_AUDIT_QUERIES
9. AUDIT REVIEW INTERFACE (User Reviews Pre-Ingestion)
   ├─ User reviews each audit query
   ├─ For each issue, user chooses:
   │  ├─ Skip record
   │  ├─ Use first/second (for duplicates)
   │  ├─ Merge records
   │  ├─ Manual fix
   │  └─ Reject (investigate)
   ├─ User approves queries to execute
   └─ State: AUDIT_RESOLUTIONS
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: KNOWLEDGE GRAPH CONSTRUCTION                           │
└──────────────────────────────────────────────────────────────────┘
10. KG CONSTRUCTION PART I (Domain Graph) 🔧 MODIFIED
    ├─ Input: Construction plan, CSV files, audit resolutions
    ├─ Process:
    │  ├─ Apply user resolutions from pre-ingestion audit
    │  ├─ Create constraints
    │  ├─ Load nodes from CSV
    │  ├─ Create relationships from CSV
    │  └─ Track ingestion actions (audit trail)
    ├─ Output: Domain Graph in Neo4j
    └─ State: INGESTION_AUDIT_TRAIL
11. KG CONSTRUCTION PART II (Subject & Lexical Graphs) 🔧 MODIFIED
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
│ PHASE 5: ENTITY RESOLUTION (AS AUDIT QUERIES)                   │
└──────────────────────────────────────────────────────────────────┘
12. ENTITY RESOLUTION AUDIT AGENT ⭐ NEW
    ├─ Input: Domain Graph, Subject Graph
    ├─ Process:
    │  ├─ Find entities with same label in both graphs
    │  ├─ Calculate similarity scores (fuzzy matching)
    │  ├─ Generate match proposals as audit queries
    │  └─ Include evidence: scores, context, alternatives
    ├─ Output: Entity resolution audit queries (NOT executed)
    └─ State: ENTITY_RESOLUTION_AUDIT_QUERIES
13. AUDIT REVIEW INTERFACE (User Reviews Entity Matches)
    ├─ User reviews each proposed entity match
    ├─ User sees:
    │  ├─ Subject entity (from text)
    │  ├─ Proposed domain match
    │  ├─ Similarity score
    │  ├─ Source context
    │  └─ Alternative matches
    ├─ User decides:
    │  ├─ Approve match
    │  ├─ Reject match
    │  ├─ Manual match (different entity)
    │  └─ Skip (keep unresolved)
    └─ State: AUDIT_RESOLUTIONS (updated)
14. ENTITY RESOLUTION EXECUTION
    ├─ Execute approved entity match queries
    ├─ Create CORRESPONDS_TO relationships
    ├─ Track what was done
    └─ State: ENTITY_RESOLUTION_AUDIT_TRAIL
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 6: POST-INGESTION VALIDATION                              │
└──────────────────────────────────────────────────────────────────┘
15. POST-INGESTION AUDIT AGENT ⭐ NEW
    ├─ Input: Complete KG, data quality rules
    ├─ Generates audit queries for:
    │  ├─ Required relationship violations
    │  ├─ Temporal constraint violations
    │  ├─ Orphaned nodes
    │  ├─ Unresolved entities (in Subject but not Domain)
    │  ├─ Domain vs Subject inconsistencies
    │  ├─ Custom rule violations
    │  └─ Coverage issues (unused fact types)
    ├─ Output: Post-ingestion audit queries
    └─ State: POST_INGESTION_AUDIT_QUERIES
16. AUDIT REVIEW INTERFACE (User Reviews Quality Issues)
    ├─ User reviews each quality issue
    ├─ User sees:
    │  ├─ Issue description
    │  ├─ Affected entities
    │  ├─ Source documents (provenance)
    │  ├─ Evidence text
    │  └─ Severity
    ├─ User decides:
    │  ├─ Fix source data and re-ingest
    │  ├─ Accept as-is (acknowledge issue)
    │  ├─ Manual fix in graph
    │  └─ Flag for investigation
    └─ State: POST_INGESTION_RESOLUTIONS
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 7: FINAL AUDIT REPORT & GRAPH VALIDATION                  │
└──────────────────────────────────────────────────────────────────┘
17. AUDIT REPORT GENERATION
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
18. KNOWLEDGE GRAPH (Source of Truth)
    ├─ Validated and user-approved
    ├─ Complete provenance
    ├─ Full audit trail
    └─ Ready for use

🗄️ Graph Structure in Neo4j
┌─────────────────────────────────────────────────────────┐
│ DOMAIN GRAPH (From CSV - Structured Data)              │
│                                                         │
│ (:Artist {name: "Pablo Picasso", birth_year: 1881})   │
│ (:Artwork {title: "Guernica", year: 1937})            │
│ (:Location {name: "Madrid"})                           │
│                                                         │
│ (Artwork)-[:CREATED_BY]->(Artist)                      │
│ (Artwork)-[:LOCATED_AT]->(Location)                    │
└─────────────────────────────────────────────────────────┘
                         ↕ CORRESPONDS_TO
┌─────────────────────────────────────────────────────────┐
│ SUBJECT GRAPH (From Markdown - Extracted Entities)     │
│                                                         │
│ (:__Entity__ {label:"Artist", name:"Pablo Picasso"})  │
│ (:__Entity__ {label:"Location", name:"Málaga"})       │
│ (:__Entity__ {label:"ArtMovement", name:"Cubism"})    │
│                                                         │
│ (Artist)-[:born_in]->(Location)                        │
│ (Artist)-[:founded_art_movement]->(ArtMovement)       │
└─────────────────────────────────────────────────────────┘
                         ↓ MENTIONED_IN
┌─────────────────────────────────────────────────────────┐
│ LEXICAL GRAPH (Source Documents & Chunks)              │
│                                                         │
│ (:Document {path: "artist_bios.md"})                   │
│   -[:HAS_CHUNK]->                                      │
│ (:Chunk {text: "Pablo Picasso was born...", pos: 1})  │
│   -[:NEXT_CHUNK]->                                     │
│ (:Chunk {text: "He co-founded Cubism...", pos: 2})    │
└─────────────────────────────────────────────────────────┘

📦 Session State Structure
session_state = {
    # Phase 1: Planning
    "approved_user_goal": {...},
    "approved_files": [...],
    "approved_construction_plan": {...},
    "approved_entity_types": [...],
    "approved_fact_types": {...},
    
    # Phase 2: Quality Rules
    "data_quality_rules": [
        {
            "rule_id": "artwork_must_have_creator",
            "type": "required_relationship",
            "entity": "Artwork",
            "relationship": "CREATED_BY",
            "target": "Artist",
            "severity": "error"
        },
        # ... more rules
    ],
    
    # Phase 3: Pre-Ingestion Audits
    "pre_ingestion_audit_queries": {
        "pre_ing_001": {
            "query_id": "pre_ing_001",
            "type": "pre_ingestion",
            "category": "duplicate_unique_identifier",
            "status": "pending_review",  # approved, rejected, executed
            "evidence": {...},
            "cypher_query": "...",
            "user_decision": null,
            "decided_at": null
        },
        # ... more audit queries
    },
    
    # Phase 3: User Resolutions
    "audit_resolutions": {
        "pre_ing_001": {
            "resolution": "use_first",
            "notes": "First record is correct",
            "resolved_at": "2024-01-15T10:30:00"
        },
        # ... more resolutions
    },
    
    # Phase 4: Ingestion Tracking
    "ingestion_audit_trail": {
        "artworks.csv": {
            "total_rows": 100,
            "imported": 95,
            "skipped": 3,
            "modified": 2,
            "details": [...]
        },
        # ... more files
    },
    
    # Phase 5: Entity Resolution
    "entity_resolution_audit_queries": {
        "entity_res_001": {
            "query_id": "entity_res_001",
            "type": "entity_resolution",
            "status": "pending_review",
            "proposed_action": {
                "action": "create_corresponds_to",
                "confidence": "high"
            },
            "evidence": {
                "similarity_score": 0.85,
                "source_context": {...}
            },
            "cypher_query": "...",
            "user_decision": null
        },
        # ... more entity matches
    },
    
    # Phase 6: Post-Ingestion Audits
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
        },
        # ... more quality issues
    },
    
    # Phase 7: Final Report
    "final_audit_report": {
        "generated_at": "2024-01-15T15:00:00",
        "summary": {
            "total_audit_queries": 150,
            "approved": 120,
            "rejected": 20,
            "outstanding": 10
        },
        "sections": [...]
    }
}

🎯 Audit Query Lifecycle
┌──────────────────────┐
│ AUDIT QUERY CREATED  │
│ Status: pending      │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ USER REVIEWS         │
│ - Views evidence     │
│ - Makes decision     │
└──────────┬───────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌─────────┐  ┌──────────┐
│APPROVED │  │ REJECTED │
└────┬────┘  └──────────┘
     ↓
┌──────────────────────┐
│ QUERY EXECUTED       │
│ - Runs Cypher        │
│ - Records results    │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ AUDIT TRAIL UPDATED  │
│ Status: executed     │
└──────────────────────┘

🛠️ New Agents to Implement
Agent
Priority
Complexity
Estimated Time
Data Quality Rules Agent
1
Medium
3-4 hours
Pre-Ingestion Audit Agent
2
Medium
4-5 hours
Entity Resolution Audit Agent
3
Medium
4-5 hours
Post-Ingestion Audit Agent
4
Medium
4-5 hours
Audit Review Interface (UI)
5
High
6-8 hours

Total Implementation Time: ~25-30 hours
🔧 Modifications to Existing Components
KG Construction Tools
Add audit resolution support
Track ingestion actions
Generate audit trail
All Existing Agents
Add orchestrator pattern for conversational flow
Fix "No specific message" issue
Session State Management
Add audit query storage
Add resolution tracking
Add audit trail storage

📊 Key Principles
✅ Nothing Auto-Executes - All actions become audit queries first
✅ User Validates Everything - Complete control and visibility
✅ Full Provenance - Every fact traceable to source
✅ Complete Audit Trail - Who did what, when, why
✅ Source of Truth - KG validated and user-approved

🎯 Success Criteria
[ ] User can define custom quality rules
[ ] All data conflicts detected before ingestion
[ ] User reviews and resolves all conflicts
[ ] Entity resolution requires user approval
[ ] Post-ingestion quality validated against rules
[ ] Complete audit trail maintained
[ ] Knowledge graph is user-verified source of truth
[ ] All issues have provenance (source documents)
This is the complete, final architecture incorporating all our discussions! 🎉

🔄 Entity Resolution as Audit Queries
Current (Automatic) Approach - RISKY:
// Automatically creates relationships based on fuzzy match
MATCH (entity:Artist:`__Entity__` {name: "P. Picasso"})
MATCH (domain:Artist {name: "Pablo Picasso"})
WHERE jaroWinklerDistance(...) < 0.1
MERGE (entity)-[:CORRESPONDS_TO]->(domain)  ❌ No user review!
Problem:
What if "P. Picasso" is actually "Paolo Picasso" not "Pablo Picasso"?
Automatic linkage creates wrong connections
User has no visibility into why match was made

Proposed (Audit-Based) Approach - SAFE:
┌─────────────────────────────────────────────────┐
│ ENTITY RESOLUTION AUDIT AGENT                   │
└─────────────────────────────────────────────────┘
STEP 1: Analyze potential matches
├─ Find entities with same label in both graphs
├─ Calculate similarity scores
└─ Generate match proposals
STEP 2: Create audit query (NOT execute)
├─ Query ID: "entity_resolution_001"
├─ Type: "entity_match_proposal"
├─ Proposed action: Link entity X to node Y
├─ Evidence: Similarity score, property comparison
└─ Status: "pending_user_review"
STEP 3: User reviews audit query
├─ User sees: "Entity 'P. Picasso' in provenance_notes.md might be 'Pablo Picasso' from artists.csv"
├─ User sees: Similarity score: 0.85, Properties: name match
├─ User sees: Source text snippet
└─ User decides: ✅ Approve | ❌ Reject | ⚙️ Manual Match
STEP 4: Only after approval, execute
└─ Create CORRESPONDS_TO relationship

📋 Audit Query Structure
Every Audit Query Contains:
audit_query = {
    "query_id": "entity_resolution_artist_001",
    "type": "entity_resolution",
    "category": "entity_match_proposal",
    "status": "pending_review",
    
    # What this query proposes to do
    "proposed_action": {
        "action": "create_relationship",
        "relationship_type": "CORRESPONDS_TO",
        "from_entity": {
            "graph": "subject",
            "label": "Artist",
            "id": "entity_12345",
            "name": "P. Picasso",
            "properties": {...}
        },
        "to_entity": {
            "graph": "domain",
            "label": "Artist", 
            "id": "artist_101",
            "name": "Pablo Picasso",
            "properties": {...}
        }
    },
    
    # Why this match is proposed
    "evidence": {
        "similarity_score": 0.85,
        "matching_properties": ["name"],
        "property_comparison": {
            "name": {
                "subject": "P. Picasso",
                "domain": "Pablo Picasso",
                "score": 0.85
            }
        },
        "source_context": {
            "file": "provenance_notes.md",
            "chunk": "The painting was acquired by P. Picasso in 1920...",
            "line_range": "45-47"
        }
    },
    
    # The Cypher query to execute IF approved
    "cypher_query": """
        MATCH (entity:`__Entity__` {id: 'entity_12345'})
        MATCH (domain:Artist {id: 'artist_101'})
        MERGE (entity)-[:CORRESPONDS_TO]->(domain)
        RETURN entity, domain
    """,
    
    # User decision
    "user_decision": null,  // null, "approved", "rejected", "manual_override"
    "decided_at": null,
    "decision_notes": null
}

🎯 Complete Audit Query Types
1. Pre-Ingestion Audits
# Duplicate ID detection
{
    "query_id": "pre_ing_duplicate_001",
    "type": "pre_ingestion",
    "category": "duplicate_unique_identifier",
    "status": "pending_review",
    "proposed_action": {
        "action": "resolve_conflict",
        "options": ["use_first", "use_second", "merge", "skip_both"]
    },
    "evidence": {
        "file": "artworks.csv",
        "column": "artwork_id",
        "duplicate_value": 1,
        "conflicts": [
            {"row": 2, "data": {"title": "Guernica", "artist_id": 101}},
            {"row": 3, "data": {"title": "Guernica Copy", "artist_id": 102}}
        ]
    },
    "cypher_query": null  // No query until user decides
}
2. Entity Resolution Audits
# Entity matching proposal
{
    "query_id": "entity_res_001",
    "type": "entity_resolution",
    "category": "entity_match_proposal",
    "status": "pending_review",
    "proposed_action": {
        "action": "create_corresponds_to",
        "confidence": "high"  // based on similarity score
    },
    "evidence": {...},
    "cypher_query": "MERGE (entity)-[:CORRESPONDS_TO]->(domain)"
}
3. Post-Ingestion Quality Audits
# Missing required relationship
{
    "query_id": "post_ing_quality_001",
    "type": "post_ingestion",
    "category": "missing_required_relationship",
    "status": "pending_review",
    "proposed_action": {
        "action": "flag_for_manual_fix",
        "severity": "error"
    },
    "evidence": {
        "rule_id": "artwork_must_have_creator",
        "violations": [
            {
                "artwork_id": 10,
                "title": "Unknown Work",
                "issue": "No CREATED_BY relationship"
            }
        ]
    },
    "cypher_query": """
        MATCH (artwork:Artwork {id: 10})
        WHERE NOT (artwork)-[:CREATED_BY]->(:Artist)
        RETURN artwork
    """
}
4. Data Consistency Audits
# Domain vs Subject contradiction
{
    "query_id": "consistency_001",
    "type": "consistency_check",
    "category": "domain_subject_mismatch",
    "status": "pending_review",
    "proposed_action": {
        "action": "flag_for_review",
        "options": ["trust_database", "trust_document", "investigate"]
    },
    "evidence": {
        "entity": "Guernica",
        "property": "location",
        "database_value": "Madrid",
        "document_value": "New York",
        "source": {
            "domain": "artworks.csv, row 5",
            "subject": "provenance_notes.md, lines 23-25"
        }
    },
    "cypher_query": null  // Investigation query, not auto-fix
}

🔄 Audit Query Workflow
┌─────────────────────────────────────────────────┐
│ AUDIT QUERY GENERATION                          │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ AUDIT QUERY STORAGE                             │
│ Status: "pending_review"                        │
│ - All queries stored in session state           │
│ - User can review in batch or individually      │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ USER REVIEW (UI/Agent)                          │
│ For each audit query:                           │
│ - Show evidence and proposed action             │
│ - User decides: Approve/Reject/Modify           │
│ - Update query status                           │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ AUDIT QUERY EXECUTION                           │
│ For approved queries:                           │
│ - Execute Cypher query                          │
│ - Track results                                 │
│ - Update status to "executed"                   │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ AUDIT TRAIL                                     │
│ - What was done                                 │
│ - Who approved it                               │
│ - When it was executed                          │
│ - Results                                       │
└─────────────────────────────────────────────────┘

🛠️ Implementation: Session State Structure
# All audit queries stored here
AUDIT_QUERIES = {
    "entity_resolution_001": {
        "query_id": "entity_resolution_001",
        "type": "entity_resolution",
        "status": "pending_review",  # or "approved", "rejected", "executed"
        "created_at": "2024-01-15T10:00:00",
        "proposed_action": {...},
        "evidence": {...},
        "cypher_query": "...",
        "user_decision": null,
        "decided_at": null,
        "executed_at": null,
        "execution_result": null
    },
    "pre_ing_duplicate_001": {...},
    "post_ing_quality_001": {...},
    # ... more audit queries
}
# Summary for UI
AUDIT_SUMMARY = {
    "total_queries": 150,
    "pending_review": 45,
    "approved": 80,
    "rejected": 15,
    "executed": 75,
    "by_type": {
        "entity_resolution": 30,
        "pre_ingestion": 20,
        "post_ingestion": 50,
        "consistency_check": 50
    },
    "by_severity": {
        "critical": 5,
        "error": 20,
        "warning": 70,
        "info": 55
    }
}

📊 User Review Interface (Example)
╔═══════════════════════════════════════════════════════════╗
║ AUDIT QUERY REVIEW                                        ║
║ Query ID: entity_resolution_001                           ║
║ Type: Entity Resolution - Match Proposal                  ║
║ Status: Pending Review                                    ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║ PROPOSED ACTION:                                          ║
║ Link subject entity to domain node                        ║
║                                                           ║
║ SUBJECT ENTITY (from text):                               ║
║ ├─ Label: Artist                                          ║
║ ├─ Name: "P. Picasso"                                     ║
║ └─ Source: provenance_notes.md, lines 45-47              ║
║    "The painting was acquired by P. Picasso in 1920..."  ║
║                                                           ║
║ DOMAIN NODE (from database):                              ║
║ ├─ Label: Artist                                          ║
║ ├─ Name: "Pablo Picasso"                                  ║
║ ├─ Birth Year: 1881                                       ║
║ └─ Source: artists.csv, row 5                            ║
║                                                           ║
║ MATCH CONFIDENCE:                                         ║
║ ├─ Similarity Score: 0.85 (High)                         ║
║ ├─ Name Match: "P. Picasso" ≈ "Pablo Picasso"           ║
║ └─ Algorithm: Jaro-Winkler Distance                      ║
║                                                           ║
║ OTHER POSSIBLE MATCHES:                                   ║
║ ├─ "Paolo Picasso" (Score: 0.78)                        ║
║ └─ "Pierre Picasso" (Score: 0.72)                       ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║ YOUR DECISION:                                            ║
║ [ ✓ Approve ] [ ✗ Reject ] [ ⚙ Manual Match ]           ║
║                                                           ║
║ Notes: _________________________________________          ║
╚═══════════════════════════════════════════════════════════╝
Batch Actions: [Approve All High Confidence] [Reject All Low Confidence]

🎯 Modified Agent Workflows
Entity Resolution Agent (NEW Workflow):
def entity_resolution_agent():
    """
    Generates entity match proposals as audit queries,
    NOT automatic linkages.
    """
    
    # Find potential matches
    potential_matches = find_entity_match_candidates()
    
    for match in potential_matches:
        # Calculate similarity
        score = calculate_similarity(match.subject, match.domain)
        
        # Generate audit query (don't execute!)
        audit_query = {
            "query_id": f"entity_res_{match.id}",
            "type": "entity_resolution",
            "status": "pending_review",
            "proposed_action": {
                "action": "create_corresponds_to",
                "confidence": get_confidence_level(score)
            },
            "evidence": {
                "similarity_score": score,
                "source_context": get_source_context(match.subject),
                "other_candidates": find_other_matches(match.subject)
            },
            "cypher_query": generate_link_query(match),
            "user_decision": null
        }
        
        # Store for review
        session.state["audit_queries"][audit_query["query_id"]] = audit_query
    
    return {
        "status": "success",
        "message": f"Generated {len(potential_matches)} entity resolution proposals",
        "pending_review": len(potential_matches)
    }

✅ Benefits of This Approach
Aspect
Automatic Execution
Audit-Based (Your Proposal)
Control
❌ System decides
✅ User decides
Transparency
❌ Hidden decisions
✅ Full visibility
Accuracy
⚠️ Can make mistakes
✅ Human verification
Audit Trail
❌ Limited
✅ Complete history
Trust
⚠️ Blind trust in algorithm
✅ User validates everything
Flexibility
❌ Fixed thresholds
✅ Case-by-case judgment


🎯 Summary
Your proposal:
✅ ALL actions become audit queries first - nothing auto-executes
✅ User reviews every query - sees evidence, makes decision
✅ Only approved queries execute - full control
✅ Complete audit trail - who approved what, when, why
This applies to:
Entity resolution (your new insight!)
Pre-ingestion conflicts
Post-ingestion quality checks
Data consistency issues
Result:
Knowledge graph becomes true "source of truth" because every fact is user-verified
Full transparency and traceability
No silent failures or automatic wrong decisions
Should we start implementing this architecture? Which agent should we build first:
Data Quality Rules Agent (define rules)
Pre-Ingestion Audit Agent (scan before load)
Entity Resolution Audit Agent (propose matches)
Audit Review Interface (UI for approving queries)

