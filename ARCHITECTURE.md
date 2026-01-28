# System Architecture

> **Comprehensive architectural documentation for the Genie Space Configuration Generator**
> 
> This document describes the system architecture, components, data flows, and best practices for generating and managing Databricks Genie spaces using LLMs.

## Table of Contents

1. [High-Level Flow](#high-level-flow)
2. [System Capabilities and Features](#system-capabilities-and-features)
3. [Project Structure](#project-structure)
4. [Output Schema](#output-schema)
5. [Component Details](#component-details)
   - [Instruction Formatting Layer (New in 2026)](#7-instruction-formatting-layer)
6. [Data Flow Diagram](#data-flow-diagram)
7. [Module Dependency Graph](#module-dependency-graph)
8. [Error Handling Flow](#error-handling-flow)
9. [Configuration Options](#configuration-options)
10. [Performance Characteristics](#performance-characteristics)
11. [Security Considerations](#security-considerations)
12. [Scripts and Utilities](#scripts-and-utilities)
13. [Extension Points](#extension-points)
14. [Testing Strategy](#testing-strategy)
15. [Monitoring and Debugging](#monitoring-and-debugging)
16. [Deployment Options](#deployment-options)
17. [Genie Space API Integration](#genie-space-api-integration)
18. [Best Practices and Design Principles](#best-practices-and-design-principles)
19. [Quick Reference](#quick-reference)

## High-Level Flow (Updated 2026 - Quality Assurance Pipeline)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: DOMAIN EXTRACTION (P3)                    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  DomainKnowledgeExtractor                                     │ │
│  │  Extracts from Requirements:                                  │ │
│  │  • Table Relationships (1:1, 1:N, N:1, N:M)                   │ │
│  │  • Business Metrics (formulas, KPIs, aggregations)            │ │
│  │  • Common Filters (status, dates, flags)                      │ │
│  │  • Business Terminology (glossary, acronyms)                  │ │
│  │  • Sample Queries with context                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                STEP 2: ENHANCED PROMPT BUILDING (P1)                 │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  PromptBuilder + Domain Knowledge Injection                   │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │ 1. Inject Extracted Domain Knowledge                    │ │ │
│  │  │ 2. Add SQL Quality Criteria (6-point checklist)         │ │ │
│  │  │ 3. Add Few-Shot Examples (high vs low quality)          │ │ │
│  │  │ 4. Add Instruction Guidelines (5 principles)            │ │ │
│  │  │ 5. Add Join Specification Requirements                  │ │ │
│  │  │ 6. Combine: Context + Format + Enhanced Requirements    │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: LLM GENERATION                            │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  DatabricksLLMClient                                          │ │
│  │  • Call foundation model with enhanced prompt                 │ │
│  │  • Generate configuration with reasoning                      │ │
│  │  • Parse and validate structure                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│             STEP 4: BENCHMARK EXTRACTION (Existing)                  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  BenchmarkExtractor                                           │ │
│  │  • Extract all FAQ questions (100% coverage)                  │ │
│  │  • Extract sample queries                                     │ │
│  │  • Merge into configuration                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STEP 5: SQL & INSTRUCTION VALIDATION (P2)               │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  SQLValidator                                                 │ │
│  │  • Syntax checking (sqlparse)                                 │ │
│  │  • Table reference validation                                 │ │
│  │  • Join pattern verification                                  │ │
│  │  • Quality checks (SELECT *, dates, division)                 │ │
│  │  → Report: errors, warnings, severity levels                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  InstructionQualityScorer                                     │ │
│  │  • Specificity Score (40 pts): column/table names             │ │
│  │  • Structure Score (30 pts): markdown formatting              │ │
│  │  • Clarity Score (30 pts): no vague terms                     │ │
│  │  → Report: scores, grades, suggestions                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│           STEP 6: COMPREHENSIVE CONFIG REVIEW (P3)                   │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  ConfigReviewAgent - 4-Dimension Quality Assessment           │ │
│  │                                                               │ │
│  │  1. SQL Validation Score (35%)                                │ │
│  │     • Syntax + table refs + joins + quality                   │ │
│  │  2. Instruction Quality Score (25%)                           │ │
│  │     • Average across all instructions                         │ │
│  │  3. Join Completeness Score (20%)                             │ │
│  │     • Coverage of required table relationships                │ │
│  │  4. Coverage Score (20%)                                      │ │
│  │     • Example queries per table                               │ │
│  │     • Benchmark questions                                     │ │
│  │     • SQL expressions                                         │ │
│  │                                                               │ │
│  │  → Overall Score (0-100) + Pass/Fail + Detailed Issues        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│         STEP 7: OUTPUT & UNITY CATALOG VALIDATION                    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Final Configuration + Quality Reports                        │ │
│  │  • Configuration JSON                                         │ │
│  │  • Validation Report (SQL + Instructions)                     │ │
│  │  • Review Report (4-dimension scores + issues)                │ │
│  │  • Unity Catalog table/column validation                      │ │
│  │  • Ready for deployment                                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Improvements:**
- **Priority 1**: Enhanced prompts with SQL criteria + few-shot examples + domain knowledge
- **Priority 2**: Automated SQL validation + instruction quality scoring
- **Priority 3**: Domain extraction + comprehensive 4-dimension review
- **Result**: 83/83 tests passing, production-ready quality assurance

## System Capabilities and Features

### Core Capabilities

1. **Automated Configuration Generation**
   - Leverages LLMs (Databricks Foundation Models or custom endpoints)
   - Generates production-ready Genie space configurations
   - Includes reasoning and confidence scores
   - Validates output against strict schemas

2. **Intelligent Prompt Engineering (Enhanced 2026)**
   - **Domain Knowledge Extraction**: Automatically extracts table relationships, metrics, filters, terminology
   - **Enhanced Prompts with Quality Criteria**: 6-point SQL checklist + few-shot examples + instruction guidelines
   - **Structured Context Injection**: Injects extracted domain knowledge as structured context
   - Incorporates best practices from curated documentation
   - Supports customizable input sources

3. **Multi-Layer Validation (New 2026)**
   - **Schema Validation**: Pydantic models ensure type safety
   - **SQL Validation (Priority 2)**: Syntax, tables, joins, quality patterns (SELECT *, dates, division)
   - **Instruction Quality Scoring (Priority 2)**: 3-dimension scoring (specificity, structure, clarity)
   - **Comprehensive Review (Priority 3)**: 4-dimension quality assessment with overall score
   - **Unity Catalog Validation**: Table and column existence checks
   - **Error handling**: Severity-based issues (critical, high, medium, low, info) with suggestions

4. **Complete API Integration**
   - Full Genie Spaces API support (2026 features)
   - Pagination for large space lists
   - Partial updates (title, description only)
   - Serialized space export (requires CAN EDIT)
   - Parent path for workspace organization
   - Trash (recoverable) vs permanent delete

5. **Configuration Transformation**
   - Automatic conversion to Databricks `serialized_space` format
   - Handles complex nested structures
   - Generates unique IDs for all components
   - Preserves relationships and metadata

### Key Features

#### Configuration Generation Features
- **Multiple LLM Support**: Foundation models and custom endpoints
- **Reasoning Output**: Understand why configurations were chosen
- **Confidence Scoring**: Assess configuration quality
- **Flexible Input**: Markdown requirements documents
- **Structured Output**: Valid JSON matching Genie API schema
- **Markdown-Formatted Instructions**: Auto-generated instructions use markdown for better structure and readability

#### Quality Assurance Features (New 2026)

**Priority 1: Enhanced Prompt Engineering**
- SQL Quality Criteria: 6-point checklist (column refs, joins, aggregations, filters, output)
- Few-Shot Examples: High vs low quality configurations
- Instruction Guidelines: 5 principles for clarity and specificity
- Join Specifications: Explicit relationship documentation
- Domain Knowledge Injection: Structured context from extracted knowledge

**Priority 2: Automated Validation**
- **SQL Validator**: Syntax + table/column + join patterns + quality checks
  - Detects: SELECT *, hard-coded dates, missing tables, incomplete joins, unsafe division
  - Severity levels: critical, high, medium, low, info
  - Actionable suggestions for each issue
- **Instruction Scorer**: 3-dimension quality scoring (0-100 scale)
  - Specificity (40 pts): Concrete column/table names, SQL patterns
  - Structure (30 pts): Markdown headers, lists, code blocks
  - Clarity (30 pts): No vague terms, actionable language
  - Letter grades (A-F) with improvement suggestions

**Priority 3: Domain Intelligence & Comprehensive Review**
- **Domain Extractor**: Extracts from requirements
  - Table relationships (1:1, 1:N, N:1, N:M)
  - Business metrics (formulas, aggregations, KPIs)
  - Common filters (status, dates, boolean flags)
  - Business terminology (glossary, acronyms)
  - Sample queries with context
- **Config Review Agent**: 4-dimension quality assessment
  - SQL Validation Score (35%)
  - Instruction Quality Score (25%)
  - Join Completeness Score (20%)
  - Coverage Score (20%)
  - Overall score (0-100) + pass/fail + detailed issues

**Test Coverage**: 83/83 tests passing
- Priority 1: 7 tests (enhanced prompts, join specs)
- Priority 2: 45 tests (SQL validation + instruction scoring)
- Priority 3: 31 tests (domain extraction + comprehensive review)

#### Space Management Features
- **Create**: New spaces with optional parent folder
- **Read**: Get space details with optional full configuration
- **Update**: Full or partial updates (title, description, config)
- **Delete**: Move to trash (recoverable) or permanent delete
- **List**: Paginated listing of all spaces

#### Developer Experience Features
- **CLI Tools**: Command-line scripts for all operations
- **Python API**: Comprehensive Python client library
- **Examples**: Ready-to-use example scripts
- **Validation**: Setup validation and table/column validation tools
- **Automation**: End-to-end workflow scripts
- **Documentation**: Comprehensive guides and references

### Supported Workflow Patterns

1. **One-Shot Generation + Creation**
   ```bash
   genie.py create --requirements data/requirements.md
   ```

2. **Manual Review + Editing**
   ```bash
   genie.py generate --requirements data/requirements.md  # Generate
   genie.py validate  # Validate (interactive fixes if needed)
   vim output/genie_space_config.json  # Edit if needed
   genie.py deploy  # Deploy
   ```

3. **Programmatic Python API**
   ```python
   from src.genie_space_client import create_genie_space_from_file
   result = create_genie_space_from_file('config.json')
   ```

4. **Iterative Management**
   ```python
   client = GenieSpaceClient()
   client.create_space(config)
   client.list_spaces()
   client.update_space(space_id, title="New Title")
   client.trash_space(space_id)
   ```

## Project Structure

```
.
├── genie.py                        # 🌟 Unified CLI (main entry point)
├── requirements.txt                # Python dependencies
├── .env.example                    # Example environment file
├── README.md                       # User guide
├── ARCHITECTURE.md                 # This file - System architecture
├── CONVERSION_PIPELINE.md          # Requirements conversion guide
├── SIMPLIFIED_WORKFLOW.md          # Simplified workflow details
│
├── src/                            # Core source code
│   ├── __init__.py
│   ├── models.py                   # Pydantic models for Genie space config
│   ├── pipeline/                   # 🌟 Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── generator.py            # Configuration generation (7-step pipeline)
│   │   ├── validator.py            # Unity Catalog table validation
│   │   ├── deployer.py             # Space deployment
│   │   ├── parser.py               # Document parsing (async/concurrent)
│   │   └── reviewer.py             # 🆕 Comprehensive config review (P3)
│   ├── api/                        # API clients
│   │   ├── __init__.py
│   │   └── genie_space_client.py   # Genie Space API client
│   ├── llm/                        # LLM clients
│   │   ├── __init__.py
│   │   └── databricks_llm.py       # Databricks LLM client
│   ├── prompt/                     # Prompt management
│   │   ├── __init__.py
│   │   ├── prompt_builder.py       # 🆕 Prompt construction + domain injection (P1, P3)
│   │   └── templates/              # Prompt templates
│   │       ├── curate_effective_genie.md         # Best practices
│   │       ├── genie_api.md                      # API documentation
│   │       └── guide_prompt_with_reasoning.md    # 🆕 Enhanced prompt (P1)
│   ├── parsing/                    # Requirements parsing
│   │   ├── __init__.py
│   │   ├── pdf_parser.py           # PDF extraction
│   │   ├── markdown_parser.py      # Markdown extraction
│   │   ├── requirements_structurer.py  # Data models & structuring
│   │   ├── llm_enricher.py         # LLM-based enrichment
│   │   └── markdown_generator.py   # Markdown output generation
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       ├── benchmark_extractor.py  # Benchmark extractor (100% FAQ coverage)
│       ├── config_transformer.py   # Config transformation
│       ├── table_validator.py      # Unity Catalog table & column validator
│       ├── sql_validator.py        # 🆕 SQL syntax & quality validator (P2)
│       ├── instruction_scorer.py   # 🆕 Instruction quality scorer (P2)
│       └── domain_extractor.py     # 🆕 Domain knowledge extractor (P3)
│
├── data/                           # Input requirements
│   └── demo_requirements.md        # Example requirements
│
├── output/                         # Generated files (gitignored)
│   ├── genie_space_config.json     # Generated config
│   └── genie_space_result.json     # Creation result
│
├── scripts/                        # Utility scripts
│   ├── validate_setup.py           # Environment validation
│   └── convert_requirements.py     # Requirements conversion
│   # Note: Legacy scripts removed - all functionality migrated to genie.py CLI
│
├── change_logs/                    # 🆕 Quality improvement documentation
│   ├── priority1_improvements_summary.md       # P1: Enhanced prompts
│   ├── priority2_improvements_summary.md       # P2: Validation
│   ├── priority3_improvements_summary.md       # P3: Domain & review
│   ├── comprehensive_improvements_summary.md   # Combined overview
│   ├── FINAL_SUMMARY.md                        # Complete 3-priority summary
│   └── sql_quality_quick_reference.md          # SQL standards reference
│
└── tests/                          # Test suite (83 tests, all passing ✅)
    ├── __init__.py
    ├── test_generation.py          # Generation tests
    ├── test_example_usage.py       # Example usage tests
    ├── test_join_specs.py          # Join specification tests
    ├── test_requirements_converter.py  # Requirements conversion tests
    ├── test_table_validator.py     # Table validator tests
    ├── test_enhanced_generation.py # 🆕 P1: Enhanced prompts (7 tests)
    ├── test_sql_validator.py       # 🆕 P2: SQL validation (22 tests)
    ├── test_instruction_scorer.py  # 🆕 P2: Instruction scoring (23 tests)
    ├── test_domain_extractor.py    # 🆕 P3: Domain extraction (17 tests)
    └── test_reviewer.py            # 🆕 P3: Config review (14 tests)
```

**Key Changes in Structure:**
- 🌟 **genie.py**: Unified CLI (main entry point) that combines parse, generate, validate, and deploy
- 🌟 **src/pipeline/**: Orchestration layer with generator, validator, deployer, and parser modules
  - **parser.py**: New async/concurrent document parsing module with progress tracking
- **src/parsing/**: Complete requirements parsing pipeline (PDF, Markdown, structuring, enrichment)
- **scripts/legacy/**: ⚠️ **REMOVED** - All functionality migrated to `genie.py` CLI

## Output Schema

The generated configuration follows this structure:

```json
{
  "genie_space_config": {
    "space_name": "Your Analytics Space",
    "description": "Natural language querying for your data",
    "purpose": "Enable business users to analyze data",
    "tables": [
      {
        "catalog_name": "your_catalog",
        "schema_name": "your_schema",
        "table_name": "your_table",
        "description": "Table description"
      }
    ],
    "joins": [
      {
        "left_table": "your_catalog.your_schema.table1",
        "left_alias": "table1",
        "right_table": "your_catalog.your_schema.table2",
        "right_alias": "table2",
        "join_condition": "`table1`.`id` = `table2`.`id`",
        "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
      }
    ],
    "instructions": [
      {
        "content": "General instructions for querying..."
      }
    ],
    "example_sql_queries": [
      {
        "question": "Example question",
        "sql_query": "SELECT column FROM ...",
        "description": "Query description"
      }
    ],
    "sql_expressions": [
      {
        "name": "metric_name",
        "expression": "SUM(column)",
        "description": "Metric description",
        "type": "metric"
      }
    ],
    "benchmark_questions": [
      {
        "question": "Test question"
      }
    ],
    "enable_data_sampling": true
  },
  "reasoning": "LLM's explanation for configuration choices...",
  "confidence_score": 0.95
}
```

**Schema Components:**
- **genie_space_config**: Main configuration object
  - **space_name**: Display name for the Genie space
  - **description**: Brief description of the space purpose
  - **purpose**: Detailed explanation of space objectives
  - **tables**: List of Unity Catalog tables to include
  - **joins**: Explicit join specifications between tables
  - **instructions**: Text instructions guiding the AI assistant (supports markdown formatting)
  - **example_sql_queries**: Example questions with SQL answers
  - **sql_expressions**: Reusable metrics, filters, and dimensions
  - **benchmark_questions**: Test questions for validation
  - **enable_data_sampling**: Whether to enable data sampling (boolean)
- **reasoning**: Optional explanation of configuration choices from the LLM
- **confidence_score**: Optional confidence score (0.0-1.0)

**Markdown-Formatted Instructions (New in 2026):**
Instructions now support markdown formatting for better structure and readability:
- Section headings (`##`) organize related instructions
- Bullet lists (`-`) for multiple related points
- **Bold** text for emphasis on critical terms
- Inline `code` for column/table names
- Numbered lists for sequential steps
- Blockquotes (`>`) for clarification questions

This improves instruction clarity and makes configurations more maintainable.

**Transformation:** This user-friendly format is automatically transformed to Databricks' internal `serialized_space` format when creating or updating spaces. See [Configuration Format Transformation](#configuration-format-transformation) for details.

## Component Details

### 1. Input Layer

**Purpose**: Provide comprehensive context for LLM generation

**Components**:
- `src/prompt/templates/curate_effective_genie.md`: Best practices and principles
- `src/prompt/templates/genie_api.md`: API documentation and schema information
- `data/demo_requirements.md`: Actual business requirements

**Format**: Markdown documents with structured information

### 2. Prompt Builder Layer (Enhanced 2026)

**Class**: `PromptBuilder`

**Responsibilities**:
```python
class PromptBuilder:
    def __init__(context_doc, output_doc, input_data):
        # Store document paths

    def _read_file(path) -> str:
        # Read file contents

    def build_prompt() -> str:
        # Build basic prompt

    def build_prompt_with_reasoning(domain_knowledge=None) -> str:
        # 🆕 Build prompt with reasoning + domain knowledge injection (P1, P3)
```

**Process (Enhanced)**:
1. Extract domain knowledge from requirements (P3)
2. Read all input documents
3. Inject domain knowledge as structured context
4. Add SQL quality criteria (P1)
5. Add few-shot examples (P1)
6. Add instruction guidelines (P1)
7. Construct comprehensive prompt
8. Format for optimal LLM comprehension

**Enhanced Prompt Template** (`guide_prompt_with_reasoning.md`):
- **SQL Quality Criteria**: 6-point checklist for correct SQL generation
- **Few-Shot Examples**: High vs low quality configurations
- **Instruction Guidelines**: 5 principles for clear, specific instructions
- **Join Specifications**: Requirements for explicit table relationships
- **Domain Knowledge Context**: Extracted relationships, metrics, filters, terminology

### 3. LLM Client Layer

**Classes**: 
- `DatabricksLLMClient` (for custom endpoints)
- `DatabricksFoundationModelClient` (for foundation models)

**Responsibilities**:
```python
class DatabricksLLMClient:
    def __init__(endpoint_name, host, token):
        # Initialize connection
    
    def _make_request(prompt, max_tokens, temperature):
        # Make API request
    
    def generate(prompt) -> str:
        # Generate raw text
    
    def generate_genie_config(prompt) -> LLMResponse:
        # Generate and parse config
```

**Features**:
- Authentication with Databricks
- Request formatting
- Response parsing
- Error handling
- JSON extraction

### 4. Validation Layer

**Models** (Pydantic):

```python
# Main configuration
GenieSpaceConfig
├── space_name: str
├── description: str
├── purpose: str
├── tables: List[GenieSpaceTable]
│   └── catalog_name, schema_name, table_name
├── instructions: List[GenieSpaceInstruction]
│   └── content, priority
├── example_sql_queries: List[GenieSpaceExampleSQL]
│   └── question, sql_query, description
├── sql_expressions: List[GenieSpaceSQLExpression]
│   └── name, expression, type, description
└── benchmark_questions: List[GenieSpaceBenchmark]
    └── question, expected_sql

# Response wrapper
LLMResponse
├── genie_space_config: GenieSpaceConfig
├── reasoning: Optional[str]
└── confidence_score: Optional[float]
```

**Validation**:
- Type checking (automatic)
- Required field verification
- Data structure validation
- Custom constraints

### 5. Document Parsing Layer

**Module**: `src/pipeline/parser.py`

**Responsibilities**:
```python
async def parse_documents_async(
    input_dir: str,
    output_path: str = "data/parsed_requirements.md",
    llm_model: str = "databricks-gpt-5-2",
    vision_model: str = "databricks-claude-sonnet-4",
    use_llm: bool = True,
    domain: str = "combined",
    databricks_host: Optional[str] = None,
    databricks_token: Optional[str] = None,
    verbose: bool = True,
    max_concurrent_pdfs: int = 3
) -> Dict[str, Any]:
    # Parse PDFs and markdown files into structured requirements
    
def parse_documents(...):
    # Synchronous wrapper for async parsing
```

**Process**:
1. Extract content from PDF files (async/concurrent)
   - Uses vision model for image-based parsing
   - Configurable concurrency (default: 3 concurrent PDFs)
   - Per-page processing (2.21x faster based on benchmarks)
   - Progress bars via `tqdm` for real-time feedback
2. Extract content from Markdown files (regex-based)
3. Structure and combine data using `RequirementsStructurer`
4. Optional LLM enrichment via `LLMEnricher`
5. Generate output markdown via `MarkdownGenerator`

**Features**:
- Async/concurrent PDF processing with semaphore control
- Vision model integration (`databricks-claude-sonnet-4`)
- Real-time progress tracking with `tqdm_asyncio`
- Automatic error handling and recovery
- Supports multiple domain types (social_analytics, kpi_analytics, combined)
- Environment variable support for credentials

**Output**: Structured markdown file containing:
- Questions (categorized by domain)
- Tables with descriptions
- SQL queries with context
- Metadata about extracted content

### 6. Table & Column Validation Layer

**Class**: `TableValidator`

**Responsibilities**:
```python
class TableValidator:
    def __init__(databricks_host, databricks_token):
        # Initialize connection to Unity Catalog
    
    def validate_table(catalog, schema, table) -> bool:
        # Verify table exists
    
    def validate_columns(catalog, schema, table, columns) -> Dict[str, bool]:
        # Verify columns exist in table
    
    def get_table_schema(catalog, schema, table) -> Dict:
        # Fetch table schema from Unity Catalog
    
    def validate_config(config_path) -> ValidationReport:
        # Validate entire configuration
```

**Process**:
1. Parse configuration file
2. Extract table and column references
3. Query Unity Catalog API for table schemas
4. Validate all tables exist and are accessible
5. Validate all columns exist in their tables
6. Generate comprehensive validation report

**Features**:
- Unity Catalog API integration
- Fallback to SQL DESCRIBE TABLE
- Schema caching for performance
- Case-insensitive column matching
- Detailed error reporting
- JSON and human-readable output

**Output**: `ValidationReport`
```python
ValidationReport
├── tables_checked: List[str]
├── tables_valid: List[str]
├── tables_invalid: List[str]
├── columns_checked: Dict[str, List[str]]
├── columns_valid: Dict[str, List[str]]
├── columns_invalid: Dict[str, List[str]]
└── issues: List[ValidationIssue]
    ├── severity: "error" | "warning" | "info"
    ├── type: str
    ├── message: str
    ├── table: Optional[str]
    ├── column: Optional[str]
    └── location: Optional[str]
```

### 7. Instruction Formatting Layer

**Purpose**: Generate well-structured, markdown-formatted instructions for better readability and organization

**Markdown Elements Supported**:

```python
# Section Headings
"## Date and Time Handling"
"## Metric Calculations"
"## Clarification Questions"

# Bullet Lists
"- Always use `event_date` column for date-based queries"
"- Default to **last 30 days** when no time period is specified"

# Bold Emphasis
"**revenue metrics**"
"**last 30 days**"

# Inline Code
"`event_date`"
"`total_revenue`"
"`status != 'cancelled'`"

# Numbered Lists
"1. Use `total_revenue` column (already includes tax)"
"2. Round all monetary values to 2 decimal places"

# Blockquotes (for clarification questions)
"> \"To analyze performance, please specify: (1) time period, (2) product category\""
```

**Example Well-Formatted Instruction**:
```markdown
## Date and Time Handling
- Always use `event_date` column for date-based queries
- Default to **last 30 days** when no time period is specified
- Use `CURRENT_DATE()` for "today" and `DATE_SUB(CURRENT_DATE(), 30)` for "last 30 days"

## Metric Calculations
When calculating **revenue metrics**:
1. Use `total_revenue` column (already includes tax)
2. Round all monetary values to 2 decimal places
3. Filter out cancelled orders using `status != 'cancelled'`

## Clarification Questions
When users ask about performance but don't specify time range or product category, ask:
> "To analyze performance, please specify: (1) time period (e.g., last month, Q1 2024), and (2) product category you want to analyze."
```

### 8. Quality Assurance Layer (New 2026)

This section describes the three-priority quality assurance system that ensures generated configurations are production-ready.

#### 8.1 Domain Knowledge Extractor (Priority 3)

**Class**: `DomainKnowledgeExtractor`
**Module**: `src/utils/domain_extractor.py`

**Purpose**: Extract structured domain knowledge from requirements documents to provide explicit context to the LLM.

**Data Models**:
```python
@dataclass
class TableRelationship:
    left_table: str
    right_table: str
    relationship_type: str  # one-to-one, one-to-many, many-to-one, many-to-many
    join_column_left: Optional[str]
    join_column_right: Optional[str]
    description: Optional[str]

@dataclass
class BusinessMetric:
    name: str
    formula: str
    description: Optional[str]
    sql_expression: Optional[str]
    type: str  # metric, dimension, filter

@dataclass
class CommonFilter:
    name: str
    condition: str
    description: Optional[str]
    examples: List[str]

@dataclass
class DomainKnowledge:
    table_relationships: List[TableRelationship]
    business_metrics: List[BusinessMetric]
    common_filters: List[CommonFilter]
    table_descriptions: Dict[str, str]
    business_terms: Dict[str, str]
    sample_queries: List[Dict[str, str]]
```

**Extraction Patterns**:
- **Table Relationships**: `customers (1) -> orders (N)`, `orders N:1 products`, SQL JOIN clauses
- **Business Metrics**: `ARPU = revenue / customers`, `Revenue: SUM(amount)`, KPI sections
- **Common Filters**: `status != 'cancelled'`, `event_date >= DATE_SUB(CURRENT_DATE(), 30)`
- **Business Terms**: Glossary sections, `**ARPU**: Average Revenue Per User`
- **Sample Queries**: SQL code blocks with associated questions

**Output**: Structured context injected into LLM prompt
```markdown
## Extracted Table Relationships
- **transactions** (many-to-one) **customers**
  - Join: `customer_id` = `customer_id`
  - Each transaction belongs to one customer

## Key Business Metrics
- **ARPU**
  - Formula: `revenue / customers`
  - Average Revenue Per User

## Standard Filters
- **status**: `status != 'cancelled'`
  - Filter out cancelled transactions
```

#### 8.2 SQL Validator (Priority 2)

**Class**: `SQLValidator`
**Module**: `src/utils/sql_validator.py`

**Purpose**: Comprehensive SQL syntax, table/column validation, and quality checking.

**Data Models**:
```python
@dataclass
class ValidationIssue:
    severity: str  # critical, high, medium, low, info
    category: str  # syntax, table, column, join, quality
    message: str
    suggestion: Optional[str]
    location: Optional[str]

@dataclass
class SQLValidationReport:
    is_valid: bool
    tables_referenced: Set[str]
    columns_referenced: Set[str]
    has_explicit_joins: bool
    issues: List[ValidationIssue]
```

**Validation Checks**:
1. **Syntax Validation**: Uses `sqlparse` to check SQL syntax
2. **Table References**: Verifies all tables exist in available tables list
3. **Join Patterns**: Checks for explicit JOIN conditions
4. **Quality Checks**:
   - SELECT * usage (should be avoided)
   - Hard-coded dates (should use CURRENT_DATE, DATE_SUB)
   - Aggregate without GROUP BY
   - Missing GROUP BY columns
   - Unsafe division (should use try_divide or NULLIF)

**Scoring**:
```
Score = 100 - (errors × 10) - (warnings × 2)
```

**Integration**: Validates all SQL in:
- `example_sql_queries`
- `sql_expressions`
- `benchmark_questions` (if they include SQL)

#### 8.3 Instruction Quality Scorer (Priority 2)

**Class**: `InstructionQualityScorer`
**Module**: `src/utils/instruction_scorer.py`

**Purpose**: Score instruction quality across 3 dimensions to ensure clear, specific, well-structured guidance.

**Data Models**:
```python
@dataclass
class InstructionScore:
    specificity_score: float  # 0-40 points
    structure_score: float    # 0-30 points
    clarity_score: float      # 0-30 points
    total_score: float        # 0-100
    issues: List[str]
    suggestions: List[str]

@dataclass
class ConfigInstructionQualityReport:
    average_score: float
    total_instructions: int
    high_quality_count: int    # Score >= 80
    medium_quality_count: int  # 60 <= Score < 80
    low_quality_count: int     # Score < 60
    instruction_scores: List[InstructionScore]
```

**Scoring Dimensions**:

1. **Specificity (40 points)**:
   - Column names (+5 pts each, max 10)
   - Table names (+5 pts each, max 10)
   - SQL keywords (+2 pts each, max 10)
   - Concrete examples (+5 pts each, max 10)

2. **Structure (30 points)**:
   - Markdown headers (+10 pts)
   - Bullet/numbered lists (+10 pts)
   - Code blocks/inline code (+5 pts)
   - Bold emphasis (+5 pts)

3. **Clarity (30 points)**:
   - No vague terms (-5 pts each): "appropriate", "relevant", "properly", "good"
   - Actionable language (+10 pts): imperative verbs
   - Logical flow (+10 pts): sequential organization
   - Clear examples (+10 pts)

**Grade Assignment**:
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Acceptable)
- D: 60-69 (Needs improvement)
- F: 0-59 (Inadequate)

**Priority 1 Requirement**: Instructions marked as `priority: 1` must score ≥80.

#### 8.4 Configuration Review Agent (Priority 3)

**Class**: `ConfigReviewAgent`
**Module**: `src/pipeline/reviewer.py`

**Purpose**: Comprehensive 4-dimension quality assessment of generated configurations before deployment.

**Data Models**:
```python
@dataclass
class ReviewIssue:
    severity: str  # critical, high, medium, low, info
    category: str  # sql, instructions, joins, coverage, structure
    message: str
    suggestion: Optional[str]
    affected_item: Optional[str]

@dataclass
class ConfigReviewReport:
    config_name: str
    overall_score: float  # 0-100
    passed: bool

    # Component scores
    sql_validation_score: float       # 35% weight
    instruction_quality_score: float  # 25% weight
    join_completeness_score: float    # 20% weight
    coverage_score: float             # 20% weight

    # Metrics
    total_sql_queries: int
    valid_sql_queries: int
    total_instructions: int
    high_quality_instructions: int
    documented_joins: int
    total_joins: int  # Expected = N-1 for N tables

    issues: List[ReviewIssue]
```

**Review Dimensions**:

1. **SQL Validation Score (35%)**:
   - Uses `SQLValidator` for all queries
   - Score = 100 - (errors × 10) - (warnings × 2)
   - Threshold: `min_sql_score` (default 70.0)

2. **Instruction Quality Score (25%)**:
   - Uses `InstructionQualityScorer`
   - Average across all instructions
   - Threshold: `min_instruction_score` (default 70.0)
   - Priority 1 instructions must score ≥80

3. **Join Completeness Score (20%)**:
   - Coverage = documented_joins / expected_joins
   - Expected joins = N-1 (minimum spanning tree for N tables)
   - Score = min(coverage × 100, 100)
   - Critical if no joins for multiple tables

4. **Coverage Score (20%)**:
   - Example queries per table (aim: 2-3 per table)
   - Benchmark questions (aim: 10-20)
   - SQL expressions (metrics/dimensions/filters)
   - Score based on thresholds

**Overall Scoring**:
```
Overall = SQL×0.35 + Instructions×0.25 + Joins×0.20 + Coverage×0.20
```

**Pass/Fail Logic**:
- Critical issues → Fail
- Overall score < 60 → Fail
- Otherwise → Pass

**Output Report**:
```
Configuration Review Report: Fashion Retail Analytics
============================================================
Overall Status: ✅ PASSED
Overall Score: 78.5/100

Component Scores:
  - SQL Validation: 85.0/100
  - Instruction Quality: 72.0/100
  - Join Completeness: 100.0/100
  - Coverage: 65.0/100

Issues Found:
  - Critical: 0
  - High: 1
  - Medium: 3
  - Low: 2
```

**Benefits**:
- **Better Organization**: Section headings group related instructions
- **Enhanced Readability**: Lists and formatting make instructions scannable
- **Clear Emphasis**: Bold text highlights critical terms
- **Code Clarity**: Inline code distinguishes column/table names from prose
- **Easier Maintenance**: Structured format is easier to update
- **Professional Appearance**: Consistent formatting across configurations

**Implementation**:
- Template files (`guide_prompt.md`, `guide_prompt_with_reasoning.md`) now include markdown formatting guidance
- LLM automatically generates markdown-formatted instructions
- No manual formatting required from users

### 8. Output Layer

**Format**: JSON file with validated configuration

**Structure**:
```json
{
  "genie_space_config": {
    "space_name": "Fashion Retail Analytics",
    "description": "Natural language querying...",
    "purpose": "Enable business users...",
    "tables": [...],
    "instructions": [...],  // Now with markdown formatting
    "example_sql_queries": [...],
    "sql_expressions": [...],
    "benchmark_questions": [...]
  },
  "reasoning": "The configuration focuses on...",
  "confidence_score": 0.95
}
```

## Data Flow Diagram

### Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER ENTRY POINTS                         │
├─────────────────────────────────────────────────────────────────┤
│  1. genie.py create (Automated - Full Pipeline)                 │
│  2. genie.py parse (Document Parsing)                           │
│  3. genie.py generate (Config Generation)                       │
│  4. genie.py validate (Table Validation)                        │
│  5. genie.py deploy (Space Deployment)                          │
│  6. examples/create_genie_space_example.py (Python API)         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: CONFIG GENERATION                    │
└─────────────────────────────────────────────────────────────────┘

genie.py (CLI Entry Point)
    │
    ├─── Load environment (.env file)
    ├─── Parse command-line arguments
    │    • Command: parse, create, generate, validate, deploy
    │    • --model, --endpoint
    │    • --requirements, --config, --output
    │    • --max-tokens, --temperature
    │    • --max-concurrent (for parse)
    │
    └─── Route to appropriate pipeline function
            │
            ▼

STEP 1: 🆕 Domain Knowledge Extraction (P3)
────────────────────────────────────────────
DomainKnowledgeExtractor.extract_from_file()
    ├─── Extract table relationships (1:1, 1:N, N:1, N:M)
    ├─── Extract business metrics (formulas, KPIs)
    ├─── Extract common filters
    ├─── Extract business terminology
    └─── Return DomainKnowledge object
            │
            ▼

STEP 2: 🆕 Enhanced Prompt Building (P1 + P3)
─────────────────────────────────────────────
PromptBuilder.build_prompt_with_reasoning(domain_knowledge)
    │
    ├─── Read src/prompt/templates/curate_effective_genie.md
    │        (Best practices, principles, guidelines)
    │
    ├─── Read src/prompt/templates/genie_api.md
    │        (API schema, output format, examples)
    │
    ├─── Read data/demo_requirements.md
    │        (Business requirements, tables, questions)
    │
    ├─── 🆕 Inject extracted domain knowledge as structured context
    │
    └─── Construct enhanced prompt with:
            • 🆕 SQL Quality Criteria (6-point checklist)
            • 🆕 Few-Shot Examples (high vs low quality)
            • 🆕 Instruction Guidelines (5 principles)
            • 🆕 Join Specification Requirements
            • Context section (best practices)
            • Output format section (schema)
            • Input section (enhanced requirements)
            │
            ▼

STEP 3: LLM Generation
──────────────────────

DatabricksFoundationModelClient.generate_genie_config()
    │
    ├─── Format request payload
    │       {
    │         "messages": [{"role": "user", "content": prompt}],
    │         "max_tokens": 16000,  # Higher for reasoning models
    │         "temperature": 0.1
    │       }
    │
    ├─── POST to serving endpoint
    │       https://{host}/serving-endpoints/{model}/invocations
    │       Models: databricks-gpt-5-2, llama-3-1-70b, etc.
    │
    ├─── Receive response
    │       {
    │         "choices": [{
    │           "message": {
    │             "content": "{ genie_space_config: {...}, reasoning: ..., confidence_score: ... }"
    │           }
    │         }]
    │       }
    │
    └─── Extract and clean JSON content
            • Find JSON boundaries { ... }
            • Remove markdown code blocks if present
            │
            ▼

Pydantic Validation (src/models.py)
    │
    ├─── Parse JSON string
    ├─── Validate against LLMResponse schema
    │    ├─── genie_space_config: GenieSpaceConfig
    │    │    ├─── space_name, description, purpose
    │    │    ├─── tables: List[GenieSpaceTable]
    │    │    ├─── instructions: List[GenieSpaceInstruction]
    │    │    ├─── example_sql_queries: List[GenieSpaceExampleSQL]
    │    │    ├─── sql_expressions: List[GenieSpaceSQLExpression]
    │    │    └─── benchmark_questions: List[GenieSpaceBenchmark]
    │    ├─── reasoning: Optional[str]
    │    └─── confidence_score: Optional[float]
    │
    ├─── Type check all fields
    ├─── Verify required fields
    ├─── Apply field constraints
    │
    └─── Create validated LLMResponse object
            │
            ▼

STEP 4: Benchmark Extraction (Existing)
───────────────────────────────────────
BenchmarkExtractor.extract_all_benchmarks()
    ├─── Extract FAQ questions (100% coverage)
    ├─── Extract sample queries from requirements
    └─── Merge into configuration
            │
            ▼

STEP 5: 🆕 SQL & Instruction Validation (P2)
────────────────────────────────────────────
SQLValidator.validate_config_sql()
    ├─── Validate example SQL queries
    ├─── Validate SQL expressions
    ├─── Check: syntax, tables, joins, quality patterns
    └─── Generate SQL validation report

InstructionQualityScorer.score_config_instructions()
    ├─── Score each instruction (0-100)
    ├─── Check: specificity, structure, clarity
    └─── Generate instruction quality report
            │
            ▼

STEP 6: 🆕 Comprehensive Config Review (P3)
───────────────────────────────────────────
ConfigReviewAgent.review_config()
    ├─── SQL Validation Score (35%)
    ├─── Instruction Quality Score (25%)
    ├─── Join Completeness Score (20%)
    ├─── Coverage Score (20%)
    ├─── Overall Score = weighted sum
    └─── Generate review report with pass/fail + issues
            │
            ▼

STEP 7: Save Configuration & Reports
────────────────────────────────────
    ├─── Convert to JSON (model.model_dump())
    ├─── Save output/genie_space_config.json
    ├─── Save output/validation_report.json (if requested)
    └─── Save output/review_report.json (if requested)
            │
            ▼

┌─────────────────────────────────────────────────────────────────┐
│          PHASE 2: TABLE & COLUMN VALIDATION (RECOMMENDED)        │
└─────────────────────────────────────────────────────────────────┘

genie.py validate (or src.pipeline.validator)
    │
    ├─── Load configuration from JSON file
    │       output/genie_space_config.json
    │
    ├─── Initialize TableValidator
    │       • Load credentials from .env
    │       • Set up Unity Catalog connection
    │
    └─── Validate configuration
            │
            ▼

TableValidator.validate_config()
    │
    ├─── Parse configuration
    │    • Extract table definitions
    │    • Extract SQL expressions
    │    • Extract example queries
    │
    ├─── Validate tables
    │    For each table:
    │       GET /api/2.1/unity-catalog/tables/{catalog}.{schema}.{table}
    │       or fallback: DESCRIBE TABLE {catalog}.{schema}.{table}
    │       └─── Cache schema for performance
    │
    ├─── Extract and validate columns
    │    • Parse SQL expressions for column references
    │    • Build alias map (t → transactions, a → articles, etc.)
    │    • Verify columns exist in table schemas
    │    • Check case-insensitively
    │
    └─── Generate ValidationReport
            • tables_valid / tables_invalid
            • columns_valid / columns_invalid
            • issues (errors, warnings, info)
            │
            ▼

Review Validation Report
    │
    ├─── If errors found:
    │       • Fix table/column references
    │       • Update configuration
    │       • Re-run validation
    │
    └─── If validation passes:
            │
            ▼

┌─────────────────────────────────────────────────────────────────┐
│             PHASE 3: GENIE SPACE CREATION                        │
└─────────────────────────────────────────────────────────────────┘

genie.py deploy (or src.pipeline.deployer)
    │
    ├─── Load configuration from JSON file
    │       output/genie_space_config.json
    │
    ├─── Initialize GenieSpaceClient
    │       • Load credentials from .env
    │       • Set up API connection
    │
    └─── Create space
            │
            ▼

GenieSpaceClient.create_space()
    │
    ├─── Validate configuration
    │    • Check warehouse_id is set
    │    • Extract space_name, description
    │
    ├─── Transform configuration
    │       config_transformer.transform_to_serialized_space()
    │       │
    │       ├─── Convert text fields to arrays of strings
    │       ├─── Nest instructions into sub-sections:
    │       │    • text_instructions
    │       │    • join_specs
    │       │    • example_question_sqls
    │       ├─── Generate unique IDs for all items
    │       ├─── Sort tables by identifier
    │       └─── Format joins with relationship types
    │
    ├─── Build API payload
    │       {
    │         "warehouse_id": "...",
    │         "title": "...",
    │         "description": "...",
    │         "serialized_space": "{ JSON string }",
    │         "parent_path": "/Workspace/..." (optional)
    │       }
    │
    ├─── POST to Genie Spaces API
    │       POST /api/2.0/genie/spaces
    │       Headers: Authorization: Bearer {token}
    │
    └─── Receive response
            {
              "space_id": "01f0f7a0f1571de6bfd79fa6...",
              "space_name": "...",
              "warehouse_id": "...",
              ...
            }
            │
            ▼

Save Creation Result
    │
    ├─── Extract space_id from response
    ├─── Generate space_url
    │       https://{host}/genie/spaces/{space_id}
    │
    └─── Write to output/genie_space_result.json
            {
              "space_id": "...",
              "space_url": "...",
              "response": { full API response }
            }
            │
            ▼

┌─────────────────────────────────────────────────────────────────┐
│                    GENIE SPACE READY TO USE                      │
│                                                                  │
│  • Accessible via Databricks UI                                  │
│  • Ready for natural language queries                            │
│  • Can be updated via API                                        │
│  • Can be managed via GenieSpaceClient                           │
└─────────────────────────────────────────────────────────────────┘
```

### Alternative Workflows

#### Workflow A: Automated End-to-End (Unified CLI)

```
genie.py create --requirements data/requirements.md
    │
    ├─── Step 1: Generate config (src.pipeline.generate_config)
    │       └─── Output: genie_space_config.json
    │
    ├─── Step 2: Validate (src.pipeline.validate_config)
    │       └─── Interactive catalog/schema replacement if needed
    │
    └─── Step 3: Deploy (src.pipeline.deploy_space)
            └─── Output: genie_space_result.json + Space URL
```

#### Workflow B: Python API Usage

```
examples/create_genie_space_example.py
    │
    ├─── Load configuration from file
    ├─── create_genie_space_from_file()
    │       └─── GenieSpaceClient methods
    │
    └─── Display space_id and space_url
```

#### Workflow C: Iterative Management

```
1. Create space
   └─── GenieSpaceClient.create_space()

2. List all spaces (with pagination)
   └─── GenieSpaceClient.list_spaces()

3. Get space details (with full config)
   └─── GenieSpaceClient.get_space(include_serialized_space=True)

4. Update space (partial or full)
   └─── GenieSpaceClient.update_space()

5. Move to trash (recoverable)
   └─── GenieSpaceClient.trash_space()
```

## Module Dependency Graph

```
genie.py (Unified CLI)
    │
    ├── Command: parse
    │   └── src.pipeline.parser
    │       ├── parse_documents() / parse_documents_async()
    │       ├── src.parsing.pdf_parser (PDFParser)
    │       ├── src.parsing.markdown_parser (MarkdownParser)
    │       ├── src.parsing.requirements_structurer
    │       ├── src.parsing.llm_enricher (LLMEnricher)
    │       └── src.parsing.markdown_generator
    │           └── Uses: aiohttp, tqdm, pdfplumber
    │
    ├── Command: generate
    │   └── src.pipeline.generator
    │       ├── generate_config()
    │       ├── src.prompt.prompt_builder (PromptBuilder)
    │       ├── src.llm.databricks_llm (DatabricksFoundationModelClient)
    │       ├── src.utils.benchmark_extractor
    │       └── src.models (Pydantic models)
    │           └── Uses: pydantic, requests
    │
    ├── Command: validate
    │   └── src.pipeline.validator
    │       ├── validate_config()
    │       └── src.utils.table_validator (TableValidator)
    │           └── Uses: requests, Unity Catalog API
    │
    ├── Command: deploy
    │   └── src.pipeline.deployer
    │       ├── deploy_space()
    │       ├── src.api.genie_space_client (GenieSpaceClient)
    │       └── src.utils.config_transformer
    │
    └── Command: create (combines all above)
        ├── generate_config()
        ├── validate_config()
        └── deploy_space()

examples/create_genie_space_example.py (Usage Examples)
    │
    └── src.api.genie_space_client
            ├── create_genie_space_from_file()
            ├── GenieSpaceClient
            │   ├── create_space()
            │   ├── get_space()
            │   ├── list_spaces()
            │   ├── update_space()
            │   └── trash_space()
            └── Uses: all client methods with examples

scripts/validate_setup.py (Setup Validation)
    └── Validates: environment variables, credentials, connectivity

scripts/convert_requirements.py (Requirements Conversion)
    └── src.parsing modules for document conversion
```

## Error Handling Flow

```
Try:
    ┌─────────────────────────┐
    │  Read Input Files       │
    └─────────────────────────┘
              │
              ├─ FileNotFoundError → "Input file missing"
              │
              ▼
    ┌─────────────────────────┐
    │  Build Prompt           │
    └─────────────────────────┘
              │
              ├─ ValueError → "Invalid document format"
              │
              ▼
    ┌─────────────────────────┐
    │  Call LLM API           │
    └─────────────────────────┘
              │
              ├─ ConnectionError → "Cannot reach endpoint"
              ├─ AuthenticationError → "Invalid credentials"
              ├─ TimeoutError → "Request timed out"
              │
              ▼
    ┌─────────────────────────┐
    │  Parse Response         │
    └─────────────────────────┘
              │
              ├─ JSONDecodeError → "Invalid JSON response"
              ├─ ValueError → "No JSON found in response"
              │
              ▼
    ┌─────────────────────────┐
    │  Validate with Pydantic │
    └─────────────────────────┘
              │
              ├─ ValidationError → "Schema mismatch"
              ├─ TypeError → "Type error"
              │
              ▼
    ┌─────────────────────────┐
    │  Save Output            │
    └─────────────────────────┘
              │
              ├─ PermissionError → "Cannot write to output"
              │
              ▼
         Success!
```

## Configuration Options

### Runtime Configuration

```python
# Model selection
--endpoint my-endpoint      # Use custom endpoint
--model llama-3-1-70b       # Use foundation model

# Input/Output
--input-data path/to/req.md # Input requirements
--output path/to/output.json # Output location

# Generation parameters
--max-tokens 4000           # Max response tokens
--temperature 0.1           # Sampling temperature (0.0-1.0)
--no-reasoning              # Skip reasoning output

# Authentication
--databricks-host https://... # Databricks workspace URL
--databricks-token dapi...    # Personal access token
```

### Environment Variables

```bash
export DATABRICKS_HOST="https://workspace.databricks.com"
export DATABRICKS_TOKEN="dapi1234..."
```

## Performance Characteristics

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| Prompt Length | 40-50 KB | Depends on input doc sizes |
| Request Time | 30-60 seconds | Model-dependent |
| Token Usage | 3000-4000 | For generation |
| Output Size | 10-50 KB | JSON configuration |
| Memory Usage | < 100 MB | Lightweight |
| Concurrent Requests | 1 | Sequential by design |

## Security Considerations

1. **Credentials**: Never commit tokens to git
2. **Environment Variables**: Use for sensitive data
3. **Output**: Review before sharing (may contain schema info)
4. **API Rate Limits**: Respect Databricks quotas
5. **Data Privacy**: Input docs may contain sensitive info

## Scripts and Utilities

### 1. Unified CLI (`genie.py`)

**Purpose**: Single entry point for all Genie space operations

**Available Commands**:
- `parse` - Parse documents into structured requirements
- `create` - Full pipeline (generate → validate → deploy)
- `generate` - Generate configuration only
- `validate` - Validate tables and columns
- `deploy` - Deploy existing configuration

**Key Features**:
- Unified interface for all operations
- Built-in progress indicators
- Interactive catalog/schema replacement
- Automatic benchmark extraction
- Environment variable support
- Error handling with helpful messages

**Usage**:
```bash
# Parse documents
genie.py parse --input-dir docs/ --output data/requirements.md --max-concurrent 5

# Complete workflow (recommended)
genie.py create --requirements data/requirements.md

# Individual steps
genie.py generate --requirements data/requirements.md
genie.py validate --config output/genie_space_config.json
genie.py deploy --config output/genie_space_config.json
```

### 2. Setup Validation Script (`scripts/validate_setup.py`)

**Purpose**: Validate environment setup and connectivity

**Checks**:
- Environment variables
- Databricks credentials
- API connectivity
- Python dependencies

**Usage**:
```bash
python scripts/validate_setup.py
```

### 3. Genie Space Usage Examples (`examples/create_genie_space_example.py`)

**Purpose**: Demonstrate Python API usage patterns

**Examples Include**:
- `example_create_space_from_file()`: Create space from JSON file
- `example_create_space_programmatic()`: Create space with Python API
- `example_list_spaces()`: List all Genie spaces
- `example_list_spaces_paginated()`: List spaces with pagination
- `example_update_space()`: Update entire space configuration
- `example_update_space_partial()`: Update only specific fields
- `example_get_space_with_serialization()`: Get space with full config
- `example_trash_space()`: Move space to trash
- `example_create_space_with_parent_path()`: Create space in specific folder

**Usage**:
```python
from examples.create_genie_space_example import example_create_space_from_file

# Create space from configuration file
result = example_create_space_from_file()
print(f"Space URL: {result['space_url']}")
```

---

## Legacy Scripts (Removed)

The following scripts have been **removed** and their functionality migrated to the unified `genie.py` CLI:

| Removed Script | Replacement | Notes |
|----------------|-------------|-------|
| `scripts/legacy/main.py` | `genie.py generate` | Basic config generation |
| `scripts/legacy/generate_config_with_direct_benchmarks.py` | `genie.py generate` | Benchmark extraction now built-in |
| `scripts/legacy/validate_tables.py` | `genie.py validate` | Interactive catalog/schema replacement added |
| `scripts/legacy/create_genie_space.py` | `genie.py deploy` | Same functionality |
| `scripts/legacy/create_genie_space_workflow.sh` | `genie.py create` | Complete pipeline in single command |
| `scripts/legacy/update_benchmarks.py` | Built into `genie.py generate` | Automatic benchmark extraction |
| `scripts/legacy/fix_benchmarks.sh` | Built into `genie.py generate` | No longer needed |

**Migration Path**: Replace all `scripts/legacy/` calls with the corresponding `genie.py` command. See [README.md](README.md) for detailed migration examples.

## Extension Points

To extend the system:

1. **Add new input sources**
   - Modify `PromptBuilder` to support additional docs
   - Add new sections to prompt template

2. **Support new LLM providers**
   - Subclass `DatabricksLLMClient`
   - Implement provider-specific request/response handling

3. **Add new output formats**
   - Create new Pydantic models
   - Add conversion methods

4. **Enhance validation**
   - Add custom validators to Pydantic models
   - Implement business rule checks

5. **Add post-processing**
   - Create pipeline after validation
   - Transform, enrich, or validate further

6. **Custom scripts**
   - Create new scripts in `scripts/` directory
   - Follow existing patterns for error handling and logging

## Testing Strategy

```
Unit Tests
├── test_models.py
│   ├── Test Pydantic validation
│   ├── Test JSON serialization
│   └── Test edge cases
│
├── test_prompt_builder.py
│   ├── Test file reading
│   ├── Test prompt construction
│   └── Test template rendering
│
└── test_llm_client.py
    ├── Test request formatting
    ├── Test response parsing
    └── Test error handling

Integration Tests
├── test_end_to_end.py
│   ├── Test full pipeline
│   ├── Test with mock LLM
│   └── Test output validation
│
└── tests/
    └── test_generation.py (current)
        ├── Test file structure
        ├── Test model validation
        └── Test prompt building
```

## Monitoring and Debugging

### Logging Points

```python
# In genie.py / pipeline modules
log.info("Building prompt...")
log.info(f"Prompt length: {len(prompt)}")
log.info("Calling LLM...")
log.info("Configuration generated")
log.info(f"Saved to: {output_path}")

# In databricks_llm.py
log.debug(f"Request: {payload}")
log.debug(f"Response: {response}")
log.error(f"API error: {e}")

# In prompt_builder.py
log.debug(f"Read {len(content)} chars from {path}")
```

### Debug Mode

Add `--debug` flag to enable:
- Full request/response logging
- Intermediate prompt states
- Validation details
- Timing information

## Deployment Options

### Local Development
```bash
genie.py create --requirements data/requirements.md
```

### Automated Workflow
```bash
# Generate config and create space in one command
genie.py create \
  --requirements data/demo_requirements.md \
  --model databricks-gpt-5-2 \
  --max-tokens 16000
```

### Scheduled Job
```bash
# Run as a Python task in Databricks Job
genie.py create \
  --requirements /dbfs/requirements.md \
  --model databricks-gpt-5-2 \
  --output /dbfs/output/config.json
```

### API Endpoint
Wrap in FastAPI or Flask for HTTP endpoint

### CI/CD Pipeline
Integrate into automated workflow

---

## Genie Space API Integration

After the LLM generates the Genie space configuration, you can use the Genie Space API to create or update actual Genie spaces in Databricks.

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION GENERATION                        │
│  (genie.py generate → LLM → genie_space_config.json)               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CONFIG TRANSFORMATION LAYER                        │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  config_transformer.py                                        │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │ transform_to_serialized_space()                         │ │ │
│  │  │                                                         │ │ │
│  │  │ Input:  User-friendly config format                    │ │ │
│  │  │ Output: Databricks serialized_space format             │ │ │
│  │  │                                                         │ │ │
│  │  │ Transformations:                                        │ │ │
│  │  │ • Convert strings to arrays of strings                 │ │ │
│  │  │ • Nest instructions properly                           │ │ │
│  │  │ • Generate unique IDs                                  │ │ │
│  │  │ • Sort tables by identifier                            │ │ │
│  │  │ • Format joins with relationship types                 │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GENIE SPACE API LAYER                            │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  GenieSpaceClient (genie_space_client.py)                    │ │
│  │                                                               │ │
│  │  Core Methods:                                                │ │
│  │  • create_space(config, parent_path=None)                    │ │
│  │    → Create new Genie space with optional folder path        │ │
│  │  • get_space(space_id, include_serialized_space=False)       │ │
│  │    → Fetch space (optionally with full config)               │ │
│  │  • list_spaces(page_size=None, page_token=None)              │ │
│  │    → List all spaces with pagination support                 │ │
│  │  • update_space(space_id, config=None, ...)                  │ │
│  │    → Update space (full or partial update)                   │ │
│  │  • trash_space(space_id)                                     │ │
│  │    → Move space to trash (recoverable)                       │ │
│  │  • get_space_url(space_id)                                   │ │
│  │    → Get UI URL for accessing space                          │ │
│  │                                                               │ │
│  │  Helper Functions:                                            │ │
│  │  • create_genie_space_from_file(config_path)                 │ │
│  │    → Convenience function for file-based creation            │ │
│  │                                                               │ │
│  │  API Endpoints:                                               │ │
│  │  POST   /api/2.0/genie/spaces                                │ │
│  │  GET    /api/2.0/genie/spaces                                │ │
│  │  GET    /api/2.0/genie/spaces/{space_id}                     │ │
│  │  PATCH  /api/2.0/genie/spaces/{space_id}                     │ │
│  │  DELETE /api/2.0/genie/spaces/{space_id}                     │ │
│  │                                                               │ │
│  │  Features (2026 API):                                         │ │
│  │  ✓ Pagination for large space lists                          │ │
│  │  ✓ Partial updates (title, description only)                 │ │
│  │  ✓ Serialized space export (requires CAN EDIT)               │ │
│  │  ✓ Parent path for workspace organization                    │ │
│  │  ✓ Trash (recoverable) vs permanent delete                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABRICKS GENIE SPACE                            │
│                                                                      │
│  • Space created/updated in workspace                                │
│  • Accessible via Databricks UI                                      │
│  • Ready for natural language queries                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Configuration Format Transformation

The system transforms between two formats:

#### User-Friendly Config (Generated by LLM)

```json
{
  "genie_space_config": {
    "space_name": "My Space",
    "tables": [...],
    "joins": [
      {
        "left_table": "catalog.schema.fact",
        "left_alias": "fact",
        "right_table": "catalog.schema.dim",
        "right_alias": "dim",
        "join_condition": "`fact`.`id` = `dim`.`id`",
        "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
      }
    ],
    "instructions": [
      {"content": "Use safe division..."}
    ],
    "example_sql_queries": [
      {
        "question": "Show revenue by category",
        "sql_query": "SELECT category, SUM(revenue)..."
      }
    ]
  }
}
```

#### Databricks Serialized Space Format

```json
{
  "version": 2,
  "data_sources": {
    "tables": [...]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "abc123...",
        "content": ["Use safe division...\n"]
      }
    ],
    "join_specs": [
      {
        "id": "def456...",
        "left": {"identifier": "...", "alias": "..."},
        "right": {"identifier": "...", "alias": "..."},
        "sql": [
          "`fact`.`id` = `dim`.`id`",
          "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
        ]
      }
    ],
    "example_question_sqls": [
      {
        "id": "ghi789...",
        "question": ["Show revenue by category\n"],
        "sql": ["SELECT category, SUM(revenue)...\n"]
      }
    ]
  },
  "benchmarks": {
    "questions": [...]
  }
}
```

### Key Transformation Rules

1. **All text fields become arrays of strings**
   - Single strings are split preserving newlines
   - Example: `"Hello\nWorld"` → `["Hello\n", "World\n"]`

2. **Instructions are nested**
   - `instructions` → `instructions.text_instructions`
   - `joins` → `instructions.join_specs`
   - `example_sql_queries` → `instructions.example_question_sqls`

3. **IDs are auto-generated**
   - Each instruction, join, and example gets a 24-char hex ID
   - Format: `01f0f7a0f1571de6bfd79fa6`

4. **Tables are sorted**
   - Sorted by identifier for consistency
   - Required by Databricks API

5. **Benchmarks are separate**
   - Not nested in `instructions`
   - Located at top-level `benchmarks.questions`

### Usage Examples

#### Creating a Genie Space

```python
from src.genie_space_client import GenieSpaceClient
import json

# Load the LLM-generated config
with open("output/genie_space_config.json") as f:
    config = json.load(f)

# Initialize client (reads from .env)
client = GenieSpaceClient()

# Create the space
response = client.create_space(
    config=config["genie_space_config"],
    parent_path="/Workspace/Users/me/genie_spaces"
)

print(f"Space ID: {response['space_id']}")
print(f"Space URL: {client.get_space_url(response['space_id'])}")
```

#### Updating a Genie Space

```python
# Update existing space
response = client.update_space(
    space_id="01f0f7a0f1571de6bfd79fa63ed872aa",
    config=updated_config
)
```

#### Fetching Space Configuration

```python
# Get space with full configuration
space_data = client.get_space(
    space_id="01f0f7a0f1571de6bfd79fa63ed872aa",
    include_serialized_space=True
)

# Parse the serialized_space
import json
serialized = json.loads(space_data["serialized_space"])
print(f"Tables: {len(serialized['data_sources']['tables'])}")
```

### API Request Flow

```
1. Client loads config from JSON
   ↓
2. GenieSpaceClient.create_space(config)
   ↓
3. config_transformer.transform_to_serialized_space(config)
   ↓
4. Build API payload:
   {
     "warehouse_id": "...",
     "title": "...",
     "description": "...",
     "serialized_space": "..." (JSON string)
   }
   ↓
5. POST to /api/2.0/genie/spaces
   ↓
6. Databricks creates Genie space
   ↓
7. Return space_id and metadata
```

### Environment Configuration

```bash
# .env file
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

### Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `warehouse_id is required` | Missing or placeholder warehouse ID | Update config with valid warehouse ID |
| `Invalid table identifier` | Malformed table name | Check catalog.schema.table format |
| `Authentication failed` | Invalid token | Verify DATABRICKS_TOKEN in .env |
| `Permission denied` | Insufficient permissions | Ensure CAN EDIT permission on space |
| `Table not found` | Table doesn't exist | Verify table exists in Unity Catalog |

### Complete Workflow Examples

#### Option 1: Automated Workflow (Recommended)

```bash
# Single command for end-to-end generation and creation
genie.py create --requirements data/demo_requirements.md

# With custom options
genie.py create \
  --requirements data/demo_requirements.md \
  --model databricks-gpt-5-2 \
  --max-tokens 16000 \
  --temperature 0.1 \
  --parent-path /Workspace/Users/your.email@domain.com/genie_spaces

# Output:
# - output/genie_space_config.json (generated config)
# - output/genie_space_result.json (space ID and URL)
```

#### Option 2: Manual Step-by-Step (For More Control)

```bash
# 1. Validate setup (optional but recommended)
python scripts/validate_setup.py

# 2. Parse documents if needed (async/concurrent with progress bars)
genie.py parse \
  --input-dir real_requirements \
  --output data/my_requirements.md \
  --max-concurrent 5

# 3. Generate config with LLM
genie.py generate \
  --requirements data/my_requirements.md \
  --model databricks-gpt-5-2 \
  --output output/genie_space_config.json

# 4. Validate tables and columns (RECOMMENDED)
genie.py validate --config output/genie_space_config.json
# Interactive prompts for catalog/schema replacement if validation fails

# 5. Review generated config
cat output/genie_space_config.json

# 6. (Optional) Edit warehouse_id, fix validation errors, etc.
vim output/genie_space_config.json

# 7. Re-validate if edited
genie.py validate --config output/genie_space_config.json

# 8. Deploy Genie space
genie.py deploy --config output/genie_space_config.json

# 9. Access your Genie space
# Space URL is printed and saved in output/genie_space_result.json
```

#### Option 3: Python API

```python
from src.genie_space_client import create_genie_space_from_file

# Create space from configuration file
result = create_genie_space_from_file('output/genie_space_config.json')
print(f'Space created: {result["space_url"]}')
print(f'Space ID: {result["space_id"]}')
```

#### Option 4: Direct API Call (curl)

```bash
# Transform config to serialized format
python -c "
from src.config_transformer import load_and_transform_config
import json

config, serialized = load_and_transform_config('output/genie_space_config.json')
payload = {
    'warehouse_id': config.get('warehouse_id'),
    'title': config.get('space_name'),
    'description': config.get('description'),
    'serialized_space': serialized
}
print(json.dumps(payload, indent=2))
" > payload.json

# Create space via API
curl -X POST https://workspace.cloud.databricks.com/api/2.0/genie/spaces \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### Testing Transformations

```python
# Test the transformation
from src.config_transformer import transform_to_serialized_space
import json

config = {...}  # Your config
serialized = transform_to_serialized_space(config)
parsed = json.loads(serialized)

# Verify structure
assert parsed["version"] == 2
assert "data_sources" in parsed
assert "instructions" in parsed
assert "text_instructions" in parsed["instructions"]
assert "join_specs" in parsed["instructions"]
assert "example_question_sqls" in parsed["instructions"]
```

## Best Practices and Design Principles

### Configuration Generation Best Practices

1. **Start Small and Focused**
   - Begin with 3-5 core tables
   - Focus on a specific business domain
   - Expand incrementally based on feedback

2. **Use High-Quality Requirements**
   - Provide clear business context
   - Include specific example questions
   - Document table relationships
   - Specify metrics and dimensions

3. **Leverage Reasoning Models**
   - Use models like `databricks-gpt-5-2` for complex configurations
   - Increase `max_tokens` to 16000+ for reasoning models
   - Review reasoning output to understand configuration choices

4. **Iterate and Refine**
   - Generate multiple configurations with different temperatures
   - Review and edit generated configurations
   - Test with benchmark questions
   - Update requirements based on results

5. **Use Markdown-Formatted Instructions** (New in 2026)
   - LLM automatically generates well-structured instructions using markdown
   - Section headings (`##`) organize related instructions by topic
   - Bullet lists (`-`) group related rules and guidelines
   - **Bold text** emphasizes critical terms and actions
   - Inline `code` highlights column names, table names, and SQL keywords
   - Numbered lists show sequential steps or priorities
   - Blockquotes (`>`) format clarification questions
   - Benefits: Improved readability, easier maintenance, better organization

### Space Management Best Practices

1. **Validate Before Creation**
   - Run `python scripts/validate_setup.py` to check environment
   - **Run `genie.py validate` to verify tables and columns** (CRITICAL)
   - Verify `warehouse_id` is valid
   - Ensure all tables exist in Unity Catalog
   - Review generated configuration manually

2. **Table & Column Validation** (NEW)
   - Always validate before creating spaces
   - Fix errors (not warnings) before creation
   - Re-validate after editing configuration
   - Use `--json` flag for CI/CD integration
   - Review validation reports in detail

3. **Use Parent Paths for Organization**
   ```python
   client.create_space(
       config,
       parent_path="/Workspace/Users/your.email@domain.com/genie_spaces"
   )
   ```

4. **Implement Version Control**
   - Store configurations in git
   - Track changes to requirements documents
   - Maintain history of generated configs
   - Document reasoning for configuration choices
   - Save validation reports for audit trail

5. **Test Before Deployment**
   - Use benchmark questions to validate
   - Test common user queries
   - Verify table joins work correctly
   - Check metric calculations

### API Usage Best Practices

1. **Use Pagination for Large Lists**
   ```python
   page_token = None
   all_spaces = []
   while True:
       result = client.list_spaces(page_size=100, page_token=page_token)
       all_spaces.extend(result.get('spaces', []))
       page_token = result.get('next_page_token')
       if not page_token:
           break
   ```

2. **Prefer Partial Updates**
   ```python
   # Update only title without changing config
   client.update_space(space_id, title="New Title")
   ```

3. **Export Before Major Changes**
   ```python
   # Get full configuration before updating
   backup = client.get_space(space_id, include_serialized_space=True)
   with open('backup.json', 'w') as f:
       json.dump(backup, f)
   ```

4. **Use Trash Instead of Permanent Delete**
   ```python
   # Move to trash (recoverable)
   client.trash_space(space_id)
   ```

### Security and Credentials

1. **Never Commit Credentials**
   - Use `.env` files (add to `.gitignore`)
   - Use environment variables
   - Rotate tokens regularly
   - Use workspace-specific tokens

2. **Limit Token Permissions**
   - Use tokens with minimal required permissions
   - Create separate tokens for different environments
   - Monitor token usage

3. **Review Generated Configurations**
   - Check for sensitive data in descriptions
   - Verify table access permissions
   - Ensure appropriate warehouse selection

### Performance Optimization

1. **Optimize LLM Calls**
   - Cache prompt components
   - Reuse client connections
   - Batch operations when possible
   - Use appropriate `max_tokens` limits

2. **Optimize API Calls**
   - Use pagination for large result sets
   - Request only needed fields
   - Cache frequently accessed data
   - Implement rate limiting

3. **Configuration Size**
   - Keep instruction sets focused
   - Avoid redundant information
   - Use SQL expressions instead of repeated logic
   - Balance comprehensiveness with simplicity

### Error Handling and Debugging

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Capture and Log Errors**
   ```python
   try:
       result = client.create_space(config)
   except Exception as e:
       logging.error(f"Failed to create space: {e}")
       if hasattr(e, 'response'):
           logging.error(f"API response: {e.response.text}")
       raise
   ```

3. **Validate Incrementally**
   - Test prompt building independently
   - Validate JSON before API calls
   - Check transformations with small configs
   - Use unit tests for critical paths

4. **Common Issues and Solutions**

   | Issue | Cause | Solution |
   |-------|-------|----------|
   | `warehouse_id is required` | Missing or placeholder warehouse ID | Update config with valid warehouse ID |
   | `Invalid table identifier` | Malformed table name | Check `catalog.schema.table` format |
   | `Authentication failed` | Invalid token | Verify `DATABRICKS_TOKEN` in `.env` |
   | `Permission denied` | Insufficient permissions | Ensure CAN EDIT permission on space |
   | `Table not found` (at creation) | Table doesn't exist | Run `genie.py validate` first |
   | `Column not found` (at runtime) | Column doesn't exist | Run `genie.py validate` first |
   | Table validation fails | Table not in Unity Catalog | Check table exists with `SHOW TABLES` |
   | Column validation fails | Column name mismatch | Check column with `DESCRIBE TABLE` |
   | JSON parsing errors | Incomplete LLM response | Increase `max_tokens` parameter |
   | Validation errors | Schema mismatch | Review Pydantic model requirements |

### Development Workflow

1. **Local Development**
   ```bash
   # 1. Set up environment
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   
   # 2. Validate setup
   python scripts/validate_setup.py
   
   # 3. Develop and test
   genie.py generate --requirements data/demo_requirements.md
   
   # 4. Validate tables and columns (CRITICAL STEP)
   genie.py validate
   
   # 5. Fix any validation errors (interactive prompts available)
   # Validation can interactively fix catalog/schema issues
   
   # 6. Re-validate if manual edits were made
   genie.py validate
   
   # 7. Deploy space
   genie.py deploy
   ```

2. **Testing Strategy**
   - Unit test individual components
   - Integration test full workflows
   - Validate with real Databricks workspace
   - Test error conditions

3. **Code Quality**
   - Use type hints throughout
   - Document complex functions
   - Follow PEP 8 style guide
   - Keep functions focused and small

### Related Documentation

- **GENIE_CONFIG_GUIDE.md**: Detailed configuration format and structure guide
- **README.md**: Installation, quick start, and user guide
- **ARCHITECTURE.md** (this file): System architecture and design
- **TABLE_VALIDATION.md**: Complete table validation guide
- **VALIDATION_QUICK_REFERENCE.md**: Quick validation reference
- **Databricks Genie API**: https://docs.databricks.com/api/workspace/genie
- **Unity Catalog Docs**: Table and schema management

---

## Table & Column Validation System

### Overview

The table validation system ensures that all customer-provided tables and columns referenced in a Genie space configuration actually exist in Databricks Unity Catalog before attempting to create the space.

### Why Validation Is Critical

**Without Validation:**
- ❌ Space creation may succeed but queries will fail at runtime
- ❌ Users see cryptic "table not found" or "column not found" errors
- ❌ Debugging is time-consuming and frustrating
- ❌ Poor user experience

**With Validation:**
- ✅ Catch errors before space creation
- ✅ Clear, actionable error messages
- ✅ Fast feedback loop for corrections
- ✅ Confident deployments

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Configuration (JSON)                                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          TableValidator                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Parse configuration                                 │ │
│  │ 2. Extract table references                            │ │
│  │ 3. Extract column references from SQL                  │ │
│  │ 4. Query Unity Catalog API                             │ │
│  │ 5. Validate existence and accessibility               │ │
│  │ 6. Generate comprehensive report                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          Unity Catalog API                                   │
│  • GET /unity-catalog/tables/{catalog}.{schema}.{table}    │
│  • Fallback: DESCRIBE TABLE via SQL execution              │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          ValidationReport                                    │
│  • tables_valid / tables_invalid                            │
│  • columns_valid / columns_invalid                          │
│  • issues (errors, warnings, info)                          │
│  • Human-readable and JSON output                           │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Validated

1. **Table Existence**
   - All tables in `tables` section
   - Checks against Unity Catalog
   - Verifies access permissions

2. **Column Existence**
   - Columns referenced in `sql_expressions`
   - Columns in `example_sql_queries`
   - Case-insensitive matching

3. **SQL Expression Parsing**
   - Extracts column references like `t.customer_id`
   - Maps aliases to tables (`t` → `transactions`)
   - Validates against table schemas

### Key Features

- **Two-Tier API Strategy**: Unity Catalog API with SQL DESCRIBE fallback
- **Schema Caching**: Avoids redundant API calls
- **Case-Insensitive Matching**: Reduces false positives
- **Detailed Reporting**: Errors, warnings, and info levels
- **JSON Output**: CI/CD integration support

### Usage

```bash
# Basic validation
python scripts/validate_tables.py

# JSON output (for automation)
python scripts/validate_tables.py --json

# Verbose mode
python scripts/validate_tables.py --verbose
```

### Python API

```python
from src.table_validator import TableValidator

validator = TableValidator()

# Validate entire config
report = validator.validate_config("output/genie_space_config.json")

if report.has_errors():
    print(report.summary())
    exit(1)

# Validate specific table
exists = validator.validate_table("catalog", "schema", "table")

# Validate columns
results = validator.validate_columns(
    "catalog", "schema", "table",
    ["customer_id", "total_amount"]
)
```

### Integration Points

The validation system integrates at multiple points in the workflow:

1. **After Configuration Generation**
   ```bash
   genie.py generate --requirements data/requirements.md
   genie.py validate  # ← Validate here (interactive fixes)
   genie.py deploy
   ```

2. **Built into Create Command** (recommended)
   ```bash
   genie.py create --requirements data/requirements.md
   # Automatically runs: generate → validate → deploy
   ```

3. **Before Space Creation** (critical when using Python API)
   - Always validate before calling create_space()
   - Fix errors, then re-validate
   - Only create space after validation passes

4. **In CI/CD Pipelines**
   ```yaml
   - run: genie.py validate --config output/genie_space_config.json
   # Returns non-zero exit code on validation failure
   ```

### Performance

- **First validation**: ~2-5 seconds (depends on table count)
- **Subsequent validations**: ~0.5-1 second (cached schemas)
- **API calls**: 1 per unique table (cached after first call)

### Error Handling

Common validation errors and solutions:

| Error | Solution |
|-------|----------|
| Table not found | Verify table exists: `SHOW TABLES IN catalog.schema` |
| Column not found | Check schema: `DESCRIBE TABLE catalog.schema.table` |
| Access denied | Verify READ permissions on table |
| API timeout | Check network connectivity, retry |

### Best Practices

1. **Always Validate**: Make it a required step in your workflow
2. **Fix Errors**: Errors must be fixed; warnings should be reviewed
3. **Save Reports**: Store validation results for audit trail
4. **Automate**: Use in CI/CD for automated validation
5. **Re-validate**: After any config changes, re-validate

### Documentation

For complete documentation:
- **Full Guide**: `docs/TABLE_VALIDATION.md`
- **Quick Reference**: `docs/VALIDATION_QUICK_REFERENCE.md`
- **Examples**: `examples/validate_tables_example.py`
- **Tests**: `tests/test_table_validator.py`

---

## Quick Reference

### Essential Commands

#### Setup and Validation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Validate setup
python scripts/validate_setup.py

# Validate tables and columns (after generating config)
python scripts/validate_tables.py
python scripts/validate_tables.py --json  # JSON output
python scripts/validate_tables.py --verbose  # Verbose mode
```

#### Document Parsing
```bash
# Parse PDFs and markdown with concurrent processing
genie.py parse --input-dir docs/ --output data/requirements.md

# Parse with custom concurrency and models
genie.py parse \
  --input-dir docs/ \
  --output data/requirements.md \
  --max-concurrent 5 \
  --llm-model databricks-gpt-5-2 \
  --vision-model databricks-claude-sonnet-4

# Parse without LLM enrichment (faster)
genie.py parse --input-dir docs/ --output data/requirements.md --no-llm
```

#### Configuration Generation
```bash
# Generate with foundation model (recommended)
genie.py generate \
  --requirements data/demo_requirements.md \
  --model databricks-gpt-5-2 \
  --max-tokens 16000 \
  --output output/genie_space_config.json

# Generate with custom endpoint
genie.py generate \
  --requirements data/demo_requirements.md \
  --endpoint my-llm-endpoint \
  --output output/genie_space_config.json

# Generate without reasoning
genie.py generate --requirements data/demo_requirements.md --no-reasoning
```

#### Table Validation
```bash
# Validate tables and columns (with interactive fixes)
genie.py validate --config output/genie_space_config.json

# Validation includes:
# - Table existence in Unity Catalog
# - Column existence in tables
# - Interactive catalog/schema replacement on failures
# - Up to 3 validation attempts
```

#### Space Creation
```bash
# Deploy from configuration file
genie.py deploy \
  --config output/genie_space_config.json \
  --result-output output/genie_space_result.json

# Deploy with custom parent path
genie.py deploy \
  --config output/genie_space_config.json \
  --parent-path /Workspace/Users/your.email@domain.com/genie_spaces

# End-to-end automated workflow (recommended)
genie.py create --requirements data/demo_requirements.md
```

### Key Python API Patterns

#### Document Parsing
```python
from src.pipeline import parse_documents
import asyncio

# Synchronous wrapper (async under the hood)
result = parse_documents(
    input_dir="docs/",
    output_path="data/requirements.md",
    llm_model="databricks-gpt-5-2",
    vision_model="databricks-claude-sonnet-4",
    use_llm=True,
    max_concurrent_pdfs=5
)

# Direct async usage
from src.pipeline.parser import parse_documents_async
result = asyncio.run(parse_documents_async(
    input_dir="docs/",
    output_path="data/requirements.md",
    max_concurrent_pdfs=5
))

print(f"Extracted: {result['questions_count']} questions, {result['tables_count']} tables")
```

#### Configuration Generation
```python
from src.pipeline import generate_config

# Generate configuration using pipeline function
config = generate_config(
    requirements_path="data/demo_requirements.md",
    output_path="output/genie_space_config.json",
    model="databricks-gpt-5-2",
    max_tokens=16000,
    temperature=0.1
)

# Or use lower-level components
from src.prompt.prompt_builder import PromptBuilder
from src.llm.databricks_llm import DatabricksFoundationModelClient

builder = PromptBuilder(
    context_doc_path="src/prompt/templates/curate_effective_genie.md",
    output_doc_path="src/prompt/templates/genie_api.md",
    input_data_path="data/demo_requirements.md"
)
prompt = builder.build_prompt_with_reasoning()

client = DatabricksFoundationModelClient(model_name="databricks-gpt-5-2")
response = client.generate_genie_config(prompt, max_tokens=16000)

import json
with open("output/genie_space_config.json", "w") as f:
    json.dump(response.model_dump(), f, indent=2)
```

#### Table & Column Validation
```python
from src.utils.table_validator import TableValidator

# Initialize validator
validator = TableValidator()

# Validate configuration
report = validator.validate_config("output/genie_space_config.json")

# Check for errors
if report.has_errors():
    print("❌ Validation failed!")
    print(report.summary())
    exit(1)
else:
    print("✅ All tables and columns are valid!")

# Validate specific table
exists = validator.validate_table("catalog", "schema", "table")

# Validate specific columns
results = validator.validate_columns(
    "catalog", "schema", "table",
    ["customer_id", "total_amount"]
)

# Get table schema
schema = validator.get_table_schema("catalog", "schema", "table")
for col in schema['columns']:
    print(f"  {col['name']}: {col['type_text']}")
```

#### Space Creation
```python
from src.api.genie_space_client import GenieSpaceClient, create_genie_space_from_file

# Method 1: Using convenience function
result = create_genie_space_from_file("output/genie_space_config.json")
print(f"Space URL: {result['space_url']}")

# Method 2: Using client directly
import json
client = GenieSpaceClient()

with open("output/genie_space_config.json") as f:
    config = json.load(f)

response = client.create_space(config)
space_id = response["space_id"]
print(f"Space ID: {space_id}")
```

#### Space Management
```python
from src.api.genie_space_client import GenieSpaceClient

client = GenieSpaceClient()

# List all spaces with pagination
spaces = client.list_spaces(page_size=100)
for space in spaces.get('spaces', []):
    print(f"{space['space_name']}: {space.get('space_id')}")

# Get space details
space = client.get_space(space_id)
print(f"Space: {space['space_name']}")

# Get space with full configuration (requires CAN EDIT)
space_full = client.get_space(space_id, include_serialized_space=True)

# Update space (partial)
client.update_space(
    space_id,
    title="Updated Title",
    description="New description"
)

# Update space (full config)
client.update_space(space_id, config=updated_config)

# Move to trash
client.trash_space(space_id)

# Get space URL
url = client.get_space_url(space_id)
print(f"Access at: {url}")
```

#### Configuration Transformation
```python
from src.utils.config_transformer import (
    transform_to_serialized_space,
    load_and_transform_config
)

# Transform config to serialized format
serialized = transform_to_serialized_space(config)

# Load and transform from file
config, serialized = load_and_transform_config("config.json")
```

### Key File Locations

| File | Purpose |
|------|---------|
| `genie.py` | 🌟 Unified CLI (parse, create, generate, validate, deploy) |
| `scripts/validate_setup.py` | Setup validation |
| `scripts/convert_requirements.py` | Requirements conversion |
| `examples/create_genie_space_example.py` | Python API examples |
| `src/pipeline/parser.py` | Document parsing module (async/concurrent) |
| `src/pipeline/generator.py` | Configuration generation module |
| `src/pipeline/validator.py` | Table validation module |
| `src/pipeline/deployer.py` | Space deployment module |
| `src/models.py` | Pydantic schema models |
| `src/prompt/prompt_builder.py` | Prompt construction |
| `src/llm/databricks_llm.py` | Databricks LLM client |
| `src/api/genie_space_client.py` | Genie Space API client |
| `src/utils/config_transformer.py` | Config transformation |
| `src/utils/table_validator.py` | Table & column validator |
| `src/utils/benchmark_extractor.py` | Benchmark extractor |
| `src/parsing/pdf_parser.py` | PDF extraction (pdfplumber + LLM) |
| `src/parsing/markdown_parser.py` | Markdown extraction (regex) |
| `src/parsing/requirements_structurer.py` | Data models & structuring |
| `src/parsing/llm_enricher.py` | LLM-based enrichment |
| `src/parsing/markdown_generator.py` | Markdown output generation |
| `src/prompt/templates/curate_effective_genie.md` | Best practices context |
| `src/prompt/templates/genie_api.md` | API documentation |
| `data/demo_requirements.md` | Example requirements |
| `output/genie_space_config.json` | Generated configuration |
| `output/genie_space_result.json` | Creation result |
| `tests/test_table_validator.py` | Table validator tests |
| `tests/test_join_specs.py` | Join specification tests |
| `tests/test_pdf_image_parsing.py` | PDF image parsing tests |

### Environment Variables

```bash
# Required
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=dapi...

# Optional (with defaults)
LLM_MODEL=databricks-gpt-5-2                    # Text-based LLM for config generation
VISION_MODEL=databricks-claude-sonnet-4         # Vision model for PDF parsing
```

**Environment Variable Details**:

| Variable | Required | Default | Used By |
|----------|----------|---------|---------|
| `DATABRICKS_HOST` | ✅ Yes | - | All components |
| `DATABRICKS_TOKEN` | ✅ Yes | - | All components |
| `LLM_MODEL` | No | `databricks-gpt-5-2` | `parse`, `generate` commands |
| `VISION_MODEL` | No | `databricks-claude-sonnet-4` | `parse` command (PDF parsing) |

### Key Concepts

- **LLMResponse**: Wrapper containing config, reasoning, and confidence score
- **GenieSpaceConfig**: Main configuration model with all space settings
- **serialized_space**: Databricks internal format (auto-generated)
- **Transformation**: Conversion from user-friendly to serialized format
- **Pagination**: Handling large lists of spaces with page tokens
- **Partial Update**: Update only specific fields without full config
- **Trash**: Recoverable deletion (vs permanent delete)
- **Markdown-Formatted Instructions**: Instructions use markdown (headings, lists, bold, code) for better structure and readability

### Common Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | `databricks-gpt-5-2` | Foundation model to use |
| `--endpoint` | None | Custom serving endpoint |
| `--input-data` | `data/demo_requirements.md` | Requirements document |
| `--output` | `output/genie_space_config.json` | Output file path |
| `--max-tokens` | 16000 | Maximum tokens to generate |
| `--temperature` | 0.1 | Sampling temperature (0.0-1.0) |
| `--no-reasoning` | False | Skip reasoning in output |

### Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias genie='python genie.py'
alias genie-parse='python genie.py parse'
alias genie-generate='python genie.py generate'
alias genie-validate='python genie.py validate'
alias genie-deploy='python genie.py deploy'
alias genie-create='python genie.py create'

# With common options
alias genie-fast='python genie.py create --skip-validation -y'
alias genie-parse-fast='python genie.py parse --no-llm'
```

---

**End of Architecture Documentation**
