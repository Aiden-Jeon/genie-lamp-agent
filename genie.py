#!/usr/bin/env python3
"""
Genie Lamp Agent - Unified CLI for Databricks Genie Space Creation

This is the main entry point for creating and managing Databricks Genie spaces.

Usage:
    # Full pipeline (recommended)
    python genie.py create --requirements data/demo_requirements.md
    
    # Individual steps
    python genie.py generate --requirements data/demo_requirements.md
    python genie.py validate
    python genie.py deploy
"""

import argparse
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline import generate_config, validate_config, deploy_space, parse_documents


def update_config_catalog_schema(config_path: str, old_catalog: str, old_schema: str, new_catalog: str, new_schema: str):
    """Update catalog and schema in configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Get the genie_space_config
    if "genie_space_config" in config:
        genie_config = config["genie_space_config"]
    else:
        genie_config = config
    
    # Update tables
    updated_count = 0
    for table_def in genie_config.get("tables", []):
        if table_def.get("catalog_name") == old_catalog and table_def.get("schema_name") == old_schema:
            table_def["catalog_name"] = new_catalog
            table_def["schema_name"] = new_schema
            updated_count += 1
    
    # Update SQL expressions
    sql_expr_count = 0
    for expr in genie_config.get("sql_expressions", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        if "expression" in expr and old_prefix in expr["expression"]:
            expr["expression"] = expr["expression"].replace(old_prefix, new_prefix)
            sql_expr_count += 1
    
    # Update example queries
    example_query_count = 0
    for query in genie_config.get("example_sql_queries", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        if "sql_query" in query and old_prefix in query["sql_query"]:
            query["sql_query"] = query["sql_query"].replace(old_prefix, new_prefix)
            example_query_count += 1
    
    # Update benchmark questions
    benchmark_count = 0
    for benchmark in genie_config.get("benchmark_questions", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        updated_this_benchmark = False

        # Update expected_sql field (may be null for FAQ items)
        if "expected_sql" in benchmark and benchmark["expected_sql"] and old_prefix in benchmark["expected_sql"]:
            benchmark["expected_sql"] = benchmark["expected_sql"].replace(old_prefix, new_prefix)
            updated_this_benchmark = True

        # Update table field (contains backtick-quoted table names)
        if "table" in benchmark and benchmark["table"]:
            old_table_ref = f"`{old_catalog}.{old_schema}."
            new_table_ref = f"`{new_catalog}.{new_schema}."
            if old_table_ref in benchmark["table"]:
                benchmark["table"] = benchmark["table"].replace(old_table_ref, new_table_ref)
                updated_this_benchmark = True

        if updated_this_benchmark:
            benchmark_count += 1

    # Update instructions
    instruction_count = 0
    for instruction in genie_config.get("instructions", []):
        old_prefix = f"{old_catalog}.{old_schema}."
        new_prefix = f"{new_catalog}.{new_schema}."
        if "content" in instruction and old_prefix in instruction["content"]:
            instruction["content"] = instruction["content"].replace(old_prefix, new_prefix)
            instruction_count += 1
    
    # Save back to file
    if "genie_space_config" in config:
        config["genie_space_config"] = genie_config
    else:
        config = genie_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return {
        'tables': updated_count,
        'sql_expressions': sql_expr_count,
        'example_queries': example_query_count,
        'benchmark_questions': benchmark_count,
        'instructions': instruction_count
    }


def prompt_catalog_schema_replacement(report, config_path: str) -> bool:
    """
    Prompt user for catalog/schema replacement when tables are not found.
    
    Returns:
        True if configuration was updated, False otherwise
    """
    # Find table_not_found errors
    table_not_found_errors = [
        issue for issue in report.issues 
        if issue.severity == "error" and issue.type == "table_not_found"
    ]
    
    if not table_not_found_errors:
        return False
    
    # Extract unique catalog.schema combinations from failed tables
    failed_schemas = {}
    for issue in table_not_found_errors:
        if issue.table:
            parts = issue.table.split('.')
            if len(parts) == 3:
                catalog, schema, table = parts
                key = f"{catalog}.{schema}"
                if key not in failed_schemas:
                    failed_schemas[key] = []
                failed_schemas[key].append(table)
    
    if not failed_schemas:
        return False
    
    print()
    print("=" * 80)
    print("⚠️  TABLE VALIDATION FAILED")
    print("=" * 80)
    print()
    print("The following catalog.schema combinations have tables that were not found:")
    print()
    
    for i, (schema_key, tables) in enumerate(failed_schemas.items(), 1):
        print(f"  {i}. {schema_key}")
        print(f"     Tables: {', '.join(tables[:3])}" + ("..." if len(tables) > 3 else ""))
    
    print()
    print("Would you like to replace the catalog and schema names?")
    response = input("Replace catalog/schema? [y/N]: ").strip().lower()
    
    if response not in ['y', 'yes']:
        return False
    
    # Prompt for replacements
    updated = False
    for schema_key, tables in failed_schemas.items():
        old_catalog, old_schema = schema_key.split('.')
        
        print()
        print(f"Replacing: {schema_key}")
        new_catalog = input(f"  New catalog (current: {old_catalog}): ").strip()
        new_schema = input(f"  New schema (current: {old_schema}): ").strip()
        
        if new_catalog and new_schema:
            print(f"  Updating {old_catalog}.{old_schema} → {new_catalog}.{new_schema}...")
            counts = update_config_catalog_schema(
                config_path, 
                old_catalog, 
                old_schema, 
                new_catalog, 
                new_schema
            )
            print(f"  ✓ Updated:")
            print(f"     - {counts['tables']} table(s)")
            print(f"     - {counts['sql_expressions']} SQL expression(s)")
            print(f"     - {counts['example_queries']} example query/queries")
            print(f"     - {counts['benchmark_questions']} benchmark question(s)")
            print(f"     - {counts['instructions']} instruction(s)")
            updated = True
        elif not new_catalog and not new_schema:
            print(f"  Skipping {schema_key}")
        else:
            print(f"  ⚠️  Both catalog and schema must be provided. Skipping {schema_key}")
    
    return updated


def cmd_create(args):
    """Run full pipeline: generate → validate → deploy."""
    print("=" * 80)
    print("🧞 Genie Lamp Agent - Full Pipeline")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Generate configuration
        print("📝 Step 1/3: Generating configuration...")
        print("-" * 80)
        
        config_data = generate_config(
            requirements_path=args.requirements,
            output_path=args.output,
            model=args.model,
            endpoint=args.endpoint,
            context_doc=args.context_doc,
            output_doc=args.output_doc,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            no_reasoning=args.no_reasoning,
            faq_section=args.faq_section,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            verbose=True
        )
        
        print()
        print("✓ Configuration generated successfully!")
        print()
        
        # Step 2: Validate tables (unless skipped)
        if not args.skip_validation:
            print("✓ Step 2/3: Validating tables and columns...")
            print("-" * 80)
            
            max_validation_attempts = 3
            validation_attempt = 0
            
            while validation_attempt < max_validation_attempts:
                validation_attempt += 1
                
                report = validate_config(
                    config_path=args.output,
                    databricks_host=args.databricks_host,
                    databricks_token=args.databricks_token,
                    verbose=True
                )
                
                if report.has_errors():
                    print()
                    print("❌ Validation failed with errors!")
                    print()
                    print("Validation Report:")
                    print(report.summary())
                    
                    # Prompt for catalog/schema replacement
                    if not args.yes and validation_attempt < max_validation_attempts:
                        updated = prompt_catalog_schema_replacement(report, args.output)
                        
                        if updated:
                            print()
                            print("=" * 80)
                            print("🔄 Configuration updated. Re-validating...")
                            print("=" * 80)
                            print()
                            continue
                    
                    print()
                    print("Please fix the errors and try again.")
                    return 1
                
                if report.has_warnings():
                    print()
                    print("⚠️  Validation completed with warnings.")
                    print()
                    # Ask user if they want to continue
                    if not args.yes:
                        response = input("Continue with deployment? [y/N]: ")
                        if response.lower() not in ['y', 'yes']:
                            print("Deployment cancelled.")
                            return 0
                
                # Validation passed
                break
            
            print()
            print("✓ Validation passed!")
            print()
        else:
            print("⚠️  Step 2/3: Validation skipped (--skip-validation)")
            print()
        
        # Step 3: Deploy space
        print("🚀 Step 3/3: Deploying Genie space...")
        print("-" * 80)
        
        result = deploy_space(
            config_path=args.output,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            parent_path=args.parent_path,
            verbose=True
        )
        
        # Save result
        if args.result_output:
            result_path = Path(args.result_output)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   Result saved to: {args.result_output}")
        
        print()
        print("=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print()
        print(f"Your Genie space is ready!")
        print()
        print(f"Space ID:  {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return 130
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        
        if args.verbose:
            import traceback
            print("Full traceback:")
            traceback.print_exc()
        
        return 1


def cmd_generate(args):
    """Generate configuration only."""
    print("=" * 80)
    print("📝 Genie Configuration Generator")
    print("=" * 80)
    print()
    
    try:
        config_data = generate_config(
            requirements_path=args.requirements,
            output_path=args.output,
            model=args.model,
            endpoint=args.endpoint,
            context_doc=args.context_doc,
            output_doc=args.output_doc,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            no_reasoning=args.no_reasoning,
            faq_section=args.faq_section,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            verbose=True
        )
        
        print()
        print("=" * 80)
        print("✓ Configuration Summary")
        print("=" * 80)
        
        config = config_data.get("genie_space_config", config_data)
        print(f"\nSpace Name: {config['space_name']}")
        print(f"Description: {config['description'][:100]}...")
        print(f"\nComponents:")
        print(f"  Tables: {len(config['tables'])}")
        print(f"  Instructions: {len(config['instructions'])}")
        print(f"  Example SQL Queries: {len(config['example_sql_queries'])}")
        print(f"  SQL Expressions: {len(config.get('sql_expressions', []))}")
        print(f"  Benchmark Questions: {len(config['benchmark_questions'])}")
        print()
        print(f"Configuration saved to: {args.output}")
        print()
        print("Next steps:")
        print(f"  1. Validate: python genie.py validate")
        print(f"  2. Deploy:   python genie.py deploy")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_validate(args):
    """Validate configuration only."""
    print("=" * 80)
    print("✓ Genie Configuration Validator")
    print("=" * 80)
    print()
    
    try:
        max_validation_attempts = 3
        validation_attempt = 0
        
        while validation_attempt < max_validation_attempts:
            validation_attempt += 1
            
            report = validate_config(
                config_path=args.config,
                databricks_host=args.databricks_host,
                databricks_token=args.databricks_token,
                verbose=True
            )
            
            print()
            print("=" * 80)
            print("Validation Report")
            print("=" * 80)
            print()
            print(report.summary())
            print()
            
            if report.has_errors():
                # Prompt for catalog/schema replacement
                if validation_attempt < max_validation_attempts:
                    updated = prompt_catalog_schema_replacement(report, args.config)
                    
                    if updated:
                        print()
                        print("=" * 80)
                        print("🔄 Configuration updated. Re-validating...")
                        print("=" * 80)
                        print()
                        continue
                
                print("Next steps:")
                print("  1. Fix the errors in your configuration")
                print("  2. Run validation again")
                return 1
            else:
                print("Next steps:")
                print(f"  Deploy: python genie.py deploy")
                return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_deploy(args):
    """Deploy existing configuration."""
    print("=" * 80)
    print("🚀 Genie Space Deployer")
    print("=" * 80)
    print()
    
    try:
        result = deploy_space(
            config_path=args.config,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            parent_path=args.parent_path,
            verbose=True
        )
        
        # Save result
        if args.result_output:
            result_path = Path(args.result_output)
            result_path.parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   Result saved to: {args.result_output}")
        
        print()
        print("=" * 80)
        print("✓ SUCCESS!")
        print("=" * 80)
        print()
        print(f"Space ID:  {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_parse(args):
    """Parse documents into structured requirements format."""
    print("=" * 80)
    print("📄 Document Parser")
    print("=" * 80)
    print()
    
    try:
        result = parse_documents(
            input_dir=args.input_dir,
            output_path=args.output,
            llm_model=args.llm_model,
            vision_model=args.vision_model,
            use_llm=not args.no_llm,
            domain=args.domain,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
            verbose=True,
            max_concurrent_pdfs=args.max_concurrent
        )
        
        print()
        print("=" * 80)
        print("✓ Parsing Summary")
        print("=" * 80)
        print()
        print(f"Output file: {result['output_path']}")
        print()
        print(f"Extracted content:")
        print(f"  Questions: {result['questions_count']}")
        print(f"  Tables: {result['tables_count']}")
        print(f"  SQL Queries: {result['queries_count']}")
        print(f"  Sections: {result['sections_count']}")
        print()
        print(f"LLM enrichment: {'Yes' if result['used_llm'] else 'No'}")
        print(f"Domain: {result['domain']}")
        print()
        print("Next steps:")
        print(f"  Generate config: python genie.py generate --requirements {result['output_path']}")
        print(f"  Full pipeline:   python genie.py create --requirements {result['output_path']}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="genie",
        description="Genie Lamp Agent - Automated Databricks Genie Space Creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline (recommended)
  %(prog)s create --requirements data/demo_requirements.md
  
  # With custom model
  %(prog)s create --requirements data/demo.md --model llama-3-1-70b
  
  # Step by step
  %(prog)s generate --requirements data/demo.md
  %(prog)s validate
  %(prog)s deploy

Environment Variables:
  DATABRICKS_HOST    Databricks workspace URL (required)
  DATABRICKS_TOKEN   Databricks personal access token (required)
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # =========================================================================
    # CREATE command (full pipeline)
    # =========================================================================
    create_parser = subparsers.add_parser(
        "create",
        help="Full pipeline: generate → validate → deploy",
        description="Generate configuration, validate tables, and deploy Genie space in one command"
    )
    
    # Required arguments
    create_parser.add_argument(
        "--requirements",
        type=str,
        required=True,
        help="Path to requirements document"
    )
    
    # Output paths
    create_parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Output path for generated configuration (default: output/genie_space_config.json)"
    )
    create_parser.add_argument(
        "--result-output",
        type=str,
        default="output/genie_space_result.json",
        help="Output path for deployment result (default: output/genie_space_result.json)"
    )
    
    # LLM configuration
    create_parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model name (default: databricks-gpt-5-2)"
    )
    create_parser.add_argument(
        "--endpoint",
        type=str,
        help="Custom serving endpoint (alternative to --model)"
    )
    create_parser.add_argument(
        "--max-tokens",
        type=int,
        default=16000,
        help="Maximum tokens to generate (default: 16000)"
    )
    create_parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature 0.0-1.0 (default: 0.1)"
    )
    create_parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Skip reasoning in LLM output"
    )
    
    # Template paths
    create_parser.add_argument(
        "--context-doc",
        type=str,
        default="src/prompt/templates/curate_effective_genie.md",
        help="Path to context document"
    )
    create_parser.add_argument(
        "--output-doc",
        type=str,
        default="src/prompt/templates/genie_api.md",
        help="Path to output format document"
    )
    
    # Benchmark extraction
    create_parser.add_argument(
        "--faq-section",
        type=str,
        default="## 📊 질문 목록 (FAQ)",
        help="FAQ section title in requirements"
    )
    
    # Validation options
    create_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip table validation (faster but risky)"
    )
    create_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    # Deployment options
    create_parser.add_argument(
        "--parent-path",
        type=str,
        help="Parent workspace path for the space"
    )
    
    # Databricks credentials
    create_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL (overrides DATABRICKS_HOST)"
    )
    create_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token (overrides DATABRICKS_TOKEN)"
    )
    
    create_parser.set_defaults(func=cmd_create)
    
    # =========================================================================
    # GENERATE command
    # =========================================================================
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate configuration only",
        description="Generate Genie space configuration from requirements"
    )
    
    generate_parser.add_argument(
        "--requirements",
        type=str,
        required=True,
        help="Path to requirements document"
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Output path (default: output/genie_space_config.json)"
    )
    generate_parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model name (default: databricks-gpt-5-2)"
    )
    generate_parser.add_argument(
        "--endpoint",
        type=str,
        help="Custom serving endpoint"
    )
    generate_parser.add_argument(
        "--max-tokens",
        type=int,
        default=16000,
        help="Maximum tokens (default: 16000)"
    )
    generate_parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Temperature 0.0-1.0 (default: 0.1)"
    )
    generate_parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Skip reasoning"
    )
    generate_parser.add_argument(
        "--context-doc",
        type=str,
        default="src/prompt/templates/curate_effective_genie.md",
        help="Context document path"
    )
    generate_parser.add_argument(
        "--output-doc",
        type=str,
        default="src/prompt/templates/genie_api.md",
        help="Output format document path"
    )
    generate_parser.add_argument(
        "--faq-section",
        type=str,
        default="## 📊 질문 목록 (FAQ)",
        help="FAQ section title"
    )
    generate_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    generate_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )
    
    generate_parser.set_defaults(func=cmd_generate)
    
    # =========================================================================
    # VALIDATE command
    # =========================================================================
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration only",
        description="Validate tables and columns in configuration"
    )
    
    validate_parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Configuration file path (default: output/genie_space_config.json)"
    )
    validate_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    validate_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )
    
    validate_parser.set_defaults(func=cmd_validate)
    
    # =========================================================================
    # DEPLOY command
    # =========================================================================
    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Deploy existing configuration",
        description="Deploy Genie space from existing configuration"
    )
    
    deploy_parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Configuration file path (default: output/genie_space_config.json)"
    )
    deploy_parser.add_argument(
        "--result-output",
        type=str,
        default="output/genie_space_result.json",
        help="Result output path (default: output/genie_space_result.json)"
    )
    deploy_parser.add_argument(
        "--parent-path",
        type=str,
        help="Parent workspace path"
    )
    deploy_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL"
    )
    deploy_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token"
    )
    
    deploy_parser.set_defaults(func=cmd_deploy)
    
    # =========================================================================
    # PARSE command
    # =========================================================================
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse documents into structured requirements",
        description="Parse PDF and markdown files into structured requirements format"
    )
    
    parse_parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing PDF and markdown files"
    )
    parse_parser.add_argument(
        "--output",
        type=str,
        default="data/parsed_requirements.md",
        help="Output path for generated markdown (default: data/parsed_requirements.md)"
    )
    parse_parser.add_argument(
        "--llm-model",
        type=str,
        default=os.getenv("LLM_MODEL", "databricks-gpt-5-2"),
        help="Foundation model for text-based LLM enrichment (default: databricks-gpt-5-2)"
    )
    parse_parser.add_argument(
        "--vision-model",
        type=str,
        default=os.getenv("VISION_MODEL", "databricks-claude-sonnet-4"),
        help="Foundation model for image-based PDF parsing (default: databricks-claude-sonnet-4)"
    )
    parse_parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM enrichment (faster but less intelligent)"
    )
    parse_parser.add_argument(
        "--domain",
        type=str,
        choices=["social_analytics", "kpi_analytics", "combined"],
        default="combined",
        help="Domain type (default: combined)"
    )
    parse_parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL (required if using LLM)"
    )
    parse_parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks token (required if using LLM)"
    )
    parse_parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum number of PDFs to process concurrently (default: 3)"
    )
    
    parse_parser.set_defaults(func=cmd_parse)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
