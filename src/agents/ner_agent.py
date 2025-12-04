"""
Named Entity Recognition (NER) Agent - Proposes entity types to extract from unstructured data.

This agent analyzes markdown files and proposes two types of entities:
1. Well-known entities: those that match existing node labels from the structured graph schema
2. Discovered entities: those that appear frequently in the text and support the user's goal

The agent works within a workflow where structured data has already been processed.
"""
import warnings
import logging
from typing import Dict, Any

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from src.utils.config import DEFAULT_MODEL
from src.utils.constants import (
    PROPOSED_ENTITIES,
    APPROVED_ENTITIES,
    APPROVED_CONSTRUCTION_PLAN
)
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal, get_approved_files
from src.tools.file_tools import sample_file
from src.tools.ner_tools import (
    get_well_known_types,
    set_proposed_entities,
    get_proposed_entities,
    approve_proposed_entities
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
# NER Agent Instructions
# ============================================================================

ner_agent_role_and_goal = """
You are a top-tier algorithm designed for analyzing text files and proposing
the kind of named entities that could be extracted which would be relevant 
for a user's goal.
"""

ner_agent_hints = """
Entities are people, places, things and qualities, but not quantities. 
Your goal is to propose a list of the type of entities, not the actual instances
of entities.

There are two general approaches to identifying types of entities:
- well-known entities: these closely correlate with approved node labels in an existing graph schema
- discovered entities: these may not exist in the graph schema, but appear consistently in the source text

Design rules for well-known entities:
- always use existing well-known entity types. For example, if there is a well-known type "Artist", and artists appear in the text, then propose "Artist" as the type of entity.
- prefer reusing existing entity types rather than creating new ones

Design rules for discovered entities:
- discovered entities are consistently mentioned in the text and are highly relevant to the user's goal
- always look for entities that would provide more depth or breadth to the existing graph
- for example, if the user goal mentions analyzing artwork provenance and the graph has "Artwork" nodes, look through the text to discover entities that are relevant like "Exhibition", "Collector", or "Art Movement"
- avoid quantitative types that may be better represented as a property on an existing entity or relationship.
- for example, do not propose "Price" as a type of entity. That is better represented as an additional property "price" on an "Artwork".
"""

ner_agent_chain_of_thought_directions = """
Prepare for the task:
- use the 'get_approved_user_goal' tool to get the user goal
- use the 'get_approved_files' tool to get the list of approved markdown files
- use the 'get_well_known_types' tool to get the approved node labels from the graph schema

Think step by step:
1. Sample some of the files using the 'sample_file' tool to understand the content
2. Consider what well-known entities (from the approved node labels) are mentioned in the text
3. Discover entities that are frequently mentioned in the text that support the user's goal
4. Use the 'set_proposed_entities' tool to save the list of well-known and discovered entity types
5. Use the 'get_proposed_entities' tool to retrieve the proposed entities and present them to the user for their approval
6. If the user approves, use the 'approve_proposed_entities' tool to finalize the entity types
7. If the user does not approve, consider their feedback and iterate on the proposal
"""

# Combine all instruction components
ner_agent_instruction = f"""
{ner_agent_role_and_goal}
{ner_agent_hints}
{ner_agent_chain_of_thought_directions}
"""


# ============================================================================
# Tool List
# ============================================================================

ner_agent_tools = [
    get_approved_user_goal,     # From schema_tools
    get_approved_files,          # From schema_tools
    sample_file,                 # From file_tools
    get_well_known_types,        # From ner_tools
    set_proposed_entities,       # From ner_tools
    get_proposed_entities,       # From ner_tools
    approve_proposed_entities    # From ner_tools
]


# ============================================================================
# Agent Definition
# ============================================================================

ner_agent = Agent(
    name="ner_agent_v1",
    model=llm,
    description="Proposes the kind of named entities that could be extracted from markdown files.",
    instruction=ner_agent_instruction,
    tools=ner_agent_tools,
)

logger.info(f"Created agent: {ner_agent.name}")

