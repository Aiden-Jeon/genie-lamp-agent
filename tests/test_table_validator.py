"""
Unit tests for the table validator module.

These tests verify the validation logic without making actual API calls.
For integration tests that connect to Databricks, use a separate test suite.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.table_validator import (
    TableValidator,
    ValidationReport,
    ValidationIssue
)


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""
    
    def test_create_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            severity="error",
            type="table_not_found",
            message="Table does not exist",
            table="catalog.schema.table"
        )
        
        assert issue.severity == "error"
        assert issue.type == "table_not_found"
        assert issue.message == "Table does not exist"
        assert issue.table == "catalog.schema.table"


class TestValidationReport:
    """Tests for ValidationReport class."""
    
    def test_report_initialization(self):
        """Test initializing an empty report."""
        report = ValidationReport()
        
        assert report.tables_checked == []
        assert report.tables_valid == []
        assert report.tables_invalid == []
        assert report.issues == []
    
    def test_add_issue(self):
        """Test adding issues to a report."""
        report = ValidationReport()
        
        report.add_issue(
            severity="error",
            type="table_not_found",
            message="Table missing",
            table="catalog.schema.table"
        )
        
        assert len(report.issues) == 1
        assert report.issues[0].severity == "error"
        assert report.issues[0].table == "catalog.schema.table"
    
    def test_has_errors(self):
        """Test checking for errors."""
        report = ValidationReport()
        
        assert not report.has_errors()
        
        report.add_issue("warning", "test", "test warning")
        assert not report.has_errors()
        
        report.add_issue("error", "test", "test error")
        assert report.has_errors()
    
    def test_has_warnings(self):
        """Test checking for warnings."""
        report = ValidationReport()
        
        assert not report.has_warnings()
        
        report.add_issue("info", "test", "test info")
        assert not report.has_warnings()
        
        report.add_issue("warning", "test", "test warning")
        assert report.has_warnings()
    
    def test_summary_format(self):
        """Test summary output format."""
        report = ValidationReport()
        report.tables_checked = ["table1", "table2"]
        report.tables_valid = ["table1"]
        report.tables_invalid = ["table2"]
        report.add_issue("error", "table_not_found", "Table 2 not found", table="table2")
        
        summary = report.summary()
        
        assert "TABLE & COLUMN VALIDATION REPORT" in summary
        assert "Tables Checked: 2" in summary
        assert "Valid:   1" in summary
        assert "Invalid: 1" in summary
        assert "VALIDATION FAILED" in summary


class TestTableValidator:
    """Tests for TableValidator class."""
    
    def test_initialization_with_env_vars(self):
        """Test initializing validator with environment variables."""
        with patch.dict('os.environ', {
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'test-token'
        }):
            validator = TableValidator()
            
            assert validator.databricks_host == "https://test.databricks.com"
            assert validator.databricks_token == "test-token"
    
    def test_initialization_with_explicit_values(self):
        """Test initializing validator with explicit values."""
        validator = TableValidator(
            databricks_host="https://custom.databricks.com",
            databricks_token="custom-token"
        )
        
        assert validator.databricks_host == "https://custom.databricks.com"
        assert validator.databricks_token == "custom-token"
    
    def test_initialization_missing_credentials(self):
        """Test that missing credentials raise an error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="databricks_host"):
                TableValidator()
    
    def test_host_url_normalization(self):
        """Test that host URL is normalized correctly."""
        # Without protocol
        validator = TableValidator(
            databricks_host="test.databricks.com",
            databricks_token="token"
        )
        assert validator.databricks_host == "https://test.databricks.com"
        
        # With protocol
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        assert validator.databricks_host == "https://test.databricks.com"
        
        # With trailing slash
        validator = TableValidator(
            databricks_host="https://test.databricks.com/",
            databricks_token="token"
        )
        assert validator.databricks_host == "https://test.databricks.com"
    
    def test_extract_columns_from_sql(self):
        """Test extracting column references from SQL."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        sql = "SELECT t.customer_id, t.total_amount, a.product_name FROM transactions t"
        alias_map = {
            "t": "catalog.schema.transactions",
            "a": "catalog.schema.articles"
        }
        
        columns = validator.extract_columns_from_sql(sql, alias_map)
        
        assert "catalog.schema.transactions.customer_id" in columns
        assert "catalog.schema.transactions.total_amount" in columns
        assert "catalog.schema.articles.product_name" in columns
    
    def test_extract_columns_filters_keywords(self):
        """Test that SQL keywords are filtered out."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        sql = "SELECT CURRENT_DATE, DATE_TRUNC('day', t.date), COUNT(*)"
        alias_map = {"t": "catalog.schema.table"}
        
        columns = validator.extract_columns_from_sql(sql, alias_map)
        
        # Should extract t.date but not CURRENT_DATE or DATE_TRUNC
        assert "catalog.schema.table.date" in columns
        assert len(columns) == 1
    
    def test_extract_tables_from_sql(self):
        """Test extracting table names from SQL."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        sql = """
        SELECT * FROM catalog1.schema1.table1 t1
        JOIN catalog2.schema2.table2 t2 ON t1.id = t2.id
        """
        
        tables = validator._extract_tables_from_sql(sql)
        
        assert "catalog1.schema1.table1" in tables
        assert "catalog2.schema2.table2" in tables
    
    def test_build_alias_map(self):
        """Test building alias map from configuration."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        genie_config = {
            "tables": [
                {
                    "catalog_name": "demo",
                    "schema_name": "retail",
                    "table_name": "transactions"
                },
                {
                    "catalog_name": "demo",
                    "schema_name": "retail",
                    "table_name": "articles"
                }
            ]
        }
        
        alias_map = validator._build_alias_map(genie_config)
        
        assert "t" in alias_map
        assert alias_map["t"] == "demo.retail.transactions"
        assert "a" in alias_map
        assert alias_map["a"] == "demo.retail.articles"
    
    @patch('src.table_validator.requests.get')
    def test_get_table_schema_success(self, mock_get):
        """Test getting table schema successfully."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "catalog.schema.table",
            "columns": [
                {"name": "id", "type_text": "INT"},
                {"name": "name", "type_text": "STRING"}
            ]
        }
        mock_get.return_value = mock_response
        
        schema = validator.get_table_schema("catalog", "schema", "table")
        
        assert schema is not None
        assert schema["full_name"] == "catalog.schema.table"
        assert len(schema["columns"]) == 2
    
    @patch('src.table_validator.requests.get')
    def test_get_table_schema_not_found(self, mock_get):
        """Test getting schema for non-existent table."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        schema = validator.get_table_schema("catalog", "schema", "nonexistent")
        
        assert schema is None
    
    @patch('src.table_validator.requests.get')
    def test_validate_table(self, mock_get):
        """Test validating table existence."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"full_name": "catalog.schema.table"}
        mock_get.return_value = mock_response
        
        assert validator.validate_table("catalog", "schema", "table") is True
    
    @patch('src.table_validator.requests.get')
    def test_validate_columns(self, mock_get):
        """Test validating columns in a table."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        # Mock table schema with columns
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "catalog.schema.table",
            "columns": [
                {"name": "customer_id", "type_text": "STRING"},
                {"name": "transaction_date", "type_text": "DATE"},
                {"name": "amount", "type_text": "DECIMAL"}
            ]
        }
        mock_get.return_value = mock_response
        
        results = validator.validate_columns(
            "catalog", "schema", "table",
            ["customer_id", "amount", "nonexistent"]
        )
        
        assert results["customer_id"] is True
        assert results["amount"] is True
        assert results["nonexistent"] is False
    
    def test_validate_config_missing_file(self):
        """Test validating a non-existent config file."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        report = validator.validate_config("nonexistent.json")
        
        assert report.has_errors()
        assert any("not found" in issue.message for issue in report.issues)


class TestIntegration:
    """Integration tests (require mock environment setup)."""
    
    @patch('src.table_validator.requests.get')
    def test_full_validation_workflow(self, mock_get):
        """Test complete validation workflow with mocked API."""
        # Create a temporary config file
        config = {
            "genie_space_config": {
                "tables": [
                    {
                        "catalog_name": "demo",
                        "schema_name": "retail",
                        "table_name": "transactions"
                    }
                ],
                "sql_expressions": [
                    {
                        "name": "revenue",
                        "expression": "SUM(t.total_amount)"
                    }
                ]
            }
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            # Mock API responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "full_name": "demo.retail.transactions",
                "columns": [
                    {"name": "total_amount", "type_text": "DECIMAL"}
                ]
            }
            mock_get.return_value = mock_response
            
            # Run validation
            validator = TableValidator(
                databricks_host="https://test.databricks.com",
                databricks_token="token"
            )
            
            report = validator.validate_config(config_path)
            
            # Verify results
            assert "demo.retail.transactions" in report.tables_checked
            assert "demo.retail.transactions" in report.tables_valid
            assert not report.has_errors()
        
        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
