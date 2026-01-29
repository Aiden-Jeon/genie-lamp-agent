"""Tests for SQL validator."""

import pytest
from src.utils.sql_validator import (
    SQLValidator,
    ValidationIssue,
    SQLValidationReport,
    validate_join_specifications
)
from src.models import GenieSpaceTable


@pytest.fixture
def sample_tables():
    """Sample tables for testing."""
    return [
        GenieSpaceTable(
            catalog_name="main",
            schema_name="retail",
            table_name="transactions"
        ),
        GenieSpaceTable(
            catalog_name="main",
            schema_name="retail",
            table_name="customers"
        ),
        GenieSpaceTable(
            catalog_name="main",
            schema_name="retail",
            table_name="products"
        )
    ]


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_create_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            severity="error",
            category="syntax",
            message="Test error message",
            suggestion="Test suggestion"
        )

        assert issue.severity == "error"
        assert issue.category == "syntax"
        assert issue.message == "Test error message"
        assert issue.suggestion == "Test suggestion"


class TestSQLValidationReport:
    """Test SQLValidationReport dataclass."""

    def test_report_initialization(self):
        """Test report initialization."""
        report = SQLValidationReport(sql_query="SELECT * FROM test", is_valid=True)

        assert report.sql_query == "SELECT * FROM test"
        assert report.is_valid == True
        assert len(report.issues) == 0

    def test_add_issue_error(self):
        """Test adding an error issue marks report as invalid."""
        report = SQLValidationReport(sql_query="SELECT", is_valid=True)

        error = ValidationIssue(severity="error", category="syntax", message="Error")
        report.add_issue(error)

        assert not report.is_valid
        assert len(report.issues) == 1

    def test_add_issue_warning(self):
        """Test adding a warning doesn't mark report as invalid."""
        report = SQLValidationReport(sql_query="SELECT", is_valid=True)

        warning = ValidationIssue(severity="warning", category="best_practice", message="Warning")
        report.add_issue(warning)

        assert report.is_valid
        assert len(report.issues) == 1

    def test_get_errors_and_warnings(self):
        """Test filtering errors and warnings."""
        report = SQLValidationReport(sql_query="SELECT", is_valid=True)

        report.add_issue(ValidationIssue(severity="error", category="syntax", message="Error 1"))
        report.add_issue(ValidationIssue(severity="warning", category="best_practice", message="Warning 1"))
        report.add_issue(ValidationIssue(severity="error", category="table", message="Error 2"))

        errors = report.get_errors()
        warnings = report.get_warnings()

        assert len(errors) == 2
        assert len(warnings) == 1


class TestSQLValidator:
    """Test SQLValidator class."""

    def test_initialization(self, sample_tables):
        """Test validator initialization."""
        validator = SQLValidator(available_tables=sample_tables)

        assert len(validator.available_tables) == 3
        assert len(validator.table_map) > 0

    def test_table_map_building(self, sample_tables):
        """Test table map contains correct identifiers."""
        validator = SQLValidator(available_tables=sample_tables)

        # Should have full identifier
        assert "main.retail.transactions" in validator.table_map

        # Should have schema.table identifier
        assert "retail.transactions" in validator.table_map

        # Should have table name
        assert "transactions" in validator.table_map

    def test_validate_empty_sql(self):
        """Test validation of empty SQL."""
        validator = SQLValidator()
        report = validator.validate_sql("")

        assert not report.is_valid
        assert len(report.get_errors()) > 0
        assert "Empty SQL" in report.get_errors()[0].message

    def test_validate_simple_valid_sql(self, sample_tables):
        """Test validation of simple valid SQL."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT t.transaction_id, t.amount
        FROM main.retail.transactions t
        WHERE t.event_date >= CURRENT_DATE()
        LIMIT 10
        """

        report = validator.validate_sql(sql)

        # Should be valid (may have warnings but no errors)
        assert len(report.get_errors()) == 0
        assert "main.retail.transactions" in report.tables_referenced
        assert report.has_limit

    def test_validate_explicit_join(self, sample_tables):
        """Test detection of explicit joins."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT c.customer_name, COUNT(t.transaction_id)
        FROM main.retail.transactions t
        INNER JOIN main.retail.customers c
          ON t.customer_id = c.customer_id
        GROUP BY c.customer_name
        """

        report = validator.validate_sql(sql)

        assert report.has_explicit_joins
        assert report.has_group_by
        assert len(report.get_errors()) == 0

    def test_detect_implicit_join(self, sample_tables):
        """Test detection of implicit comma joins."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT *
        FROM main.retail.transactions t, main.retail.customers c
        WHERE t.customer_id = c.customer_id
        """

        report = validator.validate_sql(sql)

        # Should have warning about implicit join
        warnings = report.get_warnings()
        assert any("Implicit join" in w.message for w in warnings)

    def test_detect_missing_on_clause(self, sample_tables):
        """Test detection of JOIN without ON clause."""
        validator = SQLValidator(available_tables=sample_tables)

        # Invalid SQL - JOIN without ON
        sql = """
        SELECT *
        FROM main.retail.transactions t
        INNER JOIN main.retail.customers c
        WHERE t.customer_id = c.customer_id
        """

        report = validator.validate_sql(sql)

        # Should have error about missing ON clause
        errors = report.get_errors()
        assert any("ON clause" in e.message for e in errors)

    def test_detect_select_star(self, sample_tables):
        """Test detection of SELECT *."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = "SELECT * FROM main.retail.transactions"

        report = validator.validate_sql(sql)

        # Should have warning about SELECT *
        warnings = report.get_warnings()
        assert any("SELECT *" in w.message for w in warnings)

    def test_detect_hard_coded_date(self, sample_tables):
        """Test detection of hard-coded dates."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT * FROM main.retail.transactions
        WHERE event_date > '2024-01-01'
        """

        report = validator.validate_sql(sql)

        # Should have warning about hard-coded date
        warnings = report.get_warnings()
        assert any("Hard-coded date" in w.message for w in warnings)

    def test_detect_table_not_found(self, sample_tables):
        """Test detection of non-existent tables."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = "SELECT * FROM main.retail.nonexistent_table"

        report = validator.validate_sql(sql)

        # Should have error about table not found
        errors = report.get_errors()
        assert any("Table not found" in e.message for e in errors)

    def test_detect_unbalanced_parentheses(self):
        """Test detection of unbalanced parentheses."""
        validator = SQLValidator()

        sql = "SELECT COUNT(transaction_id FROM transactions"

        report = validator.validate_sql(sql)

        # Should have error about unbalanced parentheses
        errors = report.get_errors()
        assert any("parentheses" in e.message.lower() for e in errors)

    def test_detect_aggregate_without_group_by(self, sample_tables):
        """Test detection of aggregates without GROUP BY."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT customer_name, SUM(amount)
        FROM main.retail.transactions
        """

        report = validator.validate_sql(sql)

        # Should have warning about missing GROUP BY
        warnings = report.get_warnings()
        assert any("GROUP BY" in w.message for w in warnings)

    def test_detect_unsafe_division(self, sample_tables):
        """Test detection of unsafe division."""
        validator = SQLValidator(available_tables=sample_tables)

        sql = """
        SELECT revenue / order_count as avg_order_value
        FROM main.retail.transactions
        """

        report = validator.validate_sql(sql)

        # Should have info message about unsafe division
        issues = report.issues
        assert any("division" in i.message.lower() for i in issues)

    def test_validate_config_sql(self, sample_tables):
        """Test validation of entire config."""
        validator = SQLValidator(available_tables=sample_tables)

        config = {
            "example_sql_queries": [
                {
                    "question": "Good query",
                    "sql_query": "SELECT t.id FROM main.retail.transactions t LIMIT 10"
                },
                {
                    "question": "Bad query",
                    "sql_query": "SELECT * FROM nonexistent"
                }
            ],
            "sql_snippets": {
                "measures": [
                    {
                        "alias": "total_revenue",
                        "sql": "SUM(amount)",
                        "display_name": "total revenue"
                    }
                ]
            }
        }

        results = validator.validate_config_sql(config)

        assert results["summary"]["total_queries"] == 3
        assert results["summary"]["queries_with_errors"] >= 1
        assert len(results["example_queries"]) == 2
        assert len(results["sql_snippets"]["measures"]) == 1


class TestValidateJoinSpecifications:
    """Test join specification validation."""

    def test_validate_valid_joins(self, sample_tables):
        """Test validation of valid join specifications."""
        join_specs = [
            {
                "left_table": "main.retail.transactions",
                "right_table": "main.retail.customers",
                "join_type": "INNER",
                "join_condition": "transactions.customer_id = customers.customer_id"
            }
        ]

        issues = validate_join_specifications(join_specs, sample_tables)

        assert len(issues) == 0

    def test_validate_missing_table(self, sample_tables):
        """Test validation with non-existent table."""
        join_specs = [
            {
                "left_table": "main.retail.nonexistent",
                "right_table": "main.retail.customers",
                "join_type": "INNER",
                "join_condition": "nonexistent.id = customers.id"
            }
        ]

        issues = validate_join_specifications(join_specs, sample_tables)

        assert len(issues) > 0
        assert any("not found" in i.message.lower() for i in issues)

    def test_validate_empty_join_condition(self, sample_tables):
        """Test validation with empty join condition."""
        join_specs = [
            {
                "left_table": "main.retail.transactions",
                "right_table": "main.retail.customers",
                "join_type": "INNER",
                "join_condition": ""
            }
        ]

        issues = validate_join_specifications(join_specs, sample_tables)

        assert len(issues) > 0
        assert any("Empty join condition" in i.message for i in issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
