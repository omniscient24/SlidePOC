#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - GUI Launcher
Launches the appropriate GUI version based on availability.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check which GUI libraries are available."""
    results = {
        'tkinter': False,
        'flask': False,
        'simple_web': True  # Always available as it uses standard library
    }
    
    # Check tkinter
    try:
        import tkinter
        results['tkinter'] = True
    except ImportError:
        pass
    
    # Check flask
    try:
        import flask
        results['flask'] = True
    except ImportError:
        pass
    
    return results

def main():
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    print("\n" + "="*60)
    print("Revenue Cloud Migration Tool - GUI Launcher")
    print("="*60 + "\n")
    
    deps = check_dependencies()
    
    print("Checking available interfaces...")
    print(f"{'✓' if deps['tkinter'] else '✗'} Tkinter GUI")
    print(f"{'✓' if deps['flask'] else '✗'} Flask Web UI")
    print(f"✓ Simple Web UI (standard library)")
    print()
    
    # Determine which UI to launch
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        print("Select interface:")
        options = []
        
        if deps['tkinter']:
            options.append(('1', 'tkinter', 'Tkinter GUI'))
        if deps['flask']:
            options.append(('2', 'flask', 'Flask Web UI'))
        options.append((str(len(options) + 1), 'simple', 'Simple Web UI'))
        options.append((str(len(options) + 1), 'cli', 'Command Line Interface'))
        
        for opt in options:
            print(f"{opt[0]}. {opt[2]}")
        
        user_input = input(f"\nEnter choice (1-{len(options)}) [default: {len(options)-1}]: ").strip()
        
        if not user_input:
            choice = 'simple'
        else:
            for opt in options:
                if user_input == opt[0]:
                    choice = opt[1]
                    break
            else:
                choice = 'simple'
    
    # Launch the selected interface
    try:
        if choice == 'tkinter' and deps['tkinter']:
            print("\nLaunching Tkinter GUI...")
            subprocess.run([sys.executable, 'revenue_cloud_poc_ui.py'])
        elif choice == 'flask' and deps['flask']:
            print("\nLaunching Flask Web UI...")
            subprocess.run([sys.executable, 'revenue_cloud_flask_poc.py'])
        elif choice == 'cli':
            print("\nLaunching CLI...")
            subprocess.run([sys.executable, 'revenue_cloud_cli_poc.py'])
        else:
            print("\nLaunching Simple Web UI...")
            print("The web interface will open in your browser.")
            print("If it doesn't open automatically, navigate to: http://localhost:8080")
            print("\nPress Ctrl+C to stop the server")
            print()
            subprocess.run([sys.executable, 'revenue_cloud_simple_web_poc.py'])
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Falling back to CLI...")
        subprocess.run([sys.executable, 'revenue_cloud_cli_poc.py'])

if __name__ == '__main__':
    main()