# Genie Lamp Agent 🧞

An intelligent agent that generates Databricks Genie space configurations using LLMs via Databricks serving endpoints.

[![GitHub Repository](https://img.shields.io/badge/GitHub-genie--lamp--agent-blue?style=flat&logo=github)](https://github.com/Aiden-Jeon/genie-lamp-agent)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Databricks](https://img.shields.io/badge/Databricks-Genie-FF3621?logo=databricks)](https://www.databricks.com/)

## 📚 Table of Contents

- [Overview](#overview)
- [Recent Updates](#recent-updates-january-2026)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Key Components](#key-components)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Support](#support)

## Overview

The Genie Lamp Agent automates the creation of Databricks Genie spaces by intelligently generating production-ready configurations from natural language requirements. Simply provide your business requirements and documentation, and let the agent handle the complex configuration process.

**Key Benefits:**
- 🚀 **Automated Configuration**: Transform requirements into production-ready Genie space configs
- ✅ **Complete Test Coverage**: Direct benchmark extraction ensures comprehensive FAQ coverage
- 🔍 **Smart Validation**: Pre-flight checks for tables, columns, and Unity Catalog access
- 🎯 **Best Practices Built-in**: Leverages Databricks Genie best practices automatically
- 🤖 **LLM-Powered**: Uses Databricks foundation models for intelligent configuration generation

### How It Works

```
📄 Best Practices Doc          ──┐
                                 │
📄 Genie API Specification     ──┤──> 🔨 Prompt Builder ──> 🤖 LLM (Databricks) ──> ✅ Validation ──> 📦 JSON Config
                                 │
📄 Your Requirements           ──┘
```

The agent follows a structured pipeline:
1. **Input**: Combines Genie best practices, API specs, and your requirements
2. **Generation**: Uses Databricks foundation models to generate intelligent configurations
3. **Extraction**: Directly extracts all FAQ questions as benchmarks
4. **Validation**: Verifies tables, columns, and Unity Catalog permissions
5. **Output**: Produces a production-ready Genie space configuration

## 🎉 Recent Updates (January 2026)

### 🆕 Direct Benchmark Extraction (v1.1.0)
**Problem Solved:** LLMs often extract only a subset of FAQ questions as benchmarks, missing important test scenarios.

**Solution:** New direct extraction system ensures complete FAQ coverage:
- ✅ `scripts/generate_config_with_direct_benchmarks.py` - Generate config with complete benchmarks
- ✅ `scripts/update_benchmarks.py` - Fix benchmarks in existing configs
- ✅ Preserves exact question phrasing from requirements
- ✅ Deterministic and fast (milliseconds vs seconds)

**Impact:**
```
Before: Partial coverage with LLM-based extraction ❌
After:  Complete coverage with direct extraction ✅
```

### 🔍 Enhanced Table & Column Validation (v1.0.0)
Comprehensive validation system that checks Unity Catalog before space creation:
- ✅ Validates all table references exist
- ✅ Validates column references in SQL expressions
- ✅ Detailed error reporting with actionable fixes
- ✅ Pre-flight checks prevent runtime errors
- ✅ Prevents costly deployment failures

### 🚀 2026 Databricks Genie API Support
Full support for latest Genie API features:
- 📄 Pagination support for large space lists
- ⚡ Partial updates (update title/description without full config)
- 📦 Serialized space export (requires CAN EDIT permission)
- 📁 Parent path support for workspace organization
- 🗑️ Trash (recoverable) vs permanent delete

## Features

- **Structured Prompts**: Builds comprehensive prompts with context, output format, and input data
- **Pydantic Models**: Type-safe configuration models that match Genie API requirements
- **Databricks Integration**: Direct integration with Databricks serving endpoints and foundation models
- **Schema Validation**: Automatic validation of LLM output against schema
- **Table & Column Validation**: Verify that all referenced tables and columns exist in Unity Catalog
- **Direct Benchmark Extraction**: Extract 100% of FAQ questions as benchmarks (no LLM filtering)
- **Reasoning**: Optional reasoning output to understand configuration choices

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.8+** installed
- ✅ **Databricks workspace** with access to:
  - Unity Catalog tables
  - Genie Spaces API
  - Foundation models (e.g., `databricks-gpt-5-2`)
- ✅ **Personal Access Token** with appropriate permissions
- ✅ **SQL Warehouse** ID for Genie space execution

## Installation

### Option 1: Clone from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/Aiden-Jeon/genie-lamp-agent.git
cd genie-lamp-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Existing Project

If you already have the project:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set your Databricks credentials using a `.env` file (recommended):

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```bash
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
```

Alternatively, you can use environment variables:
```bash
export DATABRICKS_HOST="https://your-workspace.databricks.com"
export DATABRICKS_TOKEN="your-personal-access-token"
```

Or provide them as command-line arguments (see Usage).

## Quick Start

### ⭐ Recommended Workflow (Complete Benchmark Coverage)

**Best for:** Production use, complete test coverage, accurate FAQ representation

```bash
# Step 1: Generate configuration with 100% benchmark extraction
python scripts/generate_config_with_direct_benchmarks.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000

# Step 2: Validate tables and columns (CRITICAL)
python scripts/validate_tables.py

# Step 3: Create the Genie space
python scripts/create_genie_space.py
```

**What this does:**
1. ✅ Generates configuration using LLM (tables, instructions, SQL)
2. ✅ Extracts all FAQ questions directly as benchmarks
3. ✅ Validates all tables and columns exist in Unity Catalog
4. ✅ Creates the Genie space with complete test coverage

**Why use this?**
- **Complete benchmark coverage** vs partial coverage with LLM-only approach
- Preserves exact question phrasing from requirements
- Catches table/column errors before space creation
- Production-ready configuration

### Alternative: Automated Workflow (Faster but Incomplete)

**Best for:** Quick demos, prototyping

```bash
./scripts/create_genie_space_workflow.sh
```

**Limitations:**
- ⚠️ LLM-based benchmark extraction (only partial FAQ coverage)
- ⚠️ May miss important test scenarios
- ⚠️ Questions may be modified or filtered

**Recommendation:** Use the complete workflow above for production deployments.

### Workflow Comparison

| Feature | Complete Workflow ⭐ | Automated Workflow |
|---------|---------------------|-------------------|
| **Benchmark Coverage** | Complete (all FAQs) | Partial (subset of questions) |
| **Question Accuracy** | Exact phrasing preserved | Modified/filtered by LLM |
| **Table Validation** | ✅ Explicit validation step | ❌ No validation |
| **Error Detection** | ✅ Before space creation | ❌ At runtime |
| **Production Ready** | ✅ Yes | ⚠️ Prototypes only |
| **Speed** | Slower (more thorough) | Faster (less comprehensive) |
| **Test Coverage** | Complete | Partial |

**Options:**

```bash
./scripts/create_genie_space_workflow.sh \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --max-tokens 16000 \
  --temperature 0.1
```

### Manual Workflow

Or run each step manually:

```bash
# 1. Generate the configuration using LLM
python main.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json

# 2. Update benchmarks to ensure 100% FAQ coverage (RECOMMENDED)
python scripts/update_benchmarks.py \
  --config output/genie_space_config.json \
  --requirements data/demo_requirements.md

# 3. Validate tables and columns (CRITICAL)
python scripts/validate_tables.py

# 4. (Optional) Edit the configuration
# - Update warehouse_id with your SQL warehouse ID
# - Adjust tables, instructions, or examples as needed
# - Fix any validation errors from step 3
vim output/genie_space_config.json

# 5. Create the Genie space
python scripts/create_genie_space.py \
  --config output/genie_space_config.json \
  --output output/genie_space_result.json

# 6. Access your Genie space
# The URL will be printed and saved in output/genie_space_result.json
```

## Usage

### Step 0: Generate with Complete Benchmark Coverage (Recommended)

**NEW:** Use the integrated script for best results:

```bash
python scripts/generate_config_with_direct_benchmarks.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json \
  --max-tokens 16000
```

This single command:
- ✅ Generates configuration with LLM (tables, joins, instructions, SQL examples)
- ✅ Extracts all FAQ questions directly from requirements
- ✅ Merges benchmarks into final configuration
- ✅ Validates configuration structure

**Skip to Step 2** (validation) after running this command.

### Step 1: Generate Genie Space Configuration (Traditional Method)

#### Using Foundation Models (Recommended)

```bash
python main.py \
  --model databricks-gpt-5-2 \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json
```

#### Using Custom Serving Endpoint

```bash
python main.py \
  --endpoint my-llm-endpoint \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json
```

#### Full Options

```bash
python main.py \
  --endpoint my-llm-endpoint \
  --context-doc src/prompt/templates/curate_effective_genie.md \
  --output-doc src/prompt/templates/genie_api.md \
  --input-data data/demo_requirements.md \
  --output output/genie_space_config.json \
  --max-tokens 4000 \
  --temperature 0.1 \
  --databricks-host https://your-workspace.databricks.com \
  --databricks-token dapi1234...
```

### Step 1.5: Update Benchmarks ⭐ (Highly Recommended)

**IMPORTANT:** If you used `main.py` which relies on LLM for benchmark extraction, you should update benchmarks to ensure complete test coverage:

```bash
python scripts/update_benchmarks.py \
  --config output/genie_space_config.json \
  --requirements data/demo_requirements.md
```

**What this fixes:**
```
Before (LLM extraction):  Partial coverage ❌
After (Direct extraction): Complete coverage ✅
```

This extracts all FAQ questions from your requirements document and replaces the LLM-generated benchmarks. 

**Why Direct Benchmark Extraction?**

Real-world analysis shows LLMs select only "representative" questions:

| Method | Coverage | Exact Match | Issues |
|--------|----------|-------------|---------|
| **LLM-based** | Partial | Some questions | Modified phrasing, missing categories |
| **Direct extraction** | Complete | All questions | None - exact preservation |

**Benefits:**
- ✅ **Complete coverage**: All questions extracted
- ✅ **Exact phrasing**: Preserves original question text
- ✅ **No filtering**: Includes all question types
- ✅ **Deterministic**: Same result every time
- ✅ **Fast**: Completes in milliseconds

**Example output:**
```
✓ Extracted benchmark questions from requirements
✓ Updated configuration with complete benchmarks
✓ Validation: All benchmarks valid
✓ Configuration saved to: output/genie_space_config.json
```

The direct extraction process uses regex patterns to identify and extract FAQ sections from your requirements document, ensuring no questions are missed or modified by LLM interpretation.

### Step 2: Validate Tables and Columns (Recommended)

**Before creating the Genie space**, validate that all tables and columns exist in your Unity Catalog:

```bash
python scripts/validate_tables.py
```

This will:
1. Check that all tables referenced in the configuration exist
2. Verify that columns referenced in SQL expressions are valid
3. Confirm you have proper access permissions
4. Provide a detailed report of any issues

**Example Output:**

```
================================================================================
TABLE & COLUMN VALIDATION REPORT
================================================================================

Tables Checked: N
  ✓ Valid:   N

Columns Checked: M
  ✓ Valid:   M

Issues:
  Errors:   0
  Warnings: 0

================================================================================
✓ VALIDATION PASSED - All tables and columns are valid!
================================================================================
```

If validation fails, fix the issues in your configuration before proceeding to create the space.

**Tip:** The validator checks both table existence and column references in SQL expressions, joins, and metric definitions. Always run this before creating a Genie space to avoid runtime errors.

### Step 3: Create the Genie Space

After validating the configuration, create the Genie space in your Databricks workspace:

```bash
python scripts/create_genie_space.py \
  --config output/genie_space_config.json \
  --output output/genie_space_result.json
```

This will:
1. Post the configuration to the Databricks Genie Spaces API
2. Create the space in your workspace
3. Return the space ID and URL
4. Save the result to a JSON file

**Note:** Before creating the space, make sure to update the `warehouse_id` field in your configuration file with a valid SQL warehouse ID from your workspace.

#### Example Output

```
================================================================================
Databricks Genie Space Creator
================================================================================

Configuration file: output/genie_space_config.json

Creating Genie space from: output/genie_space_config.json
✓ Genie space created successfully!
  Space ID: 01efc58b8b724c6e9b5c6666a3a7890f
  Space URL: https://e2-demo-field-eng.cloud.databricks.com/genie/spaces/01efc58b8b724c6e9b5c6666a3a7890f

================================================================================
Genie Space Created Successfully!
================================================================================

Space ID: 01efc58b8b724c6e9b5c6666a3a7890f
Space URL: https://e2-demo-field-eng.cloud.databricks.com/genie/spaces/01efc58b8b724c6e9b5c6666a3a7890f

You can now access your Genie space at the URL above.

✓ Result saved to: output/genie_space_result.json
```

## Project Structure

```
.
├── src/
│   ├── __init__.py              # Package initialization
│   ├── models.py                # Pydantic models for Genie space config
│   ├── api/                     # API clients
│   │   ├── __init__.py
│   │   └── genie_space_client.py    # Genie Space API client
│   ├── llm/                     # LLM clients
│   │   ├── __init__.py
│   │   └── databricks_llm.py        # Databricks LLM client
│   ├── prompt/                  # Prompt management
│   │   ├── __init__.py
│   │   ├── prompt_builder.py        # Builds structured prompts
│   │   └── templates/               # Prompt templates
│   │       ├── curate_effective_genie.md  # Best practices context
│   │       └── genie_api.md               # API documentation
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       ├── benchmark_extractor.py   # Extract benchmarks from requirements
│       ├── config_transformer.py    # Transform to Databricks format
│       └── table_validator.py       # Table & column validator
├── data/
│   └── demo_requirements.md     # Input requirements
│   ├── create_genie_space.py                      # Create Genie space
│   ├── validate_tables.py                         # Validate tables and columns
│   ├── create_genie_space_workflow.sh             # Automated workflow script
│   ├── validate_setup.py                          # Setup validation tool
│   ├── generate_config_with_direct_benchmarks.py  # Generate with full benchmarks
│   ├── update_benchmarks.py                       # Update existing config benchmarks
│   └── fix_benchmarks.sh                          # Legacy benchmark fix script
├── tests/
│   ├── __init__.py
│   ├── test_example_usage.py    # API usage examples
│   ├── test_generation.py       # Configuration generation tests
│   ├── test_join_specs.py       # Join specification tests
│   └── test_table_validator.py  # Validation tests
├── main.py                      # Generate configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment file
├── .gitignore                   # Git ignore patterns
├── README.md                    # This file
└── ARCHITECTURE.md              # System architecture documentation
```

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

## Key Components

### 1. Models (`src/models.py`)

Defines Pydantic models that match the Genie API requirements:

- `GenieSpaceTable`: Tables to include in the space
- `GenieSpaceInstruction`: Plain text instructions
- `GenieSpaceExampleSQL`: Example SQL queries
- `GenieSpaceSQLExpression`: Metrics, filters, dimensions
- `GenieSpaceBenchmark`: Test questions
- `GenieSpaceConfig`: Complete configuration
- `LLMResponse`: Wrapper with reasoning and confidence

### 2. Prompt Builder (`src/prompt/prompt_builder.py`)

Constructs structured prompts with:

- **Instruction**: Task description and principles
- **Context**: Best practices from `curate_effective_genie.md`
- **Output**: API documentation from `genie_api.md`
- **Input**: Requirements from `demo_requirements.md`

### 3. LLM Client (`src/llm/databricks_llm.py`)

Two client classes:

- `DatabricksLLMClient`: For custom serving endpoints
- `DatabricksFoundationModelClient`: For Databricks foundation models

Both support:
- JSON parsing and validation
- Error handling
- Response formatting

### 4. Config Transformer (`src/utils/config_transformer.py`)

Transforms user-friendly configuration to Databricks `serialized_space` format:

**Key Transformations:**
- Converts all text fields (instructions, questions, SQL) into arrays of strings
- Nests instructions into three sub-sections:
  - `text_instructions`: General instructions
  - `join_specs`: Table join specifications
  - `example_question_sqls`: Example questions with SQL
- Generates unique 24-character hex IDs for all items
- Sorts tables by identifier for consistency
- Formats joins with relationship type annotations

**Before (User-Friendly):**
```json
{
  "instructions": [{"content": "Use safe division..."}],
  "joins": [{"left_table": "...", "join_condition": "..."}],
  "example_sql_queries": [{"question": "...", "sql_query": "..."}]
}
```

**After (Databricks Format):**
```json
{
  "instructions": {
    "text_instructions": [{"id": "abc...", "content": ["Use safe division...\n"]}],
    "join_specs": [{"id": "def...", "left": {...}, "right": {...}, "sql": [...]}],
    "example_question_sqls": [{"id": "ghi...", "question": ["...\n"], "sql": ["...\n"]}]
  }
}
```

See `src/utils/config_transformer.py` for transformation implementation details.

### 5. Genie Space Client (`src/api/genie_space_client.py`)

Client for managing Databricks Genie Spaces via API:

- `GenieSpaceClient`: Main client class
  - `create_space(config, parent_path=None)`: Create a new Genie space with optional parent folder path
  - `get_space(space_id, include_serialized_space=False)`: Get space details with optional serialized configuration
  - `list_spaces(page_size=None, page_token=None)`: List all spaces with pagination support
  - `update_space(space_id, config=None, warehouse_id=None, title=None, description=None)`: Update space with flexible partial updates
  - `trash_space(space_id)`: Move a space to trash (recoverable)
  - `delete_space(space_id)`: Deprecated alias for trash_space()
  - `get_space_url(space_id)`: Get the UI URL for a space
- `create_genie_space_from_file()`: Convenience function to create from JSON file

**API Reference:** Based on official Databricks Genie Space API
- [Create Space API](https://docs.databricks.com/api/workspace/genie/createspace)
- [Get Space API](https://docs.databricks.com/api/workspace/genie/getspace)
- [Update Space API](https://docs.databricks.com/api/workspace/genie/updatespace)
- [List Spaces API](https://docs.databricks.com/api/workspace/genie/listspaces)
- [Trash Space API](https://docs.databricks.com/api/workspace/genie/trashspace)

### 6. Main Script (`main.py`)

Command-line interface that:
- Parses arguments
- Builds prompts
- Calls LLM
- Validates output
- Saves configuration

### 7. Creation Script (`scripts/create_genie_space.py`)

Command-line tool that:
- Reads generated configuration
- Posts to Databricks Genie API
- Returns space ID and URL
- Saves creation result

## Example Output

After running the script, you'll see:

```
================================================================================
Genie Space Configuration Generator
================================================================================

Building prompt...
Prompt length: 45231 characters

Initializing LLM client...
Using foundation model: databricks-gpt-5-2

Calling LLM to generate configuration...
  Max tokens: 4000
  Temperature: 0.1

✓ Configuration generated successfully!

Reasoning:
--------------------------------------------------------------------------------
Based on the requirements, I focused on the core tables that form the 
foundation for most business questions...

Confidence Score: 95.00%

✓ Configuration saved to: output/genie_space_config.json

Configuration Summary:
--------------------------------------------------------------------------------
Space Name: Your Genie Space Name
Description: Natural language querying for your data
Tables: N
Instructions: N
Example SQL Queries: N
SQL Expressions: N
Benchmark Questions: N

================================================================================
Done!
================================================================================
```

## Advanced Usage

### Using as a Python Module

#### Generating Configuration

```python
from src.prompt.prompt_builder import PromptBuilder
from src.llm.databricks_llm import DatabricksFoundationModelClient

# Build prompt
builder = PromptBuilder(
    context_doc_path="src/prompt/templates/curate_effective_genie.md",
    output_doc_path="src/prompt/templates/genie_api.md",
    input_data_path="data/demo_requirements.md"
)
prompt = builder.build_prompt_with_reasoning()

# Call LLM
client = DatabricksFoundationModelClient(
    model_name="databricks-gpt-5-2"
)
response = client.generate_genie_config(prompt)

# Access configuration
config = response.genie_space_config
print(f"Generated space: {config.space_name}")
print(f"Number of tables: {len(config.tables)}")
```

#### Creating Genie Space

```python
from src.api.genie_space_client import GenieSpaceClient, create_genie_space_from_file

# Method 1: Using convenience function
result = create_genie_space_from_file("output/genie_space_config.json")
print(f"Space URL: {result['space_url']}")

# Method 2: Using client directly
import json
from dotenv import load_dotenv

load_dotenv()

client = GenieSpaceClient()

# Load configuration
with open("output/genie_space_config.json", 'r') as f:
    config = json.load(f)

# Create space
response = client.create_space(config)
space_id = response["space_id"]
space_url = client.get_space_url(space_id)

print(f"Created space: {space_id}")
print(f"Access at: {space_url}")
```

#### Managing Genie Spaces

```python
from src.api.genie_space_client import GenieSpaceClient

client = GenieSpaceClient()

# List all spaces (with pagination)
spaces = client.list_spaces(page_size=10)
print(f"Total spaces: {len(spaces.get('spaces', []))}")
next_token = spaces.get('next_page_token')

# Get space details (basic info only)
space_details = client.get_space("space-id-here")
print(f"Space name: {space_details['space_name']}")

# Get space with serialized configuration (requires CAN EDIT permission)
space_full = client.get_space("space-id-here", include_serialized_space=True)
if 'serialized_space' in space_full:
    print("Full space configuration retrieved")

# Update entire space configuration
updated_response = client.update_space("space-id-here", config=updated_config)

# Update only specific fields (partial update)
client.update_space(
    "space-id-here",
    title="New Title",
    description="Updated description"
)

# Move space to trash (recoverable)
client.trash_space("space-id-here")

# Create space in specific folder
response = client.create_space(
    config,
    parent_path="/Workspace/Users/your.email@domain.com/genie_spaces"
)
```

**New API Features (2026):**
- **Pagination**: List spaces with `page_size` and `page_token` for handling large numbers of spaces
- **Partial Updates**: Update only specific fields (title, description, warehouse_id) without providing full config
- **Serialized Space Export**: Retrieve full space configuration with `include_serialized_space=True`
- **Parent Path**: Create spaces in specific workspace folders using `parent_path` parameter
- **Trash vs Delete**: Spaces are moved to trash (recoverable) rather than permanently deleted

### Customizing the Prompt

You can modify `src/prompt/prompt_builder.py` to customize:

- Instruction format
- Additional context
- Output schema requirements
- Few-shot examples

## Troubleshooting

### JSON Parsing Errors

If the LLM returns invalid JSON:
- Increase `max_tokens` to allow complete responses
- Lower `temperature` for more deterministic output
- Check that your serving endpoint supports structured output

### Authentication Errors

Ensure your Databricks credentials are correct:
```bash
# Test connection
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  $DATABRICKS_HOST/api/2.0/clusters/list
```

### Model Not Found

For foundation models, ensure the model name is correct and available in your workspace:
```bash
# List available models
databricks serving-endpoints list
```

## 📖 Documentation

### Available Documentation
- **[README.md](README.md)** (this file): Installation, quick start, and complete usage guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture, component details, and integration flows

### Template Documentation
- **[src/prompt/templates/curate_effective_genie.md](src/prompt/templates/curate_effective_genie.md)**: Databricks Genie best practices
- **[src/prompt/templates/genie_api.md](src/prompt/templates/genie_api.md)**: Genie Space API specification

### Configuration Format
The system supports a user-friendly configuration format that includes:
- **Tables**: Unity Catalog tables to include
- **Joins**: Explicit join specifications between tables
- **Instructions**: Text instructions guiding the AI
- **Example SQL Queries**: Example questions with SQL answers
- **SQL Expressions**: Reusable metric and dimension definitions
- **Benchmarks**: Test questions for validation

All configurations are automatically transformed to Databricks' internal `serialized_space` format when creating or updating Genie spaces. The transformation is handled transparently by `src/utils/config_transformer.py`.

## Parsing Module

The parsing module provides a complete pipeline for extracting, structuring, and generating documentation from various sources (PDFs, markdown files) to create Genie space configurations.

### Module Structure

```
src/parsing/
├── __init__.py                    # Module exports
├── pdf_parser.py                  # PDF extraction (hybrid: pdfplumber + LLM)
├── markdown_parser.py             # Markdown extraction (regex-based)
├── requirements_structurer.py     # Data models & structuring
├── llm_enricher.py               # LLM-based enrichment (optional)
└── markdown_generator.py          # Markdown output generation
```

### Components

#### PDF Parser (`pdf_parser.py`)
**Hybrid approach: Package-based extraction + LLM interpretation**

- **PDFContent**: Raw content dataclass
- **PDFParser**: Main parser class
  - `extract_raw_content()`: Uses pdfplumber for text/tables
  - `interpret_with_llm()`: Uses LLM for intelligent parsing
  - `parse_pdf()`: Full pipeline

**Usage:**
```python
from src.parsing import PDFParser, extract_pdf

parser = PDFParser(llm_client=llm_client)
data = parser.parse_pdf("document.pdf", use_llm=True)
```

#### Markdown Parser (`markdown_parser.py`)
**Regex-based deterministic extraction**

- **MarkdownParser**: Regex-based parser
  - `parse_file()`: Parse single markdown file
  - `parse_directory()`: Parse all markdown files in directory
  - `_categorize_question()`: Auto-categorize questions

**Usage:**
```python
from src.parsing import MarkdownParser, parse_markdown_file

parser = MarkdownParser()
data = parser.parse_file("requirements.md")
```

#### Requirements Structurer (`requirements_structurer.py`)
**Unified data models and structuring**

**Data Models:**
- **Question**: Business question with metadata
- **TableInfo**: Table schema and description
- **SQLQuery**: SQL query with context
- **RequirementSection**: Categorized section
- **RequirementsDocument**: Complete document

**Usage:**
```python
from src.parsing import RequirementsStructurer, structure_requirements

structurer = RequirementsStructurer()
doc = structurer.structure_data(pdf_data, md_data)
```

#### LLM Enricher (`llm_enricher.py`)
**Optional LLM-based enrichment**

- **LLMEnricher**: Enrichment engine
  - `enrich_document()`: Add descriptions, summaries
  - `_enrich_tables()`: Generate table descriptions
  - `_enrich_queries()`: Generate query descriptions
  - `_generate_scenarios()`: Create business scenarios

**Usage:**
```python
from src.parsing import LLMEnricher, enrich_requirements

enricher = LLMEnricher(llm_client)
enriched_doc = enricher.enrich_document(doc)
```

#### Markdown Generator (`markdown_generator.py`)
**Template-based output generation**

- **MarkdownGenerator**: Output generator
  - `generate()`: Generate full markdown document
  - Follows `demo_requirements.md` structure
  - Categorized FAQ with emojis
  - Table sections with sample queries

**Usage:**
```python
from src.parsing import MarkdownGenerator, generate_markdown

markdown = generate_markdown(doc, "output.md")
```

### Parsing Pipeline Quick Start

#### Basic Usage (All-in-one)

```python
from src.parsing import (
    PDFParser,
    MarkdownParser,
    RequirementsStructurer,
    generate_markdown
)

# 1. Extract
pdf_parser = PDFParser()
pdf_data = pdf_parser.parse_pdf("doc.pdf", use_llm=False)

md_parser = MarkdownParser()
md_data = md_parser.parse_directory("requirements/")

# 2. Structure
structurer = RequirementsStructurer()
doc = structurer.structure_data(pdf_data, md_data)

# 3. Generate
markdown = generate_markdown(doc, "output.md")
```

#### With LLM Enrichment

```python
from src.parsing import (
    PDFParser,
    MarkdownParser,
    RequirementsStructurer,
    LLMEnricher,
    generate_markdown
)
from src.llm.databricks_llm import DatabricksFoundationModelClient

# Initialize LLM
llm_client = DatabricksFoundationModelClient(model_name="databricks-gpt-5-2")

# 1. Extract with LLM
pdf_parser = PDFParser(llm_client=llm_client)
pdf_data = pdf_parser.parse_pdf("doc.pdf", use_llm=True)

md_parser = MarkdownParser()
md_data = md_parser.parse_directory("requirements/")

# 2. Structure
structurer = RequirementsStructurer()
doc = structurer.structure_data(pdf_data, md_data)

# 3. Enrich (optional)
enricher = LLMEnricher(llm_client)
doc = enricher.enrich_document(doc)

# 4. Generate
markdown = generate_markdown(doc, "output.md")
```

### Data Flow

```
PDF Files → PDFParser (pdfplumber + LLM) → Structured JSON
                                                ↓
Markdown Files → MarkdownParser (regex) → Structured JSON
                                                ↓
                                    RequirementsStructurer
                                                ↓
                                        Unified Document
                                                ↓
                                    LLMEnricher (optional)
                                                ↓
                                      Enriched Document
                                                ↓
                                    MarkdownGenerator
                                                ↓
                                        Output Markdown
```

### Parsing Module Testing

Run tests for the parsing module:

```bash
pytest tests/test_requirements_converter.py -v
```

### Design Principles

1. **Modularity**: Each component is independent
2. **Flexibility**: LLM is optional, can work without it
3. **Extensibility**: Easy to add new parsers/generators
4. **Type Safety**: Dataclasses for structured data
5. **Testability**: Unit tests for all components

## Key Scripts Reference

### Configuration Generation
| Script | Purpose | Benchmark Coverage |
|--------|---------|-------------------|
| `scripts/generate_config_with_direct_benchmarks.py` ⭐ | Generate config with complete benchmark extraction | Complete (Recommended) |
| `main.py` | Generate config with LLM-based extraction | Partial (Traditional) |
| `scripts/update_benchmarks.py` | Fix benchmarks in existing config | Complete (Fixes existing) |

### Validation & Creation
| Script | Purpose | When to Use |
|--------|---------|------------|
| `scripts/validate_tables.py` | Validate tables and columns | Before every space creation |
| `scripts/validate_setup.py` | Validate environment setup | First time setup |
| `scripts/create_genie_space.py` | Create Genie space from config | After validation passes |
| `scripts/create_genie_space_workflow.sh` | End-to-end automation | Quick demos (skip benchmarks) |

### Parsing Pipeline
| Script | Purpose | Related Module |
|--------|---------|----------------|
| `scripts/convert_requirements.py` | Main requirements conversion pipeline | `src/parsing/` |
| `tests/test_requirements_converter.py` | Parsing module tests | `src/parsing/` |

### Documentation Files
| File | Description |
|------|-------------|
| [README.md](README.md) | Complete getting started guide and API reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design patterns |
| [CONVERSION_PIPELINE.md](CONVERSION_PIPELINE.md) | Requirements conversion pipeline documentation |
| [data/demo_requirements.md](data/demo_requirements.md) | Example requirements document |

## Best Practices

1. **Start Small**: Use focused requirements documents for better results
2. **Use Direct Benchmark Extraction**: Use `generate_config_with_direct_benchmarks.py` to ensure complete FAQ coverage
3. **Validate Tables First**: Always run `scripts/validate_tables.py` before creating spaces
4. **Iterate**: Generate multiple configurations with different temperatures
5. **Validate**: Always review the generated configuration before using it
6. **Define Joins**: Explicitly define table relationships in the `joins` section
7. **Test**: Use the benchmark questions to verify Genie space accuracy
8. **Refine**: Update the input requirements based on results

## Contributing

We welcome contributions to make Genie Lamp Agent better! Here's how you can help:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/genie-lamp-agent.git
cd genie-lamp-agent

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test
python -m pytest tests/

# Commit and push
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name
```

### Extension Points

1. **Add new Pydantic models** in `src/models.py`
2. **Enhance prompt templates** in `src/prompt/prompt_builder.py`
3. **Add new LLM providers** in `src/llm/databricks_llm.py`
4. **Add new API clients** in `src/api/`
5. **Add new utilities** in `src/utils/`
6. **Update the main script** for new features

### Pull Request Process

1. Ensure your code follows the existing style
2. Add tests for new functionality
3. Update documentation as needed
4. Submit a pull request with a clear description

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:

- 🐛 **Report bugs**: [GitHub Issues](https://github.com/Aiden-Jeon/genie-lamp-agent/issues)
- 💡 **Request features**: [GitHub Issues](https://github.com/Aiden-Jeon/genie-lamp-agent/issues)
- 📖 **Documentation**: Check Databricks Genie documentation
- 🔍 **Debugging**: Review the generated reasoning output
- ⚙️ **Customization**: Adjust prompt templates for your use case

## Repository

🔗 **GitHub**: [https://github.com/Aiden-Jeon/genie-lamp-agent](https://github.com/Aiden-Jeon/genie-lamp-agent)

---

Made with ❤️ for the Databricks community
