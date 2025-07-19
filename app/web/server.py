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
            elif path == '/api/sync-status':
                self.handle_sync_status()
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
                    workbook_path = str(DATA_ROOT / 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
                
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
            workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
            
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
    
    def handle_get_product_hierarchy(self):
        """Get product hierarchy data for visualization"""
        try:
            print("[DEBUG] handle_get_product_hierarchy called")
            
            # Try to load real data from Excel first
            hierarchy_data = None
            
            try:
                import pandas as pd
                import os
                
                server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
                
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
                    
                    # Build hierarchy from real data
                    # Create root node for all catalogs
                    hierarchy_data = {
                        'id': 'root',
                        'name': 'Product Catalogs',
                        'type': 'root',
                        'children': []
                    }
                    
                    if catalogs_df is not None and len(catalogs_df) > 0:
                        # Add each catalog as a child of root
                        for idx, catalog in catalogs_df.iterrows():
                            # Use Code or Description as the name, fallback to generic name
                            catalog_name = catalog.get('Code', '')
                            if not catalog_name or pd.isna(catalog_name):
                                catalog_name = catalog.get('Description', '')
                            if not catalog_name or pd.isna(catalog_name):
                                catalog_name = f'Catalog {idx + 1}'
                            
                            catalog_id = str(catalog.get('Id', f'catalog-{idx}'))
                            catalog_node = {
                                'id': catalog_id,
                                'name': str(catalog_name),
                                'type': 'catalog',
                                'children': [],
                                # Mark items that don't have proper Salesforce IDs as not synced
                                'isSynced': catalog_id.startswith('0') or catalog_id.startswith('a')
                            }
                            
                            # Get catalog ID for filtering categories
                            catalog_id = catalog.get('Id', '')
                            
                            # Add categories that belong to this catalog
                            if categories_df is not None and catalog_id:
                                # Check if there's a ProductCatalog__c field linking categories to catalogs
                                if 'ProductCatalog__c' in categories_df.columns:
                                    catalog_categories = categories_df[categories_df['ProductCatalog__c'] == catalog_id]
                                else:
                                    # If no direct link, show all categories under each catalog
                                    catalog_categories = categories_df
                                
                                for _, category in catalog_categories.iterrows():
                                    cat_node = {
                                        'id': str(category.get('Id', f'cat-{_}')),
                                        'name': str(category.get('Name', f'Category {_}')),
                                        'type': 'category',
                                        'children': []
                                    }
                                    
                                    # Add products in this category
                                    if products_df is not None:
                                        # Filter products by category if there's a relationship field
                                        if 'ProductCategory__c' in products_df.columns:
                                            category_products = products_df[products_df['ProductCategory__c'] == category.get('Id', '')]
                                        else:
                                            # If no category relationship, distribute products across categories
                                            # This is just for demo - in real implementation you'd have proper relationships
                                            start_idx = _ * 3
                                            end_idx = start_idx + 3
                                            category_products = products_df.iloc[start_idx:end_idx]
                                        
                                        for _, product in category_products.iterrows():
                                            prod_node = {
                                                'id': str(product.get('Id', f'prod-{_}')),
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
                                                '01tdp000006HfphAAC': [  # DCS Essentials Bundle
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 10},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 20},
                                                    {'id': '01tdp000006HfprAAC', 'name': 'DCS Getting Started Package', 'seq': 30}
                                                ],
                                                '01tdp000006HfpiAAC': [  # DCS Advanced Bundle
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 40},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 50},
                                                    {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 60},
                                                    {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 70},
                                                    {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 80, 'required': False}
                                                ],
                                                '01tdp000006HfpjAAC': [  # DCS Elite Bundle
                                                    {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 90},
                                                    {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 100},
                                                    {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 110},
                                                    {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 120},
                                                    {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 130},
                                                    {'id': '01tdp000006HfplAAC', 'name': 'Unlimited Classification', 'seq': 140},
                                                    {'id': '01tdp000006HfpqAAC', 'name': 'Software Development Kit', 'seq': 150, 'required': False}
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
                                    
                                    catalog_node['children'].append(cat_node)
                            
                            hierarchy_data['children'].append(catalog_node)
                    
                    # If no catalogs but have categories, create a default catalog
                    elif categories_df is not None and len(categories_df) > 0:
                        default_catalog = {
                            'id': 'default-catalog',
                            'name': 'Default Catalog',
                            'type': 'catalog',
                            'children': []
                        }
                        
                        for _, category in categories_df.iterrows():
                            cat_node = {
                                'id': str(category.get('Id', f'cat-{_}')),
                                'name': str(category.get('Name', f'Category {_}')),
                                'type': 'category',
                                'children': []
                            }
                            
                            # Add products in this category
                            if products_df is not None:
                                if 'ProductCategory__c' in products_df.columns:
                                    category_products = products_df[products_df['ProductCategory__c'] == category.get('Id', '')]
                                else:
                                    category_products = products_df.head(3)
                                
                                for _, product in category_products.iterrows():
                                    prod_node = {
                                        'id': str(product.get('Id', f'prod-{_}')),
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
                                        '01tdp000006HfphAAC': [  # DCS Essentials Bundle
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 10},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 20},
                                            {'id': '01tdp000006HfprAAC', 'name': 'DCS Getting Started Package', 'seq': 30}
                                        ],
                                        '01tdp000006HfpiAAC': [  # DCS Advanced Bundle
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 40},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 50},
                                            {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 60},
                                            {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 70},
                                            {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 80, 'required': False}
                                        ],
                                        '01tdp000006HfpjAAC': [  # DCS Elite Bundle
                                            {'id': '01tdp000006HfpoAAC', 'name': 'DCS for Windows', 'seq': 90},
                                            {'id': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine', 'seq': 100},
                                            {'id': '01tdp000006HfpnAAC', 'name': 'DCS Admin Console', 'seq': 110},
                                            {'id': '01tdp000006HfpmAAC', 'name': 'DCS Analysis Collector', 'seq': 120},
                                            {'id': '01tdp000006HfppAAC', 'name': 'DCS for OWA', 'seq': 130},
                                            {'id': '01tdp000006HfplAAC', 'name': 'Unlimited Classification', 'seq': 140},
                                            {'id': '01tdp000006HfpqAAC', 'name': 'Software Development Kit', 'seq': 150, 'required': False}
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
                            
                            default_catalog['children'].append(cat_node)
                        
                        hierarchy_data['children'].append(default_catalog)
                    
                    # If we have some data, add stats
                    if hierarchy_data:
                        hierarchy_data['stats'] = {
                            'catalogs': len(catalogs_df) if catalogs_df is not None else 0,
                            'categories': len(categories_df) if categories_df is not None else 0,
                            'products': len(products_df) if products_df is not None else 0
                        }
                
            except Exception as e:
                print(f"[DEBUG] Error loading real data: {e}")
            
            # If no real data loaded, use sample data
            if not hierarchy_data:
                print("[DEBUG] Using sample data as fallback")
                hierarchy_data = {
                'id': 'catalog-1',
                'name': 'Revenue Cloud Products',
                'type': 'catalog',
                'children': [
                    {
                        'id': 'cat-1',
                        'name': 'Software Licenses',
                        'type': 'category',
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
                workbook_path = os.path.join(server_dir, 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')
                
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
            
            self.send_json_response({
                'success': True,
                'hierarchy': hierarchy_data
            })
            
        except Exception as e:
            print(f"Error getting product hierarchy: {e}")
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