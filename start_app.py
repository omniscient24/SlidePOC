#!/usr/bin/env python3
"""Start the Revenue Cloud Data Load Application"""
import subprocess
import sys
import os
import time

def main():
    print("\nStarting Revenue Cloud Data Load Application...")
    print("=" * 50)
    
    # Change to POC directory
    os.chdir('/Users/marcdebrey/cpq-revenue-cloud-migration/POC')
    
    # First, let's test if we can import everything
    print("Checking dependencies...")
    try:
        sys.path.insert(0, os.getcwd())
        from app.services.connection_manager import connection_manager
        from app.services.session_manager import session_manager
        print("✓ Dependencies loaded successfully")
    except Exception as e:
        print(f"✗ Error loading dependencies: {e}")
        return 1
    
    # Kill any existing processes on port 8080
    print("\nCleaning up port 8080...")
    os.system("lsof -ti :8080 | xargs kill -9 2>/dev/null || true")
    time.sleep(1)
    
    # Start the server
    print("\nStarting server...")
    print("Server will be available at: http://localhost:8080\n")
    
    try:
        # Run the server directly
        subprocess.run([sys.executable, "app/web/server.py"], check=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\nServer exited with error code: {e.returncode}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())