"""Document parsing module for converting PDFs and Markdown to structured requirements."""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm

from src.parsing.pdf_parser import PDFParser
from src.parsing.markdown_parser import MarkdownParser
from src.parsing.requirements_structurer import RequirementsStructurer
from src.parsing.llm_enricher import LLMEnricher
from src.parsing.markdown_generator import generate_markdown
from src.llm.databricks_llm import DatabricksFoundationModelClient
from src.utils.parse_cache import ParseCacheManager


async def parse_documents_async(
    input_dir: str,
    output_path: str = "data/parsed_requirements.md",
    llm_model: str = "databricks-gpt-5-2",
    vision_model: str = "databricks-claude-sonnet-4",
    use_llm: bool = True,
    domain: str = "combined",
    databricks_host: Optional[str] = None,
    databricks_token: Optional[str] = None,
    verbose: bool = True,
    max_concurrent_pdfs: int = 3,
    force: bool = False,
    cache_file: str = ".parse_cache.json",
    no_cache: bool = False
) -> Dict[str, Any]:
    """
    Async version of parse_documents.
    Parse PDF and markdown documents into structured requirements format with concurrent processing.
    
    This function:
    1. Checks cache validity (unless force=True or no_cache=True)
    2. Extracts content from PDF files (using pdfplumber + optional LLM) - ASYNC
    3. Extracts content from markdown files (using regex patterns)
    4. Structures and combines the data
    5. Optionally enriches with LLM
    6. Generates output markdown in standard format
    7. Updates cache for future runs
    
    Args:
        input_dir: Directory containing PDF and markdown files
        output_path: Output file path for generated markdown
        llm_model: Foundation model for text-based LLM enrichment (e.g., databricks-gpt-5-2)
        vision_model: Foundation model for image-based PDF parsing (e.g., databricks-claude-sonnet-4)
        use_llm: Whether to use LLM for interpretation and enrichment
        domain: Domain type (social_analytics, kpi_analytics, combined)
        databricks_host: Databricks workspace URL
        databricks_token: Databricks personal access token
        verbose: Print progress messages
        max_concurrent_pdfs: Maximum number of PDFs to process concurrently
        force: Force re-parsing even if cache is valid
        cache_file: Path to cache metadata file (default: .parse_cache.json)
        no_cache: Disable caching entirely
        
    Returns:
        dict: Parsing results with metadata:
            - output_path: Path to generated markdown file
            - questions_count: Number of questions extracted
            - tables_count: Number of tables extracted
            - queries_count: Number of SQL queries extracted
            - used_llm: Whether LLM was used
            - cache_used: Whether cached results were used
        
    Raises:
        ValueError: If input directory doesn't exist or credentials are missing (when use_llm=True)
        Exception: If parsing fails
    """
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        raise ValueError(f"Input directory not found: {input_dir}")
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # CACHE CHECK: Skip parsing if cache is valid
    # =========================================================================
    cache_used = False
    
    if not no_cache and not force:
        # Build cache config for validation
        cache_config = {
            "llm_model": llm_model,
            "vision_model": vision_model,
            "use_llm": use_llm,
            "domain": domain
        }
        
        # Check if cache is valid
        cache_manager = ParseCacheManager(cache_file=cache_file)
        
        if cache_manager.is_valid(output_path, input_dir, cache_config, verbose=verbose):
            # Cache is valid - return cached results from output file
            if verbose:
                print("✓ Using cached results (no changes detected)")
                print()
            
            # Load cached metadata
            cached_metadata = cache_manager.get_metadata()
            
            # Return results based on cached output
            cache_used = True
            results = {
                "output_path": str(output_path),
                "questions_count": 0,  # Not available from cache
                "tables_count": 0,      # Not available from cache
                "queries_count": 0,     # Not available from cache
                "sections_count": 0,    # Not available from cache
                "used_llm": use_llm,
                "domain": domain,
                "cache_used": True,
                "cached_timestamp": cached_metadata.get("timestamp") if cached_metadata else None
            }
            
            return results
        elif verbose and force:
            print("⚠️  Force re-parsing (--force flag)")
            print()
    elif verbose and no_cache:
        print("⚠️  Cache disabled (--no-cache flag)")
        print()
    
    # Initialize LLM clients if needed
    llm_client = None
    vision_client = None
    
    if use_llm:
        # Get credentials
        host = databricks_host or os.getenv("DATABRICKS_HOST")
        token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        
        if not host or not token:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN must be set when using LLM. "
                "Either set environment variables or pass as arguments."
            )
        
        try:
            # Initialize text-based LLM client for enrichment
            llm_client = DatabricksFoundationModelClient(model_name=llm_model)
            if verbose:
                print(f"   Initialized LLM client for enrichment: {llm_model}")
            
            # Initialize vision model client for PDF image parsing
            vision_client = DatabricksFoundationModelClient(model_name=vision_model)
            if verbose:
                print(f"   Initialized vision client for image parsing: {vision_model}")
                
        except Exception as e:
            if verbose:
                print(f"   Warning: Failed to initialize LLM clients: {e}")
                print(f"   Continuing without LLM support")
            use_llm = False
            llm_client = None
            vision_client = None
    
    # =========================================================================
    # STEP 1: Extract content from PDFs (ASYNC)
    # =========================================================================
    if verbose:
        print("📄 Extracting content from PDF files...")
    
    pdf_data = await _extract_pdfs_async(input_dir, vision_client, use_llm, verbose, max_concurrent_pdfs)
    
    if verbose:
        print(f"   ✓ Extracted from PDFs: {len(pdf_data['questions'])} questions, "
              f"{len(pdf_data['tables'])} tables")
    
    # =========================================================================
    # STEP 2: Extract content from Markdown files
    # =========================================================================
    if verbose:
        print("📝 Extracting content from Markdown files...")
    
    md_data = _extract_markdown(input_dir, verbose)
    
    if verbose:
        print(f"   ✓ Extracted from Markdown: {len(md_data['questions'])} questions, "
              f"{len(md_data['tables'])} tables")
    
    # =========================================================================
    # STEP 3: Structure and combine data
    # =========================================================================
    if verbose:
        print("🔨 Structuring data...")
    
    structurer = RequirementsStructurer()
    doc = structurer.structure_data(pdf_data, md_data)
    doc = structurer.update_metadata(doc)
    
    if verbose:
        print(f"   ✓ Structured document: {len(doc.all_questions)} questions, "
              f"{len(doc.all_tables)} tables, {len(doc.sections)} sections")
    
    # =========================================================================
    # STEP 4: Enrich with LLM (optional)
    # =========================================================================
    if use_llm and llm_client:
        if verbose:
            print("✨ Enriching with LLM...")
        
        try:
            enricher = LLMEnricher(llm_client)
            doc = enricher.enrich_document(doc)
            
            if verbose:
                print("   ✓ Document enrichment complete")
        except Exception as e:
            if verbose:
                print(f"   Warning: Error during enrichment: {e}")
                print(f"   Continuing with un-enriched document")
    else:
        if verbose:
            print("⚠️  Skipping LLM enrichment")
    
    # =========================================================================
    # STEP 5: Generate output markdown
    # =========================================================================
    if verbose:
        print("📋 Generating markdown output...")
    
    markdown = generate_markdown(doc, output_path)
    
    if verbose:
        print(f"   ✓ Generated {len(markdown)} characters of markdown")
    
    # =========================================================================
    # UPDATE CACHE: Save metadata for future runs
    # =========================================================================
    if not no_cache:
        cache_config = {
            "llm_model": llm_model,
            "vision_model": vision_model,
            "use_llm": use_llm,
            "domain": domain
        }
        
        cache_manager = ParseCacheManager(cache_file=cache_file)
        if cache_manager.save(output_path, input_dir, cache_config):
            if verbose:
                print(f"   ✓ Cache updated: {cache_file}")
        else:
            if verbose:
                print(f"   ⚠️  Failed to update cache")
    
    # Return results
    results = {
        "output_path": str(output_path),
        "questions_count": len(doc.all_questions),
        "tables_count": len(doc.all_tables),
        "queries_count": len(doc.all_queries),
        "sections_count": len(doc.sections),
        "used_llm": use_llm and llm_client is not None,
        "domain": domain,
        "cache_used": False
    }
    
    return results


def parse_documents(
    input_dir: str,
    output_path: str = "data/parsed_requirements.md",
    llm_model: str = "databricks-gpt-5-2",
    vision_model: str = "databricks-claude-sonnet-4",
    use_llm: bool = True,
    domain: str = "combined",
    databricks_host: Optional[str] = None,
    databricks_token: Optional[str] = None,
    verbose: bool = True,
    max_concurrent_pdfs: int = 3,
    force: bool = False,
    cache_file: str = ".parse_cache.json",
    no_cache: bool = False
) -> Dict[str, Any]:
    """
    Synchronous wrapper for async document parsing.
    Parse PDF and markdown documents into structured requirements format with concurrent processing.
    
    This function:
    1. Checks cache validity (unless force=True or no_cache=True)
    2. Extracts content from PDF files (using pdfplumber + optional LLM) - CONCURRENT
    3. Extracts content from markdown files (using regex patterns)
    4. Structures and combines the data
    5. Optionally enriches with LLM
    6. Generates output markdown in standard format
    7. Updates cache for future runs
    
    Args:
        input_dir: Directory containing PDF and markdown files
        output_path: Output file path for generated markdown
        llm_model: Foundation model for text-based LLM enrichment (e.g., databricks-gpt-5-2)
        vision_model: Foundation model for image-based PDF parsing (e.g., databricks-claude-sonnet-4)
        use_llm: Whether to use LLM for interpretation and enrichment
        domain: Domain type (social_analytics, kpi_analytics, combined)
        databricks_host: Databricks workspace URL
        databricks_token: Databricks personal access token
        verbose: Print progress messages
        max_concurrent_pdfs: Maximum number of PDFs to process concurrently (default: 3)
        force: Force re-parsing even if cache is valid
        cache_file: Path to cache metadata file (default: .parse_cache.json)
        no_cache: Disable caching entirely
        
    Returns:
        dict: Parsing results with metadata:
            - output_path: Path to generated markdown file
            - questions_count: Number of questions extracted
            - tables_count: Number of tables extracted
            - queries_count: Number of SQL queries extracted
            - used_llm: Whether LLM was used
            - cache_used: Whether cached results were used
        
    Raises:
        ValueError: If input directory doesn't exist or credentials are missing (when use_llm=True)
        Exception: If parsing fails
    """
    return asyncio.run(parse_documents_async(
        input_dir=input_dir,
        output_path=output_path,
        llm_model=llm_model,
        vision_model=vision_model,
        use_llm=use_llm,
        domain=domain,
        databricks_host=databricks_host,
        databricks_token=databricks_token,
        verbose=verbose,
        max_concurrent_pdfs=max_concurrent_pdfs,
        force=force,
        cache_file=cache_file,
        no_cache=no_cache
    ))


async def _extract_pdfs_async(
    input_dir: str, 
    vision_client, 
    use_llm: bool, 
    verbose: bool,
    max_concurrent: int = 3
) -> dict:
    """
    Extract content from PDF files in directory using vision model for image parsing.
    Processes PDFs concurrently with progress bar.
    
    Args:
        input_dir: Directory containing PDF files
        vision_client: LLM client for vision-based parsing
        use_llm: Whether to use LLM for interpretation
        verbose: Whether to print progress messages
        max_concurrent: Maximum number of PDFs to process concurrently
    
    Returns:
        Dictionary with extracted questions, tables, and queries
    """
    pdf_dir = Path(input_dir)
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if verbose:
        print(f"   Found {len(pdf_files)} PDF files")
    
    if not pdf_files:
        return {"questions": [], "tables": [], "sql_queries": [], "metadata": {}}
    
    # Initialize parser with per-page processing (2.21x faster based on benchmarks)
    # per_page=True: processes each page separately with async parallel execution
    pdf_parser = PDFParser(llm_client=vision_client, use_images=True, per_page=True)
    
    all_pdf_data = {
        "questions": [],
        "tables": [],
        "sql_queries": [],
        "metadata": {}
    }
    
    # Create semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_pdf(pdf_file: Path):
        """Process a single PDF with semaphore control."""
        async with semaphore:
            try:
                pdf_content = await pdf_parser.parse_pdf_async(str(pdf_file), use_llm=use_llm)
                return pdf_file, pdf_content, None
            except Exception as e:
                return pdf_file, None, e
    
    # Create tasks for all PDFs
    tasks = [process_pdf(pdf_file) for pdf_file in pdf_files]
    
    # Process with progress bar
    if verbose:
        print(f"   Processing PDFs (max {max_concurrent} concurrent)...")
        results = await tqdm_asyncio.gather(*tasks, desc="   PDFs", unit="file")
    else:
        results = await asyncio.gather(*tasks)
    
    # Collect results
    for pdf_file, pdf_content, error in results:
        if error:
            if verbose:
                print(f"   Error processing {pdf_file.name}: {error}")
        elif pdf_content:
            # Merge data
            all_pdf_data["questions"].extend(pdf_content.get("questions", []))
            all_pdf_data["tables"].extend(pdf_content.get("tables", []))
            all_pdf_data["sql_queries"].extend(pdf_content.get("sql_queries", []))
    
    return all_pdf_data


def _extract_pdfs(input_dir: str, vision_client, use_llm: bool, verbose: bool) -> dict:
    """
    Synchronous wrapper for async PDF extraction.
    Extract content from PDF files in directory using vision model for image parsing.
    """
    return asyncio.run(_extract_pdfs_async(input_dir, vision_client, use_llm, verbose))


def _extract_markdown(input_dir: str, verbose: bool) -> dict:
    """Extract content from markdown files in directory."""
    md_dir = Path(input_dir)
    md_files = list(md_dir.glob("*.md"))
    
    if verbose:
        print(f"   Found {len(md_files)} markdown files")
    
    if not md_files:
        return {"questions": [], "tables": [], "sql_queries": [], "metadata": {}}
    
    md_parser = MarkdownParser()
    
    all_md_data = {
        "questions": [],
        "tables": [],
        "sql_queries": [],
        "metadata": {}
    }
    
    for md_file in md_files:
        try:
            if verbose:
                print(f"   Processing: {md_file.name}")
            
            md_content = md_parser.parse_file(str(md_file))
            
            # Merge data
            all_md_data["questions"].extend(md_content.get("questions", []))
            all_md_data["tables"].extend(md_content.get("tables", []))
            all_md_data["sql_queries"].extend(md_content.get("sql_queries", []))
            
        except Exception as e:
            if verbose:
                print(f"   Error processing {md_file.name}: {e}")
    
    return all_md_data
