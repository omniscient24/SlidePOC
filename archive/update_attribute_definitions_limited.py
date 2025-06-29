#!/usr/bin/env python3
"""
Update only the modifiable fields in AttributeDefinition records.
"""

import pandas as pd
import subprocess
from pathlib import Path

class AttributeDefinitionUpdater:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        
    def update_picklist_ids_only(self):
        """Update only the PicklistId field for existing AttributeDefinition records."""
        print("=" * 60)
        print("UPDATING ATTRIBUTEDEFINITION PICKLIST IDS")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='09_AttributeDefinition')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Filter only picklist records that need updating
        picklist_records = df[df['DataType'] == 'Picklist'].copy()
        
        # We need only the Code (for matching) and PicklistId (for updating)
        update_df = picklist_records[['Code', 'PicklistId']].copy()
        
        # Remove any records without PicklistId
        update_df = update_df[update_df['PicklistId'].notna()]
        
        print(f"\nUpdating PicklistId for {len(update_df)} AttributeDefinition records")
        
        if len(update_df) > 0:
            # Save to CSV with only updateable fields
            csv_file = Path('data/temp_attribute_definition_update.csv')
            update_df.to_csv(csv_file, index=False)
            
            # Use upsert with Code as external ID
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', 'AttributeDefinition',
                '--file', str(csv_file),
                '--external-id', 'Code',
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Successfully updated AttributeDefinition PicklistId values")
            else:
                print(f"✗ Failed: {result.stderr}")
                
                # Try to get job ID for detailed errors
                if '--job-id' in result.stderr:
                    import re
                    match = re.search(r'--job-id (\w+)', result.stderr)
                    if match:
                        job_id = match.group(1)
                        print(f"\nChecking job {job_id} for details...")
                        
                        # Get error details
                        detail_cmd = [
                            'sf', 'data', 'bulk', 'results',
                            '--job-id', job_id,
                            '--target-org', self.target_org
                        ]
                        subprocess.run(detail_cmd)
            
            # Clean up
            csv_file.unlink()
            
            # Clean up any result files
            for file in Path('.').glob(f"*-success-records.csv"):
                file.unlink()
            for file in Path('.').glob(f"*-failed-records.csv"):
                file.unlink()
    
    def verify_update_success(self):
        """Verify that the updates were successful."""
        print("\n" + "=" * 60)
        print("VERIFYING UPDATE SUCCESS")
        print("=" * 60)
        
        # Query AttributeDefinitions with PicklistId
        query = """
        SELECT Name, Code, DataType, PicklistId 
        FROM AttributeDefinition 
        WHERE DataType = 'Picklist'
        ORDER BY Name
        """
        
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
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                
                print(f"\nFound {len(records)} Picklist AttributeDefinitions:")
                for rec in records:
                    status = "✓" if rec.get('PicklistId') else "✗"
                    print(f"  {status} {rec['Name']} ({rec['Code']}): {rec.get('PicklistId', 'NOT SET')}")
        else:
            print(f"Failed to query: {result.stderr}")

def main():
    updater = AttributeDefinitionUpdater()
    
    # Update only PicklistId values
    updater.update_picklist_ids_only()
    
    # Verify the updates
    updater.verify_update_success()
    
    print("\n✓ AttributeDefinition update process complete")
    print("\nYou can now run the complete upsert script again.")

if __name__ == '__main__':
    main()