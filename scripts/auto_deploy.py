#!/usr/bin/env python3
"""Automated Genie deployment with catalog replacement."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from genie.pipeline import generate_config, validate_config, deploy_space

# Load environment variables
load_dotenv()


def auto_deploy(
    requirements_path: str = "real_requirements/parsed/parsed_requirements.md",
    output_path: str = "output/genie_space_config.json",
    result_output: str = "output/genie_space_result.json",
    auto_replace_catalog: str = "sandbox",
    auto_replace_schema: str = "agent_poc"
):
    """Run full deployment with automatic catalog replacement."""

    print("=" * 80)
    print("🧞 Automated Genie Deployment")
    print("=" * 80)
    print()

    # Step 1: Generate configuration
    print("📝 Step 1/3: Generating configuration...")
    print("-" * 80)

    config_data = generate_config(
        requirements_path=requirements_path,
        output_path=output_path,
        verbose=True
    )

    print()
    print("✓ Configuration generated!")
    print()

    # Step 2: Validate with automatic replacement
    print("✓ Step 2/3: Validating with automatic catalog replacement...")
    print("-" * 80)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\nValidation attempt {attempt}/{max_attempts}")

        report = validate_config(
            config_path=output_path,
            verbose=True
        )

        if report.has_errors():
            # Check for table_not_found errors
            table_errors = [
                issue for issue in report.issues
                if issue.severity == "error" and issue.type == "table_not_found"
            ]

            if table_errors and attempt < max_attempts:
                print()
                print(f"⚠️  Found {len(table_errors)} table validation errors")
                print(f"🔄 Auto-replacing catalog.schema to {auto_replace_catalog}.{auto_replace_schema}")

                # Extract unique catalog.schema combinations
                failed_schemas = {}
                for issue in table_errors:
                    if issue.table:
                        parts = issue.table.split('.')
                        if len(parts) == 3:
                            catalog, schema, table = parts
                            key = f"{catalog}.{schema}"
                            if key not in failed_schemas:
                                failed_schemas[key] = []
                            failed_schemas[key].append(table)

                # Replace each failed catalog.schema
                import json
                from genie import update_config_catalog_schema

                for schema_key in failed_schemas.keys():
                    old_catalog, old_schema = schema_key.split('.')
                    print(f"  Replacing {old_catalog}.{old_schema} → {auto_replace_catalog}.{auto_replace_schema}")

                    counts = update_config_catalog_schema(
                        output_path,
                        old_catalog,
                        old_schema,
                        auto_replace_catalog,
                        auto_replace_schema
                    )

                    print(f"    Updated: {counts['tables']} tables, {counts['sql_expressions']} SQL expressions")
                    print(f"             {counts['example_queries']} queries, {counts['benchmark_questions']} benchmarks")

                print()
                continue
            else:
                print()
                print("❌ Validation failed!")
                print()
                print(report.summary())
                return 1

        # Validation passed
        print()
        print("✓ Validation passed!")
        break

    # Step 3: Deploy
    print()
    print("🚀 Step 3/3: Deploying Genie space...")
    print("-" * 80)

    result = deploy_space(
        config_path=output_path,
        verbose=True
    )

    # Save result
    result_path = Path(result_output)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 80)
    print("✓ DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()
    print(f"Space ID:  {result['space_id']}")
    print(f"Space URL: {result['space_url']}")
    print()
    print(f"Configuration: {output_path}")
    print(f"Result:        {result_output}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(auto_deploy())
