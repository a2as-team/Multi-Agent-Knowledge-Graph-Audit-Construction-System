# Known Issues and Solutions

This document tracks known issues encountered during development, their root causes, and solutions.

---

## Issue #1: Schema Proposal Agent Removes Node Constructions Due to Duplicate Data Values

**Date Identified:** 2025-12-04  
**Agent:** Schema Proposal Agent (Structured) and Schema Critic Agent  
**Severity:** Medium  
**Status:** Fixed

### Problem Description

The Schema Proposal Agent was removing node constructions when it found duplicate values in the test data. For example:
- Found duplicate `artist_id` values (A012 appears 2 times, A002 appears 2 times)
- Proposed Artist node construction
- Immediately removed it, thinking the column wasn't a valid unique identifier
- Never completed the full schema proposal
- Schema Critic Agent found no `proposed_construction_plan` and returned "retry"

### Root Cause

The agent was treating duplicate data values as a schema design problem, when they are actually **data quality issues**. The `artist_id` column is still the intended unique identifier - duplicates in the data will be handled during data import/cleaning, not during schema design.

The agent's instructions didn't clearly distinguish between:
- **Schema design**: Identifying which column is the unique identifier
- **Data quality**: Whether that column has duplicate values in the actual data

### Solution Implemented

1. **Updated `proposal_agent_hints`** to clarify:
   - Duplicate values in data are data quality issues, NOT schema design problems
   - The column is still the unique identifier even if duplicates exist
   - Focus on identifying the INTENDED unique identifier column (typically ends with `_id`)

2. **Updated `proposal_agent_chain_of_thought_directions`** to:
   - Emphasize proposing ALL node and relationship constructions FIRST
   - Only remove constructions after the complete schema is proposed and critic provides feedback
   - Add a completion check to ensure all approved files have constructions

3. **Updated `critic_agent_hints`** to:
   - Clearly distinguish between schema design and data quality issues
   - Emphasize that duplicate values do NOT invalidate unique identifier columns
   - Focus on schema structure validation (connectivity, completeness, correctness) rather than data quality

4. **Updated `critic_agent_chain_of_thought_directions`** to:
   - Validate schema structure, not data quality
   - Check for unique identifier columns (by name), not unique values
   - Only reject schemas for structural problems, not data quality issues

### Related Files
- `src/agents/schema_proposal_structured_agent.py`
- `data/story1/artists.csv` (contains intentional duplicate test data)

### Test Data Context
The test data intentionally contains inconsistencies (duplicate rows, missing fields, malformed fields) to test the system's ability to handle data quality issues. The schema proposal agent should identify the schema structure despite these data quality problems.

---

## Issue #2: Rate Limit Errors with Free Tier Gemini API

**Date Identified:** 2025-12-04  
**Agent:** All agents using Gemini API  
**Severity:** Low (Expected behavior)  
**Status:** Fixed

### Problem Description

Free tier Gemini API has strict rate limits:
- 10 requests per minute per model
- Schema Proposal Agent can make 30-135 API calls per run (depending on iterations)
- Hits rate limit quickly, causing `litellm.RateLimitError`

### Root Cause

The Schema Proposal Agent uses a refinement loop with multiple agents:
- Schema Proposal Agent: ~20-30 API calls per iteration
- Schema Critic Agent: ~10-15 API calls per iteration
- Max 3 iterations = 90-135 total calls possible

### Solutions Implemented

1. **Retry logic with dynamic delay extraction**: Implemented in `src/utils/helper.py`
   - Automatically retries up to 5 times when rate limit errors occur
   - Extracts exact retry delay from API error messages (e.g., "Please retry in 35.76s")
   - Falls back to exponential backoff (36s, 54s, 81s, 122s, 183s) if delay cannot be parsed
   - Catches `RateLimitError` from litellm and also checks error messages for rate limit indicators
   - Uses `extract_retry_delay_from_error()` function to parse retry delays from error messages
   
2. **Rate limit configuration**: Added to `src/utils/config.py`
   - `GEMINI_FREE_TIER_RPM = 10` (requests per minute)
   - `GEMINI_FREE_TIER_WAIT_TIME = 36` (fallback seconds to wait when rate limit hit)
   - `MAX_RETRIES_ON_RATE_LIMIT = 5`
   - `RETRY_BACKOFF_MULTIPLIER = 1.5`

### Additional Recommendations

1. **Reduce max_iterations**: Change from 3 to 2 in `schema_proposal_structured_agent.py` to reduce API calls
2. **Upgrade to paid tier**: For production use with higher rate limits

### Related Files
- `src/agents/schema_proposal_structured_agent.py` (line 239: `max_iterations=3`)
- `src/utils/config.py` (DEFAULT_MODEL configuration)

---

## Issue Template

Use this template for logging new issues:

```markdown
## Issue #X: [Brief Title]

**Date Identified:** YYYY-MM-DD  
**Agent:** [Agent Name]  
**Severity:** Low/Medium/High/Critical  
**Status:** Open/In Progress/Fixed/Won't Fix

### Problem Description
[Detailed description of the issue]

### Root Cause
[Analysis of why this happens]

### Solution Implemented/Proposed
[What was done or what should be done]

### Related Files
- `path/to/file.py`

### Test Data Context
[If applicable, describe relevant test data]
```

