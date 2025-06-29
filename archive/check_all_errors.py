#!/usr/bin/env python3
"""
Check all error details and provide solutions.
"""

import subprocess
import pandas as pd
from pathlib import Path

class ErrorAnalyzer:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        
    def analyze_csv_fields(self):
        """Analyze CSV fields against Salesforce objects."""
        print("=" * 60)
        print("ANALYZING CSV FIELDS")
        print("=" * 60)
        
        # Objects that failed
        failed_objects = {
            'AttributeDefinition': '09_AttributeDefinition.csv',
            'AttributeCategory': '10_AttributeCategory.csv', 
            'ProductSellingModel': '15_ProductSellingModel.csv',
            'Product2': '13_Product2.csv',
            'ProductAttributeDefinition': '17_ProductAttributeDef.csv',
            'ProductCategoryProduct': '26_ProductCategoryProduct.csv',
            'PricebookEntry': '20_PricebookEntry.csv',
            'ProductRelatedComponent': '25_ProductRelatedComponent.csv'
        }
        
        for obj_name, csv_file in failed_objects.items():
            print(f"\n{obj_name}:")
            csv_path = self.csv_dir / csv_file
            
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                print(f"  Records: {len(df)}")
                print(f"  Columns: {', '.join(df.columns)}")
                
                # Check for empty required fields
                if obj_name == 'Product2':
                    # Check key fields
                    for field in ['Name', 'ProductCode']:
                        if field in df.columns:
                            empty = df[field].isna().sum()
                            if empty > 0:
                                print(f"  ⚠️  {field} has {empty} empty values")
                
                elif obj_name == 'AttributeDefinition':
                    # Check required fields
                    for field in ['Name', 'Code', 'Label', 'DataType']:
                        if field in df.columns:
                            empty = df[field].isna().sum()
                            if empty > 0:
                                print(f"  ⚠️  {field} has {empty} empty values")
                        else:
                            print(f"  ❌ Missing required field: {field}")
                
                elif obj_name == 'ProductSellingModel':
                    # Check required fields
                    for field in ['Name', 'SellingModelType', 'Status']:
                        if field in df.columns:
                            empty = df[field].isna().sum()
                            if empty > 0:
                                print(f"  ⚠️  {field} has {empty} empty values")
                        else:
                            print(f"  ❌ Missing required field: {field}")
                
                elif obj_name == 'PricebookEntry':
                    # Check required fields
                    for field in ['Product2Id', 'Pricebook2Id', 'UnitPrice']:
                        if field in df.columns:
                            empty = df[field].isna().sum()
                            if empty > 0:
                                print(f"  ⚠️  {field} has {empty} empty values")
                        else:
                            print(f"  ❌ Missing required field: {field}")
                
                elif obj_name == 'ProductRelatedComponent':
                    # Check required fields
                    for field in ['ParentProductId', 'ChildProductId', 'ProductRelationshipTypeId']:
                        if field in df.columns:
                            empty = df[field].isna().sum()
                            if empty > 0:
                                print(f"  ⚠️  {field} has {empty} empty values")
                        else:
                            print(f"  ❌ Missing required field: {field}")
    
    def check_reference_ids(self):
        """Check if reference IDs exist."""
        print("\n\nCHECKING REFERENCE IDS")
        print("=" * 60)
        
        # Check Product IDs
        cmd = ['sf', 'data', 'query', 
               '--query', 'SELECT Id, Name FROM Product2',
               '--target-org', 'fortradp2',
               '--result-format', 'json']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                products = data['result']['records']
                print(f"\nFound {len(products)} Product2 records")
                product_ids = {p['Id'] for p in products}
                
                # Check if CSV references exist
                prc_df = pd.read_csv(self.csv_dir / '25_ProductRelatedComponent.csv')
                if 'ParentProductId' in prc_df.columns:
                    missing_parents = prc_df[~prc_df['ParentProductId'].isin(product_ids)]['ParentProductId'].unique()
                    if len(missing_parents) > 0:
                        print(f"  ⚠️  {len(missing_parents)} ParentProductIds don't exist")
                
                if 'ChildProductId' in prc_df.columns:
                    missing_children = prc_df[~prc_df['ChildProductId'].isin(product_ids)]['ChildProductId'].unique()
                    if len(missing_children) > 0:
                        print(f"  ⚠️  {len(missing_children)} ChildProductIds don't exist")
    
    def suggest_fixes(self):
        """Suggest fixes for common issues."""
        print("\n\nSUGGESTED FIXES")
        print("=" * 60)
        
        print("\n1. For Product2:")
        print("   - Ensure all products have unique ProductCode values")
        print("   - Remove any invalid fields from CSV")
        print("   - Use insert instead of upsert for new products")
        
        print("\n2. For AttributeDefinition:")
        print("   - Ensure Code field is populated and unique")
        print("   - Verify DataType is valid (Text, Number, Date, etc.)")
        
        print("\n3. For ProductSellingModel:")
        print("   - Ensure SellingModelType is valid")
        print("   - Set Status to 'Active' or 'Draft'")
        
        print("\n4. For Junction Objects (ProductRelatedComponent, etc.):")
        print("   - Ensure parent records exist first")
        print("   - Use insert only (not upsert)")
        print("   - Verify all lookup IDs are valid")

def main():
    analyzer = ErrorAnalyzer()
    analyzer.analyze_csv_fields()
    analyzer.check_reference_ids()
    analyzer.suggest_fixes()

if __name__ == '__main__':
    main()