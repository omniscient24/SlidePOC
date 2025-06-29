#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool Launcher
Choose between desktop or web interface.
"""

import sys
import subprocess
import webbrowser
import time

def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("REVENUE CLOUD MIGRATION TOOL")
    print("CPQ to Revenue Cloud Migration Suite")
    print("=" * 60)

def check_requirements():
    """Check if required packages are installed."""
    required = {
        'pandas': 'Data processing',
        'openpyxl': 'Excel file handling',
        'tkinter': 'Desktop UI (optional)',
        'flask': 'Web UI (optional)'
    }
    
    print("\nChecking requirements...")
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package)
            print(f"✓ {package} - {description}")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} - {description} (MISSING)")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install pandas openpyxl flask")
        if 'pandas' in missing or 'openpyxl' in missing:
            print("\nERROR: pandas and openpyxl are required for core functionality")
            return False
    
    return True

def main():
    """Main launcher."""
    print_banner()
    
    if not check_requirements():
        sys.exit(1)
    
    print("\nSelect interface:")
    print("1. Desktop UI (Tkinter)")
    print("2. Web UI (Browser-based)")
    print("3. Command Line (Scripts only)")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\nLaunching desktop UI...")
            try:
                subprocess.run([sys.executable, 'revenue_cloud_ui.py'])
            except Exception as e:
                print(f"Error launching desktop UI: {e}")
                print("Make sure tkinter is installed")
            break
            
        elif choice == '2':
            print("\nLaunching web UI...")
            print("Starting server at http://localhost:5000")
            try:
                # Start Flask server in background
                process = subprocess.Popen([sys.executable, 'revenue_cloud_web_ui.py'])
                
                # Wait a moment for server to start
                time.sleep(2)
                
                # Open browser
                webbrowser.open('http://localhost:5000')
                
                print("\nWeb UI is running. Press Ctrl+C to stop.")
                process.wait()
                
            except KeyboardInterrupt:
                print("\nStopping web server...")
            except Exception as e:
                print(f"Error launching web UI: {e}")
                print("Make sure flask is installed: pip install flask")
            break
            
        elif choice == '3':
            print("\nCommand Line Mode")
            print("-" * 40)
            print("\nAvailable scripts:")
            print("1. comprehensive_field_cleanup.py - Remove read-only fields")
            print("2. revenue_cloud_upload_process.py - Upload data to Salesforce")
            print("3. export_to_same_template.py - Export data from Salesforce")
            print("\nUsage:")
            print("  python3 <script_name>")
            print("\nRefer to REVENUE_CLOUD_UPLOAD_GUIDE.md for detailed instructions")
            break
            
        elif choice == '4':
            print("\nExiting...")
            break
            
        else:
            print("Invalid choice. Please enter 1-4.")

if __name__ == '__main__':
    main()