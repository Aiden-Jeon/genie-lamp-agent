"""
PDF Parser Module - Hybrid Approach
Extracts content from PDF files using pdfplumber, then interprets with LLM.
"""

import pdfplumber
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PDFContent:
    """Raw content extracted from PDF"""
    text_by_page: List[str]
    tables_by_page: List[List[List[str]]]
    metadata: Dict[str, str]
    
    def to_dict(self) -> dict:
        return asdict(self)


class PDFParser:
    """
    Hybrid PDF parser using pdfplumber for extraction and LLM for interpretation.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize PDF parser.
        
        Args:
            llm_client: Optional LLM client for interpretation (DatabricksFoundationModelClient)
        """
        self.llm_client = llm_client
    
    def extract_raw_content(self, pdf_path: str) -> PDFContent:
        """
        Extract raw text and tables from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDFContent with extracted text and tables
        """
        logger.info(f"Extracting content from PDF: {pdf_path}")
        
        text_by_page = []
        tables_by_page = []
        metadata = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = {
                    "num_pages": len(pdf.pages),
                    "file_name": Path(pdf_path).name,
                }
                
                # Extract content from each page
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_by_page.append(text)
                    else:
                        text_by_page.append("")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        tables_by_page.append(tables)
                    else:
                        tables_by_page.append([])
                    
                    logger.debug(f"Page {page_num}: {len(text) if text else 0} chars, {len(tables)} tables")
        
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            raise
        
        logger.info(f"Extracted {len(text_by_page)} pages, {sum(len(t) for t in tables_by_page)} tables total")
        
        return PDFContent(
            text_by_page=text_by_page,
            tables_by_page=tables_by_page,
            metadata=metadata
        )
    
    def interpret_with_llm(self, raw_content: PDFContent) -> Dict:
        """
        Use LLM to interpret raw PDF content and extract structured information.
        
        Args:
            raw_content: Raw content extracted from PDF
            
        Returns:
            Dictionary with structured information (questions, tables, queries, metadata)
        """
        if not self.llm_client:
            logger.warning("No LLM client provided, skipping interpretation")
            return self._create_empty_structure()
        
        logger.info("Interpreting PDF content with LLM")
        
        # Prepare content for LLM
        combined_text = "\n\n---PAGE BREAK---\n\n".join(raw_content.text_by_page)
        tables_json = json.dumps(raw_content.tables_by_page, ensure_ascii=False, indent=2)
        
        # Build prompt
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(combined_text, tables_json)
        
        try:
            # Call LLM
            response = self.llm_client.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=16000
            )
            
            # Parse response
            structured_data = self._parse_llm_response(response)
            
            # Validate structure
            self._validate_structure(structured_data)
            
            logger.info(f"LLM interpretation complete: {len(structured_data.get('questions', []))} questions, "
                       f"{len(structured_data.get('tables', []))} tables")
            
            return structured_data
        
        except Exception as e:
            logger.error(f"Error during LLM interpretation: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM interpretation"""
        return """You are an expert at extracting structured information from technical documents.
You will receive raw text and tables extracted from a PDF document.
Your task is to identify and structure:
1. Questions/requirements
2. Table schemas and descriptions
3. SQL queries
4. Metadata and relationships

Return your response as valid JSON only, with no additional text."""
    
    def _get_user_prompt(self, text: str, tables_json: str) -> str:
        """Get user prompt for LLM interpretation"""
        return f"""PDF Content:
{text[:20000]}  

Extracted Tables:
{tables_json[:5000]}  

Extract and structure this information as JSON:
{{
  "questions": [
    {{
      "id": "Q1",
      "text": "question text in Korean or English",
      "category": "KPI/Social/Sentiment/Trend/Comparison/Regional/Other",
      "tables_needed": ["catalog.schema.table"]
    }}
  ],
  "tables": [
    {{
      "full_name": "catalog.schema.table",
      "description": "brief description",
      "key_columns": ["col1", "col2"],
      "related_kpi": "DAU/ARPU/etc or null"
    }}
  ],
  "sql_queries": [
    {{
      "question_id": "Q1",
      "query": "SELECT ... (preserve exact SQL formatting)",
      "description": "what this query does"
    }}
  ],
  "metadata": {{
    "document_title": "extracted title",
    "domain": "social_analytics/kpi_analytics/combined"
  }}
}}

Important:
- Preserve Korean text exactly as written
- Keep SQL queries with original formatting and indentation
- Identify table relationships from JOIN clauses
- Return ONLY valid JSON, no markdown code blocks"""
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response into structured data"""
        try:
            # Try to extract JSON from response
            # Handle cases where LLM might wrap in markdown code blocks
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            elif response_clean.startswith("```"):
                response_clean = response_clean[3:]
            
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            # Parse JSON
            structured_data = json.loads(response_clean.strip())
            return structured_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
    
    def _validate_structure(self, data: Dict) -> None:
        """Validate the structure of interpreted data"""
        required_keys = ["questions", "tables", "sql_queries", "metadata"]
        
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key in LLM response: {key}")
        
        # Validate questions
        if not isinstance(data["questions"], list):
            raise ValueError("'questions' must be a list")
        
        # Validate tables
        if not isinstance(data["tables"], list):
            raise ValueError("'tables' must be a list")
        
        # Validate queries
        if not isinstance(data["sql_queries"], list):
            raise ValueError("'sql_queries' must be a list")
        
        logger.debug("Structure validation passed")
    
    def _create_empty_structure(self) -> Dict:
        """Create empty structure when LLM is not available"""
        return {
            "questions": [],
            "tables": [],
            "sql_queries": [],
            "metadata": {
                "document_title": "Unknown",
                "domain": "unknown"
            }
        }
    
    def parse_pdf(self, pdf_path: str, use_llm: bool = True) -> Dict:
        """
        Full pipeline: extract raw content and optionally interpret with LLM.
        
        Args:
            pdf_path: Path to PDF file
            use_llm: Whether to use LLM for interpretation
            
        Returns:
            Dictionary with structured information
        """
        # Step 1: Extract raw content
        raw_content = self.extract_raw_content(pdf_path)
        
        # Step 2: Interpret with LLM (optional)
        if use_llm and self.llm_client:
            structured_data = self.interpret_with_llm(raw_content)
        else:
            structured_data = self._create_empty_structure()
            # Add raw content for manual processing
            structured_data["raw_content"] = raw_content.to_dict()
        
        return structured_data


def extract_pdf(pdf_path: str, llm_client=None, use_llm: bool = True) -> Dict:
    """
    Convenience function to extract content from a PDF.
    
    Args:
        pdf_path: Path to PDF file
        llm_client: Optional LLM client for interpretation
        use_llm: Whether to use LLM for interpretation
        
    Returns:
        Dictionary with structured information
    """
    parser = PDFParser(llm_client=llm_client)
    return parser.parse_pdf(pdf_path, use_llm=use_llm)
