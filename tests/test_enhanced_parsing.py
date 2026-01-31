"""Test enhanced parsing features (Phase 1)"""
import pytest
from src.parsing.requirements_structurer import ColumnInfo, SQLQuery, JoinSpec
from src.parsing.markdown_parser import MarkdownParser


class TestColumnMetadata:
    """Test column-level metadata extraction"""

    def test_optional_column_detection_korean(self):
        """Verify optional columns are marked correctly (Korean)"""
        parser = MarkdownParser()
        text = "`channel_list.channel_name` (선택적)"
        metadata = parser._extract_column_metadata(text)
        assert "channel_list.channel_name" in metadata
        assert metadata["channel_list.channel_name"]["is_required"] == False

    def test_optional_column_detection_english(self):
        """Verify optional columns are marked correctly (English)"""
        parser = MarkdownParser()
        text = "`user_profile.avatar_url` (optional)"
        metadata = parser._extract_column_metadata(text)
        assert "user_profile.avatar_url" in metadata
        assert metadata["user_profile.avatar_url"]["is_required"] == False

    def test_usage_type_extraction(self):
        """Verify column usage types are captured"""
        parser = MarkdownParser()
        text = "`event_date` is for filtering only"
        metadata = parser._extract_column_metadata(text)
        assert "event_date" in metadata
        assert "filtering" in metadata["event_date"]["usage_type"]

    def test_column_info_defaults(self):
        """Verify ColumnInfo has proper defaults"""
        col = ColumnInfo(name="test_col")
        assert col.is_required == True
        assert col.usage_type is None
        assert col.transformation_rule is None


class TestAggregationPatterns:
    """Test aggregation pattern detection"""

    def test_coalesce_detection(self):
        """Verify COALESCE patterns are identified"""
        parser = MarkdownParser()
        query = "SELECT COALESCE(SUM(count), 0) FROM table"
        patterns = parser._extract_aggregation_patterns(query)
        assert "COALESCE" in patterns

    def test_cte_detection(self):
        """Verify CTE patterns are detected"""
        parser = MarkdownParser()
        query = "WITH hot_messages AS (SELECT * FROM messages) SELECT * FROM hot_messages"
        patterns = parser._extract_aggregation_patterns(query)
        assert "CTE" in patterns

    def test_union_all_detection(self):
        """Verify UNION ALL patterns are detected"""
        parser = MarkdownParser()
        query = "SELECT * FROM table1 UNION ALL SELECT * FROM table2"
        patterns = parser._extract_aggregation_patterns(query)
        assert "UNION_ALL" in patterns

    def test_window_function_detection(self):
        """Verify window functions are detected"""
        parser = MarkdownParser()
        query = "SELECT user_id, RANK() OVER (ORDER BY score DESC) FROM scores"
        patterns = parser._extract_aggregation_patterns(query)
        assert "RANK()" in patterns

    def test_try_divide_detection(self):
        """Verify try_divide patterns are detected"""
        parser = MarkdownParser()
        query = "SELECT try_divide(revenue, users) as arpu FROM metrics"
        patterns = parser._extract_aggregation_patterns(query)
        assert "TRY_DIVIDE" in patterns

    def test_multiple_patterns(self):
        """Verify multiple patterns in single query"""
        parser = MarkdownParser()
        query = """
        WITH ranked AS (
            SELECT user_id, RANK() OVER (ORDER BY score) as rank
            FROM scores
        )
        SELECT COALESCE(SUM(score), 0) FROM ranked
        """
        patterns = parser._extract_aggregation_patterns(query)
        assert "CTE" in patterns
        assert "RANK()" in patterns
        assert "COALESCE" in patterns


class TestFilteringRules:
    """Test filtering rule extraction"""

    def test_simple_where_clause(self):
        """Verify simple WHERE conditions are extracted"""
        parser = MarkdownParser()
        query = "SELECT * FROM table WHERE event_date >= DATE '2025-07-26'"
        rules = parser._extract_filtering_rules(query)
        assert len(rules) > 0
        assert any("event_date" in rule for rule in rules)

    def test_multiple_conditions(self):
        """Verify multiple AND conditions are extracted"""
        parser = MarkdownParser()
        query = """
        SELECT * FROM table
        WHERE event_date >= DATE '2025-07-26'
        AND game_code = 'inzoi'
        AND status = 'active'
        """
        rules = parser._extract_filtering_rules(query)
        assert len(rules) >= 3

    def test_complex_where_with_groupby(self):
        """Verify WHERE clause before GROUP BY is extracted"""
        parser = MarkdownParser()
        query = """
        SELECT game_code, COUNT(*)
        FROM table
        WHERE event_date = CURRENT_DATE
        GROUP BY game_code
        """
        rules = parser._extract_filtering_rules(query)
        assert len(rules) > 0


class TestJoinSpecs:
    """Test join specification extraction"""

    def test_simple_left_join(self):
        """Verify simple LEFT JOIN is extracted"""
        parser = MarkdownParser()
        query = """
        SELECT * FROM message m
        LEFT JOIN reaction r ON m.message_id = r.message_id
        """
        join_specs = parser._extract_join_specs_from_query(query)
        assert len(join_specs) > 0
        assert any("message_id" in spec for spec in join_specs)

    def test_multiple_joins(self):
        """Verify multiple JOINs are extracted"""
        parser = MarkdownParser()
        query = """
        SELECT * FROM message m
        LEFT JOIN reaction r ON m.message_id = r.message_id
        LEFT JOIN channel_list c ON m.channel_id = c.channel_id
        """
        join_specs = parser._extract_join_specs_from_query(query)
        assert len(join_specs) >= 2

    def test_inner_join(self):
        """Verify INNER JOIN is extracted"""
        parser = MarkdownParser()
        query = """
        SELECT * FROM users u
        INNER JOIN orders o ON u.user_id = o.user_id
        """
        join_specs = parser._extract_join_specs_from_query(query)
        assert len(join_specs) > 0
        assert any("INNER" in spec.upper() for spec in join_specs)


class TestJoinSpecDataclass:
    """Test JoinSpec dataclass"""

    def test_join_spec_parsing(self):
        """Verify join specifications are parsed correctly"""
        join_data = {
            "left_table": "message",
            "right_table": "reaction",
            "join_type": "LEFT",
            "join_condition": "message.message_id = reaction.message_id",
            "is_optional": False
        }
        join_spec = JoinSpec.from_dict(join_data)
        assert join_spec.left_table == "message"
        assert join_spec.right_table == "reaction"
        assert join_spec.join_type == "LEFT"
        assert join_spec.is_optional == False

    def test_join_spec_defaults(self):
        """Verify JoinSpec has proper defaults"""
        join_spec = JoinSpec(
            left_table="table1",
            right_table="table2",
            join_type="LEFT",
            join_condition="table1.id = table2.id"
        )
        assert join_spec.is_optional == False


class TestRemarks:
    """Test remark extraction"""

    def test_remark_extraction_korean(self):
        """Verify Korean remarks are extracted"""
        parser = MarkdownParser()
        text = "**비고:** week_start_day specification required"
        remarks = parser._extract_remarks(text)
        assert len(remarks) > 0
        assert "week_start_day" in remarks[0]

    def test_remark_extraction_english(self):
        """Verify English remarks are extracted"""
        parser = MarkdownParser()
        text = "**Remark:** PUBG Only - not available for other games"
        remarks = parser._extract_remarks(text)
        assert len(remarks) > 0
        assert "PUBG" in remarks[0]

    def test_multiple_remarks(self):
        """Verify multiple remarks are extracted"""
        parser = MarkdownParser()
        text = """
        **Remark:** First note

        **참고:** Second note
        """
        remarks = parser._extract_remarks(text)
        assert len(remarks) >= 2


class TestSQLQueryEnhancements:
    """Test SQLQuery dataclass enhancements"""

    def test_sql_query_defaults(self):
        """Verify SQLQuery has proper defaults for enhanced fields"""
        query = SQLQuery(
            question_id="Q1",
            query="SELECT * FROM table",
            description="Test query"
        )
        assert query.aggregation_patterns == []
        assert query.filtering_rules == []
        assert query.join_specs == []

    def test_sql_query_from_dict_enhanced(self):
        """Verify SQLQuery.from_dict handles enhanced fields"""
        data = {
            "question_id": "Q1",
            "query": "SELECT COALESCE(COUNT(*), 0) FROM table WHERE date = '2025-01-01'",
            "description": "Test query",
            "aggregation_patterns": ["COALESCE"],
            "filtering_rules": ["date = '2025-01-01'"],
            "join_specs": ["LEFT JOIN table2 ON table1.id = table2.id"]
        }
        query = SQLQuery.from_dict(data)
        assert "COALESCE" in query.aggregation_patterns
        assert len(query.filtering_rules) > 0
        assert len(query.join_specs) > 0

    def test_sql_query_from_dict_legacy(self):
        """Verify SQLQuery.from_dict handles legacy format"""
        data = {
            "question_id": "Q1",
            "query": "SELECT * FROM table",
            "description": "Test query"
        }
        query = SQLQuery.from_dict(data)
        assert query.aggregation_patterns == []
        assert query.filtering_rules == []
        assert query.join_specs == []


@pytest.mark.integration
class TestEnhancedParsingIntegration:
    """Integration tests for enhanced parsing"""

    def test_backward_compatibility(self):
        """Verify enhanced parsing is backward compatible"""
        # Legacy column format (list of strings)
        from src.parsing.requirements_structurer import TableInfo

        table_data = {
            "full_name": "catalog.schema.table",
            "description": "Test table",
            "key_columns": ["col1", "col2", "col3"]
        }
        table = TableInfo.from_dict(table_data)
        assert len(table.columns) == 3
        assert all(col.is_required == True for col in table.columns)

    def test_enhanced_column_format(self):
        """Verify enhanced column format is parsed correctly"""
        from src.parsing.requirements_structurer import TableInfo

        table_data = {
            "full_name": "catalog.schema.table",
            "description": "Test table",
            "key_columns": [
                {
                    "name": "event_date",
                    "data_type": "date",
                    "is_required": True,
                    "usage_type": "filtering"
                },
                {
                    "name": "channel_name",
                    "data_type": "string",
                    "is_required": False,
                    "usage_type": "display"
                }
            ],
            "table_remarks": ["PUBG Only", "Requires week_start_day"]
        }
        table = TableInfo.from_dict(table_data)
        assert len(table.columns) == 2
        assert table.columns[0].is_required == True
        assert table.columns[0].usage_type == "filtering"
        assert table.columns[1].is_required == False
        assert len(table.table_remarks) == 2
