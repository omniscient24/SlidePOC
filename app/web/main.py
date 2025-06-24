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
            
            <div class="object-card" data-category="products" onclick="manageObject('Product2')">
                <div class="object-header">
                    <div class="object-title">Product</div>
                    <div class="object-count">0 records</div>
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
            
            <div class="object-card" data-category="products" onclick="manageObject('ProductSellingModel')">
                <div class="object-header">
                    <div class="object-title">Product Selling Model</div>
                    <div class="object-count">0 records</div>
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
            
            <div class="object-card" data-category="pricing" onclick="manageObject('PricebookEntry')">
                <div class="object-header">
                    <div class="object-title">Price Book Entry</div>
                    <div class="object-count">0 records</div>
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