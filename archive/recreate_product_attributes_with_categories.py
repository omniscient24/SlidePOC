#!/usr/bin/env python3
"""
Delete and recreate ProductAttributeDefinition records with AttributeCategoryId assignments.
"""

import pandas as pd
import subprocess
import json
import time
from pathlib import Path

class ProductAttributeRecreator:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        self.backup_file = 'data/product_attributes_backup.csv'
        
    def backup_existing_records(self):
        """Query and backup existing ProductAttributeDefinition records."""
        print("1. Backing up existing ProductAttributeDefinition records...")
        
        query = """
        SELECT Id, Name, Product2Id, AttributeDefinitionId, AttributeCategoryId, 
               Sequence, IsRequired, IsHidden, IsReadOnly, IsPriceImpacting, 
               DefaultValue, HelpText, MinimumValue, MaximumValue, DisplayType, 
               Status, AttributeNameOverride, Description
        FROM ProductAttributeDefinition
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--result-format', 'csv'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open(self.backup_file, 'w') as f:
                f.write(result.stdout)
            print(f"   ✓ Backed up to {self.backup_file}")
            
            # Count records
            lines = result.stdout.strip().split('\n')
            record_count = len(lines) - 1  # Subtract header
            print(f"   ✓ Backed up {record_count} records")
            return record_count > 0
        else:
            print(f"   ✗ Backup failed: {result.stderr}")
            return False
    
    def delete_existing_records(self):
        """Delete all existing ProductAttributeDefinition records."""
        print("\n2. Deleting existing ProductAttributeDefinition records...")
        
        # Get all IDs
        query = "SELECT Id FROM ProductAttributeDefinition"
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                
                if len(records) == 0:
                    print("   No records to delete")
                    return True
                
                # Create CSV for bulk delete
                delete_csv = 'data/temp_delete.csv'
                with open(delete_csv, 'w') as f:
                    f.write('Id\n')
                    for rec in records:
                        f.write(f"{rec['Id']}\n")
                
                # Bulk delete
                print(f"   Deleting {len(records)} records...")
                cmd = [
                    'sf', 'data', 'delete', 'bulk',
                    '--sobject', 'ProductAttributeDefinition',
                    '--file', delete_csv,
                    '--target-org', self.target_org,
                    '--wait', '10'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"   ✓ Deleted {len(records)} records")
                    # Clean up temp file
                    Path(delete_csv).unlink(missing_ok=True)
                    return True
                else:
                    print(f"   ✗ Delete failed: {result.stderr}")
                    return False
        
        return False
    
    def create_records_with_categories(self):
        """Create new ProductAttributeDefinition records with AttributeCategoryId."""
        print("\n3. Creating new ProductAttributeDefinition records with categories...")
        
        # Read the spreadsheet with category assignments
        df = pd.read_excel(self.workbook_path, sheet_name='17_ProductAttributeDef')
        df.columns = df.columns.str.replace('*', '', regex=False).str.strip()
        
        # Remove the Id column for insert
        if 'Id' in df.columns:
            df = df.drop('Id', axis=1)
        
        # Ensure AttributeCategoryId is included
        if 'AttributeCategoryId' not in df.columns:
            print("   ✗ ERROR: AttributeCategoryId column not found")
            return False
        
        # Show category distribution
        print("\n   Category assignments:")
        category_counts = df['AttributeCategoryId'].value_counts()
        for cat_id, count in category_counts.items():
            if pd.notna(cat_id):
                print(f"   - {cat_id}: {count} attributes")
        
        # Save to CSV for bulk insert
        insert_csv = 'data/product_attributes_insert.csv'
        df.to_csv(insert_csv, index=False)
        
        print(f"\n   Inserting {len(df)} records...")
        
        # Bulk insert
        cmd = [
            'sf', 'data', 'import', 'bulk',
            '--sobject', 'ProductAttributeDefinition',
            '--file', insert_csv,
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✓ Successfully created {len(df)} records with categories")
            # Clean up temp file
            Path(insert_csv).unlink(missing_ok=True)
            return True
        else:
            print(f"   ✗ Insert failed: {result.stderr}")
            # Check for specific errors
            if 'failed-records.csv' in result.stderr:
                print("\n   Checking failed records...")
                # Try to find and display the error file
                import glob
                error_files = glob.glob('*failed-records.csv')
                if error_files:
                    print(f"   Error details in: {error_files[0]}")
                    # Show first few errors
                    with open(error_files[0], 'r') as f:
                        lines = f.readlines()[:5]
                        for line in lines:
                            print(f"   {line.strip()}")
            return False
    
    def verify_categories(self):
        """Verify that categories were assigned correctly."""
        print("\n4. Verifying category assignments...")
        
        query = """
        SELECT AttributeCategoryId, COUNT(Id) count
        FROM ProductAttributeDefinition
        GROUP BY AttributeCategoryId
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                print("\n   Final category distribution:")
                for rec in data['result']['records']:
                    cat_id = rec.get('AttributeCategoryId', 'NULL')
                    count = rec.get('count', 0)
                    print(f"   - {cat_id}: {count} attributes")
                
                # Check if any are NULL
                null_count = sum(rec.get('count', 0) for rec in data['result']['records'] 
                               if not rec.get('AttributeCategoryId'))
                if null_count > 0:
                    print(f"\n   ⚠️  WARNING: {null_count} records still have NULL AttributeCategoryId")
                else:
                    print("\n   ✓ All records have AttributeCategoryId assigned!")
    
    def update_spreadsheet_with_new_ids(self):
        """Update the spreadsheet with the new record IDs."""
        print("\n5. Updating spreadsheet with new record IDs...")
        
        # Export the new data
        subprocess.run(['python3', 'export_to_same_template.py'], 
                      capture_output=True, text=True)
        
        print("   ✓ Spreadsheet updated with new IDs")
    
    def run(self):
        """Execute the complete recreation process."""
        print("=" * 70)
        print("RECREATING PRODUCTATTRIBUTEDEFINITION WITH CATEGORIES")
        print("=" * 70)
        
        # Step 1: Backup
        if not self.backup_existing_records():
            print("\n✗ Backup failed. Aborting to prevent data loss.")
            return
        
        # Confirm before proceeding
        print("\n⚠️  WARNING: This will delete and recreate all ProductAttributeDefinition records!")
        print("   Backup has been created at:", self.backup_file)
        print("\n✓ Proceeding with recreation...")
        
        # Step 2: Delete existing records
        if not self.delete_existing_records():
            print("\n✗ Delete failed. Please check errors above.")
            return
        
        # Brief pause to ensure deletion is processed
        time.sleep(2)
        
        # Step 3: Create new records with categories
        if not self.create_records_with_categories():
            print("\n✗ Creation failed. Please check errors above.")
            print("   Your backup is available at:", self.backup_file)
            return
        
        # Step 4: Verify
        self.verify_categories()
        
        # Step 5: Update spreadsheet
        self.update_spreadsheet_with_new_ids()
        
        print("\n" + "=" * 70)
        print("✓ RECREATION COMPLETE")
        print("=" * 70)
        print(f"Backup saved at: {self.backup_file}")
        print("All ProductAttributeDefinition records now have AttributeCategoryId assigned!")

if __name__ == '__main__':
    recreator = ProductAttributeRecreator()
    recreator.run()