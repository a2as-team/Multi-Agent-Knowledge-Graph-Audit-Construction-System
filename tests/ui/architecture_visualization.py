"""
Architecture Visualization UI - Visual Concept Diagram

Interactive visual concept diagram with color-coded phases,
embedded details, and visual flow connections.

Run with: streamlit run tests/ui/architecture_visualization.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="Architecture Concept Diagram",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Visual Concept Diagram CSS
st.markdown("""
<style>
    .diagram-container {
        width: 100%;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .phase-node {
        position: relative;
        border: 3px solid;
        border-radius: 10px;
        padding: 12px;
        margin: 8px;
        min-width: 140px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    
    .phase-node:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    
    .phase-planning {
        background: linear-gradient(135deg, #e3f2fd 0%, #90caf9 100%);
        border-color: #1976d2;
        color: #0d47a1;
    }
    
    .phase-quality {
        background: linear-gradient(135deg, #f3e5f5 0%, #ce93d8 100%);
        border-color: #7b1fa2;
        color: #4a148c;
    }
    
    .phase-blocking {
        background: linear-gradient(135deg, #ffebee 0%, #ef5350 100%);
        border-color: #c62828;
        color: #b71c1c;
        font-weight: bold;
    }
    
    .phase-construction {
        background: linear-gradient(135deg, #e8f5e9 0%, #81c784 100%);
        border-color: #388e3c;
        color: #1b5e20;
    }
    
    .phase-validation {
        background: linear-gradient(135deg, #fff3e0 0%, #ffb74d 100%);
        border-color: #f57c00;
        color: #e65100;
    }
    
    .phase-review {
        background: linear-gradient(135deg, #e1f5fe 0%, #4fc3f7 100%);
        border-color: #0277bd;
        color: #01579b;
    }
    
    .phase-final {
        background: linear-gradient(135deg, #f1f8e9 0%, #aed581 100%);
        border-color: #558b2f;
        color: #33691e;
    }
    
    .phase-number {
        font-size: 0.7em;
        opacity: 0.8;
        margin-bottom: 4px;
    }
    
    .phase-icon {
        font-size: 1.8em;
        margin: 4px 0;
    }
    
    .phase-name {
        font-size: 0.85em;
        font-weight: bold;
        margin: 4px 0;
    }
    
    .phase-meta {
        font-size: 0.7em;
        margin-top: 6px;
        opacity: 0.9;
    }
    
    .phase-details {
        font-size: 0.65em;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid rgba(0,0,0,0.2);
        text-align: left;
    }
    
    .detail-item {
        margin: 3px 0;
        font-size: 0.7em;
    }
    
    .state-key-mini {
        background: rgba(255,255,255,0.7);
        padding: 2px 4px;
        border-radius: 3px;
        font-family: monospace;
        font-size: 0.65em;
        margin: 2px 0;
        display: block;
    }
    
    .flow-row {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 10px 0;
        flex-wrap: wrap;
    }
    
    .arrow-right {
        font-size: 24px;
        color: #666;
        margin: 0 5px;
    }
    
    .arrow-down {
        font-size: 24px;
        color: #666;
        margin: 5px 0;
    }
    
    .stage-label {
        text-align: center;
        font-weight: bold;
        color: #666;
        margin: 15px 0 5px 0;
        font-size: 0.9em;
    }
    
    .blocking-badge {
        position: absolute;
        top: -8px;
        right: -8px;
        background: #f44336;
        color: white;
        border-radius: 50%;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7em;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Architecture Data
PHASES = [
    {
        "id": 1,
        "name": "Planning & Schema",
        "icon": "📋",
        "class": "phase-planning",
        "agents": 6,
        "description": "Define goals, identify files, propose schema",
        "outputs": ["APPROVED_USER_GOAL", "APPROVED_FILES", "APPROVED_CONSTRUCTION_PLAN"]
    },
    {
        "id": 2,
        "name": "Quality Rules",
        "icon": "📏",
        "class": "phase-quality",
        "agents": 1,
        "description": "Define custom validation rules",
        "outputs": ["DATA_QUALITY_RULES"]
    },
    {
        "id": 3,
        "name": "Pre-Ingestion",
        "icon": "🔍",
        "class": "phase-blocking",
        "agents": 2,
        "blocking": True,
        "description": "Scan for data issues - BLOCKS Phase 4",
        "outputs": ["PRE_INGESTION_AUDIT_QUERIES", "PRE_INGESTION_RESOLUTIONS"]
    },
    {
        "id": 4,
        "name": "KG Construction",
        "icon": "🏗️",
        "class": "phase-construction",
        "agents": 2,
        "description": "Build knowledge graph from CSV & markdown",
        "outputs": ["INGESTION_AUDIT_TRAIL"]
    },
    {
        "id": 5,
        "name": "Entity Resolution",
        "icon": "🔗",
        "class": "phase-validation",
        "agents": 1,
        "description": "Propose entity matches",
        "outputs": ["ENTITY_RESOLUTION_AUDIT_QUERIES"]
    },
    {
        "id": 6,
        "name": "Post-Ingestion",
        "icon": "✅",
        "class": "phase-validation",
        "agents": 1,
        "description": "Validate KG quality",
        "outputs": ["POST_INGESTION_AUDIT_QUERIES"]
    },
    {
        "id": 7,
        "name": "Unified Review",
        "icon": "📊",
        "class": "phase-review",
        "agents": 1,
        "description": "Review Entity + Post queries together",
        "outputs": ["AUDIT_RESOLUTIONS"]
    },
    {
        "id": 8,
        "name": "Execution",
        "icon": "⚙️",
        "class": "phase-review",
        "agents": 1,
        "description": "Execute approved resolutions",
        "outputs": ["AUDIT_EXECUTION_TRAIL"]
    },
    {
        "id": 9,
        "name": "Final Report",
        "icon": "📄",
        "class": "phase-final",
        "agents": 2,
        "description": "Generate audit report",
        "outputs": ["FINAL_AUDIT_REPORT"]
    },
]

def render_phase_node(phase: Dict[str, Any], show_details: bool = True) -> str:
    """Generate HTML for a phase node with embedded details"""
    blocking_badge = '<div class="blocking-badge">!</div>' if phase.get("blocking") else ""
    
    # Truncate description for display
    desc = phase['description'][:50] + "..." if len(phase['description']) > 50 else phase['description']
    
    # State keys preview (first 2)
    state_keys_html = ""
    if show_details and phase.get('outputs'):
        keys_preview = phase['outputs'][:2]
        state_keys_html = '<div class="phase-details">'
        state_keys_html += f'<div class="detail-item"><strong>Outputs:</strong></div>'
        for key in keys_preview:
            state_keys_html += f'<span class="state-key-mini">{key}</span>'
        if len(phase['outputs']) > 2:
            state_keys_html += f'<span class="state-key-mini">+{len(phase["outputs"])-2} more</span>'
        state_keys_html += '</div>'
    
    blocking_note = '<div class="detail-item" style="color: #c62828; font-weight: bold;">⚠️ BLOCKS Phase 4</div>' if phase.get("blocking") else ""
    
    html = f"""
    <div class="phase-node {phase['class']}" onclick="showPhase({phase['id']})" style="min-width: 180px;">
        {blocking_badge}
        <div class="phase-number">Phase {phase['id']}</div>
        <div class="phase-icon">{phase['icon']}</div>
        <div class="phase-name">{phase['name']}</div>
        <div class="phase-meta">
            {phase['agents']} agent(s) • {len(phase['outputs'])} state key(s)
        </div>
        {blocking_note}
        {state_keys_html if show_details else ''}
    </div>
    """
    return html

def render_visual_diagram():
    """Render the complete visual concept diagram"""
    
    diagram_html = """
    <div class="diagram-container">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333; margin: 0;">🏗️ Setu Content Audit System Architecture</h2>
            <p style="color: #666; margin: 5px 0;">Visual Concept Diagram - Click phases for details</p>
        </div>
        
        <!-- Stage 1: Planning -->
        <div class="stage-label">📋 STAGE 1: Planning & Preparation</div>
        <div class="flow-row">
    """
    
    # Row 1: Phases 1-2
    diagram_html += render_phase_node(PHASES[0], show_details=True)
    diagram_html += '<span class="arrow-right">→</span>'
    diagram_html += render_phase_node(PHASES[1], show_details=True)
    
    diagram_html += """
        </div>
        <div class="arrow-down">↓</div>
        
        <!-- Stage 2: Pre-Ingestion (Blocking) -->
        <div class="stage-label">🔴 STAGE 2: Pre-Ingestion Validation (BLOCKING)</div>
        <div class="flow-row">
    """
    
    # Row 2: Phase 3 (Blocking)
    diagram_html += render_phase_node(PHASES[2], show_details=True)
    
    diagram_html += """
        </div>
        <div class="arrow-down">↓</div>
        
        <!-- Stage 3: Construction -->
        <div class="stage-label">🏗️ STAGE 3: Knowledge Graph Construction</div>
        <div class="flow-row">
    """
    
    # Row 3: Phase 4
    diagram_html += render_phase_node(PHASES[3], show_details=True)
    
    diagram_html += """
        </div>
        <div class="arrow-down">↓</div>
        
        <!-- Stage 4: Validation -->
        <div class="stage-label">🔍 STAGE 4: Validation & Resolution</div>
        <div class="flow-row">
    """
    
    # Row 4: Phases 5-6
    diagram_html += render_phase_node(PHASES[4], show_details=True)
    diagram_html += '<span class="arrow-right">→</span>'
    diagram_html += render_phase_node(PHASES[5], show_details=True)
    
    diagram_html += """
        </div>
        <div class="arrow-down">↓</div>
        
        <!-- Stage 5: Review & Finalization -->
        <div class="stage-label">📊 STAGE 5: Review & Finalization</div>
        <div class="flow-row">
    """
    
    # Row 5: Phases 7-9
    diagram_html += render_phase_node(PHASES[6], show_details=True)
    diagram_html += '<span class="arrow-right">→</span>'
    diagram_html += render_phase_node(PHASES[7], show_details=True)
    diagram_html += '<span class="arrow-right">→</span>'
    diagram_html += render_phase_node(PHASES[8], show_details=True)
    
    diagram_html += """
        </div>
    </div>
    
    <script>
    function showPhase(id) {
        // This will be handled by Streamlit button clicks
        window.parent.postMessage({type: 'phase_click', phaseId: id}, '*');
    }
    </script>
    """
    
    return diagram_html

# Initialize session state
if "selected_phase" not in st.session_state:
    st.session_state["selected_phase"] = None

# Header
st.title("🏗️ Architecture Concept Diagram")
st.markdown("**Interactive visual diagram with color-coded phases and embedded details**")

# Render the visual diagram
st.markdown(render_visual_diagram(), unsafe_allow_html=True)

# Phase selection buttons (invisible but functional)
st.markdown("### Select Phase for Details")
cols = st.columns(9)
for idx, phase in enumerate(PHASES):
    with cols[idx]:
        if st.button(
            f"P{phase['id']}",
            key=f"phase_{phase['id']}",
            use_container_width=True,
            type="primary" if phase.get("blocking") else "secondary"
        ):
            st.session_state["selected_phase"] = phase["id"]
            st.rerun()

# Phase details panel
if st.session_state.get("selected_phase"):
    phase = PHASES[st.session_state["selected_phase"] - 1]
    
    st.divider()
    
    # Color-coded header matching phase
    st.markdown(f"""
    <div style="background: {'#ffebee' if phase.get('blocking') else '#e3f2fd'}; 
                padding: 15px; border-radius: 8px; border-left: 5px solid {'#c62828' if phase.get('blocking') else '#1976d2'};">
        <h3>{phase['icon']} Phase {phase['id']}: {phase['name']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Description:** {phase['description']}")
    
    if phase.get("blocking"):
        st.error("🔴 **BLOCKING PHASE** - Must complete before Phase 4")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Agents", phase["agents"])
    with col2:
        st.metric("State Keys Created", len(phase["outputs"]))
    
    st.markdown("**State Keys Created:**")
    for key in phase["outputs"]:
        st.code(key, language=None)
    
    if st.button("Close Details", use_container_width=True):
        st.session_state["selected_phase"] = None
        st.rerun()

# Legend
st.divider()
st.markdown("### 🎨 Color Legend")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown("**📋 Planning**<br>Blue", unsafe_allow_html=True)
with col2:
    st.markdown("**📏 Quality**<br>Purple", unsafe_allow_html=True)
with col3:
    st.markdown("**🔴 Blocking**<br>Red", unsafe_allow_html=True)
with col4:
    st.markdown("**🏗️ Construction**<br>Green", unsafe_allow_html=True)
with col5:
    st.markdown("**📊 Review**<br>Cyan", unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    Architecture Concept Diagram | Setu Content Audit System
</div>
""", unsafe_allow_html=True)
