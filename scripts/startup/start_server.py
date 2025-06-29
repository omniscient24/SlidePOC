#!/usr/bin/env python3
"""
Simple launcher to start the web server from the root directory
"""

import os
import sys

# Get the absolute path to the web UI module
web_ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'web-ui')
sys.path.insert(0, web_ui_path)

# Import and start the server
from revenue_cloud_structured_web_poc import start_server

if __name__ == "__main__":
    print("Starting Revenue Cloud Migration Tool...")
    print("The application will open at http://localhost:8080")
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped.")