"""Integration Domain Tests

End-to-end integration tests for the complete pipeline:
- Full workflow from requirements to deployment
- Multi-component integration
- Real file operations
- API integration tests
"""

import os
import pytest
from pathlib import Path
import json
import tempfile


# ============================================================================
# FULL PIPELINE INTEGRATION TESTS
# ============================================================================

class TestFullPipeline:
    """Tests for complete end-to-end pipeline."""
    
    def test_file_structure_requirements(self):
        """Test that required files exist for pipeline."""
        required_files = [
            "src/__init__.py",
            "src/models.py",
            "src/prompt/__init__.py",
            "src/prompt/prompt_builder.py",
            "src/llm/__init__.py",
            "src/llm/databricks_llm.py",
            "src/api/__init__.py",
            "src/api/genie_space_client.py",
            "src/pipeline/__init__.py",
            "src/pipeline/generator.py",
            "src/pipeline/validator.py",
            "src/pipeline/deployer.py",
            "genie.py",
            "requirements.txt",
            "README.md",
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            assert path.exists(), f"Missing required file: {file_path}"
    
    def test_output_directory_creation(self, output_dir):
        """Test that output directory is created properly."""
        assert output_dir.exists()
        assert output_dir.is_dir()
        
        # Test writing to output directory
        test_file = output_dir / "test_integration.json"
        test_file.write_text('{"test": true}')
        assert test_file.exists()
        
        # Cleanup
        test_file.unlink()
    
    @pytest.mark.skipif(
        os.getenv("SKIP_LLM_TESTS", "true").lower() == "true",
        reason="LLM tests disabled"
    )
    def test_parse_generate_validate_workflow(self):
        """Test parse → generate → validate workflow.
        
        Requires DATABRICKS_HOST and DATABRICKS_TOKEN.
        """
        if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
            pytest.skip("Databricks credentials not configured")
        
        from src.pipeline.parser import parse_requirements
        from src.pipeline.generator import generate_config
        from src.pipeline.validator import validate_config
        
        # Use demo requirements
        requirements_path = "data/demo_requirements.md"
        if not Path(requirements_path).exists():
            pytest.skip(f"Requirements not found: {requirements_path}")
        
        # Step 1: Parse (if PDF)
        # (Skip for markdown - already in correct format)
        
        # Step 2: Generate
        output_path = "output/test_integration_config.json"
        config_data = generate_config(
            requirements_path=requirements_path,
            output_path=output_path,
            max_tokens=24000,
            temperature=0.1,
            verbose=False
        )
        
        assert "genie_space_config" in config_data
        assert Path(output_path).exists()
        
        # Step 3: Validate
        validation_report = validate_config(output_path)
        
        assert validation_report is not None
        
        # Cleanup
        if Path(output_path).exists():
            Path(output_path).unlink()


# ============================================================================
# REQUIREMENTS TO CONFIG INTEGRATION
# ============================================================================

class TestRequirementsToConfig:
    """Tests for requirements → config conversion."""
    
    def test_extract_and_merge_examples(self, sample_requirements_file):
        """Test extracting examples and merging into config."""
        from src.extractor.example_extractor import (
            extract_sample_queries_as_examples,
            merge_examples_into_config_dict
        )
        
        # Extract examples
        examples = extract_sample_queries_as_examples(sample_requirements_file)
        assert len(examples) > 0
        
        # Create a basic config
        config_dict = {
            "space_name": "Test Space",
            "description": "Test",
            "purpose": "Testing",
            "tables": [
                {
                    "catalog_name": "demo",
                    "schema_name": "retail",
                    "table_name": "transactions"
                }
            ]
        }
        
        # Merge examples
        merged = merge_examples_into_config_dict(config_dict, examples)
        
        assert "example_sql_queries" in merged
        assert len(merged["example_sql_queries"]) > 0
    
    def test_extract_and_merge_benchmarks(self, sample_requirements_file):
        """Test extracting benchmarks and merging into config."""
        from src.benchmark.benchmark_extractor import extract_sample_queries_as_benchmarks
        
        # Extract benchmarks
        benchmarks = extract_sample_queries_as_benchmarks(sample_requirements_file)
        assert len(benchmarks) > 0
        
        # Benchmarks are already in the correct format for config
        # Just verify they have the required fields
        for bm in benchmarks:
            assert "question" in bm
            assert "expected_sql" in bm


# ============================================================================
# CONFIG TRANSFORMATION & VALIDATION INTEGRATION
# ============================================================================

class TestConfigTransformationValidation:
    """Tests for config transformation + validation workflow."""
    
    def test_transform_then_validate(self, sample_config):
        """Test transforming config and then validating."""
        from src.utils.config_transformer import transform_to_serialized_space
        from src.validation.table_validator import TableValidator
        
        # Transform
        config_dict = sample_config.model_dump()
        serialized_json = transform_to_serialized_space(config_dict)
        
        # serialized_json is a JSON string
        assert isinstance(serialized_json, str)
        serialized = json.loads(serialized_json)
        assert "version" in serialized
        assert "data_sources" in serialized
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump({"genie_space_config": config_dict}, f)
            temp_path = f.name
        
        try:
            # Validate (will check structure even without Databricks connection)
            validator = TableValidator(
                databricks_host="https://test.databricks.com",
                databricks_token="test-token"
            )
            
            report = validator.validate_config(temp_path)
            
            # Report should be generated (even if tables don't exist)
            assert report is not None
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_catalog_replacement_then_validate(self, temp_config_file):
        """Test catalog replacement followed by validation."""
        from src.utils.config_transformer import update_config_catalog_schema
        from src.validation.table_validator import TableValidator
        
        # Replace catalog.schema
        counts = update_config_catalog_schema(
            temp_config_file,
            old_catalog="demo",
            old_schema="retail",
            new_catalog="sandbox",
            new_schema="test"
        )
        
        assert counts is not None
        
        # Validate updated config
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="test-token"
        )
        
        report = validator.validate_config(temp_config_file)
        assert report is not None


# ============================================================================
# API INTEGRATION TESTS
# ============================================================================

class TestAPIIntegration:
    """Tests for Databricks API integration."""
    
    @pytest.mark.skipif(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        reason="Databricks credentials not configured"
    )
    def test_databricks_endpoint_connectivity(self):
        """Test connection to Databricks serving endpoint."""
        from src.llm.databricks_llm import DatabricksLLM
        
        llm = DatabricksLLM(
            model_name="databricks-meta-llama-3-1-405b-instruct"
        )
        
        # Test simple completion
        response = llm.complete("Hello, reply with 'test successful'")
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.skipif(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        reason="Databricks credentials not configured"
    )
    def test_unity_catalog_table_query(self):
        """Test querying Unity Catalog for table information."""
        from src.validation.table_validator import TableValidator
        
        validator = TableValidator()
        
        # Try to validate a common catalog
        # (This may fail if catalog doesn't exist, which is expected)
        schema = validator.get_table_schema(
            catalog_name="main",
            schema_name="default",
            table_name="test"
        )
        
        # We just test that the API call completes without errors
        # Schema may be None if table doesn't exist
        assert schema is None or isinstance(schema, dict)
    
    @pytest.mark.skipif(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        reason="Databricks credentials not configured"
    )
    def test_genie_space_api_list(self):
        """Test listing Genie spaces via API."""
        from src.api.genie_space_client import GenieSpaceClient
        
        client = GenieSpaceClient()
        
        # List spaces (may be empty, that's ok)
        spaces = client.list_spaces(max_results=5)
        
        assert isinstance(spaces, list)


# ============================================================================
# BENCHMARK LOADING INTEGRATION
# ============================================================================

class TestBenchmarkLoadingIntegration:
    """Tests for benchmark loading from various sources."""
    
    def test_load_benchmarks_auto_detection(self):
        """Test automatic benchmark loading from directory."""
        from src.benchmark.benchmark_loader import load_benchmarks_auto
        
        # Try loading from real_requirements if it exists
        if Path("real_requirements/benchmarks").exists():
            benchmarks = load_benchmarks_auto("real_requirements/benchmarks")
            assert isinstance(benchmarks, list)
    
    def test_load_benchmarks_from_json(self):
        """Test loading benchmarks from JSON file."""
        from src.benchmark.benchmark_loader import load_benchmarks_from_json
        
        # Create temp benchmark file with proper structure
        test_data = {
            "benchmarks": [
                {
                    "question": "What is the total revenue?",
                    "expected_sql": "SELECT SUM(amount) FROM transactions"
                },
                {
                    "question": "How many customers?",
                    "expected_sql": "SELECT COUNT(*) FROM customers"
                }
            ],
            "metadata": {
                "total_count": 2
            }
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            benchmarks = load_benchmarks_from_json(temp_path, verbose=False)
            assert len(benchmarks) == 2
            assert all("question" in bm for bm in benchmarks)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# ERROR HANDLING INTEGRATION
# ============================================================================

class TestErrorHandling:
    """Tests for error handling across components."""
    
    def test_missing_requirements_file(self):
        """Test handling of missing requirements file."""
        from src.prompt.prompt_builder import PromptBuilder
        
        with pytest.raises((FileNotFoundError, Exception)):
            builder = PromptBuilder(
                context_doc_path="src/prompt/templates/curate_effective_genie.md",
                output_doc_path="src/prompt/templates/genie_api.md",
                input_data_path="nonexistent_requirements.md"
            )
            builder.build_prompt()
    
    def test_invalid_config_json(self):
        """Test handling of invalid JSON config."""
        from src.validation.table_validator import TableValidator
        
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            validator = TableValidator(
                databricks_host="https://test.databricks.com",
                databricks_token="test-token"
            )
            
            # Should raise exception for invalid JSON
            with pytest.raises(Exception):
                report = validator.validate_config(temp_path)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_missing_config_file(self):
        """Test handling of missing config file."""
        from src.validation.table_validator import TableValidator
        
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="test-token"
        )
        
        report = validator.validate_config("nonexistent_config.json")
        
        assert report.has_errors()
        assert any("not found" in issue.message for issue in report.issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
