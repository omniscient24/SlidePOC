#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Simple Web UI POC
A minimal web interface using only Python standard library.
"""

import http.server
import socketserver
import subprocess
import json
import threading
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8080
org = "fortradp2"
workbook = "data/Revenue_Cloud_Complete_Upload_Template.xlsx"

# HTML content
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud Migration Tool</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
        }
        .info-box {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
        }
        .info-row {
            display: flex;
            margin-bottom: 8px;
        }
        .info-label {
            font-weight: bold;
            width: 120px;
            color: #34495e;
        }
        .info-value {
            color: #2c3e50;
        }
        .button-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }
        button {
            padding: 15px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .btn-test {
            background-color: #3498db;
            color: white;
        }
        .btn-test:hover:not(:disabled) {
            background-color: #2980b9;
        }
        .btn-clean {
            background-color: #2ecc71;
            color: white;
        }
        .btn-clean:hover:not(:disabled) {
            background-color: #27ae60;
        }
        .btn-import {
            background-color: #f39c12;
            color: white;
        }
        .btn-import:hover:not(:disabled) {
            background-color: #e67e22;
        }
        .btn-upload {
            background-color: #e74c3c;
            color: white;
        }
        .btn-upload:hover:not(:disabled) {
            background-color: #c0392b;
        }
        .log-container {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.4;
        }
        .log-entry {
            margin-bottom: 3px;
        }
        .log-success {
            color: #2ecc71;
        }
        .log-error {
            color: #e74c3c;
        }
        .log-warning {
            color: #f39c12;
        }
        .status-bar {
            background-color: #34495e;
            color: white;
            padding: 12px 20px;
            border-radius: 5px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }
        .spinner {
            border: 2px solid #f3f3f3;
            border-top: 2px solid #3498db;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            animation: spin 1s linear infinite;
            display: none;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .running .spinner {
            display: inline-block;
        }
        .icon {
            font-size: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Revenue Cloud Migration Tool</h1>
        <p class="subtitle">Minimal Proof of Concept</p>
        
        <div class="info-box">
            <div class="info-row">
                <span class="info-label">Target Org:</span>
                <span class="info-value">%ORG%</span>
            </div>
            <div class="info-row">
                <span class="info-label">Workbook:</span>
                <span class="info-value">%WORKBOOK%</span>
            </div>
        </div>
        
        <div class="button-grid">
            <button class="btn-test" onclick="runAction('test')">
                <span class="icon">🔌</span>
                Test Connection
            </button>
            <button class="btn-clean" onclick="runAction('clean')">
                <span class="icon">🧹</span>
                Clean Fields
            </button>
            <button class="btn-import" onclick="runAction('import')">
                <span class="icon">📥</span>
                Import from Org
            </button>
            <button class="btn-upload" onclick="confirmAndRun()">
                <span class="icon">📤</span>
                Upload to Org
            </button>
        </div>
        
        <h3>Process Log</h3>
        <div class="log-container" id="log">
            <div class="log-entry">Welcome to Revenue Cloud Migration Tool</div>
            <div class="log-entry">Ready to start...</div>
        </div>
        
        <div class="status-bar">
            <div>
                <span id="status">Ready</span>
                <div class="spinner" id="spinner"></div>
            </div>
            <div id="time"></div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        function updateTime() {
            document.getElementById('time').textContent = new Date().toLocaleString();
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        function log(message, type = '') {
            const logDiv = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            if (type) entry.className += ' log-' + type;
            entry.textContent = message;
            logDiv.appendChild(entry);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function setRunning(running) {
            isRunning = running;
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = running);
            
            const status = document.getElementById('status');
            const statusBar = status.parentElement.parentElement;
            
            if (running) {
                statusBar.classList.add('running');
            } else {
                statusBar.classList.remove('running');
            }
        }
        
        function updateStatus(text) {
            document.getElementById('status').textContent = text;
        }
        
        function confirmAndRun() {
            if (confirm('Are you sure you want to upload data to Salesforce?\\n\\nThis will modify data in your org.')) {
                runAction('upload');
            }
        }
        
        async function runAction(action) {
            if (isRunning) {
                log('Another operation is already running', 'warning');
                return;
            }
            
            setRunning(true);
            log('\\n' + '='.repeat(50));
            
            try {
                updateStatus('Running ' + action + '...');
                
                const response = await fetch('/api/' + action);
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\\n');
                    
                    for (const line of lines) {
                        if (line.trim()) {
                            let type = '';
                            if (line.includes('✓') || line.includes('Success')) {
                                type = 'success';
                            } else if (line.includes('✗') || line.includes('Error')) {
                                type = 'error';
                            } else if (line.includes('⚠') || line.includes('Warning')) {
                                type = 'warning';
                            }
                            log(line, type);
                        }
                    }
                }
                
                updateStatus('Ready');
            } catch (error) {
                log('Error: ' + error.message, 'error');
                updateStatus('Error');
            } finally {
                setRunning(false);
            }
        }
    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve main page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = HTML_CONTENT.replace('%ORG%', org).replace('%WORKBOOK%', workbook)
            self.wfile.write(html.encode())
            
        elif parsed_path.path.startswith('/api/'):
            # Handle API requests
            action = parsed_path.path[5:]  # Remove '/api/'
            self.handle_api(action)
        else:
            self.send_error(404)
    
    def handle_api(self, action):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        if action == 'test':
            self.test_connection()
        elif action == 'clean':
            self.run_script('comprehensive_field_cleanup.py', 'Field Cleanup')
        elif action == 'import':
            self.run_script('export_to_same_template.py', 'Data Import')
        elif action == 'upload':
            self.run_script('revenue_cloud_upload_process.py', 'Data Upload')
        else:
            self.wfile.write(b"Unknown action\\n")
    
    def test_connection(self):
        self.wfile.write(b"Testing connection...\\n")
        self.wfile.flush()
        
        try:
            cmd = ['sf', 'org', 'display', '--target-org', org]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse username from output
                for line in result.stdout.split('\\n'):
                    if 'Username' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            username = parts[-1]
                            self.wfile.write(f"✓ Connected to: {username}\\n".encode())
                            return
                
                self.wfile.write("✓ Connection successful\n".encode())
            else:
                self.wfile.write(f"✗ Connection failed: {result.stderr}\\n".encode())
        except Exception as e:
            self.wfile.write(f"✗ Error: {str(e)}\\n".encode())
    
    def run_script(self, script_name, operation_name):
        self.wfile.write(f"Starting {operation_name}...\\n".encode())
        self.wfile.write(b"=" * 50 + b"\\n")
        self.wfile.flush()
        
        try:
            process = subprocess.Popen(
                ['python3', script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.wfile.write(line.encode())
                    self.wfile.flush()
            
            process.wait()
            
            if process.returncode == 0:
                self.wfile.write(f"\\n✓ {operation_name} completed successfully!\\n".encode())
            else:
                self.wfile.write(f"\\n✗ {operation_name} failed with exit code {process.returncode}\\n".encode())
                
        except Exception as e:
            self.wfile.write(f"\\n✗ Error running {operation_name}: {str(e)}\\n".encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def main():
    os.chdir(Path(__file__).parent)
    
    print("\\n" + "="*60)
    print("Revenue Cloud Migration Tool - Simple Web UI")
    print("="*60)
    print(f"Starting web server on port {PORT}...")
    print(f"Open your browser to: http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\\n")
    
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nShutting down server...")

if __name__ == '__main__':
    main()