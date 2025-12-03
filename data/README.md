# Data Directory Structure

This directory contains test datasets organized by story/feature development.

## Directory Organization

### `raw/`
- **Purpose**: Original test data (reference/backup)
- **Content**: Complete base test dataset with base set of inconsistencies
- **Usage**: Reference only - do not modify
- **Note**: This is the source of truth for the base dataset

### `story1/`
- **Purpose**: Base test data for Story 1 (Base Course Implementation Setup)
- **Content**: CSV files (artworks, artists, locations, medium, relationships) and Markdown files (artist bios, exhibition histories, provenance notes, etc.)
- **Inconsistencies**: Contains initial inconsistency patterns:
  - Duplicate rows
  - Missing fields (GAP)
  - Malformed fields
  - Contradictions
  - Redundancies
- **Usage**: Primary dataset for Story 1 implementation and testing
- **Note**: After Story 1 testing, if the system cannot handle the full complexity, create a simplified version here. This simplified version will then be used for Story 2.

### `story2/`
- **Purpose**: Test data for Story 2 (Audit Query Generation System - completing the base pipeline)
- **Content**: Will use the same dataset as `story1/` (or the simplified version if one was created after Story 1 testing)
- **Usage**: For Story 2 development and testing
- **Note**: Story 1 + Story 2 together form the complete base setup. Story 2 extends the system but uses the same dataset as Story 1.

## Data Files

### CSV Files (Structured Data)
- `artworks.csv` - Artwork information (artwork_id, title, creation_date, dimensions, medium_id)
- `artists.csv` - Artist information (artist_id, name, birth_date, nationality)
- `locations.csv` - Location information (location_id, name, building, room)
- `medium.csv` - Medium information (medium_id, type, description)
- `artwork_artist.csv` - Artwork to Artist relationships
- `artwork_location.csv` - Artwork to Location relationships

### Markdown Files (Unstructured Data)
- `artist_bios.md` - Artist biographies and narratives
- `exhibition_histories.md` - Exhibition history records
- `provenance_notes.md` - Provenance and ownership records
- `misc_notes.md` - Miscellaneous notes
- `developer_inconsistencies.md` - Documentation of intentionally added inconsistencies

## Workflow

1. **Story 1**: 
   - Start with dataset from `raw/` copied to `story1/`
   - Implement course setup locally and test on this dataset
   - If system cannot handle full complexity, create simplified version in `story1/`
   - Document what inconsistencies were removed/simplified

2. **Story 2**: 
   - Use the same dataset from `story1/` (or simplified version if created)
   - Extend the system to complete the base pipeline
   - Story 1 + Story 2 = complete base setup

3. **Future Stories**: Each story can extend the previous story's dataset or add new data types

## Creating Simplified Versions

If the system cannot handle the full complexity of the base dataset after Story 1 testing:
1. Create a simplified version in `story1/` directory
2. Document what inconsistencies were removed/simplified
3. Use this simplified version for Story 2
4. Gradually add complexity back as the system improves
