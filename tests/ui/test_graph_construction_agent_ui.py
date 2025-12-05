"""
Streamlit UI for testing the Graph Construction Agent.

This UI allows interactive testing of the Graph Construction Agent with:
- Chat interface for user interaction
- Session state viewer
- Ingestion progress dashboard
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

from src.agents.graph_construction_agent import graph_construction_agent
from src.utils.helper import make_agent_caller, AgentCaller
from src.utils.constants import (
    APPROVED_USER_GOAL,
    APPROVED_CONSTRUCTION_PLAN,
    INGESTION_AUDIT_TRAIL,
    AUDIT_RESOLUTIONS
)


# Page configuration
st.set_page_config(
    page_title="Graph Construction Agent Test",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Graph Construction Agent Test UI")
st.markdown("Test the Graph Construction Agent for building the knowledge graph in Neo4j")

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
    audit_resolutions: Dict[str, Any] = None
):
    """Initialize the agent caller with approved context."""
    try:
        # Initial state with all approved context
        initial_state = {
            APPROVED_USER_GOAL: approved_user_goal,
            APPROVED_CONSTRUCTION_PLAN: approved_construction_plan
        }
        
        # Add audit resolutions if provided
        if audit_resolutions:
            initial_state[AUDIT_RESOLUTIONS] = audit_resolutions
        
        # Create agent caller with initial state
        agent_caller = asyncio.run(make_agent_caller(
            graph_construction_agent,
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
        "source_file": "artwork_artist.csv",
        "relationship_type": "CREATED_BY",
        "from_node_label": "Artwork",
        "to_node_label": "Artist",
        "from_node_column": "artwork_id",
        "to_node_column": "artist_id"
    },
    "LOCATED_AT_rel": {
        "construction_type": "relationship",
        "source_file": "artwork_location.csv",
        "relationship_type": "LOCATED_AT",
        "from_node_label": "Artwork",
        "to_node_label": "Location",
        "from_node_column": "artwork_id",
        "to_node_column": "location_id"
    }
}""",
        height=400
    )

# Audit Resolutions (optional)
st.sidebar.subheader("Pre-Ingestion Audit Resolutions (Optional)")
with st.sidebar.expander("Add Audit Resolutions"):
    resolutions_text = st.text_area(
        "JSON (leave empty if none)",
        value="{}",
        height=150,
        help="Resolutions from pre-ingestion audit agent, if any"
    )

# Initialize button
if st.sidebar.button("Initialize Agent", type="primary"):
    try:
        # Parse inputs
        approved_user_goal = {"graph_description": user_goal}
        approved_construction_plan = json.loads(construction_plan_text)
        
        # Parse audit resolutions if provided
        audit_resolutions = None
        if resolutions_text.strip() and resolutions_text.strip() != "{}":
            audit_resolutions = json.loads(resolutions_text)
        
        # Initialize agent
        initialize_agent(
            approved_user_goal,
            approved_construction_plan,
            audit_resolutions
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

# Clear Neo4j button (with confirmation)
st.sidebar.markdown("**⚠️ Clear Graph Data**")
clear_confirmed = st.sidebar.checkbox(
    "I understand this will delete all data",
    key="clear_confirmation"
)

if st.sidebar.button("🗑️ Clear Neo4j Database", disabled=not clear_confirmed):
    if st.session_state.agent_caller is not None:
        async def clear_db():
            response = await st.session_state.agent_caller.call(
                "Clear all data from Neo4j database",
                verbose=False
            )
            return response
        
        try:
            # Use status message in sidebar since spinner doesn't work there
            status_placeholder = st.sidebar.empty()
            status_placeholder.info("🔄 Clearing Neo4j...")
            result = asyncio.run(clear_db())
            status_placeholder.empty()
            st.sidebar.success("✅ " + result)
            st.sidebar.info("💡 You can now rebuild the graph without duplicates")
        except Exception as e:
            st.sidebar.error(f"❌ Failed to clear: {e}")
    else:
        st.sidebar.warning("⚠️ Initialize agent first")

# Neo4j setup instructions
with st.sidebar.expander("📖 Neo4j Setup Instructions"):
    setup_method = st.radio(
        "Choose setup method:",
        ["🐳 Docker (Recommended)", "🖥️ Neo4j Desktop"],
        key="neo4j_setup_method"
    )
    
    if setup_method == "🐳 Docker (Recommended)":
        st.markdown("""
        **Quick Setup with Docker:**
        
        **1. Install Docker:**
        - Download Docker Desktop: https://docs.docker.com/get-docker/
        - Start Docker Desktop
        
        **2. Run Setup Script:**
        
        **Linux/macOS:**
        ```bash
        chmod +x scripts/setup_neo4j.sh
        ./scripts/setup_neo4j.sh
        ```
        
        **Windows (PowerShell):**
        ```powershell
        .\scripts\setup_neo4j.ps1
        ```
        
        **Or use Docker Compose:**
        ```bash
        docker-compose up -d
        ```
        
        **3. Set Environment Variables:**
        Create/update `.env` file:
        ```
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USERNAME=neo4j
        NEO4J_PASSWORD=your_password
        NEO4J_DATABASE=neo4j
        ```
        
        **4. Place CSV Files:**
        - Copy CSV files to `./neo4j_import/` directory
        - Or use: `docker cp file.csv neo4j:/var/lib/neo4j/import/`
        
        **5. Access Neo4j:**
        - Browser: http://localhost:7474
        - Bolt: bolt://localhost:7687
        
        **Useful Commands:**
        - `docker logs neo4j` - View logs
        - `docker stop neo4j` - Stop Neo4j
        - `docker start neo4j` - Start Neo4j
        """)
    else:
        st.markdown("""
        **Neo4j Desktop Setup:**
        
        **1. Install Neo4j Desktop:**
        - Download from https://neo4j.com/download/
        - Install and create a new database
        
        **2. Set Environment Variables:**
        Create a `.env` file in project root:
        ```
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USERNAME=neo4j
        NEO4J_PASSWORD=your_password
        NEO4J_DATABASE=neo4j
        ```
        
        **3. Start Neo4j:**
        - Open Neo4j Desktop
        - Start your database
        - Note the bolt:// URI (usually bolt://localhost:7687)
        
        **4. Place CSV Files:**
        - Find Neo4j import directory (check with agent)
        - Copy CSV files to that directory
        - Default: `neo4j/import/` or check Neo4j Desktop settings
        """)
    
    st.markdown("""
    **Prevent Duplicates:**
    - Use "Clear Neo4j Database" button before rebuilding
    - Or use MERGE (already implemented) - won't create duplicates
    """)


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
                    
                    # Force rerun to refresh ingestion progress after construction
                    st.rerun()
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
    st.info("👈 Please initialize the agent in the sidebar to start chatting")


# Ingestion Progress Dashboard
st.divider()
st.header("3. Ingestion Progress")

if st.session_state.agent_caller is not None:
    async def get_session_state():
        session = await st.session_state.agent_caller.get_session()
        return session.state if session else {}
    
    try:
        session_state = asyncio.run(get_session_state())
        
        audit_trail = session_state.get(INGESTION_AUDIT_TRAIL, [])
        
        if audit_trail:
            # Summary metrics
            st.subheader("📊 Ingestion Summary")
            
            node_actions = [a for a in audit_trail if a.get("action") == "load_nodes"]
            rel_actions = [a for a in audit_trail if a.get("action") == "load_relationships"]
            
            total_nodes = sum(a.get("nodes_loaded", 0) for a in node_actions)
            total_relationships = sum(a.get("relationships_loaded", 0) for a in rel_actions)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Actions", len(audit_trail))
            col2.metric("Nodes Loaded", total_nodes)
            col3.metric("Relationships Loaded", total_relationships)
            
            # Detailed trail
            st.divider()
            st.subheader("📋 Detailed Audit Trail")
            
            for idx, action in enumerate(audit_trail, 1):
                with st.expander(f"Action {idx}: {action.get('action', 'unknown')} - {action.get('file', 'N/A')}"):
                    st.json(action)
        else:
            st.info("No ingestion progress yet. Ask the agent to build the graph.")
        
    except Exception as e:
        st.error(f"Error displaying ingestion progress: {e}")
else:
    st.info("Initialize agent to view ingestion progress")


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
    **Neo4j Setup (First Time):**
    1. Install Neo4j Desktop and create a database
    2. Set environment variables in `.env` file:
       - NEO4J_URI=bolt://localhost:7687
       - NEO4J_USERNAME=neo4j
       - NEO4J_PASSWORD=your_password
    3. Start Neo4j database in Desktop
    4. Place CSV files in Neo4j import directory
    5. Click "Check Neo4j Connection" to verify
    
    **Preventing Duplicates:**
    - **Option 1:** Click "Clear Neo4j Database" before building (recommended for testing)
    - **Option 2:** Use MERGE (already implemented) - safe to run multiple times
    - MERGE updates existing nodes instead of creating duplicates
    
    **Getting Started:**
    1. Initialize the agent with your construction plan
    2. Check Neo4j connection
    3. (Optional) Clear database for fresh start
    4. Ask the agent to build the graph
    5. Monitor ingestion progress in the dashboard
    
    **Example Prompts:**
    - "Check if Neo4j is ready"
    - "Clear all data from Neo4j database"
    - "Please build the graph according to the construction plan"
    - "Execute the construction plan"
    - "Show me the ingestion progress"
    
    **Process:**
    1. Agent checks Neo4j connection
    2. Creates uniqueness constraints for all node types
    3. Loads all nodes from CSV files (using MERGE)
    4. Loads all relationships from CSV files
    5. Reports final summary
    
    **Pre-Ingestion Audit:**
    - If you ran the pre-ingestion audit agent, you can provide
      the audit resolutions in the sidebar
    - The agent will apply those resolutions during ingestion
    """)

