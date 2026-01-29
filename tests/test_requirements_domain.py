"""Requirements Domain Tests

Consolidates all tests related to requirements parsing and extraction:
- PDF parsing
- Markdown parsing  
- Benchmark extraction
- Example extraction
- Domain extraction
- Table extraction
"""

import pytest
from pathlib import Path
from src.parsing.pdf_parser import PDFParser, PDFContent
from src.parsing.markdown_parser import MarkdownParser
from src.parsing.requirements_structurer import RequirementsStructurer
from src.parsing.markdown_generator import MarkdownGenerator
from src.benchmark.benchmark_extractor import extract_sample_queries_as_benchmarks
from src.extractor.example_extractor import (
    extract_sample_queries_as_examples,
    validate_examples
)
from src.extractor.domain_extractor import DomainKnowledgeExtractor
from src.extractor.table_extractor import TableExtractor
from src.models import GenieSpaceExampleSQL


# ============================================================================
# PDF PARSING TESTS
# ============================================================================

class TestPDFParsing:
    """Tests for PDF parsing functionality."""
    
    def test_pdf_content_creation(self):
        """Test PDFContent dataclass creation."""
        content = PDFContent(
            text_by_page=["Page 1", "Page 2"],
            tables_by_page=[[["a", "b"]], []],
            images=[],
            metadata={"num_pages": 2}
        )
        
        assert len(content.text_by_page) == 2
        assert content.metadata["num_pages"] == 2
    
    def test_parser_initialization(self):
        """Test PDF parser initialization."""
        parser = PDFParser()
        assert parser is not None
        assert parser.llm_client is None
    
    def test_empty_structure_creation(self):
        """Test creating empty structure."""
        parser = PDFParser()
        empty = parser._create_empty_structure()
        
        assert "questions" in empty
        assert "tables" in empty
        assert "sql_queries" in empty
        assert "metadata" in empty


# ============================================================================
# MARKDOWN PARSING TESTS
# ============================================================================

class TestMarkdownParsing:
    """Tests for markdown parsing functionality."""
    
    def test_parser_initialization(self):
        """Test markdown parser initialization."""
        parser = MarkdownParser()
        assert parser is not None
    
    def test_question_pattern(self):
        """Test question extraction pattern."""
        import re
        parser = MarkdownParser()
        
        text = "### 1. 테스트 질문입니까?"
        matches = list(re.finditer(parser.QUESTION_PATTERN, text))
        
        assert len(matches) == 1
        assert matches[0].group(1) == "1"
        assert "테스트 질문" in matches[0].group(2)
    
    def test_sql_query_pattern(self):
        """Test SQL query extraction pattern."""
        import re
        parser = MarkdownParser()
        
        text = """```sql
SELECT * FROM table
```"""
        matches = list(re.finditer(parser.SQL_QUERY_PATTERN, text, re.DOTALL))
        
        assert len(matches) == 1
        assert "SELECT" in matches[0].group(1)
    
    def test_table_name_pattern(self):
        """Test table name extraction pattern."""
        import re
        parser = MarkdownParser()
        
        text = "`main.log_discord.message`"
        matches = re.findall(parser.TABLE_NAME_PATTERN, text)
        
        assert len(matches) == 1
        assert matches[0] == "main.log_discord.message"
    
    def test_categorize_question(self):
        """Test question categorization."""
        parser = MarkdownParser()
        
        # _categorize_question requires both question_text and section_content
        section_content = "**필요한 테이블:** transactions"
        
        # Aggregation question
        category = parser._categorize_question("전체 매출은?", section_content)
        assert category == "aggregation"
        
        # Trend question
        category = parser._categorize_question("시간에 따른 변화는?", section_content)
        assert category == "trend"
        
        # Comparison question
        category = parser._categorize_question("A와 B의 차이는?", section_content)
        assert category == "comparison"


# ============================================================================
# BENCHMARK EXTRACTION TESTS
# ============================================================================

class TestBenchmarkExtraction:
    """Tests for benchmark extraction from requirements."""
    
    def test_extract_benchmarks_basic(self, sample_requirements_file):
        """Test basic benchmark extraction."""
        benchmarks = extract_sample_queries_as_benchmarks(sample_requirements_file)
        
        assert len(benchmarks) > 0, "Should extract benchmarks"
        
        # Check structure
        for bm in benchmarks:
            assert "question" in bm
            assert "expected_sql" in bm
            assert "source" in bm
            assert bm["source"] == "sample_query"
    
    def test_sql_completeness(self, sample_requirements_file):
        """Test that extracted SQL queries are complete."""
        benchmarks = extract_sample_queries_as_benchmarks(sample_requirements_file)
        
        for bm in benchmarks:
            sql = bm["expected_sql"]
            sql_stripped = sql.strip()
            
            # Should not end with comma (truncation indicator)
            assert not sql_stripped.endswith(","), "SQL should not be truncated"
            
            # Should have basic SQL clauses
            assert "SELECT" in sql.upper(), "SQL should have SELECT"
            assert "FROM" in sql.upper(), "SQL should have FROM"
    
    @pytest.mark.skipif(
        not Path("real_requirements/question-table-mapping-content-delivery.md").exists(),
        reason="Real requirements file not available"
    )
    def test_extract_from_real_requirements(self):
        """Test extraction from real Korean format requirements."""
        requirements_path = "real_requirements/question-table-mapping-content-delivery.md"
        benchmarks = extract_sample_queries_as_benchmarks(requirements_path)
        
        assert len(benchmarks) > 0, "Should extract from real requirements"
        print(f"\n✓ Extracted {len(benchmarks)} benchmarks from real requirements")


# ============================================================================
# EXAMPLE EXTRACTION TESTS
# ============================================================================

class TestExampleExtraction:
    """Tests for example SQL extraction."""
    
    def test_extract_examples_basic(self, sample_requirements_file):
        """Test basic example extraction."""
        examples = extract_sample_queries_as_examples(sample_requirements_file)
        
        assert len(examples) > 0, "Should extract examples"
        
        # Check structure
        first_example = examples[0]
        assert isinstance(first_example, GenieSpaceExampleSQL)
        assert first_example.question
        assert first_example.sql_query
        assert len(first_example.sql_query) > 10
    
    def test_extract_examples_file_not_found(self):
        """Test extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            extract_sample_queries_as_examples("nonexistent_file.md")
    
    def test_validate_examples_valid(self):
        """Test validation with valid examples."""
        examples = [
            GenieSpaceExampleSQL(
                question="What are the top selling products?",
                sql_query="SELECT product_name, COUNT(*) FROM products GROUP BY product_name ORDER BY COUNT(*) DESC LIMIT 10"
            ),
            GenieSpaceExampleSQL(
                question="How many customers do we have?",
                sql_query="SELECT COUNT(DISTINCT customer_id) FROM customers"
            )
        ]
        
        issues = validate_examples(examples)
        assert len(issues) == 0, "Valid examples should have no issues"
    
    def test_validate_examples_short_question(self):
        """Test validation catches short questions."""
        examples = [
            GenieSpaceExampleSQL(
                question="Hi",  # Too short
                sql_query="SELECT * FROM table"
            )
        ]
        
        issues = validate_examples(examples)
        assert len(issues) > 0, "Should detect short question"
        assert any("short" in issue.lower() for issue in issues)
    
    def test_validate_examples_missing_sql_keywords(self):
        """Test validation catches SQL without keywords."""
        examples = [
            GenieSpaceExampleSQL(
                question="What is the total revenue?",
                sql_query="This is not a valid SQL query"
            )
        ]
        
        issues = validate_examples(examples)
        assert len(issues) > 0, "Should detect missing SQL keywords"


# ============================================================================
# DOMAIN EXTRACTION TESTS
# ============================================================================

class TestDomainExtraction:
    """Tests for domain knowledge extraction."""
    
    def test_domain_extractor_initialization(self):
        """Test domain extractor initialization."""
        extractor = DomainKnowledgeExtractor()
        assert extractor is not None
    
    def test_extract_from_requirements(self, sample_requirements_file):
        """Test extracting domain knowledge from requirements."""
        extractor = DomainKnowledgeExtractor()
        
        # Use extract_from_file method
        domain_knowledge = extractor.extract_from_file(sample_requirements_file)
        
        # domain_knowledge is a DomainKnowledge dataclass
        assert hasattr(domain_knowledge, 'table_relationships')
        assert hasattr(domain_knowledge, 'business_metrics')


# ============================================================================
# TABLE EXTRACTION TESTS
# ============================================================================

class TestTableExtraction:
    """Tests for table information extraction."""
    
    def test_table_extractor_initialization(self):
        """Test table extractor initialization."""
        extractor = TableExtractor()
        assert extractor is not None
    
    def test_extract_tables_from_markdown(self, sample_requirements_file):
        """Test extracting table information from markdown."""
        extractor = TableExtractor()
        
        # Use the extract_from_file method
        tables = extractor.extract_from_file(sample_requirements_file)
        
        assert isinstance(tables, list)
        assert len(tables) > 0
        # Each table should have catalog, schema, table attributes
        for table in tables:
            assert hasattr(table, 'catalog')
            assert hasattr(table, 'schema')
            assert hasattr(table, 'table')


# ============================================================================
# REQUIREMENTS STRUCTURING TESTS
# ============================================================================

class TestRequirementsStructuring:
    """Tests for requirements structuring."""
    
    def test_structurer_initialization(self):
        """Test requirements structurer initialization."""
        structurer = RequirementsStructurer()
        assert structurer is not None
    
    def test_structure_requirements(self, sample_requirements_content):
        """Test structuring requirements into standardized format."""
        structurer = RequirementsStructurer()
        
        # structure_data requires pdf_data and md_data dicts
        pdf_data = {}  # Empty PDF data for this test
        md_data = {"content": sample_requirements_content}
        
        structured = structurer.structure_data(pdf_data, md_data)
        
        # structured is a RequirementsDocument dataclass
        assert hasattr(structured, 'all_questions')
        assert hasattr(structured, 'all_tables')
        assert hasattr(structured, 'all_queries')


# ============================================================================
# MARKDOWN GENERATION TESTS
# ============================================================================

class TestMarkdownGeneration:
    """Tests for markdown generation from structured data."""
    
    def test_generator_initialization(self):
        """Test markdown generator initialization."""
        generator = MarkdownGenerator()
        assert generator is not None
    
    def test_generate_markdown_from_structured_data(self, tmp_path):
        """Test generating markdown from structured requirements."""
        from src.parsing.requirements_structurer import RequirementsDocument, Question, TableInfo, SQLQuery
        
        generator = MarkdownGenerator()
        
        # Create a RequirementsDocument
        doc = RequirementsDocument()
        doc.all_questions = [
            Question(
                id="Q1",
                text="What is the revenue?",
                category="aggregation",
                tables_needed=[],
                columns_needed=[]
            )
        ]
        doc.all_tables = [
            TableInfo(
                catalog="demo",
                schema="retail",
                table="transactions",
                description="Sales data"
            )
        ]
        doc.all_queries = [
            SQLQuery(
                question="Total revenue",
                sql="SELECT SUM(amount) FROM transactions",
                related_questions=[]
            )
        ]
        doc.metadata = {}
        
        output_path = str(tmp_path / "test_output.md")
        markdown = generator.generate(doc, output_path)
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "revenue" in markdown.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
