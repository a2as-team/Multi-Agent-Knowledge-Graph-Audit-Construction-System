"""
Unified Workflow UI for Setu Content Audit System

This UI orchestrates all agents in a sequential workflow according to the proposed architecture.
It allows running phases individually or the full pipeline, with state persistence between phases.

Run with: streamlit run tests/ui/unified_workflow_ui.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Agent imports
from src.agents.user_intent_agent import user_intent_agent
from src.agents.file_suggestion_agent import file_suggestion_agent
from src.agents.schema_proposal_structured_agent import schema_refinement_loop
from src.agents.file_suggestion_unstructured_agent import file_suggestion_unstructured_agent
from src.agents.ner_agent import ner_agent
from src.agents.fact_extraction_agent import fact_refinement_loop
from src.agents.data_quality_rules_agent import data_quality_rules_agent
from src.agents.pre_ingestion_audit_agent import pre_ingestion_audit_agent
from src.agents.graph_construction_agent import graph_construction_agent
from src.agents.knowledge_extraction_agent import knowledge_extraction_agent

from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_FILES,
    APPROVED_CONSTRUCTION_PLAN,
    APPROVED_ENTITIES,
    APPROVED_FACTS,
    APPROVED_QUALITY_RULES,
    PRE_INGESTION_AUDIT_QUERIES,
    AUDIT_RESOLUTIONS,
    INGESTION_AUDIT_TRAIL
)


def run_async(coro):
    """Helper to run async functions in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# Page configuration
st.set_page_config(
    page_title="Unified Workflow - Setu Content Audit",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏗️ Unified Workflow - Setu Content Audit System")
st.markdown("Orchestrate all agents in a sequential workflow to build and validate your knowledge graph")

# Initialize session state
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = {
        "phase_status": {},
        "agent_callers": {},
        "current_state": {},
        "phase_history": []
    }

if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


# Phase definitions
PHASES = {
    1: {
        "name": "Planning & Schema Definition",
        "agents": [
            {"name": "User Intent", "agent": user_intent_agent, "key": "user_intent"},
            {"name": "File Suggestion (Structured)", "agent": file_suggestion_agent, "key": "file_suggestion_structured"},
            {"name": "Schema Proposal", "agent": schema_refinement_loop, "key": "schema_proposal"},
            {"name": "File Suggestion (Unstructured)", "agent": file_suggestion_unstructured_agent, "key": "file_suggestion_unstructured"},
            {"name": "NER Agent", "agent": ner_agent, "key": "ner"},
            {"name": "Fact Extraction", "agent": fact_refinement_loop, "key": "fact_extraction"}
        ],
        "prerequisites": [],
        "blocking": False
    },
    2: {
        "name": "Data Quality Rules Definition",
        "agents": [
            {"name": "Data Quality Rules", "agent": data_quality_rules_agent, "key": "quality_rules"}
        ],
        "prerequisites": [APPROVED_CONSTRUCTION_PLAN, APPROVED_ENTITIES, APPROVED_FACTS],
        "blocking": False
    },
    3: {
        "name": "Pre-Ingestion Validation",
        "agents": [
            {"name": "Pre-Ingestion Audit", "agent": pre_ingestion_audit_agent, "key": "pre_ingestion_audit"}
        ],
        "prerequisites": [APPROVED_CONSTRUCTION_PLAN],
        "blocking": True  # Blocks Phase 4
    },
    4: {
        "name": "Knowledge Graph Construction",
        "agents": [
            {"name": "KG Construction (Domain)", "agent": graph_construction_agent, "key": "graph_construction"},
            {"name": "KG Construction (Subject/Lexical)", "agent": knowledge_extraction_agent, "key": "knowledge_extraction"}
        ],
        "prerequisites": [APPROVED_CONSTRUCTION_PLAN],
        "blocking": False,
        "requires_pre_ingestion_resolved": True
    }
}


def get_phase_status(phase_num: int) -> str:
    """Get status of a phase: pending, in_progress, completed, blocked"""
    status = st.session_state.workflow_state["phase_status"].get(phase_num, "pending")
    return status


def check_prerequisites(phase_num: int):
    """Check if prerequisites for a phase are met."""
    phase = PHASES[phase_num]
    missing = []
    
    current_state = st.session_state.workflow_state["current_state"]
    
    for prereq in phase.get("prerequisites", []):
        if prereq not in current_state or not current_state[prereq]:
            missing.append(prereq)
    
    # Special check for Phase 4: pre-ingestion queries must be resolved
    if phase_num == 4 and phase.get("requires_pre_ingestion_resolved"):
        audit_queries = current_state.get(PRE_INGESTION_AUDIT_QUERIES, {})
        if audit_queries:
            pending = [q for q in audit_queries.values() if q.get("status") == "pending_review"]
            if pending:
                missing.append(f"{len(pending)} pre-ingestion queries pending")
    
    return len(missing) == 0, missing


def update_state_from_agent(agent_caller: AgentCaller):
    """Update workflow state from agent session state."""
    try:
        session = run_async(agent_caller.get_session())
        if session and session.state:
            st.session_state.workflow_state["current_state"].update(session.state)
    except Exception as e:
        st.warning(f"Could not update state: {e}")


def initialize_agent_for_phase(phase_num: int, agent_info: Dict[str, Any]) -> Optional[AgentCaller]:
    """Initialize an agent with required state from previous phases."""
    phase = PHASES[phase_num]
    current_state = st.session_state.workflow_state["current_state"]
    
    # Build initial state based on prerequisites
    initial_state = {}
    
    # Add all available state keys that might be needed
    for key in [APPROVED_USER_GOAL, APPROVED_FILES, APPROVED_CONSTRUCTION_PLAN, 
                APPROVED_ENTITIES, APPROVED_FACTS, APPROVED_QUALITY_RULES,
                PRE_INGESTION_AUDIT_QUERIES, AUDIT_RESOLUTIONS]:
        if key in current_state:
            initial_state[key] = current_state[key]
    
    try:
        agent_caller = run_async(make_agent_caller(agent_info["agent"], initial_state=initial_state))
        return agent_caller
    except Exception as e:
        st.error(f"Error initializing {agent_info['name']}: {e}")
        return None


def run_agent_interaction(agent_caller: AgentCaller, prompt: str) -> str:
    """Run a single agent interaction."""
    try:
        response = run_async(agent_caller.call(prompt, verbose=st.session_state.verbose_logging))
        update_state_from_agent(agent_caller)
        return response
    except Exception as e:
        return f"Error: {str(e)}"


# Sidebar: Workflow Controls
with st.sidebar:
    st.header("🎛️ Workflow Controls")
    
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.workflow_state = {
            "phase_status": {},
            "agent_callers": {},
            "current_state": {},
            "phase_history": []
        }
        st.rerun()
    
    st.session_state.verbose_logging = st.checkbox("Verbose Logging", value=st.session_state.verbose_logging)
    
    st.divider()
    st.header("📊 Phase Status")
    
    for phase_num in sorted(PHASES.keys()):
        phase = PHASES[phase_num]
        status = get_phase_status(phase_num)
        prereqs_met, missing = check_prerequisites(phase_num)
        
        # Status indicator
        if status == "completed":
            icon = "✅"
        elif status == "in_progress":
            icon = "🔄"
        elif not prereqs_met:
            icon = "⏸️"
        elif phase.get("blocking"):
            icon = "🔴"
        else:
            icon = "⏳"
        
        st.markdown(f"**Phase {phase_num}:** {icon} {phase['name']}")
        
        if missing:
            st.caption(f"Missing: {', '.join(missing[:2])}")
    
    st.divider()
    st.header("📋 Current State Keys")
    current_state = st.session_state.workflow_state["current_state"]
    for key in sorted(current_state.keys()):
        value = current_state[key]
        if isinstance(value, dict):
            count = len(value) if isinstance(value, dict) else "N/A"
            st.caption(f"• {key}: {count} items")
        elif isinstance(value, list):
            st.caption(f"• {key}: {len(value)} items")
        else:
            st.caption(f"• {key}: ✓")


# Main Content: Phase Cards
st.header("📋 Workflow Phases")

for phase_num in sorted(PHASES.keys()):
    phase = PHASES[phase_num]
    status = get_phase_status(phase_num)
    prereqs_met, missing = check_prerequisites(phase_num)
    
    # Phase card
    with st.expander(
        f"**Phase {phase_num}: {phase['name']}** {'🔴 BLOCKING' if phase.get('blocking') else ''}",
        expanded=(status == "in_progress" or (status == "pending" and prereqs_met))
    ):
        # Status indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            if status == "completed":
                st.success("✅ Completed")
            elif status == "in_progress":
                st.info("🔄 In Progress")
            elif not prereqs_met:
                st.warning(f"⏸️ Prerequisites Missing ({len(missing)})")
            else:
                st.info("⏳ Pending")
        
        with col2:
            if phase.get("blocking"):
                st.error("🔴 Blocking Phase")
            else:
                st.info("🟢 Non-blocking")
        
        with col3:
            if prereqs_met:
                st.success("✅ Prerequisites Met")
            else:
                st.error(f"❌ Missing: {len(missing)}")
        
        # Show missing prerequisites
        if missing:
            st.warning(f"**Missing Prerequisites:** {', '.join(missing)}")
        
        # Agents in this phase
        st.subheader("Agents in this Phase")
        
        for agent_info in phase["agents"]:
            agent_key = f"phase_{phase_num}_{agent_info['key']}"
            
            # Check if agent caller exists
            if agent_key not in st.session_state.workflow_state["agent_callers"]:
                if st.button(f"Initialize {agent_info['name']}", key=f"init_{agent_key}"):
                    with st.spinner(f"Initializing {agent_info['name']}..."):
                        agent_caller = initialize_agent_for_phase(phase_num, agent_info)
                        if agent_caller:
                            st.session_state.workflow_state["agent_callers"][agent_key] = agent_caller
                            st.session_state.workflow_state["phase_status"][phase_num] = "in_progress"
                            st.success(f"✅ {agent_info['name']} initialized")
                            st.rerun()
            
            # Agent interaction section
            if agent_key in st.session_state.workflow_state["agent_callers"]:
                agent_caller = st.session_state.workflow_state["agent_callers"][agent_key]
                
                st.markdown(f"#### 🤖 {agent_info['name']}")
                
                # Agent chat interface
                agent_messages_key = f"messages_{agent_key}"
                if agent_messages_key not in st.session_state:
                    st.session_state[agent_messages_key] = []
                
                # Display chat history
                for msg in st.session_state[agent_messages_key]:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
                
                # Chat input
                prompt = st.chat_input(
                    f"Message {agent_info['name']}...",
                    key=f"chat_{agent_key}"
                )
                
                if prompt:
                    st.session_state[agent_messages_key].append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    with st.chat_message("assistant"):
                        with st.spinner("Processing..."):
                            response = run_agent_interaction(agent_caller, prompt)
                            st.write(response)
                            st.session_state[agent_messages_key].append({"role": "assistant", "content": response})
                    
                    # Update state after interaction
                    update_state_from_agent(agent_caller)
                    st.rerun()
                
                # Quick action buttons for specific agents
                if agent_info["key"] == "pre_ingestion_audit":
                    if st.button("🔍 Scan Files for Issues", key=f"scan_{agent_key}"):
                        prompt = "Please scan all files for data quality issues and create audit queries"
                        st.session_state[agent_messages_key].append({"role": "user", "content": prompt})
                        with st.spinner("Scanning files..."):
                            response = run_agent_interaction(agent_caller, prompt)
                            st.session_state[agent_messages_key].append({"role": "assistant", "content": response})
                        st.rerun()
                
                elif agent_info["key"] == "graph_construction":
                    if st.button("🏗️ Execute Construction Plan", key=f"execute_{agent_key}"):
                        prompt = "Execute the construction plan to build the knowledge graph"
                        st.session_state[agent_messages_key].append({"role": "user", "content": prompt})
                        with st.spinner("Building knowledge graph..."):
                            response = run_agent_interaction(agent_caller, prompt)
                            st.session_state[agent_messages_key].append({"role": "assistant", "content": response})
                        st.rerun()
                
                elif agent_info["key"] == "knowledge_extraction":
                    if st.button("📚 Extract Knowledge from Markdown", key=f"extract_{agent_key}"):
                        prompt = "Extract entities and relationships from all approved markdown files"
                        st.session_state[agent_messages_key].append({"role": "user", "content": prompt})
                        with st.spinner("Extracting knowledge..."):
                            response = run_agent_interaction(agent_caller, prompt)
                            st.session_state[agent_messages_key].append({"role": "assistant", "content": response})
                        st.rerun()
                
                # Mark phase as completed button
                if st.button(f"✅ Mark Phase {phase_num} as Completed", key=f"complete_{phase_num}"):
                    st.session_state.workflow_state["phase_status"][phase_num] = "completed"
                    st.session_state.workflow_state["phase_history"].append({
                        "phase": phase_num,
                        "timestamp": datetime.now().isoformat(),
                        "status": "completed"
                    })
                    st.success(f"Phase {phase_num} marked as completed")
                    st.rerun()
        
        st.divider()


# Pre-Ingestion Audit Query Dashboard (if Phase 3 is active)
phase_3_keys = [key for key in st.session_state.workflow_state["agent_callers"].keys() if "phase_3" in key]
if phase_3_keys or PRE_INGESTION_AUDIT_QUERIES in st.session_state.workflow_state["current_state"]:
    st.divider()
    st.header("🔍 Pre-Ingestion Audit Queries")
    
    audit_queries = st.session_state.workflow_state["current_state"].get(PRE_INGESTION_AUDIT_QUERIES, {})
    
    if audit_queries:
        # Summary metrics
        pending = sum(1 for q in audit_queries.values() if q.get("status") == "pending_review")
        resolved = sum(1 for q in audit_queries.values() if q.get("status") in ["resolved", "approved", "rejected"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Issues", len(audit_queries))
        col2.metric("Pending Review", pending, delta=f"-{len(audit_queries) - pending}" if pending < len(audit_queries) else None)
        col3.metric("Resolved", resolved)
        
        if pending > 0:
            st.warning(f"⚠️ **{pending} queries pending review. Phase 4 is blocked until all are resolved.**")
        
        # Display queries with resolution options
        for query_id, query in audit_queries.items():
            status = query.get("status", "pending_review")
            severity = query.get("severity", "info")
            category = query.get("category", "unknown")
            
            with st.expander(f"{'🔴' if severity == 'error' else '🟡' if severity == 'warning' else '🔵'} {query_id} - {category.replace('_', ' ').title()} {'✅' if status != 'pending_review' else '⏳'}"):
                # Query details
                st.markdown(f"**Status:** {status} | **Severity:** {severity}")
                if "description" in query:
                    st.markdown(f"**Description:** {query['description']}")
                
                # Evidence
                if "evidence" in query:
                    with st.expander("📋 View Evidence"):
                        st.json(query["evidence"])
                
                # Resolution options for pending queries
                if status == "pending_review":
                    st.markdown("**🎯 Resolution Options:**")
                    proposed_actions = query.get("proposed_actions", [
                        "skip_record", "use_first", "use_second", "merge", 
                        "manual_fix", "approve", "reject"
                    ])
                    
                    # Find the pre-ingestion audit agent caller
                    pre_ingestion_key = None
                    for key in st.session_state.workflow_state["agent_callers"].keys():
                        if "pre_ingestion_audit" in key:
                            pre_ingestion_key = key
                            break
                    
                    if pre_ingestion_key:
                        agent_caller = st.session_state.workflow_state["agent_callers"][pre_ingestion_key]
                        
                        # Action buttons
                        action_labels = {
                            "skip_record": "⏭️ Skip Record",
                            "use_first": "1️⃣ Use First",
                            "use_second": "2️⃣ Use Second",
                            "merge": "🔀 Merge",
                            "manual_fix": "🔧 Manual Fix",
                            "approve": "✅ Approve",
                            "reject": "❌ Reject"
                        }
                        
                        cols = st.columns(min(len(proposed_actions), 4))
                        for idx, action in enumerate(proposed_actions):
                            if action in action_labels:
                                with cols[idx % len(cols)]:
                                    if st.button(
                                        action_labels[action],
                                        key=f"resolve_{query_id}_{action}",
                                        use_container_width=True
                                    ):
                                        resolution_prompt = f"Resolve audit query {query_id} with action: {action}"
                                        with st.spinner(f"Resolving {query_id}..."):
                                            response = run_agent_interaction(agent_caller, resolution_prompt)
                                            st.success(f"✅ Resolved: {action}")
                                            st.rerun()
                    else:
                        st.info("Initialize Pre-Ingestion Audit Agent to resolve queries")
                else:
                    # Show resolution if already resolved
                    resolution = query.get("user_decision")
                    if resolution:
                        st.success(f"✅ **Resolved:** {resolution}")
                        if "decision_notes" in query:
                            st.caption(f"Notes: {query['decision_notes']}")
    else:
        st.info("No audit queries generated yet. Run the Pre-Ingestion Audit Agent to scan files.")


# Full State Viewer
with st.expander("🔍 Full Workflow State (Debug)", expanded=False):
    st.json(st.session_state.workflow_state)


# Footer
st.divider()
st.markdown("""
### 💡 Usage Tips

1. **Sequential Execution**: Run phases in order. Each phase depends on outputs from previous phases.
2. **Initialize Agents**: Click "Initialize" buttons to set up agents for each phase.
3. **Chat Interface**: Use the chat interface to interact with each agent naturally.
4. **Quick Actions**: Use quick action buttons for common tasks (scan files, execute plan, etc.).
5. **Blocking Phases**: Phase 3 (Pre-Ingestion) blocks Phase 4 until all audit queries are resolved.
6. **State Persistence**: State is automatically persisted between phases and agent interactions.

### 🎯 Example Workflow

1. **Phase 1**: Start with User Intent Agent → "I want to build a knowledge graph for art collection provenance"
2. **Phase 1**: Continue with File Suggestion → Approve suggested CSV files
3. **Phase 1**: Schema Proposal → Review and approve construction plan
4. **Phase 1**: File Suggestion (Unstructured) → Approve markdown files
5. **Phase 1**: NER Agent → Approve entity types
6. **Phase 1**: Fact Extraction → Approve fact types
7. **Phase 2**: Data Quality Rules → Define validation rules
8. **Phase 3**: Pre-Ingestion Audit → Scan files and resolve all queries
9. **Phase 4**: Graph Construction → Build the knowledge graph
""")

