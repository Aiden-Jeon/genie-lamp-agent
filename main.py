"""Main script to generate Genie space configuration using Databricks LLM."""

import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from src.prompt.prompt_builder import PromptBuilder
from src.llm.databricks_llm import DatabricksLLMClient, DatabricksFoundationModelClient

# Load environment variables from .env file
load_dotenv()


def main():
    """Main entry point for generating Genie space configuration."""
    parser = argparse.ArgumentParser(
        description="Generate Genie space configuration using Databricks LLM"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Databricks serving endpoint name (e.g., 'my-llm-endpoint')",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Foundation model name (used if --endpoint not provided)",
    )
    parser.add_argument(
        "--context-doc",
        type=str,
        default="src/prompt/templates/curate_effective_genie.md",
        help="Path to context document (best practices)",
    )
    parser.add_argument(
        "--output-doc",
        type=str,
        default="src/prompt/templates/genie_api.md",
        help="Path to output format document (API docs)",
    )
    parser.add_argument(
        "--input-data",
        type=str,
        default="data/demo_requirements.md",
        help="Path to input requirements document",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/genie_space_config.json",
        help="Path to save the generated configuration",
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=None,
        help="Root directory of the workspace (defaults to current directory)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=16000,
        help="Maximum tokens to generate (reasoning models like GPT-5.2 need higher limits)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (0.0 to 1.0)",
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Don't include reasoning in the output",
    )
    parser.add_argument(
        "--databricks-host",
        type=str,
        default=None,
        help="Databricks host URL (defaults to DATABRICKS_HOST env var)",
    )
    parser.add_argument(
        "--databricks-token",
        type=str,
        default=None,
        help="Databricks token (defaults to DATABRICKS_TOKEN env var)",
    )
    
    args = parser.parse_args()
    
    # Set workspace root
    workspace_root = args.workspace_root or os.getcwd()
    
    print("=" * 80)
    print("Genie Space Configuration Generator")
    print("=" * 80)
    print()
    
    # Build the prompt
    print("Building prompt...")
    prompt_builder = PromptBuilder(
        context_doc_path=args.context_doc,
        output_doc_path=args.output_doc,
        input_data_path=args.input_data,
        workspace_root=workspace_root,
    )
    
    if args.no_reasoning:
        prompt = prompt_builder.build_prompt()
    else:
        prompt = prompt_builder.build_prompt_with_reasoning()
    
    print(f"Prompt length: {len(prompt)} characters")
    print()
    
    # Initialize LLM client
    print("Initializing LLM client...")
    if args.endpoint:
        print(f"Using serving endpoint: {args.endpoint}")
        llm_client = DatabricksLLMClient(
            endpoint_name=args.endpoint,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
        )
    else:
        print(f"Using foundation model: {args.model}")
        llm_client = DatabricksFoundationModelClient(
            model_name=args.model,
            databricks_host=args.databricks_host,
            databricks_token=args.databricks_token,
        )
    print()
    
    # Generate configuration
    print("Calling LLM to generate configuration...")
    print(f"  Max tokens: {args.max_tokens}")
    print(f"  Temperature: {args.temperature}")
    print()
    
    try:
        response = llm_client.generate_genie_config(
            prompt=prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            include_reasoning=not args.no_reasoning,
        )
        
        print("✓ Configuration generated successfully!")
        print()
        
        if response.reasoning:
            print("Reasoning:")
            print("-" * 80)
            print(response.reasoning)
            print()
        
        if response.confidence_score:
            print(f"Confidence Score: {response.confidence_score:.2%}")
            print()
        
        # Save the configuration
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuration saved to: {output_path}")
        print()
        
        # Print summary
        config = response.genie_space_config
        print("Configuration Summary:")
        print("-" * 80)
        print(f"Space Name: {config.space_name}")
        print(f"Description: {config.description}")
        print(f"Tables: {len(config.tables)}")
        print(f"Instructions: {len(config.instructions)}")
        print(f"Example SQL Queries: {len(config.example_sql_queries)}")
        print(f"SQL Expressions: {len(config.sql_expressions)}")
        print(f"Benchmark Questions: {len(config.benchmark_questions)}")
        print()
        
        print("=" * 80)
        print("Done!")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ Error generating configuration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
