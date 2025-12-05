"""
Streamlit UI for testing the Knowledge Extraction Agent.

This UI allows interactive testing of the Knowledge Extraction Agent with:
- Chat interface for user interaction
- Session state viewer
- Extraction progress dashboard
- Verbose logging toggle
- Reset session functionality
"""
import streamlit as st
import asyncio
import json
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add project root to sys.path for module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.knowledge_extraction_agent import knowledge_extraction_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_FILES,
    APPROVED_ENTITIES,
    APPROVED_FACTS,
    INGESTION_AUDIT_TRAIL
)


# Page configuration
st.set_page_config(
    page_title="Knowledge Extraction Agent Test",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Knowledge Extraction Agent Test UI")
st.markdown("Test the Knowledge Extraction Agent for extracting entities and facts from markdown files")

# Initialize session state
if "agent_caller" not in st.session_state:
    st.session_state.agent_caller = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "verbose_logging" not in st.session_state:
    st.session_state.verbose_logging = False


def initialize_agent(
    approved_user_goal: Dict[str, Any],
    approved_files: List[str],
    approved_entities: List[str],
    approved_facts: Dict[str, Any]
):
    """Initialize the agent caller with approved context."""
    try:
        # Initial state with all approved context
        initial_state = {
            APPROVED_USER_GOAL: approved_user_goal,
            APPROVED_FILES: approved_files,
            APPROVED_ENTITIES: approved_entities,
            APPROVED_FACTS: approved_facts
        }
        
        # Create agent caller with initial state
        agent_caller = asyncio.run(make_agent_caller(
            knowledge_extraction_agent,
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
    value="A knowledge graph for art collection provenance which includes all levels from artworks to artists, locations, and mediums.\n\nAdd artist biographies, exhibition histories, and provenance notes to provide deeper context and historical information about artworks and artists.",
    height=100
)

# Approved Files
st.sidebar.subheader("Approved Markdown Files")
with st.sidebar.expander("View/Edit Approved Files"):
    approved_files_text = st.text_area(
        "JSON Array",
        value='["artist_bios.md", "exhibition_histories.md", "provenance_notes.md"]',
        height=100
    )

# Approved Entities
st.sidebar.subheader("Approved Entity Types")
with st.sidebar.expander("View/Edit Approved Entities"):
    approved_entities_text = st.text_area(
        "JSON Array",
        value='["Artist", "Artwork", "Location", "Exhibition", "Collection", "ArtMovement", "Collector", "Institution"]',
        height=150
    )

# Approved Facts
st.sidebar.subheader("Approved Fact Types")
with st.sidebar.expander("View/Edit Approved Facts"):
    approved_facts_text = st.text_area(
        "JSON Object",
        value="""{
    "born_in": {
        "subject_label": "Artist",
        "predicate_label": "born_in",
        "object_label": "Location"
    },
    "founder_of": {
        "subject_label": "Artist",
        "predicate_label": "founder_of",
        "object_label": "ArtMovement"
    },
    "featured_in": {
        "subject_label": "Artwork",
        "predicate_label": "featured_in",
        "object_label": "Exhibition"
    },
    "owned_by": {
        "subject_label": "Artwork",
        "predicate_label": "owned_by",
        "object_label": "Collector"
    },
    "loaned_for": {
        "subject_label": "Artwork",
        "predicate_label": "loaned_for",
        "object_label": "Exhibition"
    }
}""",
        height=300
    )

# Initialize button
if st.sidebar.button("Initialize Agent", type="primary"):
    try:
        # Parse inputs
        approved_user_goal = {"graph_description": user_goal}
        approved_files = json.loads(approved_files_text)
        approved_entities = json.loads(approved_entities_text)
        approved_facts = json.loads(approved_facts_text)
        
        # Initialize agent
        initialize_agent(
            approved_user_goal,
            approved_files,
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

# Neo4j Setup Section
st.sidebar.divider()
st.sidebar.subheader("🔧 Neo4j Setup")

# Connection status check
if st.sidebar.button("Check Neo4j Connection"):
    if st.session_state.agent_caller is not None:
        async def check_connection():
            response = await st.session_state.agent_caller.call(
                "Check if Neo4j is ready",
                verbose=False
            )
            return response
        
        try:
            result = asyncio.run(check_connection())
            st.sidebar.success("✅ " + result)
        except Exception as e:
            st.sidebar.error(f"❌ Connection failed: {e}")
    else:
        st.sidebar.warning("⚠️ Initialize agent first")


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
                    
                    # Force rerun to refresh extraction progress after extraction
                    st.rerun()
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
    st.info("👈 Please initialize the agent in the sidebar to start chatting")


# Extraction Progress Dashboard
st.divider()
st.header("3. Extraction Progress")

if st.session_state.agent_caller is not None:
    async def get_session_state():
        session = await st.session_state.agent_caller.get_session()
        return session.state if session else {}
    
    try:
        session_state = asyncio.run(get_session_state())
        
        # Get extraction progress from audit trail
        audit_trail = session_state.get(INGESTION_AUDIT_TRAIL, [])
        extraction_actions = [a for a in audit_trail if a.get("action") == "knowledge_extraction"]
        
        if extraction_actions:
            # Summary metrics
            st.subheader("📊 Extraction Summary")
            
            total_nodes = sum(a.get("nodes_created", 0) for a in extraction_actions)
            total_relationships = sum(a.get("relationships_created", 0) for a in extraction_actions)
            total_chunks = sum(a.get("chunks_processed", 0) for a in extraction_actions)
            total_files = len(extraction_actions)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Files Processed", total_files)
            col2.metric("Chunks Processed", total_chunks)
            col3.metric("Entities Extracted", total_nodes)
            col4.metric("Relationships Extracted", total_relationships)
            
            # Detailed trail
            st.divider()
            st.subheader("📋 Detailed Extraction Trail")
            
            for idx, action in enumerate(extraction_actions, 1):
                with st.expander(f"File {idx}: {action.get('file', 'N/A')}"):
                    st.json(action)
        else:
            st.info("No extraction progress yet. Ask the agent to extract knowledge from markdown files.")
        
    except Exception as e:
        st.error(f"Error displaying extraction progress: {e}")
else:
    st.info("Initialize agent to view extraction progress")


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
    **Prerequisites:**
    1. NER Agent must be run and entities approved
    2. Fact Extraction Agent must be run and facts approved
    3. File Suggestion Agent (Unstructured) must be run and files approved
    4. Neo4j must be running and connected
    
    **Getting Started:**
    1. Initialize the agent with approved files, entities, and facts
    2. Check Neo4j connection
    3. Ask the agent to extract knowledge from markdown files
    4. Monitor extraction progress in the dashboard
    
    **Example Prompts:**
    - "Check if Neo4j is ready"
    - "Extract knowledge from the approved markdown files"
    - "Execute knowledge extraction"
    - "Show me the extraction progress"
    
    **Process:**
    1. Agent checks Neo4j connection
    2. Gets approved files, entities, and facts
    3. Processes each markdown file:
       - Chunks the file by separator ("---")
       - Extracts entities and relationships from each chunk using LLM
       - Creates Document, Chunk, Entity, and Relationship nodes
       - Links entities to source chunks for provenance
    4. Reports final summary
    
    **Graph Structure Created:**
    - Document nodes (one per markdown file)
    - Chunk nodes (text chunks from files)
    - Entity nodes (extracted entities with approved types)
    - Relationship nodes (extracted facts/relationships)
    - Document → HAS_CHUNK → Chunk
    - Entity → EXTRACTED_FROM → Chunk
    - Entity → [fact_type] → Entity
    
    **API Optimization:**
    - Uses batch execution tool (execute_knowledge_extraction)
    - Reduces API calls from 20-30+ to just 1-2
    - Processes all files in one operation
    """)

