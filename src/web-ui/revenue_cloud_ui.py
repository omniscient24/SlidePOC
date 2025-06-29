#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - User Interface
A comprehensive UI for managing the CPQ to Revenue Cloud migration process.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import threading
import os

class RevenueCloudUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Revenue Cloud Migration Tool")
        self.root.geometry("1200x800")
        
        # Set style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'primary': '#1976D2',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'bg': '#F5F5F5',
            'card': '#FFFFFF'
        }
        
        # Variables
        self.workbook_path = tk.StringVar(value='data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = tk.StringVar(value='fortradp2')
        self.current_process = None
        
        self.create_widgets()
        self.check_environment()
    
    def create_widgets(self):
        """Create the main UI components."""
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Revenue Cloud Migration Tool", 
                font=('Arial', 24, 'bold'), bg=self.colors['primary'], 
                fg='white').pack(pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Configuration and Actions
        left_panel = tk.Frame(main_container, bg=self.colors['bg'])
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Configuration Card
        self.create_config_card(left_panel)
        
        # Actions Card
        self.create_actions_card(left_panel)
        
        # Process Status Card
        self.create_status_card(left_panel)
        
        # Right panel - Log output
        right_panel = tk.Frame(main_container, bg=self.colors['bg'])
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self.create_log_card(right_panel)
    
    def create_config_card(self, parent):
        """Create configuration section."""
        card = self.create_card(parent, "Configuration")
        
        # Workbook selection
        tk.Label(card, text="Workbook:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        
        workbook_frame = tk.Frame(card)
        workbook_frame.grid(row=0, column=1, columnspan=2, sticky='ew', pady=5)
        
        tk.Entry(workbook_frame, textvariable=self.workbook_path, width=50).pack(side='left', fill='x', expand=True)
        tk.Button(workbook_frame, text="Browse", command=self.browse_workbook).pack(side='right', padx=(5, 0))
        
        # Target org
        tk.Label(card, text="Target Org:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        tk.Entry(card, textvariable=self.target_org, width=30).grid(row=1, column=1, sticky='w', pady=5)
        
        # Connection status
        self.connection_status = tk.Label(card, text="⚪ Not connected", font=('Arial', 10))
        self.connection_status.grid(row=1, column=2, sticky='e', pady=5)
        
        tk.Button(card, text="Test Connection", command=self.test_connection,
                 bg=self.colors['primary'], fg='white').grid(row=2, column=1, pady=10)
        
        card.columnconfigure(1, weight=1)
    
    def create_actions_card(self, parent):
        """Create actions section."""
        card = self.create_card(parent, "Actions")
        
        # Main action buttons
        actions = [
            ("🔍 Analyze Workbook", self.analyze_workbook, "Check for issues and field validation"),
            ("🧹 Clean Fields", self.clean_fields, "Remove read-only and system fields"),
            ("📥 Import from Org", self.import_from_org, "Download current data from Salesforce"),
            ("📤 Upload to Org", self.upload_to_org, "Upload data to Salesforce"),
            ("📊 Generate Report", self.generate_report, "Create migration status report")
        ]
        
        for i, (text, command, tooltip) in enumerate(actions):
            btn = tk.Button(card, text=text, command=command, 
                           font=('Arial', 12), width=25, height=2,
                           bg=self.colors['card'], relief='raised', bd=2)
            btn.grid(row=i, column=0, pady=5, padx=10, sticky='ew')
            
            # Tooltip
            self.create_tooltip(btn, tooltip)
        
        card.columnconfigure(0, weight=1)
    
    def create_status_card(self, parent):
        """Create status section."""
        card = self.create_card(parent, "Process Status")
        
        # Object status grid
        self.status_frame = tk.Frame(card)
        self.status_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Headers
        headers = ["Object", "Records", "Status"]
        for i, header in enumerate(headers):
            tk.Label(self.status_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5)
        
        # Will be populated during operations
        self.status_labels = {}
    
    def create_log_card(self, parent):
        """Create log output section."""
        card = self.create_card(parent, "Process Log", expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(card, wrap=tk.WORD, height=20)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configure tags for colored output
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('success', foreground=self.colors['success'])
        self.log_text.tag_config('warning', foreground=self.colors['warning'])
        self.log_text.tag_config('error', foreground=self.colors['error'])
        
        # Control buttons
        control_frame = tk.Frame(card)
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side='left')
        tk.Button(control_frame, text="Save Log", command=self.save_log).pack(side='left', padx=5)
    
    def create_card(self, parent, title, expand=False):
        """Create a card-style frame."""
        frame = tk.LabelFrame(parent, text=title, font=('Arial', 14, 'bold'),
                            bg=self.colors['card'], relief='raised', bd=2)
        frame.pack(fill='both', expand=expand, pady=10)
        return frame
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#FFFFE0", 
                           relief='solid', borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def log(self, message, tag='info'):
        """Add message to log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f"[{timestamp}] {message}\n", tag)
        self.log_text.see('end')
        self.root.update_idletasks()
    
    def check_environment(self):
        """Check if required tools are available."""
        self.log("Checking environment...", 'info')
        
        # Check for Salesforce CLI
        try:
            result = subprocess.run(['sf', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log("✓ Salesforce CLI found", 'success')
            else:
                self.log("✗ Salesforce CLI not found", 'error')
        except:
            self.log("✗ Salesforce CLI not found", 'error')
        
        # Check for Python packages
        required_packages = ['pandas', 'openpyxl']
        for package in required_packages:
            try:
                __import__(package)
                self.log(f"✓ {package} module found", 'success')
            except ImportError:
                self.log(f"✗ {package} module not found", 'error')
    
    def browse_workbook(self):
        """Browse for workbook file."""
        filename = filedialog.askopenfilename(
            title="Select Revenue Cloud Template",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.workbook_path.set(filename)
            self.log(f"Selected workbook: {filename}", 'info')
    
    def test_connection(self):
        """Test connection to Salesforce org."""
        self.log("Testing connection...", 'info')
        
        def run_test():
            try:
                cmd = ['sf', 'org', 'display', '--target-org', self.target_org.get(), '--json']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if 'result' in data:
                        username = data['result'].get('username', 'Unknown')
                        self.connection_status.config(text=f"🟢 Connected: {username}", 
                                                    fg=self.colors['success'])
                        self.log(f"✓ Connected to {username}", 'success')
                else:
                    self.connection_status.config(text="🔴 Connection failed", 
                                                fg=self.colors['error'])
                    self.log("✗ Connection failed", 'error')
            except Exception as e:
                self.log(f"✗ Connection error: {str(e)}", 'error')
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def analyze_workbook(self):
        """Analyze workbook for issues."""
        self.log("\n=== ANALYZING WORKBOOK ===", 'info')
        
        def run_analysis():
            try:
                # Run field analysis
                from comprehensive_field_cleanup import ComprehensiveFieldCleanup
                
                cleanup = ComprehensiveFieldCleanup()
                cleanup.workbook_path = Path(self.workbook_path.get())
                cleanup.target_org = self.target_org.get()
                
                # Analyze each sheet
                issues = []
                for obj_name, sheet_name in cleanup.object_sheet_mapping.items():
                    self.log(f"Analyzing {obj_name}...", 'info')
                    
                    # Get field metadata
                    fields = cleanup.get_field_metadata(obj_name)
                    if fields:
                        # Count problematic fields
                        problematic = 0
                        for field in fields:
                            keep, reason = cleanup.analyze_field(field)
                            if not keep:
                                problematic += 1
                        
                        if problematic > 0:
                            issues.append(f"{obj_name}: {problematic} fields need removal")
                            self.log(f"  ⚠️  {problematic} problematic fields found", 'warning')
                        else:
                            self.log(f"  ✓ No issues found", 'success')
                
                if issues:
                    self.log(f"\n⚠️  Total issues found: {len(issues)}", 'warning')
                    self.log("Run 'Clean Fields' to fix these issues", 'info')
                else:
                    self.log("\n✓ Workbook is clean and ready for upload!", 'success')
                    
            except Exception as e:
                self.log(f"✗ Analysis error: {str(e)}", 'error')
        
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def clean_fields(self):
        """Run field cleanup process."""
        self.log("\n=== CLEANING FIELDS ===", 'info')
        
        def run_cleanup():
            try:
                # Run the cleanup script
                result = subprocess.run(['python3', 'comprehensive_field_cleanup.py'], 
                                      capture_output=True, text=True)
                
                # Parse output
                for line in result.stdout.split('\n'):
                    if '✓' in line:
                        self.log(line, 'success')
                    elif '✗' in line:
                        self.log(line, 'warning')
                    elif 'Processing' in line or 'COMPLETE' in line:
                        self.log(line, 'info')
                
                if result.returncode == 0:
                    self.log("\n✓ Field cleanup completed successfully!", 'success')
                else:
                    self.log("\n✗ Field cleanup failed", 'error')
                    
            except Exception as e:
                self.log(f"✗ Cleanup error: {str(e)}", 'error')
        
        threading.Thread(target=run_cleanup, daemon=True).start()
    
    def import_from_org(self):
        """Import data from Salesforce org."""
        self.log("\n=== IMPORTING FROM SALESFORCE ===", 'info')
        
        def run_import():
            try:
                # Run the export script
                result = subprocess.run(['python3', 'export_to_same_template.py'], 
                                      capture_output=True, text=True)
                
                # Parse output and update status
                for line in result.stdout.split('\n'):
                    if 'Processing' in line:
                        self.log(line, 'info')
                    elif 'Found' in line and 'records' in line:
                        # Extract object and count
                        parts = line.split()
                        if len(parts) >= 3:
                            count = parts[1]
                            self.log(f"  Found {count} records", 'success')
                    elif 'COMPLETE' in line:
                        self.log(line, 'success')
                
                if result.returncode == 0:
                    self.log("\n✓ Import completed successfully!", 'success')
                else:
                    self.log("\n✗ Import failed", 'error')
                    
            except Exception as e:
                self.log(f"✗ Import error: {str(e)}", 'error')
        
        threading.Thread(target=run_import, daemon=True).start()
    
    def upload_to_org(self):
        """Upload data to Salesforce org."""
        self.log("\n=== UPLOADING TO SALESFORCE ===", 'info')
        
        # Clear status display
        for widget in self.status_frame.winfo_children():
            if widget.grid_info()['row'] > 0:
                widget.destroy()
        
        def run_upload():
            try:
                # Run the upload script
                process = subprocess.Popen(['python3', 'revenue_cloud_upload_process.py'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT,
                                         text=True,
                                         bufsize=1)
                
                current_row = 1
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse output
                    if ':' in line and not line.startswith('='):
                        parts = line.split(':', 1)
                        obj_name = parts[0].strip()
                        
                        # Create status row if needed
                        if obj_name not in self.status_labels:
                            self.status_labels[obj_name] = {
                                'name': tk.Label(self.status_frame, text=obj_name),
                                'count': tk.Label(self.status_frame, text="-"),
                                'status': tk.Label(self.status_frame, text="⏳ Processing")
                            }
                            
                            self.status_labels[obj_name]['name'].grid(row=current_row, column=0, sticky='w', padx=5)
                            self.status_labels[obj_name]['count'].grid(row=current_row, column=1, padx=5)
                            self.status_labels[obj_name]['status'].grid(row=current_row, column=2, padx=5)
                            current_row += 1
                        
                        # Update status
                        if '✓' in line:
                            self.log(line, 'success')
                            # Extract record count
                            if 'records' in line:
                                count = line.split()[2]
                                self.status_labels[obj_name]['count'].config(text=count)
                            self.status_labels[obj_name]['status'].config(text="✅ Success", 
                                                                         fg=self.colors['success'])
                        elif '✗' in line:
                            self.log(line, 'error')
                            self.status_labels[obj_name]['status'].config(text="❌ Failed", 
                                                                         fg=self.colors['error'])
                    elif 'SUMMARY' in line:
                        self.log(line, 'info')
                    else:
                        self.log(line, 'info')
                
                process.wait()
                
                if process.returncode == 0:
                    self.log("\n✓ Upload completed successfully!", 'success')
                else:
                    self.log("\n✗ Upload completed with errors", 'warning')
                    
            except Exception as e:
                self.log(f"✗ Upload error: {str(e)}", 'error')
        
        threading.Thread(target=run_upload, daemon=True).start()
    
    def generate_report(self):
        """Generate migration status report."""
        self.log("\n=== GENERATING REPORT ===", 'info')
        
        def run_report():
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = f'migration_report_{timestamp}.txt'
                
                with open(report_file, 'w') as f:
                    f.write("REVENUE CLOUD MIGRATION REPORT\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Workbook: {self.workbook_path.get()}\n")
                    f.write(f"Target Org: {self.target_org.get()}\n\n")
                    
                    # Add log contents
                    f.write("PROCESS LOG\n")
                    f.write("-" * 80 + "\n")
                    f.write(self.log_text.get('1.0', 'end'))
                
                self.log(f"✓ Report saved: {report_file}", 'success')
                
                # Open report
                if os.name == 'nt':  # Windows
                    os.startfile(report_file)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.call(['open', report_file])
                    
            except Exception as e:
                self.log(f"✗ Report error: {str(e)}", 'error')
        
        threading.Thread(target=run_report, daemon=True).start()
    
    def clear_log(self):
        """Clear the log output."""
        self.log_text.delete('1.0', 'end')
    
    def save_log(self):
        """Save log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.log_text.get('1.0', 'end'))
            self.log(f"Log saved to: {filename}", 'success')

def main():
    root = tk.Tk()
    app = RevenueCloudUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()