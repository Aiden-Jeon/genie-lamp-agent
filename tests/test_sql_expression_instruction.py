"""
Test SQL expression instruction field support.

Verifies that SQL expressions (measures and expressions) can have instruction fields
and that they are correctly transformed to the serialized_space format.
"""

import json
from src.utils.config_transformer import transform_to_serialized_space


def test_measure_instruction_field():
    """Test that measure instruction field is correctly transformed."""
    config = {
        "tables": [
            {
                "catalog_name": "sandbox",
                "schema_name": "agent_poc",
                "table_name": "test_table"
            }
        ],
        "sql_snippets": {
            "measures": [
                {
                    "alias": "total_revenue",
                    "sql": "SUM(orders.amount)",
                    "display_name": "Total Revenue",
                    "synonyms": ["revenue", "총 매출"],
                    "instruction": "Use this measure to calculate total revenue across all orders"
                }
            ]
        }
    }
    
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    # Verify instruction is present in the serialized format
    assert "instructions" in result
    assert "sql_snippets" in result["instructions"]
    assert "measures" in result["instructions"]["sql_snippets"]
    
    measures = result["instructions"]["sql_snippets"]["measures"]
    assert len(measures) == 1
    
    measure = measures[0]
    assert measure["alias"] == "total_revenue"
    assert measure["display_name"] == "Total Revenue"
    assert "instruction" in measure
    assert isinstance(measure["instruction"], list)
    assert measure["instruction"][0] == "Use this measure to calculate total revenue across all orders"


def test_expression_instruction_field():
    """Test that expression instruction field is correctly transformed."""
    config = {
        "tables": [
            {
                "catalog_name": "sandbox",
                "schema_name": "agent_poc",
                "table_name": "test_table"
            }
        ],
        "sql_snippets": {
            "expressions": [
                {
                    "alias": "full_name",
                    "sql": "CONCAT(first_name, ' ', last_name)",
                    "display_name": "Full Name",
                    "synonyms": ["name", "전체 이름"],
                    "instruction": "Use this to get the full name of a person"
                }
            ]
        }
    }
    
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    # Verify instruction is present in the serialized format
    assert "instructions" in result
    assert "sql_snippets" in result["instructions"]
    assert "expressions" in result["instructions"]["sql_snippets"]
    
    expressions = result["instructions"]["sql_snippets"]["expressions"]
    assert len(expressions) == 1
    
    expression = expressions[0]
    assert expression["alias"] == "full_name"
    assert expression["display_name"] == "Full Name"
    assert "instruction" in expression
    assert isinstance(expression["instruction"], list)
    assert expression["instruction"][0] == "Use this to get the full name of a person"


def test_multiple_measures_with_mixed_instructions():
    """Test multiple measures where some have instructions and some don't."""
    config = {
        "tables": [
            {
                "catalog_name": "sandbox",
                "schema_name": "agent_poc",
                "table_name": "test_table"
            }
        ],
        "sql_snippets": {
            "measures": [
                {
                    "alias": "total_sales",
                    "sql": "SUM(sales.amount)",
                    "display_name": "Total Sales",
                    "instruction": "Use for calculating total sales amount"
                },
                {
                    "alias": "avg_price",
                    "sql": "AVG(products.price)",
                    "display_name": "Average Price"
                    # No instruction field
                }
            ]
        }
    }
    
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    measures = result["instructions"]["sql_snippets"]["measures"]
    assert len(measures) == 2
    
    # Find measures by alias (they're sorted by ID, not alias)
    sales_measure = next(m for m in measures if m["alias"] == "total_sales")
    price_measure = next(m for m in measures if m["alias"] == "avg_price")
    
    # First measure should have instruction
    assert "instruction" in sales_measure
    assert sales_measure["instruction"][0] == "Use for calculating total sales amount"
    
    # Second measure should NOT have instruction field
    assert "instruction" not in price_measure


def test_instruction_as_list():
    """Test that instruction field can be provided as a list."""
    config = {
        "tables": [
            {
                "catalog_name": "sandbox",
                "schema_name": "agent_poc",
                "table_name": "test_table"
            }
        ],
        "sql_snippets": {
            "measures": [
                {
                    "alias": "revenue",
                    "sql": "SUM(amount)",
                    "display_name": "Revenue",
                    "instruction": ["Line 1 instruction", "Line 2 instruction"]
                }
            ]
        }
    }
    
    serialized = transform_to_serialized_space(config)
    result = json.loads(serialized)
    
    measure = result["instructions"]["sql_snippets"]["measures"][0]
    assert "instruction" in measure
    assert isinstance(measure["instruction"], list)
    assert len(measure["instruction"]) == 2
    assert measure["instruction"][0] == "Line 1 instruction"
    assert measure["instruction"][1] == "Line 2 instruction"
