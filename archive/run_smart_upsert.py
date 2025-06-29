#!/usr/bin/env python3
"""
Run smart upsert that handles existing records and uses appropriate fields.
"""

import subprocess
from pathlib import Path
import pandas as pd

class SmartUpsertRunner:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.target_org = 'fortradp2'
        
        # Track existing records
        self.existing_records = {}
        
    def check_existing_records(self, object_name, unique_field):
        """Check which records already exist."""
        print(f"  Checking existing {object_name} records...")
        
        # Build query based on unique field
        if unique_field == 'Code':
            query = f"SELECT Id, {unique_field} FROM {object_name}"
        elif unique_field == 'Name':
            query = f"SELECT Id, {unique_field} FROM {object_name}"
        else:
            return {}
            
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--result-format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                # Create mapping of unique field value to Id
                mapping = {r.get(unique_field): r.get('Id') for r in records if r.get(unique_field)}
                print(f"    Found {len(mapping)} existing records")
                return mapping
        
        return {}
    
    def prepare_upsert_file(self, csv_file, object_name):
        """Prepare CSV file for upsert by adding IDs for existing records."""
        file_path = self.csv_dir / csv_file
        if not file_path.exists():
            return None, 'insert'
            
        df = pd.read_csv(file_path)
        
        # Special handling based on object
        if object_name == 'ProductClassification':
            # Check existing by Code
            existing = self.check_existing_records(object_name, 'Code')
            if existing and 'Code' in df.columns:
                # Add IDs for existing records
                df['Id'] = df['Code'].map(existing)
                has_ids = df['Id'].notna().any()
                if has_ids:
                    # Split into update and insert
                    update_df = df[df['Id'].notna()]
                    insert_df = df[df['Id'].isna()].drop(columns=['Id'])
                    
                    if len(update_df) > 0:
                        update_file = file_path.parent / f"{file_path.stem}_update.csv"
                        update_df.to_csv(update_file, index=False)
                        print(f"    {len(update_df)} records to update")
                    
                    if len(insert_df) > 0:
                        insert_file = file_path.parent / f"{file_path.stem}_insert.csv"
                        insert_df.to_csv(insert_file, index=False)
                        print(f"    {len(insert_df)} records to insert")
                        return insert_file, 'insert'
                    else:
                        return update_file, 'update'
        
        elif object_name == 'AttributeDefinition':
            # Ensure Code field is populated
            if 'Code' in df.columns:
                empty_codes = df['Code'].isna()
                if empty_codes.any() and 'Name' in df.columns:
                    df.loc[empty_codes, 'Code'] = df.loc[empty_codes, 'Name'].str.upper().str.replace(' ', '_').str.replace('-', '_')
                    df.to_csv(file_path, index=False)
                    print(f"    Generated {empty_codes.sum()} Code values")
        
        elif object_name == 'Product2':
            # For Product2, we'll use Id-based upsert since ProductCode isn't an external ID
            if 'Id' in df.columns and df['Id'].notna().any():
                return file_path, 'upsert'
            else:
                # All new records
                if 'Id' in df.columns:
                    df = df.drop(columns=['Id'])
                    df.to_csv(file_path, index=False)
                return file_path, 'insert'
        
        return file_path, 'upsert'
    
    def run_operation(self, csv_file, object_name, operation='auto'):
        """Run smart upsert/insert operation."""
        print(f"\n{object_name}:")
        
        # Prepare file and determine operation
        file_path, actual_operation = self.prepare_upsert_file(csv_file, object_name)
        
        if not file_path or not file_path.exists():
            print(f"  ⚠️  No file to process")
            return True
        
        # Check if we have records
        df = pd.read_csv(file_path)
        if len(df) == 0:
            print(f"  - No records to process")
            return True
        
        # Run the operation
        if actual_operation == 'update':
            print(f"  Updating {len(df)} existing records...")
            cmd = [
                'sf', 'data', 'update', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        elif actual_operation == 'upsert':
            print(f"  Upserting {len(df)} records using Id...")
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--file', str(file_path),
                '--external-id', 'Id',
                '--target-org', self.target_org,
                '--wait', '10'
            ]
        else:  # insert
            print(f"  Inserting {len(df)} new records...")
            # Remove Id column for inserts
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
            print(f"    ✗ Failed")
            if result.stderr:
                error_lines = result.stderr.split('\n')
                for line in error_lines[:5]:  # Show first 5 error lines
                    if line.strip() and 'Warning:' not in line:
                        print(f"    {line.strip()}")
            return False
    
    def run_smart_upsert(self):
        """Run the smart upsert process."""
        print("=" * 60)
        print("SMART UPSERT PROCESS")
        print("=" * 60)
        print("This process checks for existing records and uses the")
        print("appropriate operation (insert/update/upsert) for each object\n")
        
        # Define processing order
        operations = [
            # Pass 1 - Base objects
            ('11_ProductCatalog.csv', 'ProductCatalog'),
            ('12_ProductCategory.csv', 'ProductCategory'),
            ('08_ProductClassification.csv', 'ProductClassification'),
            ('09_AttributeDefinition.csv', 'AttributeDefinition'),
            ('10_AttributeCategory.csv', 'AttributeCategory'),
            ('15_ProductSellingModel.csv', 'ProductSellingModel'),
            ('13_Product2.csv', 'Product2'),
            ('19_Pricebook2.csv', 'Pricebook2'),
            
            # Pass 2 - Dependent objects
            ('17_ProductAttributeDef.csv', 'ProductAttributeDefinition'),
            ('26_ProductCategoryProduct.csv', 'ProductCategoryProduct'),
            ('20_PricebookEntry.csv', 'PricebookEntry'),
            ('25_ProductRelatedComponent.csv', 'ProductRelatedComponent'),
        ]
        
        success = 0
        failed = 0
        
        print("PASS 1: Base Objects")
        print("-" * 40)
        
        for i, (csv_file, object_name) in enumerate(operations):
            if i == 8:  # Start of Pass 2
                print("\n\nPASS 2: Dependent Objects")
                print("-" * 40)
            
            if self.run_operation(csv_file, object_name):
                success += 1
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"✓ Successful: {success}")
        print(f"✗ Failed: {failed}")
        print(f"Total: {len(operations)}")

def main():
    runner = SmartUpsertRunner()
    runner.run_smart_upsert()

if __name__ == '__main__':
    main()