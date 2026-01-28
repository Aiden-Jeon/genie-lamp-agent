"""Tests for instruction quality scorer."""

import pytest
from src.utils.instruction_scorer import (
    InstructionQualityScorer,
    InstructionScore,
    ConfigInstructionQualityReport,
    generate_instruction_improvement_suggestions
)


class TestInstructionQualityScorer:
    """Test InstructionQualityScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create a scorer instance."""
        return InstructionQualityScorer()

    def test_scorer_initialization(self, scorer):
        """Test scorer initializes correctly."""
        assert scorer is not None
        assert len(scorer.VAGUE_TERMS) > 0
        assert len(scorer.SPECIFICITY_PATTERNS) > 0

    def test_score_vague_instruction(self, scorer):
        """Test scoring of vague instruction."""
        vague_instruction = "Handle dates appropriately and use relevant tables."

        score = scorer.score_instruction(vague_instruction)

        # Should score poorly due to vague terms and lack of specificity
        assert score.total_score < 60
        assert score.specificity_score < 20
        assert any("vague" in issue.lower() for issue in score.issues)

    def test_score_specific_instruction(self, scorer):
        """Test scoring of specific, well-formatted instruction."""
        good_instruction = """## Date Handling Rules

- Always use `event_date` column for date filters
- Default to **last 30 days** when time range not specified
- Use `CURRENT_DATE()` for "today"
- Use `DATE_SUB(CURRENT_DATE(), 30)` for "last 30 days"

Example:
`WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`
"""

        score = scorer.score_instruction(good_instruction)

        # Should score high
        assert score.total_score >= 70
        assert score.specificity_score > 20
        assert score.structure_score > 15
        assert score.clarity_score > 20

    def test_score_no_markdown_structure(self, scorer):
        """Test scoring instruction without markdown structure."""
        plain_instruction = "Use the event_date column for all date-based queries."

        score = scorer.score_instruction(plain_instruction)

        # Should lose structure points
        assert score.structure_score < 15
        assert any("markdown" in suggestion.lower() for suggestion in score.suggestions)

    def test_score_with_column_references(self, scorer):
        """Test scoring recognizes column references."""
        instruction = "Filter by `status` column where `status != 'cancelled'`"

        score = scorer.score_instruction(instruction)

        # Should get specificity points for column references
        assert score.specificity_score >= 10

    def test_score_with_table_references(self, scorer):
        """Test scoring recognizes table references."""
        instruction = "Join `main.retail.transactions` to `main.retail.customers` using `customer_id`"

        score = scorer.score_instruction(instruction)

        # Should get high specificity points
        assert score.specificity_score > 15

    def test_score_with_sql_keywords(self, scorer):
        """Test scoring recognizes SQL keywords."""
        instruction = "Use `SELECT DISTINCT` for unique values and `GROUP BY` for aggregations"

        score = scorer.score_instruction(instruction)

        # Should get specificity points
        assert score.specificity_score >= 10

    def test_score_with_headers(self, scorer):
        """Test scoring recognizes markdown headers."""
        instruction = """## Data Filtering
Use event_date column for dates.

## Aggregation Rules
Use COUNT(DISTINCT customer_id) for unique customers.
"""

        score = scorer.score_instruction(instruction)

        # Should get structure points for headers
        assert score.structure_score >= 10

    def test_score_with_bullet_lists(self, scorer):
        """Test scoring recognizes bullet lists."""
        instruction = """Rules:
- Filter by date
- Use INNER JOIN
- Group by customer_id
"""

        score = scorer.score_instruction(instruction)

        # Should get structure points for lists
        assert score.structure_score >= 8

    def test_score_with_bold_text(self, scorer):
        """Test scoring recognizes bold emphasis."""
        instruction = "Always use **last 30 days** as the default time range."

        score = scorer.score_instruction(instruction)

        # Should get structure points for emphasis
        assert score.structure_score > 0

    def test_score_vague_terms_detected(self, scorer):
        """Test that vague terms are detected."""
        vague_instruction = "Handle dates appropriately and use relevant filters when necessary."

        score = scorer.score_instruction(vague_instruction)

        # Should detect multiple vague terms
        assert score.clarity_score < 25
        assert any("vague" in issue.lower() for issue in score.issues)

    def test_score_action_verbs(self, scorer):
        """Test that action verbs improve clarity score."""
        active_instruction = "Use event_date column. Filter by status. Join to customers table."

        score = scorer.score_instruction(active_instruction)

        # Should not lose points for lack of action verbs
        assert score.clarity_score >= 20

    def test_score_very_short_instruction(self, scorer):
        """Test scoring of very short instruction."""
        short = "Use dates."

        score = scorer.score_instruction(short)

        # Should have issues about being too short
        assert any("short" in issue.lower() for issue in score.issues)

    def test_score_very_long_instruction(self, scorer):
        """Test scoring of very long instruction."""
        long = " ".join(["This is a very long instruction."] * 100)

        score = scorer.score_instruction(long)

        # Should have issues about being too long
        assert any("long" in issue.lower() for issue in score.issues)

    def test_score_grade_assignment(self, scorer):
        """Test letter grade assignment."""
        # Create instructions with different quality levels
        excellent = """## Date Handling
- Use `event_date` column
- Apply `WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`
- Filter `status != 'cancelled'`
"""

        poor = "Handle appropriately."

        excellent_score = scorer.score_instruction(excellent)
        poor_score = scorer.score_instruction(poor)

        assert excellent_score.grade() in ['A', 'B', 'C']
        assert poor_score.grade() in ['D', 'F']

    def test_score_config_instructions(self, scorer):
        """Test scoring all instructions in a config."""
        config = {
            "instructions": [
                {
                    "content": """## Date Handling
- Use `event_date` column
- Default to **last 30 days**
""",
                    "priority": 1
                },
                {
                    "content": "Handle appropriately.",
                    "priority": 2
                },
                {
                    "content": """Use `customer_id` for joins:
`JOIN customers ON transactions.customer_id = customers.customer_id`
""",
                    "priority": 1
                }
            ]
        }

        report = scorer.score_config_instructions(config)

        assert report.total_instructions == 3
        assert report.average_score > 0
        assert report.high_quality_count + report.medium_quality_count + report.low_quality_count == 3

    def test_critical_instruction_priority(self, scorer):
        """Test that critical (priority 1) instructions get flagged if low quality."""
        critical_vague = "Handle dates appropriately."

        score = scorer.score_instruction(critical_vague, priority=1)

        # Should have issue about critical instruction being low quality
        if score.total_score < 80:
            assert any("priority 1" in issue.lower() or "critical" in issue.lower() for issue in score.issues)


class TestInstructionScore:
    """Test InstructionScore dataclass."""

    def test_score_creation(self):
        """Test creating an InstructionScore."""
        score = InstructionScore(
            content="Test instruction",
            total_score=85.0,
            specificity_score=35.0,
            structure_score=25.0,
            clarity_score=25.0,
            issues=[],
            suggestions=[]
        )

        assert score.total_score == 85.0
        assert score.grade() == "B"

    def test_grade_ranges(self):
        """Test letter grade ranges."""
        scores_and_grades = [
            (95, "A"),
            (85, "B"),
            (75, "C"),
            (65, "D"),
            (55, "F"),
        ]

        for score_value, expected_grade in scores_and_grades:
            score = InstructionScore(
                content="Test",
                total_score=score_value,
                specificity_score=0,
                structure_score=0,
                clarity_score=0
            )
            assert score.grade() == expected_grade


class TestConfigInstructionQualityReport:
    """Test ConfigInstructionQualityReport dataclass."""

    def test_report_creation(self):
        """Test creating a quality report."""
        scores = [
            InstructionScore("Test 1", 90, 35, 30, 25),
            InstructionScore("Test 2", 70, 25, 25, 20),
            InstructionScore("Test 3", 50, 15, 20, 15),
        ]

        report = ConfigInstructionQualityReport(
            instruction_scores=scores,
            average_score=70.0,
            total_instructions=3,
            high_quality_count=1,
            medium_quality_count=1,
            low_quality_count=1
        )

        assert report.total_instructions == 3
        assert report.high_quality_count == 1
        assert report.medium_quality_count == 1
        assert report.low_quality_count == 1

    def test_summary_format(self):
        """Test summary string formatting."""
        scores = [
            InstructionScore("Test", 85, 30, 30, 25)
        ]

        report = ConfigInstructionQualityReport(
            instruction_scores=scores,
            average_score=85.0,
            total_instructions=1,
            high_quality_count=1,
            medium_quality_count=0,
            low_quality_count=0
        )

        summary = report.summary()
        assert "Total Instructions: 1" in summary
        assert "Average Score: 85.0" in summary
        assert "High Quality (≥80): 1" in summary


class TestImprovementSuggestions:
    """Test improvement suggestion generation."""

    def test_high_quality_instruction(self):
        """Test suggestions for high-quality instruction."""
        score = InstructionScore(
            content="Good instruction",
            total_score=85.0,
            specificity_score=35.0,
            structure_score=25.0,
            clarity_score=25.0
        )

        suggestions = generate_instruction_improvement_suggestions(score)

        assert "High quality" in suggestions

    def test_low_quality_instruction(self):
        """Test suggestions for low-quality instruction."""
        score = InstructionScore(
            content="Poor instruction",
            total_score=45.0,
            specificity_score=10.0,
            structure_score=15.0,
            clarity_score=20.0,
            issues=["Too vague", "No structure"],
            suggestions=["Add column names", "Use markdown"]
        )

        suggestions = generate_instruction_improvement_suggestions(score)

        assert "Issues:" in suggestions
        assert "Suggestions:" in suggestions
        assert "Too vague" in suggestions
        assert "Add column names" in suggestions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
