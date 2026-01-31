# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Genie Lamp Agent is an LLM-powered tool that automatically generates Databricks Genie space configurations from natural language requirements. It transforms business requirements documents into production-ready Genie space JSON configurations with comprehensive validation and deployment capabilities.

## Project Rules

**IMPORTANT:** This project has specific rules that must be followed. These rules are located in `.claude/rules/` directory:

- **`.claude/rules/python-venv.md`**: Python virtual environment usage (CRITICAL - always use `.venv/bin/python`)
- **`.claude/rules/app-permissions.md`**: ⚠️ App service principal permissions (CRITICAL - never delete permissions)
- **`.claude/rules/README.md`**: Overview of all rules and how they work

These rules override default behavior and enforce project-specific standards. Always consult the rules when:
- Suggesting Python commands
- Writing scripts
- Running tests
- Installing dependencies
- **Working with app deployment or permissions** ⚠️

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
# Run all tests (LLM tests auto-skipped if genie/llm/ not modified)
.venv/bin/python -m pytest tests/ -v

# Run specific test domains
.venv/bin/python -m pytest tests/test_generation_domain.py -v
.venv/bin/python -m pytest tests/test_validation_domain.py -v
.venv/bin/python -m pytest tests/test_requirements_domain.py -v
.venv/bin/python -m pytest tests/test_transformation_domain.py -v
.venv/bin/python -m pytest tests/test_integration.py -v

# Force run LLM tests (even if genie/llm/ not modified)
RUN_LLM_TESTS=true .venv/bin/python -m pytest tests/ -v

# Force skip LLM tests
SKIP_LLM_TESTS=true .venv/bin/python -m pytest tests/ -v
```

**Note:** LLM tests are automatically skipped unless `genie/llm/` has been modified. This speeds up test runs and avoids unnecessary API costs. To force running LLM tests, set `RUN_LLM_TESTS=true`.

### Main CLI Commands
```bash
# Full pipeline (recommended workflow)
.venv/bin/python genie.py create --requirements real_requirements/parsed/parsed_requirements.md

# Parse documents (PDFs/markdown to structured format)
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output real_requirements/parsed/parsed_requirements.md

# Individual pipeline steps
.venv/bin/python genie.py generate --requirements real_requirements/parsed/parsed_requirements.md
.venv/bin/python genie.py validate
.venv/bin/python genie.py deploy

# Validation and setup utilities
.venv/bin/python scripts/validate_setup.py
```

## Architecture Overview

### Directory Structure

```
genie-lamp-agent/
├── .claude/                          # Claude Code configuration & skills
├── .venv/                            # Root Python environment (ignored)
├── archive/                          # Archived code (pre-restructure)
│   └── 2026-02-01-pre-restructure/
│       └── src/                      # Old package structure
├── backend/                          # FastAPI service for web app
│   ├── middleware/                   # Authentication middleware
│   ├── services/                     # Job manager, file storage, validators
│   ├── main.py                       # FastAPI app entry point
│   └── requirements.txt              # Backend Python dependencies
├── frontend/                         # Next.js web interface
│   ├── app/                          # Next.js pages
│   ├── components/                   # React components
│   ├── lib/                          # Utilities and hooks
│   └── package.json                  # Frontend dependencies
├── genie/                            # Core Python package (formerly src/)
│   ├── api/                          # Genie Space API client
│   ├── benchmark/                    # Benchmark loading utilities
│   ├── llm/                          # LLM integration
│   ├── parsing/                      # PDF/markdown parsers
│   ├── pipeline/                     # Generator, validator, deployer
│   ├── prompt/                       # Prompt construction
│   └── utils/                        # Table validator, transformers
├── scripts/                          # Deployment and utility scripts
├── tests/                            # Test suite
├── real_requirements/                # Production requirements & benchmarks (ignored)
│   ├── inputs/                       # Source PDFs and markdown
│   ├── benchmarks/
│   │   └── benchmarks.json           # Production benchmark questions
│   └── parsed/
│       └── parsed_requirements.md    # Parsed production requirements
├── sample/                           # Demo data
│   └── benchmarks/
│       └── benchmarks.json           # Example benchmarks for demos
├── output/                           # Generated configurations (ignored)
│   ├── genie_space_config.json       # Current generated config
│   ├── genie_space_result.json       # Deployment result
│   └── archive/                      # Historical test artifacts
├── app.yaml                          # Databricks Apps runtime config
├── databricks.yml                    # Asset bundle config
├── genie.py                          # CLI entry point
└── requirements.txt                  # Root Python dependencies
```

### Web Application

The project includes a multi-user web application for interactive Genie space generation:

**Backend** (`backend/`):
- FastAPI service with async job processing
- Session management with SQLite storage
- File upload and storage
- Benchmark validation
- Databricks authentication middleware

**Frontend** (`frontend/`):
- Next.js application with TypeScript
- Multi-step wizard interface (parse → generate → validate → deploy)
- Real-time job progress tracking
- Session sidebar with history
- Interactive validation fixing

**Deployment:**
```bash
# Deploy to Databricks Apps
databricks bundle deploy
```

### High-Level Data Flow
```
Requirements Doc → LLM Generation → Validation → Deployment
                         ↓
                  Benchmark Extraction
```

### Core Components

1. **Pipeline Layer** (`genie/pipeline/`)
   - **generator.py**: Orchestrates LLM-based config generation with prompt building
   - **validator.py**: Validates tables/columns against Unity Catalog with interactive replacement
   - **deployer.py**: Deploys configurations via Genie Space API
   - **parser.py**: Async PDF/markdown parsing with concurrent processing

2. **LLM Integration** (`genie/llm/`)
   - **databricks_llm.py**: Databricks Foundation Model client with structured output support
   - Handles both text models (databricks-gpt-5-2) and vision models (databricks-claude-sonnet-4)

3. **Prompt Construction** (`genie/prompt/`)
   - **prompt_builder.py**: Builds multi-part prompts from templates and requirements
   - Combines best practices, API specs, and user requirements into structured prompts
   - Templates in `genie/prompt/templates/`:
     - `curate_effective_genie.md`: Databricks Genie best practices
     - `genie_api.md`: Genie Space API specification

4. **Validation & Utilities** (`genie/utils/`)
   - **table_validator.py**: Unity Catalog table/column verification
   - **config_transformer.py**: Converts user-friendly format to Databricks `serialized_space` format

5. **API Integration** (`genie/api/`)
   - **genie_space_client.py**: Complete Genie Space API wrapper (create, update, list, trash)

6. **Parsing System** (`genie/parsing/`)
   - **pdf_parser.py**: Hybrid PDF parsing (pdfplumber + LLM vision models)
   - **markdown_parser.py**: Regex-based markdown extraction
   - **requirements_structurer.py**: Unified data models for requirements
   - **llm_enricher.py**: Optional LLM-based enrichment

### Key Data Models (`genie/models.py`)

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

### Git Worktree Workflow
**MANDATORY: Always use Git worktrees for new tasks.** Never work directly on the main branch.

#### Creating a New Worktree
When starting any new task, feature, or fix, create a dedicated worktree:

```bash
# Create worktree with branch name
git worktree add worktrees/<branch-name> -b <branch-name>

# Examples
git worktree add worktrees/feat/add-validation -b feat/add-validation
git worktree add worktrees/fix/parsing-bug -b fix/parsing-bug
git worktree add worktrees/refactor/cleanup-llm -b refactor/cleanup-llm
```

#### Working in Worktrees
Change to the worktree directory and work normally:

```bash
cd worktrees/feat/add-validation

# Work normally - virtual environment is shared
.venv/bin/python -m pytest tests/ -v

# Commit changes
git add .
git commit -m "feat: Add validation feature"
```

#### After Merging to Main
Clean up the worktree after the branch is merged:

```bash
# Return to main repository
cd ../..

# Remove the worktree
git worktree remove worktrees/feat/add-validation

# Delete the merged branch
git branch -d feat/add-validation
```

#### Listing and Managing Worktrees
```bash
# List all worktrees
git worktree list

# Remove worktree if branch is deleted
git worktree prune
```

#### Why Use Worktrees?
1. **Isolation**: Each task has its own working directory
2. **Context switching**: No need to stash or commit incomplete work
3. **Parallel work**: Work on multiple tasks simultaneously
4. **Safety**: Main branch stays clean and untouched
5. **Easy cleanup**: Remove worktree directory after merge

### Virtual Environment Requirement
**ALWAYS use `.venv/bin/python` instead of `python` or `python3`**. This is enforced by `.claude/rules/python-venv.md`. See the rules file for complete usage guidelines and examples.

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

**Project Rules:** See `.claude/rules/` for detailed project-specific rules.

Key standards:
1. All test files must be in `tests/` directory
2. Test files must start with `test_` prefix
3. All markdown documentation (except README.md, ARCHITECTURE.md, CLAUDE.md) goes in `change_logs/` directory
4. **Always use `.venv/bin/python` for Python commands** (see `.claude/rules/python-venv.md`)

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
Complete API wrapper in `genie/api/genie_space_client.py`:
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
1. Update Pydantic models in `genie/models.py`
2. Modify prompt templates in `genie/prompt/templates/`
3. Update `config_transformer.py` for serialized format
4. Add tests in `tests/test_generation.py`

### Adding New Validation Rules
1. Extend `table_validator.py` validation logic
2. Update validation report structure
3. Add tests in `tests/test_table_validator.py`

### Modifying Prompt Templates
Templates are markdown files in `genie/prompt/templates/`:
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
