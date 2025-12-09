# Architecture Diagram Web Apps

## Overview
Two standalone, interactive web applications for visualizing the Setu Content Audit System architecture:

1. **architecture_diagram.html** - High-level phase view (9 phases)
2. **architecture_diagram_detailed.html** - Detailed agent view (17 agents individually)

## How to Use

### Option 1: Direct Browser Open
1. Navigate to `tests/ui/` directory
2. Double-click:
   - `architecture_diagram.html` for high-level phase view
   - `architecture_diagram_detailed.html` for detailed agent view
3. The diagram will open in your default browser

### Option 2: Local Server (Recommended)
```bash
# Using Python
cd tests/ui
python -m http.server 8000

# Then open in browser:
# High-level: http://localhost:8000/architecture_diagram.html
# Detailed: http://localhost:8000/architecture_diagram_detailed.html
```

### Option 3: VS Code Live Server
1. Install "Live Server" extension in VS Code
2. Right-click `architecture_diagram.html`
3. Select "Open with Live Server"

## Features

### High-Level Diagram (architecture_diagram.html)
- **Single-Screen View**: All 9 phases visible without scrolling
- **Color-Coded Phases**: Visual distinction between phase types
- **Interactive**: Click any phase to see detailed information
- **Embedded Details**: Key information visible directly in phase boxes

### Detailed Diagram (architecture_diagram_detailed.html)
- **All 17 Agents**: Each agent shown individually in sequence
- **Agent-Level Detail**: See each agent's inputs, outputs, and purpose
- **Phase Dividers**: Clear visual separation between phases
- **Complete Flow**: Understand exact sequence of agent execution

### Both Versions
- **Interactive**: Click any phase/agent to see detailed information
- **Responsive Design**: Works on different screen sizes
- **No Dependencies**: Pure HTML/CSS/JavaScript - no frameworks needed
- **Color-Coded**: Visual distinction between agent/phase types

## Phase Color Coding

- 🔵 **Blue**: Planning phases
- 🟣 **Purple**: Quality Rules
- 🔴 **Red**: Blocking phase (Pre-Ingestion)
- 🟢 **Green**: Construction phase
- 🟠 **Orange**: Validation phases
- 🔵 **Cyan**: Review phases
- 🟢 **Light Green**: Final phase

## Interaction

- **Click** any phase box to see detailed information
- **Modal popup** shows:
  - Full description
  - All agents in the phase
  - State keys created
  - Prerequisites and notes
- **Close** by clicking X button, overlay, or pressing Escape key

## File Structure

```
tests/ui/
├── architecture_diagram.html          # High-level phase view (9 phases)
├── architecture_diagram_detailed.html  # Detailed agent view (17 agents)
└── README_ARCHITECTURE_DIAGRAM.md     # This file
```

## Which Version to Use?

- **Use High-Level** (`architecture_diagram.html`): 
  - Quick overview of system phases
  - Understanding workflow at phase level
  - Presentation to stakeholders
  
- **Use Detailed** (`architecture_diagram_detailed.html`):
  - Understanding exact agent sequence
  - Implementation reference
  - Detailed agent inputs/outputs
  - Developer onboarding

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

## Customization

The HTML file is self-contained. You can modify:
- Colors in the `<style>` section
- Phase data in the `phaseData` JavaScript object
- Layout and styling as needed

