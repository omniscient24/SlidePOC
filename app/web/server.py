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
from app.services.sync_service import sync_service
from app.services.upload_service import upload_service
from app.services.sync_status_service import sync_status_service
from app.services.edit_service import edit_service
from config.settings.app_config import HOST, PORT, TEMPLATES_ROOT, STATIC_ROOT, DATA_ROOT

class SimpleHandler(BaseHTTPRequestHandler):
    """Simple request handler without complex inheritance"""
    
    def log_message(self, format, *args):
        """Override to add timestamp to logs"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        try:
            print(f"[DEBUG] GET request for: {path}")
            # Route handling
            if path == '/login':
                self.serve_login_page()
            elif path == '/api/connections':
                self.handle_get_connections()
            elif path == '/api/session':
                self.handle_get_session()
            elif path.startswith('/api/workbook/'):
                if path.startswith('/api/workbook/export'):
                    self.handle_export_workbook()
                elif path.startswith('/api/workbook/view'):
                    self.handle_view_workbook()
                elif path.startswith('/api/workbook/download'):
                    self.handle_download_workbook()
                else:
                    self.send_error(404)
            elif path == '/api/objects/status':
                self.handle_get_object_status()
            elif path == '/api/objects/counts':
                self.handle_get_object_counts()
            elif path == '/api/product-hierarchy':
                self.handle_get_product_hierarchy()
            elif path == '/api/edit/permissions':
                self.handle_get_edit_permissions()
            elif path == '/api/edit/field-config':
                self.handle_get_field_config()
            elif path == '/api/edit/changes/history':
                self.handle_get_change_history()
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
                print("[DEBUG] Checking auth for data-management page")
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                print(f"[DEBUG] Session ID: {session_id}")
                if session_id and session_manager.is_session_valid(session_id):
                    print("[DEBUG] Session valid, serving data-management page")
                    self.serve_data_management_page()
                else:
                    print("[DEBUG] No valid session, redirecting to login")
                    self.redirect('/login')
            elif path == '/connections':
                # Check auth for connections page
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_connections_page()
                else:
                    self.redirect('/login')
            elif path == '/sync':
                # Check auth for sync page
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_sync_page()
                else:
                    self.redirect('/login')
            elif path == '/product-hierarchy':
                # Check auth for product hierarchy page
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_product_hierarchy_page()
                else:
                    self.redirect('/login')
            elif path == '/product-hierarchy-test':
                # Test page without auth
                self.serve_product_hierarchy_test_page()
            elif path == '/test-catalogid-fix':
                # Test page for CatalogId fix
                self.serve_test_page('test-catalogid-fix.html')
            elif path == '/admin-settings':
                # Check auth for admin settings page
                cookie = self.headers.get('Cookie', '')
                session_id = session_manager.get_session_cookie(cookie)
                if session_id and session_manager.is_session_valid(session_id):
                    self.serve_admin_settings_page()
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
            elif path.startswith('/api/sync/'):
                # Handle individual object sync
                object_name = path.replace('/api/sync/', '')
                self.handle_object_sync(object_name)
            elif path == '/api/sync-status':
                self.handle_sync_status()
            elif path == '/api/logout':
                self.handle_logout()
            elif path == '/api/workbook/open':
                self.handle_open_workbook()
            elif path.startswith('/api/connections/'):
                # Handle connection-specific endpoints
                if path == '/api/connections/test':
                    self.handle_test_connection()
                elif path == '/api/connections/delete':
                    self.handle_delete_connection()
                elif path == '/api/connections/refresh':
                    self.handle_refresh_connection()
                elif path == '/api/connections/set-active':
                    self.handle_set_active_connection()
                else:
                    self.send_error(404)
            elif path == '/api/edit/permissions':
                self.handle_update_edit_permissions()
            elif path == '/api/edit/field-config':
                self.handle_update_field_config()
            elif path == '/api/edit/changes/validate':
                self.handle_validate_changes()
            elif path == '/api/edit/changes/commit':
                self.handle_commit_changes()
            elif path == '/api/hierarchy/add':
                self.handle_add_hierarchy_node()
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
            
            # Get active connection from session
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            active_connection_id = None
            
            if session_id and session_manager.is_session_valid(session_id):
                session_data = session_manager.get_session(session_id)
                active_connection_id = session_data.get('active_connection_id')
            
            response = {
                'success': True,
                'connections': connections,
                'active_connection_id': active_connection_id
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
            
            # Save the updated session back
            session_manager.update_session(session_id, session)
            
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
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with optional status code"""
        try:
            content = json.dumps(data).encode()
            self.send_response(status_code)
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
            print("[DEBUG] serve_data_management_page called")
            file_path = TEMPLATES_ROOT / 'data-management.html'
            print(f"[DEBUG] Looking for template at: {file_path}")
            print(f"[DEBUG] File exists: {file_path.exists()}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            print(f"[DEBUG] Read {len(content)} bytes from template")
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            print("[DEBUG] Successfully served data-management page")
        except Exception as e:
            print(f"[ERROR] Error serving data management page: {e}")
            import traceback
            traceback.print_exc()
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
    
    def serve_sync_page(self):
        """Serve the sync management page"""
        try:
            # Read the main.py file to get the SYNC_PAGE_HTML
            from app.web.main import SYNC_PAGE_HTML
            content = SYNC_PAGE_HTML.encode()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving sync page: {e}")
            self.send_error(500)
    
    def serve_product_hierarchy_page(self):
        """Serve the product hierarchy visualization page"""
        try:
            file_path = TEMPLATES_ROOT / 'product-hierarchy.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving product hierarchy page: {e}")
            self.send_error(500)
    
    def serve_product_hierarchy_test_page(self):
        """Serve the product hierarchy test page"""
        try:
            file_path = TEMPLATES_ROOT / 'product-hierarchy-test.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving product hierarchy test page: {e}")
            self.send_error(500)
    
    def serve_test_page(self, filename):
        """Serve a test page from the root directory"""
        try:
            import os
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(server_dir, filename)
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving test page {filename}: {e}")
            self.send_error(500)
    
    def serve_admin_settings_page(self):
        """Serve the admin settings page"""
        try:
            file_path = TEMPLATES_ROOT / 'admin-settings.html'
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving admin settings page: {e}")
            self.send_error(500)
    
    def handle_get_session(self):
        """Get current session info"""
        try:
            print("[DEBUG] handle_get_session called")
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            print(f"[DEBUG] Session cookie extracted: {session_id}")
            
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
            
            # Check if using workbook
            use_workbook = form.getvalue('useWorkbook', 'false') == 'true'
            
            if use_workbook:
                # Use the workbook file directly
                workbook_path = form.getvalue('workbookPath', '')
                if not workbook_path:
                    workbook_path = str(DATA_ROOT / 'templates' / 'master' / 'Revenue_Cloud_Complete_Upload_Template.xlsx')
                
                # Get form fields
                object_name = form.getvalue('object', '')
                operation = form.getvalue('operation', 'upsert')
                external_id = form.getvalue('externalId', '')
                
                if not object_name:
                    self.send_json_response({
                        'success': False,
                        'error': 'Object name required'
                    })
                    return
                
                # Use the workbook directly
                saved_file_path = workbook_path
                
            else:
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
                
                if not success:
                    self.send_json_response({
                        'success': False,
                        'error': result.get('error', 'Upload failed')
                    })
                    return
                
                # Get the saved file path
                saved_file_path = result['file_path']
            
            # Get session data to get connection alias
            session_data = session_manager.get_session(session_id)
            print(f"[DEBUG] Session data: {session_data}")
            
            if not session_data:
                self.send_json_response({
                    'success': False,
                    'error': 'No session data found'
                })
                return
                
            if 'active_connection_alias' not in session_data:
                print(f"[DEBUG] Session keys: {list(session_data.keys())}")
                self.send_json_response({
                    'success': False,
                    'error': 'No active connection alias in session'
                })
                return
            
            connection_alias = session_data['active_connection_alias']
            print(f"[DEBUG] Connection alias: {connection_alias}")
            
            # Upload to Salesforce and update workbook with results
            upload_success, upload_result = upload_service.upload_to_salesforce(
                saved_file_path,
                object_name,
                operation,
                external_id,
                connection_alias
            )
            
            # Check if this is a partial success (some records succeeded, some failed)
            is_partial_success = (not upload_success and 
                                upload_result.get('partial_success') and 
                                upload_result.get('records_processed', 0) > upload_result.get('records_failed', 0))
            
            if upload_success or is_partial_success:
                # Update sync status
                records_processed = upload_result.get('records_processed', 0)
                records_failed = upload_result.get('records_failed', 0)
                upload_message = upload_result.get('message', 'Upload completed successfully')
                
                sync_status_service.update_upload_status(
                    object_name=object_name,
                    upload_success=upload_success,
                    records_processed=records_processed,
                    records_failed=records_failed,
                    upload_message=upload_message
                )
                
                # Handle workbook vs file upload responses
                if use_workbook:
                    response_data = {
                        'success': True,
                        'message': upload_result.get('message', 'Upload completed successfully'),
                        'recordCount': upload_result.get('records_processed', 0),
                        'file_path': saved_file_path,
                        'preview': None,  # No preview for workbook
                        'salesforce_result': upload_result
                    }
                else:
                    # Combine results from file save and Salesforce upload
                    response_data = {
                        'success': True,
                        'message': upload_result.get('message', 'Upload completed successfully'),
                        'recordCount': result['metadata']['record_count'],
                        'file_path': result['file_path'],
                        'preview': result['preview'],
                        'salesforce_result': upload_result
                    }
                
                # Add specific fields based on operation type
                if operation == 'upsert':
                    response_data['records_processed'] = upload_result.get('records_processed', 0)
                    response_data['records_failed'] = upload_result.get('records_failed', 0)
                    response_data['records_created'] = upload_result.get('records_created', 0)
                    
                    # Add failure details if available
                    if 'failure_details' in upload_result:
                        response_data['failure_details'] = upload_result['failure_details']
                
                self.send_json_response(response_data)
            else:
                self.send_json_response({
                    'success': False,
                    'error': upload_result.get('error', 'Salesforce upload failed'),
                    'details': upload_result.get('details', '')
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
            # Get session to retrieve connection info
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Authentication required'
                })
                return
            
            session = session_manager.get_session(session_id)
            if not session:
                self.send_json_response({
                    'success': False,
                    'error': 'Invalid session'
                })
                return
            
            # Get active connection
            connection = connection_manager.get_active_connection(session)
            if not connection:
                self.send_json_response({
                    'success': False,
                    'error': 'No active connection'
                })
                return
            
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
            
            # Get connection alias
            connection_alias = connection.get('cli_alias')
            
            # Perform sync using sync service
            print(f"[SYNC] Starting sync for {len(objects)} objects using connection {connection_alias}")
            success, result = sync_service.sync_objects(objects, connection_alias)
            
            # Update sync status for each successfully synced object
            if 'synced' in result:
                for synced_obj in result['synced']:
                    object_name = synced_obj.get('object')
                    record_count = synced_obj.get('recordCount', 0)
                    if object_name:
                        sync_status_service.update_sync_status(
                            object_name=object_name,
                            record_count=record_count,
                            sync_success=True
                        )
            
            if success:
                self.send_json_response({
                    'success': True,
                    'synced': result.get('synced', []),
                    'failed': result.get('failed', []),
                    'message': f'Sync completed for {len(objects)} objects'
                })
            else:
                self.send_json_response({
                    'success': False,
                    'synced': result.get('synced', []),
                    'failed': result.get('failed', []),
                    'error': 'Some objects failed to sync'
                })
            
        except Exception as e:
            print(f"Error handling sync: {e}")
            self.send_json_response({
                'success': False,
                'error': f'Sync error: {str(e)}'
            })
    
    def handle_object_sync(self, object_name):
        """Handle sync request for a specific object"""
        try:
            # Get session to retrieve connection info
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Authentication required'
                })
                return
            
            session = session_manager.get_session(session_id)
            if not session:
                self.send_json_response({
                    'success': False,
                    'error': 'Invalid session'
                })
                return
            
            # Get active connection alias
            active_connection_id = session.get('active_connection_id')
            if not active_connection_id:
                self.send_json_response({
                    'success': False,
                    'error': 'No active connection selected'
                })
                return
            
            # Get the actual connection object
            active_connection = connection_manager.get_connection(active_connection_id)
            if not active_connection:
                self.send_json_response({
                    'success': False,
                    'error': 'Active connection not found'
                })
                return
            
            connection_alias = active_connection.get('cli_alias')
            
            # Log the sync request
            print(f"[SYNC] Individual sync request for {object_name} using connection {connection_alias}")
            
            # Perform sync for the specific object
            success, result = sync_service.sync_single_object(object_name, connection_alias)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'recordCount': result.get('recordCount', 0),
                    'message': result.get('message', f'Successfully synced {object_name}')
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': result.get('error', 'Sync failed')
                })
                
        except Exception as e:
            print(f"Error in handle_object_sync: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': f'Sync error: {str(e)}'
            })
    
    def handle_sync_status(self):
        """Handle sync status request"""
        try:
            # Get session to ensure user is authenticated
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id:
                self.send_json_response({
                    'success': False,
                    'error': 'Authentication required'
                })
                return
            
            # Get sync status
            all_status = sync_status_service.get_all_status()
            summary = sync_status_service.get_sync_summary()
            
            self.send_json_response({
                'success': True,
                'status': all_status,
                'summary': summary
            })
            
        except Exception as e:
            print(f"Error handling sync status: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': f'Sync status error: {str(e)}'
            })
    
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
    
    def handle_set_active_connection(self):
        """Set a connection as active"""
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
            
            # Get session data
            session = session_manager.get_session(session_id)
            if not session:
                self.send_json_response({
                    'success': False,
                    'error': 'Invalid session'
                })
                return
                
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
            
            # Set the active connection
            success = connection_manager.set_active_connection(session, connection_id)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': 'Connection set as active'
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': 'Failed to set active connection'
                })
                
        except Exception as e:
            print(f"Error setting active connection: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            })
    
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
            workbook_path = os.path.join(server_dir, 'data', 'templates', 'master', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
            
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
                'AttributeBasedAdjustment': '24_AttributeBasedAdj',
                # Transaction objects
                'Order': '27_Order',
                'OrderItem': '28_OrderItem',
                'Asset': '29_Asset',
                'AssetAction': '30_AssetAction',
                'AssetActionSource': '31_AssetActionSource',
                'Contract': '32_Contract'
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
                print(f"[VIEW] Reading sheet {sheet_name} from {workbook_path}")
                print(f"[VIEW] File modified time: {os.path.getmtime(workbook_path)}")
                df = pd.read_excel(workbook_path, sheet_name=sheet_name)
                print(f"[VIEW] Successfully read {len(df)} rows")
                print(f"[VIEW] Columns: {list(df.columns[:5])}")
                print(f"[VIEW] First ID: {df.iloc[0]['Id'] if len(df) > 0 and 'Id' in df.columns else 'No ID column'}")
                
                # Remove any rows that are completely empty
                df = df.dropna(how='all')
                
                # Convert to records format
                records = df.to_dict('records')
                
                # Clean up the records (convert NaN to None/null but keep all columns)
                cleaned_records = []
                for record in records:
                    cleaned_record = {}
                    for key, value in record.items():
                        if pd.isna(value):
                            cleaned_record[key] = None  # Keep the key but with None value
                        else:
                            cleaned_record[key] = value
                    if any(v is not None for v in cleaned_record.values()):  # Only add if record has at least one non-null value
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
    
    def handle_export_workbook(self):
        """Export workbook sheet data as Excel file for upload"""
        try:
            # Parse query parameters
            from urllib.parse import parse_qs
            query_string = self.path.split('?')[1] if '?' in self.path else ''
            params = parse_qs(query_string)
            
            object_name = params.get('object', [''])[0]
            if not object_name:
                self.send_error(400, "Object name required")
                return
            
            # Import pandas and openpyxl
            import pandas as pd
            from io import BytesIO
            import os
            
            # Path to the main workbook
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workbook_path = os.path.join(server_dir, 'data', 'templates', 'master', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
            
            if not os.path.exists(workbook_path):
                self.send_error(404, "Workbook not found")
                return
            
            # Map object names to sheet names (from sync_service)
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
                'AttributeBasedAdjustment': '24_AttributeBasedAdj',
                # Transaction objects
                'Order': '27_Order',
                'OrderItem': '28_OrderItem',
                'Asset': '29_Asset',
                'AssetAction': '30_AssetAction',
                'AssetActionSource': '31_AssetActionSource',
                'Contract': '32_Contract'
            }
            
            sheet_name = sheet_mapping.get(object_name)
            if not sheet_name:
                self.send_error(400, f"No sheet mapping for {object_name}")
                return
            
            try:
                # Read the specific sheet
                df = pd.read_excel(workbook_path, sheet_name=sheet_name)
                
                # Remove empty rows
                df = df.dropna(how='all')
                
                # Create Excel file in memory with just this sheet's data
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=object_name, index=False)
                
                # Get the Excel data
                excel_data = output.getvalue()
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition', f'attachment; filename="{object_name}_upload_data.xlsx"')
                self.send_header('Content-Length', len(excel_data))
                self.end_headers()
                self.wfile.write(excel_data)
                
            except Exception as e:
                print(f"Error exporting sheet {sheet_name}: {e}")
                self.send_error(500, f"Failed to export data: {str(e)}")
            
        except Exception as e:
            print(f"Error in export workbook: {e}")
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
            print("[DEBUG] handle_get_object_counts called")
            try:
                import pandas as pd
                print("[DEBUG] pandas imported successfully")
            except ImportError as e:
                print(f"[ERROR] Failed to import pandas: {e}")
                self.send_json_response({
                    'success': False,
                    'error': 'pandas not installed',
                    'counts': {}
                })
                return
            import os
            
            # Path to the main workbook
            server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            workbook_path = os.path.join(server_dir, 'data', 'templates', 'master', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
            
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
                    'AttributeBasedAdjustment': '24_AttributeBasedAdj',
                    # Transaction objects
                    'Order': '27_Order',
                    'OrderItem': '28_OrderItem',
                    'Asset': '29_Asset',
                    'AssetAction': '30_AssetAction',
                    'AssetActionSource': '31_AssetActionSource',
                    'Contract': '32_Contract'
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
                # ProductSellingModelOption already has a sheet, so not including it
                unmapped_objects = []
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
    
    def handle_open_workbook(self):
        """Handle opening workbook in system default application"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            path = data.get('path')
            sheet = data.get('sheet')
            api_name = data.get('apiName')
            
            if not path:
                self.send_json_response({
                    'success': False,
                    'error': 'Workbook path required'
                })
                return
            
            # Check if file exists
            import os
            if not os.path.exists(path):
                self.send_json_response({
                    'success': False,
                    'error': 'Workbook file not found'
                })
                return
            
            # Open the file with the system default application
            import subprocess
            import platform
            
            print(f"[OPEN] Opening workbook: {path}")
            print(f"[OPEN] Sheet: {sheet}, API Name: {api_name}")
            
            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', path])
                elif platform.system() == 'Windows':
                    os.startfile(path)
                else:  # Linux and others
                    subprocess.run(['xdg-open', path])
                
                self.send_json_response({
                    'success': True,
                    'message': f'Opened {api_name} in spreadsheet application'
                })
                
            except Exception as e:
                print(f"[ERROR] Failed to open workbook: {e}")
                self.send_json_response({
                    'success': False,
                    'error': f'Failed to open spreadsheet: {str(e)}'
                })
                
        except Exception as e:
            print(f"Error in handle_open_workbook: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': f'Error opening workbook: {str(e)}'
            })
    
    def handle_get_product_hierarchy(self):
        """Get product hierarchy data for visualization"""
        try:
            print("[DEBUG] handle_get_product_hierarchy called")
            
            # Load deleted items list
            deleted_items = set()
            try:
                import os
                server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                deleted_items_path = os.path.join(server_dir, 'data', 'deleted_items.json')
                
                if os.path.exists(deleted_items_path):
                    with open(deleted_items_path, 'r') as f:
                        deleted_data = json.load(f)
                        # Combine all deleted IDs into a single set
                        for category in deleted_data.get('deletedItems', {}).values():
                            if isinstance(category, list):
                                deleted_items.update(category)
                    print(f"[DEBUG] Loaded {len(deleted_items)} deleted items to filter")
            except Exception as e:
                print(f"[DEBUG] Could not load deleted items: {e}")
            
            # Try to load real data from Excel first
            hierarchy_data = None
            
            try:
                import pandas as pd
                import os
                
                server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                workbook_path = os.path.join(server_dir, 'data', 'templates', 'master', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
                
                if not os.path.exists(workbook_path):
                    workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
                
                if os.path.exists(workbook_path):
                    print(f"[DEBUG] Loading hierarchy from: {workbook_path}")
                    
                    # Load the data from Excel sheets
                    catalogs_df = None
                    categories_df = None
                    products_df = None
                    component_groups_df = None
                    related_components_df = None
                    
                    try:
                        catalogs_df = pd.read_excel(workbook_path, sheet_name='11_ProductCatalog')
                        print(f"[DEBUG] Loaded {len(catalogs_df)} catalogs")
                    except Exception as e:
                        print(f"[DEBUG] Error loading catalogs: {e}")
                    
                    try:
                        categories_df = pd.read_excel(workbook_path, sheet_name='12_ProductCategory')
                        print(f"[DEBUG] Loaded {len(categories_df)} categories")
                        print(f"[DEBUG] Actual category columns from Excel: {categories_df.columns.tolist()}")
                        print(f"[DEBUG] First category: {categories_df.iloc[0].to_dict() if len(categories_df) > 0 else 'None'}")
                    except Exception as e:
                        print(f"[DEBUG] Error loading categories: {e}")
                    
                    try:
                        products_df = pd.read_excel(workbook_path, sheet_name='13_Product2')
                        print(f"[DEBUG] Loaded {len(products_df)} products")
                    except Exception as e:
                        print(f"[DEBUG] Error loading products: {e}")
                    
                    try:
                        component_groups_df = pd.read_excel(workbook_path, sheet_name='14_ProductComponentGroup')
                        print(f"[DEBUG] Loaded {len(component_groups_df)} component groups")
                    except Exception as e:
                        print(f"[DEBUG] Error loading component groups: {e}")
                    
                    try:
                        related_components_df = pd.read_excel(workbook_path, sheet_name='25_ProductRelatedComponent')
                        print(f"[DEBUG] Loaded {len(related_components_df)} related components")
                    except Exception as e:
                        print(f"[DEBUG] Error loading related components: {e}")
                    
                    # Load ProductCategoryProduct junction table
                    product_category_df = None
                    try:
                        product_category_df = pd.read_excel(workbook_path, sheet_name='26_ProductCategoryProduct')
                        print(f"[DEBUG] Loaded {len(product_category_df)} product-category mappings")
                        # Filter out rows with empty ProductCategoryId or ProductId
                        if 'ProductCategoryId' in product_category_df.columns and 'ProductId' in product_category_df.columns:
                            product_category_df = product_category_df[
                                product_category_df['ProductCategoryId'].notna() & 
                                product_category_df['ProductId'].notna()
                            ]
                            print(f"[DEBUG] After filtering: {len(product_category_df)} valid mappings")
                    except Exception as e:
                        print(f"[DEBUG] Error loading product-category mappings: {e}")
                    
                    # Build hierarchy from real data
                    # Create root node for all catalogs
                    hierarchy_data = {
                        'id': 'root',
                        'name': 'Product Catalogs',
                        'type': 'root',
                        'children': []
                    }
                    
                    if catalogs_df is not None and len(catalogs_df) > 0:
                        print(f"[DEBUG] Building hierarchy with {len(catalogs_df)} catalogs")
                        # Add each catalog as a child of root
                        for idx, catalog in catalogs_df.iterrows():
                            # Use Code or Description as the name, fallback to generic name
                            catalog_name = catalog.get('Code', '')
                            if not catalog_name or pd.isna(catalog_name):
                                catalog_name = catalog.get('Description', '')
                            if not catalog_name or pd.isna(catalog_name):
                                catalog_name = f'Catalog {idx + 1}'
                            
                            catalog_id = str(catalog.get('Id', f'catalog-{idx}'))
                            
                            # Skip deleted catalogs
                            if catalog_id in deleted_items:
                                print(f"[DEBUG] Skipping deleted catalog: {catalog_name} ({catalog_id})")
                                continue
                            catalog_node = {
                                'id': catalog_id,
                                'name': str(catalog_name),
                                'type': 'catalog',
                                'catalogId': catalog_id,  # Add catalogId property for findCatalogId function
                                'children': [],
                                # Mark items that don't have proper Salesforce IDs as not synced
                                'isSynced': catalog_id.startswith('0') or catalog_id.startswith('a')
                            }
                            
                            # Get catalog ID for filtering categories
                            catalog_id = catalog.get('Id', '')
                            
                            # Add categories that belong to this catalog
                            if categories_df is not None and catalog_id:
                                print(f"[DEBUG] Category columns: {categories_df.columns.tolist()}")
                                
                                # Check if this is a newly created catalog (has a Salesforce ID)
                                # New catalogs should not have any categories initially
                                is_new_catalog = not catalog_id.startswith('0ZS')  # ProductCatalog IDs start with 0ZS
                                
                                if is_new_catalog:
                                    print(f"[DEBUG] New catalog {catalog_name} - not assigning any categories")
                                    catalog_categories = pd.DataFrame()  # Empty dataframe
                                elif 'CatalogId' in categories_df.columns:
                                    # Check if there's a CatalogId field linking categories to catalogs
                                    catalog_categories = categories_df[categories_df['CatalogId'] == catalog_id]
                                    print(f"[DEBUG] Found {len(catalog_categories)} categories for catalog {catalog_id}")
                                else:
                                    # For existing catalogs without CatalogId field, only assign categories to known catalogs
                                    # This is a temporary measure - ideally we should have a CatalogId field
                                    if catalog_name in ['Cyber', 'Tech']:
                                        catalog_categories = categories_df
                                        print(f"[DEBUG] No CatalogId field found - assigning all categories to existing {catalog_name} catalog")
                                    else:
                                        # For other catalogs, don't assign any categories
                                        catalog_categories = pd.DataFrame()
                                        print(f"[DEBUG] No CatalogId field found - not assigning categories to {catalog_name} catalog")
                                
                                # Build a dictionary to track parent-child relationships
                                category_dict = {}
                                for _, category in catalog_categories.iterrows():
                                    cat_id = str(category.get('Id', f'cat-{_}'))
                                    
                                    # Skip deleted categories when building the dictionary
                                    if cat_id in deleted_items:
                                        print(f"[DEBUG] Skipping deleted category when building dict: {cat_id}")
                                        continue
                                    
                                    parent_id = str(category.get('ParentCategoryId', '')) if pd.notna(category.get('ParentCategoryId', '')) else None
                                    
                                    cat_node = {
                                        'id': cat_id,
                                        'name': str(category.get('Name', f'Category {_}')),
                                        'type': 'subcategory' if parent_id else 'category',
                                        'catalogId': catalog_id,  # Add catalogId property for all categories
                                        'children': [],
                                        'parent_id': parent_id
                                    }
                                    category_dict[cat_id] = cat_node
                                
                                # Build the hierarchy by connecting parents and children
                                root_categories = []
                                print(f"[DEBUG] Building category hierarchy from {len(category_dict)} categories")
                                for cat_id, cat_node in category_dict.items():
                                    parent_id = cat_node.get('parent_id')
                                    if parent_id and parent_id in category_dict:
                                        # This is a sub-category, add it to its parent
                                        category_dict[parent_id]['children'].append(cat_node)
                                    else:
                                        # This is a root category, add it to the catalog
                                        root_categories.append(cat_node)
                                    # Remove the temporary parent_id field
                                    if 'parent_id' in cat_node:
                                        del cat_node['parent_id']
                                
                                # Track which products have been assigned
                                assigned_products = set()
                                
                                # Function to add products to a category and its subcategories
                                def add_products_to_category(cat_node):
                                    cat_id = cat_node['id']
                                    
                                    # Add products in this category
                                    if products_df is not None:
                                        category_products = pd.DataFrame()
                                        
                                        # Use ProductCategoryProduct junction table if available
                                        if product_category_df is not None and len(product_category_df) > 0:
                                            # Get product IDs for this category from junction table
                                            try:
                                                category_mappings = product_category_df[product_category_df['ProductCategoryId'] == cat_id]
                                                if len(category_mappings) > 0:
                                                    product_ids = category_mappings['ProductId'].tolist()
                                                    # Only get products that haven't been assigned yet
                                                    unassigned_product_ids = [pid for pid in product_ids if pid not in assigned_products]
                                                    category_products = products_df[products_df['Id'].isin(unassigned_product_ids)]
                                            except Exception as e:
                                                print(f"[DEBUG] Error getting category mappings: {e}")
                                        # Fallback to ProductCategory__c field if junction table not available
                                        elif 'ProductCategory__c' in products_df.columns:
                                            category_products = products_df[products_df['ProductCategory__c'] == cat_id]
                                            # Filter out already assigned products
                                            category_products = category_products[~category_products['Id'].isin(assigned_products)]
                                        # If no mappings exist, assign products to categories based on name matching
                                        if len(category_products) == 0 and 'Family' in products_df.columns:
                                            # For demo purposes, assign products to lowest level categories based on name patterns
                                            # Check if this is a leaf node (no child categories)
                                            has_child_categories = any(child['type'] in ['category', 'subcategory'] for child in cat_node.get('children', []))
                                            if cat_node['type'] == 'subcategory' and not has_child_categories:
                                                # This is a leaf subcategory - assign products based on specific patterns
                                                cat_name = cat_node['name']
                                                
                                                # Create specific mappings based on category names
                                                # Only assign products to specific catalog-category combinations
                                                catalog_name = catalog_node.get('name', '')
                                                
                                                if cat_name == 'Data Classification':
                                                    # Only DCS core products and bundles go to Data Classification
                                                    # Exclude HRM, Professional Services, Support, and Training
                                                    category_products = products_df[
                                                        (products_df['Name'].str.contains('DCS', na=False)) & 
                                                        (~products_df['Name'].str.contains('HRM|Professional|Support|Training', na=False))
                                                    ]
                                                    # Filter out already assigned products
                                                    category_products = category_products[~category_products['Id'].isin(assigned_products)]
                                                    print(f"[DEBUG] Assigning {len(category_products)} DCS products to {cat_name} in {catalog_name}")
                                                elif cat_name == 'Human Risk Management':
                                                    # Check if this is the L2 node by checking if ID matches the L2 HRM ID
                                                    # L2 HRM ID is 0ZGdp0000000AyfGAE
                                                    if cat_id == '0ZGdp0000000AyfGAE':
                                                        # This is the L2 node - assign ONLY HRM products (9 total, including 3 bundles)
                                                        # Do NOT include Professional Services, Support, or Training
                                                        category_products = products_df[
                                                            products_df['Name'].str.contains('HRM', na=False)
                                                        ]
                                                        # Filter out already assigned products
                                                        category_products = category_products[~category_products['Id'].isin(assigned_products)]
                                                        print(f"[DEBUG] Assigning {len(category_products)} HRM products to {cat_name} (L2) in {catalog_name}")
                                                    else:
                                                        # This is the L1 node - don't assign products directly
                                                        category_products = pd.DataFrame()
                                                        print(f"[DEBUG] Skipping product assignment to {cat_name} (L1) in {catalog_name}")
                                                # Don't assign products to other catalog-category combinations
                                        
                                        for _, product in category_products.iterrows():
                                            prod_id = str(product.get('Id', f'prod-{_}'))
                                            
                                            # Skip deleted products
                                            if prod_id in deleted_items:
                                                continue
                                                
                                            prod_node = {
                                                'id': prod_id,
                                                'name': str(product.get('Name', f'Product {_}')),
                                                'type': 'product',
                                                'productCode': str(product.get('ProductCode', '')),
                                                'isActive': bool(product.get('IsActive', True)),
                                                'price': str(product.get('UnitPrice', ''))
                                            }
                                            
                                            # Check if this product is a bundle/parent
                                            # Since the Excel template is missing ChildProductId, we'll use a hardcoded mapping
                                            # based on the CSV data we found
                                            bundle_mappings = {
                                                '01tdp000006JEGlAAO': [  # DCS Essentials Bundle (updated ID)
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 10},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 20},
                                                    {'id': '01tdp000006HfprAAC', 'name': 'DCS Getting Started Package', 'seq': 30}
                                                ],
                                                '01tdp000006JEGjAAO': [  # DCS Advanced Bundle (updated ID)
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 40},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 50},
                                                    {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 60},
                                                    {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 70},
                                                    {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 80, 'required': False}
                                                ],
                                                '01tdp000006JEGkAAO': [  # DCS Elite Bundle (updated ID)
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 90},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 100},
                                                    {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 110},
                                                    {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 120},
                                                    {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 130},
                                                    {'id': '01tdp000006HfplAAC', 'name': 'Unlimited Classification', 'seq': 140},
                                                    {'id': '01tdp000006HfpqAAC', 'name': 'Software Development Kit', 'seq': 150, 'required': False}
                                                ],
                                                # HRM Bundles
                                                '01tdp000006iLGbAAM': [  # HRM Essentials Bundle
                                                    {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                                    {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20}
                                                ],
                                                '01tdp000006m0jpAAA': [  # HRM Advanced Bundle
                                                    {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                                    {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20},
                                                    {'id': '01tdp000006iLGeAAM', 'name': 'HRM Phishing Simulation', 'seq': 30},
                                                    {'id': '01tdp000006iLGfAAM', 'name': 'HRM Advanced Analytics', 'seq': 40}
                                                ],
                                                '01tdp000006m14nAAA': [  # HRM Elite Bundle
                                                    {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                                    {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20},
                                                    {'id': '01tdp000006iLGeAAM', 'name': 'HRM Phishing Simulation', 'seq': 30},
                                                    {'id': '01tdp000006iLGfAAM', 'name': 'HRM Advanced Analytics', 'seq': 40},
                                                    {'id': '01tdp000006iLGgAAM', 'name': 'HRM Executive Dashboard', 'seq': 50},
                                                    {'id': '01tdp000006iLGhAAM', 'name': 'HRM Custom Campaigns', 'seq': 60}
                                                ]
                                            }
                                            
                                            product_id = str(product.get('Id', ''))
                                            if product_id in bundle_mappings:
                                                prod_node['children'] = []
                                                prod_node['isBundle'] = True
                                                
                                                for comp in bundle_mappings[product_id]:
                                                    # Try to find the actual product for more details
                                                    comp_product = None
                                                    if products_df is not None:
                                                        comp_products = products_df[products_df['Id'] == comp['id']]
                                                        if len(comp_products) > 0:
                                                            comp_product = comp_products.iloc[0]
                                                    
                                                    component_node = {
                                                        'id': comp['id'],
                                                        'name': comp_product.get('Name', comp['name']) if comp_product is not None else comp['name'],
                                                        'type': 'component',
                                                        'quantity': '1',
                                                        'isRequired': comp.get('required', True),
                                                        'sequence': comp['seq'],
                                                        'productCode': str(comp_product.get('ProductCode', '')) if comp_product is not None else ''
                                                    }
                                                    prod_node['children'].append(component_node)
                                                
                                                # Sort components by sequence
                                                prod_node['children'].sort(key=lambda x: x.get('sequence', 0))
                                            
                                            cat_node['children'].append(prod_node)
                                            # Mark this product as assigned
                                            assigned_products.add(prod_node['id'])
                                    
                                    # Recursively process sub-categories
                                    for child_cat in cat_node['children']:
                                        if child_cat['type'] in ['category', 'subcategory']:
                                            add_products_to_category(child_cat)
                                
                                # Process all root categories
                                print(f"[DEBUG] Found {len(root_categories)} root categories for catalog {catalog_name}")
                                for cat_node in root_categories:
                                    add_products_to_category(cat_node)
                                    catalog_node['children'].append(cat_node)
                                print(f"[DEBUG] Catalog {catalog_name} has {len(catalog_node['children'])} children after adding categories")
                            
                            hierarchy_data['children'].append(catalog_node)
                    
                    # If no catalogs but have categories, create a default catalog
                    elif categories_df is not None and len(categories_df) > 0:
                        default_catalog = {
                            'id': 'default-catalog',
                            'name': 'Default Catalog',
                            'type': 'catalog',
                            'catalogId': 'default-catalog',  # Add catalogId for default catalog
                            'children': []
                        }
                        
                        # Build a dictionary to track parent-child relationships
                        category_dict = {}
                        for _, category in categories_df.iterrows():
                            cat_id = str(category.get('Id', f'cat-{_}'))
                            
                            # Skip deleted categories when building the dictionary
                            if cat_id in deleted_items:
                                print(f"[DEBUG] Skipping deleted category when building dict: {cat_id}")
                                continue
                                
                            parent_id = str(category.get('ParentCategoryId', '')) if pd.notna(category.get('ParentCategoryId', '')) else None
                            
                            cat_node = {
                                'id': cat_id,
                                'name': str(category.get('Name', f'Category {_}')),
                                'type': 'subcategory' if parent_id else 'category',
                                'catalogId': 'default-catalog',  # Add catalogId for categories in default catalog
                                'children': [],
                                'parent_id': parent_id
                            }
                            category_dict[cat_id] = cat_node
                        
                        # Build the hierarchy by connecting parents and children
                        root_categories = []
                        for cat_id, cat_node in category_dict.items():
                            parent_id = cat_node.get('parent_id')
                            if parent_id and parent_id in category_dict:
                                # This is a sub-category, add it to its parent
                                category_dict[parent_id]['children'].append(cat_node)
                            else:
                                # This is a root category
                                root_categories.append(cat_node)
                            # Remove the temporary parent_id field
                            if 'parent_id' in cat_node:
                                del cat_node['parent_id']
                        
                        # Track which products have been assigned in default catalog
                        assigned_products_default = set()
                        
                        # Function to add products to a category and its subcategories
                        def add_products_to_category_default(cat_node):
                            cat_id = cat_node['id']
                            
                            # Add products in this category
                            if products_df is not None:
                                category_products = pd.DataFrame()
                                
                                # Use ProductCategoryProduct junction table if available
                                if product_category_df is not None and len(product_category_df) > 0:
                                    # Get product IDs for this category from junction table
                                    try:
                                        category_mappings = product_category_df[product_category_df['ProductCategoryId'] == cat_id]
                                        if len(category_mappings) > 0:
                                            product_ids = category_mappings['ProductId'].tolist()
                                            category_products = products_df[products_df['Id'].isin(product_ids)]
                                    except Exception as e:
                                        print(f"[DEBUG] Error in default catalog product mapping: {e}")
                                # Fallback to ProductCategory__c field if junction table not available
                                elif 'ProductCategory__c' in products_df.columns:
                                    category_products = products_df[products_df['ProductCategory__c'] == cat_id]
                                # If no mappings exist, assign products to categories based on name matching
                                if len(category_products) == 0 and 'Family' in products_df.columns:
                                    # For demo purposes, assign products to lowest level categories based on name patterns
                                    # Check if this is a leaf node (no child categories)
                                    has_child_categories = any(child['type'] in ['category', 'subcategory'] for child in cat_node.get('children', []))
                                    if cat_node['type'] == 'subcategory' and not has_child_categories:
                                        # This is a leaf subcategory - assign products based on specific patterns
                                        cat_name = cat_node['name']
                                        
                                        # Create specific mappings based on category names
                                        # For default catalog, assign all products to Data Classification
                                        if cat_name == 'Data Classification':
                                            # All products go to Data Classification in default catalog
                                            category_products = products_df
                                            # Filter out already assigned products
                                            category_products = category_products[~category_products['Id'].isin(assigned_products_default)]
                                            print(f"[DEBUG] Assigning {len(category_products)} products to {cat_name} in default catalog")
                                        # Don't assign products to other categories in default catalog
                                
                                for _, product in category_products.iterrows():
                                    prod_id = str(product.get('Id', f'prod-{_}'))
                                    
                                    # Skip deleted products
                                    if prod_id in deleted_items:
                                        continue
                                        
                                    prod_node = {
                                        'id': prod_id,
                                        'name': str(product.get('Name', f'Product {_}')),
                                        'type': 'product',
                                        'productCode': str(product.get('ProductCode', '')),
                                        'isActive': bool(product.get('IsActive', True)),
                                        'price': str(product.get('UnitPrice', ''))
                                    }
                                    
                                    # Check if this product is a bundle/parent
                                    # Since the Excel template is missing ChildProductId, we'll use a hardcoded mapping
                                    # based on the CSV data we found
                                    bundle_mappings = {
                                        '01tdp000006JEGlAAO': [  # DCS Essentials Bundle (updated ID)
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 10},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 20},
                                            {'id': '01tdp000006HfprAAC', 'name': 'DCS Getting Started Package', 'seq': 30}
                                        ],
                                        '01tdp000006JEGjAAO': [  # DCS Advanced Bundle (updated ID)
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 40},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 50},
                                            {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 60},
                                            {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 70},
                                            {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 80, 'required': False}
                                        ],
                                        '01tdp000006JEGkAAO': [  # DCS Elite Bundle (updated ID)
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 90},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 100},
                                            {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 110},
                                            {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 120},
                                            {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 130},
                                            {'id': '01tdp000006HfplAAC', 'name': 'Unlimited Classification', 'seq': 140},
                                            {'id': '01tdp000006HfpqAAC', 'name': 'Software Development Kit', 'seq': 150, 'required': False}
                                        ],
                                        # HRM Bundles
                                        '01tdp000006iLGbAAM': [  # HRM Essentials Bundle
                                            {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                            {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20}
                                        ],
                                        '01tdp000006m0jpAAA': [  # HRM Advanced Bundle
                                            {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                            {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20},
                                            {'id': '01tdp000006iLGeAAM', 'name': 'HRM Phishing Simulation', 'seq': 30},
                                            {'id': '01tdp000006iLGfAAM', 'name': 'HRM Advanced Analytics', 'seq': 40}
                                        ],
                                        '01tdp000006m14nAAA': [  # HRM Elite Bundle
                                            {'id': '01tdp000006iLGcAAM', 'name': 'HRM Core Module', 'seq': 10},
                                            {'id': '01tdp000006iLGdAAM', 'name': 'HRM Basic Training', 'seq': 20},
                                            {'id': '01tdp000006iLGeAAM', 'name': 'HRM Phishing Simulation', 'seq': 30},
                                            {'id': '01tdp000006iLGfAAM', 'name': 'HRM Advanced Analytics', 'seq': 40},
                                            {'id': '01tdp000006iLGgAAM', 'name': 'HRM Executive Dashboard', 'seq': 50},
                                            {'id': '01tdp000006iLGhAAM', 'name': 'HRM Custom Campaigns', 'seq': 60}
                                        ]
                                    }
                                    
                                    product_id = str(product.get('Id', ''))
                                    if product_id in bundle_mappings:
                                        prod_node['children'] = []
                                        prod_node['isBundle'] = True
                                        
                                        for comp in bundle_mappings[product_id]:
                                            # Try to find the actual product for more details
                                            comp_product = None
                                            if products_df is not None:
                                                comp_products = products_df[products_df['Id'] == comp['id']]
                                                if len(comp_products) > 0:
                                                    comp_product = comp_products.iloc[0]
                                            
                                            component_node = {
                                                'id': comp['id'],
                                                'name': comp_product.get('Name', comp['name']) if comp_product is not None else comp['name'],
                                                'type': 'component',
                                                'quantity': '1',
                                                'isRequired': comp.get('required', True),
                                                'sequence': comp['seq'],
                                                'productCode': str(comp_product.get('ProductCode', '')) if comp_product is not None else ''
                                            }
                                            prod_node['children'].append(component_node)
                                        
                                        # Sort components by sequence
                                        prod_node['children'].sort(key=lambda x: x.get('sequence', 0))
                                    
                                    cat_node['children'].append(prod_node)
                                    # Mark this product as assigned
                                    assigned_products_default.add(prod_node['id'])
                            
                            # Recursively process sub-categories
                            for child_cat in cat_node['children']:
                                if child_cat['type'] in ['category', 'subcategory']:
                                    add_products_to_category_default(child_cat)
                        
                        # Process all root categories
                        for cat_node in root_categories:
                            add_products_to_category_default(cat_node)
                            default_catalog['children'].append(cat_node)
                        
                        hierarchy_data['children'].append(default_catalog)
                    
                    # If we have some data, add stats
                    if hierarchy_data:
                        hierarchy_data['stats'] = {
                            'catalogs': len(catalogs_df) if catalogs_df is not None else 0,
                            'categories': len(categories_df) if categories_df is not None else 0,
                            'products': len(products_df) if products_df is not None else 0
                        }
                        print(f"[DEBUG] Real hierarchy built successfully with {len(hierarchy_data.get('children', []))} root items")
                
            except Exception as e:
                print(f"[DEBUG] Error loading real data: {e}")
            
            # If no real data loaded, use sample data
            if not hierarchy_data or (hierarchy_data and 'children' in hierarchy_data and len(hierarchy_data['children']) == 0):
                print("[DEBUG] Using sample data as fallback")
                hierarchy_data = {
                'id': 'catalog-1',
                'name': 'Revenue Cloud Products',
                'type': 'catalog',
                'catalogId': 'catalog-1',  # Add catalogId for sample catalog
                'children': [
                    {
                        'id': 'cat-1',
                        'name': 'Software Licenses',
                        'type': 'category',
                        'catalogId': 'catalog-1',  # Add catalogId for sample category
                        'children': [
                            {
                                'id': 'subcat-1',
                                'name': 'Enterprise',
                                'type': 'subcategory',
                                'children': [
                                    {
                                        'id': 'prod-1',
                                        'name': 'Revenue Cloud Enterprise',
                                        'type': 'product',
                                        'price': '$5,000/month',
                                        'productCode': 'RCE-001',
                                        'isActive': True,
                                        'children': [
                                            {
                                                'id': 'var-1',
                                                'name': '100 Users',
                                                'type': 'variant',
                                                'price': '$5,000/month',
                                                'sku': 'RCE-001-100'
                                            },
                                            {
                                                'id': 'var-2',
                                                'name': '500 Users',
                                                'type': 'variant',
                                                'price': '$20,000/month',
                                                'sku': 'RCE-001-500'
                                            }
                                        ]
                                    },
                                    {
                                        'id': 'prod-2',
                                        'name': 'CPQ Enterprise',
                                        'type': 'product',
                                        'price': '$3,000/month',
                                        'productCode': 'CPQE-001',
                                        'isActive': True
                                    }
                                ]
                            },
                            {
                                'id': 'subcat-2',
                                'name': 'Professional',
                                'type': 'subcategory',
                                'children': [
                                    {
                                        'id': 'prod-3',
                                        'name': 'Revenue Cloud Professional',
                                        'type': 'product',
                                        'price': '$1,500/month',
                                        'productCode': 'RCP-001',
                                        'isActive': True
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'id': 'cat-2',
                        'name': 'Services',
                        'type': 'category',
                        'catalogId': 'catalog-1',  # Add catalogId for sample category
                        'children': [
                            {
                                'id': 'subcat-3',
                                'name': 'Implementation',
                                'type': 'subcategory',
                                'children': [
                                    {
                                        'id': 'prod-4',
                                        'name': 'Standard Implementation',
                                        'type': 'product',
                                        'price': '$50,000',
                                        'productCode': 'IMPL-STD',
                                        'isActive': True
                                    },
                                    {
                                        'id': 'prod-5',
                                        'name': 'Enterprise Implementation',
                                        'type': 'product',
                                        'price': '$150,000',
                                        'productCode': 'IMPL-ENT',
                                        'isActive': True
                                    }
                                ]
                            },
                            {
                                'id': 'subcat-4',
                                'name': 'Training',
                                'type': 'subcategory',
                                'children': [
                                    {
                                        'id': 'prod-6',
                                        'name': 'Admin Training',
                                        'type': 'product',
                                        'price': '$5,000',
                                        'productCode': 'TRN-ADM',
                                        'isActive': True
                                    },
                                    {
                                        'id': 'prod-7',
                                        'name': 'End User Training',
                                        'type': 'product',
                                        'price': '$2,500',
                                        'productCode': 'TRN-USR',
                                        'isActive': True
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            # Get stats from actual data if available
            try:
                import pandas as pd
                import os
                
                server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                workbook_path = os.path.join(server_dir, 'data', 'templates', 'master', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
                
                if not os.path.exists(workbook_path):
                    workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template.xlsx')
                
                if os.path.exists(workbook_path):
                    # Try to enhance with real data counts
                    stats = {}
                    
                    # ProductCatalog count
                    try:
                        df = pd.read_excel(workbook_path, sheet_name='11_ProductCatalog')
                        stats['catalogs'] = len(df)
                    except:
                        stats['catalogs'] = 1
                    
                    # ProductCategory count
                    try:
                        df = pd.read_excel(workbook_path, sheet_name='12_ProductCategory')
                        stats['categories'] = len(df)
                    except:
                        stats['categories'] = 2
                    
                    # Product2 count
                    try:
                        df = pd.read_excel(workbook_path, sheet_name='13_Product2')
                        stats['products'] = len(df)
                    except:
                        stats['products'] = 7
                    
                    hierarchy_data['stats'] = stats
                
            except Exception as e:
                print(f"Error getting real stats: {e}")
            
            print(f"[DEBUG] Sending hierarchy response with {len(hierarchy_data.get('children', [])) if hierarchy_data else 0} children")
            print(f"[DEBUG] Hierarchy type: {hierarchy_data.get('type') if hierarchy_data else 'None'}")
            
            self.send_json_response({
                'success': True,
                'hierarchy': hierarchy_data
            })
            
        except Exception as e:
            print(f"Error getting product hierarchy: {e}")
            self.send_error(500)
    
    def handle_get_edit_permissions(self):
        """Handle GET /api/edit/permissions"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            user_id = user_session.get('user_id', 'default_user')
            
            # Get org_id from query params
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?')[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
                        
            org_id = query_params.get('org_id', user_session.get('active_connection_id'))
            
            if not org_id:
                self.send_json_response({'error': 'No organization selected'}, 400)
                return
                
            # Get permissions
            permissions = edit_service.get_user_permissions_details(user_id, org_id)
            self.send_json_response(permissions)
            
        except Exception as e:
            print(f"Error getting edit permissions: {e}")
            self.send_error(500)
            
    def handle_get_field_config(self):
        """Handle GET /api/edit/field-config"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            
            # Get query params
            query_params = {}
            if '?' in self.path:
                query_string = self.path.split('?')[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
                        
            org_id = query_params.get('org_id', user_session.get('active_connection_id'))
            object_type = query_params.get('object_type', 'Product2')
            
            if not org_id:
                self.send_json_response({'error': 'No organization selected'}, 400)
                return
                
            # Get field configuration
            fields = edit_service.get_field_configuration(org_id, object_type)
            
            self.send_json_response({
                'org_id': org_id,
                'object_type': object_type,
                'fields': fields,
                'total': len(fields)
            })
            
        except Exception as e:
            print(f"Error getting field config: {e}")
            self.send_error(500)
            
    def handle_update_edit_permissions(self):
        """Handle POST /api/edit/permissions"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            user_id = user_session.get('user_id', 'default_user')
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            target_user_id = data.get('user_id')
            org_id = data.get('org_id', user_session.get('active_connection_id'))
            permission_level = data.get('permission_level')
            
            # Check if user is admin
            if not edit_service.check_permission(user_id, org_id, 'admin'):
                self.send_json_response({'error': 'Admin permission required'}, 403)
                return
                
            # Validate inputs
            if not all([target_user_id, org_id, permission_level]):
                self.send_json_response({'error': 'Missing required fields'}, 400)
                return
                
            # Update permission
            edit_service.update_user_permission(target_user_id, org_id, permission_level, user_id)
            
            # Log audit
            edit_service.log_audit_action(
                user_id, org_id, 'update_permission', 'edit_permissions', target_user_id,
                {'target_user': target_user_id, 'permission_level': permission_level},
                {'ip_address': self.client_address[0], 'session_id': session_id}
            )
            
            self.send_json_response({
                'success': True,
                'message': f'Permission updated for user {target_user_id}'
            })
            
        except Exception as e:
            print(f"Error updating permissions: {e}")
            self.send_error(500)
            
    def handle_update_field_config(self):
        """Handle POST /api/edit/field-config"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            user_id = user_session.get('user_id', 'default_user')
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            org_id = data.get('org_id', user_session.get('active_connection_id'))
            object_type = data.get('object_type', 'Product2')
            fields = data.get('fields', [])
            
            # Check if user is admin
            if not edit_service.check_permission(user_id, org_id, 'admin'):
                self.send_json_response({'error': 'Admin permission required'}, 403)
                return
                
            if not org_id:
                self.send_json_response({'error': 'No organization selected'}, 400)
                return
                
            # Update configuration
            edit_service.update_field_configuration(org_id, object_type, fields)
            
            # Log audit
            edit_service.log_audit_action(
                user_id, org_id, 'update_field_config', 'field_config', object_type,
                {'object_type': object_type, 'field_count': len(fields)},
                {'ip_address': self.client_address[0], 'session_id': session_id}
            )
            
            self.send_json_response({
                'success': True,
                'message': f'Field configuration updated for {object_type}',
                'fields_configured': len(fields)
            })
            
        except Exception as e:
            print(f"Error updating field config: {e}")
            self.send_error(500)
    
    def handle_validate_changes(self):
        """Handle POST /api/edit/changes/validate"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            changes = data.get('changes', [])
            deletions = data.get('deletions', [])
            
            # Basic validation
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check for any obvious issues
            for change in changes:
                if not change.get('nodeId'):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Missing nodeId in change: {change}")
            
            for deletion in deletions:
                if not deletion.get('nodeId'):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Missing nodeId in deletion: {deletion}")
                    
                # Warn about deletions with children
                if deletion.get('deleteChildren'):
                    validation_result['warnings'].append(
                        f"Node {deletion.get('nodeName')} and all its children will be deleted"
                    )
            
            self.send_json_response(validation_result)
            
        except Exception as e:
            print(f"Error validating changes: {e}")
            self.send_error(500)
    
    def handle_commit_changes(self):
        """Handle POST /api/edit/changes/commit"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            user_id = user_session.get('user_id', 'default_user')
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            changes = data.get('changes', [])
            deletions = data.get('deletions', [])
            additions = data.get('additions', [])
            org_id = data.get('org_id', user_session.get('active_connection_id'))
            
            if not org_id:
                self.send_json_response({'error': 'No organization selected'}, 400)
                return
            
            # Get active connection
            connection = connection_manager.get_active_connection(user_session)
            if not connection:
                self.send_json_response({
                    'success': False,
                    'error': 'No active Salesforce connection'
                })
                return
            
            connection_alias = connection.get('cli_alias')
            
            # Import SalesforceService
            from app.services.salesforce_service import SalesforceService
            import os
            salesforce_service = SalesforceService()
            
            # Process results
            results = {
                'success': True,
                'changes_processed': 0,
                'deletions_processed': 0,
                'additions_processed': 0,
                'deletion_details': [],
                'addition_details': [],
                'errors': []
            }
            
            # Log to change history
            from datetime import datetime
            batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Process field changes first
            print(f"[COMMIT] Processing {len(changes)} field changes")
            for change in changes:
                try:
                    node_id = change.get('nodeId')
                    node_type = change.get('nodeType', 'unknown')
                    field_name = change.get('fieldName')
                    new_value = change.get('newValue')
                    
                    # Determine object name from node type
                    object_name = 'Product2' if node_type == 'product' else 'Product2'
                    
                    # Update the record
                    success, result = salesforce_service.update_record(
                        object_name, 
                        node_id, 
                        {field_name: new_value},
                        connection_alias
                    )
                    
                    if success:
                        results['changes_processed'] += 1
                        # Log successful change
                        edit_service.log_change_history(
                            user_id, org_id, node_id, node_type, 'update',
                            change, 'committed', batch_id
                        )
                    else:
                        results['errors'].append(f"Failed to update {node_id}: {result}")
                        # Log failed change
                        edit_service.log_change_history(
                            user_id, org_id, node_id, node_type, 'update',
                            change, 'failed', batch_id
                        )
                except Exception as e:
                    error_msg = f"Error updating {change.get('nodeId')}: {str(e)}"
                    print(f"[COMMIT] {error_msg}")
                    results['errors'].append(error_msg)
            
            # Process deletions
            print(f"[COMMIT] Processing {len(deletions)} deletions")
            for deletion in deletions:
                try:
                    node_id = deletion.get('nodeId')
                    node_type = deletion.get('nodeType', 'product')
                    delete_children = deletion.get('deleteChildren', False)
                    new_parent_id = deletion.get('newParentId')
                    
                    # Use unified delete method
                    success, result = salesforce_service.delete_with_children(
                        node_id, node_type, delete_children, new_parent_id, connection_alias
                    )
                    
                    if success:
                        results['deletions_processed'] += 1
                        results['deletion_details'].append(result)
                        # Log successful deletion
                        edit_service.log_change_history(
                            user_id, org_id, node_id, node_type, 'delete',
                            deletion, 'committed', batch_id
                        )
                        
                        # Track deleted item to filter from Excel data
                        try:
                            deleted_items_path = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'data', 'deleted_items.json'
                            )
                            
                            # Load existing deleted items
                            deleted_data = {'deletedItems': {'catalogs': [], 'categories': [], 'products': []}}
                            if os.path.exists(deleted_items_path):
                                with open(deleted_items_path, 'r') as f:
                                    deleted_data = json.load(f)
                            
                            # Add this item to the appropriate list
                            if node_type == 'catalog' and node_id not in deleted_data['deletedItems']['catalogs']:
                                deleted_data['deletedItems']['catalogs'].append(node_id)
                            elif node_type in ['category', 'subcategory'] and node_id not in deleted_data['deletedItems']['categories']:
                                deleted_data['deletedItems']['categories'].append(node_id)
                            elif node_type == 'product' and node_id not in deleted_data['deletedItems']['products']:
                                deleted_data['deletedItems']['products'].append(node_id)
                            
                            # Update timestamp
                            deleted_data['lastUpdated'] = datetime.now().isoformat()
                            
                            # Save back to file
                            with open(deleted_items_path, 'w') as f:
                                json.dump(deleted_data, f, indent=2)
                                
                            print(f"[COMMIT] Added {node_id} to deleted items tracking")
                        except Exception as e:
                            print(f"[COMMIT] Warning: Could not track deleted item: {e}")
                    else:
                        results['errors'].append(f"Failed to delete {node_id}: {result}")
                        # Log failed deletion
                        edit_service.log_change_history(
                            user_id, org_id, node_id, node_type, 'delete',
                            deletion, 'failed', batch_id
                        )
                except Exception as e:
                    error_msg = f"Error deleting {deletion.get('nodeId')}: {str(e)}"
                    print(f"[COMMIT] {error_msg}")
                    results['errors'].append(error_msg)
            
            # Process additions
            print(f"[COMMIT] Processing {len(additions)} additions")
            for addition in additions:
                try:
                    print(f"[COMMIT] Addition data: {addition}")
                    node_id = addition.get('nodeId')
                    node_type = addition.get('type', 'unknown')
                    print(f"[COMMIT] Node ID: {node_id}, Type: {node_type}")
                    
                    # The addition object now has the data directly at the top level
                    # Determine object name and data from node type
                    if node_type == 'catalog':
                        object_name = 'ProductCatalog'
                        record_data = {
                            'Name': addition.get('name'),
                            'Code': addition.get('code', addition.get('name', '').replace(' ', '_')),  # Use provided code or generate from name
                            'Description': addition.get('description', ''),
                            'CatalogType': addition.get('catalogType', 'Sales'),  # Use provided type or default to Sales
                        }
                        
                        # Handle dates - convert from HTML datetime-local format to Salesforce format
                        if addition.get('effectiveStartDate'):
                            # Convert from YYYY-MM-DDTHH:MM to Salesforce format
                            start_date = addition.get('effectiveStartDate').replace('T', ' ') + ':00'
                            record_data['EffectiveStartDate'] = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.000+0000')
                        else:
                            # Default to current date if not provided
                            record_data['EffectiveStartDate'] = datetime.now().strftime('%Y-%m-%dT00:00:00.000+0000')
                            
                        if addition.get('effectiveEndDate'):
                            # Convert from YYYY-MM-DDTHH:MM to Salesforce format
                            end_date = addition.get('effectiveEndDate').replace('T', ' ') + ':00'
                            record_data['EffectiveEndDate'] = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.000+0000')
                        # Note: IsActive might not be a field on ProductCatalog
                    elif node_type == 'category':
                        object_name = 'ProductCategory'
                        record_data = {
                            'Name': addition.get('name'),
                            'Description': addition.get('description', ''),
                            'CatalogId': addition.get('catalogId'),  # Required field!
                            'ParentCategoryId': addition.get('parentCategoryId'),
                            'IsNavigational': addition.get('isNavigational', False),  # Required field with default
                            'SortOrder': addition.get('sortOrder') if addition.get('sortOrder') is not None else None,
                            'Code': addition.get('code', ''),
                            'ExternalId__c': addition.get('externalId', '')
                        }
                        # Remove None values to avoid Salesforce API errors
                        record_data = {k: v for k, v in record_data.items() if v is not None}
                        print(f"[COMMIT] Creating ProductCategory with data: {record_data}")
                    elif node_type == 'product':
                        object_name = 'Product2'
                        record_data = {
                            'Name': addition.get('name'),
                            'Description': addition.get('description', ''),
                            'IsActive': addition.get('isActive', True),
                            'ProductCode': addition.get('productCode', '')
                        }
                    else:
                        results['errors'].append(f"Unsupported node type for addition: {node_type}")
                        continue
                    
                    # Create the record
                    success, result = salesforce_service.create_record(
                        object_name,
                        record_data,
                        connection_alias
                    )
                    
                    if success:
                        results['additions_processed'] += 1
                        results['addition_details'].append({
                            'temp_id': node_id,
                            'real_id': result.get('id'),
                            'type': node_type,
                            'name': addition.get('name')
                        })
                        # Log successful addition
                        edit_service.log_change_history(
                            user_id, org_id, result.get('id'), node_type, 'create',
                            addition, 'committed', batch_id
                        )
                    else:
                        results['errors'].append(f"Failed to create {node_type}: {result}")
                        # Log failed addition
                        edit_service.log_change_history(
                            user_id, org_id, node_id, node_type, 'create',
                            addition, 'failed', batch_id
                        )
                except Exception as e:
                    error_msg = f"Error creating {addition.get('type')}: {str(e)}"
                    print(f"[COMMIT] {error_msg}")
                    results['errors'].append(error_msg)
            
            # Set success based on whether there were errors
            results['success'] = len(results['errors']) == 0
            
            print(f"[COMMIT] Commit complete. Changes: {results['changes_processed']}, Additions: {results['additions_processed']}, Deletions: {results['deletions_processed']}, Errors: {len(results['errors'])}")
            
            self.send_json_response(results)
            
        except Exception as e:
            print(f"Error committing changes: {e}")
            self.send_json_response({
                'success': False,
                'error': f'Commit error: {str(e)}'
            })
    
    def handle_get_change_history(self):
        """Handle GET /api/edit/changes/history"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            
            # Parse query params
            from urllib.parse import parse_qs
            query_string = urlparse(self.path).query
            params = parse_qs(query_string)
            
            org_id = params.get('org_id', [user_session.get('active_connection_id')])[0]
            limit = int(params.get('limit', ['50'])[0])
            
            # Get history
            history = edit_service.get_change_history(org_id, limit)
            
            self.send_json_response({
                'history': history,
                'total': len(history)
            })
            
        except Exception as e:
            print(f"Error getting change history: {e}")
            self.send_error(500)
    
    def handle_add_hierarchy_node(self):
        """Handle POST /api/hierarchy/add - Add new node to hierarchy"""
        try:
            # Check auth
            cookie = self.headers.get('Cookie', '')
            session_id = session_manager.get_session_cookie(cookie)
            if not session_id or not session_manager.is_session_valid(session_id):
                self.send_error(401)
                return
                
            user_session = session_manager.get_session(session_id)
            user_id = user_session.get('user_id', 'default_user')
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            node_type = data.get('type')
            parent_id = data.get('parent_id')
            node_data = data.get('data', {})
            org_id = data.get('org_id', user_session.get('active_connection_id'))
            
            if not node_type or not node_data:
                self.send_json_response({'error': 'Missing required fields'}, 400)
                return
            
            if not org_id:
                self.send_json_response({'error': 'No organization selected'}, 400)
                return
            
            # Get active connection
            connection = connection_manager.get_active_connection(user_session)
            if not connection:
                self.send_json_response({
                    'success': False,
                    'error': 'No active Salesforce connection'
                })
                return
            
            connection_alias = connection.get('cli_alias')
            
            # Import SalesforceService
            from app.services.salesforce_service import SalesforceService
            salesforce_service = SalesforceService()
            
            # Handle based on node type
            if node_type == 'catalog':
                # Create ProductCatalog record
                catalog_data = {
                    'Name': node_data.get('name'),
                    'Description': node_data.get('description', ''),
                    'IsActive': node_data.get('isActive', True)
                }
                
                success, result = salesforce_service.create_record(
                    'ProductCatalog',
                    catalog_data,
                    connection_alias
                )
                
                if success:
                    # Log successful creation
                    from datetime import datetime
                    batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
                    edit_service.log_change_history(
                        user_id, org_id, result.get('id'), 'catalog', 'create',
                        catalog_data, 'committed', batch_id
                    )
                    
                    self.send_json_response({
                        'success': True,
                        'id': result.get('id'),
                        'message': f"Created catalog: {node_data.get('name')}"
                    })
                else:
                    self.send_json_response({
                        'success': False,
                        'error': f"Failed to create catalog: {result}"
                    })
            
            elif node_type == 'category':
                # TODO: Implement category creation
                self.send_json_response({
                    'success': False,
                    'error': 'Category creation not yet implemented'
                })
            
            elif node_type == 'product':
                # TODO: Implement product creation
                self.send_json_response({
                    'success': False,
                    'error': 'Product creation not yet implemented'
                })
            
            elif node_type == 'component':
                # TODO: Implement component creation
                self.send_json_response({
                    'success': False,
                    'error': 'Component creation not yet implemented'
                })
            
            else:
                self.send_json_response({
                    'success': False,
                    'error': f'Unknown node type: {node_type}'
                })
                
        except Exception as e:
            print(f"[DEBUG] Error in handle_add_hierarchy_node: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            })
    
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
    
    print(f"[DEBUG] Creating HTTPServer on {HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), SimpleHandler)
    print(f"[DEBUG] Server created successfully")
    
    try:
        print(f"[DEBUG] Starting server.serve_forever()")
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