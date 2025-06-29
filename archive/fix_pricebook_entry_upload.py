#!/usr/bin/env python3
"""
Fix PricebookEntry upload by removing invalid fields.
"""

import pandas as pd
import subprocess
from pathlib import Path

class PricebookEntryFixer:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        
        # Valid fields for PricebookEntry
        self.valid_fields = [
            'Id',
            'Pricebook2Id',
            'Product2Id',
            'UnitPrice',
            'IsActive',
            'UseStandardPrice',
            'ProductSellingModelId'
        ]
        
    def fix_and_upload(self):
        """Fix the PricebookEntry data and upload."""
        print("=" * 60)
        print("FIXING PRICEBOOKENTRY UPLOAD")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        
        print(f"\nOriginal columns: {list(df.columns)}")
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Keep only valid fields
        valid_cols = [col for col in df.columns if col in self.valid_fields]
        df_clean = df[valid_cols].copy()
        
        print(f"\nCleaned columns: {list(df_clean.columns)}")
        
        # Remove rows with no data
        df_clean = df_clean.dropna(how='all')
        
        # Handle NaN values in ProductSellingModelId
        # Replace NaN with empty string for CSV
        if 'ProductSellingModelId' in df_clean.columns:
            df_clean['ProductSellingModelId'] = df_clean['ProductSellingModelId'].fillna('')
        
        print(f"\nRecords to process: {len(df_clean)}")
        
        # Save to CSV
        csv_file = Path('data/pricebook_entry_clean.csv')
        df_clean.to_csv(csv_file, index=False)
        
        # Upsert the data
        print("\nUpserting PricebookEntry records...")
        
        cmd = [
            'sf', 'data', 'upsert', 'bulk',
            '--sobject', 'PricebookEntry',
            '--file', str(csv_file),
            '--external-id', 'Id',
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully uploaded PricebookEntry records")
        else:
            print(f"✗ Upload failed: {result.stderr}")
            
            # Get detailed errors
            if '--job-id' in result.stderr:
                import re
                match = re.search(r'--job-id (\w+)', result.stderr)
                if match:
                    job_id = match.group(1)
                    self.check_errors(job_id)
        
        # Clean up
        csv_file.unlink()
        
    def check_errors(self, job_id):
        """Check detailed errors."""
        print(f"\nChecking job {job_id} for errors...")
        
        cmd = [
            'sf', 'data', 'bulk', 'results',
            '--job-id', job_id,
            '--target-org', self.target_org
        ]
        
        subprocess.run(cmd)
        
        # Read failed records if any
        failed_file = Path(f"{job_id}-failed-records.csv")
        if failed_file.exists():
            df_failed = pd.read_csv(failed_file)
            
            print(f"\nFailed records: {len(df_failed)}")
            
            # Group errors
            if 'sf__Error' in df_failed.columns:
                error_counts = df_failed['sf__Error'].value_counts()
                print("\nError summary:")
                for error, count in error_counts.items():
                    # Extract key error message
                    if 'INVALID_FIELD' in error:
                        print(f"  - Invalid field error: {count} records")
                    elif 'duplicate value' in error:
                        print(f"  - Duplicate value error: {count} records") 
                    elif 'required' in error.lower():
                        print(f"  - Missing required field: {count} records")
                    else:
                        print(f"  - {error[:100]}...: {count} records")
            
            # Show sample errors
            print("\nSample errors:")
            for idx, row in df_failed.head(3).iterrows():
                print(f"\nRecord {idx + 1}:")
                if 'Product2Id' in row:
                    print(f"  Product2Id: {row['Product2Id']}")
                print(f"  Error: {row['sf__Error'][:200]}...")
            
            # Clean up
            failed_file.unlink()
            
        success_file = Path(f"{job_id}-success-records.csv")
        if success_file.exists():
            success_file.unlink()
    
    def verify_upload(self):
        """Verify the upload results."""
        print("\n" + "=" * 60)
        print("VERIFYING PRICEBOOKENTRY UPLOAD")
        print("=" * 60)
        
        # Count records
        query = "SELECT COUNT() FROM PricebookEntry"
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if 'result' in data:
                count = data['result']['totalSize']
                print(f"\n✓ Total PricebookEntry records in org: {count}")

def main():
    fixer = PricebookEntryFixer()
    
    # Fix and upload
    fixer.fix_and_upload()
    
    # Verify
    fixer.verify_upload()

if __name__ == '__main__':
    main()