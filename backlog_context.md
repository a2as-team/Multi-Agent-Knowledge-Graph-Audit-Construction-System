## **Estimation Index Used:** {#estimation-index-used:}

XS: 0.5 \- 1 Days  
S: 1 \- 2 Days  
M: 2 \- 3 Days  
L: 3 \- 4 Days  
XL: 4 \- 5 Days

Net POC sprint time taken : 15 days  
Now we have to take 0.6 of this as the executable time (as per the documentation) : 15 \* 0.6 \= 9 \- 10 Days

[Estimation Index Used:](#estimation-index-used:)

[Story 1: Base Course Implementation Setup \- Art Collection Use Case (S)](#story-1:-base-course-implementation-setup---art-collection-use-case-\(s\))

[Story 2: Audit Query Generation System \- Schema-Aware Custom Rules (M)](#story-2:-audit-query-generation-system---schema-aware-custom-rules-\(m\))

[Story 3: PDF/DOCX Text and Table Extraction (M)](#story-3:-pdf/docx-text-and-table-extraction-\(m\))

[Story 4: Image Filename Pattern Detection and Artwork Linking (S)](#story-4:-image-filename-pattern-detection-and-artwork-linking-\(s\))

[Story 5: OCR Text Extraction from Images and Artwork Linking (M)](#story-5:-ocr-text-extraction-from-images-and-artwork-linking-\(m\))

[Story 6: Duplicate Image Detection with Merge/Flag Decision (S)](#story-6:-duplicate-image-detection-with-merge/flag-decision-\(s\))

Now as you can see we can only afford till story 4 in this POC sprint.

## **Story 1: Base Course Implementation Setup \- Art Collection Use Case (S)** {#story-1:-base-course-implementation-setup---art-collection-use-case-(s)}

**POC Experiment Definition**  
**Hypothesis Statement:** We believe that adapting the multi-agent architecture from the Neo4j course lessons to work with our art collection test dataset (CSV and Markdown files) will result in a **working baseline system** that successfully constructs a **Neo4j knowledge graph with Artist, Artwork, Location, and Medium entities (and more as generated/suggested)** when faced with test dataset containing CSV files (structured data) and Markdown files (unstructured text) with initial inconsistency patterns.  
**The Experiment (Test Setup)**   
To validate this, we will execute the following:

1. **Input Data:**  
* Test dataset from Story 1 containing:  
* CSV files (2-3): Structured artwork data with columns for:  
* Artwork information (artwork\_id, title, creation\_date, dimensions, medium\_id)  
* Artist information (artist\_id, name, birth\_date, nationality)  
* Location information (location\_id, name, building, room)  
* Medium information (medium\_id, type, description)  
* Relationship mappings (artwork\_id → artist\_id, artwork\_id → location\_id, artwork\_id → medium\_id)  
* Initial inconsistency patterns: duplicate rows, missing fields, malformed fields  
* Markdown files (5-10): Unstructured text content about artworks, artists, locations, exhibitions, loans, etc.  
* Content includes narrative descriptions, exhibition histories, loan records  
* Initial inconsistency patterns: typos, partial information, narrative sections  
2. **Configuration:**  
* Set up local development environment:  
* Implement course architecture components exactly as specified:  
* Adaptations for art collection domain:  
* Configure User Intent Agent test case: "art collection provenance graph" or "content audit system for art collection"  
* Let Schema Proposal Agent infer schema from CSV structure (should identify Artist, Artwork, Location, Medium nodes)  
* Configure NER/Fact Extraction to identify art collection entities from Markdown (artworks, artists, locations, exhibitions)  
* Configure entity resolution to link Markdown-extracted entities with CSV domain entities  
* Create helper modules: helper.py, neo4j\_for\_adk.py, tools.py matching course structure  
* Set up Neo4j import directory structure  
3. **Action:**  
* Execute complete pipeline end-to-end with art collection test dataset:  
* User Intent Agent: Define goal as "art collection provenance graph" or similar  
* File Suggestion Agent: Identify relevant CSV and Markdown files  
* Schema Proposal Agent: Infer schema from CSV structure (should propose Artist, Artwork, Location, Medium nodes and relationships)  
* Schema Critic Agent: Validate proposed schema  
* Domain Graph Construction: Build graph from CSV data (Artist, Artwork, Location, Medium nodes and relationships)  
* NER Agent: Extract entity types from Markdown files (should identify artworks, artists, locations, etc.)  
* Fact Extraction Agent: Extract relationship types from Markdown  
* Subject Graph Construction: Build subject graph from Markdown-extracted entities using Neo4j GraphRAG  
* Entity Resolution: Link subject graph entities to domain graph nodes (e.g., Markdown mentions of artworks → CSV Artwork nodes)  
* Verify final knowledge graph contains:  
* Artist nodes (from CSV \+ extracted from Markdown)  
* Artwork nodes (from CSV \+ extracted from Markdown)  
* Location nodes (from CSV \+ extracted from Markdown)  
* Medium nodes (from CSV)  
* Relationships: Artist-CREATED-Artwork, Artwork-LOCATED\_AT-Location, Artwork-HAS\_MEDIUM-Medium, etc.  
* Run test queries to validate graph structure and relationships

**Success Criteria (The Evidence)**   
This experiment is successful if we observe:

* \[ \] Metric: Complete pipeline executes successfully with art collection test dataset  
* \[ \] Output: All agents complete without critical errors (User Intent, File Suggestion, Schema Proposal, NER, Fact Extraction)  
* \[ \] Output: Domain graph constructed in Neo4j with Artist, Artwork, Location, Medium nodes (and maybe relevant more) from CSV files  
* \[ \] Output: Subject graph constructed in Neo4j with entities extracted from Markdown files  
* \[ \] Output: Entity resolution creates CORRESPONDS\_TO relationships between subject and domain graphs  
* \[ \] Graph Structure: Final graph contains at least:  
* \[ \] Artist nodes  
* \[ \] Artwork nodes   
* \[ \] Location nodes   
* \[ \] Medium nodes   
* \[ \] Relationships connecting these entities (CREATED, LOCATED\_AT, HAS\_MEDIUM, etc.)  
* \[ \] Log: No critical errors; all agents use tools successfully  
* \[ \] Infrastructure: Local environment is fully configured and reproducible (documentation, requirements.txt, setup scripts)  
* \[ \] Code Quality: Course components implemented and adapted for art collection use case, organized in modular structure matching course architecture  
* \[ \] Validation: Test queries return expected results (e.g., "Find all artworks by artist X", "Find all artworks in location Y")  
* \[ \] Baseline Established: System successfully handles test dataset with initial inconsistency patterns (duplicates, missing fields, malformed fields) \- even if not perfectly resolved, the graph is constructed

**Decision Trigger**

* If this FAILS, does it kill the project? Yes (cannot proceed without working baseline adapted to our use case)  
  ---

  **Status:** \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]  
  **Findings:** \[\]  
  **Recommendation:** \[\]

## **Story 2: Audit Query Generation System \- Schema-Aware Custom Rules (M)** {#story-2:-audit-query-generation-system---schema-aware-custom-rules-(m)}

**POC Experiment Definition**  
**Hypothesis Statement:** We believe that an Audit Query Generation system (with schema-aware rule engine that generates custom audit rules based on graph structure) will result in identification of data quality issues specific to the knowledge graph schema when faced with a knowledge graph constructed from test data containing inconsistency patterns, enabling curator review and safe updates.  
**The Experiment (Test Setup)**   
To validate this, we will execute the following:

1. **Input Data:**  
* Knowledge graph constructed in Story 0 (Artist, Artwork, Location, Medium nodes and relationships)  
* Graph contains data with inconsistency patterns from Story 1 test dataset  
* approved\_construction\_plan from Story 0 (defines expected schema: node labels, unique identifiers, relationships)  
2. **Configuration:**  
* Create Audit Query Generation Agent/Tool that:  
* Takes approved\_construction\_plan as input to understand expected schema  
* Analyzes the constructed graph structure (actual nodes, relationships, properties)  
* Generates schema-specific audit rules based on construction plan:  
* For each node type: check for duplicates using unique identifier from construction plan  
* For each relationship type: check for missing relationships (e.g., if Artwork should have CREATED→Artist, find artworks without this relationship)  
* For each node type: check for missing required properties  
* Allows custom audit rules to be defined (either by agent or configuration):  
* Domain-specific rules (e.g., "Artwork must have at least one Location")  
* Business logic rules (e.g., "Artwork created after 2000 should have digital medium option")  
* Cross-entity validation rules (e.g., "If Artwork has Location, Location must exist as node")  
* Implement rule engine that:  
* Auto-generates common patterns from construction plan:  
* Duplicate detection (based on unique\_column\_name from construction plan)  
* Missing relationship detection (based on relationship types in construction plan)  
* Missing property detection (based on properties list in construction plan)  
* Supports custom rule definitions (template-based or configuration-based):  
* Rule templates that can be instantiated with schema-specific details  
* Custom Cypher queries for domain-specific validations  
* Create audit report generation:  
* Execute generated audit queries  
* Collect results into structured audit report  
* Categorize issues by rule type and severity  
* Provide actionable information for curator review  
3. **Action:**  
* Define custom audit rules for art collection schema:  
* Rule 1: "Artwork nodes must have CREATED relationship to Artist" (schema-specific)  
* Rule 2: "Artwork nodes must have LOCATED\_AT relationship to Location" (schema-specific)  
* Rule 3: "No duplicate Artwork nodes with same artwork\_id" (auto-generated from unique identifier)  
* Rule 4: "Artist name should not be empty" (custom property validation)  
* Rule 5: "Same artwork\_id should not have conflicting artist names" (contradiction detection)  
* Run audit system after graph construction completes  
* Generate audit queries:  
* Auto-generate queries from construction plan (duplicates, missing relationships)  
* Execute custom rules defined for art collection schema  
* Execute all audit queries against Neo4j graph  
* Generate audit report listing:  
* Issues found by each rule  
* Number of violations per rule type  
* Specific examples (node IDs, property values) for each issue  
* Verify audit report is human-readable and actionable

**Success Criteria (The Evidence)**   
This experiment is successful if we observe:

* \[ \] Metric: Audit query generation and execution completes for test graph  
* \[ \] Output: Audit system successfully generates schema-specific audit queries from approved\_construction\_plan:  
* \[ \] Duplicate detection queries for each node type (using unique identifiers from plan)  
* \[ \] Missing relationship queries (based on relationship types in plan)  
* \[ \] Missing property queries (based on properties in plan)  
* \[ \] Output: Custom audit rules can be defined and executed:  
* \[ \] At least 3 custom rules defined for art collection schema  
* \[ \] Custom rules execute successfully and detect issues  
* \[ \] Output: Audit report identifies issues specific to art collection schema:  
* \[ \] Artworks without Artists (custom rule)  
* \[ \] Artworks without Locations (custom rule)  
* \[ \] Duplicate artworks (auto-generated rule)  
* \[ \] Missing required properties (auto-generated rule)  
* \[ \] Contradictions (custom rule)  
* \[ \] Output: Audit report is structured and categorizes issues by rule type  
* \[ \] Output: Audit report provides specific examples (node IDs, property values) for each issue type  
* \[ \] Extensibility: System allows new custom rules to be added without code changes (configuration-based or agent-defined)  
* \[ \] Log: No errors during query generation or execution  
* \[ \] Quality: All audit queries are valid Cypher and execute successfully  
* \[ \] Actionable: Audit report format enables curator to identify and review specific issues

**Decision Trigger**

* If this FAILS, does it kill the project? No (can manually query graph, but indicates need for better audit automation)

---

**Status**: \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]

**Findings**: \[\]

**Recommendation**: \[\]

## **Story 3: PDF/DOCX Text and Table Extraction (M)** {#story-3:-pdf/docx-text-and-table-extraction-(m)}

**POC Experiment Definition**  
**Hypothesis Statement:** We believe that extending the File Suggestion and Schema Proposal agents to handle PDF/DOCX text and table extraction will result in successful processing of PDF/DOCX documents as both unstructured text sources and structured table sources when faced with PDF/DOCX files containing narrative text, structured tables, and mixed content formats.  
**The Experiment (Test Setup)**   
To validate this, we will execute the following:

1. **Input Data (extension):**  
* Test dataset from Story 1 containing:  
* PDF files (3-5): Art collection catalogues with:  
* Narrative text sections (exhibition histories, artist biographies)  
* Structured tables (artwork metadata: title, artist, location, medium, dimensions)  
* Mixed content (tables embedded in narrative sections)  
* DOCX files (2-3): Similar structure to PDFs  
* Files may contain inconsistency patterns: broken headers, missing page numbers, inconsistent formatting  
2. **Configuration:**  
* Extend sample\_file tool to handle PDF/DOCX:  
* Text Extraction: Use pdfplumber for PDFs and python-docx for DOCX to extract text content  
* Table Extraction: Use pdfplumber/tabula-py for PDF tables, python-docx for DOCX tables  
* Return both text content and table structures (columns, sample rows)  
* Extend File Suggestion Agent:  
* Update list\_available\_files to detect PDF/DOCX files  
* Update sample\_file to extract text preview (first page) and table preview (first table) from PDF/DOCX  
* Agent can suggest PDF/DOCX files for both structured (tables) and unstructured (text) processing  
* Extend Schema Proposal Agent:  
* Update sample\_file and search\_file to work with PDF/DOCX-extracted tables  
* Agent can analyze table structure to propose schema (similar to CSV analysis)  
* Agent can identify which PDF/DOCX files contain tables vs narrative text  
* Extend Unstructured Data Extraction (Lesson 7):  
* Replace Markdown loader with PDF/DOCX text loader for Neo4j GraphRAG pipeline  
* Extract text from PDF/DOCX pages for entity and relationship extraction  
* Handle mixed content (extract text while preserving table context)  
1. Action:  
* Run File Suggestion Agent with PDF/DOCX files:  
* Agent lists PDF/DOCX files  
* Agent samples files to identify content type (tables vs text)  
* Agent suggests files for import  
* Run Schema Proposal Agent:  
* Agent extracts tables from PDF/DOCX files  
* Agent analyzes table structure (columns, data types, relationships)  
* Agent proposes schema based on table structure (similar to CSV analysis)  
* Run Unstructured Extraction:  
* Extract text from PDF/DOCX for NER and Fact Extraction  
* Process narrative sections for entity extraction  
* Verify both structured (tables) and unstructured (text) content are processed correctly

Success Criteria (The Evidence) This experiment is successful if we observe:

* \[ \] Metric: PDF/DOCX text extraction completes for all test files in \< 3 minutes  
* \[ \] Metric: PDF/DOCX table extraction completes for all test files in \< 2 minutes  
* \[ \] Output: sample\_file tool successfully extracts:  
* \[ \] Text content from PDF pages  
* \[ \] Text content from DOCX documents  
* \[ \] Table structures (columns, sample rows) from PDF tables  
* \[ \] Table structures from DOCX tables  
* \[ \] Output: File Suggestion Agent correctly identifies PDF/DOCX files and suggests them for import  
* \[ \] Output: Schema Proposal Agent successfully:  
* \[ \] Extracts tables from PDF/DOCX files  
* \[ \] Analyzes table structure to propose schema  
* \[ \] Identifies unique identifiers and relationships in tables  
* \[ \] Output: Unstructured extraction successfully processes PDF/DOCX text:  
* \[ \] Text extracted from PDF/DOCX pages  
* \[ \] Entities extracted from narrative text  
* \[ \] Relationships extracted from text content  
* \[ \] Log: No errors during PDF/DOCX processing  
* \[ \] Quality: Extracted tables maintain structure (columns, data types)  
* \[ \] Quality: Extracted text preserves context (page breaks, sections)

🛑 Decision Trigger

* If this FAILS, does it kill the project? No (can use CSV/Markdown only, but limits real-world applicability)

---

Status: \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]Findings: \[\]Recommendation: \[\]

---

## **Story 4: Image Filename Pattern Detection and Artwork Linking (S)** {#story-4:-image-filename-pattern-detection-and-artwork-linking-(s)}

🧪 POC Experiment DefinitionHypothesis StatementWe believe that an Image Filename Pattern Detection tool that extracts identifiers, locations, and metadata from image filenames will result in successful linking of images to artwork nodes in the knowledge graph when faced with images with mixed naming conventions (camera IDs, location-based names, date tokens).The Experiment (Test Setup) To validate this, we will execute the following:

1. Input Data (extension) :  
* Test dataset from Story 1 containing:  
* Images (15-20) with mixed naming patterns:  
* Type A: \<ID\>\_\<Location\> \<date\>.jpg (e.g., 001\_Luke Wadding Library 25 05 21.jpg)  
* Type B: \<Location\>\_\<ID\>.jpg (e.g., College Street Chapel\_034.jpg)  
* Type C: \<LongCameraID\> copy.jpg (e.g., 9I4A1851 copy.jpg)  
* Type D: \<Corridor Name\>\_\<ID\> (e.g., Corridor\_22.jpg)  
* Knowledge graph from Story 0 with Artwork and Location nodes  
1. Configuration:  
* Create Image Filename Pattern Detection tool:  
* detect\_image\_filename\_pattern(image\_path: str) \-\> dict:  
* Detects pattern type (A, B, C, D)  
* Extracts: ID, location, date (if present)  
* Returns structured metadata  
* Create Image-to-Artwork Linking tool:  
* link\_image\_to\_artwork(image\_path: str, extracted\_metadata: dict, tool\_context: ToolContext) \-\> dict:  
* Uses extracted ID to match artwork\_id in graph  
* Uses extracted location to match Location nodes  
* Creates Image node with relationship to Artwork node  
* Stores filename pattern metadata as properties  
* Extend File Suggestion Agent:  
* Add image file detection (JPG, PNG)  
* Sample images to extract filename patterns  
* Suggest images for processing  
* Create Image Processing Agent (optional) or tool:  
* Processes approved images  
* Extracts filename patterns  
* Links images to artwork nodes in graph  
1. Action:  
* Run filename pattern detection on all test images:  
* Detect pattern type for each image  
* Extract ID, location, date from filenames  
* Handle edge cases (missing components, typos in filenames)  
* Link images to artwork nodes:  
* Match extracted IDs to artwork\_id in graph  
* Create Image nodes with properties (filename, pattern\_type, extracted\_id, extracted\_location)  
* Create IMAGE\_OF relationship: Image → Artwork  
* Create LOCATED\_AT relationship: Image → Location (if location extracted)  
* Verify linking accuracy:  
* Check that images with valid IDs are linked to correct artworks  
* Check that images with location info are linked to correct locations  
* Handle cases where ID/location doesn't match (flag for review)

Success Criteria (The Evidence) This experiment is successful if we observe:

* \[ \] Metric: Filename pattern detection completes for all images in \< 1 minute  
* \[ \] Output: Pattern detection correctly identifies:  
* \[ \] At least 3 different pattern types (A, B, C, or D)  
* \[ \] Extracted IDs from filenames  
* \[ \] Extracted locations from filenames (where present)  
* \[ \] Extracted dates from filenames (where present)  
* \[ \] Output: Image nodes created in graph with properties:  
* \[ \] filename  
* \[ \] pattern\_type  
* \[ \] extracted\_id  
* \[ \] extracted\_location (if available)  
* \[ \] Output: Images successfully linked to artwork nodes:  
* \[ \] At least 10 images linked via IMAGE\_OF relationship  
* \[ \] Linking based on extracted ID matching artwork\_id  
* \[ \] Output: Images linked to location nodes (where location extracted):  
* \[ \] At least 5 images linked via LOCATED\_AT relationship  
* \[ \] Log: No errors during pattern detection or linking  
* \[ \] Quality: Pattern detection handles edge cases (missing components, typos)  
* \[ \] Quality: Unmatched images are flagged (not silently ignored)

🛑 Decision Trigger

* If this FAILS, does it kill the project? No (can manually link images, but indicates need for better pattern detection)

---

Status: \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]Findings: \[\]Recommendation: \[\]

---

## **Story 5: OCR Text Extraction from Images and Artwork Linking (M)** {#story-5:-ocr-text-extraction-from-images-and-artwork-linking-(m)}

🧪 POC Experiment DefinitionHypothesis StatementWe believe that OCR text extraction from images combined with entity matching will result in successful linking of images to artwork nodes when faced with images containing embedded text (labels, plaques, wall text) that can be OCRed to identify artwork references.The Experiment (Test Setup) To validate this, we will execute the following:

1. Input Data:  
* Test dataset containing:  
* Images (5-10) with embedded text:  
* Artwork labels with titles  
* Plaques with artist names and titles  
* Wall text with artwork information  
* Knowledge graph from Story 0 with Artwork nodes (titles, artist names)  
1. Configuration:  
* Create OCR Text Extraction tool:  
* extract\_ocr\_text(image\_path: str) \-\> dict:  
* Uses Tesseract OCR or EasyOCR to extract text from images  
* Returns extracted text and confidence scores  
* Handles multiple text regions in image  
* Create OCR-to-Artwork Linking tool:  
* link\_image\_via\_ocr(extracted\_text: str, image\_path: str, tool\_context: ToolContext) \-\> dict:  
* Uses fuzzy string matching to find artwork titles in OCR text  
* Uses entity matching to find artist names in OCR text  
* Creates or updates Image node with OCR text as property  
* Creates IMAGE\_OF relationship to matched Artwork node  
* Stores confidence score for matching  
* Integration strategy:  
* Option A: Store OCR text as Image node property, use in entity resolution  
* Option B: Feed OCR text into NER/Fact Extraction agents for entity extraction  
* Option C: Direct matching (fuzzy match OCR text to artwork titles/artist names)  
* Implement fallback strategy:  
* If filename pattern detection fails, try OCR linking  
* If OCR linking fails, flag image for manual review  
1. Action:  
* Run OCR extraction on test images:  
* Extract text from images with embedded labels/plaques  
* Handle images with multiple text regions  
* Handle images with poor quality/low contrast text  
* Link images via OCR text:  
* Match extracted text to artwork titles (fuzzy matching)  
* Match extracted text to artist names  
* Create Image nodes with OCR text property  
* Create IMAGE\_OF relationships to matched artworks  
* Verify linking accuracy:  
* Check that images with clear text are linked correctly  
* Handle cases where OCR text is ambiguous or doesn't match  
* Flag images for review where confidence is low

Success Criteria (The Evidence) This experiment is successful if we observe:

* \[ \] Metric: OCR extraction completes for all test images in \< 5 minutes  
* \[ \] Output: OCR successfully extracts text from images:  
* \[ \] At least 5 images with readable text extracted  
* \[ \] Extracted text includes artwork titles or artist names  
* \[ \] Confidence scores provided for extracted text  
* \[ \] Output: Images linked via OCR text:  
* \[ \] At least 3 images linked to artwork nodes via OCR matching  
* \[ \] Linking based on fuzzy matching of OCR text to artwork titles/artist names  
* \[ \] Output: Image nodes contain OCR text as property:  
* \[ \] ocr\_text property stores extracted text  
* \[ \] ocr\_confidence property stores confidence score  
* \[ \] Output: Linking strategy implemented:  
* \[ \] Clear decision on Option A, B, or C (or combination)  
* \[ \] Fallback strategy works (filename → OCR → manual review)  
* \[ \] Log: No errors during OCR extraction or linking  
* \[ \] Quality: OCR handles images with varying text quality  
* \[ \] Quality: Low-confidence matches are flagged for review

🛑 Decision Trigger

* If this FAILS, does it kill the project? No (can rely on filename patterns only, but limits linking capability)

---

Status: \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]Findings: \[\]Recommendation: \[\]

---

## **Story 6: Duplicate Image Detection with Merge/Flag Decision (S)** {#story-6:-duplicate-image-detection-with-merge/flag-decision-(s)}

🧪 POC Experiment DefinitionHypothesis StatementWe believe that perceptual hash-based duplicate image detection combined with a merge/flag decision system will result in identification and handling of duplicate/near-duplicate images when faced with images that are cropped variants, different orientations, or near-duplicates of the same artwork.The Experiment (Test Setup) To validate this, we will execute the following:

1. Input Data:  
* Test dataset containing:  
* Images (15-20) including:  
* Duplicate images (same artwork, same angle)  
* Near-duplicates (same artwork, cropped differently)  
* Orientation variants (same artwork, different angles/lighting)  
* Unique images (different artworks)  
* Knowledge graph with Image nodes already created (from Story 4\)  
1. Configuration:  
* Create Perceptual Hash tool:  
* compute\_perceptual\_hash(image\_path: str) \-\> dict:  
* Uses imagehash library (pHash algorithm)  
* Computes perceptual hash for image  
* Returns hash value and image metadata  
* Create Duplicate Detection tool:  
* detect\_duplicate\_images(image\_paths: List\[str\], similarity\_threshold: float \= 0.9) \-\> dict:  
* Computes perceptual hashes for all images  
* Compares hashes to find duplicates/near-duplicates  
* Groups similar images together  
* Returns duplicate groups with similarity scores  
* Create Merge/Flag Decision system:  
* Merge Strategy: Keep one canonical image, merge others as variants  
* Flag Strategy: Flag duplicates for curator review, keep all images  
* Hybrid Strategy: Auto-merge exact duplicates, flag near-duplicates  
* Decision criteria:  
* Exact duplicates (hash distance \= 0): Auto-merge  
* Near-duplicates (hash distance \< threshold): Flag for review  
* Different images (hash distance \> threshold): Keep separate  
* Implement duplicate handling:  
* If merge: Create single Image node, store variant image paths as properties  
* If flag: Create all Image nodes, add is\_duplicate property and DUPLICATE\_OF relationship  
* Store decision metadata (merge/flag, confidence, timestamp)  
1. Action:  
* Run duplicate detection on all images:  
* Compute perceptual hashes  
* Compare hashes to find duplicates  
* Group similar images  
* Apply merge/flag decision:  
* Auto-merge exact duplicates  
* Flag near-duplicates for curator review  
* Keep unique images as-is  
* Update knowledge graph:  
* If merge: Update Image nodes (merge variants)  
* If flag: Add duplicate markers to Image nodes  
* Verify duplicate handling:  
* Check that exact duplicates are merged correctly  
* Check that near-duplicates are flagged appropriately  
* Check that unique images remain separate

Success Criteria (The Evidence) This experiment is successful if we observe:

* \[ \] Metric: Duplicate detection completes for all images in \< 3 minutes  
* \[ \] Output: Perceptual hashes computed for all images:  
* \[ \] Hash values generated successfully  
* \[ \] Hash comparison works correctly  
* \[ \] Output: Duplicate groups identified:  
* \[ \] At least 2 duplicate groups found (if duplicates exist in test data)  
* \[ \] Similarity scores calculated correctly  
* \[ \] Groups include exact duplicates and near-duplicates  
* \[ \] Output: Merge/flag decision system works:  
* \[ \] Exact duplicates auto-merged (or flagged based on strategy)  
* \[ \] Near-duplicates flagged for review  
* \[ \] Decision metadata stored (merge/flag, confidence, timestamp)  
* \[ \] Output: Knowledge graph updated correctly:  
* \[ \] If merge: Single Image node with variant paths stored  
* \[ \] If flag: All Image nodes with is\_duplicate property and DUPLICATE\_OF relationships  
* \[ \] Log: No errors during hash computation or duplicate detection  
* \[ \] Quality: System correctly distinguishes:  
* \[ \] Exact duplicates (same image file)  
* \[ \] Near-duplicates (cropped, different orientation)  
* \[ \] Unique images (different artworks)  
* \[ \] Configurability: Merge/flag strategy can be configured (auto-merge vs flag-all)

🛑 Decision Trigger

* If this FAILS, does it kill the project? No (can keep all images, but indicates need for better duplicate handling)

---

Status: \[VALIDATED ✅ / INVALIDATED ❌ / INCONCLUSIVE ⚠️\]Findings: \[\]Recommendation: \[\]

