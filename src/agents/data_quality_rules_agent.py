"""
Data Quality Rules Agent - Helps users define custom data quality rules.

This agent uses a conversational approach to help users define rules that will
be used to validate the knowledge graph after construction.
"""
import warnings
import logging

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from src.utils.config import DEFAULT_MODEL
from src.utils.logger import logger
from src.tools.schema_tools import get_approved_user_goal
from src.tools.schema_proposal_tools import get_proposed_construction_plan, get_approved_construction_plan
from src.tools.ner_tools import get_approved_entities
from src.tools.fact_extraction_tools import get_approved_facts
from src.tools.data_quality_rules_tools import (
    get_schema_context,
    add_quality_rule,
    remove_quality_rule,
    get_proposed_quality_rules,
    approve_quality_rules,
    get_approved_quality_rules
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
# Data Quality Rules Agent Instructions
# ============================================================================

agent_role_and_goal = """
You are a data quality expert who helps users define custom quality rules
for validating their knowledge graph.

Your task is to work with the user to define comprehensive data quality rules
that will be used to audit the knowledge graph after it's constructed.

You have access to:
- The user's goal
- The approved schema (construction plan)
- The approved entity types
- The approved fact types

Use this information to propose relevant quality rules and refine them based
on user feedback.
"""

agent_hints = """
**Understanding Quality Rules:**

Quality rules define what makes a "valid" or "high-quality" knowledge graph.
They are checked AFTER the graph is constructed to find issues.

**Rule Types:**

1. **required_relationship**: An entity must have a specific relationship
   - Example: Every Artwork must have a CREATED_BY relationship to an Artist
   - Parameters: entity_label, relationship_type, target_label

2. **temporal_constraint**: Date/time fields must follow logical order
   - Example: Artwork year must be >= Artist birth_year
   - Parameters: entity_label, field1, operator, field2, relationship (optional)

3. **cardinality_constraint**: Relationship must have specific cardinality
   - Example: Artwork should have exactly one creator (not multiple)
   - Parameters: entity_label, relationship_type, min_count, max_count

4. **orphan_detection**: Find nodes with no relationships
   - Example: Find Artists with no artworks and no bio information
   - Parameters: entity_label, exception_labels (optional)

5. **unresolved_entity**: Find entities in Subject graph without Domain correspondence
   - Example: Find Artists mentioned in text but not in database
   - Parameters: entity_label

6. **value_constraint**: Property value must meet certain criteria
   - Example: Artwork year must be between 1000 and current year
   - Parameters: entity_label, property_name, constraint_type, value

7. **custom_cypher**: Custom validation using Cypher query
   - Example: Complex business logic specific to your domain
   - Parameters: cypher_query, description

**Rule Severity:**
- **error**: Critical issues that must be fixed
- **warning**: Important issues that should be reviewed
- **info**: Informational findings for awareness

**Best Practices:**
- Start with the most critical rules (required relationships)
- Consider temporal logic (dates, sequences)
- Think about data completeness (orphans, missing values)
- Consider domain-specific business rules
- Balance between too strict (many false positives) and too loose (misses issues)
"""

agent_chain_of_thought = """
AVAILABLE TOOLS (use these exact names - no other functions exist):
- get_approved_user_goal: Get the user's goal
- get_approved_construction_plan: Get the approved schema (domain graph)
- get_approved_entities: Get approved entity types (subject graph)
- get_approved_facts: Get approved fact types (subject graph)
- get_schema_context: Get summary of schema context
- add_quality_rule: Add a new quality rule
- remove_quality_rule: Remove a quality rule
- get_proposed_quality_rules: Get all proposed rules
- approve_quality_rules: Approve the rules (user action)
- get_approved_quality_rules: Get approved rules

**Workflow:**

1. **Understand Context**
   - Get user goal, schema, entities, and facts
   - Understand what the graph represents
   - Identify critical relationships and constraints

2. **Propose Initial Rules**
   - Start with required relationships (most critical)
   - Add temporal constraints if dates are involved
   - Add orphan detection for key entity types
   - Add unresolved entity detection
   - Propose 5-10 rules initially, not too many

3. **Present to User**
   - Get proposed rules
   - Present in an organized way:
     * Group by severity (error, warning, info)
     * Explain what each rule checks
     * Explain why it's important
   - Ask if user wants to add/modify/remove any rules

4. **Refine Based on Feedback**
   - Add new rules user requests
   - Remove rules user doesn't want
   - Adjust severity levels if needed
   - Modify parameters if needed

5. **Finalize**
   - Review final set of rules
   - Ensure all critical aspects covered
   - Get user approval
   - Call approve_quality_rules when user approves

**CRITICAL:**
- Only use exact tool names listed above
- Always get schema context first before proposing rules
- Present rules clearly to the user before asking for approval
- Don't propose too many rules at once (5-10 is good start)
- Focus on rules that match the user's domain and goal
- When user approves, call approve_quality_rules
"""

# Combine all instruction components
agent_instruction = f"""
{agent_role_and_goal}

{agent_hints}

{agent_chain_of_thought}
"""


# ============================================================================
# Tool List
# ============================================================================

agent_tools = [
    get_approved_user_goal,
    get_approved_construction_plan,
    get_approved_entities,
    get_approved_facts,
    get_schema_context,
    add_quality_rule,
    remove_quality_rule,
    get_proposed_quality_rules,
    approve_quality_rules,
    get_approved_quality_rules
]


# ============================================================================
# Agent Definition
# ============================================================================

data_quality_rules_agent = LlmAgent(
    name="data_quality_rules_agent_v1",
    description="Helps users define custom data quality rules for knowledge graph validation",
    model=llm,
    instruction=agent_instruction,
    tools=agent_tools
)

logger.info("Created Data Quality Rules Agent")

