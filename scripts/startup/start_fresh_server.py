#!/usr/bin/env python3
"""
Fresh server start script
"""
import os
import sys
import subprocess
import time
import signal

def kill_existing_servers():
    """Kill any existing servers on port 8080"""
    print("Killing existing servers...")
    
    # Try multiple methods to ensure all processes are killed
    commands = [
        "lsof -ti :8080 | xargs kill -9 2>/dev/null || true",
        "pkill -f 'python.*server.py' || true",
        "pkill -f 'python.*8080' || true"
    ]
    
    for cmd in commands:
        subprocess.run(cmd, shell=True, capture_output=True)
    
    # Wait for ports to be released
    time.sleep(2)

def start_server():
    """Start the server"""
    print("Starting fresh server...")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    # Start server
    cmd = [sys.executable, "app/web/server.py"]
    
    try:
        # Run server
        process = subprocess.Popen(cmd)
        print(f"Server started with PID: {process.pid}")
        
        # Wait a moment
        time.sleep(3)
        
        # Test if server is responding
        test_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/login"
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout == '200':
            print("✓ Server is running and responding!")
            print("\nAccess the application at: http://localhost:8080/login")
            print("Press Ctrl+C to stop the server")
            
            # Keep running
            process.wait()
        else:
            print(f"✗ Server is not responding properly. HTTP status: {result.stdout}")
            process.terminate()
            
    except KeyboardInterrupt:
        print("\nStopping server...")
        process.terminate()
    except Exception as e:
        print(f"Error: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    kill_existing_servers()
    start_server()