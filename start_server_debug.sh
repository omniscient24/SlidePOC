#!/bin/bash

echo "Starting Revenue Cloud Data Load Application..."
echo "=============================================="

# Change to the POC directory
cd /Users/marcdebrey/cpq-revenue-cloud-migration/POC

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Check if the server file exists
if [ ! -f "app/web/server.py" ]; then
    echo "ERROR: Server file not found at app/web/server.py"
    exit 1
fi

# Start the server
echo "Starting server on http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

python3 app/web/server.py