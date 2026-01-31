"""Test Phase 2 enhanced parsing features"""
import pytest
from src.parsing.requirements_structurer import (
    QueryResultExample, FormulaDefinition, PlatformNote, SQLQuery, TableInfo
)
from src.parsing.formula_extractor import FormulaExtractor
from src.parsing.platform_analyzer import PlatformAnalyzer


class TestQueryResultExample:
    """Test query result example data structure"""

    def test_result_example_creation(self):
        """Verify result example can be created"""
        result = QueryResultExample(
            query_id="Q1",
            sample_rows=[
                {"user_id": "123", "count": "10"},
                {"user_id": "456", "count": "20"}
            ],
            column_names=["user_id", "count"],
            notes="Sample data for validation"
        )

        assert result.query_id == "Q1"
        assert len(result.sample_rows) == 2
        assert "user_id" in result.column_names

    def test_result_example_from_dict(self):
        """Verify result example can be created from dict"""
        data = {
            "query_id": "Q1",
            "sample_rows": [{"col1": "val1"}],
            "column_names": ["col1"],
            "notes": "Test notes"
        }
        result = QueryResultExample.from_dict(data)

        assert result.query_id == "Q1"
        assert len(result.sample_rows) == 1


class TestFormulaDefinition:
    """Test formula definition data structure"""

    def test_formula_creation(self):
        """Verify formula definition can be created"""
        formula = FormulaDefinition(
            name="ARPU",
            formula="try_divide(SUM(revenue), COUNT(DISTINCT user_id))",
            description="Average Revenue Per User",
            required_columns=["revenue", "user_id"],
            notes="Use try_divide to handle zero users"
        )

        assert formula.name == "ARPU"
        assert "try_divide" in formula.formula
        assert "revenue" in formula.required_columns

    def test_formula_from_dict(self):
        """Verify formula can be created from dict"""
        data = {
            "name": "DAU",
            "formula": "COUNT(DISTINCT user_id)",
            "description": "Daily Active Users",
            "required_columns": ["user_id"]
        }
        formula = FormulaDefinition.from_dict(data)

        assert formula.name == "DAU"
        assert formula.formula == "COUNT(DISTINCT user_id)"


class TestPlatformNote:
    """Test platform note data structure"""

    def test_platform_note_creation(self):
        """Verify platform note can be created"""
        note = PlatformNote(
            platform="PUBG",
            note_type="restriction",
            description="PUBG Only - not available for other games",
            affected_tables=["pubg.gcoin_usage"],
            example_code="WHERE week_start_day = 'MONDAY'"
        )

        assert note.platform == "PUBG"
        assert note.note_type == "restriction"
        assert "PUBG Only" in note.description

    def test_platform_note_from_dict(self):
        """Verify platform note can be created from dict"""
        data = {
            "platform": "Steam",
            "note_type": "transformation",
            "description": "Convert Unix timestamp",
            "affected_tables": ["steam.reviews"]
        }
        note = PlatformNote.from_dict(data)

        assert note.platform == "Steam"
        assert note.note_type == "transformation"


class TestFormulaExtractor:
    """Test formula extraction logic"""

    def test_dau_extraction(self):
        """Verify DAU formula is detected"""
        extractor = FormulaExtractor()

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT COUNT(DISTINCT user_id) as dau FROM users",
                description="Daily active users"
            )
        ]

        formulas = extractor.extract_formulas(queries)

        assert any(f.name == "DAU" for f in formulas)
        dau_formula = next(f for f in formulas if f.name == "DAU")
        assert "user_id" in dau_formula.required_columns

    def test_arpu_extraction(self):
        """Verify ARPU formula is detected"""
        extractor = FormulaExtractor()

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT try_divide(SUM(revenue), COUNT(DISTINCT user_id)) as arpu",
                description="Average revenue per user"
            )
        ]

        formulas = extractor.extract_formulas(queries)

        assert any(f.name == "ARPU" for f in formulas)
        arpu_formula = next(f for f in formulas if f.name == "ARPU")
        assert "revenue" in arpu_formula.required_columns
        assert "user_id" in arpu_formula.required_columns

    def test_multiple_formula_detection(self):
        """Verify multiple formulas can be detected"""
        extractor = FormulaExtractor()

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT COUNT(DISTINCT user_id) as dau FROM users",
                description="DAU"
            ),
            SQLQuery(
                question_id="Q2",
                query="SELECT try_divide(SUM(revenue), COUNT(DISTINCT user_id)) as arpu",
                description="ARPU"
            )
        ]

        formulas = extractor.extract_formulas(queries)

        assert len(formulas) >= 2
        formula_names = [f.name for f in formulas]
        assert "DAU" in formula_names
        assert "ARPU" in formula_names

    def test_formula_usage_tracking(self):
        """Verify formula usage is tracked across queries"""
        extractor = FormulaExtractor()

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT COUNT(DISTINCT user_id) as dau FROM users WHERE date = '2023-01-01'",
                description="DAU for day 1"
            ),
            SQLQuery(
                question_id="Q2",
                query="SELECT COUNT(DISTINCT user_id) as dau FROM users WHERE date = '2023-01-02'",
                description="DAU for day 2"
            )
        ]

        formulas = extractor.extract_formulas(queries)

        dau_formula = next(f for f in formulas if f.name == "DAU")
        assert "Q1" in dau_formula.notes
        assert "Q2" in dau_formula.notes


class TestPlatformAnalyzer:
    """Test platform-specific logic analysis"""

    def test_platform_detection_from_table_name(self):
        """Verify platform is detected from table name"""
        analyzer = PlatformAnalyzer()

        platform = analyzer._detect_platform("pubg.gcoin_usage")
        assert platform == "PUBG"

        platform = analyzer._detect_platform("steam.reviews")
        assert platform == "Steam"

        platform = analyzer._detect_platform("discord.messages")
        assert platform == "Discord"

    def test_restriction_detection(self):
        """Verify restrictions are detected from remarks"""
        analyzer = PlatformAnalyzer()

        tables = [
            TableInfo(
                catalog="main",
                schema="pubg",
                table="gcoin_usage",
                description="GCoin usage data",
                table_remarks=["PUBG Only - not available for other games"]
            )
        ]

        notes = analyzer.analyze_tables(tables)

        assert len(notes) > 0
        assert any(n.note_type == "restriction" for n in notes)
        assert any("PUBG" in n.platform for n in notes)

    def test_transformation_detection(self):
        """Verify transformations are detected from queries"""
        analyzer = PlatformAnalyzer()

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT FROM_UNIXTIME(timestamp_created) as created_at FROM steam.reviews",
                description="Steam reviews with timestamp conversion"
            )
        ]

        notes = analyzer.analyze_queries(queries)

        assert len(notes) > 0
        assert any(n.note_type == "transformation" for n in notes)
        assert any("FROM_UNIXTIME" in str(n.example_code) for n in notes if n.example_code)

    def test_requirement_detection(self):
        """Verify requirements are detected from remarks"""
        analyzer = PlatformAnalyzer()

        tables = [
            TableInfo(
                catalog="main",
                schema="pubg",
                table="weekly_summary",
                description="Weekly summary",
                table_remarks=["week_start_day must be specified"]
            )
        ]

        notes = analyzer.analyze_tables(tables)

        assert len(notes) > 0
        assert any(n.note_type == "requirement" for n in notes)

    def test_note_deduplication(self):
        """Verify duplicate notes are merged"""
        analyzer = PlatformAnalyzer()

        notes = [
            PlatformNote(
                platform="PUBG",
                note_type="restriction",
                description="PUBG Only",
                affected_tables=["table1"]
            ),
            PlatformNote(
                platform="PUBG",
                note_type="restriction",
                description="PUBG Only",
                affected_tables=["table2"]
            )
        ]

        deduplicated = analyzer.deduplicate_notes(notes)

        assert len(deduplicated) == 1
        assert len(deduplicated[0].affected_tables) == 2


class TestSQLQueryPhase2Fields:
    """Test SQLQuery Phase 2 enhancements"""

    def test_sql_query_with_phase2_fields(self):
        """Verify SQLQuery supports Phase 2 fields"""
        result_example = QueryResultExample(
            query_id="Q1",
            sample_rows=[{"col1": "val1"}],
            column_names=["col1"]
        )

        query = SQLQuery(
            question_id="Q1",
            query="SELECT * FROM table",
            description="Test query",
            intent="monitoring",
            complexity="medium",
            optimization_notes=["Add index on user_id"],
            result_example=result_example
        )

        assert query.intent == "monitoring"
        assert query.complexity == "medium"
        assert len(query.optimization_notes) == 1
        assert query.result_example.query_id == "Q1"

    def test_sql_query_phase2_defaults(self):
        """Verify Phase 2 fields have proper defaults"""
        query = SQLQuery(
            question_id="Q1",
            query="SELECT * FROM table",
            description="Test query"
        )

        assert query.intent is None
        assert query.complexity is None
        assert query.optimization_notes == []
        assert query.result_example is None

    def test_sql_query_from_dict_with_phase2(self):
        """Verify SQLQuery.from_dict handles Phase 2 fields"""
        data = {
            "question_id": "Q1",
            "query": "SELECT * FROM table",
            "description": "Test query",
            "intent": "analysis",
            "complexity": "high",
            "optimization_notes": ["Consider partitioning"],
            "result_example": {
                "query_id": "Q1",
                "sample_rows": [{"col1": "val1"}],
                "column_names": ["col1"]
            }
        }

        query = SQLQuery.from_dict(data)

        assert query.intent == "analysis"
        assert query.complexity == "high"
        assert len(query.optimization_notes) == 1
        assert query.result_example.query_id == "Q1"


@pytest.mark.integration
class TestPhase2Integration:
    """Integration tests for Phase 2 features"""

    def test_formula_extraction_integration(self):
        """Verify formula extraction works end-to-end"""
        from src.parsing.formula_extractor import extract_formulas

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT COUNT(DISTINCT user_id) as dau FROM users",
                description="DAU"
            ),
            SQLQuery(
                question_id="Q2",
                query="SELECT try_divide(SUM(revenue), COUNT(DISTINCT user_id)) as arpu",
                description="ARPU"
            )
        ]

        formulas = extract_formulas(queries)

        assert len(formulas) >= 2
        assert any(f.name == "DAU" for f in formulas)
        assert any(f.name == "ARPU" for f in formulas)

    def test_platform_analysis_integration(self):
        """Verify platform analysis works end-to-end"""
        from src.parsing.platform_analyzer import analyze_platform_logic

        tables = [
            TableInfo(
                catalog="main",
                schema="pubg",
                table="gcoin_usage",
                description="GCoin data",
                table_remarks=["PUBG Only"]
            )
        ]

        queries = [
            SQLQuery(
                question_id="Q1",
                query="SELECT FROM_UNIXTIME(timestamp) FROM steam.reviews",
                description="Steam reviews"
            )
        ]

        notes = analyze_platform_logic(tables, queries)

        assert len(notes) > 0
        platforms = [n.platform for n in notes]
        assert any(p in ["PUBG", "Steam"] for p in platforms)
