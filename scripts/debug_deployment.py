#!/usr/bin/env python3
"""Debug deployment configuration to identify transformation issues."""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from genie.utils.config_transformer import transform_to_serialized_space

def debug_config(config_path: str):
    print(f"🔍 Debugging: {config_path}\n")

    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        full_config = json.load(f)

    config = full_config.get("genie_space_config", full_config)

    # Check for problematic fields
    print("CONFIGURATION INSPECTION")
    print("=" * 80)

    has_joins = "joins" in config
    has_join_specs = "join_specifications" in config

    print(f"Has 'joins' field: {has_joins}")
    if has_joins:
        print(f"  Content: {config['joins']}")
        if config['joins'] == []:
            print(f"  ❌ PROBLEM: Empty 'joins' field!")

    print(f"Has 'join_specifications' field: {has_join_specs}")
    if has_join_specs:
        print(f"  Count: {len(config['join_specifications'])}")

    # Transform and inspect
    print(f"\nTRANSFORMATION TEST")
    print("=" * 80)

    try:
        serialized_space_str = transform_to_serialized_space(config)
        serialized_space = json.loads(serialized_space_str)

        join_specs = serialized_space.get("instructions", {}).get("join_specs", [])

        print(f"✓ Transformation successful")
        print(f"Input join_specifications: {len(config.get('join_specifications', []))}")
        print(f"Output join_specs: {len(join_specs)}")

        if len(join_specs) == 0 and len(config.get('join_specifications', [])) > 0:
            print(f"\n❌ CRITICAL: Joins were NOT transformed!")

        # Save for inspection
        debug_dir = project_root / "output" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        output_file = debug_dir / "serialized_space_debug.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serialized_space, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved to: {output_file}")

    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: .venv/bin/python scripts/debug_deployment.py <config_path>")
        sys.exit(1)

    debug_config(sys.argv[1])
