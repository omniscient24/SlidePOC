#!/usr/bin/env python3
"""
Create ProductSellingModelOption records for the new bundle products.
"""

import subprocess
import pandas as pd
from pathlib import Path

def create_bundle_psmo():
    """Create ProductSellingModelOption records for bundle products."""
    print("=" * 60)
    print("CREATING PRODUCTSELLINGMODELOPTION FOR BUNDLES")
    print("=" * 60)
    
    # Bundle products that need PSMO
    bundle_products = [
        {'Product2Id': '01tdp000006JEGjAAO', 'Name': 'DCS Advanced (V2)'},
        {'Product2Id': '01tdp000006JEGlAAO', 'Name': 'DCS Essentials (V2)'},
        {'Product2Id': '01tdp000006JEGkAAO', 'Name': 'DCS Elite (V2)'}
    ]
    
    # ProductSellingModelId from the failed records
    selling_model_id = '0jPdp00000000zREAQ'  # Term Based - Yearly
    
    print(f"\nCreating PSMO records for {len(bundle_products)} bundle products")
    print(f"ProductSellingModelId: {selling_model_id}")
    
    # Create PSMO data
    psmo_data = []
    for product in bundle_products:
        psmo_data.append({
            'Product2Id': product['Product2Id'],
            'ProductSellingModelId': selling_model_id
        })
        print(f"  - {product['Name']}")
    
    # Create CSV
    df = pd.DataFrame(psmo_data)
    csv_file = Path('data/bundle_psmo.csv')
    df.to_csv(csv_file, index=False)
    
    # Insert PSMO records
    print("\nInserting ProductSellingModelOption records...")
    
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductSellingModelOption',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductSellingModelOption records")
        
        # Now insert the PricebookEntry records
        create_pricebook_entries()
    else:
        print(f"✗ Failed to create PSMO: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

def create_pricebook_entries():
    """Create the PricebookEntry records for bundles."""
    print("\n" + "=" * 60)
    print("CREATING PRICEBOOKENTRY FOR BUNDLES")
    print("=" * 60)
    
    # PricebookEntry data for bundles
    pbe_data = [
        {
            'Product2Id': '01tdp000006JEGjAAO',
            'Pricebook2Id': '01sa5000001vuxlAAA',
            'ProductSellingModelId': '0jPdp00000000zREAQ',
            'UnitPrice': 5000,
            'IsActive': True
        },
        {
            'Product2Id': '01tdp000006JEGlAAO',
            'Pricebook2Id': '01sa5000001vuxlAAA',
            'ProductSellingModelId': '0jPdp00000000zREAQ',
            'UnitPrice': 5000,
            'IsActive': True
        },
        {
            'Product2Id': '01tdp000006JEGkAAO',
            'Pricebook2Id': '01sa5000001vuxlAAA',
            'ProductSellingModelId': '0jPdp00000000zREAQ',
            'UnitPrice': 5000,
            'IsActive': True
        }
    ]
    
    # Create CSV
    df = pd.DataFrame(pbe_data)
    csv_file = Path('data/bundle_pbe.csv')
    df.to_csv(csv_file, index=False)
    
    print("\nInserting PricebookEntry records...")
    
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'PricebookEntry',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created PricebookEntry records for bundles")
    else:
        print(f"✗ Failed to create PBE: {result.stderr}")
    
    # Clean up
    csv_file.unlink()
    
    # Verify final count
    verify_final_count()

def verify_final_count():
    """Verify the final PricebookEntry count."""
    print("\n" + "=" * 60)
    print("VERIFYING FINAL STATE")
    print("=" * 60)
    
    import json
    
    query = "SELECT COUNT() FROM PricebookEntry"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data:
            count = data['result']['totalSize']
            print(f"\n✓ Total PricebookEntry records: {count}")
            print("  (Was 19, should now be 22)")
    
    # Check bundle products have entries
    query2 = """
    SELECT Product2.Name, Product2.ProductCode, UnitPrice
    FROM PricebookEntry
    WHERE Product2.Type = 'Bundle'
    ORDER BY Product2.Name
    """
    
    cmd2 = [
        'sf', 'data', 'query',
        '--query', query2,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    
    if result2.returncode == 0:
        data2 = json.loads(result2.stdout)
        if 'result' in data2 and 'records' in data2['result']:
            bundles = data2['result']['records']
            
            print(f"\n✓ Bundle products with PricebookEntry: {len(bundles)}")
            for bundle in bundles:
                print(f"  - {bundle['Product2']['Name']} ({bundle['Product2']['ProductCode']}): ${bundle['UnitPrice']}")

if __name__ == '__main__':
    create_bundle_psmo()