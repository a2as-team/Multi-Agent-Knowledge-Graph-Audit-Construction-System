"""
Streamlit UI for testing the Pre-Ingestion Audit Agent.

This UI allows interactive testing of the Pre-Ingestion Audit Agent with:
- Chat interface for user interaction
- Session state viewer
- Audit query dashboard
- Verbose logging toggle
- Reset session functionality
"""
import streamlit as st
import asyncio
import json
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to sys.path for module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.pre_ingestion_audit_agent import pre_ingestion_audit_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_CONSTRUCTION_PLAN,
    PRE_INGESTION_AUDIT_QUERIES,
    AUDIT_RESOLUTIONS
)


# Page configuration
st.set_page_config(
    page_title="Pre-Ingestion Audit Agent Test",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Pre-Ingestion Audit Agent Test UI")
st.markdown("Test the Pre-Ingestion Audit Agent for detecting data quality issues before ingestion")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(
    approved_user_goal: Dict[str, Any],
    approved_construction_plan: Dict[str, Any]
):
    """Initialize the agent caller with approved context."""
    try:
        # Initial state with all approved context
        # Note: Files to scan are derived from construction_plan, not a separate list
        initial_state = {
            APPROVED_USER_GOAL: approved_user_goal,
            APPROVED_CONSTRUCTION_PLAN: approved_construction_plan
        }
        
        # Create agent caller with initial state
        agent_caller = asyncio.run(make_agent_caller(
            pre_ingestion_audit_agent,
            initial_state
        ))
        
        st.session_state.agent_caller = agent_caller
        st.success("✅ Agent initialized successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return False


# Sidebar for initialization
st.sidebar.header("1. Initialize Agent")

# User Goal Input
st.sidebar.subheader("User Goal")
user_goal = st.sidebar.text_area(
    "Graph Description",
    value="A knowledge graph for art collection provenance which includes all levels from artworks to artists, locations, and mediums.\n\nSupports root-cause analysis and content auditing.",
    height=100
)

# Construction Plan
st.sidebar.subheader("Approved Construction Plan")
st.sidebar.info("📌 Files to scan are derived from the 'source_file' fields in the construction plan below")
with st.sidebar.expander("View/Edit Construction Plan"):
    construction_plan_text = st.text_area(
        "JSON",
        value="""{
    "Artwork_node": {
        "construction_type": "node",
        "source_file": "artworks.csv",
        "label": "Artwork",
        "unique_column_name": "artwork_id",
        "properties": ["artwork_id", "title", "year", "artist_id", "location_id"]
    },
    "Artist_node": {
        "construction_type": "node",
        "source_file": "artists.csv",
        "label": "Artist",
        "unique_column_name": "artist_id",
        "properties": ["artist_id", "name", "birth_year"]
    },
    "Location_node": {
        "construction_type": "node",
        "source_file": "locations.csv",
        "label": "Location",
        "unique_column_name": "location_id",
        "properties": ["location_id", "name", "country"]
    },
    "CREATED_BY_rel": {
        "construction_type": "relationship",
        "relationship_type": "CREATED_BY",
        "from_node_label": "Artwork",
        "to_node_label": "Artist",
        "from_node_column": "artist_id",
        "to_node_column": "artist_id"
    },
    "LOCATED_AT_rel": {
        "construction_type": "relationship",
        "relationship_type": "LOCATED_AT",
        "from_node_label": "Artwork",
        "to_node_label": "Location",
        "from_node_column": "location_id",
        "to_node_column": "location_id"
    }
}""",
        height=400
    )

# Initialize button
if st.sidebar.button("Initialize Agent", type="primary"):
    try:
        # Parse inputs
        approved_user_goal = {"graph_description": user_goal}
        approved_construction_plan = json.loads(construction_plan_text)
        
        # Initialize agent (files are derived from construction plan)
        initialize_agent(
            approved_user_goal,
            approved_construction_plan
        )
        
        # Clear messages
        st.session_state.messages = []
        
    except json.JSONDecodeError as e:
        st.sidebar.error(f"❌ JSON parsing error: {e}")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

# Reset session
if st.sidebar.button("Reset Session"):
    st.session_state.agent_caller = None
    st.session_state.messages = []
    st.rerun()

# Verbose logging toggle
st.sidebar.divider()
st.sidebar.subheader("Settings")
st.session_state.verbose_logging = st.sidebar.checkbox(
    "Verbose Logging",
    value=st.session_state.verbose_logging
)


# Main chat interface
st.header("2. Chat with Agent")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if st.session_state.agent_caller is not None:
    if prompt := st.chat_input("Enter your message"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking..."):
                try:
                    async def get_response():
                        response = await st.session_state.agent_caller.call(
                            prompt,
                            verbose=st.session_state.verbose_logging
                        )
                        return response
                    
                    response = asyncio.run(get_response())
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Force rerun to refresh session state viewer after audit queries created
                    st.rerun()
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
    st.info("👈 Please initialize the agent in the sidebar to start chatting")


# Helper function to handle action button clicks
async def resolve_issue_with_action(query_id: str, action: str):
    """Send resolution command to agent."""
    try:
        resolution_message = f"Resolve issue {query_id} with action: {action}"
        response = await st.session_state.agent_caller.call(
            resolution_message,
            verbose=st.session_state.verbose_logging
        )
        st.session_state.messages.append({"role": "user", "content": resolution_message})
        st.session_state.messages.append({"role": "assistant", "content": response})
        return response
    except Exception as e:
        st.error(f"Error resolving issue: {e}")
        return None


def render_audit_query_card(query_id: str, query: Dict[str, Any]):
    """Render an audit query with clickable action buttons."""
    status = query.get("status", "pending_review")
    category = query.get("category", "unknown")
    severity = query.get("severity", "info")
    
    # Status badge
    status_emoji = "⏳" if status == "pending_review" else "✅"
    severity_color = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
    
    with st.container():
        st.markdown(f"#### {severity_color} {query_id}")
        st.markdown(f"**Category:** {category.replace('_', ' ').title()} | **Status:** {status_emoji} {status}")
        
        # Description
        if "description" in query:
            st.markdown(f"**Description:** {query['description']}")
        
        # Evidence
        if "evidence" in query:
            with st.expander("📋 View Evidence"):
                evidence = query["evidence"]
                if isinstance(evidence, dict):
                    for key, value in evidence.items():
                        st.markdown(f"**{key}:** {value}")
                elif isinstance(evidence, str):
                    st.markdown(evidence)
                else:
                    st.json(evidence)
        
        # Action buttons (only for pending queries)
        if status == "pending_review":
            proposed_actions = query.get("proposed_actions", [])
            if proposed_actions:
                st.markdown("**🎯 Choose Action:**")
                
                # Create button columns based on number of actions
                num_actions = len(proposed_actions)
                cols = st.columns(num_actions)
                
                # Action button labels
                action_labels = {
                    "skip_record": "⏭️ Skip Record",
                    "use_first": "1️⃣ Use First",
                    "use_second": "2️⃣ Use Second",
                    "merge_data": "🔀 Merge Data",
                    "manual_fix": "🔧 Manual Fix",
                    "update_construction_plan": "📝 Update Plan",
                    "approve": "✅ Approve",
                    "reject": "❌ Reject"
                }
                
                for idx, action in enumerate(proposed_actions):
                    with cols[idx]:
                        button_label = action_labels.get(action, action.replace("_", " ").title())
                        if st.button(button_label, key=f"{query_id}_{action}", use_container_width=True):
                            # Store the resolution request
                            st.session_state[f"pending_resolution_{query_id}"] = action
                            st.rerun()
        else:
            # Show resolution if already resolved
            resolution = query.get("resolution", {})
            if resolution:
                st.success(f"✅ **Resolved:** {resolution.get('action', 'Unknown action')}")
                if "notes" in resolution:
                    st.markdown(f"*Notes:* {resolution['notes']}")
        
        st.divider()


# Audit Query Dashboard
st.divider()
st.header("3. Audit Query Dashboard")

if st.session_state.agent_caller is not None:
    async def get_session_state():
        session = await st.session_state.agent_caller.get_session()
        return session.state if session else {}
    
    # Check for pending resolutions and process them
    pending_resolutions = [key for key in st.session_state.keys() if key.startswith("pending_resolution_")]
    if pending_resolutions:
        for key in pending_resolutions:
            query_id = key.replace("pending_resolution_", "")
            action = st.session_state[key]
            
            with st.spinner(f"Resolving {query_id} with action: {action}..."):
                response = asyncio.run(resolve_issue_with_action(query_id, action))
                if response:
                    st.success(f"✅ Resolved {query_id}")
            
            # Clean up
            del st.session_state[key]
        
        # Rerun to refresh the display
        st.rerun()
    
    try:
        session_state = asyncio.run(get_session_state())
        
        audit_queries = session_state.get(PRE_INGESTION_AUDIT_QUERIES, {})
        resolutions = session_state.get(AUDIT_RESOLUTIONS, {})
        
        if audit_queries:
            # Summary metrics
            st.subheader("📊 Audit Summary")
            
            pending = sum(1 for q in audit_queries.values() if q.get("status") == "pending_review")
            resolved = sum(1 for q in audit_queries.values() if q.get("status") in ["resolved", "approved", "rejected"])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Issues", len(audit_queries))
            col2.metric("Pending Review", pending)
            col3.metric("Resolved", resolved)
            
            # Organize by severity
            errors = {k: v for k, v in audit_queries.items() if v.get("severity") == "error"}
            warnings = {k: v for k, v in audit_queries.items() if v.get("severity") == "warning"}
            infos = {k: v for k, v in audit_queries.items() if v.get("severity") == "info"}
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔴 Errors", len(errors))
            col2.metric("🟡 Warnings", len(warnings))
            col3.metric("🔵 Info", len(infos))
            
            # Display queries by severity with action buttons
            st.divider()
            
            if errors:
                st.markdown("### 🔴 Error-Level Issues")
                for query_id, query in errors.items():
                    render_audit_query_card(query_id, query)
            
            if warnings:
                st.markdown("### 🟡 Warning-Level Issues")
                for query_id, query in warnings.items():
                    render_audit_query_card(query_id, query)
            
            if infos:
                st.markdown("### 🔵 Info-Level Issues")
                for query_id, query in infos.items():
                    render_audit_query_card(query_id, query)
        else:
            st.info("No audit queries generated yet. Ask the agent to scan the files.")
        
        # Resolutions summary
        if resolutions:
            st.divider()
            st.subheader("✅ Resolutions Summary")
            for query_id, resolution in resolutions.items():
                st.markdown(f"**{query_id}:** {resolution.get('action', 'Unknown')} - {resolution.get('status', 'Unknown')}")
            
    except Exception as e:
        st.error(f"Error displaying audit queries: {e}")
else:
    st.info("Initialize agent to view audit queries")


# Session State Viewer
st.divider()
st.header("4. Full Session State")

if st.session_state.agent_caller is not None:
    try:
        session_state = asyncio.run(get_session_state())
        st.json(session_state)
    except Exception as e:
        st.error(f"Error displaying session state: {e}")
else:
    st.info("Initialize agent to view session state")


# Footer with helpful tips
st.divider()
with st.expander("💡 Tips for Using This Agent"):
    st.markdown("""
    **Getting Started:**
    1. Initialize the agent with your construction plan
    2. Ask the agent to scan the files for issues
    3. Review audit queries in the dashboard below
    4. Click action buttons to resolve each issue (or chat with the agent)
    
    **Example Prompts:**
    - "Please scan all files for data quality issues"
    - "Scan artworks.csv for duplicate IDs"
    - "Check for missing required fields in artists.csv"
    - "Show me all audit queries"
    
    **Two Ways to Resolve Issues:**
    
    1. **Click Action Buttons (Recommended):** 
       - Each pending issue shows clickable action buttons
       - Simply click your preferred action to resolve
       - The agent processes your decision automatically
    
    2. **Chat with Agent:**
       - "For query pre_ing_001, use the first record"
       - "Resolve pre_ing_002 by skipping the record"
    
    **Resolution Options Explained:**
    - ⏭️ **Skip Record**: Don't import this record
    - 1️⃣ **Use First**: Use first occurrence (for duplicates)
    - 2️⃣ **Use Second**: Use second occurrence (for duplicates)
    - 🔀 **Merge Data**: Combine both records (for duplicates)
    - 🔧 **Manual Fix**: User will fix source file
    - 📝 **Update Plan**: Adjust construction plan instead of file
    - ✅ **Approve**: Accept the finding and proceed
    - ❌ **Reject**: Reject the finding (false positive)
    
    **Dashboard Features:**
    - View all audit queries organized by severity
    - See pending vs resolved counts
    - Clickable action buttons for quick resolution
    - Evidence details in expandable sections
    """)

