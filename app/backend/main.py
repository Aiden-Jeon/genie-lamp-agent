"""FastAPI backend for Genie Lamp Agent Databricks App."""

import os
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


# Session endpoint
@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    # current_user: dict = Depends(get_current_user)  # Disabled for local dev
):
    """
    Get all jobs for a session.

    Shows workflow progress across all steps.
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
                "error": job.error,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
