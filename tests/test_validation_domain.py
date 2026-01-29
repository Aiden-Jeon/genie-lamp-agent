"""Validation Domain Tests

Consolidates all tests related to validation:
- Table validation (Unity Catalog)
- SQL validation
- Join validation
- Column validation
- Benchmark validation
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.validation.table_validator import (
    TableValidator,
    ValidationReport,
    ValidationIssue
)
from src.validation.sql_validator import SQLValidator


# ============================================================================
# VALIDATION ISSUE & REPORT TESTS
# ============================================================================

class TestValidationInfrastructure:
    """Tests for validation infrastructure (issues, reports)."""
    
    def test_create_validation_issue(self):
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
    
    def test_validation_report_initialization(self):
        """Test initializing an empty report."""
        report = ValidationReport()
        
        assert report.tables_checked == []
        assert report.tables_valid == []
        assert report.tables_invalid == []
        assert report.issues == []
    
    def test_add_issue_to_report(self):
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
    
    def test_report_has_errors(self):
        """Test checking for errors in report."""
        report = ValidationReport()
        
        assert not report.has_errors()
        
        report.add_issue("warning", "test", "test warning")
        assert not report.has_errors()
        
        report.add_issue("error", "test", "test error")
        assert report.has_errors()
    
    def test_report_has_warnings(self):
        """Test checking for warnings in report."""
        report = ValidationReport()
        
        assert not report.has_warnings()
        
        report.add_issue("info", "test", "test info")
        assert not report.has_warnings()
        
        report.add_issue("warning", "test", "test warning")
        assert report.has_warnings()
    
    def test_report_summary_format(self):
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


# ============================================================================
# TABLE VALIDATOR TESTS
# ============================================================================

class TestTableValidator:
    """Tests for Unity Catalog table validation."""
    
    def test_validator_initialization_with_env_vars(self):
        """Test initializing validator with environment variables."""
        with patch.dict('os.environ', {
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'test-token'
        }):
            validator = TableValidator()
            
            assert validator.databricks_host == "https://test.databricks.com"
            assert validator.databricks_token == "test-token"
    
    def test_validator_initialization_with_explicit_values(self):
        """Test initializing validator with explicit values."""
        validator = TableValidator(
            databricks_host="https://custom.databricks.com",
            databricks_token="custom-token"
        )
        
        assert validator.databricks_host == "https://custom.databricks.com"
        assert validator.databricks_token == "custom-token"
    
    def test_validator_initialization_missing_credentials(self):
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
    
    @patch('src.validation.table_validator.requests.get')
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
    
    @patch('src.validation.table_validator.requests.get')
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
    
    @patch('src.validation.table_validator.requests.get')
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
    
    @patch('src.validation.table_validator.requests.get')
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


# ============================================================================
# SQL VALIDATION TESTS
# ============================================================================

class TestSQLValidation:
    """Tests for SQL query validation."""
    
    def test_sql_validator_initialization(self):
        """Test SQL validator initialization."""
        validator = SQLValidator()
        assert validator is not None
    
    def test_extract_columns_from_sql(self):
        """Test extracting column references from SQL."""
        validator = SQLValidator()
        
        sql = "SELECT t.customer_id, t.total_amount, a.product_name FROM transactions t"
        
        report = validator.validate_sql(sql)
        
        # Check that column references were extracted
        assert len(report.columns_referenced) > 0
        # Column references include table.column format
        assert any("customer_id" in col for col in report.columns_referenced)
    
    def test_extract_columns_filters_keywords(self):
        """Test that SQL keywords are filtered out."""
        validator = SQLValidator()
        
        sql = "SELECT CURRENT_DATE, DATE_TRUNC('day', t.date), COUNT(*) FROM catalog.schema.table t"
        
        report = validator.validate_sql(sql)
        
        # Should extract t.date column reference
        assert any("date" in col.lower() for col in report.columns_referenced)
        # Keywords should not be in column references
        assert not any("CURRENT_DATE" in col for col in report.columns_referenced)
    
    def test_extract_tables_from_sql(self):
        """Test extracting table names from SQL."""
        validator = SQLValidator()
        
        sql = """
        SELECT * FROM catalog1.schema1.table1 t1
        JOIN catalog2.schema2.table2 t2 ON t1.id = t2.id
        """
        
        report = validator.validate_sql(sql)
        
        assert "catalog1.schema1.table1" in report.tables_referenced
        assert "catalog2.schema2.table2" in report.tables_referenced
    
    def test_extract_tables_with_backticks(self):
        """Test extracting table names from SQL (without backticks in validation)."""
        validator = SQLValidator()
        
        sql = """
        SELECT * FROM main.log_steam.partner_traffic
        JOIN catalog2.schema2.table2 ON t1.id = t2.id
        JOIN catalog3.schema3.table3 t3 ON t1.id = t3.id
        """
        
        report = validator.validate_sql(sql)
        
        # Check that tables were extracted
        assert len(report.tables_referenced) >= 2
        assert any("partner_traffic" in table for table in report.tables_referenced)
    
    def test_validate_sql_syntax_basic(self):
        """Test basic SQL syntax validation."""
        validator = SQLValidator()
        
        # Valid SQL
        valid_sql = "SELECT customer_id, SUM(amount) FROM transactions GROUP BY customer_id"
        report = validator.validate_sql(valid_sql)
        # Should parse successfully, might have warnings but not errors
        assert report.is_valid or len(report.get_errors()) == 0
        
        # Invalid SQL (no FROM clause - but this creates a warning, not error)
        invalid_sql = "SELECT customer_id, amount"
        report = validator.validate_sql(invalid_sql)
        # Should have at least a warning about missing FROM
        assert len(report.issues) > 0
    
    def test_detect_select_star(self):
        """Test detection of SELECT * anti-pattern."""
        validator = SQLValidator()
        
        sql_with_star = "SELECT * FROM transactions"
        report = validator.validate_sql(sql_with_star)
        
        # Should have warning about SELECT *
        warnings = report.get_warnings()
        assert any("SELECT *" in warning.message or "*" in warning.message for warning in warnings)
    
    def test_validate_join_specifications(self):
        """Test join specification validation."""
        validator = SQLValidator()
        
        # Valid join
        valid_join = """
        SELECT t.id, c.name 
        FROM transactions t 
        JOIN customers c ON t.customer_id = c.id
        """
        report = validator.validate_sql(valid_join)
        assert report.has_explicit_joins
        # Valid join should not have join-related errors
        join_errors = [issue for issue in report.get_errors() if issue.category == "join"]
        assert len(join_errors) == 0
        
        # Cross join (missing ON clause)
        cross_join = """
        SELECT t.id, c.name 
        FROM transactions t 
        JOIN customers c
        """
        report = validator.validate_sql(cross_join)
        # Should have error about missing ON clause
        join_errors = [issue for issue in report.get_errors() if issue.category == "join"]
        assert len(join_errors) > 0


# ============================================================================
# BENCHMARK VALIDATION TESTS
# ============================================================================

class TestBenchmarkValidation:
    """Tests for benchmark question validation."""
    
    @patch('src.validation.table_validator.requests.get')
    def test_validate_benchmark_queries(self, mock_get, temp_config_file):
        """Test validating tables referenced in benchmark questions."""
        # Update config to include benchmarks
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["genie_space_config"]["benchmark_questions"] = [
            {
                "question": "What is the total revenue?",
                "expected_sql": "SELECT SUM(amount) FROM demo.retail.transactions;"
            },
            {
                "question": "How many customers?",
                "expected_sql": "SELECT COUNT(*) FROM demo.retail.customers;"
            }
        ]
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "demo.retail.transactions",
            "columns": [{"name": "amount", "type_text": "DECIMAL"}]
        }
        mock_get.return_value = mock_response
        
        # Run validation
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        report = validator.validate_config(temp_config_file)
        
        # Should validate benchmarks
        validation_sections = [
            issue for issue in report.issues
            if issue.type == "validation_section" and "benchmark" in issue.message.lower()
        ]
        assert len(validation_sections) >= 1
    
    @patch('src.validation.table_validator.requests.get')
    def test_validate_benchmark_with_invalid_table(self, mock_get, temp_config_file):
        """Test validation detects invalid tables in benchmarks."""
        # Update config with invalid table
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config["genie_space_config"]["benchmark_questions"] = [
            {
                "question": "Invalid query",
                "expected_sql": "SELECT COUNT(*) FROM demo.retail.invalid_table;"
            }
        ]
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f)
        
        # Mock 404 for invalid table
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        report = validator.validate_config(temp_config_file)
        
        # Should have validation issues for invalid table
        # At least some validation issue should be raised
        assert len(report.issues) > 0


# ============================================================================
# INTEGRATION VALIDATION TESTS
# ============================================================================

class TestValidationIntegration:
    """Integration tests for validation workflow."""
    
    @patch('src.validation.table_validator.requests.get')
    def test_full_validation_workflow(self, mock_get, temp_config_file):
        """Test complete validation workflow with mocked API."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "demo.retail.transactions",
            "columns": [
                {"name": "amount", "type_text": "DECIMAL"},
                {"name": "customer_id", "type_text": "INT"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Run validation
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        report = validator.validate_config(temp_config_file)
        
        # Verify results
        assert len(report.tables_checked) > 0
        assert not report.has_errors()
    
    def test_validation_saves_report(self, temp_config_file):
        """Test that validation creates a report."""
        validator = TableValidator(
            databricks_host="https://test.databricks.com",
            databricks_token="token"
        )
        
        # Run validation
        report = validator.validate_config(temp_config_file)
        
        # Check that report was created with expected attributes
        assert hasattr(report, 'tables_checked')
        assert hasattr(report, 'issues')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
