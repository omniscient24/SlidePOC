#!/usr/bin/env python3
"""
Import existing Salesforce CLI connections into the Revenue Cloud Migration Tool
"""
import sys
import os
import json
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings.app_config import CONNECTION_FILE

def import_cli_connections():
    """Import connections from Salesforce CLI"""
    
    # Get CLI orgs
    result = subprocess.run(['sf', 'org', 'list', '--json'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to get org list from CLI")
        return
    
    cli_data = json.loads(result.stdout)
    
    # Find fortradp2 and fortra-dev
    connections = []
    for org in cli_data['result'].get('sandboxes', []) + cli_data['result'].get('other', []):
        if org['alias'] in ['fortradp2', 'fortra-dev'] and org.get('connectedStatus') == 'Connected':
            connection = {
                'id': f"imported_{org['alias']}_{int(time.time())}",
                'name': org['alias'].replace('-', ' ').title(),
                'cli_alias': org['alias'],
                'org_type': 'sandbox' if org.get('isSandbox') else 'production',
                'description': f"Imported from Salesforce CLI",
                'created_by': 'import',
                'created_at': datetime.now().isoformat(),
                'last_used': org.get('lastUsed', datetime.now().isoformat()),
                'status': 'active',
                'metadata': {
                    'org_id': org['orgId'],
                    'instance_url': org['instanceUrl'],
                    'username': org['username'],
                    'api_version': org.get('instanceApiVersion', '64.0')
                }
            }
            connections.append(connection)
            print(f"Imported: {connection['name']} ({connection['metadata']['username']})")
    
    # Save connections
    CONNECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONNECTION_FILE, 'w') as f:
        json.dump({'connections': connections}, f, indent=2)
    
    print(f"\nImported {len(connections)} connections to {CONNECTION_FILE}")

if __name__ == "__main__":
    import time
    from datetime import datetime
    import_cli_connections()