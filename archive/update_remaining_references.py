#!/usr/bin/env python3
"""
Update remaining references to old products before deletion.
"""

import subprocess
import json
from pathlib import Path

class ReferenceUpdater:
    def __init__(self):
        self.target_org = 'fortradp2'
        
        # Load the mapping from previous run
        mapping_file = Path('data/bundle_migration_mapping.json')
        with open(mapping_file, 'r') as f:
            data = json.load(f)
            self.mappings = data['mappings']
    
    def update_product_attribute_definitions(self):
        """Update all ProductAttributeDefinition records."""
        print("=" * 60)
        print("UPDATING PRODUCT ATTRIBUTE DEFINITIONS")
        print("=" * 60)
        
        total_updated = 0
        
        for old_id, new_info in self.mappings.items():
            print(f"\nChecking for {new_info['name']}...")
            
            # Query for PAD records
            query = f"SELECT Id, ProductId, AttributeDefinitionId FROM ProductAttributeDefinition WHERE ProductId = '{old_id}'"
            
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
                    
                    if records:
                        print(f"  Found {len(records)} ProductAttributeDefinition records")
                        
                        for rec in records:
                            # Update to new product ID
                            update_cmd = [
                                'sf', 'data', 'update', 'record',
                                '--sobject', 'ProductAttributeDefinition',
                                '--record-id', rec['Id'],
                                '--values', f"ProductId={new_info['new_id']}",
                                '--target-org', self.target_org
                            ]
                            
                            update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                            
                            if update_result.returncode == 0:
                                total_updated += 1
                                print(f"    ✓ Updated PAD {rec['Id']}")
                            else:
                                print(f"    ✗ Failed to update: {update_result.stderr}")
        
        print(f"\n✓ Total ProductAttributeDefinition records updated: {total_updated}")
    
    def check_quote_line_items(self):
        """Check for Quote Line Items referencing old products."""
        print("\n" + "=" * 60)
        print("CHECKING QUOTE LINE ITEMS")
        print("=" * 60)
        
        print("\nNote: Quote Line Items cannot be updated to reference different products.")
        print("Options:")
        print("1. Delete the quotes containing these line items")
        print("2. Keep the old products (not delete them)")
        print("3. Create new quotes with the bundle products")
        
        for old_id, new_info in self.mappings.items():
            # Check if QuoteLineItem object exists
            query = f"SELECT COUNT() FROM QuoteLineItem WHERE Product2Id = '{old_id}'"
            
            cmd = [
                'sf', 'data', 'query',
                '--query', query,
                '--target-org', self.target_org,
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.DEVNULL)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data:
                    count = data['result']['totalSize']
                    if count > 0:
                        print(f"\n  {new_info['name']}: {count} Quote Line Items found")
    
    def update_all_references(self):
        """Update all possible references."""
        print("=" * 60)
        print("UPDATING ALL REMAINING REFERENCES")
        print("=" * 60)
        
        # Update ProductSellingModelOption
        self.update_generic_object('ProductSellingModelOption', 'Product2Id')
        
        # Update PricebookEntry
        self.update_generic_object('PricebookEntry', 'Product2Id')
        
        # Update ProductCategoryProduct
        self.update_generic_object('ProductCategoryProduct', 'ProductId')
    
    def update_generic_object(self, object_name, field_name):
        """Update any object with product references."""
        print(f"\nUpdating {object_name}...")
        
        total_updated = 0
        
        for old_id, new_info in self.mappings.items():
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
                            total_updated += 1
        
        if total_updated > 0:
            print(f"  ✓ Updated {total_updated} records")
        else:
            print(f"  No records to update")
    
    def attempt_deletion_again(self):
        """Try to delete old products again."""
        print("\n" + "=" * 60)
        print("ATTEMPTING DELETION AGAIN")
        print("=" * 60)
        
        # Create CSV with IDs to delete
        delete_data = [{'Id': old_id} for old_id in self.mappings.keys()]
        df = pd.DataFrame(delete_data)
        csv_file = Path('data/temp_delete_products_retry.csv')
        df.to_csv(csv_file, index=False)
        
        print(f"\nAttempting to delete {len(delete_data)} products...")
        
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
        else:
            print("✗ Deletion still failing")
            print("\nProducts cannot be deleted due to Quote Line Item references.")
            print("The old products will remain in the system.")
            print("\nThe bundle migration is complete with new bundle products created:")
            for old_id, new_info in self.mappings.items():
                print(f"  - {new_info['name']} ({new_info['code']})")
        
        # Clean up
        csv_file.unlink()

def main():
    import pandas as pd
    
    updater = ReferenceUpdater()
    
    # Update ProductAttributeDefinitions
    updater.update_product_attribute_definitions()
    
    # Update other references
    updater.update_all_references()
    
    # Check Quote Line Items
    updater.check_quote_line_items()
    
    # Try deletion again
    updater.attempt_deletion_again()

if __name__ == '__main__':
    main()