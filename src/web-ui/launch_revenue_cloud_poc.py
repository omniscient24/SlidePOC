#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool Launcher
Automatically detects and launches the appropriate version (GUI or CLI).
"""

import sys
import subprocess
from pathlib import Path

def check_tkinter():
    """Check if Tkinter is available."""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def check_pywebview():
    """Check if pywebview is available for web UI."""
    try:
        import webview
        return True
    except ImportError:
        return False

def launch_gui():
    """Launch the Tkinter GUI version."""
    print("Launching GUI version...")
    subprocess.run([sys.executable, "revenue_cloud_poc_ui.py"])

def launch_web_ui():
    """Launch the web UI version."""
    print("Launching Web UI version...")
    subprocess.run([sys.executable, "revenue_cloud_web_ui.py"])

def launch_cli():
    """Launch the CLI version."""
    print("Launching CLI version...")
    subprocess.run([sys.executable, "revenue_cloud_cli_poc.py"])

def main():
    print("\n" + "="*60)
    print("REVENUE CLOUD MIGRATION TOOL LAUNCHER")
    print("="*60 + "\n")
    
    # Check which versions are available
    has_tkinter = check_tkinter()
    has_pywebview = check_pywebview()
    
    print("Checking available interfaces...")
    print(f"✓ CLI interface: Available")
    print(f"{'✓' if has_tkinter else '✗'} GUI interface (Tkinter): {'Available' if has_tkinter else 'Not available'}")
    print(f"{'✓' if has_pywebview else '✗'} Web interface (PyWebView): {'Available' if has_pywebview else 'Not available'}")
    print()
    
    # Auto-select based on availability
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        if has_tkinter:
            print("GUI interface is available. Choose your preferred interface:")
            print("1. GUI (Graphical User Interface)")
            print("2. CLI (Command Line Interface)")
            if has_pywebview:
                print("3. Web (Web Browser Interface)")
            
            choice = input("\nEnter your choice (1/2" + ("/3" if has_pywebview else "") + ") [default: 1]: ").strip() or "1"
        elif has_pywebview:
            print("Tkinter not available, but Web UI is available. Choose interface:")
            print("1. Web (Web Browser Interface)")
            print("2. CLI (Command Line Interface)")
            
            choice = input("\nEnter your choice (1/2) [default: 1]: ").strip() or "1"
            if choice == "1":
                choice = "web"
            elif choice == "2":
                choice = "cli"
        else:
            print("No GUI libraries available. Using CLI interface...")
            choice = "cli"
    
    # Launch the selected interface
    if choice in ["1", "gui"] and has_tkinter:
        launch_gui()
    elif choice in ["3", "web"] and has_pywebview:
        launch_web_ui()
    elif choice in ["2", "cli"] or choice == "cli":
        launch_cli()
    else:
        print("Invalid choice or interface not available. Launching CLI...")
        launch_cli()

if __name__ == "__main__":
    main()