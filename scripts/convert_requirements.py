#!/usr/bin/env python3
"""
Requirements Conversion Pipeline
Converts real requirements (PDFs and markdown) into structured demo_requirements.md format.
"""

import argparse
import logging
import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from genie.parsing.pdf_parser import PDFParser
from genie.parsing.markdown_parser import MarkdownParser
from genie.parsing.requirements_structurer import RequirementsStructurer
from genie.parsing.llm_enricher import LLMEnricher
from genie.parsing.markdown_generator import generate_markdown
from genie.llm.databricks_llm import DatabricksFoundationModelClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RequirementsConverter:
    """
    Main pipeline for converting requirements documents.
    """
    
    def __init__(self, model_name: str = None, use_llm: bool = True):
        """
        Initialize converter.
        
        Args:
            model_name: Databricks model name for LLM (e.g., 'databricks-gpt-5-2')
            use_llm: Whether to use LLM for interpretation and enrichment
        """
        self.use_llm = use_llm
        self.llm_client = None
        
        if use_llm and model_name:
            try:
                self.llm_client = DatabricksFoundationModelClient(model_name=model_name)
                logger.info(f"Initialized LLM client with model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                logger.warning("Continuing without LLM support")
                self.use_llm = False
    
    def convert(self, input_dir: str, output_path: str, domain: str = "combined") -> str:
        """
        Main conversion pipeline.
        
        Args:
            input_dir: Directory containing PDF and markdown files
            output_path: Path for output markdown file
            domain: Domain type (social_analytics, kpi_analytics, combined)
            
        Returns:
            Path to generated markdown file
        """
        logger.info("="*80)
        logger.info("Requirements Conversion Pipeline")
        logger.info("="*80)
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output path: {output_path}")
        logger.info(f"Domain: {domain}")
        logger.info(f"Use LLM: {self.use_llm}")
        logger.info("="*80)
        
        # Stage 1: Extract content
        logger.info("\n" + "="*80)
        logger.info("STAGE 1: Extract Content")
        logger.info("="*80)
        
        pdf_data = self._extract_pdfs(input_dir)
        md_data = self._extract_markdown(input_dir)
        
        # Stage 2: Structure data
        logger.info("\n" + "="*80)
        logger.info("STAGE 2: Structure Data")
        logger.info("="*80)
        
        structured_doc = self._structure_data(pdf_data, md_data)
        
        # Stage 3: Enrich with LLM (optional)
        if self.use_llm and self.llm_client:
            logger.info("\n" + "="*80)
            logger.info("STAGE 3: Enrich with LLM")
            logger.info("="*80)
            
            enriched_doc = self._enrich_data(structured_doc)
        else:
            logger.info("\n" + "="*80)
            logger.info("STAGE 3: Enrich with LLM (SKIPPED)")
            logger.info("="*80)
            enriched_doc = structured_doc
        
        # Stage 4: Generate markdown
        logger.info("\n" + "="*80)
        logger.info("STAGE 4: Generate Markdown")
        logger.info("="*80)
        
        markdown = self._generate_output(enriched_doc, output_path)
        
        logger.info("\n" + "="*80)
        logger.info("CONVERSION COMPLETE")
        logger.info("="*80)
        logger.info(f"✓ Output saved to: {output_path}")
        logger.info(f"✓ Questions: {len(enriched_doc.all_questions)}")
        logger.info(f"✓ Tables: {len(enriched_doc.all_tables)}")
        logger.info(f"✓ Queries: {len(enriched_doc.all_queries)}")
        logger.info("="*80)
        
        return output_path
    
    def _extract_pdfs(self, input_dir: str) -> dict:
        """Extract content from PDF files"""
        pdf_dir = Path(input_dir)
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            logger.warning("No PDF files found")
            return {"questions": [], "tables": [], "sql_queries": [], "metadata": {}}
        
        # Use PDF parser
        pdf_parser = PDFParser(llm_client=self.llm_client)
        
        all_pdf_data = {
            "questions": [],
            "tables": [],
            "sql_queries": [],
            "metadata": {}
        }
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing PDF: {pdf_file.name}")
                pdf_content = pdf_parser.parse_pdf(str(pdf_file), use_llm=self.use_llm)
                
                # Merge data
                all_pdf_data["questions"].extend(pdf_content.get("questions", []))
                all_pdf_data["tables"].extend(pdf_content.get("tables", []))
                all_pdf_data["sql_queries"].extend(pdf_content.get("sql_queries", []))
                
                logger.info(f"✓ Extracted from {pdf_file.name}: "
                          f"{len(pdf_content.get('questions', []))} questions, "
                          f"{len(pdf_content.get('tables', []))} tables")
            
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
        
        logger.info(f"Total from PDFs: {len(all_pdf_data['questions'])} questions, "
                   f"{len(all_pdf_data['tables'])} tables")
        
        return all_pdf_data
    
    def _extract_markdown(self, input_dir: str) -> dict:
        """Extract content from markdown files"""
        md_dir = Path(input_dir)
        md_files = list(md_dir.glob("*.md"))
        
        logger.info(f"Found {len(md_files)} markdown files")
        
        if not md_files:
            logger.warning("No markdown files found")
            return {"questions": [], "tables": [], "sql_queries": [], "metadata": {}}
        
        # Use markdown parser
        md_parser = MarkdownParser()
        
        all_md_data = {
            "questions": [],
            "tables": [],
            "sql_queries": [],
            "metadata": {}
        }
        
        for md_file in md_files:
            try:
                logger.info(f"Processing markdown: {md_file.name}")
                md_content = md_parser.parse_file(str(md_file))
                
                # Merge data
                all_md_data["questions"].extend(md_content.get("questions", []))
                all_md_data["tables"].extend(md_content.get("tables", []))
                all_md_data["sql_queries"].extend(md_content.get("sql_queries", []))
                
                logger.info(f"✓ Extracted from {md_file.name}: "
                          f"{len(md_content.get('questions', []))} questions, "
                          f"{len(md_content.get('tables', []))} tables")
            
            except Exception as e:
                logger.error(f"Error processing {md_file.name}: {e}")
        
        logger.info(f"Total from markdown: {len(all_md_data['questions'])} questions, "
                   f"{len(all_md_data['tables'])} tables")
        
        return all_md_data
    
    def _structure_data(self, pdf_data: dict, md_data: dict):
        """Structure and combine data"""
        structurer = RequirementsStructurer()
        doc = structurer.structure_data(pdf_data, md_data)
        doc = structurer.update_metadata(doc)
        
        logger.info(f"Structured document: {len(doc.all_questions)} questions, "
                   f"{len(doc.all_tables)} tables, {len(doc.sections)} sections")
        
        return doc
    
    def _enrich_data(self, doc):
        """Enrich data with LLM"""
        if not self.llm_client:
            logger.warning("No LLM client available, skipping enrichment")
            return doc
        
        try:
            enricher = LLMEnricher(self.llm_client)
            enriched = enricher.enrich_document(doc)
            logger.info("Document enrichment complete")
            return enriched
        except Exception as e:
            logger.error(f"Error during enrichment: {e}")
            logger.warning("Continuing with un-enriched document")
            return doc
    
    def _generate_output(self, doc, output_path: str) -> str:
        """Generate final markdown output"""
        markdown = generate_markdown(doc, output_path)
        logger.info(f"Generated {len(markdown)} characters of markdown")
        return markdown


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert requirements documents to structured markdown format"
    )
    
    parser.add_argument(
        "--input-dir",
        type=str,
        default="real_requirements",
        help="Directory containing PDF and markdown files (default: real_requirements)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="data/converted_requirements.md",
        help="Output path for generated markdown (default: data/converted_requirements.md)"
    )
    
    parser.add_argument(
        "--domain",
        type=str,
        choices=["social_analytics", "kpi_analytics", "combined"],
        default="combined",
        help="Domain type (default: combined)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="databricks-gpt-5-2",
        help="Databricks model name for LLM (default: databricks-gpt-5-2)"
    )
    
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM usage (faster but less intelligent)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check input directory exists
    if not Path(args.input_dir).exists():
        logger.error(f"Input directory not found: {args.input_dir}")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run conversion
    try:
        converter = RequirementsConverter(
            model_name=args.model if not args.no_llm else None,
            use_llm=not args.no_llm
        )
        
        output_path = converter.convert(
            input_dir=args.input_dir,
            output_path=args.output,
            domain=args.domain
        )
        
        print(f"\n✅ SUCCESS! Output saved to: {output_path}")
        
    except KeyboardInterrupt:
        logger.info("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
