"""FastAPI backend for Genie Lamp Agent Databricks App."""

import os
from datetime import datetime
from typing import List
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services.session_store import SQLiteSessionStore
from backend.services.job_manager import JobManager
from backend.services.file_storage import LocalFileStorageService
from backend.services.job_tasks import (
    run_parse_job,
    run_generate_job,
    run_validate_job,
    run_deploy_job,
    apply_validation_fixes
)
from backend.services.benchmark_validator import validate_benchmark_queries
from backend.middleware.auth import get_current_user


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

# Serve Next.js static export
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Look for static export in 'out' directory (Next.js static export)
frontend_export_dir = os.getenv("FRONTEND_EXPORT_DIR", "../frontend/out")
frontend_export_path = Path(frontend_export_dir)

# Debug: Log frontend path info
print(f"Frontend export dir: {frontend_export_dir}")
print(f"Frontend export path: {frontend_export_path}")
print(f"Frontend path exists: {frontend_export_path.exists()}")
print(f"Frontend path absolute: {frontend_export_path.absolute()}")
if frontend_export_path.exists():
    print(f"Frontend directory contents: {list(frontend_export_path.iterdir())[:10]}")

# Mount static assets early (before API routes)
if frontend_export_path.exists():
    print(f"Mounting frontend static assets from {frontend_export_path}")
    # Serve static assets from _next directory
    if (frontend_export_path / "_next").exists():
        app.mount("/_next", StaticFiles(directory=str(frontend_export_path / "_next")), name="next_static")
        print("Mounted /_next static files")
else:
    print(f"WARNING: Frontend export directory not found at {frontend_export_path.absolute()}")

# Initialize services
session_store = SQLiteSessionStore()
job_manager = JobManager(session_store)
file_storage = LocalFileStorageService()


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
    space_name: str = None  # Optional override for space name


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


# Debug endpoint
@app.get("/api/debug/auth")
async def debug_auth(current_user: dict = Depends(get_current_user)):
    """
    Debug endpoint to check authentication and permissions.

    Returns information about:
    - User identity
    - Token validity
    - SQL warehouse access
    - Genie space permissions
    """
    import jwt
    from genie.api.genie_space_client import GenieSpaceClient

    user_token = current_user["token"]
    databricks_host = os.getenv("DATABRICKS_HOST")

    # Decode token
    try:
        payload = jwt.decode(user_token, options={"verify_signature": False})
        token_info = {
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "scopes": payload.get("scope", "").split() if payload.get("scope") else [],
            "exp": payload.get("exp"),
            "iss": payload.get("iss"),
        }
    except Exception as e:
        token_info = {"error": str(e)}

    # Test Genie Space API access
    try:
        client = GenieSpaceClient(
            databricks_host=databricks_host,
            databricks_token=user_token
        )

        # Try to list spaces
        spaces_response = client.list_spaces(page_size=1)
        genie_access = {
            "can_list_spaces": True,
            "spaces_count": len(spaces_response.get("spaces", []))
        }

        # Try to get warehouse
        warehouse_id = client.get_available_warehouse()
        genie_access["warehouse_id"] = warehouse_id
        genie_access["has_warehouse_access"] = warehouse_id is not None

    except Exception as e:
        genie_access = {
            "error": str(e),
            "can_list_spaces": False
        }

    return {
        "user_id": current_user["user_id"],
        "token_info": token_info,
        "genie_access": genie_access,
        "databricks_host": databricks_host
    }


# Download config endpoint
@app.get("/api/download/config/{session_id}")
async def download_config(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download the generated Genie space configuration as JSON.

    Args:
        session_id: Session ID

    Returns:
        JSON file download response
    """
    from fastapi.responses import JSONResponse
    import json

    # Get config path
    session_dir = file_storage.get_session_dir(session_id)
    config_path = f"{session_dir}/genie_space_config.json"

    # Check if file exists
    if not os.path.exists(config_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Configuration file not found")

    # Read config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Return as downloadable JSON
    return JSONResponse(
        content=config,
        headers={
            "Content-Disposition": f"attachment; filename=genie_space_config_{session_id}.json"
        }
    )


@app.get("/api/config/metadata")
async def get_config_metadata(
    config_path: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get metadata from a configuration file (space_name, description, etc.)

    Args:
        config_path: Path to config file (relative to session storage)

    Returns:
        Dict with space_name, description, purpose
    """
    import json
    from fastapi import HTTPException

    # Security: Only allow reading from storage directory
    if not config_path.startswith("storage/"):
        raise HTTPException(status_code=400, detail="Invalid config path")

    # Check if file exists
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Configuration file not found")

    # Read config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Extract metadata
        if "genie_space_config" in config:
            cfg = config["genie_space_config"]
        else:
            cfg = config

        return {
            "space_name": cfg.get("space_name", ""),
            "description": cfg.get("description", ""),
            "purpose": cfg.get("purpose", ""),
            "table_count": len(cfg.get("tables", [])),
            "join_count": len(cfg.get("join_specifications", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read config: {str(e)}")


# Parse endpoint
@app.post("/api/parse")
async def parse_files(
    session_id: str = Form(...),
    use_llm: bool = Form(True),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user)
):
    """
    Parse uploaded requirement documents.

    Saves files to Unity Catalog Volume and starts async parsing job.
    Uses app OAuth token for LLM operations (vision models).
    """
    user_token = current_user["token"]

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
        output_path,
        user_token  # Pass user token (though parse uses app token for LLM)
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
    current_user: dict = Depends(get_current_user)
):
    """
    Generate Genie space configuration from requirements.

    Uses LLM to create configuration JSON from parsed requirements.
    Uses app OAuth token for LLM operations.
    """
    user_token = current_user["token"]

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
        request.model,
        user_token  # Pass user token (though generate uses app token for LLM)
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
    current_user: dict = Depends(get_current_user)
):
    """
    Validate configuration against Unity Catalog.

    Checks that all tables and columns exist in Unity Catalog.
    Uses user's OAuth token for SQL operations (on-behalf authentication).
    """
    user_token = current_user["token"]

    # Create job
    job = job_manager.create_job("validate", request.session_id, {
        "config_path": request.config_path
    })

    # Start background task
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_validate_job,
        request.config_path,
        user_token  # REQUIRED: User token for SQL validation
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
    current_user: dict = Depends(get_current_user)
):
    """
    Apply table/catalog/schema fixes and re-validate.

    Updates configuration with corrected table references and re-runs validation.
    Supports bulk catalog/schema updates and table exclusions.
    Uses user's OAuth token for SQL operations (on-behalf authentication).
    """
    user_token = current_user["token"]

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
        request.config_path,
        user_token  # REQUIRED: User token for SQL validation
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
    current_user: dict = Depends(get_current_user)
):
    """
    Deploy Genie space to Databricks.

    Creates a new Genie space with the validated configuration.
    Uses user's OAuth token for deployment (on-behalf authentication).
    The Genie space will be owned by the user.
    """
    user_token = current_user["token"]

    # Create job
    job = job_manager.create_job("deploy", request.session_id, {
        "config_path": request.config_path,
        "parent_path": request.parent_path,
        "space_name": request.space_name
    })

    # Start background task
    background_tasks.add_task(
        job_manager.run_job,
        job.job_id,
        run_deploy_job,
        request.config_path,
        request.parent_path,
        user_token,  # REQUIRED: User token for on-behalf deployment
        request.space_name  # Optional: Override space name
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
    current_user: dict = Depends(get_current_user)
):
    """
    Validate benchmark SQL queries against Unity Catalog.

    Executes each benchmark's expected_sql query to verify it runs successfully.
    Uses user's OAuth token for SQL operations (on-behalf authentication).
    """
    user_token = current_user["token"]

    # Create job
    job = job_manager.create_job("benchmark_validate", request.session_id, {
        "total_benchmarks": len(request.benchmarks)
    })

    # Get Databricks connection details from environment
    databricks_server_hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
    databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH")

    # Create wrapper function that returns result or raises exception
    # Note: run_job adds job_id to kwargs, so we need to accept **kwargs
    def run_benchmark_validation(**kwargs):
        return validate_benchmark_queries(
            benchmarks=request.benchmarks,
            databricks_server_hostname=databricks_server_hostname,
            databricks_http_path=databricks_http_path,
            databricks_token=user_token  # Use user token for SQL operations
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
):
    """
    List all sessions with pagination.

    Returns sessions ordered by updated_at DESC (most recent first).
    """
    sessions, total_count = session_store.list_sessions(user_id=user_id, limit=limit, offset=offset)

    # Calculate current step for each session
    sessions_with_step = []
    for session in sessions:
        jobs = session_store.get_jobs_for_session(session["session_id"])
        completed_types = {job.type for job in jobs if job.status == "completed"}
        current_step = len(completed_types) + 1

        sessions_with_step.append({
            "session_id": session["session_id"],
            "name": session["name"],
            "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
            "updated_at": session["updated_at"].isoformat() if isinstance(session["updated_at"], datetime) else session["updated_at"],
            "job_count": session["job_count"],
            "current_step": current_step
        })

    return {
        "sessions": sessions_with_step,
        "total_count": total_count
    }


# Create session endpoint
@app.post("/api/sessions")
async def create_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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
    current_user: dict = Depends(get_current_user)
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


# Serve frontend - MUST be after all API routes
if frontend_export_path.exists():
    # Serve index.html for root path
    @app.get("/")
    async def serve_frontend_root():
        return FileResponse(str(frontend_export_path / "index.html"))

    # Catch-all route to serve frontend files
    # This must be last to not interfere with API routes
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Try to serve the exact file if it exists
        file_path = frontend_export_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        # Try with .html extension for clean URLs
        html_path = frontend_export_path / f"{full_path}.html"
        if html_path.exists():
            return FileResponse(str(html_path))

        # Try with index.html in directory
        dir_index = frontend_export_path / full_path / "index.html"
        if dir_index.exists():
            return FileResponse(str(dir_index))

        # Default to root index.html for client-side routing
        return FileResponse(str(frontend_export_path / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
