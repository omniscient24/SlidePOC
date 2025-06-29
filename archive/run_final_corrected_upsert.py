#!/usr/bin/env python3
"""
Run final upsert with correct field mappings based on actual data.
"""

import subprocess
from pathlib import Path
import pandas as pd

class FinalCorrectedUpsertRunner:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.target_org = 'fortradp2'
        
        # Objects with their correct external ID approach
        self.upsert_config = [
            # Pass 1 - Base objects
            ('11_ProductCatalog.csv', 'ProductCatalog', 'Id', 'upsert'),  # Use Id for existing records
            ('12_ProductCategory.csv', 'ProductCategory', 'Id', 'upsert'),  # Use Id for existing records
            ('08_ProductClassification.csv', 'ProductClassification', None, 'insert'),  # Insert only
            ('09_AttributeDefinition.csv', 'AttributeDefinition', 'Code', 'upsert'),  # Use Code as external ID
            ('10_AttributeCategory.csv', 'AttributeCategory', 'Id', 'upsert'),  # Use Id for existing records
            ('15_ProductSellingModel.csv', 'ProductSellingModel', 'Id', 'upsert'),  # Use Id for existing records
            ('13_Product2.csv', 'Product2', 'ProductCode', 'upsert'),  # Use ProductCode as external ID
            ('19_Pricebook2.csv', 'Pricebook2', 'Id', 'upsert'),  # Use Id for existing records
            
            # Pass 2 - Dependent objects (insert only)
            ('17_ProductAttributeDef.csv', 'ProductAttributeDefinition', None, 'insert'),
            ('26_ProductCategoryProduct.csv', 'ProductCategoryProduct', None, 'insert'),
            ('20_PricebookEntry.csv', 'PricebookEntry', None, 'insert'),
            ('25_ProductRelatedComponent.csv', 'ProductRelatedComponent', None, 'insert'),
        ]
    
    def prepare_csv_for_upsert(self, csv_file, object_name, external_id_field):
        """Prepare CSV file for upsert."""
        file_path = self.csv_dir / csv_file
        if not file_path.exists():
            return None
            
        df = pd.read_csv(file_path)
        
        # Special handling for AttributeDefinition - ensure Code is populated
        if object_name == 'AttributeDefinition' and external_id_field == 'Code':
            if 'Code' in df.columns:
                empty_codes = df['Code'].isna()
                if empty_codes.any() and 'Name' in df.columns:
                    # Generate Code from Name
                    df.loc[empty_codes, 'Code'] = df.loc[empty_codes, 'Name'].str.upper().str.replace(' ', '_').str.replace('-', '_')
                    df.to_csv(file_path, index=False)
                    print(f"    Generated {empty_codes.sum()} Code values from Name")
        
        # For Product2, ensure ProductCode is populated
        elif object_name == 'Product2' and external_id_field == 'ProductCode':
            if 'ProductCode' in df.columns:
                empty_codes = df['ProductCode'].isna()
                if empty_codes.any():
                    print(f"    ⚠️  Warning: {empty_codes.sum()} products have no ProductCode")
        
        return file_path
    
    def run_operation(self, csv_file, object_name, external_id_field, operation):
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
        
        # Prepare CSV if needed
        if external_id_field and external_id_field not in ['Id', None]:
            file_path = self.prepare_csv_for_upsert(csv_file, object_name, external_id_field)
            if not file_path:
                return False
        
        if operation == 'upsert' and external_id_field:
            # For Id-based upserts, only upsert if we have existing Ids
            if external_id_field == 'Id' and 'Id' in df.columns:
                # Check if we have any non-empty Ids
                has_ids = df['Id'].notna().any()
                if not has_ids:
                    print(f"  No existing Ids found, switching to insert")
                    operation = 'insert'
        
        if operation == 'upsert' and external_id_field:
            print(f"  Upserting {len(df)} records using {external_id_field}...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--external-id', external_id_field,
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        else:
            # Insert new records
            print(f"  Inserting {len(df)} records...")
            # Remove Id column for inserts if present
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
            # Try to extract job results
            if 'successfully processed' in result.stdout:
                print(f"    {result.stdout.strip()}")
            elif 'Job ID' in result.stdout:
                # Extract job ID
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Job ID' in line:
                        print(f"    {line.strip()}")
            return True
        else:
            print(f"    ✗ Failed")
            # Extract specific error
            if result.stderr:
                error_lines = result.stderr.split('\n')
                for line in error_lines:
                    if line.strip() and 'Try this:' not in line and 'Warning:' not in line:
                        print(f"    Error: {line.strip()}")
            return False
    
    def run_final_upsert(self):
        """Run the final corrected upsert process."""
        print("=" * 60)
        print("FINAL CORRECTED UPSERT PROCESS")
        print("=" * 60)
        print(f"Using CSV files from: {self.csv_dir}\n")
        
        print("External ID Strategy:")
        print("-" * 40)
        print("Product2: ProductCode (standard field)")
        print("AttributeDefinition: Code (will generate if missing)")
        print("Others: Id (for updates) or insert new records")
        print()
        
        success = 0
        failed = 0
        failed_objects = []
        
        print("PASS 1: Base Objects")
        print("-" * 40)
        
        for i, (csv_file, object_name, external_id, operation) in enumerate(self.upsert_config):
            if i == 8:  # Start of Pass 2
                print("\n\nPASS 2: Dependent Objects")
                print("-" * 40)
            
            print(f"\n{object_name}:")
            
            if self.run_operation(csv_file, object_name, external_id, operation):
                success += 1
            else:
                failed += 1
                failed_objects.append(object_name)
        
        # Summary
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"✓ Successful: {success}")
        print(f"✗ Failed: {failed}")
        print(f"Total: {len(self.upsert_config)}")
        
        if failed == 0:
            print("\n🎉 ALL OPERATIONS COMPLETED SUCCESSFULLY!")
            print("\nYour Revenue Cloud data has been fully imported!")
            print("\nWhat was imported:")
            print("- Product Catalogs and Categories")
            print("- Products with classifications")
            print("- Attribute definitions and categories")
            print("- Selling models and price books")
            print("- Product relationships and bundles")
            print("- Price book entries")
        else:
            print(f"\n⚠️  {failed} operations failed:")
            for obj in failed_objects:
                print(f"  - {obj}")
            
            print("\nTroubleshooting steps:")
            print("1. Check the error messages above for specific issues")
            print("2. Verify all required fields are populated")
            print("3. Ensure lookup references exist (parent records)")
            print("4. Check field-level security permissions")
            print("5. For Product2: Ensure ProductCode values are unique")
            print("6. For AttributeDefinition: Check if Code values are unique")

def main():
    runner = FinalCorrectedUpsertRunner()
    runner.run_final_upsert()

if __name__ == '__main__':
    main()