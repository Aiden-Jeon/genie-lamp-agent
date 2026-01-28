#!/usr/bin/env python3
"""
Standalone script to validate tables and columns in a Genie space configuration.

This script checks that all tables and columns referenced in the configuration
actually exist in your Databricks Unity Catalog before attempting to create
the Genie space.

Usage:
    python scripts/validate_tables.py
    python scripts/validate_tables.py output/genie_space_config.json
    python scripts/validate_tables.py --help

Environment Variables Required:
    DATABRICKS_HOST: Your Databricks workspace URL
    DATABRICKS_TOKEN: Your Databricks personal access token

Examples:
    # Validate default config
    python scripts/validate_tables.py
    
    # Validate custom config
    python scripts/validate_tables.py my_config.json
    
    # Show detailed output
    python scripts/validate_tables.py --verbose
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.table_validator import TableValidator, ValidationReport
from dotenv import load_dotenv


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate tables and columns in Genie space configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s output/genie_space_config.json
  %(prog)s --verbose

Environment Variables:
  DATABRICKS_HOST    Databricks workspace URL (required)
  DATABRICKS_TOKEN   Databricks personal access token (required)
        """
    )
    
    parser.add_argument(
        "config_path",
        nargs="?",
        default="output/genie_space_config.json",
        help="Path to Genie space configuration file (default: output/genie_space_config.json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation output"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    return parser.parse_args()


def main():
    """Main validation script."""
    args = parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Check environment variables
    if not os.getenv("DATABRICKS_HOST"):
        print("✗ Error: DATABRICKS_HOST environment variable not set")
        print("  Please create a .env file with your Databricks credentials")
        print("  See .env.example for reference")
        return 1
    
    if not os.getenv("DATABRICKS_TOKEN"):
        print("✗ Error: DATABRICKS_TOKEN environment variable not set")
        print("  Please create a .env file with your Databricks credentials")
        print("  See .env.example for reference")
        return 1
    
    # Check config file exists
    config_path = args.config_path
    if not Path(config_path).exists():
        print(f"✗ Error: Configuration file not found: {config_path}")
        print()
        print("Please generate a configuration first:")
        print("  python main.py --model databricks-gpt-5-2")
        return 1
    
    if not args.json:
        print("=" * 80)
        print("TABLE & COLUMN VALIDATOR FOR GENIE SPACE")
        print("=" * 80)
        print()
        print(f"Configuration file: {config_path}")
        print(f"Databricks host:    {os.getenv('DATABRICKS_HOST')}")
        print()
        print("Starting validation...")
        print()
    
    try:
        # Initialize validator
        validator = TableValidator()
        
        # Run validation
        report = validator.validate_config(config_path)
        
        # Output results
        if args.json:
            import json
            output = {
                "config_path": config_path,
                "tables_checked": report.tables_checked,
                "tables_valid": report.tables_valid,
                "tables_invalid": report.tables_invalid,
                "total_columns_checked": sum(len(cols) for cols in report.columns_checked.values()),
                "total_columns_valid": sum(len(cols) for cols in report.columns_valid.values()),
                "total_columns_invalid": sum(len(cols) for cols in report.columns_invalid.values()),
                "issues": [
                    {
                        "severity": issue.severity,
                        "type": issue.type,
                        "message": issue.message,
                        "table": issue.table,
                        "column": issue.column,
                        "location": issue.location
                    }
                    for issue in report.issues
                ],
                "has_errors": report.has_errors(),
                "has_warnings": report.has_warnings()
            }
            print(json.dumps(output, indent=2))
        else:
            # Print human-readable report
            print(report.summary())
        
        # Return appropriate exit code
        if report.has_errors():
            if not args.json:
                print()
                print("Next steps:")
                print("  1. Check that the tables exist in your Unity Catalog")
                print("  2. Verify you have proper access permissions")
                print("  3. Update the configuration file to fix any issues")
                print("  4. Run this validation again")
            return 1
        else:
            if not args.json:
                print()
                print("Next steps:")
                print("  1. Update warehouse_id in your configuration if needed")
                print("  2. Create the Genie space: python scripts/create_genie_space.py")
            return 0
    
    except Exception as e:
        if args.json:
            import json
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"✗ Validation failed with error:")
            print(f"  {e}")
            print()
            if args.verbose:
                import traceback
                traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
