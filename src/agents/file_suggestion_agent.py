"""
File Suggestion Agent - Suggests relevant files for knowledge graph construction.

This agent is for STRUCTURED data (CSV/JSON files).
It analyzes available files and suggests which ones are relevant based on the approved user goal.

Domain-specific adaptation happens through user inputs during testing.
"""
import warnings
import logging
from pathlib import Path
from typing import Dict, Any, List

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from src.utils.config import DEFAULT_MODEL
from src.utils.constants import (
    ALL_AVAILABLE_FILES,
    SUGGESTED_FILES,
    APPROVED_FILES
)
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal
from src.tools.file_tools import list_available_files, sample_file
from src.neo4j.neo4j_for_adk import tool_success, tool_error

# Ignore warnings
warnings.filterwarnings("ignore")

# Set logging level
logging.basicConfig(level=logging.CRITICAL)


# Initialize LLM with Gemini
try:
    llm = LiteLlm(model=DEFAULT_MODEL)
    logger.info(f"Initialized LLM with model: {DEFAULT_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    raise


# ============================================================================
# Agent Instructions (Generic - works for any knowledge graph use case)
# ============================================================================

file_suggestion_agent_instruction = """
You are a constructive critic AI reviewing a list of files. Your goal is to suggest relevant files
for constructing a knowledge graph.

**Task:**
Review the file list for relevance to the kind of graph and description specified in the approved user goal. 

For any file that you're not sure about, use the 'sample_file' tool to get 
a better understanding of the file contents. 

Only consider structured data files like CSV or JSON.

Prepare for the task:
- use the 'get_approved_user_goal' tool to get the approved user goal

Think carefully, repeating these steps until finished:
1. list available files using the 'list_available_files' tool
2. evaluate the relevance of each file, then record the list of suggested files using the 'set_suggested_files' tool
3. use the 'get_suggested_files' tool to get the list of suggested files
4. ask the user to approve the set of suggested files
5. If the user has feedback, go back to step 1 with that feedback in mind
6. If approved, use the 'approve_suggested_files' tool to record the approval
"""


# ============================================================================
# Tool Definitions (Agent-specific)
# ============================================================================

def set_suggested_files(suggest_files: List[str], tool_context: ToolContext) -> Dict[str, Any]:
    """
    Set the suggested files to be used for data import.

    Args:
        suggest_files: List of file paths to suggest (relative to data directory)
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and suggested_files or error message.
    """
    tool_context.state[SUGGESTED_FILES] = suggest_files
    logger.info(f"Set suggested files: {suggest_files}")
    return tool_success(SUGGESTED_FILES, suggest_files)


def get_suggested_files(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Get the files that have been suggested for data import.
    
    Helps encourage the LLM to first set the suggested files before approving.
    This is an important strategy for maintaining consistency through defined values.

    Args:
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and suggested_files or error message.
    """
    if SUGGESTED_FILES not in tool_context.state:
        return tool_error(
            f"{SUGGESTED_FILES} not set. Use 'set_suggested_files' tool first to suggest files."
        )
    
    return tool_success(SUGGESTED_FILES, tool_context.state[SUGGESTED_FILES])


def approve_suggested_files(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Approves the suggested files in state for further processing as approved_files.
    
    Only call this tool if the user has explicitly approved the suggested files.
    
    Args:
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and approved_files or error message.
    """
    if SUGGESTED_FILES not in tool_context.state:
        return tool_error(
            "Current files have not been set. Take no action other than to inform user."
        )

    tool_context.state[APPROVED_FILES] = tool_context.state[SUGGESTED_FILES]
    logger.info(f"Approved files: {tool_context.state[APPROVED_FILES]}")
    return tool_success(APPROVED_FILES, tool_context.state[APPROVED_FILES])


# List of tools for the file suggestion agent
file_suggestion_agent_tools = [
    get_approved_user_goal,  # From schema_tools
    list_available_files,    # From file_tools
    sample_file,             # From file_tools
    set_suggested_files,     # Agent-specific
    get_suggested_files,     # Agent-specific
    approve_suggested_files  # Agent-specific
]


# ============================================================================
# Agent Definition
# ============================================================================

file_suggestion_agent = Agent(
    name="file_suggestion_agent_v1",
    model=llm,  # Gemini model defined earlier
    description="Helps the user select files to import for structured data.",  # used for delegation
    instruction=file_suggestion_agent_instruction,  # the complete instructions
    tools=file_suggestion_agent_tools,  # the list of tools
)

logger.info(f"Created agent: {file_suggestion_agent.name}")

