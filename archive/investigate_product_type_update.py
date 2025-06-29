#!/usr/bin/env python3
"""
Investigate how to handle Product2.Type field for bundles.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

class ProductTypeSolution:
    def __init__(self):
        self.target_org = 'fortradp2'
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        
    def check_existing_products_detail(self):
        """Check existing products in detail."""
        print("=" * 60)
        print("EXISTING PRODUCT2 RECORDS ANALYSIS")
        print("=" * 60)
        
        query = """
        SELECT Id, Name, ProductCode, Type, IsActive, 
               ConfigureDuringSale, CreatedDate
        FROM Product2
        ORDER BY CreatedDate DESC
        LIMIT 10
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                
                print(f"\nSample of existing products (newest first):")
                for rec in records[:5]:
                    print(f"\n- {rec.get('Name')} ({rec.get('ProductCode')})")
                    print(f"  Id: {rec.get('Id')}")
                    print(f"  Type: {rec.get('Type', 'NULL')}")
                    print(f"  Created: {rec.get('CreatedDate')}")
    
    def test_type_update(self):
        """Test if we can update Type on existing record."""
        print("\n" + "=" * 60)
        print("TESTING TYPE FIELD UPDATE")
        print("=" * 60)
        
        # Get a test product
        query = "SELECT Id, Name, Type FROM Product2 WHERE Type = null LIMIT 1"
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result'] and data['result']['records']:
                test_product = data['result']['records'][0]
                print(f"\nTest product: {test_product.get('Name')}")
                print(f"Current Type: {test_product.get('Type', 'NULL')}")
                
                # Try to update
                update_cmd = [
                    'sf', 'data', 'update', 'record',
                    '--sobject', 'Product2',
                    '--record-id', test_product['Id'],
                    '--values', 'Type=Bundle',
                    '--target-org', self.target_org
                ]
                
                print("\nAttempting to update Type to 'Bundle'...")
                update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                
                if update_result.returncode == 0:
                    print("✓ Update successful!")
                else:
                    print(f"✗ Update failed: {update_result.stderr}")
                    if "not updateable" in update_result.stderr.lower():
                        print("\nCONFIRMED: Type field cannot be updated after creation")
    
    def analyze_solution(self):
        """Analyze the solution for Bundle products."""
        print("\n" + "=" * 60)
        print("SOLUTION ANALYSIS: BUNDLE PRODUCTS")
        print("=" * 60)
        
        print("\nSince Product2.Type is NOT updateable after creation, you have two options:")
        
        print("\n1. DELETE AND RECREATE Products as Bundles:")
        print("   - Export existing product data")
        print("   - Delete products that need to be bundles")
        print("   - Recreate them with Type='Bundle'")
        print("   - Restore all relationships and pricing")
        print("   Pros: Clean approach, ensures proper setup")
        print("   Cons: Requires handling dependencies, may affect historical data")
        
        print("\n2. CREATE NEW Bundle Products:")
        print("   - Keep existing products as-is")
        print("   - Create new products with Type='Bundle'")
        print("   - Use ProductRelatedComponent to link existing products as components")
        print("   - Update references to point to new bundle products")
        print("   Pros: Preserves existing data, safer approach")
        print("   Cons: May result in duplicate products")
        
        print("\n3. REQUIRED STEPS for Bundle Creation:")
        print("   a) Set Type='Bundle' at creation time")
        print("   b) Set ConfigureDuringSale='Allowed' (typically)")
        print("   c) Create ProductSellingModelOption records")
        print("   d) Create ProductRelatedComponent records for bundle components")
        print("   e) Configure pricing at bundle or component level")
        
        # Check if we have any bundle candidates
        self.identify_bundle_candidates()
    
    def identify_bundle_candidates(self):
        """Identify which products should be bundles."""
        print("\n" + "-" * 40)
        print("Identifying Bundle Candidates...")
        
        # Read Product2 sheet
        df = pd.read_excel(self.workbook_path, sheet_name='13_Product2')
        df.columns = df.columns.str.replace('*', '')
        
        # Look for products that might be bundles based on naming
        bundle_keywords = ['bundle', 'package', 'suite', 'kit', 'combo', 'set']
        
        bundle_candidates = []
        for idx, row in df.iterrows():
            name = str(row.get('Name', '')).lower()
            for keyword in bundle_keywords:
                if keyword in name:
                    bundle_candidates.append({
                        'Name': row.get('Name'),
                        'ProductCode': row.get('ProductCode'),
                        'Type': row.get('Type')
                    })
                    break
        
        if bundle_candidates:
            print(f"\nFound {len(bundle_candidates)} potential bundle products:")
            for prod in bundle_candidates:
                print(f"  - {prod['Name']} ({prod['ProductCode']}) - Current Type: {prod['Type']}")
        else:
            print("\nNo obvious bundle candidates found based on naming")
        
        # Check ProductRelatedComponent sheet
        prc_sheet = '25_ProductRelatedComponent'
        if prc_sheet in pd.ExcelFile(self.workbook_path).sheet_names:
            df_prc = pd.read_excel(self.workbook_path, sheet_name=prc_sheet)
            if not df_prc.empty:
                print(f"\nProductRelatedComponent has {len(df_prc)} records")
                print("These define bundle structures")
    
    def create_bundle_example(self):
        """Create example of how to properly create a bundle."""
        print("\n" + "=" * 60)
        print("EXAMPLE: Creating a Bundle Product")
        print("=" * 60)
        
        print("\nTo create a bundle product in Revenue Cloud:")
        print("\n1. Product2 record (at creation):")
        print("   {")
        print("     'Name': 'Security Suite Bundle',")
        print("     'ProductCode': 'SEC-BUNDLE-001',")
        print("     'Type': 'Bundle',  // MUST be set at creation")
        print("     'IsActive': true,")
        print("     'ConfigureDuringSale': 'Allowed',")
        print("     'Description': 'Complete security solution bundle'")
        print("   }")
        
        print("\n2. ProductSellingModelOption (link to selling model):")
        print("   {")
        print("     'Product2Id': '<Bundle_Product_Id>',")
        print("     'ProductSellingModelId': '<Appropriate_Selling_Model_Id>'")
        print("   }")
        
        print("\n3. ProductRelatedComponent (define components):")
        print("   {")
        print("     'ParentProductId': '<Bundle_Product_Id>',")
        print("     'ChildProductId': '<Component_Product_Id>',")
        print("     'ChildProductRole': 'Component',")
        print("     'MinQuantity': 1,")
        print("     'MaxQuantity': 1,")
        print("     'DefaultQuantity': 1")
        print("   }")

def main():
    solution = ProductTypeSolution()
    
    # Check existing products
    solution.check_existing_products_detail()
    
    # Test if Type can be updated
    solution.test_type_update()
    
    # Analyze solution
    solution.analyze_solution()
    
    # Show example
    solution.create_bundle_example()

if __name__ == '__main__':
    main()