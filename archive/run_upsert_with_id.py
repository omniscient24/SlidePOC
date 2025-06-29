#!/usr/bin/env python3
"""
Run upsert using Id field for existing records.
This avoids the need for External_ID__c fields.
"""

import pandas as pd
import subprocess
import os
from pathlib import Path

class IdBasedUpsertRunner:
    def __init__(self):
        self.excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.csv_output_dir = Path('data/csv_upsert_output')
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Objects we know exist in the org
        self.known_objects = {
            '11_ProductCatalog': ('ProductCatalog', True),
            '12_ProductCategory': ('ProductCategory', True),
            '13_Product2': ('Product2', True),
            '09_AttributeDefinition': ('AttributeDefinition', True),
            '08_ProductClassification': ('ProductClassification', True),
            '15_ProductSellingModel': ('ProductSellingModel', True),
            '19_Pricebook2': ('Pricebook2', True),
            '20_PricebookEntry': ('PricebookEntry', True),
            '26_ProductCategoryProduct': ('ProductCategoryProduct', True),
            '17_ProductAttributeDef': ('ProductAttributeDefinition', True),
            '25_ProductRelatedComponent': ('ProductRelatedComponent', True),
        }
    
    def prepare_csv_for_upsert(self, sheet_name):
        """Prepare CSV file for upsert by checking if records have IDs."""
        df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
        df = df.dropna(how='all')
        
        if len(df) == 0:
            return None
            
        csv_file = self.csv_output_dir / f"{sheet_name}.csv"
        
        # Check if we have Id column with values
        has_ids = 'Id' in df.columns and df['Id'].notna().any()
        
        if has_ids:
            # Split into updates (have IDs) and inserts (no IDs)
            updates_df = df[df['Id'].notna()]
            inserts_df = df[df['Id'].isna()]
            
            # Save files
            if len(updates_df) > 0:
                update_file = self.csv_output_dir / f"{sheet_name}_update.csv"
                updates_df.to_csv(update_file, index=False)
                
            if len(inserts_df) > 0:
                insert_file = self.csv_output_dir / f"{sheet_name}_insert.csv"
                # Remove Id column for inserts
                inserts_df = inserts_df.drop(columns=['Id'])
                inserts_df.to_csv(insert_file, index=False)
                
            return has_ids
        else:
            # All inserts
            if 'Id' in df.columns:
                df = df.drop(columns=['Id'])
            df.to_csv(csv_file, index=False)
            return False
    
    def run_update(self, object_name, csv_file):
        """Run update using Id field."""
        print(f"  Updating {object_name} records...")
        
        cmd = [
            'sf', 'data', 'update', 'bulk',
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
            print(f"    ✗ Error: {result.stderr}")
            return False
    
    def run_insert(self, object_name, csv_file):
        """Run insert for new records."""
        print(f"  Inserting new {object_name} records...")
        
        # Check if file has data
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            print(f"    - No records to insert")
            return True
        
        cmd = [
            'sf', 'data', 'create', 'bulk',
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
            print(f"    ✗ Error: {result.stderr}")
            return False
    
    def run_smart_upsert(self):
        """Run upsert using appropriate method for each object."""
        print("=" * 60)
        print("SMART UPSERT PROCESS")
        print("=" * 60)
        print("Using Id field for updates, creating new records as needed\n")
        
        success_count = 0
        fail_count = 0
        
        for sheet_name, (object_name, is_active) in self.known_objects.items():
            if not is_active:
                continue
                
            print(f"\nProcessing {object_name}...")
            
            has_ids = self.prepare_csv_for_upsert(sheet_name)
            
            if has_ids is None:
                print("  - No data to process")
                continue
            
            # Run updates if we have them
            update_file = self.csv_output_dir / f"{sheet_name}_update.csv"
            if update_file.exists():
                if self.run_update(object_name, update_file):
                    success_count += 1
                else:
                    fail_count += 1
            
            # Run inserts if we have them
            insert_file = self.csv_output_dir / f"{sheet_name}_insert.csv"
            if insert_file.exists():
                if self.run_insert(object_name, insert_file):
                    success_count += 1
                else:
                    fail_count += 1
            elif not has_ids:
                # All records are inserts
                csv_file = self.csv_output_dir / f"{sheet_name}.csv"
                if csv_file.exists():
                    if self.run_insert(object_name, csv_file):
                        success_count += 1
                    else:
                        fail_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Successful operations: {success_count}")
        print(f"Failed operations: {fail_count}")
        
        if fail_count == 0:
            print("\nAll operations completed successfully!")
        else:
            print(f"\n{fail_count} operations failed. Check the errors above.")

def main():
    runner = IdBasedUpsertRunner()
    runner.run_smart_upsert()

if __name__ == '__main__':
    main()