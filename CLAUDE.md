# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Genie Lamp Agent is an LLM-powered tool that automatically generates Databricks Genie space configurations from natural language requirements. It transforms business requirements documents into production-ready Genie space JSON configurations with comprehensive validation and deployment capabilities.

## Development Commands

### Environment Setup
```bash
# Always use the virtual environment
.venv/bin/python -m pip install -r requirements.txt

# Configure credentials (required)
cp .env.example .env
# Edit .env with DATABRICKS_HOST and DATABRICKS_TOKEN
```

### Running Tests
```bash
# Run all tests (LLM tests auto-skipped if src/llm/ not modified)
.venv/bin/python -m pytest tests/ -v

# Run specific test domains
.venv/bin/python -m pytest tests/test_generation_domain.py -v
.venv/bin/python -m pytest tests/test_validation_domain.py -v
.venv/bin/python -m pytest tests/test_requirements_domain.py -v
.venv/bin/python -m pytest tests/test_transformation_domain.py -v
.venv/bin/python -m pytest tests/test_integration.py -v

# Force run LLM tests (even if src/llm/ not modified)
RUN_LLM_TESTS=true .venv/bin/python -m pytest tests/ -v

# Force skip LLM tests
SKIP_LLM_TESTS=true .venv/bin/python -m pytest tests/ -v
```

**Note:** LLM tests are automatically skipped unless `src/llm/` has been modified. This speeds up test runs and avoids unnecessary API costs. To force running LLM tests, set `RUN_LLM_TESTS=true`.

### Main CLI Commands
```bash
# Full pipeline (recommended workflow)
.venv/bin/python genie.py create --requirements data/demo_requirements.md

# Parse documents (PDFs/markdown to structured format)
.venv/bin/python genie.py parse --input-dir real_requirements --output data/parsed.md

# Individual pipeline steps
.venv/bin/python genie.py generate --requirements data/parsed.md
.venv/bin/python genie.py validate
.venv/bin/python genie.py deploy

# Validation and setup utilities
.venv/bin/python scripts/validate_setup.py
```

## Architecture Overview

### High-Level Data Flow
```
Requirements Doc → LLM Generation → Validation → Deployment
                         ↓
                  Benchmark Extraction
```

### Core Components

1. **Pipeline Layer** (`src/pipeline/`)
   - **generator.py**: Orchestrates LLM-based config generation with prompt building
   - **validator.py**: Validates tables/columns against Unity Catalog with interactive replacement
   - **deployer.py**: Deploys configurations via Genie Space API
   - **parser.py**: Async PDF/markdown parsing with concurrent processing

2. **LLM Integration** (`src/llm/`)
   - **databricks_llm.py**: Databricks Foundation Model client with structured output support
   - Handles both text models (databricks-gpt-5-2) and vision models (databricks-claude-sonnet-4)

3. **Prompt Construction** (`src/prompt/`)
   - **prompt_builder.py**: Builds multi-part prompts from templates and requirements
   - Combines best practices, API specs, and user requirements into structured prompts
   - Templates in `src/prompt/templates/`:
     - `curate_effective_genie.md`: Databricks Genie best practices
     - `genie_api.md`: Genie Space API specification

4. **Validation & Utilities** (`src/utils/`)
   - **table_validator.py**: Unity Catalog table/column verification
   - **config_transformer.py**: Converts user-friendly format to Databricks `serialized_space` format

5. **API Integration** (`src/api/`)
   - **genie_space_client.py**: Complete Genie Space API wrapper (create, update, list, trash)

6. **Parsing System** (`src/parsing/`)
   - **pdf_parser.py**: Hybrid PDF parsing (pdfplumber + LLM vision models)
   - **markdown_parser.py**: Regex-based markdown extraction
   - **requirements_structurer.py**: Unified data models for requirements
   - **llm_enricher.py**: Optional LLM-based enrichment

### Key Data Models (`src/models.py`)

All models use Pydantic v2 for validation:
- **LLMResponseWithReasoning**: LLM output with reasoning and confidence
- **GenieSpaceConfig**: Complete Genie space configuration
- **TableDefinition**: Unity Catalog table specifications
- **JoinSpec**: Explicit join relationships between tables
- **Instruction**: AI guidance with markdown formatting support
- **ExampleSQLQuery**: Question + SQL + reasoning examples
- **SQLExpression**: Reusable metric/dimension definitions
- **BenchmarkQuestion**: Test questions for validation

## Important Patterns

### Virtual Environment Requirement
**ALWAYS use `.venv/bin/python` instead of `python` or `python3`**. This is enforced by `.cursor/rules/python-standards.mdc`.

### Validation Flow with Interactive Replacement
When table validation fails:
1. System identifies missing catalog.schema combinations
2. Prompts user for correct catalog/schema names
3. Automatically updates all references (tables, SQL expressions, example queries, benchmarks)
4. Re-validates configuration
5. Up to 3 validation attempts allowed

### Configuration Transformation
User-friendly JSON → `serialized_space` format transformation happens automatically in `config_transformer.py`. The system handles:
- Table definitions with join specifications
- Instructions (now supports markdown formatting)
- Example SQL queries
- SQL expressions (metrics/dimensions)
- Benchmark questions

### Benchmark Loading Strategy
Benchmarks are loaded from external JSON files (`benchmarks/benchmarks.json`) using the `benchmark_loader.py` module. This allows for curated, high-quality benchmark questions with expected SQL queries. The system automatically searches for benchmark files relative to the requirements path and loads them if available.

### Async PDF Parsing
PDF parsing runs asynchronously with concurrent processing:
- Default: 3 concurrent PDFs
- Configurable via `--max-concurrent` flag
- Progress bars via `tqdm`
- Per-page parsing enabled by default (2.21x faster)

## Output Files

All generated files go to `output/` directory:
- `genie_space_config.json`: Generated configuration
- `genie_space_result.json`: Deployment result with space ID and URL
- `validation_report.json`: Table/column validation details

## Testing Strategy

Tests are in `tests/` directory with `test_` prefix:
- `test_generation.py`: End-to-end config generation
- `test_table_validator.py`: Unity Catalog validation logic
- `test_requirements_converter.py`: PDF/markdown parsing
- `test_pdf_image_parsing.py`: Vision model PDF parsing
- `test_endpoint.py`: Databricks endpoint connectivity
- `test_join_specs.py`: Join specification handling

## Configuration & Environment

Required environment variables (`.env`):
- `DATABRICKS_HOST`: Workspace URL
- `DATABRICKS_TOKEN`: Personal access token

Optional environment variables:
- `LLM_MODEL`: Text model (default: databricks-gpt-5-2)
- `VISION_MODEL`: Vision model for PDFs (default: databricks-claude-sonnet-4)

## Code Organization Standards

From `.cursor/rules/python-standards.mdc`:
1. All test files must be in `tests/` directory
2. Test files must start with `test_` prefix
3. All markdown documentation (except README.md, ARCHITECTURE.md, CLAUDE.md) goes in `change_logs/` directory
4. Always use `.venv/bin/python` for Python commands

## Key Integration Points

### Databricks Foundation Models
- Uses serving endpoints for LLM access
- Supports structured output via Pydantic models
- Temperature: 0.1 (deterministic)
- Max tokens: 4000 (configurable)

### Unity Catalog Integration
- Validates table existence via SQL queries
- Checks column schemas match configuration
- Reports detailed validation errors with suggestions

### Genie Space API
Complete API wrapper in `src/api/genie_space_client.py`:
- `create_space()`: Deploy new spaces
- `update_space()`: Full or partial updates
- `list_spaces()`: Paginated listing
- `get_space()`: Fetch space details (optionally with serialized config)
- `trash_space()`: Soft delete (recoverable)

## Claude Code Skills

This project includes custom skills in the `.claude/skills/` directory to automate common workflows.

### Available Skills

**genie-commit**: Automated commit workflow with testing and validation
- Triggers: When asked to "commit changes" or "create a commit"
- Runs `.venv/bin/python -m pytest tests/ -v` before committing
- Follows conventional commit format (feat/fix/refactor/docs/test)
- Checks for sensitive files and validates staging
- See `.claude/skills/README.md` for installation instructions

### Installing Skills

To use the skills in Claude Code:

```bash
# Create symlink (recommended - updates automatically with repo)
ln -s "$(pwd)/.claude/skills/genie-commit" ~/.codex/skills/genie-commit

# Or copy to Claude Code skills directory
cp -r .claude/skills/genie-commit ~/.codex/skills/

# Restart Claude Code to load skills
```

## Common Workflows

### Adding New Features to Config Generation
1. Update Pydantic models in `src/models.py`
2. Modify prompt templates in `src/prompt/templates/`
3. Update `config_transformer.py` for serialized format
4. Add tests in `tests/test_generation.py`

### Adding New Validation Rules
1. Extend `table_validator.py` validation logic
2. Update validation report structure
3. Add tests in `tests/test_table_validator.py`

### Modifying Prompt Templates
Templates are markdown files in `src/prompt/templates/`:
- Edit `curate_effective_genie.md` for best practices
- Edit `genie_api.md` for API specifications
- Prompts are assembled by `PromptBuilder` class

### Requirements Document Format
Standard format includes:
- **Table Section**: Table names with sample queries
- **Business Context**: Domain-specific requirements
- **FAQ Section**: Business questions (optional, for reference)
- Supports both markdown and PDF input (parsed to standard format)

Note: Benchmarks are loaded from separate JSON files (`benchmarks/benchmarks.json`), not extracted from requirements documents.
