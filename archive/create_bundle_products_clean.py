#!/usr/bin/env python3
"""
Create new Bundle products with only valid fields.
"""

import pandas as pd
import subprocess
import json
from pathlib import Path
from datetime import datetime

class BundleProductCreator:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        self.bundle_products = []
        self.old_to_new_map = {}
        
        # Valid Product2 fields for creation
        self.valid_fields = [
            'Name', 'ProductCode', 'Description', 'Family', 'IsActive',
            'QuantityUnitOfMeasure', 'Type', 'ConfigureDuringSale',
            'IsIncludedInAma', 'StockKeepingUnit', 'BasedOnId'
        ]
        
    def identify_bundle_products(self):
        """Identify products marked as Bundle in the spreadsheet."""
        print("=" * 60)
        print("IDENTIFYING BUNDLE PRODUCTS")
        print("=" * 60)
        
        # Read Product2 sheet
        df = pd.read_excel(self.workbook_path, sheet_name='13_Product2')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Find products with Type='Bundle'
        bundle_df = df[df['Type'] == 'Bundle'].copy()
        
        print(f"\nFound {len(bundle_df)} products marked as Bundle:")
        for idx, row in bundle_df.iterrows():
            print(f"  - {row['Name']} ({row['ProductCode']})")
            self.bundle_products.append({
                'old_id': row['Id'],
                'name': row['Name'],
                'code': row['ProductCode'],
                'data': row.to_dict()
            })
        
        return len(bundle_df) > 0
    
    def create_new_bundle_products(self):
        """Create new Product2 records with Type='Bundle'."""
        print("\n" + "=" * 60)
        print("CREATING NEW BUNDLE PRODUCTS")
        print("=" * 60)
        
        # Prepare data for new bundle products
        new_products = []
        
        for bundle in self.bundle_products:
            # Only include valid fields
            new_product = {}
            for field in self.valid_fields:
                if field in bundle['data'] and pd.notna(bundle['data'][field]):
                    new_product[field] = bundle['data'][field]
            
            # Ensure required fields
            new_product['Type'] = 'Bundle'
            new_product['IsActive'] = True
            
            # Set ConfigureDuringSale if not already set
            if 'ConfigureDuringSale' not in new_product:
                new_product['ConfigureDuringSale'] = 'Allowed'
            
            # Modify ProductCode to indicate it's a bundle version
            if 'ProductCode' in new_product and not new_product['ProductCode'].endswith('-BDL'):
                new_product['ProductCode'] = f"{new_product['ProductCode']}-BDL"
            
            new_products.append(new_product)
            
            print(f"\nPreparing: {new_product['Name']}")
            print(f"  ProductCode: {new_product['ProductCode']}")
            print(f"  Type: {new_product['Type']}")
            print(f"  ConfigureDuringSale: {new_product['ConfigureDuringSale']}")
        
        # Create CSV for bulk insert
        df_new = pd.DataFrame(new_products)
        csv_file = Path('data/temp_new_bundles.csv')
        df_new.to_csv(csv_file, index=False)
        
        print(f"\nCreating {len(new_products)} new bundle products...")
        
        # Insert new products
        cmd = [
            'sf', 'data', 'import', 'bulk',
            '--sobject', 'Product2',
            '--file', str(csv_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully created new bundle products")
            
            # Get the new product IDs
            self.map_old_to_new_products()
            
            # Clean up
            csv_file.unlink()
            return True
        else:
            print(f"✗ Failed to create products: {result.stderr}")
            
            # Check for detailed errors
            if '--job-id' in result.stderr:
                import re
                match = re.search(r'--job-id (\w+)', result.stderr)
                if match:
                    job_id = match.group(1)
                    self.check_job_errors(job_id)
            
            csv_file.unlink()
            return False
    
    def check_job_errors(self, job_id):
        """Check detailed job errors."""
        print(f"\nChecking job {job_id} for errors...")
        cmd = [
            'sf', 'data', 'bulk', 'results',
            '--job-id', job_id,
            '--target-org', self.target_org
        ]
        subprocess.run(cmd)
    
    def map_old_to_new_products(self):
        """Map old product IDs to new bundle product IDs."""
        print("\n" + "-" * 40)
        print("Mapping old products to new bundles...")
        
        # Query for the newly created products
        product_codes = [f"{p['code']}-BDL" if not p['code'].endswith('-BDL') else p['code'] 
                        for p in self.bundle_products]
        
        # Build query with proper escaping
        codes_list = "', '".join(product_codes)
        query = f"SELECT Id, Name, ProductCode, Type FROM Product2 WHERE ProductCode IN ('{codes_list}')"
        
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
                new_products = data['result']['records']
                
                print(f"\nFound {len(new_products)} newly created bundle products:")
                
                # Create mapping
                for new_prod in new_products:
                    print(f"  - {new_prod['Name']} ({new_prod['ProductCode']}) - Type: {new_prod['Type']}")
                    
                    # Find corresponding old product
                    base_code = new_prod['ProductCode'].replace('-BDL', '')
                    for old_prod in self.bundle_products:
                        if old_prod['code'] == base_code or old_prod['code'] == new_prod['ProductCode']:
                            self.old_to_new_map[old_prod['old_id']] = {
                                'new_id': new_prod['Id'],
                                'name': new_prod['Name'],
                                'code': new_prod['ProductCode']
                            }
                            break
    
    def update_related_records(self):
        """Update related records to point to new bundle products."""
        print("\n" + "=" * 60)
        print("UPDATING RELATED RECORDS")
        print("=" * 60)
        
        if not self.old_to_new_map:
            print("No mapping found, skipping updates")
            return
        
        # Count related records first
        self.count_related_records()
        
        # Update each type
        self.update_records('ProductSellingModelOption', 'Product2Id')
        self.update_records('ProductAttributeDefinition', 'ProductId')
        self.update_records('PricebookEntry', 'Product2Id')
        self.update_records('ProductCategoryProduct', 'ProductId')
    
    def count_related_records(self):
        """Count related records that need updating."""
        print("\nCounting related records...")
        
        for old_id, new_info in self.old_to_new_map.items():
            print(f"\nFor {new_info['name']}:")
            
            # Check each object type
            objects = [
                ('ProductSellingModelOption', 'Product2Id'),
                ('ProductAttributeDefinition', 'ProductId'),
                ('PricebookEntry', 'Product2Id'),
                ('ProductCategoryProduct', 'ProductId')
            ]
            
            for obj_name, field_name in objects:
                query = f"SELECT COUNT() FROM {obj_name} WHERE {field_name} = '{old_id}'"
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
                        count = data['result']['totalSize']
                        if count > 0:
                            print(f"  - {obj_name}: {count} records")
    
    def update_records(self, object_name, field_name):
        """Generic method to update related records."""
        print(f"\nUpdating {object_name} records...")
        
        update_count = 0
        for old_id, new_info in self.old_to_new_map.items():
            query = f"SELECT Id FROM {object_name} WHERE {field_name} = '{old_id}'"
            
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
                    
                    for rec in records:
                        update_cmd = [
                            'sf', 'data', 'update', 'record',
                            '--sobject', object_name,
                            '--record-id', rec['Id'],
                            '--values', f"{field_name}={new_info['new_id']}",
                            '--target-org', self.target_org
                        ]
                        
                        update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                        if update_result.returncode == 0:
                            update_count += 1
        
        if update_count > 0:
            print(f"  ✓ Updated {update_count} {object_name} records")
    
    def delete_old_products(self):
        """Delete the old non-bundle products."""
        print("\n" + "=" * 60)
        print("DELETING OLD PRODUCTS")
        print("=" * 60)
        
        if not self.old_to_new_map:
            print("No products to delete")
            return
        
        print(f"\nPreparing to delete {len(self.old_to_new_map)} old products:")
        for old_id, new_info in self.old_to_new_map.items():
            print(f"  - Will delete old version of: {new_info['name']}")
        
        # Create CSV with IDs to delete
        delete_data = [{'Id': old_id} for old_id in self.old_to_new_map.keys()]
        df_delete = pd.DataFrame(delete_data)
        csv_file = Path('data/temp_delete_products.csv')
        df_delete.to_csv(csv_file, index=False)
        
        # Delete products
        cmd = [
            'sf', 'data', 'delete', 'bulk',
            '--sobject', 'Product2',
            '--file', str(csv_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        print("\nDeleting old products...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully deleted old products")
        else:
            print(f"✗ Failed to delete products: {result.stderr}")
        
        # Clean up
        csv_file.unlink()
    
    def create_summary_report(self):
        """Create a summary of the bundle migration."""
        print("\n" + "=" * 60)
        print("BUNDLE MIGRATION SUMMARY")
        print("=" * 60)
        
        if self.old_to_new_map:
            print(f"\n✓ Successfully migrated {len(self.old_to_new_map)} products to bundles:")
            for old_id, new_info in self.old_to_new_map.items():
                print(f"  - {new_info['name']} ({new_info['code']})")
                print(f"    New ID: {new_info['new_id']}")
        
        # Save mapping to file
        mapping_file = Path('data/bundle_migration_mapping.json')
        with open(mapping_file, 'w') as f:
            json.dump({
                'migration_date': datetime.now().isoformat(),
                'mappings': self.old_to_new_map,
                'bundle_products': [
                    {
                        'name': p['name'],
                        'old_code': p['code'],
                        'new_code': f"{p['code']}-BDL" if not p['code'].endswith('-BDL') else p['code']
                    }
                    for p in self.bundle_products
                ]
            }, f, indent=2)
        
        print(f"\n✓ Mapping saved to: {mapping_file}")

def main():
    creator = BundleProductCreator()
    
    # Identify bundle products
    if not creator.identify_bundle_products():
        print("\nNo products marked as Bundle in the spreadsheet")
        return
    
    # Create new bundle products
    if creator.create_new_bundle_products():
        # Update related records
        creator.update_related_records()
        
        # Delete old products
        creator.delete_old_products()
        
        # Create summary
        creator.create_summary_report()
    else:
        print("\nBundle creation failed, aborting process")

if __name__ == '__main__':
    main()