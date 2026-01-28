"""
Test enhanced config generation with improved SQL quality and join specifications.

This test verifies Priority 1 improvements:
1. Join specifications are included in generated configs
2. SQL quality guidelines are reflected in examples
3. Instructions follow quality guidelines
"""

import pytest
import json
from src.models import (
    GenieSpaceConfig,
    GenieSpaceJoinSpec,
    GenieSpaceInstruction,
    GenieSpaceExampleSQL,
)


def test_join_spec_model():
    """Test that GenieSpaceJoinSpec model is properly defined."""
    join_spec = GenieSpaceJoinSpec(
        left_table="main.schema.table1",
        right_table="main.schema.table2",
        join_type="INNER",
        join_condition="table1.id = table2.foreign_id",
        description="Test join relationship"
    )

    assert join_spec.left_table == "main.schema.table1"
    assert join_spec.right_table == "main.schema.table2"
    assert join_spec.join_type == "INNER"
    assert join_spec.join_condition == "table1.id = table2.foreign_id"
    assert join_spec.description == "Test join relationship"


def test_config_with_join_specifications():
    """Test that GenieSpaceConfig accepts join_specifications."""
    config = GenieSpaceConfig(
        space_name="Test Space",
        description="Test description",
        purpose="Test purpose",
        tables=[],
        join_specifications=[
            GenieSpaceJoinSpec(
                left_table="catalog.schema.transactions",
                right_table="catalog.schema.customers",
                join_type="INNER",
                join_condition="transactions.customer_id = customers.customer_id",
                description="Each transaction belongs to one customer"
            )
        ]
    )

    assert len(config.join_specifications) == 1
    assert config.join_specifications[0].join_type == "INNER"


def test_join_spec_serialization():
    """Test that join specifications serialize correctly to JSON."""
    config = GenieSpaceConfig(
        space_name="Test Space",
        description="Test description",
        purpose="Test purpose",
        tables=[],
        join_specifications=[
            GenieSpaceJoinSpec(
                left_table="catalog.schema.fact_sales",
                right_table="catalog.schema.dim_product",
                join_type="INNER",
                join_condition="fact_sales.product_id = dim_product.product_id",
                description="Sales fact table joins to product dimension"
            ),
            GenieSpaceJoinSpec(
                left_table="catalog.schema.fact_sales",
                right_table="catalog.schema.dim_customer",
                join_type="LEFT",
                join_condition="fact_sales.customer_id = dim_customer.customer_id",
                description="Optional customer information for sales"
            )
        ]
    )

    # Serialize to JSON
    config_dict = config.model_dump()
    assert "join_specifications" in config_dict
    assert len(config_dict["join_specifications"]) == 2

    # Verify first join spec
    join1 = config_dict["join_specifications"][0]
    assert join1["left_table"] == "catalog.schema.fact_sales"
    assert join1["right_table"] == "catalog.schema.dim_product"
    assert join1["join_type"] == "INNER"
    assert "product_id" in join1["join_condition"]

    # Verify second join spec
    join2 = config_dict["join_specifications"][1]
    assert join2["join_type"] == "LEFT"
    assert "customer_id" in join2["join_condition"]


def test_instruction_priority():
    """Test that instruction priority field works correctly."""
    instruction1 = GenieSpaceInstruction(
        content="Critical: Always filter status != 'cancelled'",
        priority=1
    )

    instruction2 = GenieSpaceInstruction(
        content="Default to last 30 days when time range not specified",
        priority=2
    )

    instruction3 = GenieSpaceInstruction(
        content="Format monetary values with 2 decimals",
        priority=3
    )

    assert instruction1.priority == 1
    assert instruction2.priority == 2
    assert instruction3.priority == 3


def test_sql_example_quality_patterns():
    """Test that example SQL follows quality patterns."""
    # High-quality SQL example
    example = GenieSpaceExampleSQL(
        question="What were the top 10 customers by revenue last month?",
        sql_query="""
SELECT
  c.customer_id,
  c.customer_name,
  COUNT(DISTINCT t.transaction_id) as transaction_count,
  CAST(SUM(t.amount) AS DECIMAL(38,2)) as total_revenue
FROM main.retail.transactions t
INNER JOIN main.retail.customers c
  ON t.customer_id = c.customer_id
WHERE t.event_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND t.status != 'cancelled'
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC
LIMIT 10;
        """.strip(),
        description="Demonstrates explicit JOIN, correct aggregation, and date filtering"
    )

    # Verify SQL quality patterns are present
    sql = example.sql_query

    # Check for explicit JOIN
    assert "INNER JOIN" in sql or "LEFT JOIN" in sql

    # Check for ON clause
    assert " ON " in sql

    # Check for fully qualified table names (catalog.schema.table)
    assert "main.retail" in sql

    # Check for explicit column selection (not SELECT *)
    assert "SELECT\n  c.customer_id" in sql

    # Check for GROUP BY
    assert "GROUP BY" in sql

    # Check for proper decimal casting
    assert "CAST(" in sql and "DECIMAL" in sql

    # Check for ORDER BY
    assert "ORDER BY" in sql

    # Check for LIMIT
    assert "LIMIT" in sql


def test_markdown_formatted_instructions():
    """Test that instructions use markdown formatting."""
    instruction = GenieSpaceInstruction(
        content="""## Date Handling Rules

- Always use `event_date` column for date filters
- Default to **last 30 days** when time range not specified
- Use `CURRENT_DATE()` for "today"

## Clarification Questions

When users ask about "sales" without specifying product, ask:
> "Which product category would you like to analyze?"
        """.strip(),
        priority=1
    )

    content = instruction.content

    # Check for markdown headers
    assert "##" in content

    # Check for bullet lists
    assert "- " in content or "* " in content

    # Check for bold text
    assert "**" in content

    # Check for inline code
    assert "`" in content

    # Check for blockquote
    assert ">" in content


def test_config_transformer_handles_join_specifications():
    """Test that config_transformer can handle join_specifications."""
    from src.utils.config_transformer import _convert_join_specifications_to_joins

    join_specs = [
        {
            "left_table": "catalog.schema.transactions",
            "right_table": "catalog.schema.customers",
            "join_type": "INNER",
            "join_condition": "transactions.customer_id = customers.customer_id",
            "description": "Transaction to customer relationship"
        },
        {
            "left_table": "catalog.schema.transactions",
            "right_table": "catalog.schema.products",
            "join_type": "LEFT",
            "join_condition": "transactions.product_id = products.product_id",
            "description": "Optional product details"
        }
    ]

    joins = _convert_join_specifications_to_joins(join_specs)

    assert len(joins) == 2

    # Check first join
    join1 = joins[0]
    assert join1["left_table"] == "catalog.schema.transactions"
    assert join1["right_table"] == "catalog.schema.customers"
    assert join1["left_alias"] == "transactions"
    assert join1["right_alias"] == "customers"
    assert join1["join_condition"] == "transactions.customer_id = customers.customer_id"
    assert join1["relationship_type"] == "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
    assert join1["comment"] == "Transaction to customer relationship"

    # Check second join
    join2 = joins[1]
    assert join2["left_table"] == "catalog.schema.transactions"
    assert join2["right_table"] == "catalog.schema.products"
    assert join2["relationship_type"] == "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
    assert join2["comment"] == "Optional product details"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
