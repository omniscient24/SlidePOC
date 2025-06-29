#!/usr/bin/env python3
"""
Run complete upsert from the Revenue_Cloud_Complete_Upload_Template.xlsx file.
"""

import subprocess
from pathlib import Path
import pandas as pd
import os

class CompleteUpsertRunner:
    def __init__(self):
        self.excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.csv_output_dir = Path('data/csv_upsert_output')
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        self.target_org = 'fortradp2'
        
        # Define sheet processing order and configurations
        self.sheet_configs = [
            # Pass 1 - Base objects
            {'sheet': '11_ProductCatalog', 'object': 'ProductCatalog', 'external_id': 'Id'},
            {'sheet': '12_ProductCategory', 'object': 'ProductCategory', 'external_id': 'Id'},
            {'sheet': '08_ProductClassification', 'object': 'ProductClassification', 'external_id': 'Code'},
            {'sheet': '09_AttributeDefinition', 'object': 'AttributeDefinition', 'external_id': 'Code'},
            {'sheet': '10_AttributeCategory', 'object': 'AttributeCategory', 'external_id': 'Code'},
            {'sheet': '15_ProductSellingModel', 'object': 'ProductSellingModel', 'external_id': 'Id'},
            {'sheet': '13_Product2', 'object': 'Product2', 'external_id': 'Id'},
            {'sheet': '19_Pricebook2', 'object': 'Pricebook2', 'external_id': 'Id'},
            
            # Pass 2 - Dependent objects
            {'sheet': '17_ProductAttributeDef', 'object': 'ProductAttributeDefinition', 'external_id': 'Id'},
            {'sheet': '18_AttributePicklistValue', 'object': 'AttributePicklistValue', 'external_id': 'Id'},
            {'sheet': '26_ProductCategoryProduct', 'object': 'ProductCategoryProduct', 'external_id': 'Id'},
            {'sheet': '20_PricebookEntry', 'object': 'PricebookEntry', 'external_id': 'Id'},
            {'sheet': '25_ProductRelatedComponent', 'object': 'ProductRelatedComponent', 'external_id': 'Id'},
        ]
    
    def excel_to_csv(self, sheet_name):
        """Convert Excel sheet to CSV for Salesforce import."""
        try:
            # Read the specific sheet
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove rows where key fields are empty
            if 'Name' in df.columns:
                df = df[df['Name'].notna()]
            elif 'Id' in df.columns:
                df = df[df['Id'].notna()]
            
            if len(df) == 0:
                return None
            
            # Clean column names - remove asterisks
            df.columns = df.columns.str.replace('*', '', regex=False)
            
            # Save to CSV
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            df.to_csv(csv_file, index=False)
            
            return csv_file
            
        except Exception as e:
            print(f"    Error processing sheet: {str(e)}")
            return None
    
    def run_upsert(self, csv_file, object_name, external_id):
        """Run upsert operation for a specific object."""
        if not csv_file or not csv_file.exists():
            return False, "No data to process"
        
        # Read CSV to check if we have records
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            return True, "No records to process"
        
        # Determine operation based on external_id and data
        if external_id == 'Id' and 'Id' in df.columns and df['Id'].notna().any():
            # We have IDs, use upsert
            print(f"    Upserting {len(df)} records using Id...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--external-id', external_id,
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        elif external_id != 'Id' and external_id in df.columns:
            # Use specified external ID
            print(f"    Upserting {len(df)} records using {external_id}...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--external-id', external_id,
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        else:
            # No external ID available, use insert
            print(f"    Inserting {len(df)} new records...")
            # Remove Id column if present for insert
            if 'Id' in df.columns:
                df = df.drop(columns=['Id'])
                df.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Try to extract success count from output
            if 'successfully processed' in result.stdout:
                return True, result.stdout.strip()
            else:
                return True, "Success"
        else:
            # Extract error message
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            if 'Try this:' in error_msg:
                # Extract just the error part
                error_lines = error_msg.split('\n')
                for line in error_lines:
                    if 'Error' in line and 'Try this:' not in line:
                        error_msg = line.strip()
                        break
            return False, error_msg[:200]  # Limit error message length
    
    def run_complete_upsert(self):
        """Run the complete upsert process."""
        print("=" * 70)
        print("COMPLETE REVENUE CLOUD UPSERT PROCESS")
        print("=" * 70)
        print(f"Source: {self.excel_file}")
        print(f"Target Org: {self.target_org}")
        print()
        
        # Track results
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        print("PASS 1: Base Objects")
        print("-" * 50)
        
        pass2_start = 8  # Index where pass 2 starts
        
        for idx, config in enumerate(self.sheet_configs):
            if idx == pass2_start:
                print("\n\nPASS 2: Dependent Objects")
                print("-" * 50)
            
            sheet_name = config['sheet']
            object_name = config['object']
            external_id = config['external_id']
            
            print(f"\n{object_name} ({sheet_name}):")
            
            # Convert Excel to CSV
            print("    Converting to CSV...")
            csv_file = self.excel_to_csv(sheet_name)
            
            if csv_file:
                # Run upsert
                success, message = self.run_upsert(csv_file, object_name, external_id)
                
                if success:
                    if "No records" in message:
                        print(f"    ✓ {message}")
                        results['skipped'] += 1
                    else:
                        print(f"    ✓ Success!")
                        results['success'] += 1
                else:
                    print(f"    ✗ Failed: {message}")
                    results['failed'] += 1
                
                results['details'].append({
                    'object': object_name,
                    'sheet': sheet_name,
                    'status': 'Success' if success else 'Failed',
                    'message': message
                })
            else:
                print("    ⚠️  No data found in sheet")
                results['skipped'] += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("UPSERT SUMMARY")
        print("=" * 70)
        print(f"✓ Successful: {results['success']}")
        print(f"✗ Failed: {results['failed']}")
        print(f"⚠️  Skipped: {results['skipped']}")
        print(f"Total: {len(self.sheet_configs)}")
        
        if results['failed'] > 0:
            print("\nFailed Operations:")
            for detail in results['details']:
                if detail['status'] == 'Failed':
                    print(f"  - {detail['object']}: {detail['message']}")
        
        print("\n✓ Upsert process complete")
        
        # Clean up CSV files
        print("\nCleaning up temporary CSV files...")
        for csv_file in self.csv_output_dir.glob("*.csv"):
            csv_file.unlink()

def main():
    runner = CompleteUpsertRunner()
    runner.run_complete_upsert()

if __name__ == '__main__':
    main()