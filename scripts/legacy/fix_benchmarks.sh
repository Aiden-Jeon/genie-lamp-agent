#!/bin/bash
# Quick fix script to update benchmarks in existing config
# This is the fastest way to fix incomplete benchmark extraction

set -e

echo ""
echo "================================================================================"
echo "Fix Benchmarks - Quick Update Script"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Load your existing Genie space config"
echo "  2. Extract ALL benchmarks from requirements (100% coverage)"
echo "  3. Replace LLM-generated benchmarks with directly extracted ones"
echo "  4. Save the updated config"
echo ""

# Default paths
CONFIG_FILE="${1:-output/genie_space_config.json}"
REQUIREMENTS_FILE="${2:-data/demo_requirements.md}"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file not found: $CONFIG_FILE"
    echo ""
    echo "Usage:"
    echo "  ./scripts/fix_benchmarks.sh [config_file] [requirements_file]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/fix_benchmarks.sh"
    echo "  ./scripts/fix_benchmarks.sh output/my_config.json"
    echo "  ./scripts/fix_benchmarks.sh output/my_config.json data/my_requirements.md"
    exit 1
fi

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ Error: Requirements file not found: $REQUIREMENTS_FILE"
    exit 1
fi

echo "Config file:        $CONFIG_FILE"
echo "Requirements file:  $REQUIREMENTS_FILE"
echo ""

# Create backup
BACKUP_FILE="${CONFIG_FILE}.backup"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✓ Created backup: $BACKUP_FILE"
echo ""

# Run the update script
echo "Updating benchmarks..."
echo ""

python scripts/update_benchmarks.py \
    --config "$CONFIG_FILE" \
    --requirements "$REQUIREMENTS_FILE"

echo ""
echo "================================================================================"
echo "✓ Done! Benchmarks have been updated."
echo "================================================================================"
echo ""
echo "Backup saved to: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "  1. Review the updated config: cat $CONFIG_FILE"
echo "  2. Verify extraction: python compare_benchmarks.py"
echo "  3. Create/update Genie space: python scripts/create_genie_space.py"
echo ""
