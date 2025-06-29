#!/bin/bash

# Salesforce Revenue Cloud Tree Import Script - Pass 2
# This script imports dependent objects that reference Pass 1 objects

echo "=========================================="
echo "Revenue Cloud Tree Import - Pass 2"
echo "=========================================="
echo ""

# Set working directory
cd /Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload

# Check if we're in the correct directory
if [ ! -f "plans_tree/pass2_import.json" ]; then
    echo "Error: Import plan not found. Make sure you're in the correct directory."
    exit 1
fi

# Verify JSON files exist
echo "Verifying JSON files..."
for file in json_tree_output/pass2/*.json; do
    if [ -f "$file" ]; then
        echo "✓ Found: $(basename $file)"
    fi
done
echo ""

# Remind user about Pass 1
echo "⚠️  IMPORTANT: Make sure Pass 1 import has completed successfully before running Pass 2"
echo "   Pass 2 contains dependent objects that reference records from Pass 1"
echo ""
read -p "Have you successfully completed Pass 1 import? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please run ./fortradp2_run_tree_import_pass1.sh first"
    exit 1
fi

# Run the tree import
echo ""
echo "Starting tree import for Pass 2..."
echo "Command: sf data import tree --plan plans_tree/pass2_import.json --target-org fortradp2"
echo ""

sf data import tree --plan plans_tree/pass2_import.json --target-org fortradp2

# Check the exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Pass 2 import completed successfully!"
    echo ""
    echo "All data has been imported to Revenue Cloud!"
    echo ""
    echo "Next steps:"
    echo "1. Verify all records in Salesforce"
    echo "2. Check that all relationships are properly established"
    echo "3. Test the product configuration"
else
    echo ""
    echo "✗ Pass 2 import failed. Please check the error messages above."
    echo ""
    echo "Common issues to check:"
    echo "- Make sure Pass 1 was completed successfully"
    echo "- Check that all referenced records exist"
    echo "- Verify field permissions for junction objects"
    echo "- Check for duplicate external IDs"
fi
