#!/usr/bin/env python3
"""
Import remaining objects that haven't been successfully imported yet.
"""

import subprocess
import json
from pathlib import Path
import pandas as pd

class RemainingImporter:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.target_org = 'fortradp2'
        
    def check_what_exists(self):
        """Check what's already in the org."""
        print("=" * 60)
        print("CHECKING EXISTING DATA")
        print("=" * 60)
        
        objects = [
            ('Product2', 'SELECT COUNT(Id) FROM Product2'),
            ('AttributeDefinition', 'SELECT COUNT(Id) FROM AttributeDefinition'),
            ('ProductAttributeDefinition', 'SELECT COUNT(Id) FROM ProductAttributeDefinition'),
            ('PricebookEntry', 'SELECT COUNT(Id) FROM PricebookEntry WHERE Pricebook2.Name != \'Standard Price Book\''),
            ('ProductCategoryProduct', 'SELECT COUNT(Id) FROM ProductCategoryProduct'),
            ('ProductRelatedComponent', 'SELECT COUNT(Id) FROM ProductRelatedComponent'),
            ('AttributeCategory', 'SELECT COUNT(Id) FROM AttributeCategory')
        ]
        
        for obj_name, query in objects:
            cmd = ['sf', 'data', 'query', '--query', query, '--target-org', self.target_org, '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data:
                    count = data['result']['totalSize']
                    print(f"{obj_name}: {count} records")
    
    def import_attribute_categories(self):
        """Import AttributeCategory if not already done."""
        print("\nImporting AttributeCategory...")
        
        # Check if already imported
        cmd = ['sf', 'data', 'query', '--query', 'SELECT Id FROM AttributeCategory LIMIT 1', 
               '--target-org', self.target_org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data['result']['totalSize'] > 0:
                print("  Already imported")
                return True
        
        # Import
        df = pd.read_csv(self.csv_dir / '10_AttributeCategory.csv')
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        temp_file = Path('temp_attr_cat.csv')
        df.to_csv(temp_file, index=False)
        
        cmd = ['sf', 'data', 'import', 'bulk', '--sobject', 'AttributeCategory',
               '--file', str(temp_file), '--target-org', self.target_org, '--wait', '10']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        temp_file.unlink()
        
        if result.returncode == 0:
            print("  ✓ Success!")
            return True
        else:
            print("  ✗ Failed")
            return False
    
    def import_remaining_attribute_definitions(self):
        """Import remaining AttributeDefinitions."""
        print("\nImporting remaining AttributeDefinitions...")
        
        # Get existing codes
        cmd = ['sf', 'data', 'query', '--query', 'SELECT Code FROM AttributeDefinition',
               '--target-org', self.target_org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        existing_codes = set()
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                existing_codes = {r['Code'] for r in data['result']['records'] if r.get('Code')}
                print(f"  Found {len(existing_codes)} existing records")
        
        # Read CSV and filter
        df = pd.read_csv(self.csv_dir / '09_AttributeDefinition.csv')
        
        # Fix empty fields
        if 'Label' in df.columns:
            df['Label'] = df['Label'].fillna(df['Name'])
        if 'DataType' in df.columns:
            df['DataType'] = df['DataType'].fillna('Text')
        
        # Filter out existing
        if 'Code' in df.columns and existing_codes:
            df = df[~df['Code'].isin(existing_codes)]
        
        if len(df) == 0:
            print("  All records already imported")
            return True
        
        print(f"  {len(df)} new records to import")
        
        # Remove Id and save
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        temp_file = Path('temp_attr_def.csv')
        df.to_csv(temp_file, index=False)
        
        cmd = ['sf', 'data', 'import', 'bulk', '--sobject', 'AttributeDefinition',
               '--file', str(temp_file), '--target-org', self.target_org, '--wait', '10']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        temp_file.unlink()
        
        if result.returncode == 0:
            print("  ✓ Success!")
            return True
        else:
            print("  ✗ Failed")
            return False
    
    def import_junction_objects(self):
        """Import junction objects with correct references."""
        print("\nImporting junction objects...")
        
        # Get Product mappings
        cmd = ['sf', 'data', 'query', '--query', 'SELECT Id, ProductCode, Name FROM Product2',
               '--target-org', self.target_org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        product_mapping = {}
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                for r in data['result']['records']:
                    if r.get('ProductCode'):
                        product_mapping[r['ProductCode']] = r['Id']
                    product_mapping[r['Name']] = r['Id']
        
        print(f"  Found {len(product_mapping)} products")
        
        # Import PricebookEntry
        print("\n  PricebookEntry:")
        pbe_df = pd.read_csv(self.csv_dir / '20_PricebookEntry.csv')
        
        # Get Standard Pricebook
        cmd = ['sf', 'data', 'query', '--query', "SELECT Id FROM Pricebook2 WHERE IsStandard = true",
               '--target-org', self.target_org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data['result']['totalSize'] > 0:
                standard_pb_id = data['result']['records'][0]['Id']
                # Use standard pricebook if Pricebook2Id is missing
                if 'Pricebook2Id' in pbe_df.columns:
                    pbe_df['Pricebook2Id'] = pbe_df['Pricebook2Id'].fillna(standard_pb_id)
        
        # Ensure we have valid Product2Ids
        valid_product_ids = set(product_mapping.values())
        if 'Product2Id' in pbe_df.columns:
            pbe_df = pbe_df[pbe_df['Product2Id'].isin(valid_product_ids)]
        
        if 'Id' in pbe_df.columns:
            pbe_df = pbe_df.drop(columns=['Id'])
        
        if len(pbe_df) > 0:
            temp_file = Path('temp_pbe.csv')
            pbe_df.to_csv(temp_file, index=False)
            
            cmd = ['sf', 'data', 'import', 'bulk', '--sobject', 'PricebookEntry',
                   '--file', str(temp_file), '--target-org', self.target_org, '--wait', '10']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            temp_file.unlink()
            
            print(f"    {len(pbe_df)} records: {'✓ Success' if result.returncode == 0 else '✗ Failed'}")
        else:
            print("    No valid records to import")
        
        return True
    
    def run_remaining_imports(self):
        """Run all remaining imports."""
        self.check_what_exists()
        
        print("\n" + "=" * 60)
        print("IMPORTING REMAINING OBJECTS")
        print("=" * 60)
        
        # Import in dependency order
        self.import_attribute_categories()
        self.import_remaining_attribute_definitions()
        self.import_junction_objects()
        
        print("\n✓ Import process completed")
        print("\nFinal status:")
        self.check_what_exists()

def main():
    importer = RemainingImporter()
    importer.run_remaining_imports()

if __name__ == '__main__':
    main()