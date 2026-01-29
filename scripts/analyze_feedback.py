"""
Analyze parsed feedback to generate insights and reports
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsing.feedback_parser import parse_feedback_file


def print_separator(char="=", length=80):
    print(char * length)


def analyze_feedback(filepath: str):
    """Analyze feedback file and generate detailed report"""
    parser = parse_feedback_file(filepath)
    
    # Summary
    summary = parser.get_summary()
    print_separator()
    print("📊 GENIE SPACE FEEDBACK ANALYSIS")
    print_separator()
    print(f"\n📈 Overall Statistics:")
    print(f"  • Total Questions: {summary['total_entries']}")
    print(f"  • Success Rate: {summary['success_rate']}")
    print(f"  • Good Responses: {summary['good_assessments']}")
    print(f"  • Bad Responses: {summary['bad_assessments']}")
    print(f"  • Empty Results: {summary['empty_results']}")
    
    # Failure reasons breakdown
    print(f"\n❌ Failure Reasons:")
    for reason, count in sorted(summary['score_reason_counts'].items(), 
                                 key=lambda x: x[1], reverse=True):
        percentage = (count / summary['total_entries']) * 100
        print(f"  • {reason}: {count} ({percentage:.1f}%)")
    
    # Detailed entry examples
    print(f"\n\n📋 Detailed Entry Examples:\n")
    print_separator("-")
    
    for idx, entry in enumerate(parser.entries[:3], 1):  # Show first 3
        print(f"\n[{idx}] Question: {entry.question}")
        print(f"    Assessment: {entry.assessment}")
        print(f"    Reasons: {', '.join(entry.score_reasons)}")
        print(f"    Empty Result: {entry.empty_result}")
        
        if entry.failure_reasoning:
            print(f"\n    💡 Failure Reasoning:")
            print(f"       {entry.failure_reasoning[:200]}...")
        
        if entry.model_output and entry.model_output_type == "text":
            print(f"\n    🤖 Model Output (Text):")
            print(f"       {entry.model_output[:150]}...")
        elif entry.model_output and entry.model_output_type == "SQL":
            lines = entry.model_output.split('\n')[:5]
            print(f"\n    🤖 Model Output (SQL - first 5 lines):")
            for line in lines:
                print(f"       {line}")
            if len(entry.model_output.split('\n')) > 5:
                print(f"       ... ({len(entry.model_output.split('\n'))} total lines)")
        
        if entry.ground_truth_sql:
            lines = entry.ground_truth_sql.split('\n')[:5]
            print(f"\n    ✅ Ground Truth SQL (first 5 lines):")
            for line in lines:
                print(f"       {line}")
            if len(entry.ground_truth_sql.split('\n')) > 5:
                print(f"       ... ({len(entry.ground_truth_sql.split('\n'))} total lines)")
        
        print_separator("-")
    
    # Category breakdown
    print(f"\n\n📊 Question Categories:\n")
    
    # Group by score reasons
    missing_columns = parser.get_entries_by_reason("Missing Columns")
    wrong_intent = parser.get_entries_by_reason("Wrong Intent")
    incomplete = parser.get_entries_by_reason("Incomplete Output")
    empty_result = parser.get_entries_by_reason("Empty Result")
    filter_issue = parser.get_entries_by_reason("Filter Issue")
    
    print(f"Missing Columns ({len(missing_columns)} questions):")
    for e in missing_columns[:3]:
        print(f"  • {e.question}")
    if len(missing_columns) > 3:
        print(f"  ... and {len(missing_columns) - 3} more")
    
    print(f"\nWrong Intent ({len(wrong_intent)} questions):")
    for e in wrong_intent:
        print(f"  • {e.question}")
    
    print(f"\nIncomplete Output ({len(incomplete)} questions):")
    for e in incomplete:
        print(f"  • {e.question}")
    
    print(f"\nEmpty Result ({len(empty_result)} questions):")
    for e in empty_result:
        print(f"  • {e.question}")
    
    print(f"\nFilter Issue ({len(filter_issue)} questions):")
    for e in filter_issue:
        print(f"  • {e.question}")
    
    print_separator()
    print(f"\n✅ Analysis complete!")
    print(f"📁 Parsed data saved to: {filepath.replace('.md', '_parsed.json')}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_feedback.py <feedback_file.md>")
        sys.exit(1)
    
    analyze_feedback(sys.argv[1])
