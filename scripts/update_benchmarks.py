#!/usr/bin/env python3
"""
Update benchmarks in an existing Genie space configuration.

This script replaces LLM-generated benchmarks with directly extracted ones
from the requirements document. Use this to fix incomplete benchmark extraction
without regenerating the entire configuration.

Usage:
    # Update benchmarks in existing config
    python scripts/update_benchmarks.py

    # Specify custom paths
    python scripts/update_benchmarks.py \\
        --config output/genie_space_config.json \\
        --requirements data/demo_requirements.md \\
        --output output/genie_space_config_fixed.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmark_extractor import (
    extract_all_benchmarks,
    merge_benchmarks_into_config,
    validate_benchmarks
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update benchmarks in Genie space configuration"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="output/genie_space_config.json",
        help="Path to existing configuration file"
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default="data/demo_requirements.md",
        help="Path to requirements document"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (defaults to overwriting input config)"
    )
    parser.add_argument(
        "--faq-section",
        type=str,
        default="## 📊 질문 목록 (FAQ)",
        help="FAQ section title to extract benchmarks from"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing benchmarks instead of replacing"
    )
    parser.add_argument(
        "--faq-only",
        action="store_true",
        help="Extract only FAQ questions (skip sample queries)"
    )
    parser.add_argument(
        "--sample-queries-only",
        action="store_true",
        help="Extract only sample queries (skip FAQ questions)"
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    config_path = Path(args.config)
    requirements_path = Path(args.requirements)
    output_path = Path(args.output) if args.output else config_path
    
    # Validate input files exist
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        return 1
    
    if not requirements_path.exists():
        print(f"❌ Error: Requirements file not found: {requirements_path}")
        return 1
    
    print("\n" + "="*80)
    print("UPDATE BENCHMARKS IN GENIE SPACE CONFIGURATION")
    print("="*80 + "\n")
    
    # =========================================================================
    # STEP 1: Load existing configuration
    # =========================================================================
    print("STEP 1: Loading existing configuration")
    print("-"*80 + "\n")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Get original benchmark count
        if "genie_space_config" in config_data:
            config = config_data["genie_space_config"]
            original_benchmarks = config.get("benchmark_questions", [])
        else:
            config = config_data
            original_benchmarks = config.get("benchmark_questions", [])
        
        print(f"✓ Loaded configuration from: {config_path}")
        print(f"  Space Name: {config.get('space_name', 'N/A')}")
        print(f"  Current Benchmarks: {len(original_benchmarks)}")
        
        if original_benchmarks:
            print(f"\n  Current benchmark examples:")
            for i, bm in enumerate(original_benchmarks[:3], 1):
                print(f"    {i}. {bm['question'][:60]}...")
            if len(original_benchmarks) > 3:
                print(f"    ... and {len(original_benchmarks) - 3} more")
    
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1
    
    # =========================================================================
    # STEP 2: Extract benchmarks from requirements
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 2: Extracting benchmarks from requirements")
    print("-"*80 + "\n")
    
    try:
        # Determine what to extract
        include_faq = not args.sample_queries_only
        include_sample_queries = not args.faq_only
        
        benchmarks = extract_all_benchmarks(
            requirements_path=str(requirements_path),
            include_faq=include_faq,
            include_sample_queries=include_sample_queries,
            faq_section_title=args.faq_section
        )
        
        # Count by type
        faq_count = sum(1 for bm in benchmarks if bm.get('source') == 'faq')
        sample_query_count = sum(1 for bm in benchmarks if bm.get('source') == 'sample_query')
        
        print(f"✓ Extracted {len(benchmarks)} benchmarks from: {requirements_path}")
        if faq_count > 0 and sample_query_count > 0:
            print(f"  - FAQ questions: {faq_count}")
            print(f"  - Sample queries: {sample_query_count} (with expected SQL)")
        
        # Show examples by type
        if benchmarks:
            print(f"\n  Extracted benchmark examples:")
            
            # Show FAQ examples
            faq_examples = [bm for bm in benchmarks if bm.get('source') == 'faq'][:3]
            if faq_examples:
                print(f"\n    FAQ Questions:")
                for i, bm in enumerate(faq_examples, 1):
                    print(f"    {i}. {bm['question']}")
            
            # Show sample query examples
            sample_examples = [bm for bm in benchmarks if bm.get('source') == 'sample_query'][:3]
            if sample_examples:
                print(f"\n    Sample Queries (with SQL):")
                for i, bm in enumerate(sample_examples, 1):
                    print(f"    {i}. {bm['question']}")
            
            if len(benchmarks) > 6:
                print(f"\n    ... and {len(benchmarks) - 6} more")
        
        # Validate
        report = validate_benchmarks(benchmarks)
        print(f"\n  Validation:")
        print(f"    Valid: {report['valid_count']}/{report['total_count']}")
        
        if report['issues']:
            print(f"\n  Issues:")
            for issue in report['issues']:
                print(f"    - {issue}")
    
    except Exception as e:
        print(f"❌ Error extracting benchmarks: {e}")
        return 1
    
    # =========================================================================
    # STEP 3: Merge benchmarks
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 3: Merging benchmarks")
    print("-"*80 + "\n")
    
    try:
        replace_mode = not args.append
        config_data = merge_benchmarks_into_config(
            config=config_data,
            benchmarks=benchmarks,
            replace=replace_mode
        )
        
        if replace_mode:
            print(f"✓ Replaced {len(original_benchmarks)} existing benchmarks")
            print(f"✓ Added {len(benchmarks)} directly extracted benchmarks")
        else:
            new_count = len(benchmarks) - len(original_benchmarks)
            print(f"✓ Kept {len(original_benchmarks)} existing benchmarks")
            print(f"✓ Added {new_count} new benchmarks")
            print(f"✓ Total benchmarks: {len(benchmarks)}")
    
    except Exception as e:
        print(f"❌ Error merging benchmarks: {e}")
        return 1
    
    # =========================================================================
    # STEP 4: Save updated configuration
    # =========================================================================
    print("\n" + "-"*80)
    print("STEP 4: Saving updated configuration")
    print("-"*80 + "\n")
    
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuration saved to: {output_path}")
        
        # Final summary
        if "genie_space_config" in config_data:
            final_config = config_data["genie_space_config"]
        else:
            final_config = config_data
        
        final_benchmarks = final_config.get("benchmark_questions", [])
        
        print(f"\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\nBenchmark Update:")
        print(f"  Original: {len(original_benchmarks)} benchmarks")
        print(f"  Updated:  {len(final_benchmarks)} benchmarks")
        print(f"  Change:   {len(final_benchmarks) - len(original_benchmarks):+d} benchmarks")
        
        print(f"\nConfiguration Components:")
        print(f"  Tables: {len(final_config.get('tables', []))}")
        print(f"  Instructions: {len(final_config.get('instructions', []))}")
        print(f"  Example SQL Queries: {len(final_config.get('example_sql_queries', []))}")
        print(f"  Benchmark Questions: {len(final_benchmarks)} ✓")
        
        print(f"\n✓ Benchmarks successfully updated!")
        
        if output_path != config_path:
            print(f"\nOriginal config preserved at: {config_path}")
            print(f"Updated config saved to: {output_path}")
        
        print(f"\nNext steps:")
        print(f"  1. Review updated benchmarks: cat {output_path}")
        print(f"  2. Validate with: python compare_benchmarks.py")
        print(f"  3. Create/update Genie space: python scripts/create_genie_space.py")
    
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
