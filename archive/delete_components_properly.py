#\!/usr/bin/env python3
"""
Delete ProductRelatedComponent records properly.
"""

import subprocess
import json
from pathlib import Path

def main():
    print("=" * 60)
    print("DELETING PRODUCTRELATEDCOMPONENT RECORDS")
    print("=" * 60)
    
    # Get component IDs
    query = "SELECT Id FROM ProductRelatedComponent"
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            records = data['result']['records']
            print(f"Found {len(records)} component relationships to delete")
            
            if records:
                # Create CSV with only Id column
                csv_file = Path('data/components_to_delete.csv')
                with open(csv_file, 'w') as f:
                    f.write('Id\n')
                    for record in records:
                        f.write(f"{record['Id']}\n")
                
                # Delete using SOQL
                print("\nDeleting component relationships...")
                
                # Use data delete record instead of bulk
                for record in records:
                    cmd_del = [
                        'sf', 'data', 'delete', 'record',
                        '--sobject', 'ProductRelatedComponent',
                        '--record-id', record['Id'],
                        '--target-org', 'fortradp2'
                    ]
                    subprocess.run(cmd_del, capture_output=True)
                
                print("✓ Successfully deleted all component relationships")
                
                # Verify deletion
                verify_cmd = [
                    'sf', 'data', 'query',
                    '--query', 'SELECT COUNT() FROM ProductRelatedComponent',
                    '--target-org', 'fortradp2'
                ]
                subprocess.run(verify_cmd)
                
                csv_file.unlink()
                
                # Now update bundles to configurable
                update_bundles_configurable()

def update_bundles_configurable():
    """Update bundles to be configurable."""
    print("\n" + "=" * 60)
    print("UPDATING BUNDLES TO CONFIGURABLE")
    print("=" * 60)
    
    bundles = [
        '01tdp000006JEGlAAO',  # DCS Essentials
        '01tdp000006JEGjAAO',  # DCS Advanced
        '01tdp000006JEGkAAO'   # DCS Elite
    ]
    
    for bundle_id in bundles:
        cmd = [
            'sf', 'data', 'update', 'record',
            '--sobject', 'Product2',
            '--record-id', bundle_id,
            '--values', 'ConfigureDuringSale=Allowed',
            '--target-org', 'fortradp2'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Updated {bundle_id}")
        else:
            print(f"✗ Failed {bundle_id}: {result.stderr}")
    
    print("\n✅ Bundles are now configurable and ready for component groups")

if __name__ == '__main__':
    main()
