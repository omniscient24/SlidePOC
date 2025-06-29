#!/bin/bash
# Revenue Cloud Migration Tool - Server Startup Script

echo "Starting Revenue Cloud Migration Tool..."

# Kill any existing servers on port 8080
echo "Stopping any existing servers..."
lsof -ti :8080 | xargs kill -9 2>/dev/null || true

# Wait for port to be released
sleep 2

# Start the server
echo "Starting server on http://localhost:8080"
python3 simple_server.py