#!/usr/bin/env python3
"""
Simple working server implementation
"""
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.connection_manager import connection_manager
from app.services.session_manager import session_manager
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
            file_path = TEMPLATES_ROOT / 'index.html'
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
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
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