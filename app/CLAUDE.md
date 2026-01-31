# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-user web application for generating Databricks Genie Spaces from natural language requirements. This is the web frontend to the parent Genie Lamp Agent project, wrapping the existing CLI pipeline (`../genie.py`, `../src/`) with a FastAPI backend and Next.js frontend.

**Key Architecture**: This app reuses all existing pipeline code from the parent directory via wrapper functions in `backend/services/job_tasks.py`.

## Local Development Commands

### Starting the Application

```bash
# Quick start - automatically sets up and starts both services
./start-local.sh
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Manual backend startup
cd backend
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your DATABRICKS_* credentials
uvicorn main:app --reload --port 8000

# Manual frontend startup
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

**Important**: The `start-local.sh` script handles virtual environment creation, dependency installation, and health checks. Always use it for first-time setup.

### Viewing Logs

```bash
# View backend logs
tail -f backend.log

# View frontend logs
tail -f frontend.log

# View live updates from both
tail -f backend.log frontend.log
```

### Stopping the Application

```bash
./stop-local.sh
# Or Ctrl+C if using start-local.sh
```

### Building for Production

```bash
# Build frontend static export
./build-frontend.sh

# Deploy to Databricks via Asset Bundle
databricks bundle deploy -t dev

# Access deployed app
# https://<your-workspace>.databricks.com/apps/genie-lamp-agent
```

### Verifying Configuration

```bash
# Check migration to app.yaml + Asset Bundle
./verify-migration.sh

# Test backend health
curl http://localhost:8000/health

# Test API documentation
open http://localhost:8000/docs
```

## Environment Configuration

### Backend (.env)
Copy from `.env.example` and configure:
- `DATABRICKS_HOST`: Workspace URL
- `DATABRICKS_TOKEN`: Personal access token
- `DATABRICKS_SERVER_HOSTNAME`: Server hostname for SQL
- `DATABRICKS_HTTP_PATH`: SQL warehouse HTTP path (e.g., `/sql/1.0/warehouses/<id>`)

**Note**: If `DATABRICKS_HTTP_PATH` contains placeholder text or is invalid, backend will use in-memory session store instead of Databricks SQL.

### Frontend (.env.local)
Copy from `.env.example` and configure:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## Architecture Overview

### High-Level Flow
```
User Upload → FastAPI Backend → Background Jobs → Pipeline Functions → Unity Catalog
                      ↓                                    ↓
                Frontend Polling ← Session Store → Job Results
```

### Backend Architecture

**Core Structure** (`backend/`):
- **main.py**: FastAPI application with 8 REST endpoints
  - `/api/parse`, `/api/generate`, `/api/validate`, `/api/validate/fix`, `/api/deploy`
  - `/api/jobs/{job_id}`, `/api/sessions/{session_id}`, `/health`
- **services/job_tasks.py**: Wrapper functions that call parent project pipeline code
  - `run_parse_job()`, `run_generate_job()`, `run_validate_job()`, `run_deploy_job()`
  - All functions change directory to project root before calling pipeline
  - Progress tracking via callbacks for parsing jobs
- **services/session_store.py**: Job persistence using Databricks SQL or in-memory store
- **services/job_manager.py**: Background job execution and lifecycle management
- **services/file_storage.py**: Unity Catalog Volume storage for uploads and outputs
- **middleware/auth.py**: OAuth2 authentication (disabled for local dev)

**Critical Pattern**: All pipeline functions are imported from parent directory:
```python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)
from src.pipeline.parser import parse_documents_async_with_progress
from src.pipeline.generator import generate_config
```

### Frontend Architecture

**Core Structure** (`frontend/`):
- **app/page.tsx**: Main workflow UI with 5-step wizard (Upload & Extract → Generate → Validate → Deploy → Complete)
- **app/layout.tsx**: App layout and global styles
- **components/**: Step-specific components
  - `ParseStep.tsx`: File upload and requirement extraction with real-time progress
  - `GenerateStep.tsx`: LLM config generation
  - `ValidateStep.tsx`: Unity Catalog validation
  - `ValidationFixer.tsx`: Interactive table reference fixing
  - `DeployStep.tsx`: Genie space deployment
  - `FileProgressList.tsx`: Real-time extraction progress display
  - `ReasoningDisplay.tsx`: LLM reasoning visualization
  - `Stepper.tsx`: Progress indicator
- **lib/api-client.ts**: Type-safe API client for backend
- **lib/hooks/useJobPolling.ts**: Job status polling hook (2-second interval)

**State Management**: React hooks + job polling. No global state library needed.

### Job Lifecycle

1. User triggers action (upload, generate, etc.)
2. Backend creates job with `pending` status
3. Background task starts, job status → `running`
4. Frontend polls `/api/jobs/{job_id}` every 2 seconds
5. Job completes with `completed` or `failed` status
6. Frontend displays results or errors

**Progress Tracking**: Parsing jobs track per-file, per-page progress with cache hit status and LLM enrichment stages.

## Databricks App Deployment

### Prerequisites

1. **Unity Catalog Volumes**:
   ```bash
   databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/uploads
   databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/sessions
   ```

2. **Secrets Scope**:
   ```bash
   databricks secrets create-scope genie-lamp
   databricks secrets put-secret genie-lamp service-token --string-value "YOUR_TOKEN"
   databricks secrets put-secret genie-lamp sql-warehouse-http-path --string-value "/sql/1.0/warehouses/<id>"
   ```

### Deployment Workflow

1. Build frontend: `./build-frontend.sh`
2. Deploy: `databricks bundle deploy -t dev`
3. Access: `https://<workspace>/apps/genie-lamp-agent`

**Configuration Files**:
- `databricks.yml`: Asset Bundle configuration
- `app.yaml`: Runtime configuration (command, environment, secrets)

## Key Integration Points

### Parent Project Dependencies

This app wraps existing pipeline code from parent directory:
- `../src/pipeline/parser.py`: Document extraction with LLM enrichment
- `../src/pipeline/generator.py`: Config generation
- `../src/pipeline/validator.py`: Unity Catalog validation
- `../src/pipeline/deployer.py`: Genie space deployment
- `../genie.py`: CLI utility functions (table replacement, removal)

**Important**: Any changes to parent pipeline code automatically affect this app.

### Working Directory Management

All wrapper functions in `job_tasks.py` temporarily change to project root:
```python
original_cwd = os.getcwd()
try:
    os.chdir(project_root)  # Required for template paths and imports
    result = generate_config(...)
finally:
    os.chdir(original_cwd)
```

This ensures prompt templates and relative paths resolve correctly.

### Progress Tracking System

Extraction jobs support real-time progress updates:
- Per-file status tracking (queued → processing → completed)
- Per-page progress for PDFs
- Cache hit indicators
- LLM enrichment stage tracking
- Progress stored in job's `progress` field in session store

Frontend polls and displays progress via `FileProgressList.tsx`.

## API Endpoint Details

### POST /api/parse
- **Input**: Files (multipart), session_id, use_llm flag
- **Output**: job_id
- **Background Task**: Extracts requirements from documents, identifies tables, optionally enriches with LLM
- **Result**: `{ output_path, tables_found, files_parsed, cache_stats, enrichment_reasoning }`

### POST /api/generate
- **Input**: `{ session_id, requirements_path, model }`
- **Output**: job_id
- **Background Task**: Generates Genie space configuration
- **Result**: `{ output_path, reasoning, tables_count, instructions_count }`

### POST /api/validate
- **Input**: `{ session_id, config_path }`
- **Output**: job_id
- **Background Task**: Validates tables/columns against Unity Catalog
- **Result**: `{ has_errors, tables_valid, tables_invalid, issues[] }`

### POST /api/validate/fix
- **Input**: `{ session_id, config_path, replacements[], bulk_catalog, bulk_schema, exclude_tables[] }`
- **Output**: job_id
- **Synchronous**: Applies fixes immediately
- **Background Task**: Re-validates after fixes
- **Supports**: Individual table replacements, bulk catalog/schema updates, table exclusions

### POST /api/deploy
- **Input**: `{ session_id, config_path, parent_path }`
- **Output**: job_id
- **Background Task**: Deploys to Databricks Genie
- **Result**: `{ space_id, space_url }`

### GET /api/jobs/{job_id}
- **Output**: `{ job_id, status, type, result, error, progress, created_at, completed_at }`
- **Used for**: Polling job status

### GET /api/sessions/{session_id}
- **Output**: `{ session_id, current_step, jobs[] }`
- **Used for**: Session overview and workflow progress

## Development Notes

### TypeScript Configuration
- Frontend uses TypeScript with strict mode
- All API responses typed via Pydantic models in backend
- Type-safe client in `lib/api-client.ts`

### CORS Configuration
Backend allows all origins in development:
```python
allow_origins=["*"]  # Restrict in production
```

### Session Isolation
- Each user session has UUID-based directory in Unity Catalog Volume
- Format: `/Volumes/main/genie_lamp/uploads/{session_id}/`
- All outputs stored in session directory

### In-Memory Mode
If `DATABRICKS_HTTP_PATH` is invalid or contains placeholder:
- Backend uses in-memory dictionaries for session/job storage
- Data lost on restart (acceptable for local dev)
- Warning logged: "Using in-memory session store"

### Frontend Static Build
Backend serves Next.js static files if available:
- Static assets: `/.next/static`
- Standalone mode: `/.next/standalone`
- Configured via `FRONTEND_BUILD_DIR` environment variable

## Common Workflows

### Adding New Pipeline Step

1. Add wrapper function to `backend/services/job_tasks.py`
   - Import pipeline function from parent `../src/`
   - Use working directory pattern (save, chdir, restore)
   - Return job-friendly dict format
2. Add endpoint to `backend/main.py`
   - Define Pydantic request/response models
   - Create job with `job_manager.create_job()`
   - Add background task with `job_manager.run_job()`
3. Create frontend component in `frontend/components/`
   - Use `useJobPolling` hook for status updates
   - Handle `onComplete` callback to advance workflow
4. Update workflow in `frontend/app/page.tsx`
   - Add step to `steps` array
   - Add conditional rendering: `{currentStep === N && <YourStep />}`
5. Add TypeScript types to `frontend/lib/api-client.ts`
   - Define interfaces for request/response
   - Add API call function to `apiClient` object

### Modifying Job Progress Tracking

1. Update progress callback in `job_tasks.py`
   - Modify `progress_data` structure
   - Call `_update_job_progress(job_id, progress_data)`
2. Update TypeScript types in `frontend/lib/api-client.ts`
   - Add new fields to `JobProgress` interface
3. Update display component (`FileProgressList.tsx` or create new)
   - Render new progress fields
   - Add appropriate UI (progress bars, status badges)
4. Test with real job:
   - Upload files → verify progress updates every ~2s
   - Check browser console for type errors

### Testing the Full Workflow Locally

1. Start services: `./start-local.sh`
2. Open http://localhost:3000
3. **Step 1 - Upload & Extract**: Upload PDF or markdown files and extract requirements
   - Watch real-time progress (file-by-file, page-by-page)
   - Verify enrichment stages if LLM enabled
4. **Step 2 - Generate**: Review generated config reasoning
5. **Step 3 - Validate**: Check Unity Catalog validation results
   - If errors: use ValidationFixer to bulk-update catalog/schema
   - Re-validate until clean
6. **Step 4 - Deploy**: Deploy to Databricks Genie
7. **Step 5 - Complete**: Click link to open Genie space
8. Stop services: `./stop-local.sh` or Ctrl+C

### Debugging Backend Issues

```bash
# View backend logs
tail -f backend.log

# Check health endpoint
curl http://localhost:8000/health

# Check job status
curl http://localhost:8000/api/jobs/{job_id}

# Test API directly (generate example)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "requirements_path": "/path/to/requirements.md", "model": "databricks-gpt-5-2"}'

# Common backend errors:
# - "Using in-memory session store" → Fix DATABRICKS_HTTP_PATH in .env
# - "Template not found" → Check working directory (should be project root)
# - "ModuleNotFoundError: src" → Check sys.path.insert in job_tasks.py
```

### Debugging Frontend Issues

```bash
# View frontend logs
tail -f frontend.log

# Check Next.js compilation errors
cd frontend && npm run dev

# Verify API URL
cat frontend/.env.local | grep NEXT_PUBLIC_API_URL

# Common frontend errors:
# - CORS errors → Backend must be running on port 8000
# - "Network error" → Check NEXT_PUBLIC_API_URL in .env.local
# - Job polling timeout → Check backend logs for job execution errors
# - TypeScript errors → Update types in lib/api-client.ts
```

### Testing Backend Without Frontend

```bash
# Using curl (parse endpoint example)
curl -X POST http://localhost:8000/api/parse \
  -F "session_id=test-123" \
  -F "use_llm=true" \
  -F "files=@/path/to/document.pdf"

# Poll job status
curl http://localhost:8000/api/jobs/{returned-job-id}

# Using FastAPI docs (interactive)
open http://localhost:8000/docs
# Use "Try it out" buttons to test endpoints
```

## Troubleshooting Common Issues

### Backend Won't Start

**Symptom**: `./start-local.sh` fails or backend.log shows errors

**Solutions**:
1. Check Python version: `python --version` (requires 3.11+)
2. Verify virtual environment: `cd backend && source .venv/bin/activate`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check `.env` configuration:
   - `DATABRICKS_HOST` should be full URL with https://
   - `DATABRICKS_TOKEN` should start with `dapi`
   - `DATABRICKS_HTTP_PATH` format: `/sql/1.0/warehouses/<warehouse-id>`
5. Test imports: `python -c "from services.job_tasks import run_parse_job"`

### Frontend Won't Build

**Symptom**: `npm run dev` or `./build-frontend.sh` fails

**Solutions**:
1. Check Node.js version: `node --version` (requires 18+)
2. Clear build artifacts: `rm -rf .next node_modules`
3. Reinstall: `npm install`
4. Check TypeScript errors: `npm run build` (shows all type errors)
5. Verify `.env.local` exists with `NEXT_PUBLIC_API_URL`

### Job Stays "Running" Forever

**Symptom**: Frontend polls but job never completes

**Solutions**:
1. Check backend logs: `tail -f backend.log` for exceptions
2. Verify job in session store: `curl http://localhost:8000/api/jobs/{job_id}`
3. Check working directory: Jobs must chdir to project root for imports
4. Verify parent pipeline code: Test CLI directly with `../genie.py`
5. Check Databricks credentials: Token must have SQL execution permissions

### Validation Always Fails

**Symptom**: Tables not found in Unity Catalog

**Solutions**:
1. Verify SQL warehouse is running (check `DATABRICKS_HTTP_PATH`)
2. Test Unity Catalog access: Run SQL query `SHOW TABLES IN catalog.schema`
3. Use ValidationFixer UI to bulk-update catalog/schema names
4. Check token permissions: Must have `USE CATALOG` and `USE SCHEMA` grants
5. Exclude problematic tables using "exclude tables" feature

### File Uploads Fail

**Symptom**: Upload errors or files not found during parsing

**Solutions**:
1. Local dev: Check `backend/storage/` directory exists
2. Production: Verify Unity Catalog Volume: `/Volumes/main/genie_lamp/uploads`
3. Check file size limits (default: 50MB in FastAPI)
4. Verify multipart form data: `Content-Type: multipart/form-data`
5. Check session directory permissions

### CORS Errors in Browser

**Symptom**: "CORS policy" errors in browser console

**Solutions**:
1. Verify backend is running on port 8000
2. Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
3. Ensure frontend is on port 3000 (or update CORS config)
4. For production: Update `allow_origins` in `main.py` to specific domain

### Page Cache Issues

**Symptom**: Parsing shows incorrect cached results

**Solutions**:
1. Clear page cache: `rm backend/.parse_cache.json`
2. Clear parent cache: `rm ../.parse_cache.json`
3. Disable caching temporarily for debugging
4. Cache keyed by file hash, so identical files reuse cache

## Permissions

The `.claude/settings.local.json` file defines allowed commands:
- Python execution: `.venv/bin/python`, `backend/.venv/bin/python`
- Git operations: `add`, `commit`, `checkout`, `reset`, `pull`, `merge`
- Process management: `kill`, `pkill`, `lsof`
- Scripts: `./start-local.sh`, `./verify-migration.sh`, `npm run build`
- External resources: `WebSearch`, `WebFetch(docs.databricks.com)`

## Relationship to Parent Project

This directory (`app/`) is a subdirectory of the larger Genie Lamp Agent project:
- **Parent CLI**: `../genie.py` - Command-line interface
- **Core Pipeline**: `../src/pipeline/` - Parser, generator, validator, deployer
- **This App**: Web UI wrapper around parent pipeline

**Do not duplicate logic** - always call parent functions via wrappers in `job_tasks.py`.

### Key Differences from Parent CLI

| Feature | Parent CLI (`../`) | Web App (`app/`) |
|---------|-------------------|------------------|
| **Interface** | Command-line (`genie.py`) | Web UI (Next.js) |
| **Execution** | Synchronous (blocking) | Async background jobs |
| **State** | File-based (output dir) | Database (Lakebase) + files |
| **Progress** | CLI progress bars | Real-time polling |
| **Multi-user** | No (single session) | Yes (UUID-based isolation) |
| **Auth** | Token in .env | OAuth2 (Databricks gateway) |
| **Deployment** | Local/VM | Databricks Apps platform |
| **Storage** | Local filesystem | Unity Catalog Volumes |
| **Testing** | `../genie.py create --requirements ...` | Web UI workflow |

### When to Use Which

**Use Parent CLI** (`../genie.py`) when:
- Batch processing multiple requirement documents
- Scripting/automation workflows
- Debugging pipeline components
- Running tests (`../tests/`)
- No web UI needed

**Use Web App** (`app/`) when:
- Interactive user experience required
- Multiple users need concurrent access
- Real-time progress visualization needed
- Deploying to Databricks as hosted app
- OAuth2 authentication required

Both share the same core pipeline code, so improvements to `../src/` benefit both interfaces.
