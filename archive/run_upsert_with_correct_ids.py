#!/usr/bin/env python3
"""
Run upsert with correct external ID fields for each object.
"""

import subprocess
from pathlib import Path
import pandas as pd

class CorrectUpsertRunner:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.target_org = 'fortradp2'
        
        # Objects with their correct external ID fields
        self.upsert_config = [
            # Pass 1 - Base objects
            ('11_ProductCatalog.csv', 'ProductCatalog', 'Id'),  # No external ID available
            ('12_ProductCategory.csv', 'ProductCategory', 'ExternalId__c'),  # Has custom external ID
            ('08_ProductClassification.csv', 'ProductClassification', None),  # Insert only
            ('09_AttributeDefinition.csv', 'AttributeDefinition', 'Code'),  # Use Code field
            ('10_AttributeCategory.csv', 'AttributeCategory', 'Id'),  # No external ID available
            ('15_ProductSellingModel.csv', 'ProductSellingModel', 'Id'),  # No external ID available
            ('13_Product2.csv', 'Product2', 'ExternalId'),  # Use standard ExternalId field
            ('19_Pricebook2.csv', 'Pricebook2', 'Id'),  # No external ID available
            
            # Pass 2 - Dependent objects (insert only)
            ('17_ProductAttributeDef.csv', 'ProductAttributeDefinition', None),  # Insert only
            ('26_ProductCategoryProduct.csv', 'ProductCategoryProduct', None),  # Insert only
            ('20_PricebookEntry.csv', 'PricebookEntry', None),  # Insert only
            ('25_ProductRelatedComponent.csv', 'ProductRelatedComponent', None),  # Insert only
        ]
    
    def prepare_csv_for_upsert(self, csv_file, external_id_field):
        """Prepare CSV file for upsert by ensuring external ID field is populated."""
        file_path = self.csv_dir / csv_file
        if not file_path.exists():
            return None
            
        df = pd.read_csv(file_path)
        
        # Special handling for different external ID fields
        if external_id_field == 'ExternalId__c' and 'External_ID__c' in df.columns:
            # Map External_ID__c to ExternalId__c for ProductCategory
            df['ExternalId__c'] = df['External_ID__c']
            df.to_csv(file_path, index=False)
            print(f"    Mapped External_ID__c to ExternalId__c")
        
        elif external_id_field == 'ExternalId' and 'External_ID__c' in df.columns:
            # Map External_ID__c to ExternalId for Product2
            df['ExternalId'] = df['External_ID__c']
            df.to_csv(file_path, index=False)
            print(f"    Mapped External_ID__c to ExternalId")
            
        elif external_id_field == 'Code' and 'Code' not in df.columns and 'Name' in df.columns:
            # Generate Code from Name if not present
            df['Code'] = df['Name'].str.upper().str.replace(' ', '_')
            df.to_csv(file_path, index=False)
            print(f"    Generated Code field from Name")
        
        return file_path
    
    def run_operation(self, csv_file, object_name, external_id_field):
        """Run upsert or insert operation with correct external ID."""
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
        if external_id_field and external_id_field != 'Id':
            file_path = self.prepare_csv_for_upsert(csv_file, external_id_field)
            if not file_path:
                return False
        
        if external_id_field:
            # Upsert using the appropriate external ID field
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
            if 'successfully processed' in result.stdout:
                print(f"    {result.stdout.strip()}")
            return True
        else:
            print(f"    ✗ Failed")
            # Extract specific error
            if result.stderr:
                error_lines = result.stderr.split('\n')
                for line in error_lines:
                    if 'Error' in line and 'Try this:' not in line:
                        print(f"    Error: {line.strip()}")
            return False
    
    def run_corrected_upsert(self):
        """Run the upsert process with correct external IDs."""
        print("=" * 60)
        print("RUNNING UPSERT WITH CORRECT EXTERNAL ID FIELDS")
        print("=" * 60)
        print(f"Using fixed CSV files from: {self.csv_dir}\n")
        
        print("External ID Field Mapping:")
        print("-" * 40)
        for csv_file, obj_name, ext_id in self.upsert_config:
            if ext_id:
                print(f"{obj_name}: {ext_id}")
        print()
        
        success = 0
        failed = 0
        
        print("PASS 1: Base Objects")
        print("-" * 40)
        
        for i, (csv_file, object_name, external_id) in enumerate(self.upsert_config):
            if i == 8:  # Start of Pass 2
                print("\n\nPASS 2: Dependent Objects")
                print("-" * 40)
            
            print(f"\n{object_name}:")
            
            if self.run_operation(csv_file, object_name, external_id):
                success += 1
            else:
                failed += 1
        
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
            print(f"\n⚠️  {failed} operations still failed.")
            print("\nNext steps:")
            print("1. Review the error messages above")
            print("2. Check if external ID values are unique")
            print("3. Verify all required fields are populated")
            print("4. Ensure referenced records exist")

def main():
    runner = CorrectUpsertRunner()
    runner.run_corrected_upsert()

if __name__ == '__main__':
    main()