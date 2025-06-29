#!/bin/bash
# Main startup script for Slide - Revenue Cloud Data Load Application

echo "Starting Slide - Revenue Cloud Data Load Application..."
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if SFDX is installed
if ! command -v sfdx &> /dev/null; then
    echo "Warning: Salesforce CLI (SFDX) is not installed."
    echo "You will need SFDX for authentication features."
    echo "Install from: https://developer.salesforce.com/tools/sfdxcli"
fi

# Kill any existing server on port 8080
echo "Checking for existing servers..."
lsof -ti :8080 | xargs kill -9 2>/dev/null || true

# Start the server
echo "Starting server on http://localhost:8080"
cd "$(dirname "$0")"
python3 app/web/server.py