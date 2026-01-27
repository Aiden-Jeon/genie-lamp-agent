"""
Test join specification transformation.

Validates that our config transformer produces the correct join spec format
based on actual Genie space structure analysis.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config_transformer import create_join_spec, transform_to_serialized_space
import json


def test_join_spec_creation():
    """Test creating a join specification."""
    print("\n" + "=" * 80)
    print("TEST: Join Spec Creation")
    print("=" * 80)
    
    join = create_join_spec(
        left_table="catalog.schema.fact_sales",
        right_table="catalog.schema.dim_product",
        left_column="product_id",
        right_column="product_id",
        relationship_type="FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
    )
    
    # Validate structure
    assert "left_table" in join
    assert "left_alias" in join
    assert "right_table" in join
    assert "right_alias" in join
    assert "join_condition" in join
    assert "relationship_type" in join
    
    # Validate values
    assert join["left_table"] == "catalog.schema.fact_sales"
    assert join["left_alias"] == "fact_sales"  # Auto-generated from table name
    assert join["right_table"] == "catalog.schema.dim_product"
    assert join["right_alias"] == "dim_product"
    assert join["join_condition"] == "fact_sales.product_id = dim_product.product_id"
    assert join["relationship_type"] == "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
    
    print("✓ Join spec structure is correct")
    print(json.dumps(join, indent=2))


def test_join_spec_transformation():
    """Test that join specs are transformed correctly to serialized format."""
    print("\n" + "=" * 80)
    print("TEST: Join Spec Transformation")
    print("=" * 80)
    
    config = {
        "space_name": "Test Space",
        "warehouse_id": "test_warehouse",
        "tables": [
            {
                "catalog_name": "catalog",
                "schema_name": "schema",
                "table_name": "fact_sales"
            },
            {
                "catalog_name": "catalog",
                "schema_name": "schema",
                "table_name": "dim_product"
            }
        ],
        "joins": [
            {
                "left_table": "catalog.schema.fact_sales",
                "left_alias": "fact_sales",
                "right_table": "catalog.schema.dim_product",
                "right_alias": "dim_product",
                "join_condition": "fact_sales.product_id = dim_product.product_id",
                "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
            }
        ]
    }
    
    # Transform to serialized format
    serialized = transform_to_serialized_space(config)
    serialized_obj = json.loads(serialized)
    
    # Validate structure
    assert "version" in serialized_obj
    assert serialized_obj["version"] == 1
    assert "data_sources" in serialized_obj
    assert "instructions" in serialized_obj
    assert "join_specs" in serialized_obj["instructions"]
    
    # Validate join spec format
    join_specs = serialized_obj["instructions"]["join_specs"]
    assert len(join_specs) == 1
    
    join_spec = join_specs[0]
    assert "id" in join_spec
    assert "left" in join_spec
    assert "right" in join_spec
    assert "sql" in join_spec
    
    # Validate left/right structure
    assert join_spec["left"]["identifier"] == "catalog.schema.fact_sales"
    assert join_spec["left"]["alias"] == "fact_sales"
    assert join_spec["right"]["identifier"] == "catalog.schema.dim_product"
    assert join_spec["right"]["alias"] == "dim_product"
    
    # Validate SQL array (note: Databricks format includes trailing newline on condition)
    assert len(join_spec["sql"]) == 2
    assert join_spec["sql"][0] == "fact_sales.product_id = dim_product.product_id\n"
    assert join_spec["sql"][1] == "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
    
    print("✓ Join spec transformation is correct")
    print("\nTransformed join spec:")
    print(json.dumps(join_spec, indent=2))


def test_multiple_join_specs():
    """Test transforming multiple join specs."""
    print("\n" + "=" * 80)
    print("TEST: Multiple Join Specs")
    print("=" * 80)
    
    joins = [
        create_join_spec(
            "catalog.schema.fact_orders",
            "catalog.schema.dim_customer",
            "customer_id",
            "customer_id",
            "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        ),
        create_join_spec(
            "catalog.schema.fact_orders",
            "catalog.schema.dim_product",
            "product_id",
            "product_id",
            "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        ),
        create_join_spec(
            "catalog.schema.fact_orders",
            "catalog.schema.dim_date",
            "date_id",
            "date_id",
            "FROM_RELATIONSHIP_TYPE_ONE_TO_ONE"
        ),
    ]
    
    config = {
        "space_name": "Test Space",
        "warehouse_id": "test_warehouse",
        "tables": [],
        "joins": joins
    }
    
    # Transform
    serialized = transform_to_serialized_space(config)
    serialized_obj = json.loads(serialized)
    
    # Validate
    join_specs = serialized_obj["instructions"]["join_specs"]
    assert len(join_specs) == 3
    
    # Check each join spec has required fields
    for join_spec in join_specs:
        assert "id" in join_spec
        assert "left" in join_spec
        assert "right" in join_spec
        assert "sql" in join_spec
        assert len(join_spec["sql"]) == 2
        assert join_spec["sql"][1].startswith("--rt=FROM_RELATIONSHIP_TYPE_")
    
    print(f"✓ All {len(join_specs)} join specs are correctly transformed")
    print("\nTransformed join specs:")
    for i, spec in enumerate(join_specs, 1):
        print(f"\nJoin {i}:")
        print(f"  {spec['left']['alias']} → {spec['right']['alias']}")
        print(f"  Condition: {spec['sql'][0]}")
        print(f"  Type: {spec['sql'][1]}")


def test_invalid_relationship_type():
    """Test that invalid relationship types are rejected."""
    print("\n" + "=" * 80)
    print("TEST: Invalid Relationship Type")
    print("=" * 80)
    
    try:
        join = create_join_spec(
            "catalog.schema.fact_sales",
            "catalog.schema.dim_product",
            "product_id",
            "product_id",
            relationship_type="INVALID_TYPE"  # Invalid type
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly rejected invalid relationship type: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TESTING JOIN SPECIFICATION FUNCTIONALITY")
    print("=" * 80)
    
    try:
        test_join_spec_creation()
        test_join_spec_transformation()
        test_multiple_join_specs()
        test_invalid_relationship_type()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
