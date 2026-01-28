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
- **Document all join relationships explicitly** - Never rely on implicit join knowledge
- **Validate SQL correctness** - All SQL must reference existing columns with correct syntax
- **Use markdown formatting in instructions**: Structure your instruction content using markdown for clarity:
  - Use `##` for section headings to organize related instructions
  - Use bullet lists (`-`) for multiple related points
  - Use **bold** for emphasis on critical terms or actions
  - Use `code blocks` or inline `code` for column names, table names, or SQL keywords
  - Use numbered lists for sequential steps or priorities

Your output MUST be a valid JSON object matching the GenieSpaceConfig schema.

## Critical Requirements for SQL Quality

When generating SQL expressions and example queries, you MUST follow these SQL quality standards:

### 1. Use Correct Column References
- **ONLY reference columns that exist** in the specified tables from the requirements
- Use **fully qualified names**: `catalog.schema.table.column`
- Verify column names match the requirements document **exactly**
- Never assume column names - use the exact names provided

### 2. Explicit Join Conditions (CRITICAL)
- For **every multi-table query**, specify JOIN conditions explicitly
- Use the join relationships documented in the requirements
- Prefer **INNER JOIN** for required relationships, **LEFT JOIN** for optional
- **Always specify ON clauses** with exact foreign key relationships
- Example: `INNER JOIN catalog.schema.customers c ON t.customer_id = c.customer_id`

### 3. Aggregation Correctness
- Use appropriate **GROUP BY** for all non-aggregated columns in SELECT
- Include proper NULL handling: `COALESCE()`, `NULLIF()` for divisions
- Use correct aggregate functions:
  - `SUM()` for totals
  - `COUNT(DISTINCT column)` for uniqueness counts
  - `AVG()` for averages

### 4. Filter Precision
- Use correct **date functions**: `CURRENT_DATE()`, `DATE_SUB()`, `DATE_TRUNC()`
- Apply filters on the right columns (e.g., `event_date` vs `timestamp` fields)
- Include necessary WHERE clauses for data quality (e.g., `status != 'cancelled'`)
- Example: `WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`

### 5. Output Formatting
- Cast decimals explicitly: `CAST(... AS DECIMAL(38,2))`
- Use `try_divide()` for safe division operations to handle nulls
- Include appropriate **LIMIT clauses** for top-N queries
- Order results meaningfully with **ORDER BY**

### 6. Query Structure Best Practices
- Use meaningful table aliases (e.g., `t` for transactions, `c` for customers)
- Format SQL for readability (proper indentation, line breaks)
- Include comments for complex logic
- Test patterns: Ensure queries are runnable and return expected results

## Examples: High-Quality vs Low-Quality Configurations

### ❌ LOW QUALITY - Avoid This

**Vague Instruction:**
```
Use appropriate tables for queries and handle dates correctly.
```

**Poor SQL Example (implicit join, missing conditions):**
```sql
SELECT *
FROM transactions t, customers c
WHERE t.date > '2024-01-01'
```
**Problems:**
- Missing JOIN condition (Cartesian product)
- SELECT * (unclear what columns are needed)
- Implicit comma join instead of explicit JOIN syntax
- Hard-coded date instead of dynamic date function
- No table qualification

### ✅ HIGH QUALITY - Generate This

**Specific, Structured Instruction:**
```markdown
## Transaction Analysis Rules

### Required Joins
- Always join `transactions` to `customers` using `customer_id`
- Join `transactions` to `products` using `product_id` when analyzing product details

### Date Handling
- Default to **last 30 days** when time range not specified
- Use: `WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`
- For "today": use `CURRENT_DATE()`
- For "this month": use `DATE_TRUNC('month', CURRENT_DATE())`

### Data Filtering
- **Always filter out cancelled orders**: `status != 'cancelled'`
- For active customers only: `customer_status = 'active'`
- Exclude test transactions: `is_test = false`

### Aggregation Standards
- Round monetary values to 2 decimals: `CAST(amount AS DECIMAL(38,2))`
- Use safe division: `try_divide(revenue, customer_count)`
- Count unique entities with: `COUNT(DISTINCT customer_id)`

## Clarification Questions
When users ask about "performance" without specifying metrics or time period, ask:
> "To analyze performance, please specify: (1) which metrics (revenue, orders, customers), and (2) time period (e.g., last month, Q1 2024)."
```

**Excellent SQL Example (explicit joins, correct aggregation, proper formatting):**
```sql
-- Top 10 customers by revenue in last 30 days
SELECT
  c.customer_id,
  c.customer_name,
  COUNT(DISTINCT t.transaction_id) as transaction_count,
  CAST(SUM(t.amount) AS DECIMAL(38,2)) as total_revenue,
  CAST(try_divide(SUM(t.amount), COUNT(DISTINCT t.transaction_id)) AS DECIMAL(38,2)) as avg_order_value
FROM main.retail.transactions t
INNER JOIN main.retail.customers c
  ON t.customer_id = c.customer_id
WHERE t.event_date >= DATE_SUB(CURRENT_DATE(), 30)
  AND t.status != 'cancelled'
  AND t.is_test = false
GROUP BY c.customer_id, c.customer_name
HAVING total_revenue > 0
ORDER BY total_revenue DESC
LIMIT 10;
```

**Why this is high quality:**
- ✅ Explicit INNER JOIN with ON clause
- ✅ Fully qualified table names (catalog.schema.table)
- ✅ Meaningful column selection (not SELECT *)
- ✅ Correct GROUP BY (includes all non-aggregated columns)
- ✅ Safe aggregation with CAST for decimals and try_divide
- ✅ Dynamic date filtering (not hard-coded)
- ✅ Multiple business rule filters (status, is_test)
- ✅ HAVING clause for post-aggregation filtering
- ✅ Meaningful ORDER BY and LIMIT
- ✅ SQL comment explaining the query purpose

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

## Instruction Quality Guidelines

Generate instructions that are **specific, actionable, and well-structured**:

### 1. Be Specific and Concrete (NOT Vague)
❌ **Avoid:** "Handle dates appropriately" or "Use relevant tables"
✅ **Use:** "Use `event_date` column for all date filters. Default to last 30 days: `WHERE event_date >= DATE_SUB(CURRENT_DATE(), 30)`"

❌ **Avoid:** "Ask clarification questions when needed"
✅ **Use:** "When users ask about 'sales' without specifying product category or time range, ask: 'Which product category and time period would you like to analyze?'"

### 2. Structure with Markdown (Already Required)
- Use `##` headers to group related instructions
- Use bullet lists for multiple rules
- Use **bold** for critical terms
- Use `code formatting` for column/table names and SQL keywords

### 3. Prioritize Instructions Correctly
Assign priority values based on impact:
- **Priority 1 (Critical):** Data correctness rules - joins, required filters, date handling
  - Example: "Always filter out `status = 'cancelled'` from transactions"
- **Priority 2 (Important):** Default behaviors, clarification triggers, metric definitions
  - Example: "Default to last 30 days when time range not specified"
- **Priority 3+ (Optional):** Formatting preferences, nice-to-have guidance
  - Example: "Format monetary values with 2 decimal places for presentation"

### 4. Include Explicit Clarification Triggers
When questions could be ambiguous, tell Genie **exactly what to ask**:

**Structure:**
```markdown
When users ask about [TOPIC] without specifying [MISSING_INFO], ask:
> "[EXACT CLARIFICATION QUESTION]"
```

**Example:**
```markdown
When users ask about "customer performance" without specifying time period or metric, ask:
> "To analyze customer performance, please specify: (1) time period (e.g., last quarter, YTD), and (2) which metrics to analyze (revenue, order count, retention rate)."
```

### 5. Avoid Unnecessary Instructions
- Don't state obvious SQL syntax rules
- Don't repeat what's in table/column descriptions
- Don't add instructions that conflict with SQL expressions or examples
- Focus on **domain-specific** and **business-specific** rules only

## Join Specification Requirements (CRITICAL)

For **every pair of tables** that need to be joined together, you MUST document the join relationship in `join_specifications`:

```json
{{
  "join_specifications": [
    {{
      "left_table": "catalog.schema.table1",
      "right_table": "catalog.schema.table2",
      "join_type": "INNER",
      "join_condition": "table1.foreign_key_column = table2.primary_key_column",
      "description": "Explanation of the relationship (e.g., 'Each transaction belongs to one customer')"
    }}
  ]
}}
```

### Join Type Selection:
- **INNER JOIN**: Use when both tables must have matching records (e.g., transactions must have a valid customer)
- **LEFT JOIN**: Use when the right table is optional (e.g., customers may not have transactions)
- **RIGHT JOIN**: Rarely used, prefer LEFT JOIN with swapped tables
- **FULL OUTER JOIN**: Only for specific merge scenarios

### Why Join Specifications Are Critical:
- Genie uses these to understand table relationships
- Prevents Cartesian products and incorrect joins
- Documents the data model explicitly
- Improves SQL generation accuracy significantly

### Example Join Specifications:
```json
{{
  "join_specifications": [
    {{
      "left_table": "main.retail.transactions",
      "right_table": "main.retail.customers",
      "join_type": "INNER",
      "join_condition": "transactions.customer_id = customers.customer_id",
      "description": "Each transaction is associated with exactly one customer. Use INNER JOIN because all transactions must have a valid customer."
    }},
    {{
      "left_table": "main.retail.transactions",
      "right_table": "main.retail.products",
      "join_type": "INNER",
      "join_condition": "transactions.product_id = products.product_id",
      "description": "Each transaction references one product. Use INNER JOIN to ensure product details are available."
    }},
    {{
      "left_table": "main.retail.customers",
      "right_table": "main.retail.transactions",
      "join_type": "LEFT",
      "join_condition": "customers.customer_id = transactions.customer_id",
      "description": "When analyzing all customers (including those without purchases), use LEFT JOIN to include customers with no transactions."
    }}
  ]
}}
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
  "join_specifications": [
    {{
      "left_table": "catalog.schema.table1",
      "right_table": "catalog.schema.table2",
      "join_type": "INNER|LEFT|RIGHT|FULL",
      "join_condition": "table1.column = table2.column",
      "description": "string (explanation of the relationship)"
    }}
    // CRITICAL: Include join specs for EVERY pair of related tables
    // This is essential for SQL correctness
  ],
  "instructions": [
    {{{{
      "content": "string (use markdown formatting for better structure - headings, lists, bold, code, etc.)",
      "priority": "integer (1=critical data correctness, 2=important business rules, 3+=optional guidance)"
    }}}}
  ],
  "example_sql_queries": [
    {{{{
      "question": "string",
      "sql_query": "string (MUST follow SQL quality requirements above - explicit joins, correct columns, proper formatting)",
      "description": "string (optional)"
    }}}}
  ],
  "sql_expressions": [
    {{{{
      "name": "string",
      "expression": "string (MUST reference only existing columns with correct syntax)",
      "description": "string (optional)",
      "type": "metric|filter|dimension"
    }}}}
  ],
  "benchmark_questions": [
    {{{{
      "question": "string (preserve exact original phrasing from FAQ section)",
      "expected_sql": "string (optional - provide if SQL pattern is clear)",
      "expected_accuracy": "string (optional - High/Medium-High/Medium/Low)"
    }}}}
    // IMPORTANT: Include ALL questions from any FAQ or question list section in the requirements
    // Do not create a subset - extract every numbered question completely
  ],
  "warehouse_id": "string (optional)",
  "enable_data_sampling": true
}}}}
```

Respond with a JSON object that includes:
1. `genie_space_config`: The complete GenieSpaceConfig object
2. `reasoning`: Your explanation for the configuration choices (string)
3. `confidence_score`: Your confidence in this configuration (float between 0 and 1)

The JSON structure should be:
```json
{{
  "genie_space_config": {{ /* GenieSpaceConfig object */ }},
  "reasoning": "string explaining your choices",
  "confidence_score": 0.95
}}
```

Respond with ONLY the JSON object.
