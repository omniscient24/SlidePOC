#\!/usr/bin/env python3
"""
Check final state and confirm no duplicates.
"""

import subprocess
import json
from datetime import datetime

def main():
    print("=" * 70)
    print("FINAL STATE VERIFICATION")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Expected counts after all operations
    expected_counts = {
        'ProductCatalog': 3,
        'ProductCategory': 5,
        'ProductClassification': 7,
        'AttributeDefinition': 20,
        'AttributeCategory': 5,
        'AttributePicklist': 10,
        'AttributePicklistValue': 39,
        'ProductSellingModel': 9,
        'Product2': 25,
        'ProductAttributeDefinition': 17,
        'Pricebook2': 2,
        'PricebookEntry': 22,  # Increased by 3 (bundle products)
        'ProductCategoryProduct': 8,  # Increased by 3 (Add-On assignments)
        'ProductRelatedComponent': 0,
        'ProductSellingModelOption': 24  # Increased by 3 (bundle products)
    }
    
    print("OBJECT RECORD COUNTS:")
    print("-" * 60)
    print(f"{'Object':<35} {'Expected':>8} {'Actual':>8} {'Status':>10}")
    print("-" * 60)
    
    all_correct = True
    
    for obj_name, expected in expected_counts.items():
        query = f"SELECT COUNT() FROM {obj_name}"
        
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
                actual = data['result']['totalSize']
                
                if actual == expected:
                    status = "✓ Correct"
                else:
                    status = f"✗ {actual - expected:+d}"
                    all_correct = False
                
                print(f"{obj_name:<35} {expected:>8} {actual:>8} {status:>10}")
        else:
            print(f"{obj_name:<35} {expected:>8} {'Error':>8} {'✗':>10}")
            all_correct = False
    
    print("-" * 60)
    
    if all_correct:
        print("\n✅ VERIFICATION PASSED")
        print("All objects have the expected record counts.")
        print("No duplicates were created during the upsert process.")
    else:
        print("\n⚠️  VERIFICATION FAILED")
        print("Some objects have unexpected record counts.")
    
    # Show recent additions
    print("\n" + "=" * 70)
    print("RECENT ADDITIONS")
    print("=" * 70)
    
    print("\nBundle Products (Type='Bundle'):")
    query_bundles = "SELECT Name, ProductCode FROM Product2 WHERE Type = 'Bundle' ORDER BY Name"
    cmd_bundles = ['sf', 'data', 'query', '--query', query_bundles, '--target-org', 'fortradp2']
    subprocess.run(cmd_bundles)
    
    print("\nAdd-On Product Categorizations:")
    query_addons = """
    SELECT Product.Name, Product.ProductCode 
    FROM ProductCategoryProduct 
    WHERE ProductCategory.Name = 'Add-Ons'
    ORDER BY Product.Name
    """
    cmd_addons = ['sf', 'data', 'query', '--query', query_addons, '--target-org', 'fortradp2']
    subprocess.run(cmd_addons)

if __name__ == '__main__':
    main()
