"""
Tests for requirements conversion pipeline
"""

import pytest
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsing.pdf_parser import PDFParser, PDFContent
from src.parsing.markdown_parser import MarkdownParser
from src.parsing.requirements_structurer import (
    RequirementsStructurer, Question, TableInfo, SQLQuery
)
from src.parsing.markdown_generator import MarkdownGenerator


class TestPDFParser:
    """Tests for PDF parser"""
    
    def test_pdf_content_creation(self):
        """Test PDFContent dataclass creation"""
        content = PDFContent(
            text_by_page=["Page 1", "Page 2"],
            tables_by_page=[[["a", "b"]], []],
            images=[],  # Empty list of PIL images
            metadata={"num_pages": 2}
        )
        
        assert len(content.text_by_page) == 2
        assert content.metadata["num_pages"] == 2
    
    def test_parser_initialization(self):
        """Test PDF parser can be initialized"""
        parser = PDFParser()
        assert parser is not None
        assert parser.llm_client is None
    
    def test_empty_structure_creation(self):
        """Test creating empty structure"""
        parser = PDFParser()
        empty = parser._create_empty_structure()
        
        assert "questions" in empty
        assert "tables" in empty
        assert "sql_queries" in empty
        assert "metadata" in empty


class TestMarkdownParser:
    """Tests for markdown parser"""
    
    def test_parser_initialization(self):
        """Test markdown parser can be initialized"""
        parser = MarkdownParser()
        assert parser is not None
    
    def test_question_pattern(self):
        """Test question extraction pattern"""
        import re
        parser = MarkdownParser()
        
        text = "### 1. 테스트 질문입니다?"
        matches = list(re.finditer(parser.QUESTION_PATTERN, text))
        
        assert len(matches) == 1
        assert matches[0].group(1) == "1"
        assert "테스트 질문" in matches[0].group(2)
    
    def test_sql_query_pattern(self):
        """Test SQL query extraction pattern"""
        import re
        parser = MarkdownParser()
        
        text = """```sql
SELECT * FROM table
```"""
        matches = list(re.finditer(parser.SQL_QUERY_PATTERN, text, re.DOTALL))
        
        assert len(matches) == 1
        assert "SELECT" in matches[0].group(1)
    
    def test_table_name_pattern(self):
        """Test table name extraction pattern"""
        import re
        parser = MarkdownParser()
        
        text = "`main.log_discord.message`"
        matches = re.findall(parser.TABLE_NAME_PATTERN, text)
        
        assert len(matches) == 1
        assert matches[0] == "main.log_discord.message"
    
    def test_categorize_question(self):
        """Test question categorization"""
        parser = MarkdownParser()
        
        # Test KPI category
        assert parser._categorize_question("DAU는 얼마인가요?", "") == "KPI"
        
        # Test Social category
        assert parser._categorize_question("디스코드 메시지는?", "") == "Social"
        
        # Test Sentiment category
        # Note: "긍정 리뷰는?" matches Social first due to "리뷰" (review) keyword
        # Use pure sentiment keywords for sentiment categorization
        assert parser._categorize_question("긍정적인 감성 분석 결과는?", "") == "Sentiment"


class TestRequirementsStructurer:
    """Tests for requirements structurer"""
    
    def test_table_info_creation(self):
        """Test TableInfo creation from dict"""
        data = {
            "full_name": "catalog.schema.table",
            "description": "Test table",
            "key_columns": ["col1", "col2"]
        }
        
        table = TableInfo.from_dict(data)
        
        assert table.catalog == "catalog"
        assert table.schema == "schema"
        assert table.table == "table"
        assert table.full_name == "catalog.schema.table"
        assert len(table.columns) == 2
    
    def test_question_creation(self):
        """Test Question creation from dict"""
        data = {
            "id": "Q1",
            "text": "Test question?",
            "category": "KPI",
            "tables_needed": ["table1", "table2"]
        }
        
        question = Question.from_dict(data)
        
        assert question.id == "Q1"
        assert question.text == "Test question?"
        assert question.category == "KPI"
        assert len(question.tables_needed) == 2
    
    def test_sql_query_creation(self):
        """Test SQLQuery creation from dict"""
        data = {
            "question_id": "Q1",
            "query": "SELECT * FROM table",
            "description": "Test query"
        }
        
        query = SQLQuery.from_dict(data)
        
        assert query.question_id == "Q1"
        assert "SELECT" in query.query
        assert query.description == "Test query"
    
    def test_combine_questions(self):
        """Test combining questions from multiple sources"""
        structurer = RequirementsStructurer()
        
        pdf_questions = [
            {"id": "Q1", "text": "Question 1", "category": "KPI", "tables_needed": []}
        ]
        
        md_questions = [
            {"id": "Q2", "text": "Question 2", "category": "Social", "tables_needed": []},
            {"id": "Q3", "text": "Question 1", "category": "KPI", "tables_needed": []}  # Duplicate
        ]
        
        combined = structurer._combine_questions(pdf_questions, md_questions)
        
        # Should have 2 unique questions (Q1 duplicate removed)
        assert len(combined) == 2
        assert combined[0].text == "Question 2"  # MD comes first
        assert combined[1].text == "Question 1"
    
    def test_combine_tables(self):
        """Test combining tables from multiple sources"""
        structurer = RequirementsStructurer()
        
        pdf_tables = [
            {"full_name": "cat.sch.table1", "description": "Table 1", "key_columns": []}
        ]
        
        md_tables = [
            {"full_name": "cat.sch.table2", "description": "Table 2", "key_columns": []},
            {"full_name": "cat.sch.table1", "description": "Table 1 updated", "key_columns": []}  # Duplicate
        ]
        
        combined = structurer._combine_tables(pdf_tables, md_tables)
        
        # Should have 2 unique tables, with MD taking precedence
        assert len(combined) == 2


class TestMarkdownGenerator:
    """Tests for markdown generator"""
    
    def test_generator_initialization(self):
        """Test markdown generator can be initialized"""
        generator = MarkdownGenerator()
        assert generator is not None
    
    def test_header_generation(self):
        """Test header generation"""
        from src.parsing.requirements_structurer import RequirementsDocument
        
        generator = MarkdownGenerator()
        doc = RequirementsDocument(
            metadata={"title": "Test Doc", "primary_domain": "kpi_analytics"}
        )
        
        header = generator._generate_header(doc)
        
        assert "# " in header
        assert "KPI" in header or "Analytics" in header
    
    def test_overview_generation(self):
        """Test overview section generation"""
        from src.parsing.requirements_structurer import RequirementsDocument
        
        generator = MarkdownGenerator()
        doc = RequirementsDocument(
            metadata={
                "num_questions": 10,
                "summary": "Test summary"
            },
            all_tables=[]
        )
        
        overview = generator._generate_overview(doc)
        
        assert "## 개요" in overview
        assert "목적" in overview
        assert "Test summary" in overview


class TestIntegration:
    """Integration tests"""
    
    def test_full_pipeline_structure(self):
        """Test that all pipeline components can work together"""
        # Create mock data
        pdf_data = {
            "questions": [{"id": "Q1", "text": "Test?", "category": "KPI", "tables_needed": []}],
            "tables": [{"full_name": "cat.sch.table", "description": "Table", "key_columns": []}],
            "sql_queries": [],
            "metadata": {"domain": "kpi_analytics"}
        }
        
        md_data = {
            "questions": [{"id": "Q2", "text": "Test 2?", "category": "Social", "tables_needed": []}],
            "tables": [],
            "sql_queries": [],
            "metadata": {"domain": "social_analytics"}
        }
        
        # Structure data
        structurer = RequirementsStructurer()
        doc = structurer.structure_data(pdf_data, md_data)
        
        # Verify structure
        assert len(doc.all_questions) == 2
        assert len(doc.all_tables) == 1
        assert "domains" in doc.metadata
        
        # Generate markdown (to memory, not file)
        generator = MarkdownGenerator()
        markdown = generator.generate(doc, "/tmp/test_output.md")
        
        # Verify markdown contains expected sections
        assert "## 개요" in markdown
        assert "## 📊 질문 목록" in markdown
        assert len(markdown) > 100


def test_imports():
    """Test that all required imports work"""
    # This test will fail if any imports are broken
    from src.parsing.pdf_parser import PDFParser
    from src.parsing.markdown_parser import MarkdownParser
    from src.parsing.requirements_structurer import RequirementsStructurer
    from src.parsing.llm_enricher import LLMEnricher
    from src.parsing.markdown_generator import MarkdownGenerator
    
    assert True  # If we get here, all imports worked


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
