#!/usr/bin/env python3
"""Remove null instruction fields from SQL snippets."""
import json
import sys

# Read the config
with open('output/genie_space_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Remove null instruction fields from sql_snippets
if 'genie_space_config' in config and 'sql_snippets' in config['genie_space_config']:
    snippets = config['genie_space_config']['sql_snippets']
    
    # Fix expressions
    if 'expressions' in snippets:
        for expr in snippets['expressions']:
            if 'instruction' in expr and expr['instruction'] is None:
                del expr['instruction']
        print(f"✓ Fixed {len(snippets['expressions'])} expressions")
    
    # Fix measures
    if 'measures' in snippets:
        for measure in snippets['measures']:
            if 'instruction' in measure and measure['instruction'] is None:
                del measure['instruction']
        print(f"✓ Fixed {len(snippets['measures'])} measures")

# Write back
with open('output/genie_space_config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✓ Configuration updated successfully!")
