#!/usr/bin/env python3
"""Fix configuration and deploy."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from genie.pipeline import deploy_space

# Load environment variables
load_dotenv()


def filter_valid_benchmarks(config_path: str):
    """Remove benchmarks that reference non-existent tables."""
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Get configured table names
    genie_config = config.get('genie_space_config', {})
    tables = genie_config.get('tables', [])
    
    valid_table_names = set()
    for table in tables:
        fqn = f"{table['catalog_name']}.{table['schema_name']}.{table['table_name']}"
        valid_table_names.add(fqn)
        # Also add without catalog.schema for partial matches
        valid_table_names.add(table['table_name'])
    
    print(f"Valid tables: {valid_table_names}")
    
    # Filter benchmarks
    benchmarks = genie_config.get('benchmark_questions', [])
    invalid_tables = [
        'community_discussions_topics',
        'community_discussions_comments', 
        'partner_wishlist',
        'partner_traffic',
        'partner_regions_and_countries',
        'channel_list',
        'thread_list',
        'steam_app_id'
    ]
    
    valid_benchmarks = []
    removed_count = 0
    
    for bm in benchmarks:
        answer = bm.get('answer', [])
        if not answer:
            valid_benchmarks.append(bm)
            continue
            
        sql = answer[0].get('content', [''])[0] if answer else ''
        
        # Check if SQL contains any invalid table references
        contains_invalid = any(invalid_table in sql.lower() for invalid_table in invalid_tables)
        
        if not contains_invalid:
            valid_benchmarks.append(bm)
        else:
            removed_count += 1
            print(f"Removing benchmark (invalid tables): {bm.get('question', [''])[0][:80]}")
    
    print(f"\nRemoved {removed_count} benchmarks with invalid table references")
    print(f"Keeping {len(valid_benchmarks)} valid benchmarks")
    
    # Update config
    genie_config['benchmark_questions'] = valid_benchmarks
    config['genie_space_config'] = genie_config
    
    # Save cleaned config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Cleaned configuration saved to {config_path}")
    
    return len(valid_benchmarks)


def main():
    config_path = "output/genie_space_config.json"
    result_path = "output/genie_space_result.json"
    
    print("=" * 80)
    print("🔧 Fixing and Deploying Genie Space")
    print("=" * 80)
    print()
    
    # Step 1: Filter invalid benchmarks
    print("📝 Step 1/2: Removing invalid benchmarks...")
    print("-" * 80)
    
    benchmark_count = filter_valid_benchmarks(config_path)
    
    print()
    
    # Step 2: Deploy
    print("🚀 Step 2/2: Deploying Genie space...")
    print("-" * 80)
    
    try:
        result = deploy_space(
            config_path=config_path,
            verbose=True
        )
        
        # Save result
        result_path_obj = Path(result_path)
        result_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_path_obj, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 80)
        print("✓ DEPLOYMENT SUCCESSFUL!")
        print("=" * 80)
        print()
        print(f"Space ID:  {result['space_id']}")
        print(f"Space URL: {result['space_url']}")
        print()
        print(f"Configuration: {config_path}")
        print(f"Result:        {result_path}")
        print(f"Benchmarks:    {benchmark_count}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
