#!/usr/bin/env python3
"""
Import AttributePicklistValue records properly.
"""

import pandas as pd
import subprocess
from pathlib import Path

class AttributePicklistValueImporter:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        
    def import_values(self):
        """Import AttributePicklistValue records."""
        print("=" * 60)
        print("IMPORTING ATTRIBUTEPICKLISTVALUE RECORDS")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='18_AttributePicklistValue')
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove rows without Name
        df = df[df['Name'].notna()]
        
        print(f"\nTotal records found: {len(df)}")
        
        # Separate records with IDs (for update) and without IDs (for insert)
        records_with_id = df[df['Id'].notna()].copy()
        records_without_id = df[df['Id'].isna()].copy()
        
        print(f"Records with existing IDs (to update): {len(records_with_id)}")
        print(f"Records without IDs (to insert): {len(records_without_id)}")
        
        success_count = 0
        
        # First, update existing records
        if len(records_with_id) > 0:
            print("\n" + "-" * 40)
            print("Updating existing records...")
            
            csv_file = Path('data/temp_apv_update.csv')
            records_with_id.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', 'AttributePicklistValue',
                '--file', str(csv_file),
                '--external-id', 'Id',
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Successfully updated existing records")
                success_count += len(records_with_id)
            else:
                print(f"✗ Failed to update: {result.stderr[:200]}")
            
            csv_file.unlink()
        
        # Then, insert new records
        if len(records_without_id) > 0:
            print("\n" + "-" * 40)
            print("Inserting new records...")
            
            # Remove Id column for insert
            records_without_id = records_without_id.drop(columns=['Id'])
            
            # Remove External_ID__c if present (not a real field)
            if 'External_ID__c' in records_without_id.columns:
                records_without_id = records_without_id.drop(columns=['External_ID__c'])
            
            # Show sample of what we're inserting
            print("\nSample records to insert:")
            sample = records_without_id.head(3)
            for idx, row in sample.iterrows():
                print(f"\n- {row['Name']} (Value: {row['Value']}, Picklist: {row['PicklistId']})")
            
            csv_file = Path('data/temp_apv_insert.csv')
            records_without_id.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', 'AttributePicklistValue',
                '--file', str(csv_file),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"\n✓ Successfully inserted {len(records_without_id)} new records")
                success_count += len(records_without_id)
            else:
                print(f"\n✗ Failed to insert: {result.stderr}")
                
                # Try to get error details
                if '--job-id' in result.stderr:
                    import re
                    match = re.search(r'--job-id (\w+)', result.stderr)
                    if match:
                        job_id = match.group(1)
                        self.get_error_details(job_id)
            
            csv_file.unlink()
        
        print(f"\n" + "=" * 60)
        print(f"IMPORT COMPLETE")
        print(f"Total records processed: {success_count}/{len(df)}")
        
        # Verify the import
        self.verify_import()
        
    def get_error_details(self, job_id):
        """Get error details for failed job."""
        print(f"\nGetting error details for job {job_id}...")
        
        cmd = [
            'sf', 'data', 'bulk', 'results',
            '--job-id', job_id,
            '--target-org', self.target_org
        ]
        
        subprocess.run(cmd)
        
        # Check for failed records file
        failed_file = Path(f"{job_id}-failed-records.csv")
        if failed_file.exists():
            df = pd.read_csv(failed_file)
            print(f"\nSample failures (first 3):")
            for idx, row in df.head(3).iterrows():
                print(f"\n{row.get('Name', 'Unknown')}:")
                print(f"  Error: {row.get('sf__Error', 'Unknown')}")
            
            # Clean up
            failed_file.unlink()
            success_file = Path(f"{job_id}-success-records.csv")
            if success_file.exists():
                success_file.unlink()
    
    def verify_import(self):
        """Verify the import results."""
        print("\n" + "=" * 60)
        print("VERIFYING IMPORT")
        print("=" * 60)
        
        import json
        
        # Count total records
        query = "SELECT COUNT() FROM AttributePicklistValue"
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data:
                total = data['result']['totalSize']
                print(f"\nTotal AttributePicklistValue records in org: {total}")
                
                # Show breakdown by picklist
                query2 = """
                SELECT PicklistId, AttributePicklist.Name, COUNT(Id) 
                FROM AttributePicklistValue 
                GROUP BY PicklistId, AttributePicklist.Name
                ORDER BY AttributePicklist.Name
                """
                
                cmd2 = [
                    'sf', 'data', 'query',
                    '--query', query2,
                    '--target-org', self.target_org,
                    '--json'
                ]
                
                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                
                if result2.returncode == 0:
                    data2 = json.loads(result2.stdout)
                    if 'result' in data2 and 'records' in data2['result']:
                        records = data2['result']['records']
                        
                        print("\nBreakdown by AttributePicklist:")
                        for rec in records:
                            name = rec.get('Name', 'Unknown')
                            count = rec.get('expr0', 0)
                            print(f"  - {name}: {count} values")

def main():
    importer = AttributePicklistValueImporter()
    importer.import_values()

if __name__ == '__main__':
    main()