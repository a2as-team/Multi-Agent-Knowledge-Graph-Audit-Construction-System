"""
Fact Extraction Agent - Proposes fact types (relationship triples) from unstructured data.

This agent analyzes markdown files and proposes fact types as (subject, predicate, object) triples.
It uses the approved entity types from the NER Agent and looks for relationships between them.

Fact types are templates for relationships, not actual instances.
For example: (Artist, founded, ArtMovement) not (Picasso, founded, Cubism).
"""
import warnings
import logging
from typing import Dict, Any

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from src.utils.config import DEFAULT_MODEL
from src.utils.constants import (
    APPROVED_ENTITIES,
    PROPOSED_FACTS,
    APPROVED_FACTS
)
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal, get_approved_files
from src.tools.file_tools import sample_file
from src.tools.ner_tools import get_approved_entities
from src.tools.fact_extraction_tools import (
    add_proposed_fact,
    get_proposed_facts,
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
# Fact Extraction Agent Instructions
# ============================================================================

fact_agent_role_and_goal = """
You are a top-tier algorithm designed for analyzing text files and proposing
the type of facts that could be extracted from text that would be relevant 
for a user's goal.
"""

fact_agent_hints = """
Do not propose specific individual facts, but instead propose the general type 
of facts that would be relevant for the user's goal. 
For example, do not propose "Picasso founded Cubism" but the general type of fact "(Artist, founded, ArtMovement)".

Facts are triplets of (subject, predicate, object) where the subject and object are
approved entity types, and the proposed predicate provides information about
how they are related. For example, a fact type could be (Artist, founded, ArtMovement).

Design rules for facts:
- only use approved entity types as subjects or objects. Do not propose new types of entities
- the proposed predicate should describe the relationship between the approved subject and object
- the predicate should optimize for information that is relevant to the user's goal
- the predicate must appear in the source text. Do not guess or invent relationships.
- use the 'add_proposed_fact' tool to record each proposed fact type
- you may propose multiple fact types - call 'add_proposed_fact' once for each fact type

Important considerations:
- Focus on relationships that support the user's goal (e.g., provenance tracking, historical context)
- Prefer relationships that connect well-known entities (from graph schema) to discovered entities (from text)
- Look for relationships that would enrich the existing graph with contextual information
"""

fact_agent_chain_of_thought_directions = """
Prepare for the task:
- use the 'get_approved_user_goal' tool to get the user goal
- use the 'get_approved_files' tool to get the list of approved markdown files
- use the 'get_approved_entities' tool to get the list of approved entity types

Think step by step:
1. Review the approved entity types to understand what subjects and objects are available
2. Sample some of the approved files using the 'sample_file' tool to understand the content
3. Consider how subjects and objects are related in the text (look for verbs and relationship phrases)
4. Call the 'add_proposed_fact' tool for each type of fact you propose
5. Use the 'get_proposed_facts' tool to retrieve all the proposed facts
6. Present the proposed types of facts to the user, along with an explanation of why each is relevant
7. If the user approves, use the 'approve_proposed_facts' tool to finalize the fact types
8. If the user provides feedback, iterate on the proposal
"""

# Combine all instruction components
fact_agent_instruction = f"""
{fact_agent_role_and_goal}
{fact_agent_hints}
{fact_agent_chain_of_thought_directions}
"""


# ============================================================================
# Tool List
# ============================================================================

fact_extraction_agent_tools = [
    get_approved_user_goal,     # From schema_tools
    get_approved_files,          # From schema_tools
    get_approved_entities,       # From ner_tools
    sample_file,                 # From file_tools
    add_proposed_fact,           # From fact_extraction_tools
    get_proposed_facts,          # From fact_extraction_tools
    approve_proposed_facts       # From fact_extraction_tools
]


# ============================================================================
# Agent Definition
# ============================================================================

fact_extraction_agent = Agent(
    name="fact_extraction_agent_v1",
    model=llm,
    description="Proposes the kind of relevant facts that could be extracted from markdown files.",
    instruction=fact_agent_instruction,
    tools=fact_extraction_agent_tools,
)

logger.info(f"Created agent: {fact_extraction_agent.name}")

