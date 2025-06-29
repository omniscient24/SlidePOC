#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Minimal Proof of Concept
A simple UI for the core migration functions.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import os
from pathlib import Path

class MinimalRevenueCloudUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Revenue Cloud Migration - POC")
        self.root.geometry("800x600")
        
        # Variables
        self.org = tk.StringVar(value="fortradp2")
        self.workbook = tk.StringVar(value="data/Revenue_Cloud_Complete_Upload_Template.xlsx")
        self.is_running = False
        
        self.create_widgets()
        self.check_environment()
    
    def create_widgets(self):
        """Create the UI elements."""
        # Title
        title = tk.Label(self.root, text="Revenue Cloud Migration Tool", 
                        font=('Arial', 16, 'bold'), pady=10)
        title.pack()
        
        # Configuration Frame
        config_frame = tk.LabelFrame(self.root, text="Configuration", padx=10, pady=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Org selection
        tk.Label(config_frame, text="Target Org:").grid(row=0, column=0, sticky='w')
        tk.Entry(config_frame, textvariable=self.org, width=30).grid(row=0, column=1, padx=5)
        tk.Button(config_frame, text="Test Connection", 
                 command=self.test_connection).grid(row=0, column=2, padx=5)
        
        # Workbook selection
        tk.Label(config_frame, text="Workbook:").grid(row=1, column=0, sticky='w', pady=5)
        tk.Entry(config_frame, textvariable=self.workbook, width=30).grid(row=1, column=1, padx=5)
        tk.Button(config_frame, text="Browse", 
                 command=self.browse_workbook).grid(row=1, column=2, padx=5)
        
        # Action Buttons Frame
        action_frame = tk.LabelFrame(self.root, text="Actions", padx=10, pady=10)
        action_frame.pack(fill='x', padx=10, pady=5)
        
        # Create action buttons
        self.clean_btn = tk.Button(action_frame, text="🧹 Clean Fields", 
                                  command=self.clean_fields, width=20, height=2)
        self.clean_btn.pack(side='left', padx=5)
        
        self.import_btn = tk.Button(action_frame, text="📥 Import from Org", 
                                   command=self.import_data, width=20, height=2)
        self.import_btn.pack(side='left', padx=5)
        
        self.upload_btn = tk.Button(action_frame, text="📤 Upload to Org", 
                                   command=self.upload_data, width=20, height=2)
        self.upload_btn.pack(side='left', padx=5)
        
        # Log Frame
        log_frame = tk.LabelFrame(self.root, text="Process Log", padx=10, pady=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill='both', expand=True)
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side='bottom', fill='x')
    
    def log(self, message, level='INFO'):
        """Add message to log."""
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_status(self, message):
        """Update status bar."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def set_buttons_state(self, state):
        """Enable or disable action buttons."""
        self.clean_btn.config(state=state)
        self.import_btn.config(state=state)
        self.upload_btn.config(state=state)
    
    def check_environment(self):
        """Check if required tools are available."""
        self.log("Checking environment...")
        
        # Check for Salesforce CLI
        try:
            result = subprocess.run(['sf', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log("✓ Salesforce CLI found", "SUCCESS")
            else:
                self.log("✗ Salesforce CLI not found", "ERROR")
        except:
            self.log("✗ Salesforce CLI not found", "ERROR")
        
        # Check for required Python scripts
        scripts = [
            'comprehensive_field_cleanup.py',
            'export_to_same_template.py',
            'revenue_cloud_upload_process.py'
        ]
        
        for script in scripts:
            if Path(script).exists():
                self.log(f"✓ {script} found", "SUCCESS")
            else:
                self.log(f"✗ {script} not found", "ERROR")
        
        # Check workbook
        if Path(self.workbook.get()).exists():
            self.log(f"✓ Workbook found: {self.workbook.get()}", "SUCCESS")
        else:
            self.log("⚠ Workbook not found", "WARNING")
    
    def browse_workbook(self):
        """Browse for workbook file."""
        filename = filedialog.askopenfilename(
            title="Select Revenue Cloud Template",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.workbook.set(filename)
            self.log(f"Selected workbook: {filename}")
    
    def test_connection(self):
        """Test Salesforce connection."""
        self.log("Testing connection...")
        self.set_status("Testing connection...")
        
        def run_test():
            try:
                cmd = ['sf', 'org', 'display', '--target-org', self.org.get()]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Parse output for username
                    for line in result.stdout.split('\n'):
                        if 'Username' in line:
                            username = line.split()[-1]
                            self.log(f"✓ Connected to: {username}", "SUCCESS")
                            self.set_status(f"Connected to {username}")
                            return
                    
                    self.log("✓ Connection successful", "SUCCESS")
                    self.set_status("Connected")
                else:
                    self.log(f"✗ Connection failed: {result.stderr}", "ERROR")
                    self.set_status("Connection failed")
            except Exception as e:
                self.log(f"✗ Error: {str(e)}", "ERROR")
                self.set_status("Error")
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def run_script(self, script_name, operation_name):
        """Run a Python script and capture output."""
        self.is_running = True
        self.set_buttons_state('disabled')
        self.set_status(f"Running {operation_name}...")
        
        self.log(f"\n{'='*50}")
        self.log(f"Starting {operation_name}")
        self.log(f"{'='*50}")
        
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
                    line = line.strip()
                    # Color code based on content
                    if '✓' in line or 'Success' in line:
                        self.log(line, "SUCCESS")
                    elif '✗' in line or 'Error' in line or 'Failed' in line:
                        self.log(line, "ERROR")
                    elif '⚠' in line or 'Warning' in line:
                        self.log(line, "WARNING")
                    else:
                        self.log(line)
            
            process.wait()
            
            if process.returncode == 0:
                self.log(f"\n✓ {operation_name} completed successfully!", "SUCCESS")
                self.set_status(f"{operation_name} completed")
            else:
                self.log(f"\n✗ {operation_name} failed with exit code {process.returncode}", "ERROR")
                self.set_status(f"{operation_name} failed")
                
        except Exception as e:
            self.log(f"\n✗ Error running {operation_name}: {str(e)}", "ERROR")
            self.set_status("Error")
        finally:
            self.is_running = False
            self.set_buttons_state('normal')
    
    def clean_fields(self):
        """Run field cleanup."""
        if self.is_running:
            self.log("Another operation is already running", "WARNING")
            return
        
        threading.Thread(
            target=lambda: self.run_script(
                'comprehensive_field_cleanup.py', 
                'Field Cleanup'
            ),
            daemon=True
        ).start()
    
    def import_data(self):
        """Import data from Salesforce."""
        if self.is_running:
            self.log("Another operation is already running", "WARNING")
            return
        
        threading.Thread(
            target=lambda: self.run_script(
                'export_to_same_template.py', 
                'Data Import'
            ),
            daemon=True
        ).start()
    
    def upload_data(self):
        """Upload data to Salesforce."""
        if self.is_running:
            self.log("Another operation is already running", "WARNING")
            return
        
        # Ask for confirmation
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Upload", 
                              "Are you sure you want to upload data to Salesforce?\n\n"
                              "This will modify data in your org."):
            threading.Thread(
                target=lambda: self.run_script(
                    'revenue_cloud_upload_process.py', 
                    'Data Upload'
                ),
                daemon=True
            ).start()

def main():
    root = tk.Tk()
    app = MinimalRevenueCloudUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()