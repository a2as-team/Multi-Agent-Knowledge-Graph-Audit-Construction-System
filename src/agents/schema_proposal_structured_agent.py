"""
Schema Proposal Agent (Structured) - Proposes knowledge graph schema from CSV files.

This agent uses a "critic pattern" with multiple agents:
1. Schema Proposal Agent - Proposes the schema
2. Schema Critic Agent - Critiques the proposal
3. CheckStatusAndEscalate - Checks feedback and escalates if needed

The agents work in a refinement loop until the schema is approved.
"""
import warnings
import logging
from typing import Dict, Any, AsyncGenerator, ClassVar

from google.adk.agents import Agent, LlmAgent, LoopAgent, BaseAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal, get_approved_files
from src.tools.file_tools import sample_file, search_file
from src.tools.schema_proposal_tools import (
    propose_node_construction,
    propose_relationship_construction,
    remove_node_construction,
    remove_relationship_construction,
    get_proposed_construction_plan,
    approve_proposed_construction_plan
)

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
# Schema Proposal Agent Instructions
# ============================================================================

proposal_agent_role_and_goal = """
    You are an expert at knowledge graph modeling with property graphs. Propose an appropriate
    schema by specifying construction rules which transform approved files into nodes or relationships.
    The resulting schema should describe a knowledge graph based on the user goal.
    
    Consider feedback if it is available: 
    <feedback>
    {feedback}
    </feedback> 
"""

proposal_agent_hints = """
    Every file in the approved files list will become either a node or a relationship.
    Determining whether a file likely represents a node or a relationship is based
    on a hint from the filename (is it a single thing or two things) and the
    identifiers found within the file.

    Because unique identifiers are so important for determining the structure of the graph,
    always verify the existence of suspected unique identifier columns using the 'search_file' tool.
    
    IMPORTANT: If you find duplicate values in the data, this indicates a data quality issue,
    NOT a schema design problem. The column is still the unique identifier - duplicates will
    be handled during data import/cleaning. Do NOT remove node constructions because of duplicate
    data values. Focus on identifying the INTENDED unique identifier column (usually ends with _id).

    IMPORTANT: User feedback takes precedence:
    - If the user explicitly requests to remove a relationship or node (e.g., "remove X", "we don't need Y", "delete Z"), respect that request
    - Do NOT re-propose constructions that the user has explicitly asked to remove
    - User modifications override the "all files must be used" rule
    - If a user says "remove X" or "we don't need Y", do not add it back in subsequent iterations
    - Once a user requests removal, that construction should remain removed

    General guidance for identifying a node or a relationship:
    - If the file name is singular and has only 1 unique identifier column (typically ending in _id), it is likely a node
    - If the file name is a combination of two things, it is likely a full relationship
    - If the file name sounds like a node, but there are multiple unique identifiers, that is likely a node with reference relationships

    Design rules for nodes:
    - Nodes will have unique identifier columns (typically ending in _id like artist_id, artwork_id).
    - The presence of duplicate values in the data does NOT mean the column isn't a unique identifier.
    - Nodes _may_ have identifiers that are used as reference relationships.

    Design rules for relationships:
    - Relationships appear in two ways: full relationships and reference relationships.

    Full relationships:
    - Full relationships appear in dedicated relationship files, often having a filename that references two entities
    - Full relationships typically have references to a source and destination node.
    - Full relationships _do not have_ unique identifiers, but instead have references to the primary keys of the source and destination nodes.
    - The absence of a single, unique identifier is a strong indicator that a file is a full relationship.
    
    Reference relationships:
    - Reference relationships appear as foreign key references in node files
    - Reference relationship foreign key column names often hint at the destination node and relationship type
    - References may be hierarchical container relationships, with terminology revealing parent-child, "has", "contains", membership, or similar relationship
    - References may be peer relationships, that is often a self-reference to a similar class of nodes. For example, "knows" or "see also"

    The resulting schema should be a connected graph, with no isolated components.
"""

proposal_agent_chain_of_thought_directions = """
    AVAILABLE TOOLS (use these exact names - no other functions exist):
    - get_approved_user_goal: Get the approved user goal from session state
    - get_approved_files: Get the list of approved files from session state
    - get_proposed_construction_plan: Get the current proposed construction plan
    - sample_file: Sample rows from a file to see its structure
    - search_file: Search for a column name or value in a file
    - propose_node_construction: Propose a node construction (NOT "propose_construction_schema" - that doesn't exist)
    - propose_relationship_construction: Propose a relationship construction
    - remove_node_construction: Remove a node construction from the plan
    - remove_relationship_construction: Remove a relationship construction from the plan
    - approve_proposed_construction_plan: Approve the proposed construction plan

    Prepare for the task:
    - get the user goal using the 'get_approved_user_goal' tool
    - get the list of approved files using the 'get_approved_files' tool
    - get the current construction plan using the 'get_proposed_construction_plan' tool

    Think carefully, using tools to perform actions and reconsidering your actions when a tool returns an error:
    1. For each approved file, consider whether it represents a node or relationship. Check the content for potential unique identifiers using the 'sample_file' tool.
    2. For each identifier column (typically ending in _id), verify that it exists using the 'search_file' tool. Note: Duplicate values in data are data quality issues, not schema problems. The column is still the unique identifier.
    3. Use the node vs relationship guidance for deciding whether the file represents a node or a relationship.
    4. IMPORTANT: Propose ALL node and relationship constructions FIRST before removing anything. Complete the full schema proposal.
    5. For a node file, propose a node construction using the 'propose_node_construction' tool. 
    6. If the node contains a reference relationship, use the 'propose_relationship_construction' tool to propose a relationship construction. 
    7. For a relationship file, propose a relationship construction using the 'propose_relationship_construction' tool
    8. If the user explicitly requests to remove a relationship or node (e.g., "remove X", "we don't need Y", "delete Z", "remove the X relationship"), respect that request immediately using 'remove_node_construction' or 'remove_relationship_construction' tools. Do NOT re-propose constructions that the user has explicitly asked to remove.
    9. Only after proposing the complete schema, if the critic provides feedback, use 'remove_node_construction' or 'remove_relationship_construction' tools to refine.
    10. When you are done with construction proposals, use the 'get_proposed_construction_plan' tool to present the plan to the user
    11. CRITICAL: Before finishing, ensure you have proposed constructions for ALL approved files, UNLESS the user has explicitly requested to remove specific constructions. User modifications take precedence over the "all files must be used" rule.
    12. If the user explicitly approves the schema (e.g., "yes, approve", "approve the schema", "looks good", "approve", "yes approve"), use the 'approve_proposed_construction_plan' tool to finalize it.
    13. After approval, confirm to the user that the schema has been approved and is ready for use.
    
    CRITICAL: Only use the exact tool names listed above. Do NOT invent function names like "propose_construction_schema" - that function does not exist.
"""

# Combine all instruction components
proposal_agent_instruction = f"""
{proposal_agent_role_and_goal}
{proposal_agent_hints}
{proposal_agent_chain_of_thought_directions}
"""


# ============================================================================
# Schema Critic Agent Instructions
# ============================================================================

critic_agent_role_and_goal = """
    You are an expert at knowledge graph modeling with property graphs. 
    Criticize the proposed schema for relevance to the user goal and approved files.
"""

critic_agent_hints = """
    Criticize the proposed schema for relevance and correctness:
    
    IMPORTANT: Focus on SCHEMA DESIGN, not data quality:
    - Duplicate values in data are DATA QUALITY ISSUES, not schema problems
    - The presence of duplicate values does NOT invalidate a unique identifier column
    - The column is still the correct unique identifier even if duplicates exist in the data
    - Data quality issues will be handled during data import/cleaning, not schema design
    
    Schema validation criteria:
    - Does each node have a unique identifier column (typically ending in _id)? The column name is what matters, not whether values are unique in the data.
    - Are composite identifiers being used? (Composite identifiers are not acceptable - use single column identifiers)
    - Could any nodes be relationships instead? Check that the unique identifier column is not actually a foreign key reference to another node.
    - Is every node in the schema connected? What relationships could be missing? Every node should connect to at least one other node.
    - Are hierarchical container relationships missing? 
    - Are any relationships redundant? A relationship between two nodes is redundant if it is semantically equivalent to or the inverse of another relationship between those two nodes.
    - Can you manually trace through the source data to find the necessary information for answering a hypothetical question based on the user goal?
    - Are all approved files represented in the schema? Every file should be used.
"""

critic_agent_chain_of_thought_directions = """
    Prepare for the task:
    - get the user goal using the 'get_approved_user_goal' tool
    - get the list of approved files using the 'get_approved_files' tool
    - get the construction plan using the 'get_proposed_construction_plan' tool
    - use the 'sample_file' and 'search_file' tools to validate the schema design

    Think carefully, using tools to perform actions and reconsidering your actions when a tool returns an error:
    1. Analyze each construction rule in the proposed construction plan.
    2. Validate the SCHEMA STRUCTURE (not data quality):
       - Check that unique identifier columns exist (column names ending in _id)
       - Verify that the column is intended as a unique identifier (not a foreign key)
       - DO NOT reject schemas because of duplicate values in the data - this is a data quality issue, not a schema problem
    3. Check schema completeness:
       - Are all approved files represented?
       - Is the graph connected (no isolated nodes)?
       - Are relationships correctly identified (full vs reference)?
    4. If the schema structure is correct and complete, respond with a one word reply: 'valid'.
    5. If the schema has STRUCTURAL problems (not data quality issues), respond with 'retry' and provide feedback as a concise bullet list of problems.
"""

# Combine all instruction components
critic_agent_instruction = f"""
{critic_agent_role_and_goal}
{critic_agent_hints}
{critic_agent_chain_of_thought_directions}
"""


# ============================================================================
# Tool Lists
# ============================================================================

# Tools for the schema proposal agent
schema_proposal_agent_tools = [
    get_approved_user_goal,
    get_approved_files,
    get_proposed_construction_plan,
    sample_file,
    search_file,
    propose_node_construction,
    propose_relationship_construction,
    remove_node_construction,
    remove_relationship_construction,
    approve_proposed_construction_plan
]

# Tools for the schema critic agent (read-only, cannot make changes)
schema_critic_agent_tools = [
    get_approved_user_goal,
    get_approved_files,
    get_proposed_construction_plan,
    sample_file,
    search_file
]


# ============================================================================
# Agent Definitions
# ============================================================================

schema_proposal_agent = LlmAgent(
    name="schema_proposal_agent_v1",
    description="Proposes a knowledge graph schema based on the user goal and approved file list",
    model=llm,
    instruction=proposal_agent_instruction,
    tools=schema_proposal_agent_tools
)

schema_critic_agent = LlmAgent(
    name="schema_critic_agent_v1",
    description="Criticizes the proposed schema for relevance to the user goal and approved files.",
    model=llm,
    instruction=critic_agent_instruction,
    tools=schema_critic_agent_tools,
    output_key="feedback"  # The result of calling the critic is placed in the 'feedback' key
)


# ============================================================================
# CheckStatusAndEscalate Agent
# ============================================================================

class CheckStatusAndEscalate(BaseAgent):
    """
    Custom agent that checks the critic feedback status.
    - If "valid": exits the loop and presents to user
    - If "retry": continues the loop with feedback
    - If max iterations reached: escalates to user
    """
    
    # Class variable for max iterations (ClassVar to avoid Pydantic field validation)
    MAX_ITERATIONS: ClassVar[int] = 3
    
    def __init__(self, name: str = "check_status_and_escalate"):
        super().__init__(name=name)
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Check feedback status and decide whether to continue loop."""
        
        # Get current iteration count
        iteration = ctx.session.state.get("schema_refinement_iteration", 0)
        iteration += 1
        ctx.session.state["schema_refinement_iteration"] = iteration
        
        logger.info(f"📊 Schema refinement iteration: {iteration}/{self.MAX_ITERATIONS}")
        
        # Get critic feedback (stored via output_key="feedback")
        feedback = ctx.session.state.get("feedback", "valid")
        feedback_str = str(feedback).strip().lower()
        
        # Log the feedback for debugging
        logger.info(f"💬 Critic feedback: {feedback_str[:100]}...")
        
        # Check if feedback indicates valid
        is_valid = feedback_str == "valid"
        
        if is_valid:
            # Schema is valid - exit loop with friendly message
            logger.info("✅ Schema validated by critic - exiting refinement loop")
            
            # Get proposed schema count for the message
            proposed_plan = ctx.session.state.get("proposed_construction_plan", {})
            construction_count = len(proposed_plan)
            
            # Create success message
            success_message = (
                f"✅ **Schema Proposal Complete!**\n\n"
                f"I've successfully proposed and validated **{construction_count} schema constructions** from the CSV files.\n\n"
                f"**What's been done:**\n"
                f"- ✅ Analyzed all approved CSV files\n"
                f"- ✅ Identified nodes and relationships based on data structure\n"
                f"- ✅ Verified unique identifiers and foreign keys\n"
                f"- ✅ Validated by the critic agent\n\n"
                f"**Next steps:**\n"
                f"- Review the proposed schema above\n"
                f"- If you approve, say 'yes' or 'approve the schema'\n"
                f"- If you want changes, let me know what to adjust\n\n"
                f"Ready for your review! 🎯"
            )
            
            # Yield message before escalating
            response_content = types.Content(
                role='model',
                parts=[types.Part(text=success_message)]
            )
            yield Event(author=self.name, content=response_content)
            
            # Now escalate to exit loop
            yield Event(author=self.name, actions=EventActions(escalate=True))
            
        elif iteration >= self.MAX_ITERATIONS:
            # Max iterations reached - escalate with message
            logger.warning(f"⚠️ Max iterations ({self.MAX_ITERATIONS}) reached - escalating to user")
            
            # Create warning message
            warning_message = (
                f"⚠️ **Maximum Iterations Reached**\n\n"
                f"After {self.MAX_ITERATIONS} refinement iterations, there are still some issues:\n\n"
                f"{str(feedback)}\n\n"
                f"💡 **What this means:**\n"
                f"The agent has done its best to refine the schema, but some validation issues remain. "
                f"You can:\n"
                f"- Review the current proposals and manually approve if they're acceptable\n"
                f"- Provide specific feedback to guide further refinement\n"
                f"- Ask questions about the proposed schema\n\n"
                f"The proposals are available for your review."
            )
            
            # Store escalation message in state for UI
            ctx.session.state["escalation_message"] = warning_message
            
            # Yield message before escalating
            response_content = types.Content(
                role='model',
                parts=[types.Part(text=warning_message)]
            )
            yield Event(author=self.name, content=response_content)
            
            # Escalate to exit loop
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            # Continue loop - pass feedback to proposal agent
            logger.info(f"🔄 Critic requested retry (iteration {iteration}/{self.MAX_ITERATIONS})")
            logger.info(f"📝 Feedback will be automatically injected into proposal agent via {{feedback}} template")
            # Do not escalate - loop will continue
            yield Event(author=self.name, actions=EventActions(escalate=False))


# ============================================================================
# Schema Refinement Loop
# ============================================================================

schema_refinement_loop = LoopAgent(
    name="schema_refinement_loop",
    description="Analyzes approved files to propose a schema based on user intent and feedback",
    max_iterations=3,  # Allow up to 3 iterations for refinement
    sub_agents=[
        schema_proposal_agent,
        schema_critic_agent,
        CheckStatusAndEscalate(name="StopChecker")
    ]
)

logger.info("Created Schema Proposal Agent (Structured) with refinement loop")

