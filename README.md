# Genie Space Configuration Generator

This project generates Databricks Genie space configurations using LLMs via Databricks serving endpoints.

## Overview

The system takes documentation and requirements as input and generates a complete, production-ready Genie space configuration that can be used to create a Genie space via the API.

### Workflow

```
docs/curate_effective_genie.md  ──┐
                                  │
docs/genie_api.md               ──┤──> Prompt Builder ──> LLM (Databricks) ──> Pydantic Model ──> JSON Config
                                  │
data/demo_requirements.md       ──┘
```

## Recent Updates (January 2026)

### 🆕 Direct Benchmark Extraction
**Problem Solved:** LLMs were only extracting 26% of FAQ questions as benchmarks, missing 74% of important test scenarios.

**Solution:** New direct extraction system ensures 100% FAQ coverage:
- ✅ `scripts/generate_config_with_direct_benchmarks.py` - Generate config with complete benchmarks
- ✅ `scripts/update_benchmarks.py` - Fix benchmarks in existing configs
- ✅ Preserves exact question phrasing from requirements
- ✅ See [docs/BENCHMARK_EXTRACTION.md](docs/BENCHMARK_EXTRACTION.md) for details

### 🔍 Enhanced Table & Column Validation
Comprehensive validation system that checks Unity Catalog before space creation:
- ✅ Validates all table references exist
- ✅ Validates column references in SQL expressions
- ✅ Detailed error reporting with actionable fixes
- ✅ See [docs/TABLE_VALIDATION.md](docs/TABLE_VALIDATION.md) for details

### 🚀 2026 Databricks Genie API Features
- Pagination support for large space lists
- Partial updates (update title/description without full config)
- Serialized space export (requires CAN EDIT permission)
- Parent path support for workspace organization
- Trash (recoverable) vs permanent delete

## Features

- **Structured Prompts**: Builds comprehensive prompts with context, output format, and input data
- **Pydantic Models**: Type-safe configuration models that match Genie API requirements
- **Databricks Integration**: Direct integration with Databricks serving endpoints and foundation models
- **Schema Validation**: Automatic validation of LLM output against schema
- **Table & Column Validation**: Verify that all referenced tables and columns exist in Unity Catalog
- **Direct Benchmark Extraction**: Extract 100% of FAQ questions as benchmarks (no LLM filtering)
- **Reasoning**: Optional reasoning output to understand configuration choices

## Installation

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
2. ✅ **Extracts ALL 27 FAQ questions** directly as benchmarks (100% coverage)
3. ✅ Validates all tables and columns exist in Unity Catalog
4. ✅ Creates the Genie space with complete test coverage

**Why use this?**
- **100% benchmark coverage** vs 26% with LLM-only approach
- Preserves exact question phrasing from requirements
- Catches table/column errors before space creation
- Production-ready configuration

### Alternative: Automated Workflow (Faster but Incomplete)

**Best for:** Quick demos, prototyping

```bash
./scripts/create_genie_space_workflow.sh
```

**Limitations:**
- ⚠️ LLM-based benchmark extraction (only ~26% of FAQ questions)
- ⚠️ May miss important test scenarios
- ⚠️ Questions may be modified or filtered

**Recommendation:** Use the complete workflow above for production deployments.

### Workflow Comparison

| Feature | Complete Workflow ⭐ | Automated Workflow |
|---------|---------------------|-------------------|
| **Benchmark Coverage** | 100% (all 27 FAQs) | ~26% (7 questions) |
| **Question Accuracy** | Exact phrasing preserved | Modified/filtered by LLM |
| **Table Validation** | ✅ Explicit validation step | ❌ No validation |
| **Error Detection** | ✅ Before space creation | ❌ At runtime |
| **Production Ready** | ✅ Yes | ⚠️ Prototypes only |
| **Speed** | ~2-3 minutes | ~1-2 minutes |
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
- ✅ Extracts ALL FAQ questions directly from requirements (100% coverage)
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
  --context-doc docs/curate_effective_genie.md \
  --output-doc docs/genie_api.md \
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
Before (LLM extraction):  7 benchmarks  (26% coverage) ❌
After (Direct extraction): 27 benchmarks (100% coverage) ✅
```

This extracts ALL FAQ questions from your requirements document and replaces the LLM-generated benchmarks. 

**Why Direct Benchmark Extraction?**

Real-world analysis shows LLMs select only "representative" questions:

| Method | Coverage | Exact Match | Issues |
|--------|----------|-------------|---------|
| **LLM-based** | 26% (7/27) | 1 question | Modified phrasing, missing categories |
| **Direct extraction** | 100% (27/27) | All questions | None - exact preservation |

**Benefits:**
- ✅ **Complete coverage**: All 27 questions, not just 7
- ✅ **Exact phrasing**: Preserves original Korean question text
- ✅ **No filtering**: Includes all question types (KPI, sentiment, exploratory)
- ✅ **Deterministic**: Same result every time
- ✅ **Fast**: Completes in milliseconds

**Example output:**
```
✓ Extracted 27 benchmark questions from requirements
✓ Updated configuration with complete benchmarks
✓ Validation: 27/27 benchmarks valid (100%)
✓ Configuration saved to: output/genie_space_config.json
```

See [docs/BENCHMARK_EXTRACTION.md](docs/BENCHMARK_EXTRACTION.md) for complete details and analysis.

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

If validation fails, fix the issues in your configuration before proceeding to create the space.

**See [docs/TABLE_VALIDATION.md](docs/TABLE_VALIDATION.md) for detailed documentation.**

**See [docs/BENCHMARK_EXTRACTION.md](docs/BENCHMARK_EXTRACTION.md) for benchmark extraction details.**

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
│   ├── prompt_builder.py        # Builds structured prompts
│   ├── databricks_llm.py        # Databricks LLM client
│   ├── genie_space_client.py    # Genie space API client
│   ├── table_validator.py       # Table & column validator
│   ├── benchmark_extractor.py   # Extract benchmarks from requirements (NEW)
│   └── config_transformer.py    # Transform to Databricks format
├── docs/
│   ├── curate_effective_genie.md     # Best practices context
│   ├── genie_api.md                  # API documentation
│   ├── TABLE_VALIDATION.md           # Validation guide
│   ├── BENCHMARK_EXTRACTION.md       # Benchmark extraction guide (NEW)
│   ├── VALIDATION_QUICK_REFERENCE.md # Validation quick reference
│   └── VALIDATION_IMPLEMENTATION_SUMMARY.md # Implementation details
├── data/
│   └── demo_requirements.md     # Input requirements
├── output/
│   ├── genie_space_config.json  # Generated configuration
│   └── genie_space_result.json  # Creation result (space ID and URL)
├── examples/
│   ├── create_genie_space_example.py  # Python API examples
│   └── validate_tables_example.py     # Table validation examples
├── scripts/
│   ├── create_genie_space.py                      # Create Genie space
│   ├── validate_tables.py                         # Validate tables and columns
│   ├── create_genie_space_workflow.sh             # Automated workflow script
│   ├── validate_setup.py                          # Setup validation tool
│   ├── generate_config_with_direct_benchmarks.py  # Generate with full benchmarks (NEW)
│   └── update_benchmarks.py                       # Update existing config benchmarks (NEW)
├── main.py                      # Generate configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment file
├── README.md                    # This file
└── ARCHITECTURE.md              # System architecture documentation
```

## Output Schema

The generated configuration follows this structure:

```json
{
  "genie_space_config": {
    "space_name": "Fashion Retail Analytics",
    "description": "Natural language querying for fashion retail data",
    "purpose": "Enable business users to analyze sales and customer behavior",
    "tables": [
      {
        "catalog_name": "jongseob_demo",
        "schema_name": "fashion_recommendations",
        "table_name": "transactions",
        "description": "Transaction data table"
      }
    ],
    "joins": [
      {
        "left_table": "jongseob_demo.fashion_recommendations.transactions",
        "left_alias": "transactions",
        "right_table": "jongseob_demo.fashion_recommendations.articles",
        "right_alias": "articles",
        "join_condition": "`transactions`.`article_id` = `articles`.`article_id`",
        "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
      }
    ],
    "instructions": [
      {
        "content": "When users ask about sales without specifying time range..."
      }
    ],
    "example_sql_queries": [
      {
        "question": "What were the top selling products last week?",
        "sql_query": "SELECT product_name, COUNT(*) as sales FROM ...",
        "description": "Shows top 10 products by sales count"
      }
    ],
    "sql_expressions": [
      {
        "name": "daily_revenue",
        "expression": "SUM(total_amount)",
        "description": "Total revenue for the day",
        "type": "metric"
      }
    ],
    "benchmark_questions": [
      {
        "question": "What were the top 10 selling products last week?"
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

### 2. Prompt Builder (`src/prompt_builder.py`)

Constructs structured prompts with:

- **Instruction**: Task description and principles
- **Context**: Best practices from `curate_effective_genie.md`
- **Output**: API documentation from `genie_api.md`
- **Input**: Requirements from `demo_requirements.md`

### 3. LLM Client (`src/databricks_llm.py`)

Two client classes:

- `DatabricksLLMClient`: For custom serving endpoints
- `DatabricksFoundationModelClient`: For Databricks foundation models

Both support:
- JSON parsing and validation
- Error handling
- Response formatting

### 4. Config Transformer (`src/config_transformer.py`)

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

See `GENIE_CONFIG_GUIDE.md` for detailed transformation documentation.

### 5. Genie Space Client (`src/genie_space_client.py`)

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
Based on the requirements, I focused on the core transaction and product
tables as they form the foundation for most business questions...

Confidence Score: 95.00%

✓ Configuration saved to: output/genie_space_config.json

Configuration Summary:
--------------------------------------------------------------------------------
Space Name: Fashion Retail Analytics
Description: Natural language querying for fashion retail sales and customer data
Tables: 5
Instructions: 8
Example SQL Queries: 12
SQL Expressions: 6
Benchmark Questions: 10

================================================================================
Done!
================================================================================
```

## Advanced Usage

### Using as a Python Module

#### Generating Configuration

```python
from src import PromptBuilder, DatabricksFoundationModelClient

# Build prompt
builder = PromptBuilder(
    context_doc_path="docs/curate_effective_genie.md",
    output_doc_path="docs/genie_api.md",
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
print(f"Tables: {len(config.tables)}")
```

#### Creating Genie Space

```python
from src.genie_space_client import GenieSpaceClient, create_genie_space_from_file

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
from src.genie_space_client import GenieSpaceClient

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

You can modify `src/prompt_builder.py` to customize:

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

## Documentation

### Quick Reference
- **README.md** (this file): Installation, quick start, and API reference
- **ARCHITECTURE.md**: System architecture, component details, and integration flows
- **docs/BENCHMARK_EXTRACTION.md**: Complete guide to benchmark extraction (NEW)
- **docs/TABLE_VALIDATION.md**: Table and column validation guide
- **docs/VALIDATION_QUICK_REFERENCE.md**: Quick validation reference

### Configuration Format
The system supports a user-friendly configuration format that includes:
- **Tables**: Unity Catalog tables to include
- **Joins**: Explicit join specifications between tables
- **Instructions**: Text instructions guiding the AI
- **Example SQL Queries**: Example questions with SQL answers
- **SQL Expressions**: Reusable metric and dimension definitions
- **Benchmarks**: Test questions for validation

All configurations are automatically transformed to Databricks' internal `serialized_space` format when creating or updating Genie spaces.

For detailed configuration format documentation, see `GENIE_CONFIG_GUIDE.md`.

## Key Scripts Reference

### Configuration Generation
| Script | Purpose | Benchmark Coverage |
|--------|---------|-------------------|
| `scripts/generate_config_with_direct_benchmarks.py` ⭐ | Generate config with 100% benchmark extraction | 100% (Recommended) |
| `main.py` | Generate config with LLM-based extraction | ~26% (Traditional) |
| `scripts/update_benchmarks.py` | Fix benchmarks in existing config | 100% (Fixes existing) |

### Validation & Creation
| Script | Purpose | When to Use |
|--------|---------|------------|
| `scripts/validate_tables.py` | Validate tables and columns | Before every space creation |
| `scripts/validate_setup.py` | Validate environment setup | First time setup |
| `scripts/create_genie_space.py` | Create Genie space from config | After validation passes |
| `scripts/create_genie_space_workflow.sh` | End-to-end automation | Quick demos (skip benchmarks) |

### Documentation
| File | Description |
|------|-------------|
| [README.md](README.md) | This file - getting started guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [docs/BENCHMARK_EXTRACTION.md](docs/BENCHMARK_EXTRACTION.md) | Complete benchmark extraction guide |
| [docs/TABLE_VALIDATION.md](docs/TABLE_VALIDATION.md) | Table and column validation guide |
| [docs/VALIDATION_QUICK_REFERENCE.md](docs/VALIDATION_QUICK_REFERENCE.md) | Quick validation reference |

## Best Practices

1. **Start Small**: Use focused requirements documents for better results
2. **Use Direct Benchmark Extraction**: Use `generate_config_with_direct_benchmarks.py` to ensure 100% FAQ coverage (not 26%)
3. **Validate Tables First**: Always run `scripts/validate_tables.py` before creating spaces
4. **Iterate**: Generate multiple configurations with different temperatures
5. **Validate**: Always review the generated configuration before using it
6. **Define Joins**: Explicitly define table relationships in the `joins` section
7. **Test**: Use the benchmark questions to verify Genie space accuracy
8. **Refine**: Update the input requirements based on results

## Contributing

To extend this project:

1. Add new Pydantic models in `src/models.py`
2. Enhance prompt templates in `src/prompt_builder.py`
3. Add new LLM providers in `src/databricks_llm.py`
4. Update the main script for new features

## License

[Your License Here]

## Support

For issues or questions:
- Check Databricks Genie documentation
- Review the generated reasoning output
- Adjust prompt templates for your use case
