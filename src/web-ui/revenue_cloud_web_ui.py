#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Web UI
A modern web interface for the Revenue Cloud migration process.
"""

from flask import Flask, render_template, jsonify, request, send_file
import subprocess
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import threading
import queue
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'revenue-cloud-migration-2024'

# Global variables
process_queue = queue.Queue()
current_status = {
    'connected': False,
    'org': 'fortradp2',
    'username': '',
    'workbook': 'data/Revenue_Cloud_Complete_Upload_Template.xlsx',
    'process_running': False,
    'last_update': ''
}

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current status."""
    return jsonify(current_status)

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test Salesforce connection."""
    data = request.json
    org = data.get('org', 'fortradp2')
    
    try:
        cmd = ['sf', 'org', 'display', '--target-org', org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            org_data = json.loads(result.stdout)
            if 'result' in org_data:
                current_status['connected'] = True
                current_status['org'] = org
                current_status['username'] = org_data['result'].get('username', 'Unknown')
                return jsonify({
                    'success': True,
                    'message': f'Connected to {current_status["username"]}'
                })
        
        current_status['connected'] = False
        return jsonify({
            'success': False,
            'message': 'Connection failed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/analyze', methods=['POST'])
def analyze_workbook():
    """Analyze workbook for issues."""
    if current_status['process_running']:
        return jsonify({'success': False, 'message': 'Another process is running'})
    
    def run_analysis():
        current_status['process_running'] = True
        results = []
        
        try:
            from comprehensive_field_cleanup import ComprehensiveFieldCleanup
            
            cleanup = ComprehensiveFieldCleanup()
            cleanup.workbook_path = Path(current_status['workbook'])
            cleanup.target_org = current_status['org']
            
            total_issues = 0
            for obj_name, sheet_name in cleanup.object_sheet_mapping.items():
                fields = cleanup.get_field_metadata(obj_name)
                if fields:
                    problematic = 0
                    for field in fields:
                        keep, reason = cleanup.analyze_field(field)
                        if not keep:
                            problematic += 1
                    
                    results.append({
                        'object': obj_name,
                        'issues': problematic,
                        'status': 'clean' if problematic == 0 else 'needs_cleanup'
                    })
                    total_issues += problematic
            
            process_queue.put({
                'type': 'analysis_complete',
                'results': results,
                'total_issues': total_issues
            })
            
        except Exception as e:
            process_queue.put({
                'type': 'error',
                'message': str(e)
            })
        
        current_status['process_running'] = False
    
    threading.Thread(target=run_analysis, daemon=True).start()
    return jsonify({'success': True, 'message': 'Analysis started'})

@app.route('/api/clean', methods=['POST'])
def clean_fields():
    """Run field cleanup."""
    if current_status['process_running']:
        return jsonify({'success': False, 'message': 'Another process is running'})
    
    def run_cleanup():
        current_status['process_running'] = True
        
        try:
            result = subprocess.run(['python3', 'comprehensive_field_cleanup.py'], 
                                  capture_output=True, text=True)
            
            process_queue.put({
                'type': 'cleanup_complete',
                'success': result.returncode == 0,
                'output': result.stdout
            })
            
        except Exception as e:
            process_queue.put({
                'type': 'error',
                'message': str(e)
            })
        
        current_status['process_running'] = False
    
    threading.Thread(target=run_cleanup, daemon=True).start()
    return jsonify({'success': True, 'message': 'Cleanup started'})

@app.route('/api/import', methods=['POST'])
def import_data():
    """Import data from Salesforce."""
    if current_status['process_running']:
        return jsonify({'success': False, 'message': 'Another process is running'})
    
    def run_import():
        current_status['process_running'] = True
        
        try:
            process = subprocess.Popen(['python3', 'export_to_same_template.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     bufsize=1)
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    process_queue.put({
                        'type': 'log',
                        'message': line.strip()
                    })
            
            process.wait()
            
            process_queue.put({
                'type': 'import_complete',
                'success': process.returncode == 0
            })
            
        except Exception as e:
            process_queue.put({
                'type': 'error',
                'message': str(e)
            })
        
        current_status['process_running'] = False
    
    threading.Thread(target=run_import, daemon=True).start()
    return jsonify({'success': True, 'message': 'Import started'})

@app.route('/api/upload', methods=['POST'])
def upload_data():
    """Upload data to Salesforce."""
    if current_status['process_running']:
        return jsonify({'success': False, 'message': 'Another process is running'})
    
    def run_upload():
        current_status['process_running'] = True
        object_status = {}
        
        try:
            process = subprocess.Popen(['python3', 'revenue_cloud_upload_process.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     bufsize=1)
            
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                
                # Parse upload progress
                if ':' in line and not line.startswith('='):
                    parts = line.split(':', 1)
                    obj_name = parts[0].strip()
                    
                    if '✓' in line:
                        object_status[obj_name] = 'success'
                    elif '✗' in line:
                        object_status[obj_name] = 'failed'
                    else:
                        object_status[obj_name] = 'processing'
                    
                    process_queue.put({
                        'type': 'upload_progress',
                        'object': obj_name,
                        'status': object_status[obj_name],
                        'message': line
                    })
                else:
                    process_queue.put({
                        'type': 'log',
                        'message': line
                    })
            
            process.wait()
            
            process_queue.put({
                'type': 'upload_complete',
                'success': process.returncode == 0,
                'results': object_status
            })
            
        except Exception as e:
            process_queue.put({
                'type': 'error',
                'message': str(e)
            })
        
        current_status['process_running'] = False
    
    threading.Thread(target=run_upload, daemon=True).start()
    return jsonify({'success': True, 'message': 'Upload started'})

@app.route('/api/events')
def events():
    """Server-sent events for real-time updates."""
    def generate():
        while True:
            try:
                message = process_queue.get(timeout=1)
                yield f"data: {json.dumps(message)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/api/download-report')
def download_report():
    """Generate and download report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'migration_report_{timestamp}.txt'
    
    with open(report_file, 'w') as f:
        f.write("REVENUE CLOUD MIGRATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Workbook: {current_status['workbook']}\n")
        f.write(f"Target Org: {current_status['org']}\n")
        f.write(f"Connected User: {current_status['username']}\n")
        f.write("\n")
        f.write("Last Update: " + current_status.get('last_update', 'N/A') + "\n")
    
    return send_file(report_file, as_attachment=True)

# Create templates directory
templates_dir = Path('templates')
templates_dir.mkdir(exist_ok=True)

# Create HTML template
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Revenue Cloud Migration Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: #1976D2; color: white; padding: 2rem; text-align: center; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .button { background: #1976D2; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .button:hover { background: #1565C0; }
        .button:disabled { background: #ccc; cursor: not-allowed; }
        .button.secondary { background: #757575; }
        .button.success { background: #4CAF50; }
        .button.warning { background: #FF9800; }
        .status { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; }
        .status.connected { background: #E8F5E9; color: #2E7D32; }
        .status.disconnected { background: #FFEBEE; color: #C62828; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .log { background: #263238; color: #B0BEC5; padding: 1rem; border-radius: 4px; height: 400px; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.875rem; }
        .log .success { color: #81C784; }
        .log .error { color: #E57373; }
        .log .warning { color: #FFB74D; }
        .progress { margin: 1rem 0; }
        .progress-item { display: flex; align-items: center; padding: 0.5rem 0; }
        .progress-item .name { flex: 1; }
        .progress-item .status { margin-left: 1rem; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #1976D2; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Revenue Cloud Migration Tool</h1>
        <p>Migrate from Salesforce CPQ to Revenue Cloud</p>
    </div>
    
    <div class="container">
        <div class="card">
            <h2>Connection Status</h2>
            <div style="margin: 1rem 0;">
                <span id="connection-status" class="status disconnected">Disconnected</span>
                <span id="org-name" style="margin-left: 1rem;"></span>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <input type="text" id="org-input" placeholder="Target Org" value="fortradp2" style="flex: 1; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                <button class="button" onclick="testConnection()">Connect</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Actions</h2>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <button class="button" onclick="analyzeWorkbook()" id="analyze-btn">
                        🔍 Analyze Workbook
                    </button>
                    <button class="button" onclick="cleanFields()" id="clean-btn">
                        🧹 Clean Fields
                    </button>
                    <button class="button" onclick="importData()" id="import-btn">
                        📥 Import from Org
                    </button>
                    <button class="button success" onclick="uploadData()" id="upload-btn">
                        📤 Upload to Org
                    </button>
                    <button class="button secondary" onclick="downloadReport()">
                        📊 Download Report
                    </button>
                </div>
            </div>
            
            <div class="card">
                <h2>Upload Progress</h2>
                <div id="progress" class="progress"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>Process Log</h2>
            <div id="log" class="log"></div>
        </div>
    </div>
    
    <script>
        let eventSource;
        let isProcessing = false;
        
        function log(message, type = 'info') {
            const logEl = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            const className = type === 'success' ? 'success' : type === 'error' ? 'error' : '';
            logEl.innerHTML += `<div class="${className}">[${timestamp}] ${message}</div>`;
            logEl.scrollTop = logEl.scrollHeight;
        }
        
        function updateButtons(disabled) {
            isProcessing = disabled;
            document.querySelectorAll('button').forEach(btn => {
                if (btn.textContent.includes('Download')) return;
                btn.disabled = disabled;
            });
        }
        
        function testConnection() {
            const org = document.getElementById('org-input').value;
            log('Testing connection...');
            
            fetch('/api/test-connection', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({org: org})
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('connection-status').className = 'status connected';
                    document.getElementById('connection-status').textContent = 'Connected';
                    document.getElementById('org-name').textContent = data.message;
                    log(data.message, 'success');
                } else {
                    log(data.message, 'error');
                }
            });
        }
        
        function analyzeWorkbook() {
            updateButtons(true);
            log('Starting workbook analysis...');
            
            fetch('/api/analyze', {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    log(data.message, 'error');
                    updateButtons(false);
                }
            });
        }
        
        function cleanFields() {
            updateButtons(true);
            log('Starting field cleanup...');
            
            fetch('/api/clean', {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    log(data.message, 'error');
                    updateButtons(false);
                }
            });
        }
        
        function importData() {
            updateButtons(true);
            log('Starting data import...');
            
            fetch('/api/import', {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    log(data.message, 'error');
                    updateButtons(false);
                }
            });
        }
        
        function uploadData() {
            updateButtons(true);
            log('Starting data upload...');
            document.getElementById('progress').innerHTML = '';
            
            fetch('/api/upload', {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    log(data.message, 'error');
                    updateButtons(false);
                }
            });
        }
        
        function downloadReport() {
            window.location.href = '/api/download-report';
        }
        
        // Set up server-sent events
        function setupEvents() {
            eventSource = new EventSource('/api/events');
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                switch(data.type) {
                    case 'log':
                        log(data.message);
                        break;
                    
                    case 'upload_progress':
                        updateProgress(data.object, data.status, data.message);
                        break;
                    
                    case 'analysis_complete':
                        showAnalysisResults(data.results, data.total_issues);
                        updateButtons(false);
                        break;
                    
                    case 'cleanup_complete':
                        log(data.success ? '✓ Cleanup completed!' : '✗ Cleanup failed', data.success ? 'success' : 'error');
                        updateButtons(false);
                        break;
                    
                    case 'import_complete':
                        log(data.success ? '✓ Import completed!' : '✗ Import failed', data.success ? 'success' : 'error');
                        updateButtons(false);
                        break;
                    
                    case 'upload_complete':
                        log(data.success ? '✓ Upload completed!' : '✗ Upload completed with errors', data.success ? 'success' : 'error');
                        updateButtons(false);
                        break;
                    
                    case 'error':
                        log(data.message, 'error');
                        updateButtons(false);
                        break;
                }
            };
        }
        
        function updateProgress(object, status, message) {
            const progressEl = document.getElementById('progress');
            let item = document.getElementById(`progress-${object}`);
            
            if (!item) {
                item = document.createElement('div');
                item.id = `progress-${object}`;
                item.className = 'progress-item';
                item.innerHTML = `
                    <span class="name">${object}</span>
                    <span class="status"></span>
                `;
                progressEl.appendChild(item);
            }
            
            const statusEl = item.querySelector('.status');
            if (status === 'processing') {
                statusEl.innerHTML = '<div class="spinner"></div>';
            } else if (status === 'success') {
                statusEl.innerHTML = '✅';
            } else if (status === 'failed') {
                statusEl.innerHTML = '❌';
            }
            
            log(message, status === 'success' ? 'success' : status === 'failed' ? 'error' : 'info');
        }
        
        function showAnalysisResults(results, totalIssues) {
            const progressEl = document.getElementById('progress');
            progressEl.innerHTML = '<h3>Analysis Results</h3>';
            
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'progress-item';
                item.innerHTML = `
                    <span class="name">${result.object}</span>
                    <span class="status">${result.issues > 0 ? `⚠️ ${result.issues} issues` : '✅ Clean'}</span>
                `;
                progressEl.appendChild(item);
            });
            
            if (totalIssues > 0) {
                log(`⚠️ Found ${totalIssues} total issues. Run 'Clean Fields' to fix.`, 'warning');
            } else {
                log('✓ Workbook is clean and ready for upload!', 'success');
            }
        }
        
        // Initialize
        setupEvents();
        testConnection();
    </script>
</body>
</html>'''

# Save the template
with open('templates/index.html', 'w') as f:
    f.write(html_template)

if __name__ == '__main__':
    print("Starting Revenue Cloud Web UI...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)