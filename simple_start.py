#!/usr/bin/env python3
"""Simple server starter with better error handling"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now start the server
print("Starting server...")
try:
    from app.web.server import main
    main()
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()