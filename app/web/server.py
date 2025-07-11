#!/usr/bin/env python3
"""
Simple working server implementation
"""
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.connection_manager import connection_manager
from app.services.session_manager import session_manager
from app.services.file_upload_service import file_upload_service
from config.settings.app_config import HOST, PORT, TEMPLATES_ROOT, STATIC_ROOT

class SimpleHandler(BaseHTTPRequestHandler):
    """Simple request handler without complex inheritance"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        try:
            # Route handling
            if path == '/login':
                self.serve_login_page()
            elif path == '/api/connections':
                self.handle_get_connections()
            elif path == '/api/session':
                self.handle_get_session()
            elif path.startswith('/api/workbook/'):
                if path.startswith('/api/workbook/view'):
                    self.handle_view_workbook()
                elif path.startswith('/api/workbook/download'):
                    self.handle_download_workbook()
                else:
                    self.send_error(404)
            elif path == '/api/objects/status':
                self.handle_get_object_status()
            elif path == '/api/objects/counts':
                self.handle_get_object_counts()
            elif path.startswith('/static/'):
                self.serve_static_file(path)
            elif path == '/':
                # Check auth and redirect
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_home_page()
                else:
                    self.redirect('/login')
            elif path == '/data-management':
                # Check auth for data management
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_data_management_page()
                else:
                    self.redirect('/login')
            elif path == '/connections':
                # Check auth for connections page
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_connections_page()
                else:
                    self.redirect('/login')
            else:
                self.send_error(404)
        except Exception as e:
            print(f"Error in GET: {e}")
            self.send_error(500)
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        try:
            if path == '/api/login':
                self.handle_login()
            elif path == '/api/connections/add':
                self.handle_add_connection()
            elif path == '/api/upload':
                self.handle_file_upload()
            elif path == '/api/sync':
                self.handle_sync()
            elif path == '/api/logout':
                self.handle_logout()
            elif path.startswith('/api/connections/'):
                # Handle connection-specific endpoints
                if path == '/api/connections/test':
                    self.handle_test_connection()
                elif path == '/api/connections/delete':
                    self.handle_delete_connection()
                elif path == '/api/connections/refresh':
                    self.handle_refresh_connection()
                else:
                    self.send_error(404)
            else:
                self.send_error(404)
        except Exception as e:
            print(f"Error in POST: {e}")
            self.send_error(500)
    
    def serve_login_page(self):
        """Serve the login page"""
        try:
            file_path = TEMPLATES_ROOT / 'login.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving login page: {e}")
            self.send_error(500)
    
    def serve_home_page(self):
        """Serve the home page"""
        try:
            file_path = TEMPLATES_ROOT / 'home.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving home page: {e}")
            self.send_error(500)
    
    def serve_static_file(self, path):
        """Serve static files"""
        try:
            # Remove /static/ prefix
            file_path = STATIC_ROOT / path[8:]
            
            if not file_path.exists():
                self.send_error(404)
                return
            
            # Determine content type
            if file_path.suffix == '.css':
                content_type = 'text/css'
            elif file_path.suffix == '.js':
                content_type = 'application/javascript'
            else:
                content_type = 'text/plain'
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving static file: {e}")
            self.send_error(500)
    
    def handle_get_connections(self):
        """Handle GET /api/connections"""
        try:
            connections = connection_manager.get_all_connections()
            response = {
                'success': True,
                'connections': connections
            }
            self.send_json_response(response)
        except Exception as e:
            print(f"Error getting connections: {e}")
            self.send_error(500)
    
    def handle_login(self):
        """Handle POST /api/login"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            connection_id = data.get('connection_id')
            if not connection_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Connection ID required'
                })
                return
            
            # Verify connection
            connection = connection_manager.get_connection(connection_id)
            if not connection:
                self.send_json_response({
                    'success': False,
                    'error': 'Invalid connection'
                })
                return
            
            # Create session
            username = connection['metadata'].get('username', 'unknown')
            session_id = session_manager.create_session(username, connection_id)
            
            # Set active connection
            session = session_manager.get_session(session_id)
            connection_manager.set_active_connection(session, connection_id)
            
            # Send response with session cookie
            response = {
                'success': True,
                'session_id': session_id,
                'redirect': '/'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'rcm_session={session_id}; Path=/; HttpOnly')
            content = json.dumps(response).encode()
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            print(f"Error handling login: {e}")
            self.send_error(500)
    
    def handle_add_connection(self):
        """Handle POST /api/connections/add"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            # Get data
            name = data.get('name', '')
            org_type = data.get('org_type', 'sandbox')
            description = data.get('description', '')
            
            if not name:
                self.send_json_response({
                    'success': False,
                    'error': 'Connection name required'
                })
                return
            
            # Add connection (this will open browser for OAuth)
            success, result = connection_manager.add_connection(
                name, description, org_type
            )
            
            if success:
                self.send_json_response({
                    'success': True,
                    'connection': result
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': result.get('error', 'Failed to add connection')
                })
                
        except Exception as e:
            print(f"Error adding connection: {e}")
            self.send_error(500)
    
    def send_json_response(self, data):
        """Send JSON response"""
        try:
            content = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error sending JSON: {e}")
    
    def redirect(self, location):
        """Send redirect response"""
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()
    
    def serve_data_management_page(self):
        """Serve the data management page"""
        try:
            file_path = TEMPLATES_ROOT / 'data-management.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving data management page: {e}")
            self.send_error(500)
    
    def serve_connections_page(self):
        """Serve the connections management page"""
        try:
            file_path = TEMPLATES_ROOT / 'connections.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving connections page: {e}")
            self.send_error(500)
    
    def handle_get_session(self):
        """Get current session info"""
        try:
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            
            if session_id:
                session = session_manager.get_session(session_id)
                if session:
                    # Get active connection info
                    conn_id = session.get('active_connection_id')
                    if conn_id:
                        connection = connection_manager.get_connection(conn_id)
                        self.send_json_response({
                            'success': True,
                            'session_id': session_id,
                            'username': session.get('username'),
                            'active_connection': connection
                        })
                        return
            
            self.send_json_response({
                'success': False,
                'error': 'No active session'
            })
        except Exception as e:
            print(f"Error getting session: {e}")
            self.send_error(500)
    
    def handle_file_upload(self):
        """Handle file upload"""
        try:
            # Get session
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_json_response({
                    'success': False,
                    'error': 'Authentication required'
                })
                return
            
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_json_response({
                    'success': False,
                    'error': 'Invalid content type'
                })
                return
            
            # For simple implementation, we'll use cgi module
            import cgi
            from io import BytesIO
            
            # Create environment for cgi
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': self.headers.get('Content-Length', '0')
            }
            
            # Parse form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ
            )
            
            # Get file and form fields
            if 'file' not in form:
                self.send_json_response({
                    'success': False,
                    'error': 'No file provided'
                })
                return
            
            file_item = form['file']
            if not file_item.filename:
                self.send_json_response({
                    'success': False,
                    'error': 'No file selected'
                })
                return
            
            # Get other form fields
            object_name = form.getvalue('object', '')
            operation = form.getvalue('operation', 'upsert')
            external_id = form.getvalue('externalId', '')
            
            if not object_name:
                self.send_json_response({
                    'success': False,
                    'error': 'Object name required'
                })
                return
            
            # Read file data
            file_data = file_item.file.read()
            filename = file_item.filename
            
            # Validate file
            valid, error = file_upload_service.validate_file(filename, len(file_data))
            if not valid:
                self.send_json_response({
                    'success': False,
                    'error': error
                })
                return
            
            # Save and process file
            success, result = file_upload_service.save_upload(
                file_data, filename, object_name, session_id
            )
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': f'File uploaded successfully',
                    'recordCount': result['metadata']['record_count'],
                    'file_path': result['file_path'],
                    'preview': result['preview']
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': result.get('error', 'Upload failed')
                })
            
        except Exception as e:
            print(f"Error handling file upload: {e}")
            self.send_json_response({
                'success': False,
                'error': f'Upload error: {str(e)}'
            })
    
    def handle_sync(self):
        """Handle data sync request"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            objects = data.get('objects', [])
            if not objects:
                self.send_json_response({
                    'success': False,
                    'error': 'No objects selected'
                })
                return
            
            # For now, return a placeholder response
            # TODO: Implement actual sync functionality
            job_id = str(uuid.uuid4())
            
            self.send_json_response({
                'success': True,
                'jobId': job_id,
                'message': f'Sync started for {len(objects)} objects'
            })
            
        except Exception as e:
            print(f"Error handling sync: {e}")
            self.send_error(500)
    
    def handle_logout(self):
        """Handle logout"""
        try:
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            
            if session_id:
                session_manager.destroy_session(session_id)
            
            self.send_json_response({
                'success': True,
                'redirect': '/login'
            })
            
        except Exception as e:
            print(f"Error handling logout: {e}")
            self.send_error(500)
    
    def handle_test_connection(self):
        """Test a Salesforce connection"""
        try:
            # Get request data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            connection_id = data.get('connection_id')
            if not connection_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Connection ID required'
                })
                return
            
            # Test the connection
            success, result = connection_manager.test_connection(connection_id)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': result.get('message', 'Connection test successful'),
                    'details': result
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': result.get('error', 'Connection test failed')
                })
                
        except Exception as e:
            print(f"Error testing connection: {e}")
            self.send_error(500)
    
    def handle_delete_connection(self):
        """Delete a connection"""
        try:
            # Get request data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            connection_id = data.get('connection_id')
            if not connection_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Connection ID required'
                })
                return
            
            # Delete the connection
            success = connection_manager.delete_connection(connection_id)
            
            self.send_json_response({
                'success': success,
                'message': 'Connection deleted' if success else 'Failed to delete connection'
            })
            
        except Exception as e:
            print(f"Error deleting connection: {e}")
            self.send_error(500)
    
    def handle_refresh_connection(self):
        """Refresh a connection"""
        try:
            # Get request data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            connection_id = data.get('connection_id')
            if not connection_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Connection ID required'
                })
                return
            
            # Refresh the connection
            success, message = connection_manager.refresh_connection(connection_id)
            
            self.send_json_response({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            print(f"Error refreshing connection: {e}")
            self.send_error(500)
    
    def handle_view_workbook(self):
        """Handle viewing workbook data"""
        try:
            # Parse query parameters
            from urllib.parse import parse_qs
            query_string = self.path.split('?')[1] if '?' in self.path else ''
            params = parse_qs(query_string)
            
            object_name = params.get('object', [''])[0]
            if not object_name:
                self.send_json_response({
                    'success': False,
                    'error': 'Object name required'
                })
                return
            
            # Get session
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            
            # Import pandas for Excel reading
            import pandas as pd
            import os
            
            # Path to the main workbook - use absolute path from server location
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
            
            # Check if workbook exists
            if not os.path.exists(workbook_path):
                # Try alternative path
                workbook_path = os.path.join(BASE_DIR, 'data', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
            
            if not os.path.exists(workbook_path):
                self.send_json_response({
                    'success': False,
                    'error': 'Workbook not found'
                })
                return
            
            # Map object names to sheet names
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
                'CostBookEntry': '15_CostBookEntry',
                'PriceAdjustmentSchedule': '21_PriceAdjustmentSchedule',
                'PriceAdjustmentTier': '22_PriceAdjustmentTier',
                'LegalEntity': '02_LegalEntity',
                'TaxEngine': '03_TaxEngine',
                'TaxPolicy': '04_TaxPolicy',
                'TaxTreatment': '05_TaxTreatment',
                'BillingPolicy': '06_BillingPolicy',
                'BillingTreatment': '07_BillingTreatment',
                'ProductSellingModel': '15_ProductSellingModel',
                'ProductComponentGroup': '14_ProductComponentGroup',
                'ProductRelatedComponent': '25_ProductRelatedComponent',
                'ProductCategoryProduct': '26_ProductCategoryProduct',
                'AttributeBasedAdjRule': '23_AttributeBasedAdjRule',
                'AttributeBasedAdjustment': '24_AttributeBasedAdj'
            }
            
            # Get sheet name
            sheet_name = sheet_mapping.get(object_name)
            if not sheet_name:
                # For objects without sheets in the workbook, return empty data
                self.send_json_response({
                    'success': True,
                    'data': [],
                    'object': object_name,
                    'sheet': None,
                    'workbook': os.path.basename(workbook_path),
                    'message': f'No sheet available for {object_name} in the workbook'
                })
                return
            
            try:
                # Read the specific sheet
                print(f"Reading sheet {sheet_name} from {workbook_path}")
                df = pd.read_excel(workbook_path, sheet_name=sheet_name)
                print(f"Successfully read {len(df)} rows")
                
                # Remove any rows that are completely empty
                df = df.dropna(how='all')
                
                # Convert to records format
                records = df.to_dict('records')
                
                # Clean up the records (remove NaN values)
                cleaned_records = []
                for record in records:
                    cleaned_record = {}
                    for key, value in record.items():
                        if pd.notna(value):
                            cleaned_record[key] = value
                    if cleaned_record:  # Only add if record has data
                        cleaned_records.append(cleaned_record)
                
                print(f"Returning {len(cleaned_records)} cleaned records")
                
                self.send_json_response({
                    'success': True,
                    'data': cleaned_records,
                    'object': object_name,
                    'sheet': sheet_name,
                    'workbook': os.path.basename(workbook_path)
                })
                
            except Exception as e:
                print(f"Error reading sheet {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                self.send_json_response({
                    'success': False,
                    'error': f'Failed to read sheet: {str(e)}'
                })
            
        except Exception as e:
            print(f"Error viewing workbook: {e}")
            self.send_error(500)
    
    def handle_download_workbook(self):
        """Handle downloading workbook"""
        try:
            # Parse query parameters
            from urllib.parse import parse_qs
            query_string = self.path.split('?')[1] if '?' in self.path else ''
            params = parse_qs(query_string)
            
            object_name = params.get('object', [''])[0]
            if not object_name:
                self.send_error(400, "Object name required")
                return
            
            # Create sample Excel workbook
            import pandas as pd
            from io import BytesIO
            
            # Sample data
            data = {
                'Id': ['01t1234567890ABC', '01t1234567890ABD', '01t1234567890ABE'],
                'Name': ['Sample Product 1', 'Sample Product 2', 'Sample Product 3'],
                'ProductCode': ['PROD-001', 'PROD-002', 'PROD-003'],
                'IsActive': [True, True, False]
            }
            
            df = pd.DataFrame(data)
            
            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=object_name, index=False)
            
            # Get the Excel data
            excel_data = output.getvalue()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', f'attachment; filename="{object_name}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx"')
            self.send_header('Content-Length', len(excel_data))
            self.end_headers()
            self.wfile.write(excel_data)
            
        except Exception as e:
            print(f"Error downloading workbook: {e}")
            self.send_error(500)
    
    def handle_get_object_status(self):
        """Get sync status for all objects"""
        try:
            # For now, return empty status
            # TODO: Implement actual status tracking
            self.send_json_response({
                'success': True,
                'status': {}
            })
            
        except Exception as e:
            print(f"Error getting object status: {e}")
            self.send_error(500)
    
    def handle_get_object_counts(self):
        """Get actual record counts from workbook"""
        try:
            import pandas as pd
            import os
            
            # Path to the main workbook
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
            
            if not os.path.exists(workbook_path):
                workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
            
            counts = {}
            
            if os.path.exists(workbook_path):
                # Sheet mapping
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
                    'CostBookEntry': '15_CostBookEntry',
                    'PriceAdjustmentSchedule': '21_PriceAdjustmentSchedule',
                    'PriceAdjustmentTier': '22_PriceAdjustmentTier',
                    'LegalEntity': '02_LegalEntity',
                    'TaxEngine': '03_TaxEngine',
                    'TaxPolicy': '04_TaxPolicy',
                    'TaxTreatment': '05_TaxTreatment',
                    'BillingPolicy': '06_BillingPolicy',
                    'BillingTreatment': '07_BillingTreatment',
                    'ProductSellingModel': '15_ProductSellingModel',
                    'ProductComponentGroup': '14_ProductComponentGroup',
                    'ProductRelatedComponent': '25_ProductRelatedComponent',
                    'ProductCategoryProduct': '26_ProductCategoryProduct',
                    'AttributeBasedAdjRule': '23_AttributeBasedAdjRule',
                    'AttributeBasedAdjustment': '24_AttributeBasedAdj'
                }
                
                # Read workbook once
                xl_file = pd.ExcelFile(workbook_path)
                
                # First, get counts for all mapped objects
                for api_name, sheet_name in sheet_mapping.items():
                    try:
                        if sheet_name in xl_file.sheet_names:
                            df = pd.read_excel(xl_file, sheet_name=sheet_name)
                            # Remove empty rows
                            df_clean = df.dropna(how='all')
                            counts[api_name] = len(df_clean)
                        else:
                            counts[api_name] = 0
                    except:
                        counts[api_name] = 0
                
                # Add 0 counts for objects without sheet mappings
                # These are transaction objects that don't have upload templates
                unmapped_objects = ['Order', 'OrderItem', 'Asset', 'AssetAction', 
                                  'AssetActionSource', 'Contract', 'ProductSellingModelOption']
                for obj in unmapped_objects:
                    counts[obj] = 0
            
            self.send_json_response({
                'success': True,
                'counts': counts,
                'workbook': os.path.basename(workbook_path) if os.path.exists(workbook_path) else None
            })
            
        except Exception as e:
            print(f"Error getting object counts: {e}")
            self.send_error(500)
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"{self.address_string()} - {format % args}")

def main():
    """Run the server"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║        Revenue Cloud Migration Tool - Web Server         ║
║                                                          ║
║  Server running at: http://{HOST}:{PORT}              ║
║  Press Ctrl+C to stop                                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    server = HTTPServer((HOST, PORT), SimpleHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()
    except Exception as e:
        print(f"Server error: {e}")
        server.shutdown()

if __name__ == "__main__":
    # Kill any existing servers first
    os.system("lsof -ti :8080 | xargs kill -9 2>/dev/null || true")
    import time
    time.sleep(1)
    
    main()