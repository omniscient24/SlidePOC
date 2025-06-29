#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Command Line POC
A simple CLI interface for the core migration functions.
"""

import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

class RevenueCloudCLI:
    def __init__(self):
        self.org = "fortradp2"
        self.workbook = "data/Revenue_Cloud_Complete_Upload_Template.xlsx"
        self.is_connected = False
        
    def print_header(self):
        """Print application header."""
        print("\n" + "="*60)
        print("REVENUE CLOUD MIGRATION TOOL - POC")
        print("="*60)
        print(f"Org: {self.org}")
        print(f"Workbook: {self.workbook}")
        print("="*60 + "\n")
    
    def print_menu(self):
        """Print main menu."""
        print("\nMAIN MENU:")
        print("1. Test Connection")
        print("2. Clean Fields (Remove read-only fields)")
        print("3. Import from Org (Download current data)")
        print("4. Upload to Org (Upload data to Salesforce)")
        print("5. Change Org")
        print("6. Change Workbook")
        print("7. Check Environment")
        print("0. Exit")
        print()
    
    def check_environment(self):
        """Check if required tools are available."""
        print("\nChecking environment...")
        print("-" * 40)
        
        all_good = True
        
        # Check for Salesforce CLI
        try:
            result = subprocess.run(['sf', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Salesforce CLI found")
            else:
                print("✗ Salesforce CLI not found")
                all_good = False
        except:
            print("✗ Salesforce CLI not found")
            all_good = False
        
        # Check for required Python scripts
        scripts = [
            'comprehensive_field_cleanup.py',
            'export_to_same_template.py',
            'revenue_cloud_upload_process.py'
        ]
        
        for script in scripts:
            if Path(script).exists():
                print(f"✓ {script} found")
            else:
                print(f"✗ {script} not found")
                all_good = False
        
        # Check workbook
        if Path(self.workbook).exists():
            print(f"✓ Workbook found: {self.workbook}")
        else:
            print(f"⚠ Workbook not found: {self.workbook}")
        
        # Check Python packages
        try:
            import pandas
            print("✓ pandas installed")
        except ImportError:
            print("✗ pandas not installed (pip install pandas)")
            all_good = False
        
        try:
            import openpyxl
            print("✓ openpyxl installed")
        except ImportError:
            print("✗ openpyxl not installed (pip install openpyxl)")
            all_good = False
        
        print("-" * 40)
        if all_good:
            print("✓ All requirements met!")
        else:
            print("✗ Some requirements are missing")
        
        return all_good
    
    def test_connection(self):
        """Test Salesforce connection."""
        print(f"\nTesting connection to {self.org}...")
        
        try:
            cmd = ['sf', 'org', 'display', '--target-org', self.org]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse output for username
                username = None
                for line in result.stdout.split('\n'):
                    if 'Username' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            username = parts[-1]
                            break
                
                if username:
                    print(f"✓ Connected to: {username}")
                else:
                    print("✓ Connection successful")
                self.is_connected = True
            else:
                print(f"✗ Connection failed")
                print(f"Error: {result.stderr}")
                self.is_connected = False
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            self.is_connected = False
        
        return self.is_connected
    
    def run_script(self, script_name, operation_name):
        """Run a Python script and show output."""
        print(f"\n{'='*60}")
        print(f"{operation_name}")
        print(f"{'='*60}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Run the script
            process = subprocess.Popen(
                ['python3', script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            process.wait()
            
            print()
            print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if process.returncode == 0:
                print(f"✓ {operation_name} completed successfully!")
            else:
                print(f"✗ {operation_name} failed with exit code {process.returncode}")
            
            return process.returncode == 0
                
        except Exception as e:
            print(f"\n✗ Error running {operation_name}: {str(e)}")
            return False
    
    def clean_fields(self):
        """Run field cleanup."""
        return self.run_script('comprehensive_field_cleanup.py', 'FIELD CLEANUP')
    
    def import_data(self):
        """Import data from Salesforce."""
        if not self.is_connected:
            print("\n⚠ Please test connection first (Option 1)")
            return False
        
        return self.run_script('export_to_same_template.py', 'DATA IMPORT')
    
    def upload_data(self):
        """Upload data to Salesforce."""
        if not self.is_connected:
            print("\n⚠ Please test connection first (Option 1)")
            return False
        
        # Confirmation
        print("\n⚠️  WARNING: This will upload data to Salesforce!")
        print(f"Target org: {self.org}")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        
        if response.lower() == 'yes':
            return self.run_script('revenue_cloud_upload_process.py', 'DATA UPLOAD')
        else:
            print("Upload cancelled.")
            return False
    
    def change_org(self):
        """Change target org."""
        print(f"\nCurrent org: {self.org}")
        new_org = input("Enter new org alias: ").strip()
        
        if new_org:
            self.org = new_org
            self.is_connected = False
            print(f"✓ Org changed to: {self.org}")
            print("⚠ Please test connection again")
    
    def change_workbook(self):
        """Change workbook path."""
        print(f"\nCurrent workbook: {self.workbook}")
        new_workbook = input("Enter new workbook path: ").strip()
        
        if new_workbook:
            if Path(new_workbook).exists():
                self.workbook = new_workbook
                print(f"✓ Workbook changed to: {self.workbook}")
            else:
                print("✗ File not found")
    
    def run(self):
        """Main application loop."""
        self.print_header()
        
        # Initial environment check
        self.check_environment()
        
        while True:
            self.print_menu()
            
            try:
                choice = input("Enter your choice (0-7): ").strip()
                
                if choice == '0':
                    print("\nExiting...")
                    break
                elif choice == '1':
                    self.test_connection()
                elif choice == '2':
                    self.clean_fields()
                elif choice == '3':
                    self.import_data()
                elif choice == '4':
                    self.upload_data()
                elif choice == '5':
                    self.change_org()
                elif choice == '6':
                    self.change_workbook()
                elif choice == '7':
                    self.check_environment()
                else:
                    print("\n⚠ Invalid choice. Please enter 0-7.")
                
                # Pause before showing menu again
                if choice in ['2', '3', '4']:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")

def main():
    cli = RevenueCloudCLI()
    cli.run()

if __name__ == '__main__':
    main()