"""
Shared tools for accessing state from previous agents.
These tools allow agents to read approved outputs from earlier stages.
"""
from google.adk.tools import ToolContext

from src.utils.constants import APPROVED_USER_GOAL, APPROVED_FILES
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def get_approved_user_goal(tool_context: ToolContext):
    """
    Returns the user's goal, which is a dictionary containing the kind of graph and its description.
    
    This tool reads the approved_user_goal from session state, which was set by the User Intent Agent.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_user_goal or error message
    """
    if APPROVED_USER_GOAL not in tool_context.state:
        return tool_error(
            f"{APPROVED_USER_GOAL} not set. Ask the user to clarify their goal "
            "(kind of graph and description) using the User Intent Agent."
        )
    
    user_goal_data = tool_context.state[APPROVED_USER_GOAL]
    return tool_success("approved_user_goal", user_goal_data)


def get_approved_files(tool_context: ToolContext):
    """
    Returns the files that have been approved for import.
    
    This tool reads the approved_files from session state, which was set by the File Suggestion Agent.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and approved_files or error message
    """
    if APPROVED_FILES not in tool_context.state:
        return tool_error(
            f"{APPROVED_FILES} not set. Ask the user to approve the file suggestions "
            "using the File Suggestion Agent."
        )
    
    files = tool_context.state[APPROVED_FILES]
    return tool_success("approved_files", files)


