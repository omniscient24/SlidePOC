#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Startup Script
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the server
from app.web.server import main

if __name__ == "__main__":
    main()