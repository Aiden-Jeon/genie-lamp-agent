"""Generation Domain Tests

Consolidates all tests related to configuration generation:
- Prompt building
- Config generation pipeline
- LLM integration
- Config review
- Instruction scoring
"""

import os
import pytest
from pathlib import Path
from src.prompt.prompt_builder import PromptBuilder
from src.models import GenieSpaceConfig, GenieSpaceInstruction
from src.pipeline.reviewer import (
    ConfigReviewAgent,
    ReviewIssue,
    ConfigReviewReport
)
from src.validation.instruction_scorer import InstructionQualityScorer


# ============================================================================
# PROMPT BUILDING TESTS
# ============================================================================

class TestPromptBuilding:
    """Tests for prompt construction."""
    
    def test_prompt_builder_initialization(self):
        """Test prompt builder initialization."""
        builder = PromptBuilder(
            context_doc_path="src/prompt/templates/curate_effective_genie.md",
            output_doc_path="src/prompt/templates/genie_api.md",
            input_data_path="data/demo_requirements.md"
        )
        assert builder is not None
    
    def test_build_basic_prompt(self):
        """Test building a basic prompt."""
        builder = PromptBuilder(
            context_doc_path="src/prompt/templates/curate_effective_genie.md",
            output_doc_path="src/prompt/templates/genie_api.md",
            input_data_path="data/demo_requirements.md"
        )
        
        prompt = builder.build_prompt()
        
        assert len(prompt) > 1000, "Prompt should be substantial"
        assert "Instruction" in prompt
        assert "Context" in prompt
        assert "Output" in prompt
        assert "Input" in prompt
    
    def test_prompt_with_reasoning(self):
        """Test prompt includes reasoning structure."""
        builder = PromptBuilder(
            context_doc_path="src/prompt/templates/curate_effective_genie.md",
            output_doc_path="src/prompt/templates/genie_api.md",
            input_data_path="data/demo_requirements.md"
        )
        
        prompt = builder.build_prompt()
        
        assert "reasoning" in prompt
        assert "confidence_score" in prompt


# ============================================================================
# CONFIG GENERATION TESTS
# ============================================================================

class TestConfigGeneration:
    """Tests for configuration generation pipeline."""
    
    def test_model_validation(self):
        """Test Pydantic model validation."""
        config_data = {
            "space_name": "Test Space",
            "description": "A test space",
            "purpose": "Testing purposes",
            "tables": [
                {
                    "catalog_name": "test_catalog",
                    "schema_name": "test_schema",
                    "table_name": "test_table"
                }
            ],
            "instructions": [
                {
                    "content": "Test instruction",
                    "priority": 1
                }
            ],
            "example_sql_queries": [
                {
                    "question": "What is the total?",
                    "sql_query": "SELECT SUM(amount) FROM table"
                }
            ],
            "sql_expressions": [
                {
                    "name": "total_revenue",
                    "expression": "SUM(amount)",
                    "type": "metric"
                }
            ],
            "benchmark_questions": [
                {
                    "question": "What is the total revenue?"
                }
            ]
        }
        
        config = GenieSpaceConfig(**config_data)
        
        assert config.space_name == "Test Space"
        assert len(config.tables) == 1
        assert len(config.instructions) == 1
    
    def test_json_serialization(self):
        """Test model JSON serialization."""
        config_data = {
            "space_name": "Test Space",
            "description": "Test description",
            "purpose": "Testing",
            "tables": [
                {
                    "catalog_name": "test_catalog",
                    "schema_name": "test_schema",
                    "table_name": "test_table"
                }
            ]
        }
        
        config = GenieSpaceConfig(**config_data)
        json_str = config.model_dump_json(indent=2)
        
        assert "test_catalog" in json_str
        assert isinstance(json_str, str)
    
    @pytest.mark.skipif(
        os.getenv("SKIP_LLM_TESTS", "true").lower() == "true",
        reason="LLM tests disabled (SKIP_LLM_TESTS=true)"
    )
    def test_full_generation_pipeline(self):
        """Test complete generation pipeline with LLM.
        
        Requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables.
        """
        if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
            pytest.skip("Databricks credentials not configured")
        
        from src.pipeline.generator import generate_config
        
        requirements_path = "data/demo_requirements.md"
        if not Path(requirements_path).exists():
            pytest.skip(f"Requirements not found: {requirements_path}")
        
        output_path = "output/test_generation_config.json"
        
        config_data = generate_config(
            requirements_path=requirements_path,
            output_path=output_path,
            max_tokens=24000,
            temperature=0.1,
            verbose=False
        )
        
        # Verify structure
        assert "genie_space_config" in config_data
        config = config_data["genie_space_config"]
        
        # Verify required fields
        assert "space_name" in config
        assert "tables" in config
        assert len(config["tables"]) > 0
        
        # Cleanup
        if Path(output_path).exists():
            Path(output_path).unlink()


# ============================================================================
# CONFIG REVIEW TESTS
# ============================================================================

class TestConfigReview:
    """Tests for configuration review agent."""
    
    def test_review_issue_creation(self):
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
    
    def test_review_report_initialization(self):
        """Test review report initialization."""
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
    
    def test_filter_issues_by_severity(self):
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
    
    def test_review_agent_initialization(self, sample_tables):
        """Test review agent initialization."""
        agent = ConfigReviewAgent(available_tables=sample_tables)
        assert agent is not None
        assert len(agent.available_tables) == len(sample_tables)
    
    def test_review_sql_quality(self, sample_tables):
        """Test SQL quality review."""
        agent = ConfigReviewAgent(available_tables=sample_tables)
        
        # Create a config with good SQL
        good_config = {
            "example_sql_queries": [
                {
                    "question": "Total sales by customer",
                    "sql_query": "SELECT customer_id, SUM(amount) FROM demo.retail.transactions GROUP BY customer_id"
                }
            ]
        }
        report = agent.review_config(good_config)
        critical_issues = report.get_issues_by_severity("critical")
        assert len(critical_issues) == 0
        
        # Create a config with bad SQL (SELECT *)
        bad_config = {
            "example_sql_queries": [
                {
                    "question": "All transactions",
                    "sql_query": "SELECT * FROM demo.retail.transactions"
                }
            ]
        }
        report = agent.review_config(bad_config)
        # Should have warnings about SELECT *
        assert len(report.issues) > 0
    
    def test_review_instructions(self, sample_tables):
        """Test instruction review."""
        agent = ConfigReviewAgent(available_tables=sample_tables)
        
        # Create a config with instructions
        config = {
            "instructions": [
                {
                    "content": "Use demo.retail.transactions for sales data",
                    "priority": 1
                },
                {
                    "content": "Join with customers on customer_id",
                    "priority": 2
                }
            ]
        }
        
        report = agent.review_config(config)
        assert isinstance(report, ConfigReviewReport)


# ============================================================================
# INSTRUCTION SCORING TESTS
# ============================================================================

class TestInstructionScoring:
    """Tests for instruction quality scoring."""
    
    def test_scorer_initialization(self):
        """Test instruction scorer initialization."""
        scorer = InstructionQualityScorer()
        assert scorer is not None
    
    def test_score_clear_instruction(self):
        """Test scoring a clear, well-written instruction."""
        scorer = InstructionQualityScorer()
        
        content = "Always use demo.retail.transactions for sales data. Join with demo.retail.customers on customer_id for customer information."
        
        score = scorer.score_instruction(content, priority=1)
        
        assert score.total_score >= 70, "Clear instruction should score high"
    
    def test_score_vague_instruction(self):
        """Test scoring a vague instruction."""
        scorer = InstructionQualityScorer()
        
        content = "Use tables"  # Too vague
        
        score = scorer.score_instruction(content, priority=1)
        
        assert score.total_score < 50, "Vague instruction should score low"
    
    def test_score_with_specific_examples(self):
        """Test that instructions with examples score higher."""
        scorer = InstructionQualityScorer()
        
        # Instruction with example
        with_example = "For revenue calculations, use SUM(amount) from transactions table. Example: SELECT SUM(amount) FROM demo.retail.transactions"
        
        # Instruction without example
        without_example = "For revenue calculations, use the amount field"
        
        score_with = scorer.score_instruction(with_example, priority=1)
        score_without = scorer.score_instruction(without_example, priority=1)
        
        assert score_with.total_score > score_without.total_score, "Instruction with example should score higher"
    
    def test_score_batch_instructions(self):
        """Test scoring multiple instructions."""
        scorer = InstructionQualityScorer()
        
        # Create config with instructions
        config = {
            "instructions": [
                {
                    "content": "Use demo.retail.transactions for all sales queries",
                    "priority": 1
                },
                {
                    "content": "Join customers table on customer_id",
                    "priority": 2
                },
                {
                    "content": "Use data",  # Vague
                    "priority": 3
                }
            ]
        }
        
        report = scorer.score_config_instructions(config)
        
        assert report.total_instructions == 3
        assert len(report.instruction_scores) == 3
        assert all(0 <= score.total_score <= 100 for score in report.instruction_scores)
        
        # First two should score higher than the vague one
        assert report.instruction_scores[0].total_score > report.instruction_scores[2].total_score
        assert report.instruction_scores[1].total_score > report.instruction_scores[2].total_score


# ============================================================================
# FILE STRUCTURE TESTS
# ============================================================================

class TestFileStructure:
    """Tests for required file structure."""
    
    def test_required_files_exist(self):
        """Test that all required files exist."""
        required_files = [
            "src/__init__.py",
            "src/models.py",
            "src/prompt/__init__.py",
            "src/prompt/prompt_builder.py",
            "src/llm/__init__.py",
            "src/llm/databricks_llm.py",
            "src/api/__init__.py",
            "src/api/genie_space_client.py",
            "src/utils/__init__.py",
            "genie.py",
            "requirements.txt",
            "README.md",
            "src/prompt/templates/curate_effective_genie.md",
            "src/prompt/templates/genie_api.md",
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            assert path.exists(), f"Missing required file: {file_path}"
    
    def test_output_directory(self, output_dir):
        """Test that output directory exists."""
        assert output_dir.exists(), "Output directory should exist"
        assert output_dir.is_dir(), "Output should be a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
