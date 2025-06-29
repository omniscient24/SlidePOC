#!/usr/bin/env python3
"""
Create new Bundle products and delete old non-bundle versions.
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
            # Copy all fields except Id
            new_product = {}
            for field, value in bundle['data'].items():
                if field != 'Id' and pd.notna(value):
                    new_product[field] = value
            
            # Ensure Type is set to Bundle
            new_product['Type'] = 'Bundle'
            
            # Set ConfigureDuringSale if not already set
            if 'ConfigureDuringSale' not in new_product or pd.isna(new_product.get('ConfigureDuringSale')):
                new_product['ConfigureDuringSale'] = 'Allowed'
            
            # Modify ProductCode to indicate it's a bundle version
            if 'ProductCode' in new_product:
                # Only add -BDL if not already present
                if not new_product['ProductCode'].endswith('-BDL'):
                    new_product['ProductCode'] = f"{new_product['ProductCode']}-BDL"
            
            new_products.append(new_product)
        
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
            csv_file.unlink()
            return False
    
    def map_old_to_new_products(self):
        """Map old product IDs to new bundle product IDs."""
        print("\n" + "-" * 40)
        print("Mapping old products to new bundles...")
        
        # Query for the newly created products
        product_codes = [f"{p['code']}-BDL" if not p['code'].endswith('-BDL') else p['code'] 
                        for p in self.bundle_products]
        
        # Build IN clause
        codes_list = "', '".join(product_codes)
        query = f"SELECT Id, Name, ProductCode FROM Product2 WHERE ProductCode IN ('{codes_list}')"
        
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
                
                print(f"\nFound {len(new_products)} newly created bundle products")
                
                # Create mapping
                for new_prod in new_products:
                    # Find corresponding old product
                    base_code = new_prod['ProductCode'].replace('-BDL', '')
                    for old_prod in self.bundle_products:
                        if old_prod['code'] == base_code or old_prod['code'] == new_prod['ProductCode']:
                            self.old_to_new_map[old_prod['old_id']] = {
                                'new_id': new_prod['Id'],
                                'name': new_prod['Name'],
                                'code': new_prod['ProductCode']
                            }
                            print(f"  Mapped: {old_prod['name']} -> {new_prod['Name']}")
                            break
    
    def update_related_records(self):
        """Update related records to point to new bundle products."""
        print("\n" + "=" * 60)
        print("UPDATING RELATED RECORDS")
        print("=" * 60)
        
        if not self.old_to_new_map:
            print("No mapping found, skipping updates")
            return
        
        # Update ProductSellingModelOption
        self.update_product_selling_model_options()
        
        # Update ProductAttributeDefinition
        self.update_product_attribute_definitions()
        
        # Update PricebookEntry
        self.update_pricebook_entries()
        
        # Update ProductCategoryProduct
        self.update_product_category_products()
    
    def update_product_selling_model_options(self):
        """Update ProductSellingModelOption to new product IDs."""
        print("\nUpdating ProductSellingModelOption records...")
        
        for old_id, new_info in self.old_to_new_map.items():
            query = f"SELECT Id FROM ProductSellingModelOption WHERE Product2Id = '{old_id}'"
            
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
                            '--sobject', 'ProductSellingModelOption',
                            '--record-id', rec['Id'],
                            '--values', f"Product2Id={new_info['new_id']}",
                            '--target-org', self.target_org
                        ]
                        
                        update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                        if update_result.returncode == 0:
                            print(f"  ✓ Updated PSMO for {new_info['name']}")
                        else:
                            print(f"  ✗ Failed to update PSMO: {update_result.stderr}")
    
    def update_product_attribute_definitions(self):
        """Update ProductAttributeDefinition to new product IDs."""
        print("\nUpdating ProductAttributeDefinition records...")
        
        for old_id, new_info in self.old_to_new_map.items():
            query = f"SELECT Id FROM ProductAttributeDefinition WHERE ProductId = '{old_id}'"
            
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
                            '--sobject', 'ProductAttributeDefinition',
                            '--record-id', rec['Id'],
                            '--values', f"ProductId={new_info['new_id']}",
                            '--target-org', self.target_org
                        ]
                        
                        update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                        if update_result.returncode == 0:
                            print(f"  ✓ Updated PAD for {new_info['name']}")
    
    def update_pricebook_entries(self):
        """Update PricebookEntry to new product IDs."""
        print("\nUpdating PricebookEntry records...")
        
        for old_id, new_info in self.old_to_new_map.items():
            query = f"SELECT Id FROM PricebookEntry WHERE Product2Id = '{old_id}'"
            
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
                            '--sobject', 'PricebookEntry',
                            '--record-id', rec['Id'],
                            '--values', f"Product2Id={new_info['new_id']}",
                            '--target-org', self.target_org
                        ]
                        
                        update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                        if update_result.returncode == 0:
                            print(f"  ✓ Updated PBE for {new_info['name']}")
    
    def update_product_category_products(self):
        """Update ProductCategoryProduct to new product IDs."""
        print("\nUpdating ProductCategoryProduct records...")
        
        for old_id, new_info in self.old_to_new_map.items():
            query = f"SELECT Id FROM ProductCategoryProduct WHERE ProductId = '{old_id}'"
            
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
                            '--sobject', 'ProductCategoryProduct',
                            '--record-id', rec['Id'],
                            '--values', f"ProductId={new_info['new_id']}",
                            '--target-org', self.target_org
                        ]
                        
                        update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                        if update_result.returncode == 0:
                            print(f"  ✓ Updated PCP for {new_info['name']}")
    
    def delete_old_products(self):
        """Delete the old non-bundle products."""
        print("\n" + "=" * 60)
        print("DELETING OLD PRODUCTS")
        print("=" * 60)
        
        if not self.old_to_new_map:
            print("No products to delete")
            return
        
        print(f"\nDeleting {len(self.old_to_new_map)} old products...")
        
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
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully deleted old products")
            for old_id, new_info in self.old_to_new_map.items():
                print(f"  - Deleted old product, replaced with: {new_info['name']}")
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
                'mappings': self.old_to_new_map
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