"""
Fact Extraction Agent - Proposes fact types (relationship triples) from unstructured data.

This agent uses a "critic pattern" with multiple agents:
1. Fact Proposal Agent - Proposes fact types from markdown files
2. Fact Critic Agent - Validates and critiques the proposals
3. CheckStatusAndEscalate - Checks feedback and escalates if needed

The agents work in a refinement loop until fact types are approved.
"""
import warnings
import logging
from typing import Dict, Any, AsyncGenerator, ClassVar

from google.adk.agents import Agent, LlmAgent, LoopAgent, BaseAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal, get_approved_files
from src.tools.file_tools import sample_file
from src.tools.ner_tools import get_approved_entities
from src.tools.fact_extraction_tools import (
    get_well_known_relationships,
    add_proposed_fact,
    add_proposed_facts_batch,
    remove_proposed_fact,
    get_proposed_facts,
    set_critic_feedback,
    get_critic_feedback,
    approve_proposed_facts
)

# Ignore warnings
warnings.filterwarnings("ignore")

# Set logging level
logging.basicConfig(level=logging.CRITICAL)


# Initialize LLM
try:
    llm = LiteLlm(model=DEFAULT_MODEL)
    logger.info(f"Initialized LLM with model: {DEFAULT_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    raise


# ============================================================================
# Fact Proposal Agent Instructions
# ============================================================================

fact_proposal_agent_role_and_goal = """
You are a top-tier algorithm designed for analyzing text files and proposing
the type of facts that could be extracted from text that would be relevant 
for a user's goal.

Your task is to propose a clean, deduplicated set of fact types (relationship triples)
that represent relationships found in the text.

**CRITICAL: If this is a refinement iteration (check session state for 'critic_feedback'):**
1. FIRST: Use 'get_critic_feedback' tool to read the structured feedback
2. CHECK: If status is "retry", there are issues that MUST be addressed
3. READ: The 'issues' list contains specific problems to fix
4. ACT: Use 'remove_proposed_fact' to remove problematic fact types by their predicate label
5. VERIFY: After removing, check 'get_proposed_facts' to confirm the issue is resolved
6. DO NOT re-propose the same problematic facts that were just removed

If no critic feedback exists yet, proceed with initial proposal.
"""

fact_proposal_agent_hints = """
Do not propose specific individual facts, but instead propose the general type 
of facts that would be relevant for the user's goal. 
For example, do not propose "John Smith works at Acme Corp" but the general type of fact "(Person, works_at, Organization)".

Facts are triplets of (subject, predicate, object) where the subject and object are
approved entity types, and the proposed predicate provides information about
how they are related. For example, a fact type could be (Person, employed_by, Organization).

Design rules for facts:
- only use approved entity types as subjects or objects. Do not propose new types of entities
- the proposed predicate should describe the relationship between the approved subject and object
- the predicate should optimize for information that is relevant to the user's goal
- the predicate must be grounded in the source text. Do not guess or invent relationships.

**Avoid redundancy with existing structured data relationships (CRITICAL):**
- Use the 'get_well_known_relationships' tool to see what relationships already exist from structured data
- Do NOT propose fact types that duplicate or overlap with existing relationships
- Focus on NEW relationships that only appear in unstructured text and add value to the graph
- Example: If structured data already has (Artwork, CREATED_BY, Artist), do NOT propose:
  - (Artist, created, Artwork) ← inverse of existing
  - (Artwork, created_by, Artist) ← duplicate with different case
  - (Artwork, made_by, Artist) ← synonym of existing
- Look for relationships that complement existing data with new information types

**Predicate consolidation within each file:**
- Consolidate similar predicates into ONE canonical form PER FILE
  - Example: if text uses "displayed in", "shown in", "exhibited in" → choose ONE canonical form like "displayed_at"
  - Avoid creating multiple relationship types that represent the same semantic meaning
- Use standard relationship naming conventions:
  - lowercase_with_underscores for predicates
  - Use clear, concise verbs or prepositions
  - Prefer active voice: "created_by", "located_at", "member_of"
- Within each file, avoid inverse relationships (choose ONE direction)

**CRITICAL: Use batch tool calls to avoid rate limits**
- ALWAYS use 'add_proposed_facts_batch' to add multiple facts at once (PREFERRED METHOD)
- This reduces API calls by 70-80% and prevents rate limit errors
- After sampling each file, add ALL facts from that file in a single batch call
- Only use 'add_proposed_fact' if you need to add a single fact later
- Use 'remove_proposed_fact' to remove specific facts when addressing critic feedback

Format for batch tool:
- Pass a list of dicts, each with: approved_subject_label, proposed_predicate_label, approved_object_label
- Example: [{"approved_subject_label": "Person", "proposed_predicate_label": "employed_by", "approved_object_label": "Organization"}]

Important considerations:
- Focus on relationships that directly support the user's stated goal
- Prefer relationships that connect well-known entities (from existing graph schema) to discovered entities (from text)
- Look for relationships that would enrich the graph with meaningful contextual information
- The critic will review your proposals, so focus on getting good coverage first
- Cross-file consolidation will be handled by the critic
"""

fact_proposal_agent_chain_of_thought_directions = """
**STEP 0: CHECK FOR CRITIC FEEDBACK (DO THIS FIRST!)**
- BEFORE doing anything else, call 'get_critic_feedback' to check if there's feedback from a previous iteration
- If the feedback status is "retry" and there are issues:
  a) READ each issue carefully
  b) For each problematic fact mentioned, call 'remove_proposed_fact' with the predicate_label
  c) VERIFY removal by calling 'get_proposed_facts' to confirm the fact is gone
  d) After addressing ALL issues, call 'get_proposed_facts' again to see what remains
  e) If the critic asked you to remove a fact, DO NOT re-propose it
- If there's no feedback or status is "valid", proceed with initial proposal

**Prepare for the task:**
- use the 'get_approved_user_goal' tool to get the user goal
- use the 'get_approved_files' tool to get the list of approved markdown files
- use the 'get_approved_entities' tool to get the list of approved entity types
- use the 'get_well_known_relationships' tool to get existing relationships from structured data

**Think step by step:**
1. Review the approved entity types to understand what subjects and objects are available
2. Review the existing relationships from structured data to know what to AVOID proposing
3. Check if this is a refinement iteration (see STEP 0 above)
4. Sample ONE markdown file using the 'sample_file' tool
5. Identify ALL relevant fact types from that file, noting any synonym predicates
6. Filter out any facts that duplicate or overlap with existing relationships from structured data
7. Consolidate similar predicates into canonical forms within this file (e.g., "shown in" + "displayed in" → "displayed_at")
8. Check for inverse relationships within this file and choose ONE direction to represent each relationship
9. Call 'add_proposed_facts_batch' with ALL deduplicated, non-redundant facts from that file in ONE batch call
10. Repeat steps 4-9 for each remaining file (sample, identify, filter, consolidate, batch add)
11. After processing all files, you're done - the critic will review for cross-file issues

**CRITICAL**: 
- ALWAYS check for critic feedback FIRST using 'get_critic_feedback' before doing anything
- If critic identified issues, you MUST address them by removing the problematic facts
- Always check existing relationships from structured data FIRST using 'get_well_known_relationships'
- Do NOT propose fact types that duplicate existing structured relationships
- Always use 'add_proposed_facts_batch' instead of calling 'add_proposed_fact' multiple times
- Always consolidate similar predicates WITHIN each file before adding them
- The critic will handle cross-file consolidation - focus on per-file quality
"""

# Combine all instruction components
fact_proposal_agent_instruction = f"""
{fact_proposal_agent_role_and_goal}
{fact_proposal_agent_hints}
{fact_proposal_agent_chain_of_thought_directions}
"""


# ============================================================================
# Fact Critic Agent Instructions
# ============================================================================

fact_critic_agent_role_and_goal = """
You are a critical reviewer of proposed fact types for knowledge graph construction.

Your task is to review the proposed fact types and check for issues that would
reduce the quality or usability of the knowledge graph.
"""

fact_critic_agent_hints = """
You are looking for systematic issues with the proposed fact types, not subjective preferences.

**Validation Checklist** (check ALL of these):

1. **No duplicate fact types** (same triple proposed multiple times)
   - Check: Are there exact duplicates of (subject, predicate, object) across the list?
   - Example BAD: (EntityA, predicate, EntityB) appears twice with different predicate keys

2. **No inverse relationships** (both directions of same relationship)
   - Check: Are there pairs like (A, rel, B) and (B, inverse_rel, A)?
   - Example BAD: (EntityA, acquired_by, EntityB) AND (EntityA, acquired_from, EntityB)
   - These are inverses - choose ONE direction

3. **No synonym predicates** (different names, same semantic meaning)
   - Check: Do multiple predicates mean essentially the same thing?
   - Example BAD: "predicate1" and "predicate2" if both mean EntityA→EntityB with same semantics
   - Example BAD: "lent_to" and "loaned_to" are synonyms

4. **No semantic redundancy with existing structured relationships**
   - Check: Do proposed facts semantically duplicate existing relationships?
   - Use 'get_well_known_relationships' to review existing relationships
   - Example BAD: Proposing "new_location_rel" when "LOCATED_AT" already covers location
   - Example GOOD: Proposing "previously_related_to" (temporal distinction from current relationship)

5. **All subjects and objects are approved entity types**
   - Check: Are all entity labels in the approved entities list?
   - Use 'get_approved_entities' to verify

6. **Predicates are appropriately consolidated**
   - Check: Are there similar predicates that should be merged?
   - Example: "owns", "is_owner_of", "owned_by" → consolidate to ONE

7. **Fact types support the user's stated goal**
   - Check: Is each fact type relevant to achieving the user's objective?
   - Use 'get_approved_user_goal' to review the goal

8. **No duplicate subject-object pairs** (unless semantically distinct)
   - Check: Do multiple predicates connect the same entity types?
   - Example MAYBE BAD: (EntityA, predicate1, EntityB) AND (EntityA, predicate2, EntityB)
   - Question: Are these truly different relationships, or should they be consolidated?
   - If distinct: Document WHY (e.g., temporal difference, ownership vs association, current vs historical)
   - If redundant: Choose the most general/accurate predicate

9. **All approved entity types are used in at least one relationship**
   - Check: Is every approved entity type used as a subject or object in either:
     a) Proposed fact types (unstructured), OR
     b) Existing structured relationships (construction plan)
   - Use 'get_approved_entities' to get all entity types
   - Use 'get_well_known_relationships' to check structured usage
   - Use 'get_proposed_facts' to check unstructured usage
   - If NOT used: The entity type will create orphaned/isolated nodes in the graph
   - Action: Either propose a fact using this entity, or flag for user review
   - Example BAD: Entity type "EntityX" approved but never appears in any relationship
   - Exception: Some entity types might be standalone reference nodes (rare - must be justified)

**Be specific in your feedback:**
- Don't just say "there are duplicates" - list which specific fact types are duplicated
- Don't just say "consolidate predicates" - specify which predicates should be merged
- For orphaned entities, suggest specific relationships that could connect them
- Provide actionable guidance that the proposal agent can follow
"""

fact_critic_agent_chain_of_thought_directions = """
**YOUR ROLE: You are a REVIEWER ONLY. You provide feedback but DO NOT modify facts.**
- You have access to read-only tools: get_proposed_facts, get_well_known_relationships, get_approved_entities, get_approved_user_goal
- Your ONLY action tool is: set_critic_feedback (to provide structured feedback)
- You do NOT have tools to add or remove facts - that's the proposal agent's job
- DO NOT try to call 'remove_proposed_fact' or 'add_proposed_fact' - you don't have those tools

Think step by step:
1. Use 'get_proposed_facts' to retrieve the proposed fact types
2. Use 'get_well_known_relationships' to get existing relationships from structured data
3. Use 'get_approved_entities' to get approved entity types
4. Use 'get_approved_user_goal' to understand the user's objective
5. Run through each validation check systematically:
   - Check for duplicate fact types (same subject, predicate, object)
   - Check for inverse relationships (A→B and A←B)
   - Check for synonym predicates (different names, same meaning)
   - Check for semantic overlap with existing relationships
   - Check all entities are approved
   - Check predicates are well-consolidated
   - Check relevance to user goal
   - Check for duplicate subject-object pairs (unless semantically distinct)
   - Check all approved entity types are used in at least one relationship
6. If ALL checks pass:
   - Call 'set_critic_feedback' ONCE with status="valid" and empty issues list
   - DO NOT call any other tools after this
7. If ANY check fails:
   - Call 'set_critic_feedback' ONCE with status="retry" and detailed issues list
   - Be specific: list exact fact types (including the predicate_label), explain why they're problematic
   - DO NOT call any other tools after this
   
**CRITICAL**: After calling 'set_critic_feedback', you are DONE. Do not call any other tools.

**Output format for issues (ALWAYS include the predicate_label in single quotes):**
Each issue should be a clear, actionable statement with the predicate_label clearly specified:
- "Remove predicate 'predicate_label': (EntityA, predicate_label, EntityB) is a duplicate"
- "Remove predicate 'acquired_from': (EntityA, acquired_by, EntityB) and (EntityA, acquired_from, EntityB) are inverses - keep 'acquired_by'"
- "Remove predicate 'predicate2': 'predicate1' and 'predicate2' are synonyms - keep 'predicate1'"
- "Remove predicate 'new_predicate': overlaps with existing 'EXISTING_RELATIONSHIP'"
- "Remove predicate 'predicate2': (EntityA, predicate1, EntityB) and (EntityA, predicate2, EntityB) connect same entities - keep 'predicate1'"
- "Orphaned entity 'EntityX': not used in any relationship. Proposal agent should add a fact using EntityX"

**CRITICAL**: Always specify which predicate_label to remove or keep. The proposal agent needs the exact predicate_label string.
"""

# Combine all instruction components
fact_critic_agent_instruction = f"""
{fact_critic_agent_role_and_goal}
{fact_critic_agent_hints}
{fact_critic_agent_chain_of_thought_directions}
"""


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
    
    def __init__(self):
        super().__init__(name="check_status_and_escalate")
    
    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Check feedback status and decide whether to continue loop."""
        
        # Get current iteration count
        iteration = ctx.session.state.get("fact_refinement_iteration", 0)
        iteration += 1
        ctx.session.state["fact_refinement_iteration"] = iteration
        
        logger.info(f"Fact refinement iteration: {iteration}/{self.MAX_ITERATIONS}")
        
        # Get critic feedback (stored via output_key="feedback")
        feedback = ctx.session.state.get("feedback", "")
        
        # Also check structured feedback from tool (for UI display)
        critic_feedback = ctx.session.state.get("critic_feedback", {})
        status = critic_feedback.get("status", "")
        issues = critic_feedback.get("issues", [])
        
        # Log the feedback for debugging
        logger.info(f"📊 Critic status: {status}")
        if issues:
            logger.info(f"📋 Critic issues ({len(issues)}): {issues[0][:100] if issues else 'None'}...")
        
        # Check if feedback indicates valid (either via tool status or feedback text)
        is_valid = (status == "valid") or ("valid" in str(feedback).lower() and "invalid" not in str(feedback).lower())
        
        if is_valid:
            # Facts are valid - exit loop
            logger.info("✅ Fact types validated by critic - exiting refinement loop")
            yield Event(author=self.name, actions=EventActions(escalate=True))
        elif iteration >= self.MAX_ITERATIONS:
            # Max iterations reached - escalate with message
            logger.warning(f"⚠️ Max iterations ({self.MAX_ITERATIONS}) reached - escalating to user")
            
            if issues:
                issue_text = "\n".join(f"- {issue}" for issue in issues)
            else:
                issue_text = str(feedback) or "Unknown issues"
            
            # Store escalation message in state for UI
            ctx.session.state["escalation_message"] = (
                f"⚠️ After {self.MAX_ITERATIONS} refinement iterations, there are still {len(issues)} issue(s):\n\n" +
                issue_text +
                f"\n\n💡 The agent has done its best. Please review and manually address remaining issues."
            )
            
            # Escalate to exit loop
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            # Continue loop - pass feedback to proposal agent
            logger.info(f"🔄 Critic requested retry (iteration {iteration}/{self.MAX_ITERATIONS})")
            logger.info(f"📝 Passing {len(issues)} issue(s) to proposal agent for refinement")
            # Do not escalate - loop will continue
            yield Event(author=self.name, actions=EventActions(escalate=False))


# ============================================================================
# Tool Lists
# ============================================================================

fact_proposal_agent_tools = [
    get_approved_user_goal,
    get_approved_files,
    get_approved_entities,
    get_well_known_relationships,
    sample_file,
    add_proposed_fact,
    add_proposed_facts_batch,
    remove_proposed_fact,
    get_proposed_facts,
    get_critic_feedback  # To read feedback and address issues in refinement iterations
]

fact_critic_agent_tools = [
    get_approved_user_goal,
    get_approved_entities,
    get_well_known_relationships,
    get_proposed_facts,
    set_critic_feedback
]


# ============================================================================
# Agent Definitions
# ============================================================================

# Proposal Agent
fact_proposal_agent = LlmAgent(
    name="fact_proposal_agent_v1",
    model=llm,
    description="Proposes fact types (relationship triples) from markdown files.",
    instruction=fact_proposal_agent_instruction,
    tools=fact_proposal_agent_tools,
)

# Critic Agent
fact_critic_agent = LlmAgent(
    name="fact_critic_agent_v1",
    model=llm,
    description="Validates proposed fact types and provides structured feedback.",
    instruction=fact_critic_agent_instruction,
    tools=fact_critic_agent_tools,
    output_key="feedback"  # The result of calling the critic is placed in the 'feedback' key
)

# Check Status Agent
check_status_and_escalate = CheckStatusAndEscalate()

# Refinement Loop
fact_refinement_loop = LoopAgent(
    name="fact_refinement_loop",
    description="Analyzes markdown files to propose fact types based on user intent and feedback",
    max_iterations=3,  # Allow up to 3 iterations for refinement
    sub_agents=[
        fact_proposal_agent,
        fact_critic_agent,
        check_status_and_escalate
    ]
)

logger.info("Created fact extraction agents with critic pattern: fact_refinement_loop")

# Export the main loop agent (backward compatible interface)
fact_extraction_agent = fact_refinement_loop
