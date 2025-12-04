"""
Streamlit UI for testing the Fact Extraction Agent (with Critic Pattern).

This UI allows interactive testing of the Fact Extraction Agent with:
- Chat interface for user interaction
- Critic pattern with automatic refinement (up to 3 iterations)
- Session state viewer
- Verbose logging toggle
- Reset session functionality

The agent uses a critic pattern:
1. Proposal Agent proposes fact types
2. Critic Agent validates and provides feedback
3. Refinement loop iterates until valid (max 3 iterations)
"""
import streamlit as st
import asyncio
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to sys.path for module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.fact_extraction_agent import fact_extraction_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_FILES,
    APPROVED_ENTITIES,
    APPROVED_CONSTRUCTION_PLAN,
    PROPOSED_FACTS,
    APPROVED_FACTS
)


# Page configuration
st.set_page_config(
    page_title="Fact Extraction Agent Test",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 Fact Extraction Agent Test UI")
st.markdown("Test the Fact Extraction Agent for proposing fact types (relationship triples) from unstructured data")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(initial_state: Dict[str, Any]):
    """Initialize the agent caller with required state."""
    async def _init():
        caller = await make_agent_caller(
            fact_extraction_agent,
            initial_state=initial_state
        )
        # Verify the caller is properly initialized
        if asyncio.iscoroutine(caller):
            caller = await caller
        return caller
    
    try:
        result = asyncio.run(_init())
        # Final check that result is not a coroutine
        if asyncio.iscoroutine(result):
            raise ValueError("Agent caller initialization returned a coroutine instead of an object")
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to initialize agent: {e}") from e


def reset_session():
    """Reset the session state."""
    if st.session_state.agent_caller is not None:
        try:
            async def clear_agent_session():
                session = await st.session_state.agent_caller.get_session()
                # Ensure session is not a coroutine
                if asyncio.iscoroutine(session):
                    session = await session
                if hasattr(session, 'state'):
                    session.state.clear()
            asyncio.run(clear_agent_session())
        except Exception as e:
            # Silently fail - session will be cleared anyway
            pass
    
    st.session_state.agent_caller = None
    st.session_state.messages = []
    st.session_state.verbose_logging = False


# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    st.markdown("""
    **Prerequisites**: The Fact Extraction Agent requires:
    1. Approved user goal (extended for unstructured data)
    2. Approved markdown files
    3. **Approved entity types** (from NER Agent)
    4. **Approved construction plan** (from structured data phase - to avoid redundancy)
    """)
    
    # Approved User Goal
    st.subheader("1. Approved User Goal")
    kind_of_graph = st.text_input(
        "Kind of Graph",
        value="art collection provenance",
        help="2-3 words describing the type of graph"
    )
    
    graph_description = st.text_area(
        "Graph Description (Extended)",
        value="""A knowledge graph for art collection provenance which includes all levels from artworks to artists, locations, and mediums.

Add artist biographies, exhibition histories, and provenance notes to provide deeper context and historical information about artworks and artists.""",
        help="Extended description including unstructured extraction goals",
        height=100
    )
    
    approved_user_goal = {
        "kind_of_graph": kind_of_graph,
        "graph_description": graph_description
    }
    
    st.divider()
    
    # Approved Files
    st.subheader("2. Approved Files")
    approved_files_input = st.text_area(
        "Approved Markdown Files (one per line)",
        value="artist_bios.md\nexhibition_histories.md\nprovenance_notes.md",
        help="List of approved markdown files",
        height=70
    )
    
    approved_files = [f.strip() for f in approved_files_input.split("\n") if f.strip()]
    
    st.divider()
    
    # Approved Entity Types (from NER Agent)
    st.subheader("3. Approved Entity Types")
    st.markdown("Output from NER Agent")
    
    approved_entities_input = st.text_area(
        "Approved Entity Types (one per line)",
        value="""Artist
Artwork
Location
Exhibition
Collection
ArtMovement
Collector
Institution""",
        help="Entity types approved by NER Agent",
        height=120
    )
    
    approved_entities = [e.strip() for e in approved_entities_input.split("\n") if e.strip()]
    
    st.divider()
    
    # Approved Construction Plan (from structured data)
    st.subheader("4. Approved Construction Plan")
    st.markdown("Relationships from structured data phase (to avoid redundancy)")
    
    st.markdown("**Example format**: `relationship_type | from_label | to_label`")
    construction_plan_input = st.text_area(
        "Existing Relationships (one per line)",
        value="""CREATED_BY | Artwork | Artist
LOCATED_AT | Artwork | Location
HAS_MEDIUM | Artwork | Medium""",
        help="Relationships from structured CSV data (format: REL_TYPE | FromNode | ToNode)",
        height=80
    )
    
    # Parse construction plan
    approved_construction_plan = {}
    if construction_plan_input.strip():
        for line in construction_plan_input.split("\n"):
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    rel_type, from_label, to_label = parts
                    key = f"{from_label}_{rel_type}_{to_label}"
                    approved_construction_plan[key] = {
                        "construction_type": "relationship",
                        "relationship_type": rel_type,
                        "from_node_label": from_label,
                        "to_node_label": to_label
                    }
    
    # Validate
    if not (kind_of_graph.strip() and graph_description.strip() and approved_files and approved_entities):
        st.warning("⚠️ All fields (1-3) are required. Field 4 is optional but recommended.")
    
    # Initialize Agent button
    if st.button("Initialize Agent", type="primary", 
                 disabled=not (kind_of_graph.strip() and graph_description.strip() and approved_files and approved_entities)):
        with st.spinner("Initializing agent..."):
            try:
                initial_state = {
                    "approved_user_goal": approved_user_goal,
                    "approved_files": approved_files,
                    "approved_entity_types": approved_entities,
                    "approved_construction_plan": approved_construction_plan  # Include to avoid redundancy
                }
                st.session_state.agent_caller = initialize_agent(initial_state)
                st.success("Agent initialized successfully!")
                st.session_state.messages = []
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
    
    st.divider()
    
    # Example prompts
    with st.expander("💡 Example Prompts & Info"):
        st.markdown("""
        **How it works:**
        The agent uses a critic pattern with automatic refinement:
        1. Proposal Agent proposes fact types from markdown files
        2. Critic Agent validates and checks for issues (duplicates, inverses, synonyms, redundancy)
        3. If issues found, loop iterates with feedback (max 3 times)
        4. If valid or max iterations reached, presents to you
        
        **Try these prompts:**
        - `Propose fact types that could be extracted from the markdown files`
        - `What relationships exist between these entity types in the text?`
        - `Analyze the files and suggest relevant fact types`
        
        **After automatic refinement:**
        - Review the proposed facts and critic feedback (if any)
        - `Yes, approve these fact types` (if you're satisfied)
        - Or provide additional feedback for manual refinement
        
        **Example Fact Types:**
        - (Artwork, displayed_at, Exhibition)
        - (Artist, founded, ArtMovement)
        - (Artwork, owned_by, Collection)
        - (Collection, held_by, Institution)
        
        **Note:** The critic automatically checks for:
        - ✓ No duplicates across files
        - ✓ No inverse relationships
        - ✓ No synonym predicates
        - ✓ No redundancy with existing structured relationships
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
        "approved_files": approved_files,
        "approved_entities": approved_entities
    })
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask the agent to propose fact types..."):
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
        async def get_session_state():
            session = await st.session_state.agent_caller.get_session()
            # Ensure session is not a coroutine
            if asyncio.iscoroutine(session):
                session = await session
            return session
        
        session = asyncio.run(get_session_state())
        
        # Verify session has state attribute
        if not hasattr(session, 'state'):
            st.error("Session object is invalid. Please try resetting and reinitializing the agent.")
            st.stop()
        
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
            
            st.subheader("Approved Entity Types")
            if APPROVED_ENTITIES in session.state:
                st.json(session.state[APPROVED_ENTITIES])
            else:
                st.warning("Not set")
        
        with col2:
            st.subheader("Proposed Fact Types")
            if PROPOSED_FACTS in session.state:
                facts = session.state[PROPOSED_FACTS]
                # Display as readable triples
                st.markdown("**Fact Triples:**")
                for pred_label, fact in facts.items():
                    st.markdown(
                        f"- `({fact['subject_label']}, {fact['predicate_label']}, {fact['object_label']})`"
                    )
                with st.expander("View Raw JSON"):
                    st.json(facts)
            else:
                st.info("Not proposed yet")
            
            st.subheader("Approved Fact Types")
            if APPROVED_FACTS in session.state:
                facts = session.state[APPROVED_FACTS]
                # Display as readable triples
                st.markdown("**Approved Fact Triples:**")
                for pred_label, fact in facts.items():
                    st.markdown(
                        f"- `({fact['subject_label']}, {fact['predicate_label']}, {fact['object_label']})`"
                    )
                with st.expander("View Raw JSON"):
                    st.json(facts)
            else:
                st.info("Not approved yet")
        
        # Critic feedback section (if available)
        if "critic_feedback" in session.state:
            st.divider()
            st.subheader("🔍 Critic Feedback")
            feedback = session.state["critic_feedback"]
            status = feedback.get("status", "unknown")
            
            if status == "valid":
                st.success("✓ Critic validated all fact types")
            elif status == "retry":
                st.warning("⚠ Critic requested refinement")
                issues = feedback.get("issues", [])
                if issues:
                    st.markdown("**Issues found:**")
                    for issue in issues:
                        st.markdown(f"- {issue}")
            
            # Show iteration count
            iteration = session.state.get("fact_refinement_iteration", 0)
            if iteration > 0:
                st.caption(f"Refinement iterations: {iteration}/3")
        
        # Full state (expandable)
        with st.expander("View Full Session State"):
            st.json(dict(session.state))
    
    except Exception as e:
        st.error(f"Error retrieving session state: {e}")
else:
    st.info("Initialize the agent to view session state.")

