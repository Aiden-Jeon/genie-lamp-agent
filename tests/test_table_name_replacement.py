"""
Test suite for table name replacement functionality.

Tests the ability to replace catalog, schema, and table names individually
during the validation step.
"""

import json
import tempfile
from pathlib import Path
import pytest

from genie import update_config_catalog_schema_table, update_config_catalog_schema


@pytest.fixture
def sample_config():
    """Create a sample Genie configuration for testing."""
    return {
        "genie_space_config": {
            "space_name": "Test Space",
            "tables": [
                {
                    "catalog_name": "old_catalog",
                    "schema_name": "old_schema",
                    "table_name": "customers",
                    "description": "Customer data"
                },
                {
                    "catalog_name": "old_catalog",
                    "schema_name": "old_schema",
                    "table_name": "orders",
                    "description": "Order data"
                },
                {
                    "catalog_name": "other_catalog",
                    "schema_name": "other_schema",
                    "table_name": "products",
                    "description": "Product data"
                }
            ],
            "sql_snippets": {
                "measures": [
                    {
                        "alias": "total_amount",
                        "sql": "SUM(old_catalog.old_schema.orders.amount)",
                        "display_name": "total amount"
                    }
                ]
            },
            "example_sql_queries": [
                {
                    "question": "What are the total orders?",
                    "sql_query": "SELECT COUNT(*) FROM old_catalog.old_schema.orders"
                },
                {
                    "question": "Customer orders",
                    "sql_query": "SELECT c.name, o.total FROM old_catalog.old_schema.customers c JOIN old_catalog.old_schema.orders o ON c.id = o.customer_id"
                }
            ],
            "benchmark_questions": [
                {
                    "question": "How many customers?",
                    "expected_sql": "SELECT COUNT(*) FROM old_catalog.old_schema.customers",
                    "table": "`old_catalog.old_schema.customers`"
                }
            ],
            "instructions": [
                {
                    "content": "Use old_catalog.old_schema.customers for customer queries"
                }
            ],
            "joins": [
                {
                    "left_table": "old_catalog.old_schema.customers",
                    "left_alias": "customers",
                    "right_table": "old_catalog.old_schema.orders",
                    "right_alias": "orders",
                    "join_condition": "customers.id = orders.customer_id",
                    "relationship_type": "FROM_RELATIONSHIP_TYPE_ONE_TO_MANY"
                }
            ],
            "join_specifications": [
                {
                    "left_table": "old_catalog.old_schema.orders",
                    "right_table": "other_catalog.other_schema.products",
                    "join_type": "INNER",
                    "join_condition": "orders.product_id = products.id",
                    "description": "Link orders to products"
                }
            ]
        }
    }


def test_update_individual_table_name(sample_config):
    """Test updating an individual table's catalog, schema, and name."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f, indent=2)
        config_path = f.name

    try:
        # Update the customers table
        counts = update_config_catalog_schema_table(
            config_path,
            old_catalog="old_catalog",
            old_schema="old_schema",
            old_table="customers",
            new_catalog="new_catalog",
            new_schema="new_schema",
            new_table="users"
        )

        # Verify counts
        assert counts['tables'] == 1
        assert counts['sql_expressions'] == 0  # customers not in expressions
        assert counts['example_queries'] == 1  # One query with customers
        assert counts['benchmark_questions'] == 1
        assert counts['instructions'] == 1
        assert counts['joins'] == 1  # customers is in joins

        # Load and verify the updated config
        with open(config_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        genie_config = updated_config["genie_space_config"]

        # Check table definition
        customers_table = next(
            (t for t in genie_config["tables"] if t["table_name"] == "users"),
            None
        )
        assert customers_table is not None
        assert customers_table["catalog_name"] == "new_catalog"
        assert customers_table["schema_name"] == "new_schema"
        assert customers_table["table_name"] == "users"

        # Check orders table is unchanged
        orders_table = next(
            (t for t in genie_config["tables"] if t["table_name"] == "orders"),
            None
        )
        assert orders_table is not None
        assert orders_table["catalog_name"] == "old_catalog"
        assert orders_table["schema_name"] == "old_schema"

        # Check SQL snippet is unchanged (doesn't reference customers)
        assert "old_catalog.old_schema.orders" in genie_config["sql_snippets"]["measures"][0]["sql"]

        # Check example query is updated
        query_with_customers = next(
            (q for q in genie_config["example_sql_queries"] if "Customer" in q["question"]),
            None
        )
        assert query_with_customers is not None
        assert "new_catalog.new_schema.users" in query_with_customers["sql_query"]
        assert "old_catalog.old_schema.customers" not in query_with_customers["sql_query"]

        # Check benchmark is updated
        benchmark = genie_config["benchmark_questions"][0]
        assert "new_catalog.new_schema.users" in benchmark["expected_sql"]
        assert "`new_catalog.new_schema.users`" in benchmark["table"]

        # Check instruction is updated
        instruction = genie_config["instructions"][0]
        assert "new_catalog.new_schema.users" in instruction["content"]

        # Check join is updated
        join = genie_config["joins"][0]
        assert join["left_table"] == "new_catalog.new_schema.users"
        assert join["left_alias"] == "users"
        assert join["right_table"] == "old_catalog.old_schema.orders"
        assert "users.id" in join["join_condition"]

    finally:
        # Clean up
        Path(config_path).unlink()


def test_update_catalog_schema_bulk(sample_config):
    """Test bulk update of catalog and schema for all tables."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f, indent=2)
        config_path = f.name

    try:
        # Update all tables in old_catalog.old_schema
        counts = update_config_catalog_schema(
            config_path,
            old_catalog="old_catalog",
            old_schema="old_schema",
            new_catalog="new_catalog",
            new_schema="new_schema"
        )

        # Verify counts
        assert counts['tables'] == 2  # customers and orders
        assert counts['sql_expressions'] == 1  # orders expression
        assert counts['example_queries'] == 2  # Both queries
        assert counts['benchmark_questions'] == 1
        assert counts['instructions'] == 1
        assert counts['joins'] == 1

        # Load and verify the updated config
        with open(config_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        genie_config = updated_config["genie_space_config"]

        # Check both tables are updated
        for table in genie_config["tables"]:
            if table["table_name"] in ["customers", "orders"]:
                assert table["catalog_name"] == "new_catalog"
                assert table["schema_name"] == "new_schema"
            elif table["table_name"] == "products":
                assert table["catalog_name"] == "other_catalog"
                assert table["schema_name"] == "other_schema"

        # Check SQL snippet is updated
        assert "new_catalog.new_schema.orders" in genie_config["sql_snippets"]["measures"][0]["sql"]

        # Check all example queries are updated
        for query in genie_config["example_sql_queries"]:
            assert "old_catalog.old_schema" not in query["sql_query"]
            if "customers" in query["sql_query"] or "orders" in query["sql_query"]:
                assert "new_catalog.new_schema" in query["sql_query"]

    finally:
        # Clean up
        Path(config_path).unlink()


def test_update_preserves_other_tables(sample_config):
    """Test that updating one table doesn't affect other tables."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f, indent=2)
        config_path = f.name

    try:
        # Update only the products table
        counts = update_config_catalog_schema_table(
            config_path,
            old_catalog="other_catalog",
            old_schema="other_schema",
            old_table="products",
            new_catalog="prod_catalog",
            new_schema="prod_schema",
            new_table="items"
        )

        # Load and verify
        with open(config_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        genie_config = updated_config["genie_space_config"]

        # Check products is updated
        items_table = next(
            (t for t in genie_config["tables"] if t["table_name"] == "items"),
            None
        )
        assert items_table is not None
        assert items_table["catalog_name"] == "prod_catalog"
        assert items_table["schema_name"] == "prod_schema"

        # Check other tables are unchanged
        customers_table = next(
            (t for t in genie_config["tables"] if t["table_name"] == "customers"),
            None
        )
        assert customers_table is not None
        assert customers_table["catalog_name"] == "old_catalog"
        assert customers_table["schema_name"] == "old_schema"

        orders_table = next(
            (t for t in genie_config["tables"] if t["table_name"] == "orders"),
            None
        )
        assert orders_table is not None
        assert orders_table["catalog_name"] == "old_catalog"
        assert orders_table["schema_name"] == "old_schema"

    finally:
        # Clean up
        Path(config_path).unlink()


def test_update_join_alias_replacement(sample_config):
    """Test that join aliases are updated when table names change."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f, indent=2)
        config_path = f.name

    try:
        # Update the orders table name
        counts = update_config_catalog_schema_table(
            config_path,
            old_catalog="old_catalog",
            old_schema="old_schema",
            old_table="orders",
            new_catalog="new_catalog",
            new_schema="new_schema",
            new_table="transactions"
        )

        # Load and verify
        with open(config_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        genie_config = updated_config["genie_space_config"]

        # Check join is updated with new alias
        join = genie_config["joins"][0]
        assert join["right_table"] == "new_catalog.new_schema.transactions"
        assert join["right_alias"] == "transactions"
        # Join condition should use new alias
        assert "transactions.customer_id" in join["join_condition"]
        assert "orders.customer_id" not in join["join_condition"]

    finally:
        # Clean up
        Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
