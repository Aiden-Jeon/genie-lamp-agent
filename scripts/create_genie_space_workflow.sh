#!/bin/bash

# Genie Space Creation Workflow
# This script generates a Genie space configuration and creates the space in Databricks.

set -e  # Exit on error

# Change to project root directory (parent of scripts/)
cd "$(dirname "$0")/.."

echo "================================================================================"
echo "Genie Space Creation Workflow"
echo "================================================================================"
echo ""

# Default values
MODEL="databricks-gpt-5-2"
INPUT_DATA="data/demo_requirements.md"
CONFIG_OUTPUT="output/genie_space_config.json"
RESULT_OUTPUT="output/genie_space_result.json"
MAX_TOKENS=16000
TEMPERATURE=0.1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --input-data)
      INPUT_DATA="$2"
      shift 2
      ;;
    --config-output)
      CONFIG_OUTPUT="$2"
      shift 2
      ;;
    --result-output)
      RESULT_OUTPUT="$2"
      shift 2
      ;;
    --max-tokens)
      MAX_TOKENS="$2"
      shift 2
      ;;
    --temperature)
      TEMPERATURE="$2"
      shift 2
      ;;
    --skip-generation)
      SKIP_GENERATION=true
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --model MODEL              Foundation model name (default: databricks-gpt-5-2)"
      echo "  --input-data PATH          Path to input requirements (default: data/demo_requirements.md)"
      echo "  --config-output PATH       Path to save config (default: output/genie_space_config.json)"
      echo "  --result-output PATH       Path to save result (default: output/genie_space_result.json)"
      echo "  --max-tokens N             Max tokens to generate (default: 16000)"
      echo "  --temperature N            Sampling temperature (default: 0.1)"
      echo "  --skip-generation          Skip config generation, use existing config file"
      echo "  --help                     Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# Step 1: Generate configuration (unless skipped)
if [ "$SKIP_GENERATION" = true ]; then
  echo "Skipping configuration generation..."
  echo "Using existing config: $CONFIG_OUTPUT"
  echo ""
else
  echo "Step 1: Generating Genie Space Configuration"
  echo "--------------------------------------------------------------------------------"
  echo "  Model: $MODEL"
  echo "  Input: $INPUT_DATA"
  echo "  Output: $CONFIG_OUTPUT"
  echo "  Max tokens: $MAX_TOKENS"
  echo "  Temperature: $TEMPERATURE"
  echo ""
  
  python main.py \
    --model "$MODEL" \
    --input-data "$INPUT_DATA" \
    --output "$CONFIG_OUTPUT" \
    --max-tokens "$MAX_TOKENS" \
    --temperature "$TEMPERATURE"
  
  if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Configuration generation failed!"
    exit 1
  fi
  
  echo ""
  echo "✓ Configuration generated successfully"
  echo ""
fi

# Step 2: Create Genie space
echo "Step 2: Creating Genie Space in Databricks"
echo "--------------------------------------------------------------------------------"
echo "  Config: $CONFIG_OUTPUT"
echo "  Result output: $RESULT_OUTPUT"
echo ""

python scripts/create_genie_space.py \
  --config "$CONFIG_OUTPUT" \
  --output "$RESULT_OUTPUT"

if [ $? -ne 0 ]; then
  echo ""
  echo "✗ Genie space creation failed!"
  exit 1
fi

echo ""
echo "================================================================================"
echo "Workflow Completed Successfully!"
echo "================================================================================"
echo ""
echo "Your Genie space has been created. Check $RESULT_OUTPUT for details."
echo ""

# Extract and display the URL if jq is available
if command -v jq &> /dev/null; then
  SPACE_URL=$(jq -r '.space_url' "$RESULT_OUTPUT" 2>/dev/null || echo "")
  if [ -n "$SPACE_URL" ]; then
    echo "Access your Genie space at:"
    echo "  $SPACE_URL"
    echo ""
  fi
fi

exit 0
