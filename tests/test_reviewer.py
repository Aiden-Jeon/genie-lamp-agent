"""Tests for configuration review agent."""

import pytest
from src.pipeline.reviewer import (
    ConfigReviewAgent,
    ReviewIssue,
    ConfigReviewReport
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
        )
    ]


class TestReviewIssue:
    """Test ReviewIssue dataclass."""

    def test_create_issue(self):
        """Test creating a review issue."""
        issue = ReviewIssue(
            severity="high",
            category="sql",
            message="SQL error found",
            suggestion="Fix the SQL",
            affected_item="Query #1"
        )

        assert issue.severity == "high"
        assert issue.category == "sql"
        assert issue.message == "SQL error found"


class TestConfigReviewReport:
    """Test ConfigReviewReport dataclass."""

    def test_report_initialization(self):
        """Test report initialization."""
        report = ConfigReviewReport(
            config_name="Test Config",
            overall_score=85.0,
            passed=True
        )

        assert report.config_name == "Test Config"
        assert report.passed == True
        assert len(report.issues) == 0

    def test_add_critical_issue_fails_report(self):
        """Test that critical issue marks report as failed."""
        report = ConfigReviewReport(
            config_name="Test",
            overall_score=80.0,
            passed=True
        )

        report.add_issue(ReviewIssue(
            severity="critical",
            category="sql",
            message="Critical error"
        ))

        assert not report.passed

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        report = ConfigReviewReport(
            config_name="Test",
            overall_score=70.0,
            passed=True
        )

        report.add_issue(ReviewIssue(severity="critical", category="sql", message="Error 1"))
        report.add_issue(ReviewIssue(severity="high", category="sql", message="Error 2"))
        report.add_issue(ReviewIssue(severity="critical", category="joins", message="Error 3"))

        critical = report.get_issues_by_severity("critical")
        high = report.get_issues_by_severity("high")

        assert len(critical) == 2
        assert len(high) == 1


class TestConfigReviewAgent:
    """Test ConfigReviewAgent class."""

    def test_initialization(self, sample_tables):
        """Test agent initialization."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        assert len(agent.available_tables) == 2
        assert agent.min_sql_score == 70.0
        assert agent.min_instruction_score == 70.0

    def test_initialization_with_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        agent = ConfigReviewAgent(
            min_sql_score=80.0,
            min_instruction_score=75.0,
            strict_mode=True
        )

        assert agent.min_sql_score == 80.0
        assert agent.min_instruction_score == 75.0
        assert agent.strict_mode == True

    def test_review_minimal_config(self, sample_tables):
        """Test reviewing a minimal valid configuration."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test Space",
            "description": "A test Genie space for validation",
            "purpose": "Testing the review functionality",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                }
            ],
            "instructions": [],
            "example_sql_queries": [],
            "sql_expressions": [],
            "join_specifications": [],
            "benchmark_questions": []
        }

        report = agent.review_config(config, config_name="Test Space")

        assert report.config_name == "Test Space"
        assert isinstance(report.overall_score, float)

    def test_review_config_with_sql_errors(self, sample_tables):
        """Test review detects SQL errors."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test",
            "description": "Test config with SQL errors",
            "purpose": "Testing SQL validation",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                }
            ],
            "example_sql_queries": [
                {
                    "question": "Bad query",
                    "sql_query": "SELECT * FROM nonexistent_table"
                }
            ],
            "join_specifications": []
        }

        report = agent.review_config(config)

        sql_issues = [i for i in report.issues if i.category == "sql"]
        assert len(sql_issues) > 0

    def test_review_config_with_low_quality_instructions(self, sample_tables):
        """Test review detects low quality instructions."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test",
            "description": "Test config with poor instructions",
            "purpose": "Testing instruction quality",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                }
            ],
            "instructions": [
                {
                    "content": "Handle appropriately",  # Vague
                    "priority": 1
                }
            ],
            "join_specifications": []
        }

        report = agent.review_config(config)

        instruction_issues = [i for i in report.issues if i.category == "instructions"]
        assert len(instruction_issues) > 0

    def test_review_config_missing_joins(self, sample_tables):
        """Test review detects missing join specifications."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test",
            "description": "Test config with multiple tables",
            "purpose": "Testing join detection",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "customers"
                }
            ],
            "join_specifications": []  # Missing joins!
        }

        report = agent.review_config(config)

        join_issues = [i for i in report.issues if i.category == "joins"]
        assert len(join_issues) > 0
        assert any("No join specifications" in i.message for i in join_issues)

    def test_review_config_with_valid_joins(self, sample_tables):
        """Test review accepts valid join specifications."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test",
            "description": "Test config with valid joins",
            "purpose": "Testing join validation",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "customers"
                }
            ],
            "join_specifications": [
                {
                    "left_table": "main.retail.transactions",
                    "right_table": "main.retail.customers",
                    "join_type": "INNER",
                    "join_condition": "transactions.customer_id = customers.customer_id"
                }
            ]
        }

        report = agent.review_config(config)

        # Should have better join score
        assert report.join_completeness_score >= 80

    def test_review_config_low_coverage(self, sample_tables):
        """Test review detects low example/benchmark coverage."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Test",
            "description": "Test config with low coverage",
            "purpose": "Testing coverage detection",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "customers"
                }
            ],
            "example_sql_queries": [
                {
                    "question": "One query",
                    "sql_query": "SELECT COUNT(*) FROM main.retail.transactions"
                }
            ],
            "benchmark_questions": []  # No benchmarks
        }

        report = agent.review_config(config)

        coverage_issues = [i for i in report.issues if i.category == "coverage"]
        assert len(coverage_issues) > 0

    def test_review_config_missing_required_fields(self, sample_tables):
        """Test review detects missing required fields."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            # Missing space_name, description, purpose
            "tables": []
        }

        report = agent.review_config(config)

        structure_issues = [i for i in report.issues if i.category == "structure"]
        assert len(structure_issues) >= 3  # At least 3 missing required fields

    def test_review_config_passes_with_good_config(self, sample_tables):
        """Test that a good config passes review."""
        agent = ConfigReviewAgent(available_tables=sample_tables)

        config = {
            "space_name": "Excellent Test Space",
            "description": "A well-configured test Genie space with proper structure",
            "purpose": "Testing that high-quality configurations pass review",
            "tables": [
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "main",
                    "schema_name": "retail",
                    "table_name": "customers"
                }
            ],
            "join_specifications": [
                {
                    "left_table": "main.retail.transactions",
                    "right_table": "main.retail.customers",
                    "join_type": "INNER",
                    "join_condition": "transactions.customer_id = customers.customer_id"
                }
            ],
            "instructions": [
                {
                    "content": """## Date Handling
- Use `event_date` column for all date filters
- Default to **last 30 days**: `WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`
""",
                    "priority": 1
                }
            ],
            "example_sql_queries": [
                {
                    "question": "Top customers by revenue",
                    "sql_query": """
SELECT c.customer_name, SUM(t.amount) as revenue
FROM main.retail.transactions t
INNER JOIN main.retail.customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY revenue DESC
LIMIT 10
"""
                },
                {
                    "question": "Recent transactions",
                    "sql_query": """
SELECT * FROM main.retail.transactions
WHERE event_date >= DATE_SUB(CURRENT_DATE(), 7)
LIMIT 100
"""
                }
            ],
            "benchmark_questions": [
                {"question": "What are the top 10 customers?"},
                {"question": "How many transactions last week?"},
                {"question": "What is the total revenue?"},
                {"question": "Who are the new customers?"},
                {"question": "What is the average order value?"}
            ],
            "sql_expressions": [
                {
                    "name": "total_revenue",
                    "expression": "SUM(amount)",
                    "type": "metric"
                }
            ]
        }

        report = agent.review_config(config)

        # Should pass with good score
        assert report.overall_score >= 60  # At least passing
        # May have minor warnings but no critical issues
        critical = report.get_issues_by_severity("critical")
        assert len(critical) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
