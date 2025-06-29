#\!/usr/bin/env python3
"""
Create ProductRelatedComponent records for static bundles with IsDefaultComponent.
"""

import pandas as pd
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("CREATING STATIC BUNDLE COMPONENTS")
    print("=" * 60)
    
    # Component definitions with IsDefaultComponent = true for static bundles
    components = [
        # DCS Essentials - 3 components
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfpoAAC', 'bundle': 'Essentials'},
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfpkAAC', 'bundle': 'Essentials'},
        {'ParentProductId': '01tdp000006JEGlAAO', 'ChildProductId': '01tdp000006HfprAAC', 'bundle': 'Essentials'},
        
        # DCS Advanced - 4 components
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpoAAC', 'bundle': 'Advanced'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpkAAC', 'bundle': 'Advanced'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpnAAC', 'bundle': 'Advanced'},
        {'ParentProductId': '01tdp000006JEGjAAO', 'ChildProductId': '01tdp000006HfpmAAC', 'bundle': 'Advanced'},
        
        # DCS Elite - 6 components
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpoAAC', 'bundle': 'Elite'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpkAAC', 'bundle': 'Elite'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpnAAC', 'bundle': 'Elite'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfpmAAC', 'bundle': 'Elite'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfppAAC', 'bundle': 'Elite'},
        {'ParentProductId': '01tdp000006JEGkAAO', 'ChildProductId': '01tdp000006HfplAAC', 'bundle': 'Elite'}
    ]
    
    # Add required fields for static bundles
    seq = 10
    for comp in components:
        comp['ProductRelationshipTypeId'] = '0yoa5000000gTtdAAE'  # Bundle to Bundle Component
        comp['Quantity'] = 1
        comp['IsDefaultComponent'] = True  # Required for static bundles
        comp['Sequence'] = seq
        seq += 10
    
    # Count by bundle
    from collections import Counter
    bundle_counts = Counter([c['bundle'] for c in components])
    for bundle, count in bundle_counts.items():
        print(f"  - DCS {bundle}: {count} components")
    
    # Remove bundle field before import
    for comp in components:
        del comp['bundle']
    
    print(f"\nTotal component relationships: {len(components)}")
    
    # Save to CSV
    df = pd.DataFrame(components)
    csv_file = Path('data/static_bundle_components.csv')
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
        print("✓ Successfully created bundle components\!")
        
        # Show bundle structure
        print("\n" + "-" * 80)
        print("BUNDLE COMPONENT STRUCTURE:")
        print("-" * 80)
        
        query = """
        SELECT Parent.Name, Parent.ProductCode,
               Child.Name, Child.ProductCode,
               Quantity
        FROM ProductRelatedComponent
        ORDER BY Parent.Name, Sequence
        """
        
        cmd_show = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
        subprocess.run(cmd_show)
        
        # Update workbook
        print("\n✓ Bundle component relationships successfully established\!")
        print("  - 3 bundles with 13 total components")
        print("  - All components are included by default (IsDefaultComponent = true)")
        
    else:
        print(f"✗ Import failed: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
