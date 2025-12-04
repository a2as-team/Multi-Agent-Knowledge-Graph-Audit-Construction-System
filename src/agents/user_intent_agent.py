"""
User Intent Agent - Helps users ideate on knowledge graph use cases.

This agent is generic and works for any knowledge graph use case.
Domain-specific adaptation happens through user inputs during testing.
"""
import warnings
import logging

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from src.utils.config import DEFAULT_MODEL, get_gemini_api_key
from src.utils.constants import PERCEIVED_USER_GOAL, APPROVED_USER_GOAL
from src.utils.logger import logger
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

agent_role_and_goal = """
    You are an expert at knowledge graph use cases. 
    Your primary goal is to help the user come up with a knowledge graph use case.
"""

agent_conversational_hints = """
    If the user is unsure what to do, make some suggestions based on classic use cases like:
    - social network involving friends, family, or professional relationships
    - logistics network with suppliers, customers, and partners
    - recommendation system with customers, products, and purchase patterns
    - fraud detection over multiple accounts with suspicious patterns of transactions
    - pop-culture graphs with movies, books, or music
"""

agent_output_definition = """
    A user goal has two components:
    - kind_of_graph: at most 3 words describing the graph, for example "social network" or "USA freight logistics"
    - description: a few sentences about the intention of the graph, for example "A dynamic routing and delivery system for cargo." or "Analysis of product dependencies and supplier alternatives."
"""

agent_chain_of_thought_directions = """
    Think carefully and collaborate with the user:
    1. Understand the user's goal, which is a kind_of_graph with description
    2. Ask clarifying questions as needed
    3. When you think you understand their goal, use the 'set_perceived_user_goal' tool to record your perception
    4. Present the perceived user goal to the user for confirmation
    5. If the user agrees, use the 'approve_perceived_user_goal' tool to approve the user goal. This will save the goal in state under the 'approved_user_goal' key.
"""

# Combine all instruction components
complete_agent_instruction = f"""
{agent_role_and_goal}
{agent_conversational_hints}
{agent_output_definition}
{agent_chain_of_thought_directions}
"""


# ============================================================================
# Tool Definitions
# ============================================================================

def set_perceived_user_goal(kind_of_graph: str, graph_description: str, tool_context: ToolContext):
    """
    Sets the perceived user's goal, including the kind of graph and its description.
    
    Args:
        kind_of_graph: 2-3 word definition of the kind of graph, for example "recent US patents"
        graph_description: a single paragraph description of the graph, summarizing the user's intent
        tool_context: ADK ToolContext containing state and other context
    """
    user_goal_data = {
        "kind_of_graph": kind_of_graph, 
        "graph_description": graph_description
    }
    tool_context.state[PERCEIVED_USER_GOAL] = user_goal_data
    logger.info(f"Set perceived user goal: {user_goal_data}")
    return tool_success(PERCEIVED_USER_GOAL, user_goal_data)


def approve_perceived_user_goal(tool_context: ToolContext):
    """
    Upon approval from user, will record the perceived user goal as the approved user goal.
    
    Only call this tool if the user has explicitly approved the perceived user goal.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    """
    # Trust, but verify. 
    # Require that the perceived goal was set before approving it.
    if PERCEIVED_USER_GOAL not in tool_context.state:
        error_msg = "perceived_user_goal not set. Set perceived user goal first, or ask clarifying questions if you are unsure."
        logger.warning(error_msg)
        return tool_error(error_msg)
    
    tool_context.state[APPROVED_USER_GOAL] = tool_context.state[PERCEIVED_USER_GOAL]
    logger.info(f"Approved user goal: {tool_context.state[APPROVED_USER_GOAL]}")
    return tool_success(APPROVED_USER_GOAL, tool_context.state[APPROVED_USER_GOAL])


# List of tools for the agent
user_intent_agent_tools = [set_perceived_user_goal, approve_perceived_user_goal]


# ============================================================================
# Agent Definition
# ============================================================================

user_intent_agent = Agent(
    name="user_intent_agent_v1",  # a unique, versioned name
    model=llm,  # Gemini model defined earlier
    description="Helps the user ideate on a knowledge graph use case.",  # used for delegation
    instruction=complete_agent_instruction,  # the complete instructions
    tools=user_intent_agent_tools,  # the list of tools
)

logger.info(f"Created agent: {user_intent_agent.name}")

