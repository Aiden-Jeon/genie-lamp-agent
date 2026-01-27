"""Build prompts for LLM to generate Genie space configurations."""

from pathlib import Path
from typing import Optional


class PromptBuilder:
    """Builds prompts for generating Genie space configurations."""
    
    def __init__(
        self,
        context_doc_path: str,
        output_doc_path: str,
        input_data_path: str,
        workspace_root: Optional[str] = None
    ):
        """
        Initialize the prompt builder.
        
        Args:
            context_doc_path: Path to the context document (curate_effective_genie.md)
            output_doc_path: Path to the output format document (genie_api.md)
            input_data_path: Path to the input data (demo_requirements.md)
            workspace_root: Root directory of the workspace (defaults to current directory)
        """
        if workspace_root is None:
            workspace_root = Path.cwd()
        else:
            workspace_root = Path(workspace_root)
            
        self.context_doc_path = workspace_root / context_doc_path
        self.output_doc_path = workspace_root / output_doc_path
        self.input_data_path = workspace_root / input_data_path
        
    def _read_file(self, path: Path) -> str:
        """Read file contents."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def build_prompt(self) -> str:
        """
        Build the complete prompt for the LLM.
        
        Returns:
            The formatted prompt string
        """
        # Read all documents
        context_content = self._read_file(self.context_doc_path)
        output_content = self._read_file(self.output_doc_path)
        input_content = self._read_file(self.input_data_path)
        
        # Build the structured prompt
        prompt = f"""# Instruction

You are an expert in creating Databricks Genie spaces. Your task is to analyze the provided requirements document and generate a comprehensive Genie space configuration that follows best practices.

Based on the input requirements, you should:

1. Identify the key tables needed for the Genie space
2. Extract important business questions that should be supported
3. Create example SQL queries that demonstrate how to answer common questions
4. Define SQL expressions for key metrics, filters, and dimensions
5. Write clear, specific instructions to guide Genie's behavior
6. Create benchmark questions for testing the space
   - **CRITICAL**: If the requirements document contains a FAQ or question list section (e.g., "## 📊 질문 목록 (FAQ)"), you MUST extract ALL questions from that section as benchmark questions
   - Preserve the exact original phrasing of each question without modification
   - Include all numbered questions in sequential order (e.g., 1-27)
   - Do NOT skip conversational, broad, or exploratory questions
   - Do NOT add constraints or modifications not present in the original (e.g., don't add "Top 5", time periods, etc. unless already specified)
   - For each benchmark question, optionally provide expected_sql if you can infer the appropriate SQL pattern
   - If no FAQ section exists, create representative benchmark questions based on the requirements

Follow these principles:
- Keep the space focused and start small (aim for 5 or fewer tables initially)
- Prioritize SQL expressions and example SQL over text instructions
- Write clear, specific instructions (avoid vague guidance)
- Ensure consistency across all instruction types
- Define the purpose and target audience clearly

Your output MUST be a valid JSON object matching the GenieSpaceConfig schema.

## Context: Best Practices for Curating a Genie Space

{context_content}

## Output Format: Genie API Documentation

{output_content}

## Input: Requirements Document

{input_content}

# Output

Please generate a complete GenieSpaceConfig JSON object based on the requirements. The JSON should be valid and follow this schema:

```json
{{
  "space_name": "string",
  "description": "string",
  "purpose": "string",
  "tables": [
    {{
      "catalog_name": "string",
      "schema_name": "string",
      "table_name": "string",
      "description": "string (optional)"
    }}
  ],
  "instructions": [
    {{
      "content": "string",
      "priority": "integer (optional)"
    }}
  ],
  "example_sql_queries": [
    {{
      "question": "string",
      "sql_query": "string",
      "description": "string (optional)"
    }}
  ],
  "sql_expressions": [
    {{
      "name": "string",
      "expression": "string",
      "description": "string (optional)",
      "type": "metric|filter|dimension"
    }}
  ],
  "benchmark_questions": [
    {{
      "question": "string (preserve exact original phrasing from FAQ section)",
      "expected_sql": "string (optional - provide if SQL pattern is clear)",
      "expected_accuracy": "string (optional - High/Medium-High/Medium/Low)"
    }}
    // IMPORTANT: Include ALL questions from any FAQ or question list section in the requirements
    // Do not create a subset - extract every numbered question completely
  ],
  "warehouse_id": "string (optional)",
  "enable_data_sampling": true
}}
```

Respond with ONLY the JSON object, no additional text or explanation.
"""
        
        return prompt
    
    def build_prompt_with_reasoning(self) -> str:
        """
        Build a prompt that includes reasoning in the response.
        
        Returns:
            The formatted prompt string that asks for reasoning
        """
        base_prompt = self.build_prompt()
        
        # Modify the prompt to include reasoning
        prompt_with_reasoning = base_prompt.replace(
            "Respond with ONLY the JSON object, no additional text or explanation.",
            """Respond with a JSON object that includes:
1. `genie_space_config`: The complete GenieSpaceConfig object
2. `reasoning`: Your explanation for the configuration choices (string)
3. `confidence_score`: Your confidence in this configuration (float between 0 and 1)

The JSON structure should be:
```json
{
  "genie_space_config": { /* GenieSpaceConfig object */ },
  "reasoning": "string explaining your choices",
  "confidence_score": 0.95
}
```

Respond with ONLY the JSON object."""
        )
        
        return prompt_with_reasoning
