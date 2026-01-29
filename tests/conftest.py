"""Shared pytest fixtures for Genie Lamp Agent tests.

This module provides common test fixtures used across all test domains.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from src.models import (
    GenieSpaceTable,
    GenieSpaceConfig,
    GenieSpaceInstruction,
    GenieSpaceExampleSQL,
    GenieSpaceSQLExpression,
    GenieSpaceBenchmark
)


@pytest.fixture
def sample_tables():
    """Sample tables for testing validation and generation."""
    return [
        GenieSpaceTable(
            catalog_name="demo",
            schema_name="retail",
            table_name="transactions"
        ),
        GenieSpaceTable(
            catalog_name="demo",
            schema_name="retail",
            table_name="customers"
        ),
        GenieSpaceTable(
            catalog_name="demo",
            schema_name="retail",
            table_name="articles"
        )
    ]


@pytest.fixture
def sample_config(sample_tables):
    """Sample Genie space configuration for testing."""
    return GenieSpaceConfig(
        space_name="Test Space",
        description="A test space for validation",
        purpose="Testing purposes",
        tables=sample_tables,
        instructions=[
            GenieSpaceInstruction(
                content="Use demo.retail.transactions for sales data",
                priority=1
            ),
            GenieSpaceInstruction(
                content="Join demo.retail.customers for customer info",
                priority=2
            )
        ],
        example_sql_queries=[
            GenieSpaceExampleSQL(
                question="What is the total revenue?",
                sql_query="SELECT SUM(amount) FROM demo.retail.transactions"
            ),
            GenieSpaceExampleSQL(
                question="How many customers?",
                sql_query="SELECT COUNT(*) FROM demo.retail.customers"
            )
        ],
        sql_expressions=[
            GenieSpaceSQLExpression(
                alias="total_revenue",
                sql="SUM(amount)",
                display_name="Total Revenue"
            )
        ],
        benchmark_questions=[
            GenieSpaceBenchmark(
                question="What is the total revenue?"
            )
        ]
    )


@pytest.fixture
def sample_config_dict(sample_config):
    """Sample configuration as a dictionary (API format)."""
    return {
        "genie_space_config": sample_config.model_dump()
    }


@pytest.fixture
def temp_config_file(sample_config_dict):
    """Create a temporary config file for testing file operations."""
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.json', 
        delete=False, 
        encoding='utf-8'
    ) as f:
        json.dump(sample_config_dict, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_databricks_response():
    """Mock Databricks API response for table validation."""
    def _create_response(table_name, columns=None):
        """Create a mock response for a given table."""
        if columns is None:
            columns = [
                {"name": "id", "type_text": "INT"},
                {"name": "name", "type_text": "STRING"},
                {"name": "amount", "type_text": "DECIMAL"}
            ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": table_name,
            "columns": columns
        }
        return mock_response
    
    return _create_response


@pytest.fixture
def mock_databricks_not_found():
    """Mock Databricks API 404 response."""
    mock_response = Mock()
    mock_response.status_code = 404
    return mock_response


@pytest.fixture
def sample_requirements_content():
    """Sample requirements content for testing parsers."""
    return """# Test Requirements

## FAQ Questions

### 1. What is the total revenue?
**사용 테이블:** `demo.retail.transactions`
**예시 쿼리:**
```sql
SELECT SUM(amount) as total_revenue
FROM demo.retail.transactions
WHERE date >= '2024-01-01';
```

### 2. How many customers do we have?
**사용 테이블:** `demo.retail.customers`
**예시 쿼리:**
```sql
SELECT COUNT(*) as customer_count
FROM demo.retail.customers;
```

## Table Information

### transactions
- Contains all sales transactions
- Key columns: transaction_id, customer_id, amount, date

### customers
- Contains customer information
- Key columns: customer_id, name, email
"""


@pytest.fixture
def sample_requirements_file(sample_requirements_content):
    """Create a temporary requirements file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(sample_requirements_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def output_dir():
    """Ensure output directory exists for tests."""
    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    return output_path


@pytest.fixture
def skip_llm_tests():
    """Skip tests that require LLM calls."""
    import os
    return os.getenv("SKIP_LLM_TESTS", "true").lower() == "true"


@pytest.fixture
def databricks_credentials():
    """Get Databricks credentials from environment."""
    import os
    return {
        "host": os.getenv("DATABRICKS_HOST"),
        "token": os.getenv("DATABRICKS_TOKEN")
    }
