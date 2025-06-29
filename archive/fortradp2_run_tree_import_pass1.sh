#!/bin/bash

# Salesforce Revenue Cloud Tree Import Script - Pass 1
# This script imports the base objects into Revenue Cloud

echo "=========================================="
echo "Revenue Cloud Tree Import - Pass 1"
echo "=========================================="
echo ""

# Set working directory
cd /Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload

# Check if we're in the correct directory
if [ ! -f "plans_tree/pass1_import.json" ]; then
    echo "Error: Import plan not found. Make sure you're in the correct directory."
    exit 1
fi

# Verify JSON files exist
echo "Verifying JSON files..."
for file in json_tree_output/pass1/*.json; do
    if [ -f "$file" ]; then
        echo "✓ Found: $(basename $file)"
    fi
done
echo ""

# Run the tree import
echo "Starting tree import for Pass 1..."
echo "Command: sf data import tree --plan plans_tree/pass1_import.json --target-org fortradp2"
echo ""

sf data import tree --plan plans_tree/pass1_import.json --target-org fortradp2

# Check the exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Pass 1 import completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Verify the imported records in Salesforce"
    echo "2. Run ./fortradp2_run_tree_import_pass2.sh to import dependent objects"
else
    echo ""
    echo "✗ Pass 1 import failed. Please check the error messages above."
    echo ""
    echo "Common issues to check:"
    echo "- Field permissions (make sure all custom fields are accessible)"
    echo "- Required field values"
    echo "- Duplicate external IDs"
    echo "- JSON file formatting"
fi
