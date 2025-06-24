#!/usr/bin/env python3
"""
Import existing Salesforce CLI connections into the migration tool
"""
import json
import subprocess
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.connection_manager import connection_manager


def import_cli_connections():
    """Import existing CLI connections"""
    print("Checking for existing Salesforce CLI connections...")
    
    try:
        # Get list of orgs from CLI
        result = subprocess.run(
            ['sf', 'org', 'list', '--json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("Error: Could not retrieve org list from Salesforce CLI")
            return
        
        data = json.loads(result.stdout)
        orgs = []
        
        # Combine scratch orgs and non-scratch orgs
        if 'result' in data:
            if 'scratchOrgs' in data['result']:
                orgs.extend(data['result']['scratchOrgs'])
            if 'nonScratchOrgs' in data['result']:
                orgs.extend(data['result']['nonScratchOrgs'])
        
        if not orgs:
            print("No orgs found in Salesforce CLI")
            return
        
        # Filter for connected orgs
        connected_orgs = [
            org for org in orgs 
            if org.get('connectedStatus') == 'Connected' and org.get('alias')
        ]
        
        if not connected_orgs:
            print("No connected orgs found in Salesforce CLI")
            return
        
        print(f"\nFound {len(connected_orgs)} connected org(s):")
        for org in connected_orgs:
            print(f"  - {org['alias']} ({org.get('username', 'Unknown')})")
        
        # Check existing connections
        existing_aliases = [
            conn['cli_alias'] 
            for conn in connection_manager.connections
        ]
        
        imported_count = 0
        for org in connected_orgs:
            alias = org['alias']
            
            # Skip if already imported
            if alias in existing_aliases:
                print(f"\nSkipping {alias} - already imported")
                continue
            
            print(f"\nImporting {alias}...")
            
            # Determine org type
            org_type = 'scratch' if org.get('isScratch') else 'production'
            if 'sandbox' in alias.lower() or org.get('instanceUrl', '').find('.sandbox.') > -1:
                org_type = 'sandbox'
            
            # Get org details
            org_info = connection_manager._get_org_info(alias)
            if not org_info:
                print(f"  Warning: Could not get details for {alias}")
                continue
            
            # Create connection record
            connection = {
                'id': f"imported_{alias}_{int(datetime.now().timestamp())}",
                'name': alias.replace('-', ' ').replace('_', ' ').title(),
                'cli_alias': alias,
                'org_type': org_type,
                'description': f"Imported from Salesforce CLI",
                'created_by': 'import',
                'created_at': datetime.now().isoformat(),
                'last_used': org.get('lastUsed', datetime.now().isoformat()),
                'status': 'active',
                'metadata': org_info
            }
            
            connection_manager.connections.append(connection)
            imported_count += 1
            print(f"  ✓ Imported successfully")
        
        if imported_count > 0:
            connection_manager.save_connections()
            print(f"\n✅ Successfully imported {imported_count} connection(s)")
        else:
            print("\n✅ No new connections to import")
            
    except Exception as e:
        print(f"\n❌ Error importing connections: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import_cli_connections()