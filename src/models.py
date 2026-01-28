"""Pydantic models for Genie space creation."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class GenieSpaceTable(BaseModel):
    """Represents a table to include in the Genie space."""
    
    catalog_name: str = Field(..., description="Catalog name in Unity Catalog")
    schema_name: str = Field(..., description="Schema name in Unity Catalog")
    table_name: str = Field(..., description="Table name in Unity Catalog")
    description: Optional[str] = Field(None, description="Custom description for the table")


class GenieSpaceInstruction(BaseModel):
    """Represents a plain text instruction for the Genie space."""
    
    content: str = Field(..., description="The instruction text")
    priority: Optional[int] = Field(None, description="Priority of the instruction (higher = more important)")


class GenieSpaceExampleSQL(BaseModel):
    """Represents an example SQL query for the Genie space."""
    
    question: str = Field(..., description="Natural language question that this SQL answers")
    sql_query: str = Field(..., description="The SQL query that answers the question")
    description: Optional[str] = Field(None, description="Additional description or context")


class GenieSpaceSQLExpression(BaseModel):
    """Represents a SQL expression for metrics, filters, or dimensions."""
    
    name: str = Field(..., description="Name of the metric/filter/dimension")
    expression: str = Field(..., description="SQL expression")
    description: Optional[str] = Field(None, description="Description of what this represents")
    type: str = Field(..., description="Type: 'metric', 'filter', or 'dimension'")


class GenieSpaceBenchmark(BaseModel):
    """Represents a benchmark question for testing the Genie space."""
    
    question: str = Field(..., description="The benchmark question")
    expected_sql: Optional[str] = Field(None, description="Expected SQL query pattern")
    expected_accuracy: Optional[str] = Field(None, description="Expected accuracy level")


class GenieSpaceConfig(BaseModel):
    """Complete configuration for creating a Genie space."""
    
    space_name: str = Field(..., description="Name of the Genie space")
    description: str = Field(..., description="Description of what this space is for")
    purpose: str = Field(..., description="Specific purpose and target audience")
    
    # Data configuration
    tables: List[GenieSpaceTable] = Field(default_factory=list, description="Tables to include in the space")
    
    # Instructions and examples
    instructions: List[GenieSpaceInstruction] = Field(default_factory=list, description="Plain text instructions")
    example_sql_queries: List[GenieSpaceExampleSQL] = Field(default_factory=list, description="Example SQL queries")
    sql_expressions: List[GenieSpaceSQLExpression] = Field(default_factory=list, description="SQL expressions for metrics/filters/dimensions")
    
    # Testing
    benchmark_questions: List[GenieSpaceBenchmark] = Field(default_factory=list, description="Benchmark questions for testing")
    
    # Metadata
    warehouse_id: Optional[str] = Field(None, description="SQL warehouse ID to use")
    enable_data_sampling: bool = Field(True, description="Whether to enable data sampling")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "space_name": "Fashion Retail Analytics",
                "description": "Natural language querying for fashion retail data",
                "purpose": "Enable business users to analyze sales, customer behavior, and product performance",
                "tables": [
                    {
                        "catalog_name": "jongseob_demo",
                        "schema_name": "fashion_recommendations",
                        "table_name": "transactions"
                    }
                ],
                "instructions": [
                    {
                        "content": "When users ask about sales without specifying a time range, default to the last 7 days.",
                        "priority": 1
                    }
                ],
                "example_sql_queries": [
                    {
                        "question": "What were the top selling products last week?",
                        "sql_query": "SELECT product_name, COUNT(*) as sales FROM transactions WHERE transaction_date >= CURRENT_DATE - 7 GROUP BY product_name ORDER BY sales DESC LIMIT 10"
                    }
                ],
                "benchmark_questions": [
                    {
                        "question": "What were the top 10 selling products last week?"
                    }
                ]
            }
        }
    )


class LLMResponse(BaseModel):
    """Response from the LLM containing the generated Genie space configuration."""
    
    genie_space_config: GenieSpaceConfig = Field(..., description="The generated Genie space configuration")
    reasoning: Optional[str] = Field(None, description="LLM's reasoning for the configuration choices")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1) for the configuration")
