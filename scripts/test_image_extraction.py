#!/usr/bin/env python3
"""
Quick test script to validate embedded image extraction functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from genie.parsing.pdf_parser import PDFParser, PDFContent, EmbeddedImage, is_pymupdf_available


def test_dataclass_structure():
    """Test that PDFContent and EmbeddedImage are properly defined."""
    print("Testing dataclass structure...")

    # Check EmbeddedImage fields
    expected_fields = {'image', 'page_number', 'image_index', 'width', 'height', 'format', 'xref'}
    actual_fields = set(EmbeddedImage.__annotations__.keys())

    assert expected_fields == actual_fields, f"EmbeddedImage fields mismatch: {actual_fields}"
    print("✓ EmbeddedImage has correct fields")

    # Check PDFContent fields
    expected_fields = {'text_by_page', 'tables_by_page', 'images', 'embedded_images', 'metadata'}
    actual_fields = set(PDFContent.__annotations__.keys())

    assert expected_fields == actual_fields, f"PDFContent fields mismatch: {actual_fields}"
    print("✓ PDFContent has correct fields (including embedded_images)")


def test_parser_method():
    """Test that PDFParser has the extraction method."""
    print("\nTesting parser methods...")

    parser = PDFParser(llm_client=None, use_images=False)

    # Check method exists
    assert hasattr(parser, '_extract_embedded_images'), "Missing _extract_embedded_images method"
    print("✓ PDFParser has _extract_embedded_images method")

    # Check method is callable
    assert callable(parser._extract_embedded_images), "_extract_embedded_images is not callable"
    print("✓ _extract_embedded_images is callable")


def test_pymupdf_availability():
    """Test PyMuPDF availability check."""
    print("\nTesting PyMuPDF availability...")

    available = is_pymupdf_available()
    print(f"PyMuPDF available: {available}")

    if not available:
        print("⚠ PyMuPDF not installed - install with: pip install PyMuPDF")
    else:
        print("✓ PyMuPDF is available")

    return available


def main():
    print("=" * 60)
    print("Embedded Image Extraction - Validation Test")
    print("=" * 60)

    try:
        # Test 1: Data structures
        test_dataclass_structure()

        # Test 2: Parser methods
        test_parser_method()

        # Test 3: PyMuPDF
        pymupdf_ok = test_pymupdf_availability()

        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        print("✓ All structural tests passed!")

        if not pymupdf_ok:
            print("⚠ Warning: PyMuPDF not installed")
            print("  Install with: .venv/bin/python -m pip install PyMuPDF")
        else:
            print("✓ Ready to extract embedded images!")

        print("\nNext steps:")
        print("1. Test with a real PDF:")
        print("   .venv/bin/python scripts/extract_embedded_images.py --pdf <path>")
        print("\n2. Or use programmatically:")
        print("   from genie.parsing.pdf_parser import PDFParser")
        print("   parser = PDFParser()")
        print("   content = parser.extract_raw_content('file.pdf')")
        print("   print(content.embedded_images)")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
