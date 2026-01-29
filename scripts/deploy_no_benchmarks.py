#!/usr/bin/env python3
"""Deploy without benchmarks to test basic space."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.pipeline import deploy_space

# Load environment variables
load_dotenv()


def main():
    config_path = "output/genie_space_config_no_benchmarks.json"
    result_path = "output/genie_space_result_no_benchmarks.json"
    
    print("=" * 80)
    print("🚀 Deploying Genie Space (Without Benchmarks)")
    print("=" * 80)
    print()
    
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
        print()
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
