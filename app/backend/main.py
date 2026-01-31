"""FastAPI backend for Genie Lamp Agent Databricks App."""

import os
from datetime import datetime
from typing import List
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.session_store import SessionStore
from services.job_manager import JobManager
from services.file_storage import FileStorageService
from services.job_tasks import (
    run_parse_job,
    run_generate_job,
    run_validate_job,
    run_deploy_job,
    apply_validation_fixes
)
from services.benchmark_validator import validate_benchmark_queries
from middleware.auth import get_current_user


# Initialize FastAPI app
app = FastAPI(
    title="Genie Lamp Agent API",
    description="Generate Databricks Genie Spaces from natural language requirements",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Next.js static build
from fastapi.staticfiles import StaticFiles
from pathlib import Path

frontend_build_dir = os.getenv("FRONTEND_BUILD_DIR", "../frontend/.next")
frontend_path = Path(frontend_build_dir)

if frontend_path.exists():
    # Serve Next.js static files
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

    # Serve Next.js pages (if using static export)
    if (frontend_path / "standalone").exists():
        app.mount("/", StaticFiles(directory=str(frontend_path / "standalone"), html=True), name="frontend")

# Initialize services
session_store = SessionStore()
job_manager = JobManager(session_store)
file_storage = FileStorageService()


# Request/Response models
class GenerateRequest(BaseModel):
    session_id: str
    requirements_path: str
    model: str = "databricks-gpt-5-2"


class ValidateRequest(BaseModel):
    session_id: str
    config_path: str


class ValidationFix(BaseModel):
    old_catalog: str
    old_schema: str
    old_table: str
    new_catalog: str
    new_schema: str
    new_table: str


class FixValidationRequest(BaseModel):
    session_id: str
    config_path: str
    replacements: List[ValidationFix] = []
    bulk_catalog: str = None
    bulk_schema: str = None
    exclude_tables: List[str] = []


class DeployRequest(BaseModel):
    session_id: str
    config_path: str
    parent_path: str = None


class CreateSessionRequest(BaseModel):
    user_id: str = "default"
    name: str = None


class UpdateSessionNameRequest(BaseModel):
    name: str


class ValidateBenchmarkRequest(BaseModel):
    session_id: str
    benchmarks: List[dict]  # List of {question, expected_sql, ...}


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Parse endpoint
@app.post("/api/parse")
async def parse_files(
    session_id: str = Form(...),
    use_llm: bool = Form(True),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Parse uploaded requirement documents.

    Saves files to Unity Catalog Volume and starts async parsing job.
    """
    # Save uploaded files
    file_paths = await file_storage.save_uploads(files, session_id)

    # Create output path
    session_dir = file_storage.get_session_dir(session_id)
    output_path = f"{session_dir}/parsed_requirements.md"

    # Create job
    job = job_manager.create_job("parse", session_id, {
        "file_paths": file_paths,
        "use_llm": use_llm,
        "output_path": output_path
    })

    # Start background task (job_id will be passed automatically for progress tracking)
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_parse_job,
        file_paths,
        use_llm,
        output_path
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": f"Parsing {len(files)} files"
    }


# Generate endpoint
@app.post("/api/generate")
async def generate_config(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Generate Genie space configuration from requirements.

    Uses LLM to create configuration JSON from parsed requirements.
    """
    # Create output path
    session_dir = file_storage.get_session_dir(request.session_id)
    output_path = f"{session_dir}/genie_space_config.json"

    # Create job
    job = job_manager.create_job("generate", request.session_id, {
        "requirements_path": request.requirements_path,
        "output_path": output_path,
        "model": request.model
    })

    # Start background task
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_generate_job,
        request.requirements_path,
        output_path,
        request.model
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": f"Generating config with {request.model}"
    }


# Validate endpoint
@app.post("/api/validate")
async def validate_config_endpoint(
    request: ValidateRequest,
    background_tasks: BackgroundTasks,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Validate configuration against Unity Catalog.

    Checks that all tables and columns exist in Unity Catalog.
    """
    # Create job
    job = job_manager.create_job("validate", request.session_id, {
        "config_path": request.config_path
    })

    # Start background task
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_validate_job,
        request.config_path
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": "Validating configuration"
    }


# Fix validation endpoint
@app.post("/api/validate/fix")
async def fix_validation(
    request: FixValidationRequest,
    background_tasks: BackgroundTasks,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Apply table/catalog/schema fixes and re-validate.

    Updates configuration with corrected table references and re-runs validation.
    Supports bulk catalog/schema updates and table exclusions.
    """
    # Apply fixes synchronously (fast operation)
    replacements_dict = [rep.dict() for rep in request.replacements] if request.replacements else []
    apply_validation_fixes(
        config_path=request.config_path,
        replacements=replacements_dict,
        bulk_catalog=request.bulk_catalog,
        bulk_schema=request.bulk_schema,
        exclude_tables=request.exclude_tables
    )

    # Re-validate
    job = job_manager.create_job("validate", request.session_id, {
        "config_path": request.config_path
    })

    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_validate_job,
        request.config_path
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": "Applied fixes and re-validating"
    }


# Deploy endpoint
@app.post("/api/deploy")
async def deploy_space_endpoint(
    request: DeployRequest,
    background_tasks: BackgroundTasks,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Deploy Genie space to Databricks.

    Creates a new Genie space with the validated configuration.
    """
    # Create job
    job = job_manager.create_job("deploy", request.session_id, {
        "config_path": request.config_path,
        "parent_path": request.parent_path
    })

    # Start background task
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_deploy_job,
        request.config_path,
        request.parent_path
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": "Deploying Genie space"
    }


# Benchmark validation endpoint
@app.post("/api/benchmark/validate")
async def validate_benchmarks_endpoint(
    request: ValidateBenchmarkRequest,
    background_tasks: BackgroundTasks,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Validate benchmark SQL queries against Unity Catalog.

    Executes each benchmark's expected_sql query to verify it runs successfully.
    """
    # Create job
    job = job_manager.create_job("benchmark_validate", request.session_id, {
        "total_benchmarks": len(request.benchmarks)
    })

    # Get Databricks connection details from environment
    databricks_server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH")
    databricks_token = os.getenv("DATABRICKS_TOKEN")

    # Create wrapper function that returns result or raises exception
    # Note: run_job adds job_id to kwargs, so we need to accept **kwargs
    def run_benchmark_validation(**kwargs):
        return validate_benchmark_queries(
            benchmarks=request.benchmarks,
            databricks_server_hostname=databricks_server_hostname,
            databricks_http_path=databricks_http_path,
            databricks_token=databricks_token
        )

    # Start background task (run_job automatically handles completion/failure)
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_benchmark_validation
    )

    return {
        "job_id": job.job_id,
        "status": "running",
        "message": f"Validating {len(request.benchmarks)} benchmark queries"
    }


# Job status endpoint
@app.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Get job status and results.

    Polls this endpoint to track job progress.
    """
    job = job_manager.get_job(job_id)

    if not job:
        return {"error": "Job not found"}, 404

    return {
        "job_id": job.job_id,
        "status": job.status,
        "type": job.type,
        "result": job.result,
        "error": job.error,
        "progress": job.progress,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


# List sessions endpoint
@app.get("/api/sessions")
async def list_sessions(
    user_id: str = None,
    limit: int = 50,
    offset: int = 0,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    List all sessions with pagination.

    Returns sessions ordered by updated_at DESC (most recent first).
    """
    sessions, total_count = session_store.list_sessions(user_id=user_id, limit=limit, offset=offset)

    return {
        "sessions": [
            {
                "session_id": session["session_id"],
                "name": session["name"],
                "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
                "updated_at": session["updated_at"].isoformat() if isinstance(session["updated_at"], datetime) else session["updated_at"],
                "job_count": session["job_count"]
            }
            for session in sessions
        ],
        "total_count": total_count
    }


# Create session endpoint
@app.post("/api/sessions")
async def create_session(
    request: CreateSessionRequest,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Create a new session.

    Optionally provide a custom name, otherwise defaults to timestamp.
    """
    session_id = session_store.create_session(user_id=request.user_id, name=request.name)
    session = session_store.get_session_with_stats(session_id)

    return {
        "session_id": session_id,
        "name": session["name"],
        "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
        "updated_at": session["updated_at"].isoformat() if isinstance(session["updated_at"], datetime) else session["updated_at"],
        "job_count": 0
    }


# Update session name endpoint
@app.put("/api/sessions/{session_id}")
async def update_session_name(
    session_id: str,
    request: UpdateSessionNameRequest,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Update session name.

    Also updates the updated_at timestamp.
    """
    session_store.update_session_name(session_id, request.name)
    session = session_store.get_session_with_stats(session_id)

    if not session:
        return {"error": "Session not found"}, 404

    return {
        "session_id": session_id,
        "name": session["name"],
        "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
        "updated_at": session["updated_at"].isoformat() if isinstance(session["updated_at"], datetime) else session["updated_at"],
        "job_count": session["job_count"]
    }


# Delete session endpoint
@app.delete("/api/sessions/{session_id}")
async def delete_session(
    session_id: str,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Delete session and all associated jobs.

    This is a hard delete with cascade to jobs (cannot be undone).
    """
    session_store.delete_session(session_id)

    return {"success": True}


# Get session details endpoint
@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Get all jobs for a session with full results.

    Shows workflow progress across all steps with job results for state restoration.
    """
    jobs = session_store.get_jobs_for_session(session_id)

    # Calculate current step based on completed jobs
    completed_types = {job.type for job in jobs if job.status == "completed"}
    current_step = len(completed_types) + 1

    return {
        "session_id": session_id,
        "current_step": current_step,
        "jobs": [
            {
                "job_id": job.job_id,
                "type": job.type,
                "status": job.status,
                "result": job.result,  # Include full result for state restoration
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
    }


# File content endpoint
@app.get("/api/files/{session_id}/{filename}")
async def get_file_content(
    session_id: str,
    filename: str,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Get file content from session directory.

    Security: Only allows whitelisted files to prevent path traversal attacks.
    """
    # Security: Validate filename (prevent path traversal)
    allowed_files = [
        'parsed_requirements.md',
        'genie_space_config.json',
        'validation_report.json'
    ]

    if filename not in allowed_files:
        return {"error": "File not allowed"}, 403

    # Get file path
    session_dir = file_storage.get_session_dir(session_id)
    file_path = f"{session_dir}/{filename}"

    # Check existence
    if not os.path.exists(file_path):
        return {"error": "File not found"}, 404

    # Read with stats
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        stats = os.stat(file_path)

        return {
            "content": content,
            "filename": filename,
            "size_bytes": stats.st_size,
            "line_count": len(content.splitlines()),
            "char_count": len(content)
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}, 500


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
