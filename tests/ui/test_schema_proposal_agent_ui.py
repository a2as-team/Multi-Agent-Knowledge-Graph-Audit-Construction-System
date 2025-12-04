"""
Streamlit UI for testing the Schema Proposal Agent (Structured).

This UI allows interactive testing of the Schema Proposal Agent with:
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

from src.agents.schema_proposal_structured_agent import schema_refinement_loop
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_FILES,
    PROPOSED_CONSTRUCTION_PLAN,
    APPROVED_CONSTRUCTION_PLAN
)


# Page configuration
st.set_page_config(
    page_title="Schema Proposal Agent Test",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Schema Proposal Agent Test UI")
st.markdown("Test the Schema Proposal Agent for structured data (CSV files)")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(approved_user_goal: Dict[str, Any], approved_files: list):
    """Initialize the agent caller with approved user goal and files."""
    async def _init():
        caller = await make_agent_caller(
            schema_refinement_loop,
            initial_state={
                "approved_user_goal": approved_user_goal,
                "approved_files": approved_files,
                "feedback": ""  # Initialize feedback for refinement loop
            }
        )
        return caller
    
    return asyncio.run(_init())


def reset_session():
    """Reset the session state."""
    # Clear agent caller and its session
    if st.session_state.agent_caller is not None:
        try:
            async def clear_agent_session():
                session = await st.session_state.agent_caller.get_session()
                session.state.clear()
            asyncio.run(clear_agent_session())
        except Exception as e:
            # Silently fail if session clearing doesn't work
            pass
    
    st.session_state.agent_caller = None
    st.session_state.messages = []
    st.session_state.verbose_logging = False


# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Approved User Goal Input (required)
    st.subheader("Approved User Goal")
    st.markdown("The Schema Proposal Agent requires an approved user goal from the User Intent Agent.")
    
    kind_of_graph = st.text_input(
        "Kind of Graph",
        value="art collection provenance",
        help="2-3 words describing the type of graph"
    )
    
    graph_description = st.text_area(
        "Graph Description",
        value="A knowledge graph for art collection provenance which includes all levels from artworks to artists, locations, and mediums, which can support root-cause analysis and content auditing.",
        help="Detailed description of the graph's purpose"
    )
    
    approved_user_goal = {
        "kind_of_graph": kind_of_graph,
        "graph_description": graph_description  # Fixed: matches User Intent Agent structure
    }
    
    st.divider()
    
    # Approved Files Input (required)
    st.subheader("Approved Files")
    st.markdown("The Schema Proposal Agent requires approved files from the File Suggestion Agent.")
    
    approved_files_input = st.text_area(
        "Approved Files (one per line)",
        value="artists.csv\nartworks.csv\nartwork_artist.csv\nartwork_location.csv\nlocations.csv\nmedium.csv",
        help="List of approved CSV files, one per line"
    )
    
    approved_files = [f.strip() for f in approved_files_input.split("\n") if f.strip()]
    
    # Validate structure before allowing initialization
    if not kind_of_graph.strip() or not graph_description.strip():
        st.warning("⚠️ Both user goal fields are required to initialize the agent.")
    
    if not approved_files:
        st.warning("⚠️ At least one approved file is required.")
    
    # Initialize Agent button
    if st.button("Initialize Agent", type="primary", disabled=not (kind_of_graph.strip() and graph_description.strip() and approved_files)):
        with st.spinner("Initializing agent..."):
            try:
                st.session_state.agent_caller = initialize_agent(approved_user_goal, approved_files)
                st.success("Agent initialized successfully!")
                st.session_state.messages = []
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
    
    st.divider()
    
    # Example prompts section
    with st.expander("💡 Example Prompts"):
        st.markdown("""
        **Try these prompts:**
        - `How can these files be imported to construct the knowledge graph?`
        - `Propose a schema for these files`
        - `What schema would you suggest?`
        - `Yes, approve the schema` (after schema is proposed)
        """)
    
    st.divider()
    
    # Verbose logging toggle
    st.session_state.verbose_logging = st.checkbox(
        "Verbose Logging",
        value=st.session_state.verbose_logging,
        help="Show detailed event information in terminal"
    )
    
    # Reset session button
    if st.button("Reset Session", type="secondary"):
        reset_session()
        st.rerun()


# Main chat interface
if st.session_state.agent_caller is None:
    st.info("👈 Please configure and initialize the agent in the sidebar first.")
    st.json({
        "approved_user_goal": approved_user_goal,
        "approved_files": approved_files
    })
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask the agent to propose a schema..."):
        # Add user message
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
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


# Session State Viewer
st.divider()
st.header("Session State")

if st.session_state.agent_caller is not None:
    try:
        async def get_session():
            return await st.session_state.agent_caller.get_session()
        
        session = asyncio.run(get_session())
        
        # Display relevant state keys
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Approved User Goal")
            if APPROVED_USER_GOAL in session.state:
                st.json(session.state[APPROVED_USER_GOAL])
            else:
                st.warning("Not set")
            
            st.subheader("Approved Files")
            if APPROVED_FILES in session.state:
                st.json(session.state[APPROVED_FILES])
            else:
                st.warning("Not set")
            
            st.subheader("Feedback")
            if "feedback" in session.state:
                feedback = session.state["feedback"]
                if feedback and feedback != "valid":
                    st.warning(feedback)
                elif feedback == "valid":
                    st.success("Schema is valid ✓")
                else:
                    st.info("No feedback yet")
            else:
                st.info("No feedback yet")
        
        with col2:
            st.subheader("Proposed Construction Plan")
            if PROPOSED_CONSTRUCTION_PLAN in session.state:
                st.json(session.state[PROPOSED_CONSTRUCTION_PLAN])
            else:
                st.info("Not proposed yet")
            
            st.subheader("Approved Construction Plan")
            if APPROVED_CONSTRUCTION_PLAN in session.state:
                st.json(session.state[APPROVED_CONSTRUCTION_PLAN])
            else:
                st.info("Not approved yet")
        
        # Full state (expandable)
        with st.expander("View Full Session State"):
            st.json(dict(session.state))
    
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")
else:
    st.info("Initialize the agent to view session state.")

