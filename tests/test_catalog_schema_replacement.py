"""Tests for catalog and schema replacement functionality."""

import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from genie import update_config_catalog_schema


def test_update_config_catalog_schema_updates_instructions():
    """Test that update_config_catalog_schema updates table references in instructions."""
    # Create a test config with instructions containing table references
    test_config = {
        "genie_space_config": {
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "log_discord",
                    "table_name": "message"
                },
                {
                    "catalog_name": "main",
                    "schema_name": "log_steam",
                    "table_name": "store_appreviews"
                }
            ],
            "instructions": [
                {
                    "content": "사용자가 게임을 명시하지 않으면 기본값을 사용합니다. Discord: `main.log_discord.message.game_code = 'inzoi'`"
                },
                {
                    "content": "Steam: `main.log_steam.store_appreviews.app_id = 2456740`"
                },
                {
                    "content": "Discord 리액션 분석 시에는 반드시 `main.log_discord.message` LEFT JOIN `main.log_discord.reaction` ON `message.message_id = reaction.message_id`를 사용합니다."
                }
            ],
            "sql_snippets": {
                "measures": [
                    {
                        "alias": "total_messages",
                        "sql": "COUNT(*)",
                        "display_name": "total messages"
                    }
                ],
                "filters": [
                    {
                        "sql": "main.log_discord.message.game_code = 'inzoi'",
                        "display_name": "INZOI messages"
                    }
                ]
            },
            "example_sql_queries": [
                {
                    "question": "How many messages?",
                    "sql_query": "SELECT COUNT(*) FROM main.log_discord.message"
                }
            ],
            "benchmark_questions": [
                {
                    "question": "Total messages?",
                    "expected_sql": "SELECT COUNT(*) FROM main.log_discord.message",
                    "table": "`main.log_discord.message`"
                }
            ]
        }
    }

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_config, f)
        temp_path = f.name

    try:
        # Update catalog.schema
        counts = update_config_catalog_schema(
            temp_path,
            old_catalog="main",
            old_schema="log_discord",
            new_catalog="sandbox",
            new_schema="agent_poc"
        )

        # Verify counts
        assert counts['tables'] == 1, "Should update 1 table"
        assert counts['instructions'] == 2, "Should update 2 instructions"
        assert counts['sql_expressions'] == 1, "Should update 1 SQL snippet (filter)"
        assert counts['example_queries'] == 1, "Should update 1 example query"
        assert counts['benchmark_questions'] == 1, "Should update 1 benchmark question"

        # Read back and verify instructions were updated
        with open(temp_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        updated_genie_config = updated_config["genie_space_config"]
        instructions = updated_genie_config["instructions"]

        # Check that old references are replaced
        assert any("sandbox.agent_poc.message" in inst["content"] for inst in instructions), \
            "Should replace main.log_discord.message with sandbox.agent_poc.message"

        assert any("sandbox.agent_poc.reaction" in inst["content"] for inst in instructions), \
            "Should replace main.log_discord.reaction with sandbox.agent_poc.reaction"

        # Check that old references are gone
        assert not any("main.log_discord.message" in inst["content"] for inst in instructions), \
            "Should not contain main.log_discord.message anymore"

        # Check that Steam references are unchanged
        assert any("main.log_steam.store_appreviews" in inst["content"] for inst in instructions), \
            "Should keep main.log_steam.store_appreviews unchanged"

    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_update_config_catalog_schema_multiple_replacements():
    """Test that multiple catalog.schema replacements work correctly."""
    test_config = {
        "genie_space_config": {
            "tables": [
                {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"},
                {"catalog_name": "main", "schema_name": "log_steam", "table_name": "store_appreviews"}
            ],
            "instructions": [
                {
                    "content": "Discord tables: main.log_discord.message, main.log_discord.reaction"
                },
                {
                    "content": "Steam tables: main.log_steam.store_appreviews, main.log_steam.partner_traffic"
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_config, f)
        temp_path = f.name

    try:
        # First replacement: Discord tables
        counts1 = update_config_catalog_schema(
            temp_path,
            old_catalog="main",
            old_schema="log_discord",
            new_catalog="sandbox",
            new_schema="agent_poc"
        )

        assert counts1['tables'] == 1
        assert counts1['instructions'] == 1  # Only the Discord instruction should be updated

        # Second replacement: Steam tables
        counts2 = update_config_catalog_schema(
            temp_path,
            old_catalog="main",
            old_schema="log_steam",
            new_catalog="sandbox",
            new_schema="agent_poc"
        )

        assert counts2['tables'] == 1
        assert counts2['instructions'] == 1  # Only the Steam instruction should be updated

        # Verify final state
        with open(temp_path, 'r', encoding='utf-8') as f:
            updated_config = json.load(f)

        instructions = updated_config["genie_space_config"]["instructions"]

        # Both should be updated to sandbox.agent_poc
        assert all("sandbox.agent_poc" in inst["content"] for inst in instructions), \
            "All tables should be updated to sandbox.agent_poc"

        assert not any("main.log_discord" in inst["content"] for inst in instructions), \
            "No main.log_discord references should remain"

        assert not any("main.log_steam" in inst["content"] for inst in instructions), \
            "No main.log_steam references should remain"

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_update_config_catalog_schema_no_instructions():
    """Test that update works correctly when there are no instructions."""
    test_config = {
        "genie_space_config": {
            "tables": [
                {"catalog_name": "main", "schema_name": "log_discord", "table_name": "message"}
            ],
            "sql_snippets": {
                "filters": [
                    {
                        "sql": "main.log_discord.message.game_code = 'inzoi'",
                        "display_name": "INZOI filter"
                    }
                ]
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_config, f)
        temp_path = f.name

    try:
        # Should not error when instructions are missing
        counts = update_config_catalog_schema(
            temp_path,
            old_catalog="main",
            old_schema="log_discord",
            new_catalog="sandbox",
            new_schema="agent_poc"
        )

        assert counts['tables'] == 1
        assert counts['instructions'] == 0  # No instructions to update
        assert counts['sql_expressions'] == 1  # 1 filter updated

    finally:
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
