"""Test benchmark extraction from requirements documents.

This test ensures that SQL queries extracted from requirements are complete
and not truncated at token limits or mid-query.
"""

import pytest
from pathlib import Path
from src.utils.benchmark_extractor import extract_sample_queries_as_benchmarks


def test_extract_benchmarks_from_korean_format():
    """Test extraction from Korean format requirements (### N. Question, **예시 쿼리:**)."""
    requirements_path = "real_requirements/question-table-mapping-content-delivery.md"

    # Skip test if file doesn't exist
    if not Path(requirements_path).exists():
        pytest.skip(f"Requirements file not found: {requirements_path}")

    benchmarks = extract_sample_queries_as_benchmarks(requirements_path)

    # Should extract multiple benchmarks
    assert len(benchmarks) > 0, "No benchmarks extracted"
    print(f"\n✓ Extracted {len(benchmarks)} benchmarks")

    # Each benchmark should have required fields
    for i, bm in enumerate(benchmarks, 1):
        assert "question" in bm, f"Benchmark {i}: Missing 'question' field"
        assert "expected_sql" in bm, f"Benchmark {i}: Missing 'expected_sql' field"
        assert "source" in bm, f"Benchmark {i}: Missing 'source' field"
        assert bm["source"] == "sample_query", f"Benchmark {i}: Wrong source"

        # Questions should be non-empty
        assert len(bm["question"]) > 0, f"Benchmark {i}: Empty question"

        # SQL should be non-empty
        sql = bm["expected_sql"]
        assert len(sql) > 0, f"Benchmark {i}: Empty SQL"

        print(f"✓ Benchmark {i}: {bm['question'][:60]}... ({len(sql)} chars)")


def test_sql_completeness():
    """Test that extracted SQL queries are complete (not truncated)."""
    requirements_path = "real_requirements/question-table-mapping-content-delivery.md"

    # Skip test if file doesn't exist
    if not Path(requirements_path).exists():
        pytest.skip(f"Requirements file not found: {requirements_path}")

    benchmarks = extract_sample_queries_as_benchmarks(requirements_path)

    assert len(benchmarks) > 0, "No benchmarks extracted"

    for i, bm in enumerate(benchmarks, 1):
        sql = bm["expected_sql"]
        sql_stripped = sql.strip()

        # SQL should not end with a comma (common truncation indicator)
        assert not sql_stripped.endswith(","), \
            f"Benchmark {i} SQL ends with comma (truncated): {bm['question'][:60]}"

        # SQL should have basic SQL clauses (at least SELECT and FROM)
        assert "SELECT" in sql.upper(), \
            f"Benchmark {i} SQL missing SELECT: {bm['question'][:60]}"
        assert "FROM" in sql.upper(), \
            f"Benchmark {i} SQL missing FROM clause: {bm['question'][:60]}"

        print(f"✓ Benchmark {i} SQL is complete ({len(sql)} chars, {len(sql.split())} lines)")


def test_long_sql_extraction():
    """Test that long SQL queries (60+ lines) are extracted completely."""
    requirements_path = "real_requirements/question-table-mapping-content-delivery.md"

    # Skip test if file doesn't exist
    if not Path(requirements_path).exists():
        pytest.skip(f"Requirements file not found: {requirements_path}")

    benchmarks = extract_sample_queries_as_benchmarks(requirements_path)

    assert len(benchmarks) > 0, "No benchmarks extracted"

    # Find benchmarks with long SQL (60+ lines)
    long_sql_benchmarks = [
        bm for bm in benchmarks
        if len(bm["expected_sql"].split('\n')) >= 60
    ]

    assert len(long_sql_benchmarks) > 0, "No benchmarks with long SQL found"
    print(f"\n✓ Found {len(long_sql_benchmarks)} benchmarks with 60+ line SQL queries")

    for bm in long_sql_benchmarks:
        sql = bm["expected_sql"]
        lines = sql.split('\n')

        # Should have proper structure for long queries
        assert "WITH" in sql.upper() or "SELECT" in sql.upper(), \
            f"Long SQL missing WITH/SELECT: {bm['question'][:60]}"

        # Should have closing semicolon
        assert sql.strip().endswith(";"), \
            f"Long SQL missing closing semicolon: {bm['question'][:60]}"

        # Should not end with comma (truncation indicator)
        assert not sql.strip().endswith(","), \
            f"Long SQL ends with comma (truncated): {bm['question'][:60]}"

        print(f"✓ Long SQL complete: {bm['question'][:60]}... ({len(sql)} chars, {len(lines)} lines)")


def test_specific_kpi_traffic_benchmark():
    """Test the specific benchmark that was reported as truncated."""
    requirements_path = "real_requirements/question-table-mapping-content-delivery.md"

    # Skip test if file doesn't exist
    if not Path(requirements_path).exists():
        pytest.skip(f"Requirements file not found: {requirements_path}")

    benchmarks = extract_sample_queries_as_benchmarks(requirements_path)

    # Find the KPI traffic benchmark
    kpi_benchmark = None
    for bm in benchmarks:
        if "KPI" in bm["question"] or "트래픽" in bm["question"]:
            kpi_benchmark = bm
            break

    assert kpi_benchmark is not None, "KPI traffic benchmark not found"

    sql = kpi_benchmark["expected_sql"]
    lines = sql.split('\n')

    # This specific benchmark should have 120+ lines
    assert len(lines) >= 100, f"KPI benchmark SQL too short: {len(lines)} lines"

    # Should have multiple CTEs
    assert sql.count("WITH") >= 1, "KPI benchmark missing WITH clause"
    assert sql.count("AS (") >= 5, "KPI benchmark missing CTEs"

    # Should have final SELECT with GROUP BY and ORDER BY
    assert "GROUP BY" in sql.upper(), "KPI benchmark missing GROUP BY"
    assert "ORDER BY" in sql.upper(), "KPI benchmark missing ORDER BY"

    # Should end with semicolon, not comma
    assert sql.strip().endswith(";"), "KPI benchmark missing closing semicolon"
    assert not sql.strip().endswith(","), "KPI benchmark ends with comma (truncated)"

    print(f"\n✓ KPI traffic benchmark complete:")
    print(f"  Question: {kpi_benchmark['question']}")
    print(f"  SQL: {len(sql)} chars, {len(lines)} lines")
    print(f"  First 100 chars: {sql[:100].replace(chr(10), ' ')}")
    print(f"  Last 100 chars: {sql[-100:].replace(chr(10), ' ')}")


if __name__ == "__main__":
    # Run tests
    print("=" * 80)
    print("BENCHMARK EXTRACTION TESTS")
    print("=" * 80)

    test_extract_benchmarks_from_korean_format()
    test_sql_completeness()
    test_long_sql_extraction()
    test_specific_kpi_traffic_benchmark()

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
