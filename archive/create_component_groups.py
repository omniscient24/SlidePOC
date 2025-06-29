#\!/usr/bin/env python3
"""
Create ProductComponentGroups for configurable bundles.
"""

import subprocess
import pandas as pd
from pathlib import Path

def main():
    print("=" * 60)
    print("CREATING PRODUCTCOMPONENTGROUPS")
    print("=" * 60)
    
    # Define component groups for each bundle
    groups = [
        # DCS Essentials - 1 group
        {
            'Name': 'Core Components',
            'Description': 'Essential components included in DCS Essentials bundle',
            'ParentProductId': '01tdp000006JEGlAAO',
            'Sequence': 10,
            'Code': 'ESS_CORE'
        },
        
        # DCS Advanced - 2 groups
        {
            'Name': 'Core Components',
            'Description': 'Essential components included in DCS Advanced bundle',
            'ParentProductId': '01tdp000006JEGjAAO',
            'Sequence': 10,
            'Code': 'ADV_CORE'
        },
        {
            'Name': 'Optional Add-Ons',
            'Description': 'Optional components for DCS Advanced bundle',
            'ParentProductId': '01tdp000006JEGjAAO',
            'Sequence': 20,
            'Code': 'ADV_OPT'
        },
        
        # DCS Elite - 2 groups
        {
            'Name': 'Core Components',
            'Description': 'Essential components included in DCS Elite bundle',
            'ParentProductId': '01tdp000006JEGkAAO',
            'Sequence': 10,
            'Code': 'ELITE_CORE'
        },
        {
            'Name': 'Premium Components',
            'Description': 'Premium components included in DCS Elite bundle',
            'ParentProductId': '01tdp000006JEGkAAO',
            'Sequence': 20,
            'Code': 'ELITE_PREM'
        }
    ]
    
    print(f"Creating {len(groups)} component groups:")
    for group in groups:
        print(f"  - {group['Name']} for {group['Code']}")
    
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
    
    print("\nImporting ProductComponentGroups...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductComponentGroups")
        
        # Verify and show groups
        print("\n" + "-" * 60)
        print("CREATED COMPONENT GROUPS:")
        print("-" * 60)
        
        query = """
        SELECT Name, Code, ParentProduct.Name, Sequence
        FROM ProductComponentGroup
        ORDER BY ParentProduct.Name, Sequence
        """
        
        cmd_show = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
        subprocess.run(cmd_show)
        
        print("\n✅ Component groups created successfully\!")
        print("   Bundles are now configurable with organized component groups")
        
    else:
        print(f"✗ Import failed: {result.stderr}")
        
        # Check specific error
        import os
        failed_files = [f for f in os.listdir('.') if f.endswith('-failed-records.csv')]
        if failed_files:
            latest = sorted(failed_files)[-1]
            print(f"\nChecking error in {latest}")
            with open(latest, 'r') as f:
                print(f.read()[:500])
    
    csv_file.unlink()

if __name__ == '__main__':
    main()
