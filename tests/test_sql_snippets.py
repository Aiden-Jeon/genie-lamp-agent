"""Tests for SQL snippets (filters, expressions, measures) format."""

import json
from src.models import GenieSpaceConfig, GenieSpaceSQLSnippets, GenieSpaceSQLFilter, GenieSpaceSQLExpression, GenieSpaceSQLMeasure
from src.utils.config_transformer import transform_to_serialized_space


def test_sql_snippets_model():
    """Test that SQL snippets models work correctly."""
    # Create filter
    filter1 = GenieSpaceSQLFilter(
        sql="orders.status = 'completed'",
        display_name="completed orders",
        synonyms=["finished orders", "done orders"]
    )
    
    # Create expression (dimension)
    expr1 = GenieSpaceSQLExpression(
        alias="order_year",
        sql="YEAR(orders.order_date)",
        display_name="year",
        synonyms=["order year"]
    )
    
    # Create measure (aggregation)
    measure1 = GenieSpaceSQLMeasure(
        alias="total_revenue",
        sql="SUM(orders.order_amount)",
        display_name="total revenue",
        synonyms=["revenue", "total sales"]
    )
    
    # Create SQL snippets container
    snippets = GenieSpaceSQLSnippets(
        filters=[filter1],
        expressions=[expr1],
        measures=[measure1]
    )
    
    # Verify structure
    assert len(snippets.filters) == 1
    assert len(snippets.expressions) == 1
    assert len(snippets.measures) == 1
    
    assert snippets.filters[0].sql == "orders.status = 'completed'"
    assert snippets.expressions[0].alias == "order_year"
    assert snippets.measures[0].alias == "total_revenue"
    
    print("✓ SQL snippets models work correctly")
    return True


def test_config_with_sql_snippets():
    """Test that GenieSpaceConfig works with sql_snippets."""
    config = GenieSpaceConfig(
        space_name="Test Space",
        description="Test space with SQL snippets",
        purpose="Testing",
        tables=[],
        sql_snippets=GenieSpaceSQLSnippets(
            filters=[
                GenieSpaceSQLFilter(
                    sql="price > 100",
                    display_name="expensive items"
                )
            ],
            expressions=[
                GenieSpaceSQLExpression(
                    alias="full_name",
                    sql="CONCAT(first_name, ' ', last_name)",
                    display_name="full name"
                )
            ],
            measures=[
                GenieSpaceSQLMeasure(
                    alias="avg_price",
                    sql="AVG(price)",
                    display_name="average price"
                )
            ]
        )
    )
    
    # Verify config structure
    assert config.sql_snippets is not None
    assert len(config.sql_snippets.filters) == 1
    assert len(config.sql_snippets.expressions) == 1
    assert len(config.sql_snippets.measures) == 1
    
    print("✓ GenieSpaceConfig with sql_snippets works correctly")
    return True


def test_sql_snippets_serialization():
    """Test that sql_snippets serialize correctly to Databricks format."""
    config = {
        "space_name": "Test Space",
        "description": "Test space",
        "purpose": "Testing",
        "tables": [
            {
                "catalog_name": "main",
                "schema_name": "retail",
                "table_name": "orders"
            }
        ],
        "sql_snippets": {
            "filters": [
                {
                    "sql": "orders.status = 'completed'",
                    "display_name": "completed orders",
                    "synonyms": ["finished", "done"]
                }
            ],
            "expressions": [
                {
                    "alias": "order_year",
                    "sql": "YEAR(orders.order_date)",
                    "display_name": "year"
                }
            ],
            "measures": [
                {
                    "alias": "total_revenue",
                    "sql": "SUM(orders.order_amount)",
                    "display_name": "total revenue",
                    "synonyms": ["revenue", "total sales"]
                }
            ]
        }
    }
    
    # Transform to serialized format
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    # Verify structure
    assert "instructions" in result
    assert "sql_snippets" in result["instructions"]
    
    snippets = result["instructions"]["sql_snippets"]
    
    # Verify filters
    assert "filters" in snippets
    assert len(snippets["filters"]) == 1
    filter_item = snippets["filters"][0]
    assert "id" in filter_item
    assert filter_item["sql"] == ["orders.status = 'completed'"]
    assert filter_item["display_name"] == "completed orders"
    assert filter_item["synonyms"] == ["finished", "done"]
    
    # Verify expressions
    assert "expressions" in snippets
    assert len(snippets["expressions"]) == 1
    expr_item = snippets["expressions"][0]
    assert "id" in expr_item
    assert expr_item["alias"] == "order_year"
    assert expr_item["sql"] == ["YEAR(orders.order_date)"]
    assert expr_item["display_name"] == "year"
    
    # Verify measures
    assert "measures" in snippets
    assert len(snippets["measures"]) == 1
    measure_item = snippets["measures"][0]
    assert "id" in measure_item
    assert measure_item["alias"] == "total_revenue"
    assert measure_item["sql"] == ["SUM(orders.order_amount)"]
    assert measure_item["display_name"] == "total revenue"
    assert measure_item["synonyms"] == ["revenue", "total sales"]
    
    print("✓ SQL snippets serialize correctly to Databricks format")
    print(f"  - Filter ID: {filter_item['id']}")
    print(f"  - Expression ID: {expr_item['id']}")
    print(f"  - Measure ID: {measure_item['id']}")
    
    return True


def test_backwards_compatibility():
    """Test that configs without sql_snippets still work."""
    config = {
        "space_name": "Test Space",
        "description": "Test space",
        "purpose": "Testing",
        "tables": []
    }
    
    # Should not raise an error
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    # Should have version and data_sources
    assert result["version"] == 1
    assert "data_sources" in result
    
    # sql_snippets should not be present if not provided
    if "instructions" in result:
        assert "sql_snippets" not in result["instructions"]
    
    print("✓ Backwards compatibility maintained (configs without sql_snippets work)")
    return True


if __name__ == "__main__":
    print("Running SQL snippets tests...\n")
    test_sql_snippets_model()
    test_config_with_sql_snippets()
    test_sql_snippets_serialization()
    test_backwards_compatibility()
    print("\n✅ All SQL snippets tests passed!")
