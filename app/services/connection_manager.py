"""
Salesforce Connection Manager
Manages saved Salesforce CLI connections for the Revenue Cloud Migration Tool
"""
import json
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config.settings.app_config import CONNECTION_FILE, MAX_SAVED_CONNECTIONS, CLI_COMMAND, DEFAULT_CLI_TIMEOUT


class ConnectionManager:
    """Manages Salesforce connections using the Salesforce CLI"""
    
    def __init__(self):
        self.connections_file = CONNECTION_FILE
        self.connections = []
        self.load_connections()
    
    def load_connections(self) -> None:
        """Load saved connections from file"""
        if self.connections_file.exists():
            try:
                with open(self.connections_file, 'r') as f:
                    data = json.load(f)
                    self.connections = data.get('connections', [])
            except Exception as e:
                print(f"Error loading connections: {e}")
                self.connections = []
        else:
            self.save_connections()
    
    def save_connections(self) -> None:
        """Save connections to file"""
        self.connections_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.connections_file, 'w') as f:
            json.dump({'connections': self.connections}, f, indent=2)
    
    def get_all_connections(self) -> List[Dict]:
        """Get all saved connections"""
        # Update status for each connection
        for conn in self.connections:
            self.verify_connection(conn['id'])
        return self.connections
    
    def get_connection(self, connection_id: str) -> Optional[Dict]:
        """Get a specific connection by ID"""
        for conn in self.connections:
            if conn['id'] == connection_id:
                return conn
        return None
    
    def add_connection(self, name: str, description: str, org_type: str = 'sandbox', 
                      created_by: str = 'admin') -> Tuple[bool, Dict]:
        """
        Add a new Salesforce connection using CLI authentication
        
        Returns:
            Tuple of (success: bool, connection_or_error: dict)
        """
        if len(self.connections) >= MAX_SAVED_CONNECTIONS:
            return False, {'error': f'Maximum number of connections ({MAX_SAVED_CONNECTIONS}) reached'}
        
        # Generate unique CLI alias
        timestamp = int(time.time())
        cli_alias = f"rcm_{timestamp}"
        
        # Build CLI command with appropriate instance URL
        cmd = [CLI_COMMAND, 'org', 'login', 'web', '--alias', cli_alias]
        
        # Set the appropriate instance URL based on org type
        if org_type == 'sandbox':
            cmd.extend(['--instance-url', 'https://test.salesforce.com'])
        elif org_type == 'scratch':
            # Scratch orgs use the standard login URL
            cmd.extend(['--instance-url', 'https://login.salesforce.com'])
        elif org_type == 'production':
            cmd.extend(['--instance-url', 'https://login.salesforce.com'])
        # For dev hub, use standard login but set as default dev hub
        elif org_type == 'devhub':
            cmd.extend(['--instance-url', 'https://login.salesforce.com'])
            cmd.append('--set-default-dev-hub')
        
        try:
            # Execute CLI login
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_CLI_TIMEOUT)
            
            if result.returncode != 0:
                return False, {'error': f'CLI authentication failed: {result.stderr}'}
            
            # Get org information
            org_info = self._get_org_info(cli_alias)
            if not org_info:
                return False, {'error': 'Failed to retrieve org information'}
            
            # Create connection record
            connection = {
                'id': f"conn_{timestamp}",
                'name': name,
                'cli_alias': cli_alias,
                'org_type': org_type,
                'description': description,
                'created_by': created_by,
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'status': 'active',
                'metadata': org_info
            }
            
            self.connections.append(connection)
            self.save_connections()
            
            return True, connection
            
        except subprocess.TimeoutExpired:
            return False, {'error': 'Authentication timeout - please try again'}
        except Exception as e:
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def verify_connection(self, connection_id: str) -> bool:
        """Verify if a connection is still valid"""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        try:
            # Use org display to check connection
            result = subprocess.run(
                [CLI_COMMAND, 'org', 'display', '--target-org', connection['cli_alias'], '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('status') == 0:
                    # Update metadata
                    org_info = data.get('result', {})
                    connection['metadata'] = {
                        'org_id': org_info.get('id'),
                        'instance_url': org_info.get('instanceUrl'),
                        'username': org_info.get('username'),
                        'api_version': org_info.get('apiVersion')
                    }
                    connection['status'] = 'active'
                else:
                    connection['status'] = 'error'
            else:
                connection['status'] = 'expired'
            
            self.save_connections()
            return connection['status'] == 'active'
            
        except Exception:
            connection['status'] = 'error'
            self.save_connections()
            return False
    
    def refresh_connection(self, connection_id: str) -> Tuple[bool, str]:
        """Refresh an expired connection"""
        connection = self.get_connection(connection_id)
        if not connection:
            return False, "Connection not found"
        
        # Re-authenticate using the same alias and appropriate URL
        cmd = [CLI_COMMAND, 'org', 'login', 'web', '--alias', connection['cli_alias']]
        
        # Use the correct instance URL based on org type
        org_type = connection.get('org_type', 'production')
        if org_type == 'sandbox':
            cmd.extend(['--instance-url', 'https://test.salesforce.com'])
        elif org_type in ['production', 'scratch', 'devhub']:
            cmd.extend(['--instance-url', 'https://login.salesforce.com'])
        
        if org_type == 'devhub':
            cmd.append('--set-default-dev-hub')
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_CLI_TIMEOUT)
            
            if result.returncode == 0:
                # Update connection info
                org_info = self._get_org_info(connection['cli_alias'])
                if org_info:
                    connection['metadata'] = org_info
                    connection['status'] = 'active'
                    connection['last_used'] = datetime.now().isoformat()
                    self.save_connections()
                    return True, "Connection refreshed successfully"
                
            return False, "Failed to refresh connection"
            
        except Exception as e:
            return False, f"Error refreshing connection: {str(e)}"
    
    def delete_connection(self, connection_id: str) -> bool:
        """Delete a saved connection"""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        # Remove from CLI
        try:
            subprocess.run(
                [CLI_COMMAND, 'org', 'logout', '--target-org', connection['cli_alias'], '--no-prompt'],
                capture_output=True,
                timeout=30
            )
        except:
            pass  # Continue even if logout fails
        
        # Remove from saved connections
        self.connections = [c for c in self.connections if c['id'] != connection_id]
        self.save_connections()
        return True
    
    def set_active_connection(self, session: Dict, connection_id: str) -> bool:
        """Set the active connection for a session"""
        if self.verify_connection(connection_id):
            connection = self.get_connection(connection_id)
            connection['last_used'] = datetime.now().isoformat()
            session['active_connection_id'] = connection_id
            session['active_connection_alias'] = connection['cli_alias']
            self.save_connections()
            return True
        return False
    
    def get_active_connection(self, session: Dict) -> Optional[Dict]:
        """Get the active connection for a session"""
        connection_id = session.get('active_connection_id')
        if connection_id:
            return self.get_connection(connection_id)
        return None
    
    def _get_org_info(self, cli_alias: str) -> Optional[Dict]:
        """Get organization information from CLI"""
        try:
            result = subprocess.run(
                [CLI_COMMAND, 'org', 'display', '--target-org', cli_alias, '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('status') == 0:
                    org_info = data.get('result', {})
                    return {
                        'org_id': org_info.get('id'),
                        'instance_url': org_info.get('instanceUrl'),
                        'username': org_info.get('username'),
                        'api_version': org_info.get('apiVersion'),
                        'access_token': org_info.get('accessToken', 'CLI Managed')
                    }
        except Exception:
            pass
        
        return None
    
    def test_connection(self, connection_id: str) -> Tuple[bool, Dict]:
        """Test a connection by running a simple query"""
        connection = self.get_connection(connection_id)
        if not connection:
            return False, {'error': 'Connection not found'}
        
        try:
            # Run a simple query to test the connection
            result = subprocess.run(
                [CLI_COMMAND, 'data', 'query', 
                 '--query', 'SELECT COUNT() FROM User LIMIT 1',
                 '--target-org', connection['cli_alias'],
                 '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('status') == 0:
                    return True, {
                        'success': True,
                        'message': 'Connection test successful',
                        'org_id': connection['metadata'].get('org_id'),
                        'username': connection['metadata'].get('username')
                    }
            
            return False, {'error': 'Connection test failed'}
            
        except Exception as e:
            return False, {'error': f'Test failed: {str(e)}'}


# Singleton instance
connection_manager = ConnectionManager()