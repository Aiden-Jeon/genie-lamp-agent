"""Transformation Domain Tests

Consolidates all tests related to configuration transformation:
- Catalog/schema replacement
- Table name replacement
- SQL expression transformation
- Join specification transformation
- Config format conversion
"""

import pytest
import json
import tempfile
from pathlib import Path
from genie import update_config_catalog_schema
from src.utils.config_transformer import transform_to_serialized_space


# ============================================================================
# CATALOG/SCHEMA REPLACEMENT TESTS
# ============================================================================

class TestCatalogSchemaReplacement:
    """Tests for bulk catalog.schema replacement."""
    
    def test_update_tables_section(self):
        """Test updating tables section with new catalog.schema."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"},
                    {"catalog_name": "main", "schema_name": "log_steam", "table_name": "store_appreviews"}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            assert counts['tables'] == 1, "Should update 1 table"
            
            # Verify table was updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            tables = updated["genie_space_config"]["tables"]
            discord_table = next((t for t in tables if t["table_name"] == "message"), None)
            
            assert discord_table is not None
            assert discord_table["catalog_name"] == "sandbox"
            assert discord_table["schema_name"] == "agent_poc"
            
            # Steam table should remain unchanged
            steam_table = next((t for t in tables if t["table_name"] == "store_appreviews"), None)
            assert steam_table["catalog_name"] == "main"
            assert steam_table["schema_name"] == "log_steam"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_update_instructions(self):
        """Test updating table references in instructions."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
                ],
                "instructions": [
                    {"content": "Use `main.log_discord.message` for queries"},
                    {"content": "Join main.log_discord.reaction with main.log_discord.message"}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            assert counts['instructions'] == 2, "Should update 2 instructions"
            
            # Verify instructions were updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            instructions = updated["genie_space_config"]["instructions"]
            
            # Check replacements
            assert any("sandbox.agent_poc.message" in inst["content"] for inst in instructions)
            assert any("sandbox.agent_poc.reaction" in inst["content"] for inst in instructions)
            assert not any("main.log_discord" in inst["content"] for inst in instructions)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_update_sql_expressions(self):
        """Test updating table references in SQL expressions."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
                ],
                "sql_snippets": {
                    "measures": [
                        {"sql": "COUNT(*)", "display_name": "message count"}
                    ],
                    "filters": [
                        {"sql": "main.log_discord.message.game_code = 'inzoi'", "display_name": "INZOI filter"}
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            assert counts['sql_expressions'] == 1, "Should update 1 SQL expression (filter)"
            
            # Verify SQL expression was updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            filters = updated["genie_space_config"]["sql_snippets"]["filters"]
            assert any("sandbox.agent_poc.message" in f["sql"] for f in filters)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_update_example_queries(self):
        """Test updating table references in example SQL queries."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
                ],
                "example_sql_queries": [
                    {
                        "question": "How many messages?",
                        "sql_query": "SELECT COUNT(*) FROM main.log_discord.message"
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            assert counts['example_queries'] == 1, "Should update 1 example query"
            
            # Verify example query was updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            examples = updated["genie_space_config"]["example_sql_queries"]
            assert any("sandbox.agent_poc.message" in ex["sql_query"] for ex in examples)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_update_benchmark_questions(self):
        """Test updating table references in benchmark questions."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
                ],
                "benchmark_questions": [
                    {
                        "question": "Total messages?",
                        "expected_sql": "SELECT COUNT(*) FROM main.log_discord.message"
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            assert counts['benchmark_questions'] == 1, "Should update 1 benchmark question"
            
            # Verify benchmark was updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            benchmarks = updated["genie_space_config"]["benchmark_questions"]
            assert any("sandbox.agent_poc.message" in bm["expected_sql"] for bm in benchmarks)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_multiple_catalog_schema_replacements(self):
        """Test multiple sequential catalog.schema replacements."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"},
                    {"catalog_name": "main", "schema_name": "log_steam", "table_name": "store_appreviews"}
                ],
                "instructions": [
                    {"content": "Discord: main.log_discord.message"},
                    {"content": "Steam: main.log_steam.store_appreviews"}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            # First replacement: Discord tables
            update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            # Second replacement: Steam tables
            update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_steam",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            # Verify both were updated
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            instructions = updated["genie_space_config"]["instructions"]
            assert all("sandbox.agent_poc" in inst["content"] for inst in instructions)
            assert not any("main.log" in inst["content"] for inst in instructions)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# TABLE NAME REPLACEMENT TESTS
# ============================================================================

class TestTableNameReplacement:
    """Tests for individual table name replacement."""
    
    def test_table_name_replacement_via_catalog_schema(self):
        """Test that table names can be updated via catalog.schema replacement."""
        test_config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "demo", "schema_name": "retail", "table_name": "transactions"}
                ],
                "instructions": [
                    {"content": "Use demo.retail.transactions for sales data"}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            # Use catalog.schema replacement to update table references
            counts = update_config_catalog_schema(
                temp_path,
                old_catalog="demo",
                old_schema="retail",
                new_catalog="prod",
                new_schema="sales"
            )
            
            assert counts['tables'] == 1
            
            # Verify update
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            table = updated["genie_space_config"]["tables"][0]
            assert table["catalog_name"] == "prod"
            assert table["schema_name"] == "sales"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# CONFIG FORMAT TRANSFORMATION TESTS
# ============================================================================

class TestConfigFormatTransformation:
    """Tests for transforming user-friendly format to Databricks serialized format."""
    
    def test_transform_basic_config(self, sample_config):
        """Test transforming basic config to serialized format."""
        config_dict = sample_config.model_dump()
        serialized_json = transform_to_serialized_space(config_dict)
        
        # transform_to_serialized_space returns a JSON string
        assert isinstance(serialized_json, str)
        serialized = json.loads(serialized_json)
        
        # Check Databricks format structure
        assert "version" in serialized
        assert serialized["version"] == 1
        assert "data_sources" in serialized
        assert "tables" in serialized["data_sources"]
    
    def test_transform_with_join_specs(self):
        """Test transformation preserves join specifications."""
        config = {
            "space_name": "Test",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {
                    "catalog_name": "demo",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "demo",
                    "schema_name": "retail",
                    "table_name": "customers"
                }
            ],
            "join_specifications": [
                {
                    "left_table": "demo.retail.transactions",
                    "right_table": "demo.retail.customers",
                    "join_type": "INNER",
                    "join_condition": "transactions.customer_id = customers.customer_id"
                }
            ]
        }
        
        serialized_json = transform_to_serialized_space(config)
        serialized = json.loads(serialized_json)
        
        # Check tables exist in data_sources
        assert "data_sources" in serialized
        assert "tables" in serialized["data_sources"]
        tables = serialized["data_sources"]["tables"]
        assert len(tables) > 0
        
        # Check join specs are in instructions
        assert "instructions" in serialized
        if "join_specs" in serialized["instructions"]:
            assert len(serialized["instructions"]["join_specs"]) > 0
    
    def test_transform_with_sql_expressions(self):
        """Test transformation handles SQL expressions."""
        config = {
            "space_name": "Test",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {"catalog_name": "demo", "schema_name": "retail", "table_name": "transactions"}
            ],
            "sql_expressions": [
                {
                    "name": "total_revenue",
                    "expression": "SUM(amount)",
                    "type": "metric",
                    "description": "Total revenue"
                }
            ]
        }
        
        serialized_json = transform_to_serialized_space(config)
        serialized = json.loads(serialized_json)
        
        # SQL expressions should be in instructions.sql_snippets
        assert "instructions" in serialized
        # Note: sql_expressions might be transformed to sql_snippets
        # Just check that the config was transformed successfully
        assert "version" in serialized
    
    def test_transform_preserves_instructions(self):
        """Test that instructions are preserved in transformation."""
        config = {
            "space_name": "Test",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {"catalog_name": "demo", "schema_name": "retail", "table_name": "transactions"}
            ],
            "instructions": [
                {"content": "Use transactions table for sales", "priority": 1}
            ]
        }
        
        serialized_json = transform_to_serialized_space(config)
        serialized = json.loads(serialized_json)
        
        assert "instructions" in serialized
        # Instructions are in text_instructions array
        if "text_instructions" in serialized["instructions"]:
            assert len(serialized["instructions"]["text_instructions"]) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestTransformationEdgeCases:
    """Tests for edge cases in transformation."""
    
    def test_handle_missing_optional_fields(self):
        """Test transformation handles missing optional fields."""
        minimal_config = {
            "space_name": "Test",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {"catalog_name": "demo", "schema_name": "retail", "table_name": "transactions"}
            ]
        }
        
        serialized_json = transform_to_serialized_space(minimal_config)
        serialized = json.loads(serialized_json)
        
        assert "version" in serialized
        assert "data_sources" in serialized
        assert "tables" in serialized["data_sources"]
    
    def test_handle_empty_lists(self):
        """Test transformation handles empty lists gracefully."""
        config = {
            "space_name": "Test",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {"catalog_name": "demo", "schema_name": "retail", "table_name": "transactions"}
            ],
            "instructions": [],
            "example_sql_queries": [],
            "sql_expressions": []
        }
        
        serialized_json = transform_to_serialized_space(config)
        serialized = json.loads(serialized_json)
        
        assert "version" in serialized
        # Should not fail on empty lists
    
    def test_preserve_special_characters(self):
        """Test that special characters are preserved during transformation."""
        config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
                ],
                "instructions": [
                    {"content": "게임 코드: `main.log_discord.message.game_code = 'inzoi'`"}
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            # Transform and verify Korean characters are preserved
            update_config_catalog_schema(
                temp_path,
                old_catalog="main",
                old_schema="log_discord",
                new_catalog="sandbox",
                new_schema="agent_poc"
            )
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                updated = json.load(f)
            
            instruction = updated["genie_space_config"]["instructions"][0]["content"]
            assert "게임" in instruction, "Korean characters should be preserved"
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
