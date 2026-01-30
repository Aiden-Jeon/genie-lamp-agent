# Genie Lamp Agent 🧞

An intelligent agent that generates Databricks Genie space configurations using LLMs via Databricks serving endpoints.

[![GitHub Repository](https://img.shields.io/badge/GitHub-genie--lamp--agent-blue?style=flat&logo=github)](https://github.com/Aiden-Jeon/genie-lamp-agent)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Databricks](https://img.shields.io/badge/Databricks-Genie-FF3621?logo=databricks)](https://www.databricks.com/)

## 📚 Table of Contents

- [Overview](#overview)
- [Recent Updates](#recent-updates)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Support](#support)

## Recent Updates

### January 2026 ⭐

**🎯 Smart Parse Caching System**
- Automatic caching of parsing results to avoid expensive re-parsing operations
- Intelligent cache invalidation based on file changes, additions, or removals
- Significant time and cost savings (no repeated vision model API calls)
- Cache validated using file modification times, sizes, and parsing configuration
- Full user control: `--force` to bypass cache, `--no-cache` to disable, `--cache-file` for custom location
- Comprehensive test coverage (15 tests) for all caching scenarios
- Graceful handling of corrupted cache files and edge cases

**Benefits:**
- ⚡ **Instant response** when files haven't changed (vs 2-3 min re-parsing)
- 💰 **Cost savings** - no repeated vision model API calls
- 🔍 **Smart validation** - automatic cache invalidation when needed
- 🎛️ **User control** - explicit flags for cache management

## Overview

The Genie Lamp Agent automates the creation of Databricks Genie spaces by intelligently generating production-ready configurations from natural language requirements. Simply provide your business requirements and documentation, and let the agent handle the complex configuration process.

**Key Benefits:**
- 🚀 **Automated Configuration**: Transform requirements into production-ready Genie space configs
- ✅ **Complete Test Coverage**: Load curated benchmarks from JSON files for comprehensive testing
- 🔍 **Smart Validation**: Multi-layer validation (SQL syntax + instruction quality + comprehensive review)
- 🎯 **Best Practices Built-in**: Leverages Databricks Genie best practices automatically
- 🤖 **LLM-Powered**: Uses Databricks foundation models for intelligent configuration generation
- 🧠 **Domain Intelligence**: Automatically extracts domain knowledge from requirements
- 📊 **Quality Scoring**: 4-dimension quality assessment (SQL, instructions, joins, coverage)

### How It Works

```
📄 Best Practices Doc          ──┐
                                 │
📄 Genie API Specification     ──┤──> 🔨 Prompt Builder ──> 🤖 LLM (Databricks) ──> ✅ Validation ──> 📦 JSON Config
                                 │
📄 Your Requirements           ──┘
```

The agent follows a structured 7-step pipeline:
1. **Domain Extraction**: Automatically extracts table relationships, business metrics, and common filters
2. **Enhanced Prompt Building**: Injects domain knowledge + SQL quality criteria + few-shot examples
3. **LLM Generation**: Uses Databricks foundation models to generate intelligent configurations
4. **Benchmark Loading**: Loads benchmark questions from `benchmarks/benchmarks.json` (if available)
5. **SQL Validation**: Syntax checks, table references, join patterns, and quality scoring
6. **Comprehensive Review**: 4-dimension quality assessment with actionable feedback
7. **Output**: Produces a production-ready Genie space configuration with quality report


### ⚡ Performance Improvements

**Per-Page PDF Parsing (2.21x Faster)**
- PDF pages are now processed individually with async parallel execution
- **2.21x faster** than batch processing based on real-world benchmarks
- **Extracts more content**: +92% more questions, +24% more tables in tests
- Automatically enabled by default - no code changes needed
- See [PER_PAGE_PARSING.md](PER_PAGE_PARSING.md) for detailed benchmarks and configuration

**Async PDF Parsing with Progress Tracking**
- PDF parsing now runs asynchronously with concurrent processing
- Added real-time progress bars for tracking document processing
- Configurable concurrency level (default: 3 concurrent PDFs, adjustable with `--max-concurrent`)
- Significant performance improvements when processing multiple PDFs
- Uses `aiohttp` for async HTTP requests and `tqdm` for progress visualization

**Smart Parse Caching**
- Automatically caches parsing results to avoid expensive re-parsing
- Saves time and API costs (vision model calls) when requirements haven't changed
- Intelligent cache invalidation when files are modified, added, or removed
- Cache validated based on file modification times, sizes, and configuration
- Full control with `--force` (bypass cache) and `--no-cache` (disable caching)

**Usage:**
```bash
# Process PDFs with default concurrency (3)
python genie.py parse --input-dir docs/ --output data/requirements.md

# Process more PDFs simultaneously for faster results
python genie.py parse --input-dir docs/ --output data/requirements.md --max-concurrent 5

# Force re-parsing even if cache is valid
python genie.py parse --input-dir docs/ --output data/requirements.md --force

# Disable caching entirely
python genie.py parse --input-dir docs/ --output data/requirements.md --no-cache

# Custom cache file location
python genie.py parse --input-dir docs/ --output data/requirements.md --cache-file custom_cache.json
```

**Python API:**
```python
from src.pipeline.parser import parse_documents, parse_documents_async

# Synchronous (with async under the hood)
result = parse_documents(
    input_dir="docs/",
    max_concurrent_pdfs=5,
    force=False,              # Set to True to bypass cache
    cache_file=".parse_cache.json",  # Custom cache location
    no_cache=False            # Set to True to disable caching
)

# Check if cache was used
if result.get('cache_used'):
    print("✓ Used cached results (no re-parsing needed)")
else:
    print("✓ Parsed documents and updated cache")

# Direct async usage
import asyncio
result = asyncio.run(parse_documents_async(
    input_dir="docs/",
    max_concurrent_pdfs=5,
    force=False,
    no_cache=False
))
```

### 🔄 Interactive Catalog/Schema Replacement

**Smart Validation Failure Handling**
- When validation fails due to missing tables, the agent now prompts for correct catalog/schema names
- Automatically updates all references: tables, SQL expressions, and example queries
- Re-validates after updates to ensure correctness
- Up to 3 validation attempts with interactive prompts

**Example Workflow:**
```bash
.venv/bin/python genie.py create --requirements data/requirements.md

# If validation fails:
# ⚠️  TABLE VALIDATION FAILED
# The following catalog.schema combinations have tables that were not found:
#   1. main.log_discord (Tables: message, reaction)
# 
# Replace catalog/schema? [y/N]: y
# 
# Replacing: main.log_discord
#   New catalog (current: main): prod
#   New schema (current: log_discord): social_discord
#   ✓ Updated 2 table(s)
# 
# 🔄 Configuration updated. Re-validating...
```

**Benefits:**
- **No Manual Editing**: Updates configuration automatically
- **Comprehensive**: Updates tables, SQL expressions, and example queries
- **Safe**: Re-validates after each update
- **Time-Saving**: Eliminates trial-and-error with table names

See [changelogs/catalog-schema-replacement-feature.md](changelogs/catalog-schema-replacement-feature.md) for detailed documentation.

## Features

### Core Features
- **Structured Prompts**: Builds comprehensive prompts with context, output format, and input data
- **Pydantic Models**: Type-safe configuration models that match Genie API requirements
- **Databricks Integration**: Direct integration with Databricks serving endpoints and foundation models
- **Schema Validation**: Automatic validation of LLM output against schema
- **Table & Column Validation**: Verify that all referenced tables and columns exist in Unity Catalog
- **Benchmark Loading**: Load curated benchmark questions from external JSON files
- **Reasoning**: Optional reasoning output to understand configuration choices
- **Markdown-Formatted Instructions**: Generate well-structured instructions using markdown (headings, lists, bold, code blocks) for better readability and organization

### Quality Assurance Features

#### Enhanced Prompt Engineering
- **SQL Quality Criteria**: 6-point checklist for correct column references, explicit joins, aggregations, filters, and output formatting
- **Few-Shot Examples**: High vs low quality configuration examples to guide LLM generation
- **Instruction Guidelines**: 5 principles for specific, actionable, prioritized, and clear instructions
- **Join Specifications**: Explicit join relationship documentation for all table pairs

#### Automated Validation
- **SQL Validator**: Comprehensive SQL syntax, table/column verification, and quality checks
  - Validates example queries, SQL expressions, and benchmark queries
  - Detects: syntax errors, missing tables, incomplete joins, SELECT *, hard-coded dates, unsafe division
  - Provides severity-based feedback (critical, high, medium, low, info)
- **Instruction Scorer**: 3-dimension quality scoring (0-100 scale)
  - Specificity (40 pts): Concrete column names, table names, SQL patterns
  - Structure (30 pts): Markdown headers, lists, code blocks
  - Clarity (30 pts): No vague terms, actionable language
  - Letter grades (A-F) with actionable suggestions

#### Domain Intelligence & Comprehensive Review
- **Domain Knowledge Extractor**: Automatically extracts from requirements:
  - Table relationships (one-to-one, one-to-many, many-to-one, many-to-many)
  - Business metrics (formulas, aggregations, KPIs)
  - Common filters (status, date, boolean flags)
  - Business terminology (glossary terms, acronyms)
  - Sample queries with context
- **Config Review Agent**: 4-dimension quality assessment
  - SQL Validation Score (35%): Syntax + table references + join patterns
  - Instruction Quality Score (25%): Average score across all instructions
  - Join Completeness Score (20%): Coverage of required table relationships
  - Coverage Score (20%): Example queries per table + benchmark questions + SQL expressions
  - Overall pass/fail with actionable feedback for each issue

### Test Coverage
✅ **83/83 tests passing** across all features:
- Enhanced Prompt Engineering: 7 tests (prompts, join specs, instruction patterns)
- Automated Validation: 45 tests (SQL validation + instruction scoring)
- Domain Intelligence & Review: 31 tests (domain extraction + comprehensive review)

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

## Configuration

Set your Databricks credentials using a `.env` file (recommended):

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```bash
# Required Configuration
DATABRICKS_HOST=https://your-workspace.databricks.com
DATABRICKS_TOKEN=your-personal-access-token

# Optional Model Configuration
# LLM model for text-based tasks (enrichment, config generation)
LLM_MODEL=databricks-gpt-5-2

# Vision model for image-based PDF parsing
# Recommended: databricks-claude-sonnet-4 (13.7s per page)
# Alternative: databricks-claude-sonnet-4-5 (14.0s per page)
VISION_MODEL=databricks-claude-sonnet-4
```

Alternatively, you can use environment variables:
```bash
# Required
export DATABRICKS_HOST="https://your-workspace.databricks.com"
export DATABRICKS_TOKEN="your-personal-access-token"

# Optional (uses defaults if not set)
export LLM_MODEL="databricks-gpt-5-2"
export VISION_MODEL="databricks-claude-sonnet-4"
```

**Configuration Details:**

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DATABRICKS_HOST` | ✅ Yes | - | Your Databricks workspace URL |
| `DATABRICKS_TOKEN` | ✅ Yes | - | Personal access token |
| `LLM_MODEL` | No | `databricks-gpt-5-2` | Text-based LLM for config generation and enrichment |
| `VISION_MODEL` | No | `databricks-claude-sonnet-4` | Vision model for image-based PDF parsing |

**Model Recommendations:**
- For **image-based PDF parsing**, use `databricks-claude-sonnet-4` (13.7s/page) or `databricks-claude-sonnet-4-5` (14.0s/page)
- For **text-based enrichment and config generation**, use `databricks-gpt-5-2` (default)
- Models can be overridden via CLI arguments (`--llm-model`, `--vision-model`, `--model`)

Or provide them as command-line arguments (see Usage).

## Quick Start

### Complete Workflow (Recommended)

Create a Genie space from requirements in **one command**:

```bash
python genie.py create --requirements sample/inputs/demo_requirements.md
```

**That's it!** This single command will:
1. ✅ Extract domain knowledge from requirements (relationships, metrics, filters)
2. ✅ Generate configuration using LLM with enhanced prompts
3. ✅ Load benchmark questions from external JSON files (if available)
4. ✅ Validate SQL syntax, table references, and instruction quality
5. ✅ Run comprehensive 4-dimension quality review
6. ✅ Validate tables and columns exist in Unity Catalog
7. ✅ Create the Genie space in your workspace

Your Genie space is ready to use!

#### Enable Full Quality Validation (Recommended)

For best results, enable all validation and review features:

```bash
python genie.py create \
  --requirements sample/inputs/demo_requirements.md \
  --validate-sql \
  --validate-instructions \
  --review-config \
  --validation-output output/validation_report.json \
  --review-output output/review_report.json
```

This provides:
- **SQL Validation Report**: All SQL errors and warnings with suggestions
- **Instruction Quality Report**: Scores and improvement suggestions for each instruction
- **Comprehensive Review Report**: Overall quality score (0-100) with pass/fail status and detailed issues
- **Actionable Feedback**: Specific recommendations for improvement

### Parsing Documents (Optional)

If you have PDF or markdown documents that need to be converted to the standard format:

```bash
# Parse documents into structured requirements (with concurrent processing + caching)
python genie.py parse --input-dir real_requirements/inputs --output data/my_requirements.md

# Second run with same files - instant response from cache! ⚡
python genie.py parse --input-dir real_requirements/inputs --output data/my_requirements.md
# ✓ Using cached results (no changes detected)

# Process multiple PDFs faster with increased concurrency
python genie.py parse --input-dir real_requirements/inputs --output data/my_requirements.md --max-concurrent 5

# Force re-parse when needed (bypasses cache)
python genie.py parse --input-dir real_requirements/inputs --output data/my_requirements.md --force

# Then create Genie space
python genie.py create --requirements data/my_requirements.md
```

This is useful when you have:
- PDF documents with requirements (processed concurrently with progress bars)
- Markdown files in non-standard format
- Multiple source documents to combine

**Performance Notes**: 
- PDF parsing now runs asynchronously with progress tracking
- Use `--max-concurrent` to control concurrent PDFs (default: 3)
- Parsing results are automatically cached to avoid expensive re-parsing
- Subsequent runs with unchanged files return instantly from cache
- Use `--force` to bypass cache when needed

### Step-by-Step (Advanced)

For more control, run individual steps:

```bash
# Parse documents (if needed)
python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md

# Generate config only
python genie.py generate --requirements data/parsed.md

# Validate config
python genie.py validate

# Deploy config
python genie.py deploy
```

### Interactive Table Replacement

When validation fails due to missing tables, the system offers **interactive replacement** with two modes:

**Mode 1: Bulk Replacement** - Replace catalog.schema for all failed tables at once:
```bash
# When tables fail validation, you'll see:
Choose replacement mode:
  1. Bulk replacement (replace catalog.schema for all tables)
  2. Individual replacement (replace catalog.schema.table one by one)
  3. Cancel

# Example: Change dev.sales.* to prod.analytics.*
Enter choice [1/2/3]: 1
Replacing: dev.sales
  New catalog (current: dev): prod
  New schema (current: sales): analytics
```

**Mode 2: Individual Replacement** - Replace catalog.schema.table for each failed table:
```bash
# Useful when table names also differ between environments
Enter choice [1/2/3]: 2
Table 1/2: dev.sales.customer_data
  New catalog (current: dev): prod
  New schema (current: sales): analytics
  New table (current: customer_data): customers
```

The system automatically updates:
- ✅ Table definitions (catalog, schema, table names)
- ✅ SQL expressions and queries
- ✅ Join specifications and conditions
- ✅ Join aliases (e.g., `customer_data` → `customers`)
- ✅ Benchmark questions
- ✅ Instructions

After replacement, validation runs again automatically (up to 3 attempts).



### Common Options

```bash
# Use different model
python genie.py create --requirements sample/inputs/demo_requirements.md --model llama-3-1-70b

# Skip validation (faster, but risky)
python genie.py create --requirements sample/inputs/demo_requirements.md --skip-validation

# Custom output path
python genie.py create --requirements sample/inputs/demo_requirements.md --output my_config.json

# See all options
python genie.py create --help
```

## Usage

### Command-Line Interface

The `genie.py` CLI provides all the functionality you need:

```bash
# Parse documents (optional first step)
python genie.py parse --input-dir <directory-with-documents>

# Full pipeline (recommended)
python genie.py create --requirements <path-to-requirements>

# Individual steps
python genie.py generate --requirements <path-to-requirements>
python genie.py validate [--config <config-path>]
python genie.py deploy [--config <config-path>]
```

### Common Examples

```bash
# Parse documents first
python genie.py parse --input-dir real_requirements/inputs --output data/my_requirements.md

# Parse without LLM (faster)
python genie.py parse \
  --input-dir real_requirements/inputs \
  --output data/my_requirements.md \
  --no-llm

# Parse with custom models
python genie.py parse \
  --input-dir real_requirements/inputs \
  --output data/my_requirements.md \
  --llm-model databricks-gpt-5-2 \
  --vision-model databricks-claude-sonnet-4

# Parse with cache control
python genie.py parse \
  --input-dir real_requirements/inputs \
  --output data/my_requirements.md \
  --force  # Force re-parse even if cached

# Create space with default settings
python genie.py create --requirements sample/inputs/demo_requirements.md

# Use another model
python genie.py create \
  --requirements sample/inputs/demo_requirements.md \
  --model databricks-claude-sonnet-4-5

# Generate only (for review before deployment)
python genie.py generate --requirements sample/inputs/demo_requirements.md
# Review: cat output/genie_space_config.json
python genie.py validate
python genie.py deploy

# Full workflow with parsing
python genie.py parse --input-dir docs --output data/parsed.md
python genie.py create --requirements data/parsed.md

# Skip validation (faster, but risky)
python genie.py create \
  --requirements sample/inputs/demo_requirements.md \
  --skip-validation

# Custom output paths
python genie.py create \
  --requirements sample/inputs/demo_requirements.md \
  --output my_config.json \
  --result-output my_result.json
```

### All Options

See all available options for any command:

```bash
python genie.py parse --help
python genie.py create --help
python genie.py generate --help
python genie.py validate --help
python genie.py deploy --help
```

### What Happens During Creation

When you run `python genie.py create --requirements <path>`:

1. **Generate Configuration** - LLM creates table specs, instructions, SQL examples
2. **Load Benchmarks** - Load benchmark questions from JSON files (if available)
3. **Validate Tables** - Checks Unity Catalog for table/column existence
4. **Deploy Space** - Creates Genie space via API

Each step provides clear progress indicators and error messages if something fails.

> **📖 For detailed architecture information**, see [ARCHITECTURE.md](ARCHITECTURE.md) which includes:
> - Project structure and component details
> - Output schema and configuration format
> - Data flow diagrams and module dependencies
> - Integration patterns and best practices

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

You can use the pipeline functions programmatically:

```python
from src.pipeline import generate_config, validate_config, deploy_space

# Generate configuration with full quality validation
config = generate_config(
    requirements_path="sample/inputs/demo_requirements.md",
    output_path="output/config.json",
    model="databricks-gpt-5-2",

    # Enable all quality features
    extract_domain=True,              # Extract domain knowledge
    validate_sql=True,                # SQL validation
    validate_instructions=True,       # Instruction scoring
    review_config=True,               # Comprehensive review
    validation_output="output/validation.json",
    review_output="output/review.json"
)

# Check quality metrics
if "_review_report" in config:
    review = config["_review_report"]
    print(f"Overall Score: {review['overall_score']:.1f}/100")
    print(f"Passed: {review['passed']}")

    if review["passed"]:
        print("✅ Configuration is production-ready!")
    else:
        print("❌ Configuration needs improvement")
        # Review detailed issues in output/review.json

# Validate Unity Catalog tables
report = validate_config(config_path="output/config.json")
if report.has_errors():
    print("Validation failed!")
    print(report.summary())
    exit(1)

# Deploy
result = deploy_space(config_path="output/config.json")
print(f"Space URL: {result['space_url']}")
```

### Using Low-Level Components

For more control, use the underlying components directly:

```python
from src.prompt.prompt_builder import PromptBuilder
from src.llm.databricks_llm import DatabricksFoundationModelClient
from src.benchmark.benchmark_extractor import extract_all_benchmarks

# Build prompt
builder = PromptBuilder(
    context_doc_path="src/prompt/templates/curate_effective_genie.md",
    output_doc_path="src/prompt/templates/genie_api.md",
    input_data_path="sample/inputs/demo_requirements.md"
)
prompt = builder.build_prompt_with_reasoning()

# Call LLM
client = DatabricksFoundationModelClient(model_name="databricks-gpt-5-2")
response = client.generate_genie_config(prompt)

# Extract benchmarks
benchmarks = extract_all_benchmarks("sample/inputs/demo_requirements.md")

# Access configuration
config = response.genie_space_config
print(f"Generated space: {config.space_name}")
print(f"Number of tables: {len(config.tables)}")
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
- **[src/prompt/templates/guide_prompt_with_reasoning.md](src/prompt/templates/guide_prompt_with_reasoning.md)**: Enhanced prompt template with SQL quality criteria and few-shot examples

### Configuration Format
The system supports a user-friendly configuration format that includes:
- **Tables**: Unity Catalog tables to include
- **Joins**: Explicit join specifications between tables
- **Instructions**: Text instructions guiding the AI (with markdown formatting support)
- **Example SQL Queries**: Example questions with SQL answers
- **SQL Expressions**: Reusable metric and dimension definitions
- **Benchmarks**: Test questions for validation (loaded from `benchmarks/benchmarks.json`)

### Sample Data Structure

The project includes a `sample/` directory with example data to help you get started:

```
sample/
├── inputs/                          # Sample requirements documents
│   └── demo_requirements.md         # Fashion Retail Analytics demo
└── benchmarks/                      # Sample benchmark questions
    └── benchmarks.json              # 27 categorized FAQ questions
```

**Fashion Retail Analytics Demo:**
- Complete requirements document with FAQ, table specs, and sample queries
- Covers 7 tables: transactions, customers, articles, product sales, etc.
- Includes 27 business questions categorized by type (KPI, Sentiment, Cross-Analysis)
- Ready to use with: `python genie.py create --requirements sample/inputs/demo_requirements.md`

## Benchmark Questions

The system automatically loads benchmark questions from a structured JSON file if present. This allows you to maintain high-quality test questions with expected SQL queries separately from your requirements documents.

**Directory Structure:**
```
your_project/
├── inputs/                          # Original requirements documents
│   ├── requirements.pdf
│   └── specifications.md
└── benchmarks/                      # Benchmark questions
    └── benchmarks.json              # Structured benchmark file
```

**Benchmark JSON Format:**
```json
[
  {
    "question": "지난 주 가장 많이 팔린 제품은 무엇인가요?",
    "category": "KPI & Sales Analysis",
    "difficulty": "easy",
    "tags": ["sales", "product", "ranking"]
  },
  {
    "question": "긍정/부정 리뷰 동향이 있었는데, 반응이 많은 상세 내용을 요약해서 추출해줘",
    "category": "Sentiment & Trend Analysis",
    "difficulty": "hard",
    "tags": ["sentiment", "review", "summary"]
  }
]
```

**Required Fields:**
- `question`: The benchmark question (required)

**Optional Fields:**
- `category`: Question category (e.g., "KPI & Sales Analysis", "Sentiment & Trend Analysis")
- `difficulty`: Difficulty level ("easy", "medium", "hard")
- `tags`: Array of relevant tags for filtering
- `expected_sql`: Expected SQL query for validation
- `korean_question`: Korean translation (or use `question` directly)
- `source_file`: Source document reference

**Loading Behavior:**
- System searches for `benchmarks/benchmarks.json` relative to your requirements path
- If found, benchmarks are automatically loaded into the generated Genie config
- If not found, benchmark section remains empty
- Benchmarks preserve the `expected_sql` field for later validation

**Example:**
```bash
# Generate config - benchmarks auto-loaded from real_requirements/benchmarks/benchmarks.json
python genie.py generate --requirements real_requirements/inputs/requirements.pdf
```

**Markdown-Formatted Instructions**: The system now recommends using markdown formatting in instruction content for better structure and readability:
- Use `##` for section headings to organize related instructions
- Use bullet lists (`-`) for multiple related points
- Use **bold** for emphasis on critical terms or actions
- Use `code blocks` or inline `code` for column names, table names, or SQL keywords
- Use numbered lists for sequential steps or priorities

Example well-formatted instruction:
```markdown
## Date and Time Handling
- Always use `event_date` column for date-based queries
- Default to **last 30 days** when no time period is specified
- Use `CURRENT_DATE()` for "today" and `DATE_SUB(CURRENT_DATE(), 30)` for "last 30 days"

## Clarification Questions
When users ask about performance but don't specify time range, ask:
> "To analyze performance, please specify: (1) time period (e.g., last month, Q1 2024)"
```

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

## Scripts Reference

### Main CLI
| Command | Purpose | When to Use |
|---------|---------|------------|
| `genie.py parse` | Parse documents into structured requirements | Convert PDFs/markdown to standard format |
| `genie.py create` | Full pipeline (generate → validate → deploy) | Primary workflow (recommended) |
| `genie.py generate` | Generate configuration only | When you want to review config before deploying |
| `genie.py validate` | Validate tables and columns | After manual config edits |
| `genie.py deploy` | Deploy existing configuration | After validation passes |

### Utility Scripts
| Script | Purpose | When to Use |
|--------|---------|------------|
| `scripts/validate_setup.py` | Validate environment setup | First time setup, troubleshooting |
| `scripts/convert_requirements.py` | Convert requirements documents | Processing PDFs/markdown to standard format |
| `scripts/auto_deploy.py` | Automated deployment with catalog replacement | Automated workflows with known catalog/schema |
| `scripts/analyze_feedback.py` | Analyze Genie Space feedback results | Quality assessment and improvement |
| `scripts/export_feedback_csv.py` | Export feedback to CSV format | Detailed analysis in Excel/Sheets |

### Documentation Files
| File | Description |
|------|-------------|
| [README.md](README.md) | Complete getting started guide and API reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design patterns |
| [sample/inputs/demo_requirements.md](sample/inputs/demo_requirements.md) | Example requirements document |
| [sample/benchmarks/benchmarks.json](sample/benchmarks/benchmarks.json) | Example benchmark questions |

## Feedback Analysis System

After deploying a Genie Space, you can evaluate its quality by analyzing user feedback and response accuracy. The feedback system provides comprehensive analysis tools.

### Analyzing Genie Space Responses

**Step 1: Generate Feedback Data**
- Ask questions to your Genie Space
- Capture responses, assessments (Good/Bad), and reasons
- Save results to a markdown file

**Step 2: Analyze Feedback**
```bash
# Generate comprehensive analysis report
.venv/bin/python scripts/analyze_feedback.py feedback/results.md

# Output includes:
# - Success rate statistics
# - Failure reason breakdown
# - Common error patterns
# - Detailed entry examples
```

**Step 3: Export to CSV for Detailed Analysis**
```bash
# Export to CSV for Excel/Google Sheets
.venv/bin/python scripts/export_feedback_csv.py feedback/results.md

# Creates both:
# - feedback/results_summary.csv (high-level summary)
# - feedback/results_detailed.csv (detailed analysis)
```

### Feedback Entry Format

The feedback parser expects markdown files with entries like:
```markdown
---
### Question: How many users registered last month?
**Assessment**: Bad
**Score Reasons**: 
- Incorrect table reference
- Missing date filter

**Model Output (SQL)**:
```sql
SELECT COUNT(*) FROM users WHERE created_date > '2024-01-01'
```

**Ground Truth SQL**:
```sql
SELECT COUNT(*) FROM user_registrations 
WHERE registration_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
  AND registration_date < DATE_TRUNC('month', CURRENT_DATE)
```
---
```

### Feedback Analysis Features

- **Success Rate Tracking**: Overall good vs bad response rates
- **Failure Pattern Analysis**: Most common error types
- **SQL Comparison**: Ground truth vs model output differences
- **Empty Result Detection**: Queries that return no data
- **Reason Categorization**: Automated classification of issues

### Using Feedback to Improve Configurations

1. **Identify Common Failures**: Review failure reasons
2. **Update Instructions**: Add clarification for common mistakes
3. **Refine SQL Expressions**: Fix frequently misunderstood metrics
4. **Add Examples**: Include example queries for problematic patterns
5. **Re-deploy**: Update Genie Space with improvements
6. **Re-test**: Verify improvements with same questions

### Automated Deployment

For automated workflows, use the auto-deploy script:

```bash
# Auto-deploy with catalog replacement
.venv/bin/python scripts/auto_deploy.py \
  --requirements data/parsed.md \
  --catalog sandbox \
  --schema agent_poc

# This automatically:
# 1. Generates configuration
# 2. Replaces all catalog.schema references
# 3. Validates tables
# 4. Deploys space
```

## Best Practices

1. **Use the Unified CLI**: Use `genie.py create` for the complete workflow
2. **Start Small**: Use focused requirements documents for better results
3. **Review Before Deploy**: Use `genie.py generate` to review configs before deployment
4. **Validate Always**: The create command validates by default (don't skip it!)
5. **Define Joins**: Explicitly define table relationships in requirements
6. **Test Thoroughly**: Use benchmark questions to verify Genie space accuracy
7. **Iterate**: Generate multiple configurations with different temperatures
8. **Refine**: Update input requirements based on results

## Contributing

We welcome contributions to make Genie Lamp Agent better! Here's how you can help:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/genie-lamp-agent.git
cd genie-lamp-agent

# Install Claude Code skills (optional but recommended)
./.claude/install-skills.sh

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test (LLM tests auto-skipped if src/llm/ not modified)
.venv/bin/python -m pytest tests/

# To force run LLM tests:
RUN_LLM_TESTS=true .venv/bin/python -m pytest tests/

# Commit and push (use genie-commit skill or manual)
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name
```

### Claude Code Skills

This project includes custom skills for Claude Code in `.claude/skills/`:

- **genie-commit**: Automated commit workflow with testing and validation

To install:
```bash
./.claude/install-skills.sh
# Then restart Claude Code
```

See `.claude/skills/README.md` for details.

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
