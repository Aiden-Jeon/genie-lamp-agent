# Instruction

You are an expert in creating Databricks Genie spaces. Your task is to analyze the provided requirements document and generate a comprehensive Genie space configuration that follows best practices.

Based on the input requirements, you should:

1. Identify the key tables needed for the Genie space
2. Extract important business questions that should be supported
3. Create example SQL queries that demonstrate how to answer common questions
4. Define SQL expressions for key metrics, filters, and dimensions
   - Create as many SQL expressions as are relevant to your data (typically 5-15)
   - Focus on commonly used business terms, metrics, and calculations
   - Don't force a specific number - quality and relevance over quantity
5. Write clear, specific instructions to guide Genie's behavior

**Note**: Benchmark questions are extracted and processed separately by the system.

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
  "warehouse_id": "string (optional)",
  "enable_data_sampling": true
}}
```

Respond with ONLY the JSON object, no additional text or explanation.
