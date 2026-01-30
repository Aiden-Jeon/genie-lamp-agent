"""Background job task wrappers for existing pipeline functions."""

import asyncio
import os
import sys
from typing import Dict, List

# Add project root to path to import existing modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.pipeline.parser import parse_documents_async
from src.pipeline.generator import generate_config
from src.pipeline.validator import validate_config
from src.pipeline.deployer import deploy_space
from genie import update_config_catalog_schema_table, update_config_catalog_schema, remove_table_from_config


def run_parse_job(file_paths: List[str], use_llm: bool, output_path: str) -> Dict:
    """
    Run parsing job on uploaded files.

    Args:
        file_paths: List of file paths to parse
        use_llm: Whether to use LLM enrichment
        output_path: Where to save parsed output

    Returns:
        Dict with output_path and parsing stats
    """
    # Get input directory from first file
    input_dir = os.path.dirname(file_paths[0])

    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Change to project root
        os.chdir(project_root)

        # Run existing parser with asyncio.run() since it's an async function
        result = asyncio.run(parse_documents_async(
            input_dir=input_dir,
            output_path=output_path,
            use_llm=use_llm,
            verbose=False
        ))

        return {
            "output_path": output_path,
            "tables_found": result.get("tables_count", 0),
            "files_parsed": len(file_paths)
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def run_generate_job(requirements_path: str, output_path: str, model: str) -> Dict:
    """
    Generate Genie space configuration from requirements.

    Args:
        requirements_path: Path to requirements markdown
        output_path: Where to save generated config
        model: LLM model to use

    Returns:
        Dict with output_path and config metadata
    """
    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Change to project root so template paths resolve correctly
        os.chdir(project_root)

        result = generate_config(
            requirements_path=requirements_path,
            output_path=output_path,
            model=model,
            validate_sql=True,
            verbose=False
        )

        return {
            "output_path": output_path,
            "config": result
        }
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def run_validate_job(config_path: str) -> Dict:
    """
    Validate Genie space configuration against Unity Catalog.

    Args:
        config_path: Path to config JSON

    Returns:
        Dict with validation results
    """
    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Change to project root
        os.chdir(project_root)

        report = validate_config(config_path=config_path, verbose=False)

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


def run_deploy_job(config_path: str, parent_path: str = None) -> Dict:
    """
    Deploy Genie space to Databricks.

    Args:
        config_path: Path to config JSON
        parent_path: Optional parent folder path

    Returns:
        Dict with space_id and space_url
    """
    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Change to project root
        os.chdir(project_root)

        result = deploy_space(
            config_path=config_path,
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
