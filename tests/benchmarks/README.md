# Benchmark Outputs

This directory contains benchmark/expected outputs for agent testing and validation.

## Purpose

These benchmarks serve as reference outputs to compare against actual agent outputs during testing. They represent the ideal or expected behavior for each agent given specific test data.

## Files

### `schema_proposal_structured_story1_benchmark.json`

**Agent:** Schema Proposal Agent (Structured)  
**Test Data:** Story 1 (Art Collection Use Case)  
**Purpose:** Expected construction plan output for the Schema Proposal Agent when processing Story 1 CSV files.

**Usage:**
- Compare actual agent output against this benchmark during testing
- Validate that the agent correctly identifies nodes, relationships, and properties
- Ensure graph connectivity and proper schema design

**Key Validations:**
- ✅ 4 node types identified (Artist, Artwork, Location, Medium)
- ✅ 3 relationship types identified (CREATED, LOCATED_AT, HAS_MEDIUM)
- ✅ Full relationship files preferred over foreign keys
- ✅ All nodes connected (no isolated components)
- ✅ Unique identifiers correctly identified for each node

## Adding New Benchmarks

When adding benchmarks for other agents:
1. Use descriptive filenames: `<agent_name>_<test_case>_benchmark.json`
2. Include metadata: description, test data path, input conditions
3. Document validation criteria and design decisions
4. Update this README with the new benchmark

