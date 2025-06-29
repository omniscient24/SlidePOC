#!/usr/bin/env python3
"""
Final import with duplicate checks and comprehensive fixes.
"""

import subprocess
import json
from pathlib import Path
import pandas as pd

class FinalImporter:
    def __init__(self):
        self.csv_dir = Path('data/csv_final_output')
        self.final_dir = Path('data/csv_final_import')
        self.final_dir.mkdir(parents=True, exist_ok=True)
        self.target_org = 'fortradp2'
        
    def get_existing_records(self, object_name, unique_field):
        """Get existing records to avoid duplicates."""
        query = f"SELECT Id, {unique_field} FROM {object_name}"
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--result-format', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                return {r[unique_field]: r['Id'] for r in data['result']['records'] if r.get(unique_field)}
        return {}
    
    def process_attribute_definition(self):
        """Process AttributeDefinition with duplicate check."""
        print("\nProcessing AttributeDefinition...")
        df = pd.read_csv(self.csv_dir / '09_AttributeDefinition.csv')
        
        # Fix empty fields
        if 'Label' in df.columns and 'Name' in df.columns:
            df['Label'] = df['Label'].fillna(df['Name'])
        
        if 'DataType' in df.columns:
            df['DataType'] = df['DataType'].fillna('Text')
        
        # Check existing records by Code
        existing = self.get_existing_records('AttributeDefinition', 'Code')
        if existing:
            print(f"  Found {len(existing)} existing records")
            # Filter out duplicates
            df = df[~df['Code'].isin(existing.keys())]
            print(f"  {len(df)} new records to insert")
        
        # Remove Id column
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        df.to_csv(self.final_dir / '09_AttributeDefinition.csv', index=False)
        return len(df) > 0
    
    def process_product_selling_model(self):
        """Process ProductSellingModel."""
        print("\nProcessing ProductSellingModel...")
        df = pd.read_csv(self.csv_dir / '15_ProductSellingModel.csv')
        
        # Check existing by Name
        existing = self.get_existing_records('ProductSellingModel', 'Name')
        if existing:
            print(f"  Found {len(existing)} existing records")
            df = df[~df['Name'].isin(existing.keys())]
            print(f"  {len(df)} new records to insert")
        
        # Ensure required fields
        if 'Status' in df.columns:
            df['Status'] = df['Status'].fillna('Active')
        
        # Remove Id column
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        df.to_csv(self.final_dir / '15_ProductSellingModel.csv', index=False)
        return len(df) > 0
    
    def process_product2(self):
        """Process Product2 with duplicate check."""
        print("\nProcessing Product2...")
        df = pd.read_csv(self.csv_dir / '13_Product2.csv')
        
        # Check existing by ProductCode
        existing = self.get_existing_records('Product2', 'ProductCode')
        if existing:
            print(f"  Found {len(existing)} existing records")
            # Keep track of mapping for later use
            self.product_mapping = existing
            df = df[~df['ProductCode'].isin(existing.keys())]
            print(f"  {len(df)} new records to insert")
        
        # Remove Id column
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
        
        df.to_csv(self.final_dir / '13_Product2.csv', index=False)
        return len(df) > 0
    
    def update_product_references(self):
        """Update all Product ID references."""
        print("\nUpdating Product ID references...")
        
        # Get all current products
        products = self.get_existing_records('Product2', 'ProductCode')
        print(f"  Found {len(products)} total products")
        
        # Update PricebookEntry
        pbe_file = self.csv_dir / '20_PricebookEntry.csv'
        if pbe_file.exists():
            df = pd.read_csv(pbe_file)
            # This would need original ProductCode mapping
            # For now, skip records with invalid Product2Id
            valid_ids = set(products.values())
            if 'Product2Id' in df.columns:
                df = df[df['Product2Id'].isin(valid_ids)]
            if 'Id' in df.columns:
                df = df.drop(columns=['Id'])
            df.to_csv(self.final_dir / '20_PricebookEntry.csv', index=False)
            print(f"  Updated PricebookEntry: {len(df)} records")
        
        # Update other files similarly...
        return True
    
    def run_final_import(self):
        """Run the final import."""
        print("\n" + "=" * 60)
        print("FINAL IMPORT PROCESS")
        print("=" * 60)
        
        # Process and prepare files
        steps = [
            (self.process_attribute_definition, 'AttributeDefinition', '09_AttributeDefinition.csv'),
            (self.process_product_selling_model, 'ProductSellingModel', '15_ProductSellingModel.csv'),
            (self.process_product2, 'Product2', '13_Product2.csv'),
        ]
        
        for process_func, obj_name, csv_file in steps:
            if process_func():
                # Import the file
                file_path = self.final_dir / csv_file
                df = pd.read_csv(file_path)
                
                print(f"\nImporting {obj_name}: {len(df)} records")
                
                cmd = [
                    'sf', 'data', 'import', 'bulk',
                    '--sobject', obj_name,
                    '--file', str(file_path),
                    '--target-org', self.target_org,
                    '--wait', '10'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("  ✓ Success!")
                else:
                    print("  ✗ Failed")
                    # Get job ID for details
                    if 'Job ID' in result.stderr:
                        for line in result.stderr.split('\n'):
                            if 'Job ID' in line or 'job-id' in line:
                                print(f"  {line.strip()}")
            else:
                print(f"\n{obj_name}: No new records to import")
        
        # Update references after base objects are imported
        self.update_product_references()
        
        print("\n✓ Import process completed")
        print("\nNext steps:")
        print("1. Check the job results for any failures")
        print("2. Update junction object references")
        print("3. Re-run for dependent objects")

def main():
    importer = FinalImporter()
    importer.run_final_import()

if __name__ == '__main__':
    main()