#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Flask Web UI POC
A simple web interface for the core migration functions.
"""

from flask import Flask, render_template_string, request, jsonify, Response
import subprocess
import threading
import queue
import os
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)

# Global variables
org = "fortradp2"
workbook = "data/Revenue_Cloud_Complete_Upload_Template.xlsx"
output_queue = queue.Queue()
is_running = False
current_process = None

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud Migration Tool</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .config-section {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .config-row {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .config-label {
            width: 120px;
            font-weight: bold;
        }
        .config-value {
            flex: 1;
            padding: 5px 10px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-primary:hover:not(:disabled) {
            background-color: #0056b3;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        .btn-success:hover:not(:disabled) {
            background-color: #218838;
        }
        .btn-warning {
            background-color: #ffc107;
            color: black;
        }
        .btn-warning:hover:not(:disabled) {
            background-color: #e0a800;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .btn-danger:hover:not(:disabled) {
            background-color: #c82333;
        }
        .log-container {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        .log-entry {
            margin-bottom: 2px;
            white-space: pre-wrap;
        }
        .log-info { color: #d4d4d4; }
        .log-success { color: #4ec9b0; }
        .log-warning { color: #dcdcaa; }
        .log-error { color: #f48771; }
        .status-bar {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-ready { background-color: #28a745; }
        .status-running { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Revenue Cloud Migration Tool</h1>
        
        <div class="config-section">
            <h3>Configuration</h3>
            <div class="config-row">
                <span class="config-label">Target Org:</span>
                <span class="config-value" id="org">{{ org }}</span>
            </div>
            <div class="config-row">
                <span class="config-label">Workbook:</span>
                <span class="config-value" id="workbook">{{ workbook }}</span>
            </div>
        </div>
        
        <div class="button-group">
            <button class="btn-primary" onclick="testConnection()">
                🔌 Test Connection
            </button>
            <button class="btn-success" onclick="cleanFields()">
                🧹 Clean Fields
            </button>
            <button class="btn-warning" onclick="importData()">
                📥 Import from Org
            </button>
            <button class="btn-danger" onclick="uploadData()">
                📤 Upload to Org
            </button>
        </div>
        
        <h3>Process Log</h3>
        <div class="log-container" id="log-container">
            <div class="log-entry log-info">Ready to start...</div>
        </div>
        
        <div class="status-bar">
            <div>
                <span class="status-indicator status-ready" id="status-indicator"></span>
                <span id="status-text">Ready</span>
            </div>
            <div id="timestamp">{{ timestamp }}</div>
        </div>
    </div>
    
    <script>
        let eventSource = null;
        let isRunning = false;
        
        function updateButtons(disabled) {
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = disabled);
            isRunning = disabled;
            
            const indicator = document.getElementById('status-indicator');
            indicator.className = 'status-indicator ' + (disabled ? 'status-running' : 'status-ready');
        }
        
        function addLogEntry(message, level = 'info') {
            const logContainer = document.getElementById('log-container');
            const entry = document.createElement('div');
            entry.className = 'log-entry log-' + level;
            entry.textContent = message;
            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        function startEventStream(endpoint) {
            if (eventSource) {
                eventSource.close();
            }
            
            updateButtons(true);
            eventSource = new EventSource(endpoint);
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.status === 'complete') {
                    eventSource.close();
                    updateButtons(false);
                    document.getElementById('status-text').textContent = 'Ready';
                } else if (data.status === 'error') {
                    eventSource.close();
                    updateButtons(false);
                    document.getElementById('status-text').textContent = 'Error';
                    addLogEntry(data.message, 'error');
                } else {
                    let level = 'info';
                    if (data.message.includes('✓') || data.message.includes('Success')) {
                        level = 'success';
                    } else if (data.message.includes('✗') || data.message.includes('Error')) {
                        level = 'error';
                    } else if (data.message.includes('⚠') || data.message.includes('Warning')) {
                        level = 'warning';
                    }
                    addLogEntry(data.message, level);
                    
                    if (data.status_text) {
                        document.getElementById('status-text').textContent = data.status_text;
                    }
                }
            };
            
            eventSource.onerror = function() {
                eventSource.close();
                updateButtons(false);
                document.getElementById('status-text').textContent = 'Connection lost';
            };
        }
        
        function testConnection() {
            addLogEntry('\\n=== Testing Connection ===', 'info');
            startEventStream('/test-connection');
        }
        
        function cleanFields() {
            addLogEntry('\\n=== Cleaning Fields ===', 'info');
            startEventStream('/clean-fields');
        }
        
        function importData() {
            addLogEntry('\\n=== Importing Data ===', 'info');
            startEventStream('/import-data');
        }
        
        function uploadData() {
            if (confirm('Are you sure you want to upload data to Salesforce? This will modify data in your org.')) {
                addLogEntry('\\n=== Uploading Data ===', 'info');
                startEventStream('/upload-data');
            }
        }
        
        // Update timestamp
        setInterval(function() {
            document.getElementById('timestamp').textContent = new Date().toLocaleString();
        }, 1000);
    </script>
</body>
</html>
"""

def stream_output(func, *args):
    """Run a function and stream its output."""
    def generate():
        try:
            for message in func(*args):
                yield f"data: {json.dumps(message)}\\n\\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\\n\\n"
    
    return Response(generate(), mimetype="text/event-stream")

def run_command(cmd, operation_name):
    """Run a command and yield output messages."""
    global is_running, current_process
    is_running = True
    
    try:
        yield {"message": f"Starting {operation_name}...", "status_text": f"Running {operation_name}"}
        
        current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in iter(current_process.stdout.readline, ''):
            if line:
                yield {"message": line.strip()}
        
        current_process.wait()
        
        if current_process.returncode == 0:
            yield {"message": f"✓ {operation_name} completed successfully!"}
        else:
            yield {"message": f"✗ {operation_name} failed with exit code {current_process.returncode}"}
            
    except Exception as e:
        yield {"message": f"✗ Error: {str(e)}"}
    finally:
        is_running = False
        current_process = None
        yield {"status": "complete"}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                org=org, 
                                workbook=workbook,
                                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/test-connection')
def test_connection():
    cmd = ['sf', 'org', 'display', '--target-org', org, '--json']
    
    def generate():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                username = data.get('result', {}).get('username', 'Unknown')
                yield {"message": f"✓ Connected to: {username}"}
            else:
                yield {"message": "✗ Connection failed"}
        except Exception as e:
            yield {"message": f"✗ Error: {str(e)}"}
        finally:
            yield {"status": "complete"}
    
    return stream_output(lambda: generate())

@app.route('/clean-fields')
def clean_fields():
    return stream_output(run_command, 
                        ['python3', 'comprehensive_field_cleanup.py'],
                        'Field Cleanup')

@app.route('/import-data')
def import_data():
    return stream_output(run_command,
                        ['python3', 'export_to_same_template.py'],
                        'Data Import')

@app.route('/upload-data')
def upload_data():
    return stream_output(run_command,
                        ['python3', 'revenue_cloud_upload_process.py'],
                        'Data Upload')

if __name__ == '__main__':
    print("\\n" + "="*60)
    print("Revenue Cloud Migration Tool - Web UI")
    print("="*60)
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\\n")
    
    app.run(debug=False, port=5000)