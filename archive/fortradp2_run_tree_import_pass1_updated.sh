#!/bin/bash

echo "▶ Starting Salesforce Data Tree Import for pass1 at $(date)"

# Run import using the plan in the project root
sf data import tree --plan pass1_import.json --target-org fortradp2

echo "✅ Tree import for pass1 completed at $(date)"
