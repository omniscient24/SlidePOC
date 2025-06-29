#!/bin/bash

echo "Testing minimal Pass 2 import..."
echo ""

cd /Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload

echo "Running minimal Pass 2 import..."
sf data import tree --plan plans_tree/pass2_minimal_import.json --target-org fortradp2

echo ""
echo "Test complete."