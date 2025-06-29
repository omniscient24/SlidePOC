#!/usr/bin/env python3
"""
Launch the Revenue Cloud Migration Tool Web UI
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Change to web-ui directory and run the server
os.chdir(os.path.join(os.path.dirname(__file__), 'src', 'web-ui'))

# Import and run the web server
from revenue_cloud_structured_web_poc import start_server

if __name__ == "__main__":
    print("Starting Revenue Cloud Migration Tool...")
    print("The application will open at http://localhost:8080")
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped.")