#!/usr/bin/env python3
"""
Run final upsert with fixed CSV files.
"""

import subprocess
from pathlib import Path
import pandas as pd

class FinalUpsertRunner:
    def __init__(self):
        self.csv_dir = Path('data/csv_fixed_output')
        self.target_org = 'fortradp2'
        
        # Objects in dependency order
        self.upsert_order = [
            # Pass 1 - Base objects
            ('11_ProductCatalog.csv', 'ProductCatalog', 'Id'),
            ('12_ProductCategory.csv', 'ProductCategory', 'Id'),
            ('08_ProductClassification.csv', 'ProductClassification', None),  # Insert only
            ('09_AttributeDefinition.csv', 'AttributeDefinition', 'Id'),
            ('10_AttributeCategory.csv', 'AttributeCategory', 'Id'),
            ('15_ProductSellingModel.csv', 'ProductSellingModel', 'Id'),
            ('13_Product2.csv', 'Product2', 'Id'),
            ('19_Pricebook2.csv', 'Pricebook2', 'Id'),
            
            # Pass 2 - Dependent objects
            ('17_ProductAttributeDef.csv', 'ProductAttributeDefinition', 'Id'),
            ('26_ProductCategoryProduct.csv', 'ProductCategoryProduct', None),  # Insert only
            ('20_PricebookEntry.csv', 'PricebookEntry', None),  # Insert only
            ('25_ProductRelatedComponent.csv', 'ProductRelatedComponent', None),  # Insert only
        ]
    
    def run_operation(self, csv_file, object_name, id_field):
        """Run upsert or insert operation."""
        file_path = self.csv_dir / csv_file
        
        if not file_path.exists():
            print(f"  ⚠️  File not found: {csv_file}")
            return False
        
        # Check if we have records
        df = pd.read_csv(file_path)
        if len(df) == 0:
            print(f"  - No records to process")
            return True
        
        if id_field and 'Id' in df.columns and df['Id'].notna().any():
            # Upsert existing records
            print(f"  Upserting {len(df)} records...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--external-id', id_field,
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        else:
            # Insert new records
            print(f"  Inserting {len(df)} records...")
            # Remove Id column if empty
            if 'Id' in df.columns:
                df = df.drop(columns=['Id'])
                df.to_csv(file_path, index=False)
            
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"    ✓ Success!")
            return True
        else:
            print(f"    ✗ Failed: {result.stderr.strip()[:100]}...")
            return False
    
    def run_final_upsert(self):
        """Run the final upsert process."""
        print("=" * 60)
        print("FINAL UPSERT PROCESS")
        print("=" * 60)
        print(f"Using fixed CSV files from: {self.csv_dir}\n")
        
        success = 0
        failed = 0
        
        for csv_file, object_name, id_field in self.upsert_order:
            print(f"\n{object_name}:")
            
            if self.run_operation(csv_file, object_name, id_field):
                success += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"✓ Successful: {success}")
        print(f"✗ Failed: {failed}")
        print(f"Total: {len(self.upsert_order)}")
        
        if failed == 0:
            print("\n🎉 All operations completed successfully!")
            print("\nYour Revenue Cloud data has been upserted!")
        else:
            print(f"\n⚠️  {failed} operations failed.")
            print("\nTroubleshooting tips:")
            print("1. Check if required fields are missing")
            print("2. Verify data types match Salesforce expectations")
            print("3. Ensure referenced records exist (for lookups)")
            print("4. Check field-level security permissions")

def main():
    runner = FinalUpsertRunner()
    runner.run_final_upsert()

if __name__ == '__main__':
    main()