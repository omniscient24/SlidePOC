#\!/usr/bin/env python3
"""
Identify Add-On products and create ProductCategoryProduct records.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

def get_addon_products():
    """Get the Product IDs for Add-On products."""
    
    addon_product_names = [
        'DCS Policy Manager Desktop',  # Note: actual name in system
        'DCS Policy Manager M365',      # Note: actual name in system
        'Fortra Mail for iOS',
        'SAT Managed Service Starter Pack',
        'SAT Awareness Campaigns',
        'SAT Phishing Campaigns',
        'SAT Post Quiz',
        'SAT Hourly Services',
        'Security Advisory Services - Basic',
        'Security Advisory Services - Standard',
        'Security Advisory Services - Advanced'
    ]
    
    # Query all products to match names
    query = "SELECT Id, Name, ProductCode FROM Product2 ORDER BY Name"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    addon_products = []
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            all_products = data['result']['records']
            
            print("Matching Add-On products:")
            print("-" * 60)
            
            for product in all_products:
                # Check if product name matches any addon pattern
                product_name = product['Name']
                
                # Direct matches
                if product_name in addon_product_names:
                    addon_products.append(product)
                    print(f"✓ {product['Name']} ({product['ProductCode']})")
                # Handle naming variations
                elif 'Policy Manager' in product_name and ('Desktop' in product_name or 'M365' in product_name):
                    addon_products.append(product)
                    print(f"✓ {product['Name']} ({product['ProductCode']})")
                elif product_name.startswith('SAT ') and any(name.endswith(product_name.split('SAT ')[-1]) for name in addon_product_names):
                    addon_products.append(product)
                    print(f"✓ {product['Name']} ({product['ProductCode']})")
                elif 'Security Advisory Services' in product_name:
                    addon_products.append(product)
                    print(f"✓ {product['Name']} ({product['ProductCode']})")
    
    return addon_products

def main():
    print("=" * 60)
    print("CREATING ADD-ON PRODUCT CATEGORY ASSIGNMENTS")
    print("=" * 60)
    
    # Get Add-On products
    addon_products = get_addon_products()
    
    if not addon_products:
        print("\n⚠️  No matching Add-On products found\!")
        
        # Show all products for reference
        print("\nAll products in org:")
        cmd = ['sf', 'data', 'query', '--query', 'SELECT Name FROM Product2 ORDER BY Name', '--target-org', 'fortradp2']
        subprocess.run(cmd)
        return
    
    print(f"\nFound {len(addon_products)} Add-On products")
    
    # Get Add-On Module category ID
    query_cat = "SELECT Id, Name FROM ProductCategory WHERE Name = 'Add-On Modules'"
    
    cmd_cat = [
        'sf', 'data', 'query',
        '--query', query_cat,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result_cat = subprocess.run(cmd_cat, capture_output=True, text=True)
    
    if result_cat.returncode == 0:
        data_cat = json.loads(result_cat.stdout)
        if 'result' in data_cat and 'records' in data_cat['result'] and len(data_cat['result']['records']) > 0:
            addon_category_id = data_cat['result']['records'][0]['Id']
            print(f"\nAdd-On Modules Category ID: {addon_category_id}")
            
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
            
            print(f"\nCreating {len(records)} ProductCategoryProduct records...")
            
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
                
                # Verify count
                verify_query = "SELECT COUNT() FROM ProductCategoryProduct"
                cmd_verify = [
                    'sf', 'data', 'query',
                    '--query', verify_query,
                    '--target-org', 'fortradp2',
                    '--json'
                ]
                
                result_verify = subprocess.run(cmd_verify, capture_output=True, text=True)
                if result_verify.returncode == 0:
                    data_verify = json.loads(result_verify.stdout)
                    if 'result' in data_verify:
                        count = data_verify['result']['totalSize']
                        print(f"\nTotal ProductCategoryProduct records: {count}")
            else:
                print(f"✗ Failed to create records: {result_insert.stderr}")
            
            # Clean up
            csv_file.unlink()

if __name__ == '__main__':
    main()
