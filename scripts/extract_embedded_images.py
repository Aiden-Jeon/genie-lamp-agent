#!/usr/bin/env python3
"""
Script to extract embedded images from PDFs.

Usage:
    .venv/bin/python scripts/extract_embedded_images.py --pdf path/to/file.pdf --output-dir output/images

This script demonstrates the new embedded image extraction capability:
- Extracts individual images embedded within PDF pages (diagrams, photos, charts)
- Saves them as separate files with metadata
- Different from page rendering (which converts entire pages to images)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from genie.parsing.pdf_parser import PDFParser, is_pymupdf_available

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_and_save_images(pdf_path: str, output_dir: str):
    """
    Extract embedded images from PDF and save them to disk.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save extracted images
    """
    # Check if PyMuPDF is available
    if not is_pymupdf_available():
        logger.error("PyMuPDF is not installed. Install it with: pip install PyMuPDF")
        sys.exit(1)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Extracting images from: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")

    # Create parser (no LLM needed for extraction)
    parser = PDFParser(llm_client=None, use_images=False)

    # Extract raw content (including embedded images)
    raw_content = parser.extract_raw_content(pdf_path)

    # Report results
    logger.info(f"\nExtraction Results:")
    logger.info(f"  Pages: {len(raw_content.text_by_page)}")
    logger.info(f"  Tables: {sum(len(t) for t in raw_content.tables_by_page)}")
    logger.info(f"  Embedded images: {len(raw_content.embedded_images)}")

    if not raw_content.embedded_images:
        logger.warning("No embedded images found in PDF")
        return

    # Save each embedded image
    pdf_name = Path(pdf_path).stem
    saved_count = 0

    for embedded_img in raw_content.embedded_images:
        try:
            # Create filename with metadata
            filename = f"{pdf_name}_page{embedded_img.page_number}_img{embedded_img.image_index}.{embedded_img.format.lower()}"
            output_file = output_path / filename

            # Save image
            embedded_img.image.save(output_file, format=embedded_img.format)

            logger.info(f"Saved: {filename} ({embedded_img.width}x{embedded_img.height} {embedded_img.format})")
            saved_count += 1

        except Exception as e:
            logger.error(f"Failed to save image from page {embedded_img.page_number}: {e}")

    logger.info(f"\nSuccessfully saved {saved_count}/{len(raw_content.embedded_images)} images to {output_dir}")

    # Print summary by page
    page_counts = {}
    for embedded_img in raw_content.embedded_images:
        page_num = embedded_img.page_number
        page_counts[page_num] = page_counts.get(page_num, 0) + 1

    logger.info("\nImages per page:")
    for page_num in sorted(page_counts.keys()):
        logger.info(f"  Page {page_num}: {page_counts[page_num]} images")


def main():
    parser = argparse.ArgumentParser(
        description="Extract embedded images from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from a single PDF
  .venv/bin/python scripts/extract_embedded_images.py --pdf real_requirements/inputs/doc.pdf --output-dir output/images

  # Extract to a custom directory
  .venv/bin/python scripts/extract_embedded_images.py --pdf sample.pdf --output-dir /tmp/extracted_images
        """
    )

    parser.add_argument(
        '--pdf',
        type=str,
        required=True,
        help='Path to PDF file'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/images',
        help='Directory to save extracted images (default: output/images)'
    )

    args = parser.parse_args()

    # Validate PDF exists
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        sys.exit(1)

    # Extract and save images
    extract_and_save_images(args.pdf, args.output_dir)


if __name__ == "__main__":
    main()
