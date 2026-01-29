"""Tests for the example_extractor module."""

import pytest
from pathlib import Path
from src.utils.example_extractor import (
    extract_sample_queries_as_examples,
    merge_examples_into_config_dict,
    validate_examples
)
from src.models import GenieSpaceExampleSQL, GenieSpaceConfig


def test_extract_sample_queries_basic():
    """Test basic extraction of sample queries as examples."""
    # Use the parsed.md file that should exist
    requirements_path = "data/parsed.md"
    
    if not Path(requirements_path).exists():
        pytest.skip(f"Requirements file not found: {requirements_path}")
    
    examples = extract_sample_queries_as_examples(requirements_path)
    
    # Should extract at least some examples
    assert len(examples) > 0, "Should extract at least one example"
    
    # Check structure of first example
    first_example = examples[0]
    assert isinstance(first_example, GenieSpaceExampleSQL)
    assert first_example.question, "Question should not be empty"
    assert first_example.sql_query, "SQL query should not be empty"
    assert len(first_example.sql_query) > 10, "SQL query should have meaningful content"


def test_extract_sample_queries_file_not_found():
    """Test extraction with non-existent file."""
    with pytest.raises(FileNotFoundError):
        extract_sample_queries_as_examples("nonexistent_file.md")


def test_validate_examples_valid():
    """Test validation with valid examples."""
    examples = [
        GenieSpaceExampleSQL(
            question="What are the top selling products?",
            sql_query="SELECT product_name, COUNT(*) as sales FROM products GROUP BY product_name ORDER BY sales DESC LIMIT 10",
            description=None
        ),
        GenieSpaceExampleSQL(
            question="How many customers do we have?",
            sql_query="SELECT COUNT(DISTINCT customer_id) FROM customers",
            description=None
        )
    ]
    
    issues = validate_examples(examples)
    assert len(issues) == 0, "Valid examples should have no issues"


def test_validate_examples_short_question():
    """Test validation catches short questions."""
    examples = [
        GenieSpaceExampleSQL(
            question="Hi",  # Too short
            sql_query="SELECT * FROM table",
            description=None
        )
    ]
    
    issues = validate_examples(examples)
    assert len(issues) > 0, "Should detect short question"
    assert any("short" in issue.lower() for issue in issues)


def test_validate_examples_short_sql():
    """Test validation catches short SQL queries."""
    examples = [
        GenieSpaceExampleSQL(
            question="What is the total revenue?",
            sql_query="SELECT",  # Too short
            description=None
        )
    ]
    
    issues = validate_examples(examples)
    assert len(issues) > 0, "Should detect short SQL query"


def test_validate_examples_missing_sql_keywords():
    """Test validation catches SQL without keywords."""
    examples = [
        GenieSpaceExampleSQL(
            question="What is the total revenue?",
            sql_query="This is not a valid SQL query at all",  # No SQL keywords
            description=None
        )
    ]
    
    issues = validate_examples(examples)
    assert len(issues) > 0, "Should detect missing SQL keywords"
    assert any("keyword" in issue.lower() for issue in issues)


def test_merge_examples_replace():
    """Test merging examples with replace=True."""
    config = {
        "genie_space_config": {
            "space_name": "Test Space",
            "example_sql_queries": [
                {
                    "question": "Old question",
                    "sql_query": "SELECT * FROM old_table",
                    "description": None
                }
            ]
        }
    }
    
    new_examples = [
        GenieSpaceExampleSQL(
            question="New question",
            sql_query="SELECT * FROM new_table",
            description=None
        )
    ]
    
    updated_config = merge_examples_into_config_dict(config, new_examples, replace=True)
    
    examples = updated_config["genie_space_config"]["example_sql_queries"]
    assert len(examples) == 1, "Should have only new examples"
    assert examples[0]["question"] == "New question"


def test_merge_examples_append():
    """Test merging examples with replace=False."""
    config = {
        "genie_space_config": {
            "space_name": "Test Space",
            "example_sql_queries": [
                {
                    "question": "Old question",
                    "sql_query": "SELECT * FROM old_table",
                    "description": None
                }
            ]
        }
    }
    
    new_examples = [
        GenieSpaceExampleSQL(
            question="New question",
            sql_query="SELECT * FROM new_table",
            description=None
        )
    ]
    
    updated_config = merge_examples_into_config_dict(config, new_examples, replace=False)
    
    examples = updated_config["genie_space_config"]["example_sql_queries"]
    assert len(examples) == 2, "Should have both old and new examples"
    assert examples[0]["question"] == "Old question"
    assert examples[1]["question"] == "New question"


def test_merge_examples_deduplicate():
    """Test merging avoids duplicates when appending."""
    config = {
        "genie_space_config": {
            "space_name": "Test Space",
            "example_sql_queries": [
                {
                    "question": "Same question",
                    "sql_query": "SELECT * FROM table1",
                    "description": None
                }
            ]
        }
    }
    
    new_examples = [
        GenieSpaceExampleSQL(
            question="Same question",  # Duplicate
            sql_query="SELECT * FROM table2",  # Different SQL
            description=None
        ),
        GenieSpaceExampleSQL(
            question="Different question",
            sql_query="SELECT * FROM table3",
            description=None
        )
    ]
    
    updated_config = merge_examples_into_config_dict(config, new_examples, replace=False)
    
    examples = updated_config["genie_space_config"]["example_sql_queries"]
    assert len(examples) == 2, "Should avoid duplicate questions"
    
    questions = [ex["question"] for ex in examples]
    assert questions.count("Same question") == 1, "Should have only one instance of duplicate"
    assert "Different question" in questions


def test_merge_examples_direct_config():
    """Test merging with direct config format (no genie_space_config wrapper)."""
    config = {
        "space_name": "Test Space",
        "example_sql_queries": []
    }
    
    new_examples = [
        GenieSpaceExampleSQL(
            question="Test question",
            sql_query="SELECT * FROM test_table",
            description=None
        )
    ]
    
    updated_config = merge_examples_into_config_dict(config, new_examples, replace=True)
    
    assert len(updated_config["example_sql_queries"]) == 1
    assert updated_config["example_sql_queries"][0]["question"] == "Test question"


def test_example_model_validation():
    """Test that GenieSpaceExampleSQL model validates correctly."""
    # Valid example
    valid_example = GenieSpaceExampleSQL(
        question="What is the total revenue?",
        sql_query="SELECT SUM(revenue) FROM sales",
        description="Total revenue calculation"
    )
    assert valid_example.question == "What is the total revenue?"
    assert valid_example.sql_query == "SELECT SUM(revenue) FROM sales"
    assert valid_example.description == "Total revenue calculation"
    
    # Optional description
    example_no_desc = GenieSpaceExampleSQL(
        question="How many orders?",
        sql_query="SELECT COUNT(*) FROM orders"
    )
    assert example_no_desc.description is None


def test_extraction_format_2():
    """Test extraction of Format 2 (Korean style with numbered headers)."""
    # Create a temporary test file with Format 2
    test_content = """
# Test Requirements

### 1. 전체 플레이어 수를 조회하고 싶어
**필요한 테이블:**
- player_info

**예시 쿼리:**
```sql
SELECT COUNT(DISTINCT player_id) as total_players 
FROM player_info;
```

### 2. 월별 매출을 보고 싶어
**예시 쿼리:**
```sql
SELECT 
  DATE_TRUNC('month', sale_date) as month,
  SUM(amount) as total_sales
FROM sales
GROUP BY 1
ORDER BY 1 DESC;
```
"""
    
    test_file = Path("output/test_format2.md")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        examples = extract_sample_queries_as_examples(str(test_file))
        
        assert len(examples) == 2, "Should extract 2 examples"
        assert examples[0].question == "전체 플레이어 수를 조회하고 싶어"
        assert "player_info" in examples[0].sql_query
        assert examples[1].question == "월별 매출을 보고 싶어"
        assert "sales" in examples[1].sql_query
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


def test_extraction_skips_questions_without_sql():
    """Test that extraction skips questions that don't have SQL."""
    test_content = """
# Test Requirements

### 1. Question with SQL
**예시 쿼리:**
```sql
SELECT * FROM table1;
```

### 2. Question without SQL
Just some text here.

### 3. Another question with SQL
**예시 쿼리:**
```sql
SELECT * FROM table2;
```
"""
    
    test_file = Path("output/test_skip_no_sql.md")
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        examples = extract_sample_queries_as_examples(str(test_file))
        
        # Should only extract 2 examples (questions 1 and 3)
        assert len(examples) == 2, "Should only extract questions with SQL"
        assert "table1" in examples[0].sql_query
        assert "table2" in examples[1].sql_query
    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
