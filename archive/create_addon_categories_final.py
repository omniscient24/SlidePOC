#\!/usr/bin/env python3
"""
Create ProductCategoryProduct records for Add-On products.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

def main():
    print("=" * 60)
    print("CREATING ADD-ON PRODUCT CATEGORY ASSIGNMENTS")
    print("=" * 60)
    
    # Add-On products found in the system
    addon_products = [
        {'Id': '01tdp000006HfptAAC', 'Name': 'DCS Policy Manager Desktop', 'ProductCode': 'CYB-DCS-PMD-ADD'},
        {'Id': '01tdp000006HfpuAAC', 'Name': 'DCS Policy Manager M365', 'ProductCode': 'CYB-DCS-PM365-ADD'},
        {'Id': '01tdp000006HfpsAAC', 'Name': 'Fortra Mail for iOS', 'ProductCode': 'CYB-DCS-MAIL-ADD'}
    ]
    
    # Add-On Modules category ID
    addon_category_id = '0ZGdp00000007JFFAY'
    
    print(f"\nCreating assignments for {len(addon_products)} Add-On products:")
    for prod in addon_products:
        print(f"  - {prod['Name']} ({prod['ProductCode']})")
    
    # Create ProductCategoryProduct records
    records = []
    for product in addon_products:
        records.append({
            'ProductCategoryId': addon_category_id,
            'ProductId': product['Id']
        })
    
    # Save to CSV
    df = pd.DataFrame(records)
    csv_file = Path('data/addon_category_assignments.csv')
    df.to_csv(csv_file, index=False)
    
    print(f"\nInserting {len(records)} ProductCategoryProduct records...")
    
    # Insert records
    cmd_insert = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductCategoryProduct',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result_insert = subprocess.run(cmd_insert, capture_output=True, text=True)
    
    if result_insert.returncode == 0:
        print("✓ Successfully created ProductCategoryProduct records")
        
        # Show all category assignments
        print("\n" + "-" * 60)
        print("ALL PRODUCT CATEGORY ASSIGNMENTS:")
        print("-" * 60)
        
        query = """
        SELECT ProductCategory.Name, Product.Name, Product.ProductCode
        FROM ProductCategoryProduct
        ORDER BY ProductCategory.Name, Product.Name
        """
        
        cmd_show = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', 'fortradp2'
        ]
        
        subprocess.run(cmd_show)
        
    else:
        print(f"✗ Failed to create records: {result_insert.stderr}")
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
