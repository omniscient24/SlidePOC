#!/bin/bash

echo "Testing Pass 2 mapped import..."
echo ""

cd /Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload

echo "Running Pass 2 mapped import..."
sf data import tree --plan plans_tree/pass2_mapped_import.json --target-org fortradp2

echo ""
echo "Test complete."