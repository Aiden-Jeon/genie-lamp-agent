"""Example script showing how to use the Genie configuration generator."""

import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src import PromptBuilder, DatabricksFoundationModelClient
import json

# Load environment variables from .env file
load_dotenv()


def main():
    """Run a simple example."""
    
    print("Example: Generating Genie Space Configuration")
    print("=" * 80)
    print()
    
    # Step 1: Build the prompt
    print("Step 1: Building prompt...")
    builder = PromptBuilder(
        context_doc_path="src/docs/curate_effective_genie.md",
        output_doc_path="src/docs/genie_api.md",
        input_data_path="data/demo_requirements.md"
    )
    
    prompt = builder.build_prompt_with_reasoning()
    print(f"✓ Prompt built ({len(prompt)} characters)")
    print()
    
    # Step 2: Initialize LLM client
    print("Step 2: Initializing LLM client...")
    try:
        client = DatabricksFoundationModelClient(
            model_name="databricks-gpt-5-2"
        )
        print("✓ Client initialized")
        print(f"  Endpoint: {client.endpoint_url}")
        print()
    except ValueError as e:
        print(f"✗ Error: {e}")
        print()
        print("Please set DATABRICKS_HOST and DATABRICKS_TOKEN in your .env file:")
        print("  DATABRICKS_HOST=https://your-workspace.databricks.com")
        print("  DATABRICKS_TOKEN=dapi...")
        return 1
    
    # Step 3: Generate configuration
    print("Step 3: Calling LLM to generate configuration...")
    try:
        response = client.generate_genie_config(
            prompt=prompt,
            max_tokens=16000,  # Increased for reasoning models (GPT-5.2 uses reasoning tokens)
            temperature=0.1,
            include_reasoning=True
        )
        print("✓ Configuration generated!")
        print()
        
        # Step 4: Display results
        print("Step 4: Results")
        print("-" * 80)
        print()
        
        if response.reasoning:
            print("Reasoning:")
            print(response.reasoning[:500] + "..." if len(response.reasoning) > 500 else response.reasoning)
            print()
        
        if response.confidence_score:
            print(f"Confidence: {response.confidence_score:.1%}")
            print()
        
        config = response.genie_space_config
        print("Configuration Summary:")
        print(f"  Space Name: {config.space_name}")
        print(f"  Tables: {len(config.tables)}")
        print(f"  Instructions: {len(config.instructions)}")
        print(f"  Example Queries: {len(config.example_sql_queries)}")
        print(f"  SQL Expressions: {len(config.sql_expressions)}")
        print(f"  Benchmarks: {len(config.benchmark_questions)}")
        print()
        
        # Save to file
        output_file = "output/genie_space_config_example.json"
        os.makedirs("output", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to: {output_file}")
        print()
        
        print("=" * 80)
        print("Example completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
