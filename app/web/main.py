#!/usr/bin/env python3
"""
Revenue Cloud Migration Tool - Structured Web UI POC
Provides separate paths for new implementations and ongoing data management.
"""

import http.server
import socketserver
import subprocess
import json
import threading
import os
import sys
import time
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8080
org = "fortradp2"

# Get the project root directory (2 levels up from web-ui)
PROJECT_ROOT = Path(__file__).parent.parent.parent
workbook = str(PROJECT_ROOT / "data/templates/master/Revenue_Cloud_Complete_Upload_Template.xlsx")

# HTML content for main page
MAIN_PAGE_HTML = """
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
            max-width: 1000px;
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
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }
        .path-selection {
            display: flex;
            gap: 30px;
            margin-top: 40px;
            justify-content: center;
        }
        .path-card {
            flex: 1;
            max-width: 450px;
            padding: 30px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background-color: #fafafa;
        }
        .path-card:hover {
            border-color: #3498db;
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            background-color: white;
        }
        .path-card h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.8em;
        }
        .path-card p {
            color: #666;
            margin-bottom: 20px;
            min-height: 60px;
        }
        .path-card .icon {
            font-size: 3em;
            margin-bottom: 20px;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: background-color 0.3s;
        }
        .btn-primary:hover {
            background-color: #2980b9;
        }
        .info-section {
            margin-top: 50px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        .info-section h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .info-section ul {
            color: #666;
            margin-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Revenue Cloud Migration Tool</h1>
        <p class="subtitle">Choose your path based on your implementation needs</p>
        
        <div class="path-selection">
            <div class="path-card" onclick="window.location.href='/new-implementation'">
                <div class="icon">🏗️</div>
                <h2>New Implementation</h2>
                <p>Follow a guided step-by-step process for initial Revenue Cloud setup with proper object dependencies</p>
                <a href="/new-implementation" class="btn-primary">Start Setup Process</a>
            </div>
            
            <div class="path-card" onclick="window.location.href='/data-management'">
                <div class="icon">🔄</div>
                <h2>Ongoing Data Management</h2>
                <p>Manage and update existing Revenue Cloud data for established implementations</p>
                <a href="/data-management" class="btn-primary">Manage Data</a>
            </div>
        </div>
        
        <div class="info-section">
            <h3>ℹ️ About this Tool</h3>
            <ul>
                <li><strong>New Implementation:</strong> Provides a structured workflow ensuring objects are created in the correct order with all dependencies satisfied</li>
                <li><strong>Ongoing Management:</strong> Direct access to all Revenue Cloud objects for updates, imports, and maintenance</li>
                <li>Connected to org: <strong>{{org}}</strong></li>
                <li>Using template: <strong>{{workbook}}</strong></li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# HTML content for new implementation process
NEW_IMPLEMENTATION_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud - New Implementation</title>
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
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.2em;
        }
        .back-link {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .progress-container {
            margin-bottom: 40px;
        }
        .progress-bar {
            background-color: #e0e0e0;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            background-color: #27ae60;
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #666;
        }
        .phase-container {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .phase {
            flex: 1;
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            text-align: center;
            position: relative;
        }
        .phase.active {
            border-color: #3498db;
            background-color: #f0f8ff;
        }
        .phase.completed {
            border-color: #27ae60;
            background-color: #f0fff4;
        }
        .phase h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .phase-number {
            position: absolute;
            top: -15px;
            left: 50%;
            transform: translateX(-50%);
            background-color: white;
            padding: 0 10px;
            font-weight: bold;
            color: #666;
        }
        .phase.active .phase-number {
            color: #3498db;
        }
        .phase.completed .phase-number {
            color: #27ae60;
        }
        .objects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .object-card {
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: #fafafa;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .object-card:hover {
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .object-card.completed {
            background-color: #f0fff4;
            border-color: #27ae60;
        }
        .object-card.in-progress {
            background-color: #fff3cd;
            border-color: #ffc107;
        }
        .object-card h4 {
            margin: 0 0 8px 0;
            color: #2c3e50;
        }
        .object-status {
            font-size: 0.9em;
            color: #666;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background-color: #2980b9;
        }
        .btn-secondary {
            background-color: #95a5a6;
            color: white;
        }
        .btn-secondary:hover {
            background-color: #7f8c8d;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .instructions {
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .instructions h4 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .instructions ul {
            margin: 0;
            padding-left: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ New Implementation Process</h1>
            <a href="/" class="back-link">← Back to Home</a>
        </div>
        
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-text">Phase 1 of 4 - Foundation Setup</div>
        </div>
        
        <div class="phase-container">
            <div class="phase active">
                <div class="phase-number">Phase 1</div>
                <h3>Foundation</h3>
                <p>Core objects and configurations</p>
            </div>
            <div class="phase">
                <div class="phase-number">Phase 2</div>
                <h3>Products & Pricing</h3>
                <p>Product catalog and pricing setup</p>
            </div>
            <div class="phase">
                <div class="phase-number">Phase 3</div>
                <h3>Operations</h3>
                <p>Order and transaction management</p>
            </div>
            <div class="phase">
                <div class="phase-number">Phase 4</div>
                <h3>Finalization</h3>
                <p>Validation and go-live</p>
            </div>
        </div>
        
        <div class="instructions">
            <h4>📋 Phase 1: Foundation Setup</h4>
            <ul>
                <li>These objects must be configured first as they are dependencies for all other objects</li>
                <li>Complete each object in order before proceeding to the next phase</li>
                <li>Green indicates completed, yellow indicates in progress</li>
            </ul>
        </div>
        
        <div class="objects-grid">
            <div class="object-card" onclick="loadObject('Account')">
                <h4>Account</h4>
                <div class="object-status">Base customer records</div>
            </div>
            <div class="object-card" onclick="loadObject('Contact')">
                <h4>Contact</h4>
                <div class="object-status">Customer contacts</div>
            </div>
            <div class="object-card" onclick="loadObject('Legal_Entity')">
                <h4>Legal Entity</h4>
                <div class="object-status">Company legal entities</div>
            </div>
            <div class="object-card" onclick="loadObject('Tax_Treatment')">
                <h4>Tax Treatment</h4>
                <div class="object-status">Tax configurations</div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="btn btn-secondary" disabled>← Previous Phase</button>
            <button class="btn btn-primary" onclick="nextPhase()">Next Phase →</button>
        </div>
    </div>
    
    <script>
        function loadObject(objectName) {
            window.location.href = '/object-editor?object=' + objectName + '&phase=1';
        }
        
        function nextPhase() {
            // In a real implementation, this would validate completion and move to next phase
            alert('Moving to Phase 2: Products & Pricing');
        }
    </script>
</body>
</html>
"""

# HTML content for data management
DATA_MANAGEMENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud - Data Management</title>
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
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.2em;
        }
        .back-link {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .search-container {
            margin-bottom: 30px;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            transition: border-color 0.3s;
        }
        .search-box:focus {
            outline: none;
            border-color: #3498db;
        }
        .category-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }
        .category-tab {
            padding: 10px 20px;
            background-color: #f8f9fa;
            border: none;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        .category-tab:hover {
            background-color: #e9ecef;
        }
        .category-tab.active {
            background-color: #3498db;
            color: white;
        }
        .objects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .object-card {
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: white;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .object-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        .object-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .object-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }
        .object-count {
            background-color: #e0e0e0;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            color: #666;
        }
        .object-description {
            color: #666;
            margin-bottom: 15px;
        }
        .object-actions {
            display: flex;
            gap: 10px;
        }
        .btn-small {
            padding: 8px 16px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: white;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
            text-decoration: none;
            color: #333;
        }
        .btn-small:hover {
            background-color: #f8f9fa;
            border-color: #3498db;
            color: #3498db;
        }
        .btn-import {
            background-color: #3498db;
            color: white;
            border-color: #3498db;
        }
        .btn-import:hover {
            background-color: #2980b9;
        }
        .status-bar {
            margin-top: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .last-sync {
            color: #666;
        }
        .sync-button {
            background-color: #27ae60;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s;
        }
        .sync-button:hover {
            background-color: #219a52;
        }
        
        /* Sync Status Indicators */
        .sync-status-indicator {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-align: center;
            margin-top: 5px;
            min-width: 80px;
        }
        
        .sync-status-indicator[data-status="Synced"] {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .sync-status-indicator[data-status="Not Synced"] {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .sync-status-indicator[data-status="Partially Synced"] {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .sync-status-indicator[data-status="Upload Failed"] {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .sync-status-indicator[data-status="Modified"] {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Data Management</h1>
            <a href="/" class="back-link">← Back to Home</a>
        </div>
        
        <div class="search-container">
            <input type="text" class="search-box" placeholder="Search objects..." onkeyup="filterObjects(this.value)">
        </div>
        
        <div class="category-tabs">
            <button class="category-tab active" onclick="filterCategory('all')">All Objects</button>
            <button class="category-tab" onclick="filterCategory('products')">Products & Attributes</button>
            <button class="category-tab" onclick="filterCategory('pricing')">Pricing & Adjustments</button>
            <button class="category-tab" onclick="filterCategory('revenue')">Revenue & Tax</button>
        </div>
        
        <div class="objects-grid" id="objects-grid">
            <!-- Product Catalog Objects -->
            <div class="object-card" data-category="products" onclick="manageObject('ProductCatalog')">
                <div class="object-header">
                    <div class="object-title">Product Catalog</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product catalog definitions</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductCategory')">
                <div class="object-header">
                    <div class="object-title">Product Category</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product categorization structure</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" data-object="Product2" onclick="manageObject('Product2')">
                <div class="object-header">
                    <div class="object-title">Product</div>
                    <div class="object-count">0 records</div>
                    <div class="sync-status-indicator" data-status="Not Synced">Not Synced</div>
                </div>
                <div class="object-description">Product master records</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductCategoryProduct')">
                <div class="object-header">
                    <div class="object-title">Product Category Product</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product to category assignments</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" data-object="ProductSellingModel" onclick="manageObject('ProductSellingModel')">
                <div class="object-header">
                    <div class="object-title">Product Selling Model</div>
                    <div class="object-count">0 records</div>
                    <div class="sync-status-indicator" data-status="Not Synced">Not Synced</div>
                </div>
                <div class="object-description">Product selling configurations</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductComponentGroup')">
                <div class="object-header">
                    <div class="object-title">Product Component Group</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product component groupings</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductRelatedComponent')">
                <div class="object-header">
                    <div class="object-title">Product Related Component</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product component relationships</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductClassification')">
                <div class="object-header">
                    <div class="object-title">Product Classification</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product classification data</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <!-- Attribute Objects -->
            <div class="object-card" data-category="products" onclick="manageObject('AttributeDefinition')">
                <div class="object-header">
                    <div class="object-title">Attribute Definition</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product attribute definitions</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('AttributePicklist')">
                <div class="object-header">
                    <div class="object-title">Attribute Picklist</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Attribute picklist definitions</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('AttributePicklistValue')">
                <div class="object-header">
                    <div class="object-title">Attribute Picklist Value</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Picklist value options</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductAttributeDef')">
                <div class="object-header">
                    <div class="object-title">Product Attribute Definition</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product-specific attributes</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="products" onclick="manageObject('AttributeCategory')">
                <div class="object-header">
                    <div class="object-title">Attribute Category</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Attribute categorization</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <!-- Pricing Objects -->
            <div class="object-card" data-category="pricing" onclick="manageObject('Pricebook2')">
                <div class="object-header">
                    <div class="object-title">Price Book</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Price book definitions</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" data-object="PricebookEntry" onclick="manageObject('PricebookEntry')">
                <div class="object-header">
                    <div class="object-title">Price Book Entry</div>
                    <div class="object-count">0 records</div>
                    <div class="sync-status-indicator" data-status="Not Synced">Not Synced</div>
                </div>
                <div class="object-description">Product pricing entries</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('CostBook')">
                <div class="object-header">
                    <div class="object-title">Cost Book</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Cost book definitions</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('CostBookEntry')">
                <div class="object-header">
                    <div class="object-title">Cost Book Entry</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Product cost entries</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('PriceAdjustmentSchedule')">
                <div class="object-header">
                    <div class="object-title">Price Adjustment Schedule</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Price adjustment schedules</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('PriceAdjustmentTier')">
                <div class="object-header">
                    <div class="object-title">Price Adjustment Tier</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Tiered pricing adjustments</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('AttributeBasedAdjRule')">
                <div class="object-header">
                    <div class="object-title">Attribute Based Adjustment Rule</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Attribute-based pricing rules</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="pricing" onclick="manageObject('AttributeBasedAdj')">
                <div class="object-header">
                    <div class="object-title">Attribute Based Adjustment</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Attribute-based adjustments</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <!-- Billing & Tax Objects -->
            <div class="object-card" data-category="revenue" onclick="manageObject('BillingPolicy')">
                <div class="object-header">
                    <div class="object-title">Billing Policy</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Billing policy configurations</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="revenue" onclick="manageObject('BillingTreatment')">
                <div class="object-header">
                    <div class="object-title">Billing Treatment</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Billing treatment rules</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="revenue" onclick="manageObject('LegalEntity')">
                <div class="object-header">
                    <div class="object-title">Legal Entity</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Company legal entities</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="revenue" onclick="manageObject('TaxTreatment')">
                <div class="object-header">
                    <div class="object-title">Tax Treatment</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Tax treatment configurations</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="revenue" onclick="manageObject('TaxPolicy')">
                <div class="object-header">
                    <div class="object-title">Tax Policy</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Tax policy rules</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
            
            <div class="object-card" data-category="revenue" onclick="manageObject('TaxEngine')">
                <div class="object-header">
                    <div class="object-title">Tax Engine</div>
                    <div class="object-count">0 records</div>
                </div>
                <div class="object-description">Tax calculation engine</div>
                <div class="object-actions">
                    <button class="btn-small">View</button>
                    <button class="btn-small">Export</button>
                    <button class="btn-small btn-import">Import</button>
                </div>
            </div>
        </div>
        
        <div class="status-bar">
            <div class="last-sync">Last sync: 2 hours ago</div>
            <button class="sync-button" onclick="syncAll()">Sync All Objects</button>
        </div>
    </div>
    
    <script>
        function filterObjects(searchTerm) {
            // Implementation for search filtering
            console.log('Searching for:', searchTerm);
        }
        
        function filterCategory(category) {
            // Update active tab
            document.querySelectorAll('.category-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Filter objects
            document.querySelectorAll('.object-card').forEach(card => {
                if (category === 'all' || card.getAttribute('data-category') === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        function manageObject(objectName) {
            window.location.href = '/object-manager?object=' + objectName;
        }
        
        let syncSessionId = null;
        let progressPollInterval = null;
        
        function syncAll() {
            if (!confirm('This will sync all objects from Salesforce to your local workbook. A backup will be created. Continue?')) {
                return;
            }
            
            // Show progress modal
            showSyncProgress();
            
            // Start sync
            fetch('/api/sync', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    org: 'fortradp2',
                    action: 'sync_all'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.session_id) {
                    syncSessionId = data.session_id;
                    // Start polling for progress
                    pollSyncProgress();
                } else {
                    hideSyncProgress();
                    alert('Failed to start sync: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                hideSyncProgress();
                alert('Error starting sync: ' + error.message);
            });
        }
        
        function pollSyncProgress() {
            progressPollInterval = setInterval(() => {
                fetch(`/api/sync/progress/${syncSessionId}`)
                    .then(response => response.json())
                    .then(data => {
                        updateSyncProgress(data);
                        
                        if (data.status === 'completed') {
                            clearInterval(progressPollInterval);
                            hideSyncProgress();
                            
                            const result = data.result;
                            if (result.success) {
                                alert(`Sync completed successfully!\\n\\nSynced: ${result.success_count} objects\\nTotal records: ${result.total_records}\\nBackup saved: ${result.backup_path}`);
                                location.reload();
                            } else {
                                alert(`Sync completed with errors:\\n\\nSuccessful: ${result.success_count}\\nErrors: ${result.error_count}\\nTotal records: ${result.total_records}`);
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error polling progress:', error);
                    });
            }, 1000); // Poll every second
        }
        
        function updateSyncProgress(data) {
            const progressBar = document.getElementById('sync-progress-bar');
            const statusText = document.getElementById('sync-status');
            const currentObjectEl = document.getElementById('sync-current-object');
            const objectListEl = document.getElementById('sync-object-list');
            
            if (progressBar && data.percent !== undefined) {
                progressBar.style.width = data.percent + '%';
            }
            
            if (statusText) {
                statusText.textContent = data.message || 'Processing...';
            }
            
            if (currentObjectEl && data.current_object) {
                currentObjectEl.textContent = `Current: ${data.current_object}`;
            }
            
            if (objectListEl && data.completed !== undefined && data.total) {
                objectListEl.textContent = `Progress: ${data.completed} of ${data.total} objects`;
            }
        }
        
        function showSyncProgress() {
            const overlay = document.createElement('div');
            overlay.id = 'sync-overlay';
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999';
            
            const progressBox = document.createElement('div');
            progressBox.style.cssText = 'background:white;padding:40px;border-radius:10px;min-width:500px;box-shadow:0 4px 20px rgba(0,0,0,0.3)';
            progressBox.innerHTML = `
                <h2 style="margin-top:0;color:#2c3e50">🔄 Syncing with Salesforce</h2>
                <div style="margin:20px 0">
                    <div style="border:2px solid #e0e0e0;height:30px;border-radius:15px;overflow:hidden;background:#f5f5f5">
                        <div id="sync-progress-bar" style="background:linear-gradient(90deg, #3498db, #2980b9);height:100%;width:0%;border-radius:15px;transition:width 0.5s ease"></div>
                    </div>
                </div>
                <div style="margin:20px 0;color:#666">
                    <p id="sync-status" style="font-size:1.1em;margin:10px 0">Initializing sync...</p>
                    <p id="sync-current-object" style="font-weight:bold;color:#3498db;margin:10px 0"></p>
                    <p id="sync-object-list" style="font-size:0.9em;margin:10px 0"></p>
                </div>
                <div style="margin-top:30px;padding-top:20px;border-top:1px solid #e0e0e0">
                    <h4 style="margin:10px 0">Objects to Sync:</h4>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;font-size:0.85em;color:#666">
                        <div>• Product Catalog</div>
                        <div>• Product Category</div>
                        <div>• Products</div>
                        <div>• Price Books</div>
                        <div>• Attributes</div>
                        <div>• Tax & Billing</div>
                        <div>• Legal Entities</div>
                        <div>• And more...</div>
                    </div>
                </div>
            `;
            
            overlay.appendChild(progressBox);
            document.body.appendChild(overlay);
        }
        
        function hideSyncProgress() {
            if (progressPollInterval) {
                clearInterval(progressPollInterval);
                progressPollInterval = null;
            }
            
            const overlay = document.getElementById('sync-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    </script>
</body>
</html>
"""

# HTML content for object editor
# HTML content for sync page
SYNC_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud - Sync Manager</title>
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
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2em;
        }
        .back-link {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .sync-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
            margin-left: 10px;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background-color: #2980b9;
        }
        .btn-success {
            background-color: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background-color: #219a52;
        }
        .btn-secondary {
            background-color: #95a5a6;
            color: white;
        }
        .btn-secondary:hover {
            background-color: #7f8c8d;
        }
        .objects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .object-card {
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background-color: #fff;
            transition: all 0.3s;
        }
        .object-card:hover {
            border-color: #3498db;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .object-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        .object-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .object-checkbox {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        .object-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }
        .sync-status-indicator {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-align: center;
            min-width: 80px;
        }
        .sync-status-indicator[data-status="Synced"] {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .sync-status-indicator[data-status="Not Synced"] {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .sync-status-indicator[data-status="Partially Synced"] {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .sync-status-indicator[data-status="Upload Failed"] {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .sync-status-indicator[data-status="Modified"] {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .last-sync {
            font-size: 0.9em;
            color: #666;
        }
        .progress-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        .progress-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            min-width: 500px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2980b9);
            border-radius: 10px;
            transition: width 0.5s ease;
            width: 0%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Sync Manager</h1>
            <a href="/" class="back-link">← Back to Dashboard</a>
        </div>
        
        <div class="sync-controls">
            <div>
                <button class="btn btn-secondary" onclick="selectAll()">Select All</button>
                <button class="btn btn-secondary" onclick="selectNone()">Select None</button>
                <button class="btn btn-primary" onclick="syncSelected()">Sync Selected</button>
            </div>
            <div>
                <span id="selected-count">0 objects selected</span>
            </div>
        </div>
        
        <div class="objects-grid" id="objects-grid">
            <!-- Objects will be loaded here dynamically -->
        </div>
    </div>
    
    <div id="progress-overlay" class="progress-overlay">
        <div class="progress-box">
            <h3>🔄 Syncing Objects</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <p id="progress-text">Initializing...</p>
            <p id="current-object"></p>
        </div>
    </div>
    
    <script>
        const objectCategories = [
            {
                category: 'Product Configuration',
                objects: [
                    {name: 'ProductCatalog', title: 'Product Catalog', description: 'Product catalog definitions'},
                    {name: 'ProductCategory', title: 'Product Category', description: 'Product categorization structure'},
                    {name: 'Product2', title: 'Product', description: 'Product master records'},
                    {name: 'ProductSellingModel', title: 'Product Selling Model', description: 'Product selling configurations'},
                    {name: 'ProductSellingModelOption', title: 'Product Selling Model Option', description: 'Product selling model options'},
                    {name: 'ProductClassification', title: 'Product Classification', description: 'Product classification data'}
                ]
            },
            {
                category: 'Pricing & Attributes',
                objects: [
                    {name: 'Pricebook2', title: 'Price Book', description: 'Price book definitions'},
                    {name: 'PricebookEntry', title: 'Price Book Entry', description: 'Product pricing entries'},
                    {name: 'AttributeDefinition', title: 'Attribute Definition', description: 'Product attribute definitions'},
                    {name: 'AttributePicklist', title: 'Attribute Picklist', description: 'Attribute picklist definitions'},
                    {name: 'ProductAttributeDef', title: 'Product Attribute Definition', description: 'Product-specific attributes'}
                ]
            },
            {
                category: 'Financial Configuration',
                objects: [
                    {name: 'LegalEntity', title: 'Legal Entity', description: 'Company legal entities'},
                    {name: 'TaxTreatment', title: 'Tax Treatment', description: 'Tax treatment configurations'},
                    {name: 'BillingPolicy', title: 'Billing Policy', description: 'Billing policy configurations'}
                ]
            },
            {
                category: 'Transactions',
                objects: [
                    {name: 'Order', title: 'Order', description: 'Sales orders and transactions'},
                    {name: 'OrderItem', title: 'Order Item', description: 'Line items in orders'},
                    {name: 'Asset', title: 'Asset', description: 'Customer assets and subscriptions'},
                    {name: 'AssetAction', title: 'Asset Action', description: 'Actions performed on assets'},
                    {name: 'AssetActionSource', title: 'Asset Action Source', description: 'Source references for asset actions'},
                    {name: 'Contract', title: 'Contract', description: 'Customer contracts'}
                ]
            },
            {
                category: 'Fulfillment Configuration',
                objects: [
                    {name: 'Location', title: 'Location', description: 'Physical locations and warehouses'},
                    {name: 'AssociatedLocation', title: 'Associated Location', description: 'Location relationships'},
                    {name: 'OrderDeliveryMethod', title: 'Order Delivery Method', description: 'Available delivery methods'}
                ]
            },
            {
                category: 'Fulfillment Plans',
                objects: [
                    {name: 'WorkPlanTemplate', title: 'Work Plan Template', description: 'Reusable fulfillment workflows'},
                    {name: 'WorkPlanTemplateEntry', title: 'Work Plan Template Entry', description: 'Steps in fulfillment workflows'},
                    {name: 'WorkPlan', title: 'Work Plan', description: 'Active fulfillment plans'}
                ]
            },
            {
                category: 'Fulfillment Operations',
                objects: [
                    {name: 'FulfillmentOrder', title: 'Fulfillment Order', description: 'Order fulfillment records'},
                    {name: 'FulfillmentOrderLineItem', title: 'Fulfillment Order Line Item', description: 'Items being fulfilled'},
                    {name: 'OrderDeliveryGroup', title: 'Order Delivery Group', description: 'Delivery groupings'},
                    {name: 'Shipment', title: 'Shipment', description: 'Shipment tracking records'},
                    {name: 'ShipmentItem', title: 'Shipment Item', description: 'Items in shipments'}
                ]
            },
            {
                category: 'Fulfillment Workflow',
                objects: [
                    {name: 'FulfillmentStepDefinitionGroup', title: 'Fulfillment Step Definition Group', description: 'Groups of fulfillment steps'},
                    {name: 'FulfillmentStepDefinition', title: 'Fulfillment Step Definition', description: 'Fulfillment step templates'},
                    {name: 'FulfillmentStep', title: 'Fulfillment Step', description: 'Active fulfillment steps'},
                    {name: 'FulfillmentAsset', title: 'Fulfillment Asset', description: 'Assets tracked during fulfillment'},
                    {name: 'FulfillmentAssetAttribute', title: 'Fulfillment Asset Attribute', description: 'Fulfillment asset metadata'},
                    {name: 'FulfillmentOrderItemAdjustment', title: 'Fulfillment Order Item Adjustment', description: 'Price adjustments for fulfillment'},
                    {name: 'FulfillmentOrderItemTax', title: 'Fulfillment Order Item Tax', description: 'Tax calculations for fulfillment'}
                ]
            }
        ];
        
        // Flatten objects for backward compatibility
        const objects = objectCategories.flatMap(cat => cat.objects);
        
        let syncStatuses = {};
        
        function loadObjects() {
            const grid = document.getElementById('objects-grid');
            grid.innerHTML = objectCategories.map((category, catIndex) => `
                <div class="category-section">
                    <div class="category-header" onclick="toggleCategory(event, ${catIndex})">
                        <div class="category-title">
                            <input type="checkbox" class="category-checkbox" 
                                data-category="${catIndex}" 
                                onclick="toggleCategorySelection(event, ${catIndex})"
                                onchange="updateSelectedCount()">
                            <span>${category.category}</span>
                            <span class="category-count">(${category.objects.length} objects)</span>
                        </div>
                    </div>
                    <div class="category-objects" id="category-objects-${catIndex}">
                        ${category.objects.map(obj => `
                            <div class="object-card">
                                <div class="object-header">
                                    <div class="object-title">${obj.title}</div>
                                    <input type="checkbox" class="object-checkbox" 
                                        data-object="${obj.name}" 
                                        data-category="${catIndex}"
                                        onchange="updateObjectSelection(this); updateSelectedCount()">
                                </div>
                                <div class="object-description">${obj.description}</div>
                                <div class="object-status">
                                    <div class="sync-status-indicator" data-status="Not Synced">Not Synced</div>
                                    <div class="last-sync" id="last-sync-${obj.name}">Never synced</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
            loadSyncStatus();
        }
        
        function loadSyncStatus() {
            fetch('/api/sync-status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        syncStatuses = data.status.objects;
                        updateSyncStatusIndicators();
                    }
                })
                .catch(error => console.error('Error loading sync status:', error));
        }
        
        function updateSyncStatusIndicators() {
            objects.forEach(obj => {
                const status = syncStatuses[obj.name];
                if (status) {
                    const indicator = document.querySelector(`[data-object="${obj.name}"]`).closest('.object-card').querySelector('.sync-status-indicator');
                    const lastSyncEl = document.getElementById(`last-sync-${obj.name}`);
                    
                    indicator.textContent = status.status || 'Not Synced';
                    indicator.setAttribute('data-status', status.status || 'Not Synced');
                    
                    if (status.last_sync) {
                        const lastSync = new Date(status.last_sync);
                        lastSyncEl.textContent = `Last sync: ${lastSync.toLocaleString()}`;
                    }
                }
            });
        }
        
        function selectAll() {
            // Check all object checkboxes
            document.querySelectorAll('.object-checkbox').forEach(cb => {
                cb.checked = true;
            });
            // Check all category checkboxes
            document.querySelectorAll('.category-checkbox').forEach(cb => {
                cb.checked = true;
                cb.indeterminate = false;
            });
            updateSelectedCount();
        }
        
        function selectNone() {
            // Uncheck all object checkboxes
            document.querySelectorAll('.object-checkbox').forEach(cb => {
                cb.checked = false;
            });
            // Uncheck all category checkboxes
            document.querySelectorAll('.category-checkbox').forEach(cb => {
                cb.checked = false;
                cb.indeterminate = false;
            });
            updateSelectedCount();
        }
        
        function toggleCategory(event, categoryIndex) {
            // Prevent checkbox from being triggered when clicking on header
            if (event.target.type !== 'checkbox') {
                const categoryObjects = document.getElementById(`category-objects-${categoryIndex}`);
                // This could be used to collapse/expand categories if desired
            }
        }
        
        function toggleCategorySelection(event, categoryIndex) {
            event.stopPropagation();
            const categoryCheckbox = event.target;
            const isChecked = categoryCheckbox.checked;
            
            // Get all object checkboxes in this category
            const objectCheckboxes = document.querySelectorAll(`#category-objects-${categoryIndex} .object-checkbox`);
            
            // Set all object checkboxes to match category checkbox state
            objectCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateSelectedCount();
        }
        
        function updateObjectSelection(objectCheckbox) {
            const categoryIndex = objectCheckbox.getAttribute('data-category');
            const categoryCheckbox = document.querySelector(`.category-checkbox[data-category="${categoryIndex}"]`);
            
            // Get all object checkboxes in this category
            const objectCheckboxes = document.querySelectorAll(`#category-objects-${categoryIndex} .object-checkbox`);
            const checkedCount = Array.from(objectCheckboxes).filter(cb => cb.checked).length;
            
            // Update category checkbox state
            if (checkedCount === 0) {
                categoryCheckbox.checked = false;
                categoryCheckbox.indeterminate = false;
            } else if (checkedCount === objectCheckboxes.length) {
                categoryCheckbox.checked = true;
                categoryCheckbox.indeterminate = false;
            } else {
                categoryCheckbox.checked = false;
                categoryCheckbox.indeterminate = true;
            }
        }
        
        function updateSelectedCount() {
            const selected = document.querySelectorAll('.object-checkbox:checked').length;
            document.getElementById('selected-count').textContent = `${selected} objects selected`;
        }
        
        function syncSelected() {
            const selectedObjects = Array.from(document.querySelectorAll('.object-checkbox:checked'))
                .map(cb => cb.getAttribute('data-object'));
            
            if (selectedObjects.length === 0) {
                alert('Please select at least one object to sync.');
                return;
            }
            
            if (!confirm(`Sync ${selectedObjects.length} selected objects?`)) {
                return;
            }
            
            startSync(selectedObjects);
        }
        
        function startSync(objectsToSync) {
            showProgress();
            updateProgress({percent: 10, current_object: 'Starting sync...'});
            
            fetch('/api/sync', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    objects: objectsToSync
                })
            })
            .then(response => response.json())
            .then(data => {
                hideProgress();
                
                // Always uncheck successfully synced objects, regardless of overall success
                let successfulObjects = [];
                if (data.synced && data.synced.length > 0) {
                    successfulObjects = data.synced.map(s => s.object);
                    successfulObjects.forEach(objName => {
                        const checkbox = document.querySelector(`[data-object="${objName}"]`);
                        if (checkbox) {
                            checkbox.checked = false;
                            console.log(`Unchecked checkbox for ${objName}`);
                            // Update the category checkbox state
                            updateObjectSelection(checkbox);
                        }
                    });
                }
                
                updateSelectedCount();
                loadSyncStatus();
                
                // Show appropriate message based on results
                if (data.success) {
                    let message = 'Sync completed successfully!\n\n';
                    if (data.synced && data.synced.length > 0) {
                        message += `✅ Successfully synced: ${data.synced.map(s => s.object).join(', ')}\n`;
                    }
                    if (data.failed && data.failed.length > 0) {
                        message += `❌ Failed to sync: ${data.failed.map(f => f.object).join(', ')}\n`;
                    }
                    alert(message);
                } else {
                    let errorMessage = 'Sync operation completed with some issues:\n\n';
                    if (data.synced && data.synced.length > 0) {
                        errorMessage += `✅ Successfully synced: ${data.synced.map(s => s.object).join(', ')}\n\n`;
                    }
                    if (data.failed && data.failed.length > 0) {
                        errorMessage += `❌ Failed to sync:\n${data.failed.map(f => `• ${f.object}: ${f.error}`).join('\n')}`;
                    }
                    if (data.error) {
                        errorMessage += `\n\nError: ${data.error}`;
                    }
                    alert(errorMessage);
                }
            })
            .catch(error => {
                hideProgress();
                alert('Error starting sync: ' + error);
            });
        }
        
        function updateProgress(data) {
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            const currentObject = document.getElementById('current-object');
            
            if (data.percent !== undefined) {
                progressFill.style.width = data.percent + '%';
                progressText.textContent = `${data.percent}% Complete`;
            }
            
            if (data.current_object) {
                currentObject.textContent = `Syncing: ${data.current_object}`;
            }
        }
        
        function showProgress() {
            document.getElementById('progress-overlay').style.display = 'flex';
        }
        
        function hideProgress() {
            document.getElementById('progress-overlay').style.display = 'none';
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadObjects();
        });
    </script>
</body>
</html>
"""

OBJECT_EDITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revenue Cloud - Object Editor</title>
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
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2em;
        }
        .back-link {
            color: #3498db;
            text-decoration: none;
            font-size: 1.1em;
        }
        .back-link:hover {
            text-decoration: underline;
        }
        .editor-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .editor-section h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s;
        }
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background-color: #2980b9;
        }
        .btn-success {
            background-color: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background-color: #219a52;
        }
        .btn-secondary {
            background-color: #95a5a6;
            color: white;
        }
        .btn-secondary:hover {
            background-color: #7f8c8d;
        }
        .file-upload {
            margin: 20px 0;
            padding: 20px;
            border: 2px dashed #3498db;
            border-radius: 8px;
            text-align: center;
            background-color: #f0f8ff;
        }
        .file-upload input[type="file"] {
            margin: 10px 0;
        }
        .status-message {
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            display: none;
        }
        .status-message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status-message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status-message.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .field-mapping {
            margin: 20px 0;
        }
        .field-mapping table {
            width: 100%;
            border-collapse: collapse;
        }
        .field-mapping th, .field-mapping td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }
        .field-mapping th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .progress-indicator {
            margin: 20px 0;
            display: none;
        }
        .progress-bar {
            background-color: #e0e0e0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-fill {
            background-color: #3498db;
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        .log-output {
            background-color: #2c3e50;
            color: #fff;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            display: none;
            margin-top: 20px;
        }
        .category-section {
            margin-bottom: 30px;
        }
        .category-header {
            background-color: #ecf0f1;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: all 0.3s;
        }
        .category-header:hover {
            background-color: #d5dbdb;
        }
        .category-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .category-checkbox {
            width: 22px;
            height: 22px;
            cursor: pointer;
        }
        .category-count {
            font-size: 0.9em;
            color: #7f8c8d;
            font-weight: normal;
        }
        .category-objects {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📝 Configure {{object_name}}</h1>
            <a href="/new-implementation" class="back-link">← Back to Implementation</a>
        </div>
        
        <div class="editor-section">
            <h3>Object Information</h3>
            <p><strong>Object:</strong> {{object_name}}</p>
            <p><strong>Phase:</strong> {{phase}} - Foundation Setup</p>
            <p><strong>Status:</strong> <span id="object-status">Not Started</span></p>
        </div>
        
        <div class="editor-section">
            <h3>Data Upload Options</h3>
            
            <div class="action-buttons">
                <button class="btn btn-primary" onclick="useTemplate()">
                    📋 Use Template Data
                </button>
                <button class="btn btn-secondary" onclick="showUpload()">
                    📁 Upload Custom File
                </button>
                <button class="btn btn-success" onclick="executeUpload()">
                    🚀 Execute Upload
                </button>
            </div>
            
            <div id="template-info" class="status-message info">
                Using data from: Revenue_Cloud_Complete_Upload_Template.xlsx
            </div>
            
            <div id="file-upload-section" class="file-upload" style="display: none;">
                <h4>Upload Custom Data File</h4>
                <p>Select a CSV or Excel file with {{object_name}} data</p>
                <input type="file" id="custom-file" accept=".csv,.xlsx,.xls">
            </div>
        </div>
        
        <div class="editor-section">
            <h3>Field Mapping</h3>
            <div class="field-mapping">
                <table>
                    <thead>
                        <tr>
                            <th>Excel Column</th>
                            <th>Salesforce Field</th>
                            <th>Required</th>
                        </tr>
                    </thead>
                    <tbody id="field-mapping-table">
                        <!-- Field mappings will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="progress-section" class="progress-indicator">
            <h4>Upload Progress</h4>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <p id="progress-text">0% Complete</p>
        </div>
        
        <div id="status-messages"></div>
        
        <div id="log-output" class="log-output"></div>
    </div>
    
    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const objectName = urlParams.get('object');
        const phase = urlParams.get('phase');
        
        // Load field mappings based on object
        window.onload = function() {
            loadFieldMappings();
        };
        
        function loadFieldMappings() {
            // Simulate loading field mappings
            const mappings = getFieldMappingsForObject(objectName);
            const tbody = document.getElementById('field-mapping-table');
            tbody.innerHTML = mappings.map(m => `
                <tr>
                    <td>${m.excelColumn}</td>
                    <td>${m.salesforceField}</td>
                    <td>${m.required ? '✓' : ''}</td>
                </tr>
            `).join('');
        }
        
        function getFieldMappingsForObject(obj) {
            const mappings = {
                'Account': [
                    {excelColumn: 'Account Name', salesforceField: 'Name', required: true},
                    {excelColumn: 'Account Number', salesforceField: 'AccountNumber', required: false},
                    {excelColumn: 'Type', salesforceField: 'Type', required: true},
                    {excelColumn: 'Industry', salesforceField: 'Industry', required: false}
                ],
                'Contact': [
                    {excelColumn: 'First Name', salesforceField: 'FirstName', required: true},
                    {excelColumn: 'Last Name', salesforceField: 'LastName', required: true},
                    {excelColumn: 'Email', salesforceField: 'Email', required: true},
                    {excelColumn: 'Account Name', salesforceField: 'AccountId', required: true}
                ],
                'Legal_Entity': [
                    {excelColumn: 'Legal Entity Name', salesforceField: 'Name', required: true},
                    {excelColumn: 'Entity Type', salesforceField: 'Type', required: true},
                    {excelColumn: 'Tax ID', salesforceField: 'TaxId', required: false}
                ],
                'Tax_Treatment': [
                    {excelColumn: 'Tax Treatment Name', salesforceField: 'Name', required: true},
                    {excelColumn: 'Tax Rate', salesforceField: 'TaxRate', required: true},
                    {excelColumn: 'Active', salesforceField: 'IsActive', required: true}
                ]
            };
            return mappings[obj] || [];
        }
        
        function useTemplate() {
            document.getElementById('template-info').style.display = 'block';
            document.getElementById('file-upload-section').style.display = 'none';
        }
        
        function showUpload() {
            document.getElementById('template-info').style.display = 'none';
            document.getElementById('file-upload-section').style.display = 'block';
        }
        
        function executeUpload() {
            // Show progress
            document.getElementById('progress-section').style.display = 'block';
            document.getElementById('log-output').style.display = 'block';
            
            // Start the upload process
            const logOutput = document.getElementById('log-output');
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            
            logOutput.innerHTML = 'Starting upload process for ' + objectName + '...<br>';
            
            // Make the actual API call to execute the upload
            fetch('/api/upload', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    object: objectName,
                    useTemplate: true,
                    org: 'fortradp2'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('Upload completed successfully!', 'success');
                    progressFill.style.width = '100%';
                    progressText.textContent = '100% Complete';
                } else {
                    showStatus('Upload failed: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showStatus('Error: ' + error.message, 'error');
            });
            
            // Simulate progress updates
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                if (progress <= 90) {
                    progressFill.style.width = progress + '%';
                    progressText.textContent = progress + '% Complete';
                    logOutput.innerHTML += `Processing batch ${progress/10} of 10...<br>`;
                    logOutput.scrollTop = logOutput.scrollHeight;
                } else {
                    clearInterval(interval);
                }
            }, 500);
        }
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'status-message ' + type;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';
            statusDiv.appendChild(messageDiv);
        }
        
        // Load sync status for objects
        function loadSyncStatus() {
            fetch('/api/sync-status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateSyncStatusIndicators(data.status.objects);
                        console.log('Sync status loaded:', data.summary);
                    } else {
                        console.error('Failed to load sync status:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error loading sync status:', error);
                });
        }
        
        // Update sync status indicators on object cards
        function updateSyncStatusIndicators(objects) {
            const objectCards = document.querySelectorAll('.object-card[data-object]');
            
            objectCards.forEach(card => {
                const objectName = card.getAttribute('data-object');
                const indicator = card.querySelector('.sync-status-indicator');
                
                if (indicator && objects[objectName]) {
                    const status = objects[objectName].status || 'Not Synced';
                    indicator.textContent = status;
                    indicator.setAttribute('data-status', status);
                }
            });
        }
        
        // Refresh sync status after upload
        function refreshSyncStatus() {
            setTimeout(() => {
                loadSyncStatus();
            }, 1000); // Wait 1 second for server to update
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadSyncStatus();
            
            // Refresh sync status every 30 seconds
            setInterval(loadSyncStatus, 30000);
        });
    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = MAIN_PAGE_HTML.replace('{{org}}', org).replace('{{workbook}}', workbook)
            self.wfile.write(html.encode())
        
        elif parsed_path.path == '/new-implementation':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(NEW_IMPLEMENTATION_HTML.encode())
        
        elif parsed_path.path == '/data-management':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Load template from file instead of hardcoded HTML
            templates_path = Path(__file__).parent.parent.parent / "templates"
            template_file = templates_path / "data-management.html"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                self.wfile.write(template_content.encode())
            else:
                self.wfile.write(DATA_MANAGEMENT_HTML.encode())
        
        elif parsed_path.path == '/object-editor':
            query_params = parse_qs(parsed_path.query)
            object_name = query_params.get('object', ['Unknown'])[0]
            phase = query_params.get('phase', ['1'])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = OBJECT_EDITOR_HTML.replace('{{object_name}}', object_name).replace('{{phase}}', phase)
            self.wfile.write(html.encode())
        
        elif parsed_path.path == '/api/session':
            # Return current session/connection information
            response = {
                'success': True,
                'active_connection': {
                    'id': 'fortradp2',
                    'name': 'fortradp2',
                    'username': org,
                    'instance_url': 'https://fortradp2.my.salesforce.com'
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/api/objects/counts':
            # Return object record counts from the workbook
            response = {
                'success': True,
                'counts': {}
            }
            
            try:
                import pandas as pd
                xl = pd.ExcelFile(workbook)
                
                # Map of object names to sheet names
                sheet_mapping = {
                    'LegalEntity': '02_LegalEntity',
                    'TaxEngine': '03_TaxEngine',
                    'TaxPolicy': '04_TaxPolicy',
                    'TaxTreatment': '05_TaxTreatment',
                    'CostBook': '01_CostBook',
                    'BillingPolicy': '06_BillingPolicy',
                    'BillingTreatment': '07_BillingTreatment',
                    'ProductCatalog': '11_ProductCatalog',
                    'Product2': '13_Product2',
                    # Add more mappings as needed
                }
                
                for obj_name, sheet_name in sheet_mapping.items():
                    if sheet_name in xl.sheet_names:
                        df = pd.read_excel(xl, sheet_name=sheet_name)
                        response['counts'][obj_name] = len(df)
                    else:
                        response['counts'][obj_name] = 0
                        
            except Exception as e:
                # If pandas is not available or error reading, return empty counts
                pass
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/api/workbook/view':
            # View workbook data for a specific object
            query_params = parse_qs(parsed_path.query)
            object_name = query_params.get('object', [''])[0]
            
            if not object_name:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'No object specified'}).encode())
                return
            
            try:
                import pandas as pd
                
                # Object to sheet mapping - corrected based on actual sheet names
                sheet_mapping = {
                    'LegalEntity': '02_LegalEntity',
                    'TaxEngine': '03_TaxEngine',
                    'TaxPolicy': '04_TaxPolicy',
                    'TaxTreatment': '05_TaxTreatment',
                    'CostBook': '01_CostBook',
                    'BillingPolicy': '06_BillingPolicy',
                    'BillingTreatment': '07_BillingTreatment',
                    'ProductCatalog': '11_ProductCatalog',
                    'ProductCategory': '12_ProductCategory',
                    'ProductClassification': '08_ProductClassification',
                    'Product2': '13_Product2',
                    'ProductSellingModel': '15_ProductSellingModel',
                    'ProductSellingModelOption': '16_ProductSellingModelOption',  # May not exist
                    'ProductCategoryProduct': '26_ProductCategoryProduct',
                    'ProductComponentGroup': '14_ProductComponentGroup',
                    'ProductRelatedComponent': '25_ProductRelatedComponent',
                    'AttributeDefinition': '09_AttributeDefinition',
                    'AttributeCategory': '10_AttributeCategory',
                    'AttributePicklist': '14_AttributePicklist',
                    'AttributePicklistValue': '18_AttributePicklistValue',
                    'ProductAttributeDefinition': '17_ProductAttributeDef',
                    'Pricebook2': '19_Pricebook2',
                    'PricebookEntry': '20_PricebookEntry',
                    'CostBookEntry': '15_CostBookEntry',
                    'PriceAdjustmentSchedule': '21_PriceAdjustmentSchedule',
                    'PriceAdjustmentTier': '22_PriceAdjustmentTier',
                    'AttributeBasedAdjRule': '23_AttributeBasedAdjRule',
                    'AttributeBasedAdjustment': '24_AttributeBasedAdj',
                    'Order': '29_Order',  # May not exist
                    'OrderItem': '30_OrderItem',  # May not exist
                    'Asset': '31_Asset',  # May not exist
                    'AssetAction': '32_AssetAction',  # May not exist
                    'AssetActionSource': '33_AssetActionSource',  # May not exist
                    'Contract': '34_Contract'  # May not exist
                }
                
                # Get sheet name for the object
                sheet_name = sheet_mapping.get(object_name)
                
                if not sheet_name:
                    # If no mapping found, return empty data with message
                    response = {
                        'success': True,
                        'data': [],
                        'workbook': workbook,
                        'sheet': None,
                        'message': f'No sheet mapping found for {object_name}'
                    }
                else:
                    # Try to read the sheet from the workbook
                    try:
                        # Check if workbook exists
                        if not os.path.exists(workbook):
                            response = {
                                'success': False,
                                'error': f'Workbook not found: {workbook}'
                            }
                        else:
                            # Read the Excel sheet
                            df = pd.read_excel(workbook, sheet_name=sheet_name)
                            
                            # Remove asterisks from column names if present
                            df.columns = df.columns.str.replace('*', '', regex=False)
                            
                            # Convert DataFrame to list of dictionaries
                            records = df.to_dict('records')
                            
                            # Log columns for debugging
                            print(f"[VIEW] Object: {object_name}, Columns: {list(df.columns)}")
                            if records and len(records) > 0:
                                print(f"[VIEW] First record keys: {list(records[0].keys())}")
                                # Check if Id field exists
                                has_id = 'Id' in records[0] or 'id' in records[0]
                                print(f"[VIEW] Has Id field: {has_id}")
                            
                            # Convert NaN values to None for proper JSON serialization
                            for record in records:
                                for key, value in record.items():
                                    if pd.isna(value):
                                        record[key] = None
                                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                                        record[key] = str(value)
                            
                            response = {
                                'success': True,
                                'data': records,
                                'workbook': workbook,
                                'sheet': sheet_name,
                                'message': f'Loaded {len(records)} records from {sheet_name}'
                            }
                    except ValueError as e:
                        # Sheet doesn't exist
                        response = {
                            'success': True,
                            'data': [],
                            'workbook': workbook,
                            'sheet': None,
                            'message': f'Sheet {sheet_name} not found in workbook'
                        }
                    except Exception as e:
                        response = {
                            'success': False,
                            'error': f'Error reading sheet: {str(e)}'
                        }
                
            except ImportError:
                response = {
                    'success': False,
                    'error': 'pandas is not installed. Run: pip install pandas openpyxl'
                }
            except Exception as e:
                response = {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/api/workbook/open':
            # Open workbook in system's default application
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': 'Not implemented'}).encode())
        
        elif parsed_path.path.startswith('/api/sync/progress/'):
            # Get progress for a sync session
            session_id = parsed_path.path.split('/')[-1]
            progress_file = f"/tmp/sync_progress_{session_id}.json"
            result_file = f"/tmp/sync_result_{session_id}.json"
            
            response = {}
            
            # Check if sync is complete
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result = json.load(f)
                response = {
                    'status': 'completed',
                    'result': result
                }
                # Clean up files
                try:
                    os.remove(progress_file)
                    os.remove(result_file)
                except:
                    pass
            elif os.path.exists(progress_file):
                # Read progress
                with open(progress_file, 'r') as f:
                    response = json.load(f)
            else:
                response = {
                    'status': 'initializing',
                    'message': 'Preparing sync...'
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        if self.path == '/api/upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            object_name = data.get('object')
            use_template = data.get('useTemplate', True)
            org = data.get('org', 'fortradp2')
            
            # Execute the actual upload command
            uploader_script = str(PROJECT_ROOT / "src/data-processing/revenue_cloud_data_uploader.py")
            if use_template:
                cmd = f"python3 {uploader_script} --org {org} --object {object_name} --data-file {workbook}"
            else:
                # Handle custom file upload
                cmd = f"python3 {uploader_script} --org {org} --object {object_name}"
            
            try:
                # Run the command
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                
                response = {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None
                }
            except Exception as e:
                response = {
                    'success': False,
                    'error': str(e)
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/sync':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            org = data.get('org', 'fortradp2')
            action = data.get('action', 'sync_all')
            
            # Generate unique session ID for this sync
            import uuid
            session_id = str(uuid.uuid4())
            progress_file = f"/tmp/sync_progress_{session_id}.json"
            result_file = f"/tmp/sync_result_{session_id}.json"
            
            # Start sync in background
            sync_script = str(PROJECT_ROOT / "src/data-processing/revenue_cloud_sync.py")
            cmd = [
                'python3', sync_script,
                '--org', org,
                '--workbook', workbook,
                '--output-json', result_file,
                '--progress-file', progress_file
            ]
            
            # Start process in background
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            response = {
                'success': True,
                'session_id': session_id,
                'message': 'Sync started'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/workbook/open':
            # Open workbook in system's default application
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            workbook_path = data.get('path', workbook)
            sheet_name = data.get('sheet', '')
            api_name = data.get('apiName', '')
            
            try:
                # Use subprocess to open the file with the default application
                
                if sys.platform == 'darwin':  # macOS
                    if sheet_name:
                        # Use AppleScript to open Excel at specific sheet
                        applescript = f'''
                        tell application "Microsoft Excel"
                            open "{workbook_path}"
                            activate
                            tell active workbook
                                try
                                    activate object worksheet "{sheet_name}"
                                on error
                                    -- Sheet not found, just open the workbook
                                end try
                            end tell
                        end tell
                        '''
                        subprocess.Popen(['osascript', '-e', applescript])
                    else:
                        subprocess.Popen(['open', workbook_path])
                elif sys.platform == 'win32':  # Windows
                    # On Windows, we can't easily open at a specific sheet
                    subprocess.Popen(['start', '', workbook_path], shell=True)
                else:  # Linux
                    subprocess.Popen(['xdg-open', workbook_path])
                
                response = {
                    'success': True,
                    'message': f'Opening {api_name} sheet in {os.path.basename(workbook_path)}'
                }
            except Exception as e:
                response = {
                    'success': False,
                    'error': f'Failed to open spreadsheet: {str(e)}'
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/objects/delete':
            # Delete records from Salesforce
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            object_name = data.get('objectName')
            record_ids = data.get('recordIds', [])
            cascade_delete = data.get('cascadeDelete', False)
            connection_alias = data.get('connectionAlias')
            
            try:
                print(f"[DELETE] Received delete request for {object_name} with {len(record_ids)} records")
                print(f"[DELETE] Record IDs: {record_ids}")
                print(f"[DELETE] Cascade delete: {cascade_delete}")
                
                # Validate record IDs
                valid_record_ids = [rid for rid in record_ids if rid and rid != 'undefined' and rid != 'null']
                if len(valid_record_ids) != len(record_ids):
                    print(f"[DELETE] Filtered out invalid IDs. Valid IDs: {valid_record_ids}")
                    
                if not valid_record_ids:
                    response = {
                        'success': False,
                        'errors': [{
                            'recordId': 'N/A',
                            'message': 'No valid record IDs provided',
                            'solution': 'Ensure records have been synced from Salesforce and have valid IDs'
                        }]
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                record_ids = valid_record_ids
                
                # Get connection alias from session if not provided
                if not connection_alias:
                    # Use the default org connection
                    connection_alias = 'fortradp2'
                    print(f"[DELETE] Using default connection: {connection_alias}")
                
                if not connection_alias:
                    response = {
                        'success': False,
                        'errors': [{'message': 'No active Salesforce connection. Please select a connection from the dropdown.'}]
                    }
                else:
                    deleted_count = 0
                    errors = []
                    
                    # Use Salesforce CLI command
                    CLI_COMMAND = 'sf'
                    
                    # Define object relationships for cascade delete
                    cascade_relationships = {
                        'ProductCatalog': [
                            {'object': 'ProductCategory', 'field': 'CatalogId', 'deleteFirst': True}
                        ],
                        'ProductCategory': [
                            {'object': 'ProductCategoryProduct', 'field': 'ProductCategoryId', 'deleteFirst': True}
                        ],
                        'Product2': [
                            {'object': 'ProductAttributeDefinition', 'field': 'ProductId', 'deleteFirst': True},
                            {'object': 'PricebookEntry', 'field': 'Product2Id', 'deleteFirst': True},
                            {'object': 'ProductCategoryProduct', 'field': 'ProductId', 'deleteFirst': True}
                        ],
                        'AttributeDefinition': [
                            {'object': 'ProductAttributeDefinition', 'field': 'AttributeDefinitionId', 'deleteFirst': True},
                            {'object': 'AttributePicklistValue', 'field': 'AttributeDefinitionId', 'deleteFirst': True}
                        ],
                        'AttributePicklist': [
                            {'object': 'AttributePicklistValue', 'field': 'AttributePicklistId', 'deleteFirst': True}
                        ],
                        'Pricebook2': [
                            {'object': 'PricebookEntry', 'field': 'Pricebook2Id', 'deleteFirst': True}
                        ],
                        'ProductClassification': [
                            {'object': 'Product2', 'field': 'ProductClassificationId', 'deleteFirst': True},
                            {'object': 'ProductClassificationAttr', 'field': 'ProductClassificationId', 'deleteFirst': True}
                        ]
                    }
                    
                    # If cascade delete is enabled, handle related records first
                    if cascade_delete and object_name in cascade_relationships:
                        print(f"[DELETE] Processing cascade delete for {object_name}")
                        cascade_errors = []
                        cascade_deleted = []
                        
                        # Track deletion order for potential rollback
                        deletion_log = []
                        
                        for rel in cascade_relationships[object_name]:
                            if not rel.get('deleteFirst', True):
                                continue
                                
                            rel_object = rel['object']
                            rel_field = rel['field']
                            
                            for record_id in valid_record_ids:
                                # Query for related records
                                query = f"SELECT Id FROM {rel_object} WHERE {rel_field} = '{record_id}'"
                                cmd = [
                                    CLI_COMMAND, 'data', 'query',
                                    '--query', query,
                                    '--target-org', connection_alias,
                                    '--json'
                                ]
                                
                                print(f"[DELETE] Checking related {rel_object} records")
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                                
                                if result.returncode == 0:
                                    try:
                                        data = json.loads(result.stdout)
                                        if 'result' in data and 'records' in data['result']:
                                            related_records = data['result']['records']
                                            
                                            # Delete each related record
                                            for related in related_records:
                                                related_id = related['Id']
                                                del_cmd = [
                                                    CLI_COMMAND, 'data', 'delete', 'record',
                                                    '--sobject', rel_object,
                                                    '--record-id', related_id,
                                                    '--target-org', connection_alias,
                                                    '--json'
                                                ]
                                                
                                                print(f"[DELETE] Deleting related {rel_object} record: {related_id}")
                                                del_result = subprocess.run(del_cmd, capture_output=True, text=True, timeout=30)
                                                
                                                if del_result.returncode == 0:
                                                    cascade_deleted.append({
                                                        'object': rel_object,
                                                        'recordId': related_id,
                                                        'parentId': record_id
                                                    })
                                                    deletion_log.append({
                                                        'timestamp': time.time(),
                                                        'object': rel_object,
                                                        'recordId': related_id,
                                                        'success': True
                                                    })
                                                else:
                                                    try:
                                                        error_data = json.loads(del_result.stdout)
                                                        error_msg = error_data.get('message', 'Unknown error')
                                                    except:
                                                        error_msg = del_result.stderr or 'Failed to delete related record'
                                                    
                                                    cascade_errors.append({
                                                        'object': rel_object,
                                                        'recordId': related_id,
                                                        'error': error_msg
                                                    })
                                                    
                                                    # If cascade delete fails, stop the process
                                                    print(f"[DELETE] Cascade delete failed for {rel_object} record {related_id}: {error_msg}")
                                                    print(f"[DELETE] Stopping cascade delete process to prevent partial deletion")
                                                    
                                                    # Add all parent records to errors to prevent their deletion
                                                    errors.append({
                                                        'recordId': record_id,
                                                        'message': f'Cascade delete failed: Could not delete related {rel_object} record ({related_id}). {error_msg}',
                                                        'solution': 'Fix the issue with the related record and try again, or delete it manually first.'
                                                    })
                                                    
                                                    # Skip remaining deletions for this parent record
                                                    break
                                    except:
                                        pass
                        
                        # Log cascade results
                        if cascade_deleted:
                            print(f"[DELETE] Cascade deleted {len(cascade_deleted)} related records")
                        if cascade_errors:
                            print(f"[DELETE] Failed to cascade delete {len(cascade_errors)} related records")
                            # Add cascade errors to main errors list
                            for ce in cascade_errors:
                                errors.append({
                                    'recordId': ce['recordId'],
                                    'message': f"Failed to delete related {ce['object']} record: {ce['error']}",
                                    'solution': 'Check permissions or try deleting this record manually'
                                })
                    
                    # Now proceed with main record deletion
                    # Skip records that had cascade delete failures
                    failed_parent_ids = set()
                    if cascade_delete and cascade_errors:
                        # Extract parent IDs from errors
                        for err in errors:
                            if 'Cascade delete failed' in err.get('message', ''):
                                failed_parent_ids.add(err['recordId'])
                    
                    for record_id in valid_record_ids:
                        # Skip if this record had cascade delete failures
                        if record_id in failed_parent_ids:
                            print(f"[DELETE] Skipping deletion of {record_id} due to cascade delete failures")
                            continue
                        try:
                            print(f"[DELETE] Deleting record {record_id} from {object_name}")
                            
                            # Delete the record using Salesforce CLI
                            cmd = [
                                CLI_COMMAND, 'data', 'delete', 'record',
                                '--sobject', object_name,
                                '--record-id', record_id,
                                '--target-org', connection_alias,
                                '--json'
                            ]
                            
                            print(f"[DELETE] Command: {' '.join(cmd)}")
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                            print(f"[DELETE] Return code: {result.returncode}")
                            print(f"[DELETE] STDOUT: {result.stdout[:200]}")
                            print(f"[DELETE] STDERR: {result.stderr[:200] if result.stderr else 'None'}")
                            
                            if result.returncode == 0:
                                deleted_count += 1
                            else:
                                # Parse error from CLI response
                                error_msg = 'Failed to delete record'
                                solution = ''
                                
                                try:
                                    error_data = json.loads(result.stdout)
                                    if 'message' in error_data:
                                        error_msg = error_data['message']
                                except:
                                    error_msg = result.stderr or result.stdout
                                
                                # Provide helpful error messages
                                if 'INSUFFICIENT_ACCESS' in error_msg:
                                    solution = 'Contact your Salesforce administrator for delete permissions on this object.'
                                elif 'ENTITY_IS_DELETED' in error_msg:
                                    solution = 'This record has already been deleted.'
                                elif 'DELETE_FAILED' in error_msg and 'CASCADE_DELETE_FAILED' in error_msg:
                                    solution = 'Delete related records first or enable cascade delete option.'
                                elif 'FIELD_INTEGRITY_EXCEPTION' in error_msg:
                                    solution = 'This record is referenced by other records. Delete those records first or use cascade delete.'
                                elif 'INVALID_CROSS_REFERENCE_KEY' in error_msg:
                                    solution = 'The record ID is invalid or the record does not exist.'
                                elif 'associated with the following' in error_msg:
                                    # Parse the error to identify what needs to be deleted
                                    solution = 'Delete the related records first, then retry deleting this record.'
                                
                                errors.append({
                                    'recordId': record_id,
                                    'message': error_msg,
                                    'solution': solution
                                })
                                
                        except subprocess.TimeoutExpired:
                            errors.append({
                                'recordId': record_id,
                                'message': 'Operation timed out',
                                'solution': 'The deletion is taking longer than expected. Try again or check your network connection.'
                            })
                        except Exception as e:
                            errors.append({
                                'recordId': record_id,
                                'message': str(e),
                                'solution': 'An unexpected error occurred. Please try again.'
                            })
                    
                    # If we successfully deleted records, update the Excel file
                    if deleted_count > 0:
                        try:
                            print(f"[DELETE] Updating Excel file to remove {deleted_count} deleted records")
                            
                            # Import pandas for Excel manipulation
                            import pandas as pd
                            
                            # Get sheet mapping
                            sheet_mapping = {
                                'ProductCatalog': '11_ProductCatalog',
                                'ProductCategory': '12_ProductCategory',
                                'Product2': '13_Product2',
                                'ProductClassification': '08_ProductClassification',
                                'AttributeDefinition': '09_AttributeDefinition',
                                'AttributeCategory': '10_AttributeCategory',
                                'AttributePicklist': '14_AttributePicklist',
                                'AttributePicklistValue': '18_AttributePicklistValue',
                                'ProductAttributeDefinition': '17_ProductAttributeDef',
                                'Pricebook2': '19_Pricebook2',
                                'PricebookEntry': '20_PricebookEntry',
                                # Add more mappings as needed
                            }
                            
                            sheet_name = sheet_mapping.get(object_name)
                            if sheet_name and os.path.exists(workbook):
                                # Read the Excel file
                                df = pd.read_excel(workbook, sheet_name=sheet_name)
                                original_count = len(df)
                                
                                # Remove deleted records
                                successfully_deleted_ids = [rid for rid in record_ids if rid not in [err['recordId'] for err in errors]]
                                df = df[~df['Id'].isin(successfully_deleted_ids)]
                                new_count = len(df)
                                
                                print(f"[DELETE] Removed {original_count - new_count} records from Excel")
                                
                                # Write back to Excel
                                with pd.ExcelWriter(workbook, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                                
                                print(f"[DELETE] Excel file updated successfully")
                                
                        except Exception as e:
                            print(f"[DELETE] Warning: Failed to update Excel file: {e}")
                            # Don't fail the whole operation if Excel update fails
                    
                    response = {
                        'success': len(errors) == 0,
                        'deletedCount': deleted_count,
                        'errors': errors
                    }
                    
                    # Add cascade delete info if applicable
                    if cascade_delete and 'cascade_deleted' in locals():
                        response['cascadeDeleted'] = cascade_deleted
                        response['cascadeDeletedCount'] = len(cascade_deleted)
            
            except Exception as e:
                response = {
                    'success': False,
                    'errors': [{'message': f'Server error: {str(e)}'}]
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/objects/check-dependencies':
            # Check for related records before deletion
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            object_name = data.get('objectName')
            record_ids = data.get('recordIds', [])
            
            try:
                print(f"[CHECK-DEPS] Checking dependencies for {object_name} records: {record_ids}")
                
                # Define known relationships
                relationships = {
                    'AttributeDefinition': [
                        {'object': 'ProductAttributeDefinition', 'field': 'AttributeDefinitionId'},
                        {'object': 'AttributePicklistValue', 'field': 'AttributeDefinitionId'}
                    ],
                    'ProductCatalog': [
                        {'object': 'ProductCategory', 'field': 'CatalogId'}
                    ],
                    'Product2': [
                        {'object': 'ProductAttributeDefinition', 'field': 'ProductId'},
                        {'object': 'PricebookEntry', 'field': 'Product2Id'},
                        {'object': 'ProductCategoryProduct', 'field': 'ProductId'}
                    ],
                    'ProductCategory': [
                        {'object': 'ProductCategoryProduct', 'field': 'ProductCategoryId'}
                    ],
                    'ProductClassification': [
                        {'object': 'Product2', 'field': 'ProductClassificationId'},
                        {'object': 'ProductClassificationAttr', 'field': 'ProductClassificationId'}
                    ],
                    'ProductAttribute': [
                        {'object': 'ProductAttributeDefinition', 'field': 'AttributeDefinitionId'}
                    ]
                }
                
                related_records = []
                
                # Check if this object has known relationships
                if object_name in relationships:
                    CLI_COMMAND = 'sf'
                    connection_alias = 'fortradp2'
                    
                    for rel in relationships[object_name]:
                        rel_object = rel['object']
                        rel_field = rel['field']
                        
                        # Define fields to query for each object type
                        object_fields = {
                            'Product2': 'Id, Name, ProductCode, IsActive, Family',
                            'ProductAttributeDefinition': 'Id, AttributeDefinitionId, ProductId, Sequence',
                            'PricebookEntry': 'Id, Product2Id, Pricebook2Id, UnitPrice, IsActive',
                            'ProductCategoryProduct': 'Id, ProductId, ProductCategoryId',
                            'ProductCategory': 'Id, Name, Description',
                            'AttributePicklistValue': 'Id, AttributeDefinitionId, AttributePicklistId, Name, Code'
                        }
                        
                        # Get fields for this related object
                        fields = object_fields.get(rel_object, 'Id, Name')
                        
                        # Query for related records
                        for record_id in record_ids:
                            query = f"SELECT {fields} FROM {rel_object} WHERE {rel_field} = '{record_id}'"
                            cmd = [
                                CLI_COMMAND, 'data', 'query',
                                '--query', query,
                                '--target-org', connection_alias,
                                '--json'
                            ]
                            
                            print(f"[CHECK-DEPS] Query: {query}")
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                            
                            if result.returncode == 0:
                                try:
                                    data = json.loads(result.stdout)
                                    if 'result' in data and 'records' in data['result']:
                                        records = data['result']['records']
                                        print(f"[CHECK-DEPS] Found {len(records)} {rel_object} records")
                                        if records:
                                            # Remove attributes field
                                            for rec in records:
                                                if 'attributes' in rec:
                                                    del rec['attributes']
                                            
                                            related_records.append({
                                                'objectName': rel_object,
                                                'parentId': record_id,
                                                'count': len(records),
                                                'records': records,  # Return all records
                                                'hasMore': False  # We'll implement pagination if needed
                                            })
                                except:
                                    pass
                
                response = {
                    'hasRelatedRecords': len(related_records) > 0,
                    'relatedRecords': related_records
                }
                
            except Exception as e:
                print(f"[CHECK-DEPS] Error: {str(e)}")
                response = {
                    'hasRelatedRecords': False,
                    'relatedRecords': [],
                    'error': str(e)
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/objects/check-deep-dependencies':
            # Check for dependencies of a specific record (drill-down)
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            object_name = data.get('objectName')
            record_id = data.get('recordId')
            
            try:
                print(f"[CHECK-DEEP-DEPS] Checking deep dependencies for {object_name} record: {record_id}")
                
                # Same relationships as above
                relationships = {
                    'Product2': [
                        {'object': 'ProductAttributeDefinition', 'field': 'ProductId'},
                        {'object': 'PricebookEntry', 'field': 'Product2Id'},
                        {'object': 'ProductCategoryProduct', 'field': 'ProductId'}
                    ],
                    'ProductCategory': [
                        {'object': 'ProductCategoryProduct', 'field': 'ProductCategoryId'}
                    ],
                    'ProductCategoryProduct': [
                        {'object': 'Product2', 'field': 'Id', 'lookupField': 'ProductId'},
                        {'object': 'ProductCategory', 'field': 'Id', 'lookupField': 'ProductCategoryId'}
                    ],
                    'ProductClassification': [
                        {'object': 'Product2', 'field': 'ProductClassificationId'},
                        {'object': 'ProductClassificationAttr', 'field': 'ProductClassificationId'}
                    ]
                }
                
                related_records = []
                CLI_COMMAND = 'sf'
                connection_alias = 'fortradp2'
                
                if object_name in relationships:
                    for rel in relationships[object_name]:
                        rel_object = rel['object']
                        rel_field = rel['field']
                        lookup_field = rel.get('lookupField', rel_field)
                        
                        # Define fields to query
                        object_fields = {
                            'Product2': 'Id, Name, ProductCode, IsActive, Family',
                            'ProductAttributeDefinition': 'Id, AttributeDefinitionId, ProductId, Sequence',
                            'PricebookEntry': 'Id, Product2Id, Pricebook2Id, UnitPrice, IsActive',
                            'ProductCategoryProduct': 'Id, ProductId, ProductCategoryId',
                            'ProductCategory': 'Id, Name, Description'
                        }
                        
                        fields = object_fields.get(rel_object, 'Id, Name')
                        query = f"SELECT {fields} FROM {rel_object} WHERE {lookup_field} = '{record_id}'"
                        
                        cmd = [
                            CLI_COMMAND, 'data', 'query',
                            '--query', query,
                            '--target-org', connection_alias,
                            '--json'
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            try:
                                data = json.loads(result.stdout)
                                if 'result' in data and 'records' in data['result']:
                                    records = data['result']['records']
                                    if records:
                                        for rec in records:
                                            if 'attributes' in rec:
                                                del rec['attributes']
                                        
                                        related_records.append({
                                            'objectName': rel_object,
                                            'parentId': record_id,
                                            'count': len(records),
                                            'records': records
                                        })
                            except:
                                pass
                
                response = {
                    'hasRelatedRecords': len(related_records) > 0,
                    'relatedRecords': related_records
                }
                
            except Exception as e:
                response = {
                    'hasRelatedRecords': False,
                    'error': str(e)
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/api/sync/') and self.path != '/api/sync/progress/':
            # Sync specific object from Salesforce to Excel
            object_name = self.path.split('/')[-1]
            
            try:
                print(f"[SYNC] Starting sync for {object_name}")
                
                # Import necessary modules
                import pandas as pd
                
                # Get sheet mapping
                sheet_mapping = {
                    'ProductCatalog': '11_ProductCatalog',
                    'ProductCategory': '12_ProductCategory',
                    'Product2': '13_Product2',
                    'ProductClassification': '08_ProductClassification',
                    'AttributeDefinition': '09_AttributeDefinition',
                    'AttributeCategory': '10_AttributeCategory',
                    'AttributePicklist': '14_AttributePicklist',
                    'AttributePicklistValue': '18_AttributePicklistValue',
                    'ProductAttributeDefinition': '17_ProductAttributeDef',
                    'Pricebook2': '19_Pricebook2',
                    'PricebookEntry': '20_PricebookEntry',
                    'CostBook': '01_CostBook',
                    'BillingPolicy': '06_BillingPolicy',
                    'BillingTreatment': '07_BillingTreatment',
                    'LegalEntity': '02_LegalEntity',
                    'TaxEngine': '03_TaxEngine',
                    'TaxPolicy': '04_TaxPolicy',
                    'TaxTreatment': '05_TaxTreatment',
                }
                
                sheet_name = sheet_mapping.get(object_name)
                if not sheet_name:
                    response = {
                        'success': False,
                        'error': f'No sheet mapping found for {object_name}'
                    }
                else:
                    # Query Salesforce for current data
                    CLI_COMMAND = 'sf'
                    connection_alias = 'fortradp2'
                    
                    # First, let's try a simple query to test
                    # For ProductCatalog, we need specific fields since FIELDS(ALL) might not work
                    field_mappings = {
                        'ProductCatalog': 'Id, Name, Code, Description, CatalogType, EffectiveStartDate, EffectiveEndDate',
                        'Product2': 'Id, Name, ProductCode, StockKeepingUnit, Description, IsActive, Family, AvailabilityDate, BasedOnId, IsAssetizable, ConfigureDuringSale, QuantityUnitOfMeasure, UnitOfMeasureId, HelpText, IsSoldOnlyWithOtherProds, TaxPolicyId, DiscontinuedDate, EndOfLifeDate',
                        'ProductClassification': 'Id, Name, Code, Status',
                        'AttributeDefinition': 'Id, Name, Label, Description, IsActive, IsRequired, DefaultValue, Code, PicklistId, DefaultHelpText, ValueDescription, SourceSystemIdentifier',
                        'AttributeCategory': 'Id, Name, Code, Description',
                        'TaxEngine': 'Id, TaxEngineName',  # TaxEngine uses TaxEngineName instead of Name
                        'TaxPolicy': 'Id, Name',
                        'TaxTreatment': 'Id, Name',
                        'LegalEntity': 'Id, Name',
                        'BillingPolicy': 'Id, Name',
                        'BillingTreatment': 'Id, Name',
                        'CostBook': 'Id, Name',
                        'Pricebook2': 'Id, Name, IsActive, Description',
                        'PricebookEntry': 'Id, Pricebook2Id, Product2Id, UnitPrice, IsActive, UseStandardPrice, ProductSellingModelId',
                        # Add more as needed
                    }
                    
                    # Get fields for this object or use a basic set
                    fields = field_mappings.get(object_name)
                    
                    # If no field mapping exists, try to discover fields dynamically
                    if not fields:
                        print(f"[SYNC] No field mapping for {object_name}, attempting field discovery")
                        
                        # Try to describe the object to get field names
                        describe_cmd = [
                            CLI_COMMAND, 'sobject', 'describe',
                            '--sobject', object_name,
                            '--target-org', connection_alias,
                            '--json'
                        ]
                        
                        describe_result = subprocess.run(describe_cmd, capture_output=True, text=True, timeout=30)
                        
                        if describe_result.returncode == 0:
                            try:
                                describe_data = json.loads(describe_result.stdout)
                                if 'result' in describe_data and 'fields' in describe_data['result']:
                                    # Get common fields that are likely to exist
                                    available_fields = []
                                    field_names = [f['name'] for f in describe_data['result']['fields']]
                                    
                                    # Priority list of fields to include
                                    priority_fields = ['Id', 'Name', 'Code', 'Description', 'IsActive', 
                                                     'CreatedDate', 'LastModifiedDate']
                                    
                                    # Add fields in priority order if they exist
                                    for field in priority_fields:
                                        if field in field_names:
                                            available_fields.append(field)
                                    
                                    # If no Name field, look for alternatives
                                    if 'Name' not in available_fields:
                                        name_alternatives = [f for f in field_names if 'Name' in f]
                                        if name_alternatives:
                                            available_fields.extend(name_alternatives[:2])  # Add up to 2 name-like fields
                                    
                                    if available_fields:
                                        fields = ', '.join(available_fields)
                                        print(f"[SYNC] Discovered fields for {object_name}: {fields}")
                                    else:
                                        fields = 'Id'  # Fallback to just Id
                                else:
                                    fields = 'Id, Name'  # Default fallback
                            except:
                                fields = 'Id, Name'  # Default fallback
                        else:
                            fields = 'Id, Name'  # Default fallback
                    
                    # Build query command
                    cmd = [
                        CLI_COMMAND, 'data', 'query',
                        '--query', f"SELECT {fields} FROM {object_name} LIMIT 2000",
                        '--target-org', connection_alias,
                        '--result-format', 'json',
                        '--json'
                    ]
                    
                    print(f"[SYNC] Executing: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        try:
                            data = json.loads(result.stdout)
                            if 'result' in data and 'records' in data['result']:
                                records = data['result']['records']
                                
                                # Remove attributes field from each record
                                for record in records:
                                    if 'attributes' in record:
                                        del record['attributes']
                                    
                                    # Normalize name fields - if there's no 'Name' field but there's a field containing 'Name', use it
                                    if 'Name' not in record:
                                        # Look for fields containing 'Name'
                                        name_fields = [k for k in record.keys() if 'Name' in k and k != 'Id']
                                        if name_fields:
                                            # Use the first name-like field as 'Name'
                                            record['Name'] = record.get(name_fields[0], '')
                                            print(f"[SYNC] Normalized {name_fields[0]} to Name for {object_name}")
                                
                                print(f"[SYNC] Retrieved {len(records)} records from Salesforce")
                                
                                # Convert to DataFrame
                                df = pd.DataFrame(records)
                                
                                # Update Excel file
                                with pd.ExcelWriter(workbook, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                                
                                print(f"[SYNC] Updated Excel sheet {sheet_name} with {len(records)} records")
                                
                                response = {
                                    'success': True,
                                    'recordCount': len(records),
                                    'message': f'Synced {len(records)} records from Salesforce'
                                }
                            else:
                                response = {
                                    'success': False,
                                    'error': 'No records returned from Salesforce'
                                }
                        except json.JSONDecodeError as e:
                            response = {
                                'success': False,
                                'error': f'Failed to parse Salesforce response: {str(e)}'
                            }
                    else:
                        error_msg = result.stderr or result.stdout
                        print(f"[SYNC] Command failed with return code {result.returncode}")
                        print(f"[SYNC] STDOUT: {result.stdout}")
                        print(f"[SYNC] STDERR: {result.stderr}")
                        
                        # Try to parse error from JSON response
                        try:
                            error_data = json.loads(result.stdout)
                            if 'message' in error_data:
                                error_msg = error_data['message']
                            elif 'name' in error_data:
                                error_msg = error_data.get('name', 'Unknown error')
                        except:
                            pass
                            
                        response = {
                            'success': False,
                            'error': f'Salesforce query failed: {error_msg}'
                        }
                        
            except Exception as e:
                print(f"[SYNC] Error: {str(e)}")
                import traceback
                traceback.print_exc()
                response = {
                    'success': False,
                    'error': f'Sync error: {str(e)}'
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_error(404, "Endpoint not found")

def start_server():
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Revenue Cloud Migration Tool running at http://localhost:{PORT}")
        print("Press Ctrl-C to stop the server")
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")