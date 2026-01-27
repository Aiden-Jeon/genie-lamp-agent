# System Architecture

> **Comprehensive architectural documentation for the Genie Space Configuration Generator**
> 
> This document describes the system architecture, components, data flows, and best practices for generating and managing Databricks Genie spaces using LLMs.

## Table of Contents

1. [High-Level Flow](#high-level-flow)
2. [System Capabilities and Features](#system-capabilities-and-features)
3. [Project Structure](#project-structure)
4. [Component Details](#component-details)
5. [Data Flow Diagram](#data-flow-diagram)
6. [Module Dependency Graph](#module-dependency-graph)
7. [Error Handling Flow](#error-handling-flow)
8. [Configuration Options](#configuration-options)
9. [Performance Characteristics](#performance-characteristics)
10. [Security Considerations](#security-considerations)
11. [Scripts and Utilities](#scripts-and-utilities)
12. [Extension Points](#extension-points)
13. [Testing Strategy](#testing-strategy)
14. [Monitoring and Debugging](#monitoring-and-debugging)
15. [Deployment Options](#deployment-options)
16. [Genie Space API Integration](#genie-space-api-integration)
17. [Best Practices and Design Principles](#best-practices-and-design-principles)
18. [Quick Reference](#quick-reference)

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                           INPUT LAYER                                │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   Context Doc    │  │  Output Format   │  │  Requirements    │ │
│  │                  │  │                  │  │                  │ │
│  │  Best practices  │  │  Genie API docs  │  │  Business needs  │ │
│  │  Guidelines      │  │  Schema info     │  │  Tables/Metrics  │ │
│  │  Principles      │  │  Examples        │  │  Questions       │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROMPT BUILDER LAYER                            │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  PromptBuilder                                                │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │ 1. Read all input documents                             │ │ │
│  │  │ 2. Construct structured prompt:                         │ │ │
│  │  │    - Instruction section                                │ │ │
│  │  │    - Context section (best practices)                   │ │ │
│  │  │    - Output format section (schema)                     │ │ │
│  │  │    - Input section (requirements)                       │ │ │
│  │  │ 3. Format for LLM consumption                           │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM CLIENT LAYER                             │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  DatabricksLLMClient                                          │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │ - Build API request                                     │ │ │
│  │  │ - Call Databricks serving endpoint                      │ │ │
│  │  │ - Handle authentication                                 │ │ │
│  │  │ - Parse response                                        │ │ │
│  │  │ - Extract JSON                                          │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                               │ │
│  │  Options:                                                     │ │
│  │  • Foundation Models (llama-3-1-70b, etc.)                   │ │
│  │  • Custom Serving Endpoints                                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    VALIDATION LAYER (Pydantic)                       │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  GenieSpaceConfig (Main Model)                                │ │
│  │  ├── space_name: str                                          │ │
│  │  ├── description: str                                         │ │
│  │  ├── purpose: str                                             │ │
│  │  ├── tables: List[GenieSpaceTable]                            │ │
│  │  ├── instructions: List[GenieSpaceInstruction]                │ │
│  │  ├── example_sql_queries: List[GenieSpaceExampleSQL]          │ │
│  │  ├── sql_expressions: List[GenieSpaceSQLExpression]           │ │
│  │  └── benchmark_questions: List[GenieSpaceBenchmark]           │ │
│  │                                                               │ │
│  │  Validation:                                                  │ │
│  │  ✓ Type checking                                              │ │
│  │  ✓ Required fields                                            │ │
│  │  ✓ Data structure                                             │ │
│  │  ✓ Constraints                                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         OUTPUT LAYER                                 │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  LLMResponse                                                  │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │ {                                                       │ │ │
│  │  │   "genie_space_config": {                               │ │ │
│  │  │     // Complete validated configuration                 │ │ │
│  │  │   },                                                    │ │ │
│  │  │   "reasoning": "Why these choices...",                  │ │ │
│  │  │   "confidence_score": 0.95                              │ │ │
│  │  │ }                                                       │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                               │ │
│  │  Saved to: output/genie_space_config.json                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## System Capabilities and Features

### Core Capabilities

1. **Automated Configuration Generation**
   - Leverages LLMs (Databricks Foundation Models or custom endpoints)
   - Generates production-ready Genie space configurations
   - Includes reasoning and confidence scores
   - Validates output against strict schemas

2. **Intelligent Prompt Engineering**
   - Structured prompts with context, format, and requirements
   - Incorporates best practices from curated documentation
   - Supports customizable input sources

3. **Robust Validation**
   - Pydantic models ensure type safety
   - Automatic schema validation
   - Table and column validation against Unity Catalog
   - Error handling and debugging support

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
   ./scripts/create_genie_space_workflow.sh
   ```

2. **Manual Review + Editing**
   ```bash
   python main.py  # Generate
   python scripts/validate_tables.py  # Validate
   vim output/genie_space_config.json  # Edit
   python scripts/create_genie_space.py  # Create
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
├── main.py                          # Config generation CLI
├── requirements.txt                 # Python dependencies
├── .env.example                     # Example environment file
├── README.md                        # User guide
├── ARCHITECTURE.md                  # This file
├── GENIE_CONFIG_GUIDE.md           # Configuration format guide
├── CHANGELOG.md                     # Version history
├── SPACE_CREATED.md                # Post-creation documentation
│
├── src/                            # Core source code
│   ├── __init__.py
│   ├── models.py                   # Pydantic models
│   ├── prompt_builder.py           # Prompt construction
│   ├── databricks_llm.py           # LLM client
│   ├── genie_space_client.py       # Genie Space API client
│   ├── config_transformer.py       # Config transformation
│   ├── table_validator.py          # Table & column validator
│   ├── benchmark_extractor.py      # Benchmark extractor
│   └── docs/                       # LLM context documents
│       ├── curate_effective_genie.md  # Best practices
│       └── genie_api.md               # API documentation
│
├── data/                           # Input requirements
│   └── demo_requirements.md        # Example requirements
│
├── docs/                           # Documentation
│   ├── BENCHMARK_EXTRACTION.md     # Benchmark extraction guide
│   ├── TABLE_VALIDATION.md         # Table validation guide
│   ├── VALIDATION_QUICK_REFERENCE.md  # Validation quick reference
│   └── VALIDATION_IMPLEMENTATION_SUMMARY.md  # Implementation summary
│
├── output/                         # Generated files (gitignored)
│   ├── genie_space_config.json     # Generated config
│   └── genie_space_result.json     # Creation result
│
├── scripts/                        # Automation scripts
│   ├── create_genie_space.py       # Space creation script
│   ├── validate_tables.py          # Table & column validation
│   ├── create_genie_space_workflow.sh  # End-to-end workflow
│   └── validate_setup.py           # Setup validation
│
├── examples/                       # Usage examples
│   ├── create_genie_space_example.py  # Python API examples
│   └── validate_tables_example.py     # Table validation examples
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── test_generation.py          # Generation tests
    ├── test_example_usage.py       # Example usage tests
    └── test_table_validator.py     # Table validator tests
```

## Component Details

### 1. Input Layer

**Purpose**: Provide comprehensive context for LLM generation

**Components**:
- `docs/curate_effective_genie.md`: Best practices and principles
- `docs/genie_api.md`: API documentation and schema information
- `data/demo_requirements.md`: Actual business requirements

**Format**: Markdown documents with structured information

### 2. Prompt Builder Layer

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
    
    def build_prompt_with_reasoning() -> str:
        # Build prompt that includes reasoning
```

**Process**:
1. Read all input documents
2. Construct structured prompt with sections
3. Format for optimal LLM comprehension

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

### 5. Table & Column Validation Layer

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

### 6. Output Layer

**Format**: JSON file with validated configuration

**Structure**:
```json
{
  "genie_space_config": {
    "space_name": "Fashion Retail Analytics",
    "description": "Natural language querying...",
    "purpose": "Enable business users...",
    "tables": [...],
    "instructions": [...],
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
│  1. scripts/create_genie_space_workflow.sh (Automated)          │
│  2. main.py (Manual - Config Generation)                        │
│  3. scripts/create_genie_space.py (Manual - Space Creation)     │
│  4. examples/create_genie_space_example.py (Python API)         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: CONFIG GENERATION                    │
└─────────────────────────────────────────────────────────────────┘

main.py (CLI Entry Point)
    │
    ├─── Load environment (.env file)
    ├─── Parse command-line arguments
    │    • --model, --endpoint
    │    • --input-data, --output
    │    • --max-tokens, --temperature
    │
    └─── Orchestrate generation flow
            │
            ▼

PromptBuilder.build_prompt_with_reasoning()
    │
    ├─── Read src/docs/curate_effective_genie.md
    │        (Best practices, principles, guidelines)
    │
    ├─── Read src/docs/genie_api.md
    │        (API schema, output format, examples)
    │
    ├─── Read data/demo_requirements.md
    │        (Business requirements, tables, questions)
    │
    └─── Construct structured prompt
            • Instruction section
            • Context section (best practices)
            • Output format section (schema)
            • Input section (requirements)
            │
            ▼

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

Save Configuration
    │
    ├─── Convert to JSON (model.model_dump())
    ├─── Format with indentation (indent=2)
    └─── Write to output/genie_space_config.json
            │
            ▼

┌─────────────────────────────────────────────────────────────────┐
│          PHASE 2: TABLE & COLUMN VALIDATION (RECOMMENDED)        │
└─────────────────────────────────────────────────────────────────┘

scripts/validate_tables.py
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

scripts/create_genie_space.py
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

#### Workflow A: Automated End-to-End

```
scripts/create_genie_space_workflow.sh
    │
    ├─── Execute: python main.py (config generation)
    │       └─── Output: genie_space_config.json
    │
    └─── Execute: python scripts/create_genie_space.py
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
main.py (Config Generation)
    │
    ├── src.prompt_builder
    │       └── PromptBuilder
    │               └── Reads: docs/*.md, data/*.md
    │
    ├── src.databricks_llm
    │       ├── DatabricksLLMClient
    │       └── DatabricksFoundationModelClient
    │               └── Uses: requests library
    │
    └── src.models
            ├── GenieSpaceConfig
            ├── GenieSpaceTable
            ├── GenieSpaceInstruction
            ├── GenieSpaceExampleSQL
            ├── GenieSpaceSQLExpression
            ├── GenieSpaceBenchmark
            └── LLMResponse
                    └── Uses: pydantic library

scripts/validate_tables.py (Table & Column Validation)
    │
    └── src.table_validator
            ├── TableValidator
            ├── ValidationReport
            └── ValidationIssue
                    └── Uses: requests library, Unity Catalog API

scripts/create_genie_space.py (Space Creation)
    │
    ├── src.genie_space_client
    │       ├── GenieSpaceClient
    │       └── create_genie_space_from_file()
    │
    └── src.config_transformer
            └── transform_to_serialized_space()

examples/validate_tables_example.py (Validation Examples)
    │
    └── src.table_validator
            ├── TableValidator
            ├── validate_table()
            ├── validate_columns()
            ├── get_table_schema()
            └── validate_config()

examples/create_genie_space_example.py (Usage Examples)
    │
    └── src.genie_space_client
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

scripts/create_genie_space_workflow.sh (End-to-End Automation)
    │
    ├── main.py (generate config)
    │
    └── scripts/create_genie_space.py (create space)
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

### 1. Main Configuration Generator (`main.py`)

**Purpose**: Generate Genie space configurations using LLMs

**Key Features**:
- Supports both foundation models and custom endpoints
- Configurable context, output format, and input documents
- Optional reasoning and confidence scores
- JSON validation via Pydantic

**Usage**:
```bash
python main.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000 \
  --output output/genie_space_config.json
```

### 2. Space Creation Script (`scripts/create_genie_space.py`)

**Purpose**: Create Databricks Genie spaces from configuration files

**Key Features**:
- Transforms config to serialized_space format
- Posts to Genie Spaces API
- Returns space ID and URL
- Saves creation result

**Usage**:
```bash
python scripts/create_genie_space.py \
  --config output/genie_space_config.json \
  --output output/genie_space_result.json
```

### 3. Automated Workflow Script (`scripts/create_genie_space_workflow.sh`)

**Purpose**: End-to-end automation of config generation and space creation

**Workflow**:
1. Generates configuration using LLM
2. Creates Genie space via API
3. Displays space URL

**Usage**:
```bash
./scripts/create_genie_space_workflow.sh \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000 \
  --temperature 0.1
```

### 4. Table & Column Validation Script (`scripts/validate_tables.py`)

**Purpose**: Validate tables and columns in configuration against Unity Catalog

**Key Features**:
- Verifies all tables exist in Unity Catalog
- Validates columns exist in their tables
- Extracts column references from SQL expressions
- Generates detailed validation reports
- Supports JSON and human-readable output

**Usage**:
```bash
# Validate default configuration
python scripts/validate_tables.py

# Validate custom configuration
python scripts/validate_tables.py path/to/config.json

# JSON output (for CI/CD)
python scripts/validate_tables.py --json

# Verbose mode
python scripts/validate_tables.py --verbose
```

**What It Validates**:
- Table existence in Unity Catalog
- Column existence in tables
- SQL expression column references
- Access permissions

**Output Example**:
```
================================================================================
TABLE & COLUMN VALIDATION REPORT
================================================================================

Tables Checked: 5
  ✓ Valid:   5

Columns Checked: 28
  ✓ Valid:   28

Issues:
  Errors:   0
  Warnings: 0

================================================================================
✓ VALIDATION PASSED - All tables and columns are valid!
================================================================================
```

### 5. Setup Validation Script (`scripts/validate_setup.py`)

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

### 6. Table Validation Examples (`examples/validate_tables_example.py`)

**Purpose**: Demonstrate table validation API usage

**Examples Include**:
- `example_1_validate_config()`: Validate entire configuration
- `example_2_validate_single_table()`: Validate single table
- `example_3_validate_columns()`: Validate specific columns
- `example_4_get_table_schema()`: Get complete table schema
- `example_5_custom_validation()`: Custom validation logic

**Usage**:
```python
from src.table_validator import TableValidator

# Validate configuration
validator = TableValidator()
report = validator.validate_config("output/genie_space_config.json")
print(report.summary())
```

### 7. Genie Space Usage Examples (`examples/create_genie_space_example.py`)

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
# In main.py
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
python main.py
```

### Automated Workflow Script
```bash
# Generate config and create space in one command
./scripts/create_genie_space_workflow.sh \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000
```

### Scheduled Job
```bash
# Run as a Python task in Databricks Job
python main.py --model databricks-gpt-5-2 --output /dbfs/output/config.json
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
│  (main.py → LLM → genie_space_config.json)                         │
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
./scripts/create_genie_space_workflow.sh \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000 \
  --temperature 0.1

# Output:
# - output/genie_space_config.json (generated config)
# - output/genie_space_result.json (space ID and URL)
```

#### Option 2: Manual Step-by-Step (Recommended)

```bash
# 1. Validate setup (optional but recommended)
python scripts/validate_setup.py

# 2. Generate config with LLM
python main.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json

# 3. Validate tables and columns (RECOMMENDED)
python scripts/validate_tables.py

# 4. Review generated config
cat output/genie_space_config.json

# 5. (Optional) Edit warehouse_id, fix validation errors, etc.
vim output/genie_space_config.json

# 6. Re-validate if edited
python scripts/validate_tables.py

# 7. Create Genie space from config
python scripts/create_genie_space.py \
  --config output/genie_space_config.json \
  --output output/genie_space_result.json

# 8. Access your Genie space
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

### Space Management Best Practices

1. **Validate Before Creation**
   - Run `scripts/validate_setup.py` to check environment
   - **Run `scripts/validate_tables.py` to verify tables and columns** (CRITICAL)
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
   | `Table not found` (at creation) | Table doesn't exist | Run `scripts/validate_tables.py` first |
   | `Column not found` (at runtime) | Column doesn't exist | Run `scripts/validate_tables.py` first |
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
   python main.py --input-data data/demo_requirements.md
   
   # 4. Validate tables and columns (CRITICAL STEP)
   python scripts/validate_tables.py
   
   # 5. Fix any validation errors
   vim output/genie_space_config.json
   
   # 6. Re-validate
   python scripts/validate_tables.py
   
   # 7. Create space
   python scripts/create_genie_space.py
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
   python main.py
   python scripts/validate_tables.py  # ← Validate here
   python scripts/create_genie_space.py
   ```

2. **Before Space Creation** (critical)
   - Always validate before calling create_space()
   - Fix errors, then re-validate
   - Only create space after validation passes

3. **In CI/CD Pipelines**
   ```yaml
   - run: python scripts/validate_tables.py --json
   - run: |
       has_errors=$(jq -r '.has_errors' validation.json)
       if [ "$has_errors" = "true" ]; then exit 1; fi
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

#### Configuration Generation
```bash
# Generate with foundation model (recommended)
python main.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000 \
  --output output/genie_space_config.json

# Generate with custom endpoint
python main.py \
  --endpoint my-llm-endpoint \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json

# Generate without reasoning
python main.py --model databricks-gpt-5-2 --no-reasoning
```

#### Space Creation
```bash
# Create from configuration file
python scripts/create_genie_space.py \
  --config output/genie_space_config.json \
  --output output/genie_space_result.json

# End-to-end automated workflow
./scripts/create_genie_space_workflow.sh \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000
```

### Key Python API Patterns

#### Configuration Generation
```python
from src.prompt_builder import PromptBuilder
from src.databricks_llm import DatabricksFoundationModelClient

# Build prompt
builder = PromptBuilder(
    context_doc_path="src/docs/curate_effective_genie.md",
    output_doc_path="src/docs/genie_api.md",
    input_data_path="data/demo_requirements.md"
)
prompt = builder.build_prompt_with_reasoning()

# Generate config
client = DatabricksFoundationModelClient(model_name="databricks-gpt-5-2")
response = client.generate_genie_config(prompt, max_tokens=16000)

# Save config
with open("output/genie_space_config.json", "w") as f:
    json.dump(response.model_dump(), f, indent=2)
```

#### Table & Column Validation
```python
from src.table_validator import TableValidator

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
from src.genie_space_client import GenieSpaceClient, create_genie_space_from_file

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
from src.genie_space_client import GenieSpaceClient

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
from src.config_transformer import (
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
| `main.py` | Configuration generation CLI |
| `scripts/validate_tables.py` | Table & column validation CLI |
| `scripts/create_genie_space.py` | Space creation CLI |
| `scripts/create_genie_space_workflow.sh` | End-to-end automation |
| `scripts/validate_setup.py` | Setup validation |
| `examples/validate_tables_example.py` | Table validation examples |
| `examples/create_genie_space_example.py` | Python API examples |
| `src/models.py` | Pydantic schema models |
| `src/prompt_builder.py` | Prompt construction |
| `src/databricks_llm.py` | LLM client |
| `src/genie_space_client.py` | Genie Space API client |
| `src/config_transformer.py` | Config transformation |
| `src/table_validator.py` | Table & column validator |
| `src/benchmark_extractor.py` | Benchmark extractor |
| `src/docs/curate_effective_genie.md` | Best practices context |
| `src/docs/genie_api.md` | API documentation |
| `data/demo_requirements.md` | Example requirements |
| `docs/TABLE_VALIDATION.md` | Table validation guide |
| `docs/VALIDATION_QUICK_REFERENCE.md` | Validation quick reference |
| `output/genie_space_config.json` | Generated configuration |
| `output/genie_space_result.json` | Creation result |
| `tests/test_table_validator.py` | Table validator tests |

### Environment Variables

```bash
# Required
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=dapi...

# Optional (can be provided as CLI args)
WORKSPACE_ROOT=/path/to/project
```

### Key Concepts

- **LLMResponse**: Wrapper containing config, reasoning, and confidence score
- **GenieSpaceConfig**: Main configuration model with all space settings
- **serialized_space**: Databricks internal format (auto-generated)
- **Transformation**: Conversion from user-friendly to serialized format
- **Pagination**: Handling large lists of spaces with page tokens
- **Partial Update**: Update only specific fields without full config
- **Trash**: Recoverable deletion (vs permanent delete)

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
alias genie-generate='python main.py --model databricks-gpt-5-2'
alias genie-validate-tables='python scripts/validate_tables.py'
alias genie-validate-setup='python scripts/validate_setup.py'
alias genie-create='python scripts/create_genie_space.py'
alias genie-workflow='./scripts/create_genie_space_workflow.sh'

# Combined workflow
alias genie-full='python main.py --model databricks-gpt-5-2 && python scripts/validate_tables.py && python scripts/create_genie_space.py'
```

---

**End of Architecture Documentation**
