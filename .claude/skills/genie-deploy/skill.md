---
name: genie-deploy
description: Automated Genie space deployment from real_requirements with automatic catalog replacement to sandbox.agent_poc. Use when the user asks to deploy genie, create a genie space from real requirements, or wants to automate the full deployment workflow with the real requirements.
---

# Genie Deploy

Automate the complete Genie space deployment workflow including document parsing, generation, validation with automatic catalog replacement, and deployment.

## Deployment Workflow

Follow this workflow when the user requests deployment:

### 1. Parse Requirements Documents

**ALWAYS start by parsing documents from the `real_requirements` directory** using the virtual environment:

```bash
.venv/bin/python genie.py parse --input-dir real_requirements --output data/parsed.md
```

This will:
- Parse all PDF and markdown files in `real_requirements/`
- Extract FAQ questions, table specifications, and business context
- Output structured requirements to `data/parsed.md`

### 2. Create Genie Configuration Script

Create a Python script that automates the full pipeline with automatic catalog replacement. Save this as `scripts/auto_deploy.py`:

```python
#!/usr/bin/env python3
"""Automated Genie deployment with catalog replacement."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.pipeline import generate_config, validate_config, deploy_space

# Load environment variables
load_dotenv()


def auto_deploy(
    requirements_path: str = "data/parsed.md",
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
```

### 3. Run Automated Deployment

Execute the automated deployment script:

```bash
.venv/bin/python scripts/auto_deploy.py
```

This will:
1. Generate configuration from `data/parsed.md`
2. Validate tables against Unity Catalog
3. Automatically replace any failed catalog.schema with `sandbox.agent_poc`
4. Re-validate up to 3 times if needed
5. Deploy the Genie space

### 4. Verify Deployment

After deployment completes, verify the results:

```bash
# Check the deployment result
cat output/genie_space_result.json

# Check the final configuration
cat output/genie_space_config.json
```

## Configuration

The automated deployment uses these defaults:

- **Requirements input**: `data/parsed.md` (from parse step)
- **Config output**: `output/genie_space_config.json`
- **Result output**: `output/genie_space_result.json`
- **Auto-replace catalog**: `sandbox`
- **Auto-replace schema**: `agent_poc`

## Environment Variables

Required in `.env`:
- `DATABRICKS_HOST`: Databricks workspace URL
- `DATABRICKS_TOKEN`: Personal access token

Optional:
- `LLM_MODEL`: Text model for generation (default: databricks-gpt-5-2)
- `VISION_MODEL`: Vision model for PDF parsing (default: databricks-claude-sonnet-4)

## Error Handling

### Parse Failures

If parsing fails:
1. Check that `real_requirements/` directory exists and contains PDF/markdown files
2. Verify environment variables are set correctly
3. Check for corrupt or unsupported file formats

### Validation Failures

If validation still fails after 3 attempts:
1. Check that `sandbox.agent_poc` schema exists in Unity Catalog
2. Verify table names are correct in the requirements
3. Manually inspect `output/genie_space_config.json` for issues

### Deployment Failures

If deployment fails:
1. Verify Databricks credentials are valid
2. Check that you have permissions to create Genie spaces
3. Ensure parent workspace path is accessible

## Manual Override

If you need to customize the replacement catalog/schema, edit `scripts/auto_deploy.py`:

```python
# Change these parameters in the auto_deploy() call
sys.exit(auto_deploy(
    auto_replace_catalog="your_catalog",
    auto_replace_schema="your_schema"
))
```

## Project-Specific Details

### Virtual Environment

Always use `.venv/bin/python` instead of `python` or `python3` as enforced by project standards.

### Output Directory Structure

```
output/
├── genie_space_config.json    # Generated configuration
└── genie_space_result.json    # Deployment result with space ID and URL
```

### Requirements Format

The parser expects documents in `real_requirements/` with:
- **FAQ sections**: Business questions to extract as benchmarks
- **Table specifications**: Table names and sample queries
- **Business context**: Domain-specific requirements

## Quick Reference

### Full Workflow (One Command)

```bash
# Parse, generate, validate with auto-replacement, and deploy
.venv/bin/python genie.py parse --input-dir real_requirements --output data/parsed.md && \
.venv/bin/python scripts/auto_deploy.py
```

### Step-by-Step Workflow

```bash
# Step 1: Parse documents
.venv/bin/python genie.py parse --input-dir real_requirements --output data/parsed.md

# Step 2: Generate and deploy with auto-replacement
.venv/bin/python scripts/auto_deploy.py
```

### Check Deployment Status

```bash
# View space details
cat output/genie_space_result.json | jq '.space_url'

# View configuration
cat output/genie_space_config.json | jq '.space_name'
```

## Best Practices

1. **Always parse first**: Use `parse` command to convert documents to structured format
2. **Check parsed output**: Review `data/parsed.md` before generation
3. **Verify catalog exists**: Ensure `sandbox.agent_poc` schema exists in Unity Catalog
4. **Test with demo data**: Test the workflow with demo requirements first
5. **Save outputs**: Keep `output/` directory for debugging and audit trails

## References

See the main project documentation for more details:
- `CLAUDE.md`: Project overview and development commands
- `README.md`: User guide and setup instructions
- `ARCHITECTURE.md`: System architecture and design decisions
