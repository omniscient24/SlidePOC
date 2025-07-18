#!/usr/bin/env python3
"""
Debug wrapper for the server to capture crash details
"""
import subprocess
import sys
import time

def run_server():
    """Run the server and capture any errors"""
    while True:
        print("\n" + "="*60)
        print("Starting server...")
        print("="*60 + "\n")
        
        try:
            # Run the server
            result = subprocess.run(
                [sys.executable, "app/web/server.py"],
                capture_output=True,
                text=True
            )
            
            # Print output
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"\nServer exited with code: {result.returncode}")
                
        except Exception as e:
            print(f"\nException running server: {e}")
        
        print("\nServer crashed. Waiting 2 seconds before restart...")
        print("Press Ctrl+C to stop completely.")
        
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopping debug server.")
            break

if __name__ == "__main__":
    run_server()