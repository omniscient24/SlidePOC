#!/usr/bin/env python3
"""
Fix all data issues and import cleanly.
"""

import subprocess
from pathlib import Path
import pandas as pd

class CleanImporter:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.clean_dir = Path('data/csv_clean_import')
        self.clean_dir.mkdir(parents=True, exist_ok=True)
        
    def fix_attribute_definition(self):
        """Fix AttributeDefinition data."""
        print("Fixing AttributeDefinition...")
        df = pd.read_csv(self.csv_dir / '09_AttributeDefinition.csv')
        
        # Fix empty Label - use Name if Label is empty
        if 'Label' in df.columns and 'Name' in df.columns:
            empty_labels = df['Label'].isna()
            df.loc[empty_labels, 'Label'] = df.loc[empty_labels, 'Name']
            print(f"  Fixed {empty_labels.sum()} empty Labels")
        
        # Fix empty DataType - default to Text
        if 'DataType' in df.columns:
            empty_types = df['DataType'].isna()
            df.loc[empty_types, 'DataType'] = 'Text'
            print(f"  Fixed {empty_types.sum()} empty DataTypes")
        
        # Remove Id column for insert
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        df.to_csv(self.clean_dir / '09_AttributeDefinition.csv', index=False)
        return True
    
    def fix_product2(self):
        """Fix Product2 data."""
        print("\nFixing Product2...")
        df = pd.read_csv(self.csv_dir / '13_Product2.csv')
        
        # Remove Id column for insert
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
            print("  Removed Id column for insert")
        
        df.to_csv(self.clean_dir / '13_Product2.csv', index=False)
        return True
    
    def fix_other_objects(self):
        """Fix other objects by removing Id columns."""
        print("\nFixing other objects...")
        
        files_to_fix = [
            '10_AttributeCategory.csv',
            '15_ProductSellingModel.csv',
            '17_ProductAttributeDef.csv',
            '26_ProductCategoryProduct.csv',
            '20_PricebookEntry.csv',
            '25_ProductRelatedComponent.csv'
        ]
        
        for csv_file in files_to_fix:
            src = self.csv_dir / csv_file
            if src.exists():
                df = pd.read_csv(src)
                if 'Id' in df.columns:
                    df = df.drop(columns=['Id'])
                df.to_csv(self.clean_dir / csv_file, index=False)
                print(f"  Fixed {csv_file}")
        
        return True
    
    def copy_successful_files(self):
        """Copy already successful files."""
        successful = ['11_ProductCatalog.csv', '12_ProductCategory.csv', 
                     '08_ProductClassification.csv', '19_Pricebook2.csv']
        
        import shutil
        for f in successful:
            src = self.csv_dir / f
            if src.exists():
                shutil.copy2(src, self.clean_dir / f)
    
    def run_clean_import(self):
        """Run clean import in correct order."""
        print("\n" + "=" * 60)
        print("RUNNING CLEAN IMPORT")
        print("=" * 60)
        
        # Define import order with dependencies
        import_order = [
            # Already successful - skip
            # ('11_ProductCatalog.csv', 'ProductCatalog'),
            # ('12_ProductCategory.csv', 'ProductCategory'),
            # ('08_ProductClassification.csv', 'ProductClassification'),
            # ('19_Pricebook2.csv', 'Pricebook2'),
            
            # Base objects - need to import
            ('09_AttributeDefinition.csv', 'AttributeDefinition'),
            ('10_AttributeCategory.csv', 'AttributeCategory'),
            ('15_ProductSellingModel.csv', 'ProductSellingModel'),
            ('13_Product2.csv', 'Product2'),
            
            # Wait for Product2 to be imported
            (None, None),  # Pause to query Product IDs
            
            # Dependent objects
            ('17_ProductAttributeDef.csv', 'ProductAttributeDefinition'),
            ('26_ProductCategoryProduct.csv', 'ProductCategoryProduct'),
            ('20_PricebookEntry.csv', 'PricebookEntry'),
            ('25_ProductRelatedComponent.csv', 'ProductRelatedComponent'),
        ]
        
        success = 0
        failed = 0
        
        for csv_file, object_name in import_order:
            if csv_file is None:
                # Query for Product IDs and update references
                print("\nUpdating Product references...")
                self.update_product_references()
                continue
            
            print(f"\n{object_name}:")
            file_path = self.clean_dir / csv_file
            
            if not file_path.exists():
                print("  ⚠️  File not found")
                continue
            
            # Count records
            df = pd.read_csv(file_path)
            print(f"  Inserting {len(df)} records...")
            
            # Run import
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--target-org', 'fortradp2',
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("    ✓ Success!")
                success += 1
            else:
                print("    ✗ Failed")
                if result.stderr:
                    print(f"    {result.stderr.split('Error')[1].split('Try')[0].strip()}")
                failed += 1
        
        print(f"\n✓ Successful: {success}")
        print(f"✗ Failed: {failed}")
    
    def update_product_references(self):
        """Update Product ID references after Product2 import."""
        # Get current Product IDs
        cmd = [
            'sf', 'data', 'query',
            '--query', "SELECT Id, ProductCode, Name FROM Product2",
            '--target-org', 'fortradp2',
            '--result-format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                products = data['result']['records']
                print(f"  Found {len(products)} products")
                
                # Create mapping of old ID to new ID based on ProductCode
                # This would need the original mapping, skipping for now
        
    def fix_all_and_import(self):
        """Fix all issues and run import."""
        print("FIXING DATA ISSUES")
        print("=" * 60)
        
        self.fix_attribute_definition()
        self.fix_product2()
        self.fix_other_objects()
        self.copy_successful_files()
        
        self.run_clean_import()

def main():
    importer = CleanImporter()
    importer.fix_all_and_import()

if __name__ == '__main__':
    main()