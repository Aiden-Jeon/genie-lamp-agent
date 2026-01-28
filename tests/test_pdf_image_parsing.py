"""Test script for image-based PDF parsing with LLM.

NOTE: This test makes real LLM API calls (including vision models) which can incur significant costs.
Set environment variable RUN_LLM_TESTS=true to enable this test.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from src.llm.databricks_llm import DatabricksFoundationModelClient
from src.parsing.pdf_parser import PDFParser


@pytest.mark.llm
@pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "true",
    reason="Skipped: Makes real LLM API calls with vision models (HIGH COST). Set RUN_LLM_TESTS=true to run."
)
def test_single_page_pdf():
    """Test parsing a single PDF with image-based approach."""
    print("=" * 80)
    print("🧪 Testing Image-Based PDF Parsing")
    print("=" * 80)
    print()
    
    # Find a test PDF
    pdf_dir = Path("real_requirements")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in real_requirements/")
        return False
    
    # Use the first (smallest) PDF for testing
    test_pdf = min(pdf_files, key=lambda p: p.stat().st_size)
    print(f"📄 Test PDF: {test_pdf.name}")
    print(f"   Size: {test_pdf.stat().st_size / 1024:.1f} KB")
    print()
    
    try:
        # Initialize LLM client
        print("🔧 Initializing LLM client...")
        llm_client = DatabricksFoundationModelClient(
            model_name=os.getenv("LLM_MODEL_NAME", "databricks-claude-sonnet-4")
        )
        print(f"   Model: {llm_client.model_name}")
        print(f"   Endpoint: {llm_client.endpoint_url}")
        print()
        
        # Initialize PDF parser with image extraction
        print("📸 Extracting PDF pages as images...")
        parser = PDFParser(llm_client=llm_client, use_images=True)
        
        # Extract content
        raw_content = parser.extract_raw_content(str(test_pdf))
        
        print(f"✅ Extracted:")
        print(f"   Pages: {len(raw_content.images)}")
        print(f"   Images: {len(raw_content.images)} pages converted")
        if raw_content.images:
            first_img = raw_content.images[0]
            print(f"   Image size: {first_img.size} ({first_img.mode} mode)")
        print()
        
        # Test with just the first page to save time
        print("🤖 Sending first page to LLM for interpretation...")
        print("   (This may take 30-60 seconds)")
        print()
        
        # Create a smaller PDFContent with just first page
        from src.parsing.pdf_parser import PDFContent
        test_content = PDFContent(
            text_by_page=raw_content.text_by_page[:1] if raw_content.text_by_page else [],
            tables_by_page=raw_content.tables_by_page[:1] if raw_content.tables_by_page else [],
            images=raw_content.images[:1],
            metadata=raw_content.metadata
        )
        
        structured_data = parser.interpret_with_llm(test_content)
        
        print("✅ LLM Interpretation Complete!")
        print()
        print("📊 Results:")
        print(f"   Questions: {len(structured_data.get('questions', []))}")
        print(f"   Tables: {len(structured_data.get('tables', []))}")
        print(f"   SQL Queries: {len(structured_data.get('sql_queries', []))}")
        print()
        
        # Show sample data
        if structured_data.get('questions'):
            print("📝 Sample Question:")
            q = structured_data['questions'][0]
            print(f"   ID: {q.get('id')}")
            print(f"   Text: {q.get('text', '')[:100]}...")
            print(f"   Category: {q.get('category')}")
            print()
        
        if structured_data.get('tables'):
            print("📊 Sample Table:")
            t = structured_data['tables'][0]
            print(f"   Name: {t.get('full_name')}")
            print(f"   Description: {t.get('description', '')[:100]}...")
            print()
        
        print("=" * 80)
        print("✅ Image-Based PDF Parsing Test PASSED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Test FAILED")
        print(f"   Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print()
        
        import traceback
        print("Stack trace:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_single_page_pdf()
    sys.exit(0 if success else 1)

# Pytest-compatible wrapper
@pytest.mark.llm
@pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "true",
    reason="Skipped: Makes real LLM API calls with vision models (HIGH COST). Set RUN_LLM_TESTS=true to run."
)
def test_single_page_pdf_pytest():
    """Pytest wrapper for test_single_page_pdf."""
    result = test_single_page_pdf()
    assert result, "PDF image parsing test failed"
