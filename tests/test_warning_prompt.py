"""
Test that warnings prompt user for fixes.

This test verifies the interactive warning flow for benchmark validation.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.utils.table_validator import TableValidator, ValidationReport


class TestWarningPromptFlow:
    """Test interactive prompting for warnings."""

    @patch('src.utils.table_validator.requests.get')
    def test_benchmark_warnings_are_detectable(self, mock_get):
        """Test that benchmark table warnings are properly detected."""
        # Create test configuration with valid and invalid benchmark tables
        config = {
            "genie_space_config": {
                "tables": [
                    {
                        "catalog_name": "demo",
                        "schema_name": "retail",
                        "table_name": "transactions"
                    }
                ],
                "benchmark_questions": [
                    {
                        "question": "Valid query",
                        "expected_sql": "SELECT * FROM demo.retail.transactions;"
                    },
                    {
                        "question": "Invalid query",
                        "expected_sql": "SELECT * FROM demo.retail.nonexistent_table;"
                    }
                ]
            }
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            # Mock API responses - transactions exists, nonexistent_table does not
            def get_side_effect(*args, **kwargs):
                mock_response = Mock()
                if "transactions" in args[0]:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "full_name": "demo.retail.transactions",
                        "columns": [{"name": "id", "type_text": "INT"}]
                    }
                else:
                    mock_response.status_code = 404
                return mock_response

            mock_get.side_effect = get_side_effect

            # Run validation
            validator = TableValidator(
                databricks_host="https://test.databricks.com",
                databricks_token="token"
            )

            report = validator.validate_config(config_path)

            # Verify we have warnings
            assert report.has_warnings()

            # Find table_reference_invalid warnings
            invalid_table_warnings = [
                issue for issue in report.issues
                if issue.type == "table_reference_invalid" and issue.severity == "warning"
            ]

            assert len(invalid_table_warnings) > 0

            # Verify the warning has table information
            warning = invalid_table_warnings[0]
            assert warning.table is not None
            assert "nonexistent_table" in warning.table
            assert "benchmark" in warning.location.lower()

        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_prompt_replacement_handles_warnings(self):
        """Test that prompt_catalog_schema_replacement can handle warnings."""
        from genie import prompt_catalog_schema_replacement

        # Create a mock report with warnings
        report = ValidationReport()
        report.add_issue(
            severity="warning",
            type="table_reference_invalid",
            message="Benchmark question references invalid table",
            table="demo.retail.invalid_table",
            location="benchmark_questions[Test question]"
        )

        # Create a test config file
        config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "demo", "schema_name": "retail", "table_name": "valid"}
                ],
                "benchmark_questions": [
                    {
                        "question": "Test question",
                        "expected_sql": "SELECT * FROM demo.retail.invalid_table;"
                    }
                ]
            }
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            # Mock user input to cancel
            with patch('builtins.input', return_value='3'):
                result = prompt_catalog_schema_replacement(report, config_path)
                # Should return False because user chose to cancel
                assert result == False

        finally:
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
