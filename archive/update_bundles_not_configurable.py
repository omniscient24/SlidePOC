#\!/usr/bin/env python3
"""
Update bundle products to not be configurable during sale.
"""

import subprocess
import pandas as pd
from pathlib import Path

def main():
    print("=" * 60)
    print("UPDATING BUNDLES TO NON-CONFIGURABLE")
    print("=" * 60)
    
    # Bundle product IDs
    bundles = [
        {'Id': '01tdp000006JEGlAAO', 'Name': 'DCS Essentials'},
        {'Id': '01tdp000006JEGjAAO', 'Name': 'DCS Advanced'},
        {'Id': '01tdp000006JEGkAAO', 'Name': 'DCS Elite'}
    ]
    
    # Create update data
    update_data = []
    for bundle in bundles:
        update_data.append({
            'Id': bundle['Id'],
            'ConfigureDuringSale': 'NotAllowed'
        })
        print(f"  - {bundle['Name']}")
    
    # Save to CSV
    df = pd.DataFrame(update_data)
    csv_file = Path('data/bundle_config_update.csv')
    df.to_csv(csv_file, index=False)
    
    # Update records
    cmd = [
        'sf', 'data', 'update', 'bulk',
        '--sobject', 'Product2',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    print("\nUpdating bundle configuration...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully updated bundles to non-configurable")
        
        # Now create the components
        create_components()
    else:
        print(f"✗ Update failed: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

def create_components():
    """Create ProductRelatedComponent records for non-configurable bundles."""
    print("\n" + "=" * 60)
    print("CREATING BUNDLE COMPONENTS")
    print("=" * 60)
    
    # Component definitions
    components = [
        # DCS Essentials
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfpoAAC'},
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfpkAAC'},
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfprAAC'},
        
        # DCS Advanced  
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpoAAC'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpkAAC'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpnAAC'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpmAAC'},
        
        # DCS Elite
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpoAAC'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpkAAC'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpnAAC'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpmAAC'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfppAAC'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfplAAC'}
    ]
    
    # Add required fields
    seq = 10
    for comp in components:
        comp['ProductRelationshipTypeId'] = '0yoa5000000gTtdAAE'  # Bundle to Bundle Component
        comp['Quantity'] = 1
        comp['Sequence'] = seq
        seq += 10
    
    print(f"Creating {len(components)} component relationships")
    
    # Save to CSV
    df = pd.DataFrame(components)
    csv_file = Path('data/bundle_components_final.csv')
    df.to_csv(csv_file, index=False)
    
    # Import
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductRelatedComponent',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created bundle components\!")
        
        # Show results
        print("\nBundle structure created:")
        query = """
        SELECT Parent.Name, COUNT(ChildProductId)
        FROM ProductRelatedComponent
        GROUP BY Parent.Name
        ORDER BY Parent.Name
        """
        
        cmd_show = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
        subprocess.run(cmd_show)
        
    else:
        print(f"✗ Import failed: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
