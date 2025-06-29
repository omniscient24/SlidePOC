#\!/usr/bin/env python3
"""
Update bundles to be configurable and create ProductComponentGroups.
"""

import subprocess
import pandas as pd
from pathlib import Path
import json

def main():
    print("=" * 60)
    print("MAKING BUNDLES CONFIGURABLE")
    print("=" * 60)
    
    # Step 1: Update bundles to be configurable
    bundles = [
        {'Id': '01tdp000006JEGlAAO', 'Name': 'DCS Essentials'},
        {'Id': '01tdp000006JEGjAAO', 'Name': 'DCS Advanced'},
        {'Id': '01tdp000006JEGkAAO', 'Name': 'DCS Elite'}
    ]
    
    print("Step 1: Updating bundles to be configurable...")
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
    else:
        print(f"✗ Update failed: {result.stderr}")
        return
    
    csv_file.unlink()
    
    # Step 2: Create ProductComponentGroups
    create_component_groups(bundles)

def create_component_groups(bundles):
    """Create ProductComponentGroup records for configurable bundles."""
    print("\n" + "=" * 60)
    print("CREATING PRODUCTCOMPONENTGROUPS")
    print("=" * 60)
    
    # Define component groups
    groups = []
    
    # Create groups for each bundle
    for bundle in bundles:
        # Core Components group (required)
        groups.append({
            'Name': f'{bundle["Name"]} - Core Components',
            'Description': f'Required core components for {bundle["Name"]}',
            'ParentProductId': bundle['Id'],
            'Sequence': 10,
            'Code': f'{bundle["Name"][:3].upper()}_CORE'
        })
        
        # Optional Components group (for Advanced and Elite)
        if bundle['Name'] in ['DCS Advanced', 'DCS Elite']:
            groups.append({
                'Name': f'{bundle["Name"]} - Optional Components',
                'Description': f'Optional add-on components for {bundle["Name"]}',
                'ParentProductId': bundle['Id'],
                'Sequence': 20,
                'Code': f'{bundle["Name"][:3].upper()}_OPT'
            })
    
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
        
        # Get the created group IDs
        update_component_relationships()
    else:
        print(f"✗ Import failed: {result.stderr}")
    
    csv_file.unlink()

def update_component_relationships():
    """Update ProductRelatedComponent records with group IDs."""
    print("\n" + "=" * 60)
    print("UPDATING COMPONENT RELATIONSHIPS WITH GROUPS")
    print("=" * 60)
    
    # First, get the group IDs
    query = "SELECT Id, Name, ParentProductId, Code FROM ProductComponentGroup ORDER BY Name"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    group_map = {}
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            for group in data['result']['records']:
                # Map by parent product and whether it's core or optional
                key = f"{group['ParentProductId']}_{'CORE' if 'Core' in group['Name'] else 'OPT'}"
                group_map[key] = group['Id']
                print(f"  - {group['Name']}: {group['Id']}")
    
    # Get existing component relationships
    query2 = "SELECT Id, ParentProductId, ChildProduct.Name FROM ProductRelatedComponent"
    
    cmd2 = [
        'sf', 'data', 'query',
        '--query', query2,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    
    updates = []
    if result2.returncode == 0:
        data2 = json.loads(result2.stdout)
        if 'result' in data2 and 'records' in data2['result']:
            for comp in data2['result']['records']:
                # Determine which group this component belongs to
                child_name = comp['ChildProduct']['Name']
                parent_id = comp['ParentProductId']
                
                # Core components for all bundles
                core_components = ['DCS for Windows', 'Data Detection Engine', 'DCS Getting Started Package', 
                                 'DCS Admin Console', 'DCS Analysis Collector']
                
                # Determine group
                if child_name in core_components:
                    group_key = f"{parent_id}_CORE"
                else:
                    group_key = f"{parent_id}_OPT"
                
                if group_key in group_map:
                    updates.append({
                        'Id': comp['Id'],
                        'ProductComponentGroupId': group_map[group_key]
                    })
    
    if updates:
        print(f"\nUpdating {len(updates)} component relationships with groups...")
        
        # Save updates
        df = pd.DataFrame(updates)
        csv_file = Path('data/component_group_updates.csv')
        df.to_csv(csv_file, index=False)
        
        # Update records
        cmd_update = [
            'sf', 'data', 'update', 'bulk',
            '--sobject', 'ProductRelatedComponent',
            '--file', str(csv_file),
            '--target-org', 'fortradp2',
            '--wait', '10'
        ]
        
        result_update = subprocess.run(cmd_update, capture_output=True, text=True)
        
        if result_update.returncode == 0:
            print("✓ Successfully updated component relationships with groups")
            show_final_structure()
        else:
            print(f"✗ Update failed: {result_update.stderr}")
        
        csv_file.unlink()

def show_final_structure():
    """Show the final bundle structure with groups."""
    print("\n" + "=" * 80)
    print("FINAL CONFIGURABLE BUNDLE STRUCTURE:")
    print("=" * 80)
    
    query = """
    SELECT ParentProduct.Name,
           ProductComponentGroup.Name,
           ChildProduct.Name,
           IsDefaultComponent,
           Quantity
    FROM ProductRelatedComponent
    ORDER BY ParentProduct.Name, ProductComponentGroup.Sequence, Sequence
    """
    
    cmd = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
