#!/usr/bin/env python3
"""
Generate Genie space configuration with direct benchmark extraction.

This script:
1. Generates the configuration using LLM (for tables, instructions, examples, etc.)
2. Extracts benchmarks DIRECTLY from requirements document (bypassing LLM)
3. Merges the extracted benchmarks into the configuration
4. Saves the final configuration

This ensures 100% coverage of FAQ questions as benchmarks without relying on
LLM's interpretation or selection.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prompt_builder import PromptBuilder
from databricks_llm import DatabricksFoundationModelClient, DatabricksLLMClient
from models import LLMResponse
from benchmark_extractor import (
    extract_all_benchmarks,
    merge_benchmarks_into_config,
    validate_benchmarks
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Genie space configuration with direct benchmark extraction"
    )
    
    # LLM configuration
    parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model to use (e.g., databricks-gpt-5-2, llama-3-1-70b)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Custom serving endpoint name (alternative to foundation model)"
    )
    
    # Input/output paths
    parser.add_argument(
        "--input-data",
        type=str,
        default="data/demo_requirements.md",
        help="Path to requirements document"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Output file path"
    )
    parser.add_argument(
        "--context-doc",
        type=str,
        default="src/docs/curate_effective_genie.md",
        help="Path to context document"
    )
    parser.add_argument(
        "--output-doc",
        type=str,
        default="src/docs/genie_api.md",
        help="Path to output format document"
    )
    
    # LLM parameters
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=16000,
        help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (0.0-1.0)"
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Skip reasoning in LLM output"
    )
    
    # Benchmark extraction
    parser.add_argument(
        "--faq-section",
        type=str,
        default="## 📊 질문 목록 (FAQ)",
        help="FAQ section title to extract benchmarks from"
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Load existing config and only update benchmarks (skip LLM generation)"
    )
    
    # Databricks configuration
    parser.add_argument(
        "--databricks-host",
        type=str,
        help="Databricks workspace URL (overrides DATABRICKS_HOST env var)"
    )
    parser.add_argument(
        "--databricks-token",
        type=str,
        help="Databricks personal access token (overrides DATABRICKS_TOKEN env var)"
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Get credentials
    host = args.databricks_host or os.getenv("DATABRICKS_HOST")
    token = args.databricks_token or os.getenv("DATABRICKS_TOKEN")
    
    if not host or not token:
        print("❌ Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        print("   Either set environment variables or use --databricks-host and --databricks-token")
        return 1
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # STEP 1: Generate or load configuration
    # =========================================================================
    if args.skip_llm:
        print("\n" + "="*80)
        print("STEP 1: Loading existing configuration (--skip-llm)")
        print("="*80 + "\n")
        
        if not output_path.exists():
            print(f"❌ Error: Config file not found: {output_path}")
            print("   Remove --skip-llm to generate a new configuration")
            return 1
        
        with open(output_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print(f"✓ Loaded existing configuration from: {output_path}")
        
    else:
        print("\n" + "="*80)
        print("STEP 1: Generating configuration with LLM")
        print("="*80 + "\n")
        
        # Build prompt
        print("Building prompt...")
        builder = PromptBuilder(
            context_doc_path=args.context_doc,
            output_doc_path=args.output_doc,
            input_data_path=args.input_data
        )
        
        if args.no_reasoning:
            prompt = builder.build_prompt()
        else:
            prompt = builder.build_prompt_with_reasoning()
        
        print(f"✓ Prompt built ({len(prompt)} characters)")
        
        # Initialize LLM client
        print(f"\nInitializing LLM client...")
        if args.endpoint:
            print(f"  Using custom endpoint: {args.endpoint}")
            llm_client = DatabricksLLMClient(
                endpoint_name=args.endpoint,
                host=host,
                token=token
            )
        else:
            print(f"  Using foundation model: {args.model}")
            llm_client = DatabricksFoundationModelClient(
                model_name=args.model,
                host=host,
                token=token
            )
        
        # Generate configuration
        print(f"\nGenerating configuration...")
        print(f"  Max tokens: {args.max_tokens}")
        print(f"  Temperature: {args.temperature}")
        print(f"  This may take 30-60 seconds...\n")
        
        try:
            response = llm_client.generate_genie_config(
                prompt=prompt,
                max_tokens=args.max_tokens,
                temperature=args.temperature
            )
            
            print("✓ Configuration generated by LLM")
            
            # Extract config
            config_data = response.model_dump()
            
            # Show summary
            config = config_data["genie_space_config"]
            print(f"\n  Space Name: {config['space_name']}")
            print(f"  Tables: {len(config['tables'])}")
            print(f"  Instructions: {len(config['instructions'])}")
            print(f"  Example SQL Queries: {len(config['example_sql_queries'])}")
            print(f"  LLM-Generated Benchmarks: {len(config.get('benchmark_questions', []))}")
            
            if "reasoning" in config_data and config_data["reasoning"]:
                print(f"\n  LLM Reasoning:")
                reasoning = config_data["reasoning"][:300]
                print(f"    {reasoning}...")
            
            if "confidence_score" in config_data:
                print(f"\n  Confidence Score: {config_data['confidence_score']}")
        
        except Exception as e:
            print(f"❌ Error generating configuration: {e}")
            return 1
    
    # =========================================================================
    # STEP 2: Extract benchmarks directly from requirements
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 2: Extracting benchmarks directly from requirements")
    print("="*80 + "\n")
    
    try:
        benchmarks = extract_all_benchmarks(
            requirements_path=args.input_data,
            include_faq=True,
            include_sample_queries=True,
            faq_section_title=args.faq_section
        )
        
        # Count by type
        faq_count = sum(1 for bm in benchmarks if bm.get('source') == 'faq')
        sample_query_count = sum(1 for bm in benchmarks if bm.get('source') == 'sample_query')
        
        print(f"✓ Extracted {len(benchmarks)} benchmarks from requirements")
        print(f"  - FAQ questions: {faq_count}")
        print(f"  - Sample queries: {sample_query_count} (with expected SQL)")
        
        # Show examples by type
        if benchmarks:
            print(f"\n  Examples:")
            
            # Show FAQ examples
            faq_examples = [bm for bm in benchmarks if bm.get('source') == 'faq'][:3]
            if faq_examples:
                print(f"\n    FAQ Questions:")
                for i, bm in enumerate(faq_examples, 1):
                    print(f"    {i}. {bm['question']}")
            
            # Show sample query examples
            sample_examples = [bm for bm in benchmarks if bm.get('source') == 'sample_query'][:2]
            if sample_examples:
                print(f"\n    Sample Queries (with SQL):")
                for i, bm in enumerate(sample_examples, 1):
                    print(f"    {i}. {bm['question']}")
            
            if len(benchmarks) > 5:
                print(f"    ... and {len(benchmarks) - 5} more")
        
        # Validate benchmarks
        report = validate_benchmarks(benchmarks)
        print(f"\n  Validation:")
        print(f"    Total: {report['total_count']}")
        print(f"    Valid: {report['valid_count']}")
        print(f"    Invalid: {report['invalid_count']}")
        
        if report['issues']:
            print(f"\n  Issues:")
            for issue in report['issues']:
                print(f"    - {issue}")
            print(f"\n⚠ Warning: Some benchmarks failed validation")
        
    except Exception as e:
        print(f"❌ Error extracting benchmarks: {e}")
        return 1
    
    # =========================================================================
    # STEP 3: Merge benchmarks into configuration
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3: Merging benchmarks into configuration")
    print("="*80 + "\n")
    
    # Get original benchmark count
    if "genie_space_config" in config_data:
        original_count = len(config_data["genie_space_config"].get("benchmark_questions", []))
    else:
        original_count = len(config_data.get("benchmark_questions", []))
    
    # Merge (replace LLM-generated benchmarks with directly extracted ones)
    config_data = merge_benchmarks_into_config(
        config=config_data,
        benchmarks=benchmarks,
        replace=True  # Replace LLM-generated benchmarks
    )
    
    print(f"✓ Replaced {original_count} LLM-generated benchmarks")
    print(f"✓ Added {len(benchmarks)} directly extracted benchmarks")
    
    # =========================================================================
    # STEP 4: Save final configuration
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 4: Saving final configuration")
    print("="*80 + "\n")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuration saved to: {output_path}")
        
        # Final summary
        if "genie_space_config" in config_data:
            config = config_data["genie_space_config"]
        else:
            config = config_data
        
        print(f"\n" + "="*80)
        print("FINAL CONFIGURATION SUMMARY")
        print("="*80)
        print(f"\nSpace Name: {config['space_name']}")
        print(f"Description: {config['description'][:100]}...")
        print(f"\nComponents:")
        print(f"  Tables: {len(config['tables'])}")
        print(f"  Instructions: {len(config['instructions'])}")
        print(f"  Example SQL Queries: {len(config['example_sql_queries'])}")
        print(f"  SQL Expressions: {len(config.get('sql_expressions', []))}")
        print(f"  Benchmark Questions: {len(config['benchmark_questions'])} ✓ (directly extracted)")
        print(f"\n✓ Configuration is ready for Genie space creation!")
        print(f"\nNext steps:")
        print(f"  1. Review the configuration: cat {output_path}")
        print(f"  2. Create Genie space: python scripts/create_genie_space.py")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
