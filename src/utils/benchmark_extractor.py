"""Extract benchmark questions directly from requirements documents.

This module bypasses LLM generation and extracts benchmarks directly from
structured requirements documents (like demo_requirements.md).
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_benchmarks_from_requirements(
    requirements_path: str,
    faq_section_title: str = "## 📊 질문 목록 (FAQ)"
) -> List[Dict[str, Any]]:
    """
    Extract benchmark questions directly from a requirements document.
    
    This function looks for a FAQ section in the requirements document and
    extracts all numbered questions as benchmarks. This ensures 100% coverage
    of intended test questions without relying on LLM interpretation.
    
    Args:
        requirements_path: Path to the requirements document (e.g., demo_requirements.md)
        faq_section_title: The section header that marks the start of the FAQ section
        
    Returns:
        List of benchmark dictionaries with structure:
        [
            {
                "question": "원본 질문 텍스트",
                "expected_sql": None,
                "expected_accuracy": None
            },
            ...
        ]
        
    Example:
        >>> benchmarks = extract_benchmarks_from_requirements("data/demo_requirements.md")
        >>> len(benchmarks)
        27
        >>> benchmarks[0]
        {
            "question": "지난 주 가장 많이 팔린 제품은 무엇인가요?",
            "expected_sql": None,
            "expected_accuracy": None
        }
    """
    doc_path = Path(requirements_path)
    
    if not doc_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {doc_path}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    benchmarks = []
    
    # Pattern to match numbered questions (1. question, 2. question, etc.)
    pattern = r'^(\d+)\.\s+(.+)$'
    
    lines = content.split('\n')
    in_faq_section = False
    
    for line in lines:
        # Detect FAQ section
        if faq_section_title in line:
            in_faq_section = True
            continue
        
        # Stop at the next major section (marked by ---)
        if in_faq_section and line.startswith('---'):
            break
        
        # Extract numbered questions
        if in_faq_section:
            match = re.match(pattern, line.strip())
            if match:
                question_num = match.group(1)
                question_text = match.group(2)
                benchmarks.append({
                    "question": question_text,
                    "expected_sql": None,
                    "expected_accuracy": None
                })
    
    return benchmarks


def extract_sample_queries_as_benchmarks(
    requirements_path: str
) -> List[Dict[str, Any]]:
    """
    Extract sample SQL queries from requirements document as benchmarks.
    
    This function looks for sections with **Sample Query:** patterns and extracts
    the SQL queries along with the section context (title, KPIs, etc.) to create
    benchmarks with expected_sql.
    
    Pattern:
        ## Section Title
        **Table:** table_name
        **Related KPI:** KPI description
        **Sample Query:**
        ```sql
        SELECT ...
        ```
    
    Args:
        requirements_path: Path to the requirements document
        
    Returns:
        List of benchmark dictionaries with expected_sql filled in
        
    Example:
        >>> benchmarks = extract_sample_queries_as_benchmarks("data/demo_requirements.md")
        >>> benchmarks[0]
        {
            "question": "Daily Sales Summary (Daily Sales, Revenue, Customer Count, ARPU)",
            "expected_sql": "SELECT t.t_dat as transaction_date...",
            "expected_accuracy": "High"
        }
    """
    doc_path = Path(requirements_path)
    
    if not doc_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {doc_path}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    benchmarks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for section headers (## Title)
        if line.startswith('## ') and not line.startswith('###'):
            section_title = line.replace('##', '').strip()
            
            # Extract metadata from next lines
            table_name = None
            related_kpi = None
            
            j = i + 1
            while j < len(lines) and not lines[j].startswith('##'):
                if lines[j].startswith('**Table:**'):
                    table_name = lines[j].replace('**Table:**', '').strip()
                elif lines[j].startswith('**Related KPI:**'):
                    related_kpi = lines[j].replace('**Related KPI:**', '').strip()
                elif lines[j].startswith('**Sample Query:**'):
                    # Found a sample query - extract the SQL
                    sql_lines = []
                    k = j + 1
                    
                    # Skip to the start of SQL block
                    while k < len(lines) and not lines[k].strip().startswith('```sql'):
                        k += 1
                    
                    if k < len(lines):
                        k += 1  # Skip the ```sql line
                        
                        # Extract SQL until we hit the closing ```
                        while k < len(lines) and not lines[k].strip().startswith('```'):
                            sql_lines.append(lines[k])
                            k += 1
                        
                        # Build the SQL query
                        if sql_lines:
                            expected_sql = '\n'.join(sql_lines)
                            
                            # Create question from section title and KPI
                            if related_kpi:
                                question = f"{section_title} ({related_kpi})"
                            else:
                                question = section_title
                            
                            # Remove emojis from question for cleaner text
                            question = re.sub(r'[^\w\s\(\),\-:가-힣]', '', question).strip()
                            
                            benchmarks.append({
                                "question": question,
                                "expected_sql": expected_sql,
                                "expected_accuracy": "High",  # Sample queries should have high accuracy
                                "table": table_name,
                                "source": "sample_query"
                            })
                    
                    break  # Found and processed the sample query for this section
                
                j += 1
        
        i += 1
    
    return benchmarks


def extract_benchmarks_from_multiple_sections(
    requirements_path: str,
    section_patterns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extract benchmark questions from multiple sections in a requirements document.
    
    This is useful when benchmarks are scattered across different sections
    (e.g., "FAQ", "Common Questions", "Test Scenarios", etc.)
    
    Args:
        requirements_path: Path to the requirements document
        section_patterns: List of regex patterns to match section titles.
                         Defaults to common FAQ/question section patterns.
        
    Returns:
        List of benchmark dictionaries
    """
    if section_patterns is None:
        section_patterns = [
            r"##\s*.*질문.*",  # Korean: questions
            r"##\s*.*FAQ.*",
            r"##\s*.*Questions.*",
            r"##\s*.*Test.*",
            r"##\s*.*Benchmark.*"
        ]
    
    doc_path = Path(requirements_path)
    
    if not doc_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {doc_path}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    benchmarks = []
    question_pattern = r'^(\d+)\.\s+(.+)$'
    lines = content.split('\n')
    in_question_section = False
    
    for line in lines:
        # Check if we're entering a question section
        for pattern in section_patterns:
            if re.match(pattern, line):
                in_question_section = True
                break
        
        # Stop at the next major section
        if in_question_section and line.startswith('---'):
            in_question_section = False
            continue
        
        # Extract numbered questions
        if in_question_section:
            match = re.match(question_pattern, line.strip())
            if match:
                question_text = match.group(2)
                # Avoid duplicates
                if not any(bm['question'] == question_text for bm in benchmarks):
                    benchmarks.append({
                        "question": question_text,
                        "expected_sql": None,
                        "expected_accuracy": None
                    })
    
    return benchmarks


def merge_benchmarks_into_config(
    config: Dict[str, Any],
    benchmarks: List[Dict[str, Any]],
    replace: bool = True
) -> Dict[str, Any]:
    """
    Merge extracted benchmarks into a Genie space configuration.
    
    Args:
        config: The Genie space configuration dictionary
        benchmarks: List of benchmark dictionaries to add
        replace: If True, replace existing benchmarks. If False, append to existing.
        
    Returns:
        Updated configuration dictionary
    """
    if "genie_space_config" in config:
        # Handle wrapped config format
        if replace:
            config["genie_space_config"]["benchmark_questions"] = benchmarks
        else:
            existing = config["genie_space_config"].get("benchmark_questions", [])
            # Avoid duplicates
            existing_questions = {bm["question"] for bm in existing}
            new_benchmarks = [bm for bm in benchmarks if bm["question"] not in existing_questions]
            config["genie_space_config"]["benchmark_questions"] = existing + new_benchmarks
    else:
        # Handle direct config format
        if replace:
            config["benchmark_questions"] = benchmarks
        else:
            existing = config.get("benchmark_questions", [])
            existing_questions = {bm["question"] for bm in existing}
            new_benchmarks = [bm for bm in benchmarks if bm["question"] not in existing_questions]
            config["benchmark_questions"] = existing + new_benchmarks
    
    return config


def validate_benchmarks(benchmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate extracted benchmarks and return validation report.
    
    Args:
        benchmarks: List of benchmark dictionaries
        
    Returns:
        Validation report dictionary with:
        {
            "total_count": int,
            "valid_count": int,
            "invalid_count": int,
            "issues": List[str]
        }
    """
    report = {
        "total_count": len(benchmarks),
        "valid_count": 0,
        "invalid_count": 0,
        "issues": []
    }
    
    for i, bm in enumerate(benchmarks, 1):
        # Check required fields
        if "question" not in bm or not bm["question"]:
            report["issues"].append(f"Benchmark {i}: Missing or empty 'question' field")
            report["invalid_count"] += 1
            continue
        
        # Check question length
        if len(bm["question"]) < 5:
            report["issues"].append(f"Benchmark {i}: Question too short (< 5 chars): '{bm['question']}'")
            report["invalid_count"] += 1
            continue
        
        report["valid_count"] += 1
    
    return report


def extract_all_benchmarks(
    requirements_path: str,
    include_faq: bool = True,
    include_sample_queries: bool = True,
    faq_section_title: str = "## 📊 질문 목록 (FAQ)"
) -> List[Dict[str, Any]]:
    """
    Extract all benchmarks from requirements document.
    
    This combines FAQ questions and sample SQL queries into a complete
    benchmark suite.
    
    Args:
        requirements_path: Path to the requirements document
        include_faq: Whether to include FAQ questions
        include_sample_queries: Whether to include sample SQL queries
        faq_section_title: Title of the FAQ section
        
    Returns:
        Combined list of all benchmarks
    """
    all_benchmarks = []
    
    if include_faq:
        faq_benchmarks = extract_benchmarks_from_requirements(
            requirements_path,
            faq_section_title
        )
        for bm in faq_benchmarks:
            bm['source'] = 'faq'
        all_benchmarks.extend(faq_benchmarks)
    
    if include_sample_queries:
        sample_query_benchmarks = extract_sample_queries_as_benchmarks(
            requirements_path
        )
        all_benchmarks.extend(sample_query_benchmarks)
    
    return all_benchmarks


if __name__ == "__main__":
    """Example usage and testing."""
    import json
    
    print("="*80)
    print("BENCHMARK EXTRACTION - COMPREHENSIVE TEST")
    print("="*80)
    
    # Extract FAQ benchmarks
    print("\n1. Extracting FAQ questions...")
    faq_benchmarks = extract_benchmarks_from_requirements("data/demo_requirements.md")
    print(f"   ✓ Extracted {len(faq_benchmarks)} FAQ questions")
    
    # Extract sample query benchmarks
    print("\n2. Extracting sample SQL queries...")
    sample_benchmarks = extract_sample_queries_as_benchmarks("data/demo_requirements.md")
    print(f"   ✓ Extracted {len(sample_benchmarks)} sample queries")
    
    # Show sample query examples
    if sample_benchmarks:
        print(f"\n   Sample query examples:")
        for i, bm in enumerate(sample_benchmarks[:3], 1):
            print(f"   {i}. {bm['question']}")
            if bm.get('expected_sql'):
                sql_preview = bm['expected_sql'][:100].replace('\n', ' ')
                print(f"      SQL: {sql_preview}...")
    
    # Extract all benchmarks
    print("\n3. Extracting ALL benchmarks (FAQ + Sample Queries)...")
    all_benchmarks = extract_all_benchmarks("data/demo_requirements.md")
    print(f"   ✓ Total benchmarks: {len(all_benchmarks)}")
    print(f"     - FAQ questions: {len(faq_benchmarks)}")
    print(f"     - Sample queries: {len(sample_benchmarks)}")
    
    # Validate
    print("\n4. Validating benchmarks...")
    report = validate_benchmarks(all_benchmarks)
    print(f"   Total: {report['total_count']}")
    print(f"   Valid: {report['valid_count']}")
    print(f"   Invalid: {report['invalid_count']}")
    
    if report['issues']:
        print(f"\n   Issues:")
        for issue in report['issues']:
            print(f"   - {issue}")
    else:
        print(f"   ✓ All benchmarks are valid!")
    
    # Save to files
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save FAQ benchmarks
    with open(output_dir / "faq_benchmarks.json", 'w', encoding='utf-8') as f:
        json.dump(faq_benchmarks, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved FAQ benchmarks to: output/faq_benchmarks.json")
    
    # Save sample query benchmarks
    with open(output_dir / "sample_query_benchmarks.json", 'w', encoding='utf-8') as f:
        json.dump(sample_benchmarks, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved sample query benchmarks to: output/sample_query_benchmarks.json")
    
    # Save all benchmarks
    with open(output_dir / "all_benchmarks.json", 'w', encoding='utf-8') as f:
        json.dump(all_benchmarks, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved all benchmarks to: output/all_benchmarks.json")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"FAQ Questions:    {len(faq_benchmarks)} (questions without SQL)")
    print(f"Sample Queries:   {len(sample_benchmarks)} (questions WITH expected SQL)")
    print(f"Total Benchmarks: {len(all_benchmarks)}")
    print("="*80)
