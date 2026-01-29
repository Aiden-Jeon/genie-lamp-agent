"""
Export parsed feedback to CSV format for analysis in Excel/Sheets
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsing.feedback_parser import parse_feedback_file


def export_to_csv(filepath: str, output_path: str = None):
    """Export feedback entries to CSV"""
    parser = parse_feedback_file(filepath)
    
    if not output_path:
        output_path = filepath.replace('.md', '_summary.csv')
    
    # Write summary CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Question',
            'Assessment',
            'Score Reasons',
            'Empty Result',
            'Model Output Type',
            'Has Failure Analysis',
            'SQL Differences Present',
            'Ground Truth Available'
        ])
        
        # Data rows
        for entry in parser.entries:
            writer.writerow([
                entry.question,
                entry.assessment,
                ' | '.join(entry.score_reasons),
                'Yes' if entry.empty_result else 'No',
                entry.model_output_type,
                'Yes' if entry.failure_reasoning else 'No',
                'Yes' if entry.sql_differences else 'No',
                'Yes' if entry.ground_truth_sql else 'No'
            ])
    
    print(f"✅ CSV exported to: {output_path}")
    
    # Also create a detailed CSV with reasoning
    detailed_path = filepath.replace('.md', '_detailed.csv')
    with open(detailed_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Question',
            'Assessment',
            'Score Reasons',
            'Failure Reasoning',
            'SQL Differences',
            'Model Output (truncated)',
            'Ground Truth Available'
        ])
        
        # Data rows
        for entry in parser.entries:
            model_output_preview = entry.model_output[:200].replace('\n', ' ') if entry.model_output else ''
            
            writer.writerow([
                entry.question,
                entry.assessment,
                ' | '.join(entry.score_reasons),
                entry.failure_reasoning,
                entry.sql_differences,
                model_output_preview,
                'Yes' if entry.ground_truth_sql else 'No'
            ])
    
    print(f"✅ Detailed CSV exported to: {detailed_path}")
    
    return parser


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_feedback_csv.py <feedback_file.md>")
        sys.exit(1)
    
    export_to_csv(sys.argv[1])
