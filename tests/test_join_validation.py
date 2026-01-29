"""Test join validation and catalog/schema correction."""
import pytest
from src.utils.config_transformer import _validate_and_fix_join_table_references


def test_corrects_catalog_schema_mismatch():
    """Test that catalog/schema mismatches are automatically corrected."""
    tables = [
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "message"},
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "reaction"},
    ]

    joins = [
        {
            "left_table": "main.log_discord.message",
            "left_alias": "message",
            "right_table": "main.log_discord.reaction",
            "right_alias": "reaction",
            "join_condition": "main.log_discord.message.message_id = main.log_discord.reaction.message_id",
            "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        }
    ]

    corrected = _validate_and_fix_join_table_references(joins, tables)

    assert len(corrected) == 1
    assert corrected[0]["left_table"] == "sandbox.agent_poc.message"
    assert corrected[0]["right_table"] == "sandbox.agent_poc.reaction"
    assert "sandbox.agent_poc.message.message_id" in corrected[0]["join_condition"]
    assert "sandbox.agent_poc.reaction.message_id" in corrected[0]["join_condition"]


def test_skips_joins_with_missing_tables():
    """Test that joins referencing tables not in the space are skipped."""
    tables = [
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "message"},
    ]

    joins = [
        {
            "left_table": "main.log_discord.message",
            "left_alias": "message",
            "right_table": "main.log_discord.reaction",
            "right_alias": "reaction",
            "join_condition": "main.log_discord.message.message_id = main.log_discord.reaction.message_id",
            "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        }
    ]

    corrected = _validate_and_fix_join_table_references(joins, tables)

    # Join should be skipped because 'reaction' table doesn't exist
    assert len(corrected) == 0


def test_preserves_valid_joins():
    """Test that joins with correct catalog/schema are preserved unchanged."""
    tables = [
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "message"},
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "reaction"},
    ]

    joins = [
        {
            "left_table": "sandbox.agent_poc.message",
            "left_alias": "message",
            "right_table": "sandbox.agent_poc.reaction",
            "right_alias": "reaction",
            "join_condition": "sandbox.agent_poc.message.message_id = sandbox.agent_poc.reaction.message_id",
            "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        }
    ]

    corrected = _validate_and_fix_join_table_references(joins, tables)

    assert len(corrected) == 1
    assert corrected[0]["left_table"] == "sandbox.agent_poc.message"
    assert corrected[0]["right_table"] == "sandbox.agent_poc.reaction"
    assert corrected[0]["join_condition"] == "sandbox.agent_poc.message.message_id = sandbox.agent_poc.reaction.message_id"


def test_handles_complex_join_conditions():
    """Test that complex join conditions are correctly updated."""
    tables = [
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "partner_wishlist"},
        {"catalog_name": "sandbox", "schema_name": "agent_poc", "table_name": "store_appreviews"},
    ]

    joins = [
        {
            "left_table": "main.log_steam.partner_wishlist",
            "left_alias": "partner_wishlist",
            "right_table": "main.log_steam.store_appreviews",
            "right_alias": "store_appreviews",
            "join_condition": "TRY_TO_DATE(main.log_steam.partner_wishlist.date_local, 'yyyy-MM-dd') = main.log_steam.store_appreviews.event_date AND CAST(main.log_steam.partner_wishlist.app_id AS BIGINT) = main.log_steam.store_appreviews.app_id",
            "relationship_type": "FROM_RELATIONSHIP_TYPE_MANY_TO_ONE"
        }
    ]

    corrected = _validate_and_fix_join_table_references(joins, tables)

    assert len(corrected) == 1
    assert corrected[0]["left_table"] == "sandbox.agent_poc.partner_wishlist"
    assert corrected[0]["right_table"] == "sandbox.agent_poc.store_appreviews"
    # Check that all old references were replaced in the join condition
    assert "main.log_steam" not in corrected[0]["join_condition"]
    assert "sandbox.agent_poc.partner_wishlist.date_local" in corrected[0]["join_condition"]
    assert "sandbox.agent_poc.store_appreviews.event_date" in corrected[0]["join_condition"]
