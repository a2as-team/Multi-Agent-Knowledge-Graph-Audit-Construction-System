"""
Streamlit UI for testing the User Intent Agent.

Run with: streamlit run tests/ui/test_user_intent_agent_ui.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import asyncio
from typing import Dict, Any

from src.agents.user_intent_agent import user_intent_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import PERCEIVED_USER_GOAL, APPROVED_USER_GOAL


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
    page_title="User Intent Agent Tester",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 User Intent Agent Tester")
st.markdown("Test the User Intent Agent for knowledge graph use case ideation.")

# Initialize session state
if 'caller' not in st.session_state:
    with st.spinner("Initializing agent..."):
        st.session_state.caller = run_async(make_agent_caller(user_intent_agent))
        st.session_state.messages = []
        st.session_state.verbose = False

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    if st.button("🔄 Reset Session"):
        st.session_state.caller = run_async(make_agent_caller(user_intent_agent))
        st.session_state.messages = []
        st.rerun()
    
    st.session_state.verbose = st.checkbox("Verbose Logging", value=st.session_state.verbose)
    
    st.markdown("---")
    st.markdown("### Agent Info")
    st.text(f"Name: {user_intent_agent.name}")
    st.text(f"Model: {user_intent_agent.model.model}")

# Main chat interface
st.header("💬 Conversation")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "tool_calls" in msg and msg["tool_calls"]:
            with st.expander("🔧 Tool Calls"):
                st.json(msg["tool_calls"])

# Chat input
if prompt := st.chat_input("Enter your message..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = run_async(
                    st.session_state.caller.call(prompt, verbose=st.session_state.verbose)
                )
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Session State Debug Panel
with st.expander("🔍 Session State (Debug)", expanded=False):
    try:
        session = run_async(st.session_state.caller.get_session())
        st.json(session.state)
        
        # Highlight important state keys
        if PERCEIVED_USER_GOAL in session.state:
            st.success(f"✅ {PERCEIVED_USER_GOAL} is set")
            st.json(session.state[PERCEIVED_USER_GOAL])
        
        if APPROVED_USER_GOAL in session.state:
            st.success(f"✅ {APPROVED_USER_GOAL} is set")
            st.json(session.state[APPROVED_USER_GOAL])
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    **Testing the User Intent Agent:**
    
    1. Enter a knowledge graph use case idea in the chat
    2. The agent will ask clarifying questions if needed
    3. The agent will set a perceived goal and ask for approval
    4. Approve the goal when you're satisfied
    5. Check the Session State panel to see the approved goal
    
    **Example inputs:**
    - "I'd like an art collection provenance graph"
    - "I want to build a social network graph"
    - "Create a logistics network for my supply chain"
    
    **Tips:**
    - Use the Reset Session button to start fresh
    - Enable Verbose Logging to see detailed event information
    - Check Session State to see what the agent has stored
    """)

