# Instruction

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
- **Use markdown formatting in instructions**: Structure your instruction content using markdown for clarity:
  - Use `##` for section headings to organize related instructions
  - Use bullet lists (`-`) for multiple related points
  - Use **bold** for emphasis on critical terms or actions
  - Use `code blocks` or inline `code` for column names, table names, or SQL keywords
  - Use numbered lists for sequential steps or priorities

Your output MUST be a valid JSON object matching the GenieSpaceConfig schema.

### Example of Well-Formatted Instruction Content

Good markdown formatting example:
```
## Date and Time Handling
- Always use `event_date` column for date-based queries
- Default to **last 30 days** when no time period is specified
- Use `CURRENT_DATE()` for "today" and `DATE_SUB(CURRENT_DATE(), 30)` for "last 30 days"

## Metric Calculations
When calculating **revenue metrics**:
1. Use `total_revenue` column (already includes tax)
2. Round all monetary values to 2 decimal places
3. Filter out cancelled orders using `status != 'cancelled'`

## Clarification Questions
When users ask about performance but don't specify time range or product category, ask:
> "To analyze performance, please specify: (1) time period (e.g., last month, Q1 2024), and (2) product category you want to analyze."
```

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
      "content": "string (use markdown formatting for better structure - headings, lists, bold, code, etc.)",
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
