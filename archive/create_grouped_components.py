#\!/usr/bin/env python3
"""
Create ProductRelatedComponent records with ProductComponentGroup assignments.
"""

import subprocess
import pandas as pd
import json
from pathlib import Path

def main():
    print("=" * 60)
    print("CREATING GROUPED COMPONENT RELATIONSHIPS")
    print("=" * 60)
    
    # First, get the group IDs
    query = "SELECT Id, Code, ParentProductId FROM ProductComponentGroup"
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
                # Map by parent product and code
                key = f"{group['ParentProductId']}_{group['Code']}"
                group_map[key] = group['Id']
                print(f"  Group {group['Code']}: {group['Id']}")
    
    # Define component relationships with groups
    components = [
        # DCS Essentials - Core Components
        {
            'ParentProductId': '01tdp000006JEGlAAO',
            'ChildProductId': '01tdp000006HfpoAAC',  # DCS for Windows
            'GroupKey': '01tdp000006JEGlAAO_ESS_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGlAAO',
            'ChildProductId': '01tdp000006HfpkAAC',  # Data Detection Engine
            'GroupKey': '01tdp000006JEGlAAO_ESS_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGlAAO',
            'ChildProductId': '01tdp000006HfprAAC',  # Getting Started Package
            'GroupKey': '01tdp000006JEGlAAO_ESS_CORE',
            'Required': True,
            'Default': True
        },
        
        # DCS Advanced - Core Components
        {
            'ParentProductId': '01tdp000006JEGjAAO',
            'ChildProductId': '01tdp000006HfpoAAC',  # DCS for Windows
            'GroupKey': '01tdp000006JEGjAAO_ADV_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGjAAO',
            'ChildProductId': '01tdp000006HfpkAAC',  # Data Detection Engine
            'GroupKey': '01tdp000006JEGjAAO_ADV_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGjAAO',
            'ChildProductId': '01tdp000006HfpnAAC',  # Admin Console
            'GroupKey': '01tdp000006JEGjAAO_ADV_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGjAAO',
            'ChildProductId': '01tdp000006HfpmAAC',  # Analysis Collector
            'GroupKey': '01tdp000006JEGjAAO_ADV_CORE',
            'Required': True,
            'Default': True
        },
        
        # DCS Advanced - Optional Add-Ons
        {
            'ParentProductId': '01tdp000006JEGjAAO',
            'ChildProductId': '01tdp000006HfppAAC',  # DCS for OWA
            'GroupKey': '01tdp000006JEGjAAO_ADV_OPT',
            'Required': False,
            'Default': False
        },
        
        # DCS Elite - Core Components
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfpoAAC',  # DCS for Windows
            'GroupKey': '01tdp000006JEGkAAO_ELITE_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfpkAAC',  # Data Detection Engine
            'GroupKey': '01tdp000006JEGkAAO_ELITE_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfpnAAC',  # Admin Console
            'GroupKey': '01tdp000006JEGkAAO_ELITE_CORE',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfpmAAC',  # Analysis Collector
            'GroupKey': '01tdp000006JEGkAAO_ELITE_CORE',
            'Required': True,
            'Default': True
        },
        
        # DCS Elite - Premium Components
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfppAAC',  # DCS for OWA
            'GroupKey': '01tdp000006JEGkAAO_ELITE_PREM',
            'Required': True,
            'Default': True
        },
        {
            'ParentProductId': '01tdp000006JEGkAAO',
            'ChildProductId': '01tdp000006HfplAAC',  # Unlimited Classification
            'GroupKey': '01tdp000006JEGkAAO_ELITE_PREM',
            'Required': True,
            'Default': True
        }
    ]
    
    # Build import records
    import_records = []
    seq = 10
    
    for comp in components:
        if comp['GroupKey'] in group_map:
            record = {
                'ParentProductId': comp['ParentProductId'],
                'ChildProductId': comp['ChildProductId'],
                'ProductComponentGroupId': group_map[comp['GroupKey']],
                'ProductRelationshipTypeId': '0yoa5000000gTtdAAE',  # Bundle to Bundle Component
                'Quantity': 1,
                'MinQuantity': 1 if comp['Required'] else 0,
                'MaxQuantity': 1,
                'IsQuantityEditable': True,  # Allow quantity changes for configurable bundles
                'IsComponentRequired': comp['Required'],
                'IsDefaultComponent': comp['Default'],
                'Sequence': seq
            }
            import_records.append(record)
            seq += 10
    
    print(f"\nCreating {len(import_records)} component relationships with groups")
    
    # Save to CSV
    df = pd.DataFrame(import_records)
    csv_file = Path('data/grouped_components.csv')
    df.to_csv(csv_file, index=False)
    
    # Import
    cmd_import = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductRelatedComponent',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result_import = subprocess.run(cmd_import, capture_output=True, text=True)
    
    if result_import.returncode == 0:
        print("✓ Successfully created component relationships\!")
        show_final_structure()
    else:
        print(f"✗ Import failed: {result_import.stderr}")
    
    csv_file.unlink()

def show_final_structure():
    """Show the final configurable bundle structure."""
    print("\n" + "=" * 80)
    print("CONFIGURABLE BUNDLE STRUCTURE:")
    print("=" * 80)
    
    query = """
    SELECT ParentProduct.Name Bundle,
           ProductComponentGroup.Name ComponentGroup,
           COUNT(Id) Components
    FROM ProductRelatedComponent
    GROUP BY ParentProduct.Name, ProductComponentGroup.Name
    ORDER BY ParentProduct.Name, ProductComponentGroup.Sequence
    """
    
    cmd = ['sf', 'data', 'query', '--query', query, '--target-org', 'fortradp2']
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
