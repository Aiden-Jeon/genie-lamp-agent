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

from src.pipeline import generate_config, validate_config, deploy_space


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
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
