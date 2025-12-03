"""
Streamlit UI for testing the File Suggestion Agent.

This UI allows interactive testing of the File Suggestion Agent with:
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

from src.agents.file_suggestion_agent import file_suggestion_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    ALL_AVAILABLE_FILES,
    SUGGESTED_FILES,
    APPROVED_FILES
)


# Page configuration
st.set_page_config(
    page_title="File Suggestion Agent Test",
    page_icon="📁",
    layout="wide"
)

st.title("📁 File Suggestion Agent Test UI")
st.markdown("Test the File Suggestion Agent for structured data (CSV/JSON files)")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(approved_user_goal: Dict[str, Any]):
    """Initialize the agent caller with approved user goal."""
    async def _init():
        caller = await make_agent_caller(
            file_suggestion_agent,
            initial_state={"approved_user_goal": approved_user_goal}
        )
        return caller
    
    return asyncio.run(_init())


def reset_session():
    """Reset the session state."""
    st.session_state.agent_caller = None
    st.session_state.messages = []
    st.session_state.verbose_logging = False


# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Approved User Goal Input (required for File Suggestion Agent)
    st.subheader("Approved User Goal")
    st.markdown("The File Suggestion Agent requires an approved user goal from the User Intent Agent.")
    
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
        "description": graph_description
    }
    
    # Initialize Agent button
    if st.button("Initialize Agent", type="primary"):
        with st.spinner("Initializing agent..."):
            try:
                st.session_state.agent_caller = initialize_agent(approved_user_goal)
                st.success("Agent initialized successfully!")
                st.session_state.messages = []
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
    
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
    st.json(approved_user_goal)
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask the agent to suggest files..."):
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
            
            st.subheader("All Available Files")
            if ALL_AVAILABLE_FILES in session.state:
                st.json(session.state[ALL_AVAILABLE_FILES])
            else:
                st.info("Not listed yet")
        
        with col2:
            st.subheader("Suggested Files")
            if SUGGESTED_FILES in session.state:
                st.json(session.state[SUGGESTED_FILES])
            else:
                st.info("Not suggested yet")
            
            st.subheader("Approved Files")
            if APPROVED_FILES in session.state:
                st.json(session.state[APPROVED_FILES])
            else:
                st.info("Not approved yet")
        
        # Full state (expandable)
        with st.expander("View Full Session State"):
            st.json(dict(session.state))
    
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")
else:
    st.info("Initialize the agent to view session state.")

