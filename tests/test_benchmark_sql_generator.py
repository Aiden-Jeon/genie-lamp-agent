"""Unit tests for benchmark SQL generator module."""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from src.utils.benchmark_sql_generator import (
    generate_benchmark_sql_for_config,
    build_benchmark_sql_prompt,
    parse_benchmark_sql_response,
    _batch_benchmarks
)
from src.models import BenchmarkSQL, BenchmarkSQLResponse


class TestBatchBenchmarks:
    """Test benchmark batching logic."""

    def test_batch_single_batch(self):
        """Test batching with fewer items than batch size."""
        benchmarks = [{"question": f"Q{i}"} for i in range(5)]
        batches = list(_batch_benchmarks(benchmarks, batch_size=10))

        assert len(batches) == 1
        assert len(batches[0]) == 5

    def test_batch_multiple_batches(self):
        """Test batching with multiple full batches."""
        benchmarks = [{"question": f"Q{i}"} for i in range(25)]
        batches = list(_batch_benchmarks(benchmarks, batch_size=10))

        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5

    def test_batch_exact_size(self):
        """Test batching when count is exact multiple of batch size."""
        benchmarks = [{"question": f"Q{i}"} for i in range(20)]
        batches = list(_batch_benchmarks(benchmarks, batch_size=10))

        assert len(batches) == 2
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10

    def test_batch_empty_list(self):
        """Test batching empty list."""
        benchmarks = []
        batches = list(_batch_benchmarks(benchmarks, batch_size=10))

        assert len(batches) == 0


class TestBuildPrompt:
    """Test prompt building for benchmark SQL generation."""

    def test_build_prompt_basic(self):
        """Test basic prompt construction."""
        tables = [
            {
                "catalog_name": "main",
                "schema_name": "sales",
                "table_name": "transactions",
                "description": "Transaction records"
            }
        ]
        join_specs = []
        benchmarks = [
            {"question": "What is the total revenue?"}
        ]

        prompt = build_benchmark_sql_prompt(tables, join_specs, benchmarks)

        assert "main.sales.transactions" in prompt
        assert "Transaction records" in prompt
        assert "What is the total revenue?" in prompt
        assert "1. What is the total revenue?" in prompt

    def test_build_prompt_with_joins(self):
        """Test prompt with join specifications."""
        tables = [
            {"catalog_name": "main", "schema_name": "sales", "table_name": "orders"},
            {"catalog_name": "main", "schema_name": "sales", "table_name": "customers"}
        ]
        join_specs = [
            {
                "left_table": "main.sales.orders",
                "right_table": "main.sales.customers",
                "join_type": "INNER",
                "join_condition": "orders.customer_id = customers.customer_id",
                "description": "Orders belong to customers"
            }
        ]
        benchmarks = [
            {"question": "Top customers by revenue?"}
        ]

        prompt = build_benchmark_sql_prompt(tables, join_specs, benchmarks)

        assert "main.sales.orders" in prompt
        assert "main.sales.customers" in prompt
        assert "INNER" in prompt
        assert "orders.customer_id = customers.customer_id" in prompt
        assert "Orders belong to customers" in prompt

    def test_build_prompt_multiple_benchmarks(self):
        """Test prompt with multiple benchmark questions."""
        tables = [{"catalog_name": "test", "schema_name": "data", "table_name": "t1"}]
        join_specs = []
        benchmarks = [
            {"question": "Question 1?"},
            {"question": "Question 2?"},
            {"question": "Question 3?"}
        ]

        prompt = build_benchmark_sql_prompt(tables, join_specs, benchmarks)

        assert "1. Question 1?" in prompt
        assert "2. Question 2?" in prompt
        assert "3. Question 3?" in prompt


class TestParseResponse:
    """Test parsing LLM responses."""

    def test_parse_valid_response(self):
        """Test parsing valid benchmark SQL response."""
        response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(
                    question="What is total revenue?",
                    sql="SELECT SUM(amount) FROM transactions;",
                    reasoning="Sum all transaction amounts"
                )
            ]
        )

        results = parse_benchmark_sql_response(response)

        assert len(results) == 1
        assert results[0]["question"] == "What is total revenue?"
        assert results[0]["sql"] == "SELECT SUM(amount) FROM transactions;"
        assert results[0]["reasoning"] == "Sum all transaction amounts"

    def test_parse_multiple_queries(self):
        """Test parsing multiple SQL queries."""
        response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(question="Q1", sql="SELECT 1;", reasoning="R1"),
                BenchmarkSQL(question="Q2", sql="SELECT 2;", reasoning="R2")
            ]
        )

        results = parse_benchmark_sql_response(response)

        assert len(results) == 2
        assert results[0]["question"] == "Q1"
        assert results[1]["question"] == "Q2"

    def test_parse_adds_missing_semicolon(self):
        """Test auto-fixing missing semicolon."""
        response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(
                    question="Test",
                    sql="SELECT * FROM table",  # Missing semicolon
                    reasoning="Test"
                )
            ]
        )

        results = parse_benchmark_sql_response(response)

        assert results[0]["sql"] == "SELECT * FROM table;"

    def test_parse_preserves_existing_semicolon(self):
        """Test that existing semicolons are preserved."""
        response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(
                    question="Test",
                    sql="SELECT * FROM table;",
                    reasoning="Test"
                )
            ]
        )

        results = parse_benchmark_sql_response(response)

        assert results[0]["sql"] == "SELECT * FROM table;"
        assert results[0]["sql"].count(";") == 1

    def test_parse_empty_sql_raises_error(self):
        """Test that empty SQL raises validation error."""
        response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(question="Test", sql="", reasoning="Test")
            ]
        )

        with pytest.raises(ValueError, match="Empty SQL"):
            parse_benchmark_sql_response(response)


class TestGenerateBenchmarkSQL:
    """Test end-to-end benchmark SQL generation."""

    def test_no_benchmarks_needing_sql(self):
        """Test when all benchmarks already have SQL."""
        config = {
            "genie_space_config": {
                "tables": [],
                "join_specifications": [],
                "benchmark_questions": [
                    {"question": "Q1", "expected_sql": "SELECT 1;"}
                ]
            }
        }

        mock_client = Mock()
        result = generate_benchmark_sql_for_config(
            config=config,
            llm_client=mock_client,
            verbose=False
        )

        # Should not call LLM
        mock_client.generate_structured.assert_not_called()
        assert result == config

    def test_generates_sql_for_null_benchmarks(self):
        """Test SQL generation for benchmarks with null expected_sql."""
        config = {
            "genie_space_config": {
                "tables": [
                    {"catalog_name": "test", "schema_name": "data", "table_name": "t1"}
                ],
                "join_specifications": [],
                "benchmark_questions": [
                    {"question": "Q1", "expected_sql": None},
                    {"question": "Q2", "expected_sql": "SELECT 2;"},  # Already has SQL
                    {"question": "Q3", "expected_sql": None}
                ]
            }
        }

        # Mock LLM response
        mock_response = BenchmarkSQLResponse(
            benchmark_sqls=[
                BenchmarkSQL(question="Q1", sql="SELECT 1;", reasoning="Test 1"),
                BenchmarkSQL(question="Q3", sql="SELECT 3;", reasoning="Test 3")
            ]
        )

        mock_client = Mock()
        mock_client.generate_structured.return_value = mock_response

        result = generate_benchmark_sql_for_config(
            config=config,
            llm_client=mock_client,
            batch_size=10,
            verbose=False
        )

        # Should call LLM once (all fit in one batch)
        mock_client.generate_structured.assert_called_once()

        # Check results
        benchmarks = result["genie_space_config"]["benchmark_questions"]
        assert benchmarks[0]["expected_sql"] == "SELECT 1;"
        assert benchmarks[1]["expected_sql"] == "SELECT 2;"  # Unchanged
        assert benchmarks[2]["expected_sql"] == "SELECT 3;"

    def test_batching_multiple_calls(self):
        """Test that large benchmark sets are batched correctly."""
        # Create 25 benchmarks needing SQL
        benchmarks = [
            {"question": f"Q{i}", "expected_sql": None}
            for i in range(25)
        ]

        config = {
            "genie_space_config": {
                "tables": [{"catalog_name": "t", "schema_name": "s", "table_name": "t"}],
                "join_specifications": [],
                "benchmark_questions": benchmarks
            }
        }

        # Mock LLM to return appropriate batches
        def mock_generate(prompt, response_model, **kwargs):
            # Extract batch number from call count
            call_count = mock_client.generate_structured.call_count
            start_idx = (call_count - 1) * 10
            end_idx = min(start_idx + 10, 25)

            batch_results = [
                BenchmarkSQL(question=f"Q{i}", sql=f"SELECT {i};", reasoning=f"R{i}")
                for i in range(start_idx, end_idx)
            ]
            return BenchmarkSQLResponse(benchmark_sqls=batch_results)

        mock_client = Mock()
        mock_client.generate_structured.side_effect = mock_generate

        result = generate_benchmark_sql_for_config(
            config=config,
            llm_client=mock_client,
            batch_size=10,
            verbose=False
        )

        # Should call LLM 3 times (10 + 10 + 5)
        assert mock_client.generate_structured.call_count == 3

        # Check all benchmarks have SQL
        benchmarks = result["genie_space_config"]["benchmark_questions"]
        for i, bm in enumerate(benchmarks):
            assert bm["expected_sql"] == f"SELECT {i};"

    def test_llm_failure_raises_error(self):
        """Test that LLM failures are propagated."""
        config = {
            "genie_space_config": {
                "tables": [],
                "join_specifications": [],
                "benchmark_questions": [
                    {"question": "Q1", "expected_sql": None}
                ]
            }
        }

        mock_client = Mock()
        mock_client.generate_structured.side_effect = Exception("LLM API error")

        with pytest.raises(RuntimeError, match="Failed to generate SQL for batch"):
            generate_benchmark_sql_for_config(
                config=config,
                llm_client=mock_client,
                verbose=False
            )
