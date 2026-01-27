"""Source package for Genie space configuration generation."""

# Models (at root)
from .models import (
    GenieSpaceConfig,
    GenieSpaceTable,
    GenieSpaceInstruction,
    GenieSpaceExampleSQL,
    GenieSpaceSQLExpression,
    GenieSpaceBenchmark,
    LLMResponse,
)

# LLM clients
from .llm import DatabricksLLMClient, DatabricksFoundationModelClient

# Prompt builder
from .prompt import PromptBuilder

# API clients
from .api import GenieSpaceClient, create_genie_space_from_file

# Utils
from .utils import (
    extract_benchmarks_from_requirements,
    extract_sample_queries_as_benchmarks,
    extract_benchmarks_from_multiple_sections,
    extract_all_benchmarks,
    merge_benchmarks_into_config,
    validate_benchmarks,
    transform_to_serialized_space,
    create_join_spec,
    TableValidator,
    ValidationReport,
    ValidationIssue,
)

__all__ = [
    # Models
    "GenieSpaceConfig",
    "GenieSpaceTable",
    "GenieSpaceInstruction",
    "GenieSpaceExampleSQL",
    "GenieSpaceSQLExpression",
    "GenieSpaceBenchmark",
    "LLMResponse",
    # LLM
    "DatabricksLLMClient",
    "DatabricksFoundationModelClient",
    # Prompt
    "PromptBuilder",
    # API
    "GenieSpaceClient",
    "create_genie_space_from_file",
    # Utils
    "extract_benchmarks_from_requirements",
    "extract_sample_queries_as_benchmarks",
    "extract_benchmarks_from_multiple_sections",
    "extract_all_benchmarks",
    "merge_benchmarks_into_config",
    "validate_benchmarks",
    "transform_to_serialized_space",
    "create_join_spec",
    "TableValidator",
    "ValidationReport",
    "ValidationIssue",
]
