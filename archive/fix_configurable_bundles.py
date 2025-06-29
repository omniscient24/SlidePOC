#\!/usr/bin/env python3
"""
Fix bundles to be configurable by removing components first.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

def main():
    print("=" * 60)
    print("FIXING BUNDLES TO BE CONFIGURABLE")
    print("=" * 60)
    
    # Step 1: Delete existing ProductRelatedComponent records
    print("Step 1: Removing existing component relationships...")
    
    # Get all component IDs
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
                # Create CSV with IDs to delete
                df = pd.DataFrame(records)
                csv_file = Path('data/components_to_delete.csv')
                df.to_csv(csv_file, index=False)
                
                # Delete records
                cmd_delete = [
                    'sf', 'data', 'delete', 'bulk',
                    '--sobject', 'ProductRelatedComponent',
                    '--file', str(csv_file),
                    '--target-org', 'fortradp2',
                    '--wait', '10'
                ]
                
                result_delete = subprocess.run(cmd_delete, capture_output=True, text=True)
                
                if result_delete.returncode == 0:
                    print("✓ Successfully deleted component relationships")
                else:
                    print(f"✗ Delete failed: {result_delete.stderr}")
                    return
                
                csv_file.unlink()
    
    # Step 2: Update bundles to configurable
    update_to_configurable()

def update_to_configurable():
    """Update bundles to be configurable."""
    print("\nStep 2: Updating bundles to be configurable...")
    
    bundles = [
        {'Id': '01tdp000006JEGlAAO', 'Name': 'DCS Essentials'},
        {'Id': '01tdp000006JEGjAAO', 'Name': 'DCS Advanced'},
        {'Id': '01tdp000006JEGkAAO', 'Name': 'DCS Elite'}
    ]
    
    update_data = []
    for bundle in bundles:
        update_data.append({
            'Id': bundle['Id'],
            'ConfigureDuringSale': 'Allowed'
        })
        print(f"  - {bundle['Name']}")
    
    # Save and update
    df = pd.DataFrame(update_data)
    csv_file = Path('data/bundle_configurable_update.csv')
    df.to_csv(csv_file, index=False)
    
    cmd = [
        'sf', 'data', 'update', 'bulk',
        '--sobject', 'Product2',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully updated bundles to configurable")
        create_groups_and_components()
    else:
        print(f"✗ Update failed: {result.stderr}")
    
    csv_file.unlink()

def create_groups_and_components():
    """Create ProductComponentGroups and then components."""
    print("\n" + "=" * 60)
    print("CREATING COMPONENT GROUPS")
    print("=" * 60)
    
    # Create groups for each bundle
    groups = [
        # DCS Essentials groups
        {
            'Name': 'Core Components - Essentials',
            'Description': 'Required core components for DCS Essentials',
            'ParentProductId': '01tdp000006JEGlAAO',
            'Sequence': 10,
            'Code': 'ESS_CORE'
        },
        # DCS Advanced groups
        {
            'Name': 'Core Components - Advanced',
            'Description': 'Required core components for DCS Advanced',
            'ParentProductId': '01tdp000006JEGjAAO',
            'Sequence': 10,
            'Code': 'ADV_CORE'
        },
        {
            'Name': 'Optional Components - Advanced',
            'Description': 'Optional add-on components for DCS Advanced',
            'ParentProductId': '01tdp000006JEGjAAO',
            'Sequence': 20,
            'Code': 'ADV_OPT'
        },
        # DCS Elite groups
        {
            'Name': 'Core Components - Elite',
            'Description': 'Required core components for DCS Elite',
            'ParentProductId': '01tdp000006JEGkAAO',
            'Sequence': 10,
            'Code': 'ELITE_CORE'
        },
        {
            'Name': 'Advanced Components - Elite',
            'Description': 'Advanced components included in DCS Elite',
            'ParentProductId': '01tdp000006JEGkAAO',
            'Sequence': 20,
            'Code': 'ELITE_ADV'
        }
    ]
    
    print(f"Creating {len(groups)} component groups...")
    
    # Save to CSV
    df = pd.DataFrame(groups)
    csv_file = Path('data/product_component_groups.csv')
    df.to_csv(csv_file, index=False)
    
    # Import groups
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductComponentGroup',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductComponentGroups")
        
        # Show created groups
        query = "SELECT COUNT() FROM ProductComponentGroup"
        cmd_count = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
        subprocess.run(cmd_count)
        
        print("\n✅ BUNDLES ARE NOW CONFIGURABLE WITH COMPONENT GROUPS")
        print("   Next step: Create ProductRelatedComponent records with group assignments")
        
    else:
        print(f"✗ Import failed: {result.stderr}")
    
    csv_file.unlink()

if __name__ == '__main__':
    main()
