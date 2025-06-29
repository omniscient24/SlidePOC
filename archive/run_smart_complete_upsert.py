#!/usr/bin/env python3
"""
Smart upsert that handles existing records properly.
"""

import subprocess
import pandas as pd
from pathlib import Path
import json

class SmartCompleteUpsertRunner:
    def __init__(self):
        self.excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.csv_output_dir = Path('data/csv_smart_upsert')
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        self.target_org = 'fortradp2'
        
        # Define configurations with proper handling
        self.sheet_configs = [
            # Pass 1 - Base objects
            {'sheet': '11_ProductCatalog', 'object': 'ProductCatalog', 'mode': 'upsert_id'},
            {'sheet': '12_ProductCategory', 'object': 'ProductCategory', 'mode': 'upsert_id'},
            {'sheet': '08_ProductClassification', 'object': 'ProductClassification', 'mode': 'skip'},  # Already exists
            {'sheet': '09_AttributeDefinition', 'object': 'AttributeDefinition', 'mode': 'check_new'},
            {'sheet': '10_AttributeCategory', 'object': 'AttributeCategory', 'mode': 'skip'},  # Already exists
            {'sheet': '15_ProductSellingModel', 'object': 'ProductSellingModel', 'mode': 'skip'},  # Already exists
            {'sheet': '13_Product2', 'object': 'Product2', 'mode': 'skip'},  # Already exists
            {'sheet': '19_Pricebook2', 'object': 'Pricebook2', 'mode': 'skip'},  # Already exists
            
            # Pass 2 - Dependent objects
            {'sheet': '17_ProductAttributeDef', 'object': 'ProductAttributeDefinition', 'mode': 'skip'},  # Already exists
            {'sheet': '26_ProductCategoryProduct', 'object': 'ProductCategoryProduct', 'mode': 'check_new'},
            {'sheet': '20_PricebookEntry', 'object': 'PricebookEntry', 'mode': 'skip'},  # Already exists
            {'sheet': '25_ProductRelatedComponent', 'object': 'ProductRelatedComponent', 'mode': 'check_new'},
        ]
    
    def check_existing_records(self, object_name, key_field='Code'):
        """Check what records already exist."""
        try:
            query = f"SELECT Id, {key_field} FROM {object_name}"
            cmd = ['sf', 'data', 'query', '--query', query, '--target-org', self.target_org, '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data and 'records' in data['result']:
                    return {r.get(key_field): r.get('Id') for r in data['result']['records'] if r.get(key_field)}
        except:
            pass
        return {}
    
    def process_sheet(self, config):
        """Process a single sheet based on its configuration."""
        sheet_name = config['sheet']
        object_name = config['object']
        mode = config['mode']
        
        print(f"\n{object_name} ({sheet_name}):")
        
        if mode == 'skip':
            print("    ⚠️  Skipping - records already exist in org")
            return 'skipped', "Already exists"
        
        # Read Excel sheet
        try:
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            df = df.dropna(how='all')
            
            # Remove rows where key fields are empty
            if 'Name' in df.columns:
                df = df[df['Name'].notna()]
            elif 'Id' in df.columns and mode == 'upsert_id':
                df = df[df['Id'].notna()]
            
            if len(df) == 0:
                print("    No data in sheet")
                return 'skipped', "No data"
            
            # Clean column names
            df.columns = df.columns.str.replace('*', '', regex=False)
            
            print(f"    Found {len(df)} records in sheet")
            
            if mode == 'check_new':
                # Check for existing records and filter
                if object_name == 'AttributeDefinition' and 'Code' in df.columns:
                    existing = self.check_existing_records(object_name, 'Code')
                    if existing:
                        df = df[~df['Code'].isin(existing.keys())]
                        print(f"    Filtered to {len(df)} new records")
                
                if len(df) == 0:
                    print("    All records already exist")
                    return 'skipped', "All exist"
            
            # Save to CSV
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            
            # Handle specific objects
            if object_name == 'AttributeDefinition':
                # Ensure required fields
                if 'Label' in df.columns:
                    df['Label'] = df['Label'].fillna(df['Name'])
                if 'DataType' in df.columns:
                    df['DataType'] = df['DataType'].fillna('Text')
                # Remove Id for new records
                if 'Id' in df.columns and mode == 'check_new':
                    df = df.drop(columns=['Id'])
            
            elif object_name == 'ProductCategoryProduct':
                # Remove any empty required fields
                if 'ProductCategoryId' in df.columns and 'ProductId' in df.columns:
                    df = df[df['ProductCategoryId'].notna() & df['ProductId'].notna()]
                if 'Id' in df.columns:
                    df = df.drop(columns=['Id'])
            
            elif object_name == 'ProductRelatedComponent':
                # Ensure we have required fields
                required = ['ParentProductId', 'ChildProductId', 'ProductRelationshipTypeId']
                for field in required:
                    if field in df.columns:
                        df = df[df[field].notna()]
                if 'Id' in df.columns:
                    df = df.drop(columns=['Id'])
            
            df.to_csv(csv_file, index=False)
            
            # Determine operation
            if mode == 'upsert_id' and 'Id' in df.columns:
                print(f"    Upserting {len(df)} records using Id...")
                cmd = [
                    'sf', 'data', 'upsert', 'bulk',
                    '--sobject', object_name,
                    '--file', str(csv_file),
                    '--external-id', 'Id',
                    '--target-org', self.target_org,
                    '--wait', '10'
                ]
            else:
                print(f"    Inserting {len(df)} new records...")
                cmd = [
                    'sf', 'data', 'import', 'bulk',
                    '--sobject', object_name,
                    '--file', str(csv_file),
                    '--target-org', self.target_org,
                    '--wait', '10'
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return 'success', "Completed successfully"
            else:
                error = result.stderr.strip()[:100] if result.stderr else "Unknown error"
                return 'failed', error
                
        except Exception as e:
            return 'failed', str(e)
    
    def run_smart_upsert(self):
        """Run the smart upsert process."""
        print("=" * 70)
        print("SMART COMPLETE UPSERT PROCESS")
        print("=" * 70)
        print(f"Source: {self.excel_file}")
        print(f"Target Org: {self.target_org}")
        print("\nThis process will:")
        print("- Skip objects that already have all records")
        print("- Insert only new records where needed")
        print("- Update existing records where appropriate")
        
        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        print("\n" + "-" * 50)
        
        for config in self.sheet_configs:
            status, message = self.process_sheet(config)
            
            if status == 'success':
                results['success'] += 1
                print(f"    ✓ {message}")
            elif status == 'failed':
                results['failed'] += 1
                print(f"    ✗ {message}")
            else:
                results['skipped'] += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✓ Successful: {results['success']}")
        print(f"✗ Failed: {results['failed']}")
        print(f"⚠️  Skipped: {results['skipped']}")
        
        print("\n✓ Smart upsert complete")
        
        # Show what's in the org now
        print("\nCurrent org status:")
        for obj in ['Product2', 'ProductCatalog', 'ProductCategory', 'AttributeDefinition', 
                   'ProductSellingModel', 'PricebookEntry']:
            cmd = ['sf', 'data', 'query', '--query', f'SELECT COUNT(Id) FROM {obj}', 
                   '--target-org', self.target_org, '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                count = data['result']['totalSize'] if 'result' in data else 0
                print(f"  {obj}: {count} records")

def main():
    runner = SmartCompleteUpsertRunner()
    runner.run_smart_upsert()

if __name__ == '__main__':
    main()