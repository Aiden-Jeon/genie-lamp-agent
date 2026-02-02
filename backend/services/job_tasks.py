"""Background job task wrappers for existing pipeline functions."""

import asyncio
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)



# Project root is parent of backend directory (../.. from services/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

from genie.pipeline.parser import parse_documents_async, parse_documents_async_with_progress
from genie.pipeline.generator import generate_config
from genie.pipeline.validator import validate_config
from genie.pipeline.deployer import deploy_space
from genie.utils.page_cache import PageCacheManager
from genie import update_config_catalog_schema_table, update_config_catalog_schema, remove_table_from_config

# Global reference to session store (set by job manager)
_global_session_store = None

def set_session_store(store):
    """Set global session store reference for job tasks."""
    global _global_session_store
    _global_session_store = store


def run_parse_job(
    file_paths: List[str],
    use_llm: bool,
    output_path: str,
    user_token: Optional[str] = None,
    job_id: str = None
) -> Dict:
    """
    Run parsing job on uploaded files with progress tracking.

    Uses app OAuth token for LLM operations (vision models for PDF parsing).

    Args:
        file_paths: List of file paths to parse
        use_llm: Whether to use LLM enrichment
        output_path: Where to save parsed output
        user_token: User's OAuth token (not used in parsing, LLM uses app token)
        job_id: Optional job ID for progress updates (uses global session store)

    Returns:
        Dict with output_path and parsing stats
    """

    # Get input directory from first file
    input_dir = os.path.dirname(file_paths[0])

    # Get Databricks credentials from environment for LLM clients
    databricks_host = os.getenv("DATABRICKS_HOST")

    # Use app OAuth token for LLM operations (parsing PDFs with vision models)
    from genie.auth.oauth_helper import get_app_oauth_token
    databricks_token = get_app_oauth_token()
    logger.info("Using app OAuth token for parsing (LLM operations)")
    logger.debug(f"App token prefix: {databricks_token[:10]}...")

    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Change to project root
        os.chdir(project_root)

        # Use progress tracking if job_id provided and global session store available
        if job_id is not None and _global_session_store is not None:
            # Initialize progress tracking
            from datetime import datetime
            progress_data = {
                "total_files": len(file_paths),
                "completed_files": 0,
                "files": [],
                "last_update": datetime.now().isoformat()
            }

            # Get file names from paths
            file_names = [os.path.basename(fp) for fp in file_paths]

            # Initialize file progress entries for all files (PDFs and markdown)
            for file_name in file_names:
                # Determine if file is PDF or markdown
                is_pdf = file_name.lower().endswith('.pdf')
                progress_data["files"].append({
                    "name": file_name,
                    "status": "queued",
                    "pages_total": 1 if not is_pdf else None,  # Markdown files have 1 "page"
                    "pages_completed": 0
                })

            # Update initial progress
            _update_job_progress(job_id, progress_data)

            # Initialize page cache manager
            page_cache_manager = PageCacheManager()

            # Progress callback function
            def progress_callback(file_name: str, page_num: int, total_pages: int, is_cache_hit: bool, status: str, extracted_summary: dict = None):
                """Update progress for a file/page."""
                from datetime import datetime

                # Find file in progress data
                for file_entry in progress_data["files"]:
                    if file_entry["name"] == file_name:
                        file_entry["status"] = status
                        file_entry["pages_total"] = total_pages
                        file_entry["pages_completed"] = page_num
                        file_entry["cache_hit"] = is_cache_hit

                        # Add extracted summary if provided
                        if extracted_summary:
                            file_entry["extracted"] = extracted_summary

                        if status == "completed":
                            progress_data["completed_files"] += 1
                            progress_data["current_file"] = None
                        elif status == "processing":
                            progress_data["current_file"] = file_name
                            file_entry["current_page"] = page_num

                        break

                progress_data["last_update"] = datetime.now().isoformat()
                _update_job_progress(job_id, progress_data)

            # Enrichment progress callback
            def enrichment_progress_callback(stage: str, details: str):
                """Update progress for enrichment stages."""
                from datetime import datetime

                if "enrichment_progress" not in progress_data:
                    progress_data["enrichment_progress"] = []

                progress_data["enrichment_progress"].append({
                    "stage": stage,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                })
                progress_data["last_update"] = datetime.now().isoformat()
                _update_job_progress(job_id, progress_data)

            # Run parser with progress tracking
            result = asyncio.run(parse_documents_async_with_progress(
                input_dir=input_dir,
                output_path=output_path,
                use_llm=use_llm,
                databricks_host=databricks_host,
                databricks_token=databricks_token,
                verbose=False,
                progress_callback=progress_callback,
                enrichment_progress_callback=enrichment_progress_callback,
                page_cache_manager=page_cache_manager
            ))
        else:
            # Fall back to standard parsing without progress
            result = asyncio.run(parse_documents_async(
                input_dir=input_dir,
                output_path=output_path,
                use_llm=use_llm,
                databricks_host=databricks_host,
                databricks_token=databricks_token,
                verbose=False
            ))

        # Calculate file stats for frontend
        file_stats = {}
        if os.path.exists(output_path):
            stats = os.stat(output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_stats = {
                "size_bytes": stats.st_size,
                "line_count": len(content.splitlines()),
                "char_count": len(content)
            }

        return {
            "output_path": output_path,
            "tables_found": result.get("tables_count", 0),
            "files_parsed": len(file_paths),
            "cache_stats": result.get("cache_stats", {}),
            "enrichment_reasoning": result.get("enrichment_reasoning"),
            "parsed_file_stats": file_stats
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def _update_job_progress(job_id: str, progress_data: dict):
    """Update job progress in global session store."""
    if _global_session_store is None:
        return  # No session store available, skip progress update

    job = _global_session_store.get_job(job_id)
    if job:
        job.progress = progress_data
        _global_session_store.update_job(job)


def run_generate_job(
    requirements_path: str,
    output_path: str,
    model: str,
    user_token: Optional[str] = None,
    job_id: str = None
) -> Dict:  # noqa: ARG001
    """
    Generate Genie space configuration from requirements.

    Uses app OAuth token for LLM operations (config generation).

    Args:
        requirements_path: Path to requirements markdown
        output_path: Where to save generated config
        model: LLM model to use
        user_token: User's OAuth token (not used in generation, LLM uses app token)
        job_id: Optional job ID for progress updates

    Returns:
        Dict with output_path, config metadata, and reasoning
    """
    # Save current directory
    original_cwd = os.getcwd()

    # Get Databricks credentials from environment for LLM clients
    databricks_host = os.getenv("DATABRICKS_HOST")

    # Use app OAuth token for LLM operations (generating config)
    from genie.auth.oauth_helper import get_app_oauth_token
    databricks_token = get_app_oauth_token()
    logger.info("Using app OAuth token for generation (LLM operations)")
    logger.debug(f"App token prefix: {databricks_token[:10]}...")

    try:
        # Change to project root so template paths resolve correctly
        os.chdir(project_root)

        result = generate_config(
            requirements_path=requirements_path,
            output_path=output_path,
            model=model,
            databricks_host=databricks_host,
            databricks_token=databricks_token,
            validate_sql=True,
            verbose=False
        )

        # Extract reasoning from result
        reasoning = result.get("reasoning", {})

        # Extract config metadata
        config = result.get("genie_space_config", {})
        tables_count = len(config.get("tables", []))
        instructions_count = len(config.get("instructions", []))

        return {
            "output_path": output_path,
            "reasoning": reasoning,
            "tables_count": tables_count,
            "instructions_count": instructions_count
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def run_validate_job(config_path: str, user_token: str, job_id: str = None) -> Dict:  # noqa: ARG001
    """
    Validate Genie space configuration against Unity Catalog.

    Uses user's OAuth token for SQL operations (on-behalf authentication).
    This ensures validation respects user's table/catalog permissions.

    Args:
        config_path: Path to config JSON
        user_token: User's OAuth token (REQUIRED for SQL validation)
        job_id: Optional job ID for progress updates

    Returns:
        Dict with validation results
    """
    if not user_token:
        raise ValueError("user_token is required for validation (SQL operations)")

    # Save current directory
    original_cwd = os.getcwd()

    # Get Databricks credentials from environment for validator
    databricks_host = os.getenv("DATABRICKS_HOST")

    logger.info("Using user token for validation (SQL operations with user permissions)")
    logger.debug(f"User token prefix: {user_token[:10]}...")

    try:
        # Change to project root
        os.chdir(project_root)

        report = validate_config(
            config_path=config_path,
            databricks_host=databricks_host,
            databricks_token=user_token,  # Use user token for SQL validation
            verbose=False
        )

        return {
            "has_errors": report.has_errors(),
            "tables_valid": report.tables_valid,
            "tables_invalid": report.tables_invalid,
            "issues": [
                {
                    "type": issue.type,
                    "severity": issue.severity,
                    "table": issue.table,
                    "column": issue.column,
                    "location": issue.location,
                    "message": issue.message
                }
                for issue in report.issues
            ]
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def run_deploy_job(
    config_path: str,
    parent_path: str = None,
    user_token: Optional[str] = None,
    job_id: str = None
) -> Dict:  # noqa: ARG001
    """
    Deploy Genie space to Databricks.

    Uses user's OAuth token for deployment (on-behalf authentication).
    The Genie space will be owned by the user, not the app service principal.

    Args:
        config_path: Path to config JSON
        parent_path: Optional parent folder path
        user_token: User's OAuth token (REQUIRED for on-behalf deployment)
        job_id: Optional job ID for progress updates

    Returns:
        Dict with space_id and space_url
    """
    if not user_token:
        raise ValueError("user_token is required for deployment (on-behalf operation)")

    # Save current directory
    original_cwd = os.getcwd()

    # Get Databricks credentials from environment for deployment
    databricks_host = os.getenv("DATABRICKS_HOST")

    logger.info("Using user token for deployment (Genie space created on user's behalf)")
    logger.debug(f"User token prefix: {user_token[:10]}...")

    try:
        # Change to project root
        os.chdir(project_root)

        result = deploy_space(
            config_path=config_path,
            databricks_host=databricks_host,
            databricks_token=user_token,  # Use user token for deployment
            parent_path=parent_path,
            verbose=False
        )

        return {
            "space_id": result["space_id"],
            "space_url": result["space_url"]
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def apply_validation_fixes(
    config_path: str,
    replacements: List[Dict] = None,
    bulk_catalog: str = None,
    bulk_schema: str = None,
    exclude_tables: List[str] = None
) -> None:
    """
    Apply table/catalog/schema replacements to config.

    Args:
        config_path: Path to config JSON
        replacements: List of dicts with old/new catalog/schema/table (optional)
        bulk_catalog: Catalog to apply to all tables (optional)
        bulk_schema: Schema to apply to all tables (optional)
        exclude_tables: List of tables (catalog.schema.table) to remove (optional)
    """
    # Remove excluded tables first
    if exclude_tables:
        for table_name in exclude_tables:
            parts = table_name.split('.')
            if len(parts) == 3:
                catalog, schema, table = parts
                remove_table_from_config(
                    config_path=config_path,
                    catalog=catalog,
                    schema=schema,
                    table=table
                )

    # Apply bulk catalog/schema change if specified
    if bulk_catalog and bulk_schema:
        # Load config to get all unique catalog.schema combinations
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if "genie_space_config" in config:
            genie_config = config["genie_space_config"]
        else:
            genie_config = config

        # Get unique catalog.schema combinations
        catalog_schemas = set()
        for table_def in genie_config.get("tables", []):
            old_cat = table_def.get("catalog_name")
            old_sch = table_def.get("schema_name")
            if old_cat and old_sch:
                catalog_schemas.add((old_cat, old_sch))

        # Apply bulk update for each unique combination
        for old_catalog, old_schema in catalog_schemas:
            update_config_catalog_schema(
                config_path=config_path,
                old_catalog=old_catalog,
                old_schema=old_schema,
                new_catalog=bulk_catalog,
                new_schema=bulk_schema
            )

    # Apply individual replacements
    if replacements:
        for rep in replacements:
            update_config_catalog_schema_table(
                config_path=config_path,
                old_catalog=rep["old_catalog"],
                old_schema=rep["old_schema"],
                old_table=rep["old_table"],
                new_catalog=rep["new_catalog"],
                new_schema=rep["new_schema"],
                new_table=rep["new_table"]
            )
