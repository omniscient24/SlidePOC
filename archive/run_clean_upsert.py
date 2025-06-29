#!/usr/bin/env python3
"""
Run upsert using cleaned headers file.
"""

import pandas as pd
import subprocess
import os
from pathlib import Path

class CleanUpsertRunner:
    def __init__(self):
        self.excel_file = Path('data/Revenue_Cloud_Clean_Headers_20250619_162905.xlsx')
        self.csv_output_dir = Path('data/csv_clean_output')
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Core objects to process
        self.objects_to_process = [
            # Pass 1 - Base objects
            ('11_ProductCatalog', 'ProductCatalog'),
            ('12_ProductCategory', 'ProductCategory'),
            ('08_ProductClassification', 'ProductClassification'),
            ('09_AttributeDefinition', 'AttributeDefinition'),
            ('10_AttributeCategory', 'AttributeCategory'),
            ('15_ProductSellingModel', 'ProductSellingModel'),
            ('13_Product2', 'Product2'),
            ('19_Pricebook2', 'Pricebook2'),
            
            # Pass 2 - Dependent objects
            ('26_ProductCategoryProduct', 'ProductCategoryProduct'),
            ('17_ProductAttributeDef', 'ProductAttributeDefinition'),
            ('20_PricebookEntry', 'PricebookEntry'),
            ('25_ProductRelatedComponent', 'ProductRelatedComponent'),
        ]
    
    def excel_to_csv(self):
        """Convert Excel sheets to CSV files."""
        print("Converting Excel to CSV...")
        
        for sheet_name, _ in self.objects_to_process:
            try:
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
                df = df.dropna(how='all')  # Remove empty rows
                
                if len(df) > 0:
                    csv_file = self.csv_output_dir / f"{sheet_name}.csv"
                    df.to_csv(csv_file, index=False)
                    print(f"  Created: {sheet_name}.csv ({len(df)} records)")
            except Exception as e:
                print(f"  Error processing {sheet_name}: {str(e)}")
    
    def run_upsert_or_insert(self, object_name, csv_file):
        """Run upsert if records have IDs, otherwise insert."""
        # Read CSV to check for IDs
        df = pd.read_csv(csv_file)
        
        if len(df) == 0:
            print(f"  No records to process")
            return True
        
        # Check if we have ID column with values
        has_ids = 'Id' in df.columns and df['Id'].notna().any()
        
        if has_ids:
            # Use upsert with Id field
            print(f"  Upserting {len(df)} records using Id field...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--external-id', 'Id',
                '--target-org', 'fortradp2',
                '--wait', '10'
            ]
        else:
            # Use import (insert) for new records
            print(f"  Inserting {len(df)} new records...")
            # Remove Id column if it exists but is empty
            if 'Id' in df.columns:
                df = df.drop(columns=['Id'])
                df.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--target-org', 'fortradp2',
                '--wait', '10'
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"    ✓ Success!")
            return True
        else:
            print(f"    ✗ Error: {result.stderr.strip()}")
            # Check for specific errors
            if 'Field name not found' in result.stderr:
                print(f"    ℹ️  Some fields may not exist on {object_name}")
            elif 'No such column' in result.stderr:
                print(f"    ℹ️  External ID field may not exist")
            return False
    
    def run_complete_upsert(self):
        """Run the complete upsert process."""
        print("=" * 60)
        print("CLEAN UPSERT PROCESS")
        print("=" * 60)
        
        # Step 1: Convert to CSV
        print("\nStep 1: Converting Excel to CSV")
        print("-" * 40)
        self.excel_to_csv()
        
        # Step 2: Process each object
        print("\nStep 2: Processing Objects")
        print("-" * 40)
        
        success_count = 0
        fail_count = 0
        
        for sheet_name, object_name in self.objects_to_process:
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            
            if not csv_file.exists():
                print(f"\nSkipping {object_name} - no CSV file")
                continue
            
            print(f"\nProcessing {object_name}...")
            
            if self.run_upsert_or_insert(object_name, csv_file):
                success_count += 1
            else:
                fail_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")
        print(f"Total: {len(self.objects_to_process)}")
        
        if fail_count == 0:
            print("\nAll operations completed successfully! 🎉")
        else:
            print(f"\n{fail_count} operations failed. Review the errors above.")
            print("\nCommon issues:")
            print("- Field doesn't exist on the object")
            print("- No External_ID__c field for upsert")
            print("- Data type mismatches")
            print("- Required fields missing")

def main():
    runner = CleanUpsertRunner()
    runner.run_complete_upsert()

if __name__ == '__main__':
    main()