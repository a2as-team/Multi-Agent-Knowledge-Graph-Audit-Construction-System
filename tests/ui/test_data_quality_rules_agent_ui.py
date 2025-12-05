"""
Streamlit UI for testing the Data Quality Rules Agent.

This UI allows interactive testing of the Data Quality Rules Agent with:
- Chat interface for user interaction
- Session state viewer
- Verbose logging toggle
- Reset session functionality
"""
import streamlit as st
import asyncio
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to sys.path for module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.data_quality_rules_agent import data_quality_rules_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_CONSTRUCTION_PLAN,
    APPROVED_ENTITIES,
    APPROVED_FACTS,
    PROPOSED_QUALITY_RULES,
    APPROVED_QUALITY_RULES
)


# Page configuration
st.set_page_config(
    page_title="Data Quality Rules Agent Test",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Data Quality Rules Agent Test UI")
st.markdown("Test the Data Quality Rules Agent for defining custom quality rules")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(
    approved_user_goal: Dict[str, Any],
    approved_construction_plan: Dict[str, Any],
    approved_entities: list,
    approved_facts: dict
):
    """Initialize the agent caller with approved context."""
    try:
        # Initial state with all approved context
        initial_state = {
            APPROVED_USER_GOAL: approved_user_goal,
            APPROVED_CONSTRUCTION_PLAN: approved_construction_plan,
            APPROVED_ENTITIES: approved_entities,
            APPROVED_FACTS: approved_facts
        }
        
        # Create agent caller with initial state
        agent_caller = asyncio.run(make_agent_caller(
            data_quality_rules_agent,
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

# Construction Plan (Domain Graph Schema)
st.sidebar.subheader("Approved Construction Plan")
with st.sidebar.expander("View/Edit Construction Plan"):
    construction_plan_text = st.text_area(
        "JSON",
        value="""{
    "Artwork_node": {
        "construction_type": "node",
        "label": "Artwork",
        "unique_column_name": "artwork_id",
        "properties": ["title", "year"]
    },
    "Artist_node": {
        "construction_type": "node",
        "label": "Artist",
        "unique_column_name": "artist_id",
        "properties": ["name", "birth_year"]
    },
    "Location_node": {
        "construction_type": "node",
        "label": "Location",
        "unique_column_name": "location_id",
        "properties": ["name", "country"]
    },
    "CREATED_BY_rel": {
        "construction_type": "relationship",
        "relationship_type": "CREATED_BY",
        "from_node_label": "Artwork",
        "to_node_label": "Artist"
    },
    "LOCATED_AT_rel": {
        "construction_type": "relationship",
        "relationship_type": "LOCATED_AT",
        "from_node_label": "Artwork",
        "to_node_label": "Location"
    }
}""",
        height=300
    )

# Entity Types
st.sidebar.subheader("Approved Entity Types")
entity_types_text = st.sidebar.text_area(
    "Entity Types (comma-separated)",
    value="Artist, Artwork, Location, Exhibition, Collection, ArtMovement, Collector",
    height=60
)

# Fact Types
st.sidebar.subheader("Approved Fact Types")
with st.sidebar.expander("View/Edit Fact Types"):
    fact_types_text = st.text_area(
        "JSON",
        value="""{
    "born_in": {
        "subject_label": "Artist",
        "predicate_label": "born_in",
        "object_label": "Location"
    },
    "exhibited_in": {
        "subject_label": "Artwork",
        "predicate_label": "exhibited_in",
        "object_label": "Exhibition"
    },
    "owned_by": {
        "subject_label": "Artwork",
        "predicate_label": "owned_by",
        "object_label": "Collector"
    }
}""",
        height=200
    )

# Initialize button
if st.sidebar.button("Initialize Agent", type="primary"):
    import json
    
    try:
        # Parse inputs
        approved_user_goal = {"graph_description": user_goal}
        approved_construction_plan = json.loads(construction_plan_text)
        approved_entities = [e.strip() for e in entity_types_text.split(",")]
        approved_facts = json.loads(fact_types_text)
        
        # Initialize agent
        initialize_agent(
            approved_user_goal,
            approved_construction_plan,
            approved_entities,
            approved_facts
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
                    
                    # Check if approval happened and refresh session state viewer
                    async def check_approval():
                        session = await st.session_state.agent_caller.get_session()
                        return APPROVED_QUALITY_RULES in session.state
                    
                    # Check if this was an approval request or if approval was successful
                    is_approval_request = "approve" in prompt.lower()
                    approval_successful = asyncio.run(check_approval())
                    
                    # Force rerun to refresh session state viewer after state changes
                    if is_approval_request or approval_successful:
                        st.rerun()
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
    st.info("👈 Please initialize the agent in the sidebar to start chatting")


# Session State Viewer
st.divider()
st.header("Session State")

if st.session_state.agent_caller is not None:
    async def get_session_state():
        session = await st.session_state.agent_caller.get_session()
        return session.state if session else {}
    
    try:
        session_state = asyncio.run(get_session_state())
        
        # Create tabs for different state views
        tab1, tab2, tab3 = st.tabs(["📋 Proposed Rules", "✅ Approved Rules", "🔍 Full State"])
        
        with tab1:
            st.subheader("Proposed Quality Rules")
            proposed_rules = session_state.get(PROPOSED_QUALITY_RULES, {})
            if proposed_rules:
                # Organize by severity
                error_rules = {k: v for k, v in proposed_rules.items() if v.get("severity") == "error"}
                warning_rules = {k: v for k, v in proposed_rules.items() if v.get("severity") == "warning"}
                info_rules = {k: v for k, v in proposed_rules.items() if v.get("severity") == "info"}
                
                st.metric("Total Rules", len(proposed_rules))
                col1, col2, col3 = st.columns(3)
                col1.metric("Errors", len(error_rules))
                col2.metric("Warnings", len(warning_rules))
                col3.metric("Info", len(info_rules))
                
                if error_rules:
                    st.markdown("#### 🔴 Error Rules")
                    st.json(error_rules)
                if warning_rules:
                    st.markdown("#### 🟡 Warning Rules")
                    st.json(warning_rules)
                if info_rules:
                    st.markdown("#### 🔵 Info Rules")
                    st.json(info_rules)
            else:
                st.info("No proposed rules yet")
        
        with tab2:
            st.subheader("Approved Quality Rules")
            approved_rules = session_state.get(APPROVED_QUALITY_RULES, {})
            if approved_rules:
                st.metric("Total Approved", len(approved_rules))
                st.json(approved_rules)
            else:
                st.info("No approved rules yet")
        
        with tab3:
            st.subheader("Complete Session State")
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
    1. Initialize the agent with your schema context
    2. Ask the agent to propose quality rules
    3. Review and refine the rules
    4. Approve when satisfied
    
    **Example Prompts:**
    - "Please propose quality rules for this knowledge graph"
    - "Add a rule that every artwork must have a creator"
    - "Remove the rule about artwork year"
    - "Show me all proposed rules"
    - "I approve these rules"
    
    **Rule Types Available:**
    - Required relationships
    - Temporal constraints
    - Cardinality constraints
    - Orphan detection
    - Unresolved entities
    - Value constraints
    - Custom Cypher queries
    """)

