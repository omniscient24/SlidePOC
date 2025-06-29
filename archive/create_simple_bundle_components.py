#\!/usr/bin/env python3
"""
Create simple ProductRelatedComponent records with minimal required fields.
"""

import pandas as pd
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("CREATING SIMPLE BUNDLE COMPONENTS")
    print("=" * 60)
    
    # Create simple component relationships
    # Using the other relationship type for regular bundle components
    records = []
    
    # DCS Essentials Bundle - 3 core components
    essentials_components = [
        {'parent': '01tdp000006JEGlAAO', 'child': '01tdp000006HfpoAAC', 'name': 'DCS for Windows'},
        {'parent': '01tdp000006JEGlAAO', 'child': '01tdp000006HfpkAAC', 'name': 'Data Detection Engine'},
        {'parent': '01tdp000006JEGlAAO', 'child': '01tdp000006HfprAAC', 'name': 'DCS Getting Started Package'}
    ]
    
    seq = 10
    for comp in essentials_components:
        record = {
            'ParentProductId': comp['parent'],
            'ChildProductId': comp['child'],
            'ProductRelationshipTypeId': '0yoa5000000gTtdAAE',  # Bundle to Bundle Component
            'Quantity': 1,
            'IsDefaultComponent': True,  # Required for required components
            'IsQuantityEditable': False,  # Don't allow quantity changes
            'Sequence': seq
        }
        records.append(record)
        print(f"  - {comp['name']}")
        seq += 10
    
    print(f"\nPreparing {len(records)} component records")
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Save to CSV
    csv_file = Path('data/simple_bundle_components.csv')
    df.to_csv(csv_file, index=False)
    
    # Import
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductRelatedComponent',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    print("\nImporting ProductRelatedComponent records...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully imported\!")
        
        # Show results
        query = """
        SELECT Parent.Name, Child.Name, Quantity
        FROM ProductRelatedComponent
        ORDER BY Parent.Name
        """
        
        cmd_show = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
        subprocess.run(cmd_show)
        
    else:
        print(f"✗ Failed: {result.stderr}")
        
        # Check specific error
        import os
        failed_files = [f for f in os.listdir('.') if f.endswith('-failed-records.csv')]
        if failed_files:
            latest_failed = sorted(failed_files)[-1]
            print(f"\nChecking failures in {latest_failed}:")
            df_failed = pd.read_csv(latest_failed)
            if not df_failed.empty and 'sf__Error' in df_failed.columns:
                print(df_failed['sf__Error'].iloc[0])
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
