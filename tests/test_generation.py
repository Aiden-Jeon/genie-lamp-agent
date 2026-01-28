"""Test script to verify the generation system works."""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path to allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prompt.prompt_builder import PromptBuilder
from src.models import GenieSpaceConfig


def test_prompt_builder():
    """Test that prompt builder can read files and build prompts."""
    print("Testing Prompt Builder...")
    
    builder = PromptBuilder(
        context_doc_path="src/prompt/templates/curate_effective_genie.md",
        output_doc_path="src/prompt/templates/genie_api.md",
        input_data_path="data/demo_requirements.md"
    )
    
    # Test basic prompt
    prompt = builder.build_prompt()
    assert len(prompt) > 1000, "Prompt should be substantial"
    assert "Instruction" in prompt
    assert "Context" in prompt
    assert "Output" in prompt
    assert "Input" in prompt
    
    print("✓ Basic prompt generation works")
    
    # Test prompt with reasoning
    prompt_with_reasoning = builder.build_prompt_with_reasoning()
    assert "reasoning" in prompt_with_reasoning
    assert "confidence_score" in prompt_with_reasoning
    
    print("✓ Prompt with reasoning generation works")
    
    return True


def test_models():
    """Test that Pydantic models validate correctly."""
    print("\nTesting Pydantic Models...")
    
    # Test basic config
    config_data = {
        "space_name": "Test Space",
        "description": "A test space",
        "purpose": "Testing purposes",
        "tables": [
            {
                "catalog_name": "test_catalog",
                "schema_name": "test_schema",
                "table_name": "test_table"
            }
        ],
        "instructions": [
            {
                "content": "Test instruction",
                "priority": 1
            }
        ],
        "example_sql_queries": [
            {
                "question": "What is the total?",
                "sql_query": "SELECT SUM(amount) FROM table"
            }
        ],
        "sql_expressions": [
            {
                "name": "total_revenue",
                "expression": "SUM(amount)",
                "type": "metric"
            }
        ],
        "benchmark_questions": [
            {
                "question": "What is the total revenue?"
            }
        ]
    }
    
    # Validate
    config = GenieSpaceConfig(**config_data)
    assert config.space_name == "Test Space"
    assert len(config.tables) == 1
    assert len(config.instructions) == 1
    
    print("✓ Model validation works")
    
    # Test JSON serialization
    json_str = config.model_dump_json(indent=2)
    assert "test_catalog" in json_str
    
    print("✓ JSON serialization works")
    
    return True


def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting File Structure...")
    
    required_files = [
        "src/__init__.py",
        "src/models.py",
        "src/prompt/__init__.py",
        "src/prompt/prompt_builder.py",
        "src/llm/__init__.py",
        "src/llm/databricks_llm.py",
        "src/api/__init__.py",
        "src/api/genie_space_client.py",
        "src/utils/__init__.py",
        "main.py",
        "requirements.txt",
        "README.md",
        "src/prompt/templates/curate_effective_genie.md",
        "src/prompt/templates/genie_api.md",
        "data/demo_requirements.md",
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        assert path.exists(), f"Missing required file: {file_path}"
        print(f"✓ {file_path}")
    
    return True


def test_output_directory():
    """Test that output directory exists."""
    print("\nTesting Output Directory...")
    
    output_dir = Path("output")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print("✓ Created output directory")
    else:
        print("✓ Output directory exists")
    
    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("Running Tests for Genie Configuration Generator")
    print("=" * 80)
    print()
    
    tests = [
        ("File Structure", test_file_structure),
        ("Output Directory", test_output_directory),
        ("Pydantic Models", test_models),
        ("Prompt Builder", test_prompt_builder),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 80)
    print(f"Tests Complete: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n✓ All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables")
        print("2. Run: genie.py create --requirements data/demo_requirements.md")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
