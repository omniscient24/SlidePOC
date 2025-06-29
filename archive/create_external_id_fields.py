#!/usr/bin/env python3
"""
Create External_ID__c field on Revenue Cloud objects if it doesn't already exist.
"""

import subprocess
import json
from pathlib import Path

class ExternalIdFieldCreator:
    def __init__(self):
        self.target_org = 'fortradp2'
        
        # List of objects that need External_ID__c field
        self.objects_needing_external_id = [
            'CostBook',
            'LegalEntity', 
            'TaxEngine',
            'TaxPolicy',
            'TaxTreatment',
            'ProductClassification',
            'AttributeDefinition',
            'AttributeCategory',
            'ProductCatalog',
            'ProductCategory',
            'ProductSellingModel',
            'Product2',
            'Pricebook2',
            'ProductComponentGroup',
            'ProductAttributeDefinition',
            'PricebookEntry',
            'CostBookEntry',
            'PriceAdjustmentSchedule',
            'PriceAdjustmentTier',
            'AttributeBasedAdjRule',
            'ProductRelatedComponent',
            'ProductCategoryProduct',
            'ProductClassificationAttr'
        ]
    
    def check_field_exists(self, object_name, field_name):
        """Check if a field exists on an object."""
        try:
            cmd = [
                'sf', 'sobject', 'describe',
                '--sobject', object_name,
                '--target-org', self.target_org,
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data and 'fields' in data['result']:
                    fields = data['result']['fields']
                    for field in fields:
                        if field.get('name') == field_name:
                            return True
            return False
        except Exception as e:
            print(f"Error checking field {field_name} on {object_name}: {str(e)}")
            return False
    
    def create_external_id_field(self, object_name):
        """Create External_ID__c field on an object."""
        print(f"\n  Creating External_ID__c on {object_name}...")
        
        # Create metadata file for the field
        metadata_dir = Path('metadata_temp')
        metadata_dir.mkdir(exist_ok=True)
        
        # Create object directory
        object_dir = metadata_dir / 'objects' / object_name
        object_dir.mkdir(parents=True, exist_ok=True)
        
        # Create field metadata file
        field_metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>External_ID__c</fullName>
    <externalId>true</externalId>
    <label>External ID</label>
    <length>255</length>
    <required>false</required>
    <trackHistory>false</trackHistory>
    <type>Text</type>
    <unique>true</unique>
</CustomField>"""
        
        field_file = object_dir / 'fields' / 'External_ID__c.field-meta.xml'
        field_file.parent.mkdir(exist_ok=True)
        
        with open(field_file, 'w') as f:
            f.write(field_metadata)
        
        # Deploy the field
        try:
            cmd = [
                'sf', 'project', 'deploy', 'start',
                '--source-dir', str(metadata_dir),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"    ✓ Successfully created External_ID__c on {object_name}")
                return True
            else:
                # Check if it's because the field already exists
                if 'duplicate value found' in result.stderr:
                    print(f"    ℹ Field already exists (duplicate error)")
                    return True
                else:
                    print(f"    ✗ Failed to create field: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"    ✗ Exception creating field: {str(e)}")
            return False
        finally:
            # Clean up metadata files
            import shutil
            if metadata_dir.exists():
                shutil.rmtree(metadata_dir)
    
    def create_all_external_id_fields(self):
        """Create External_ID__c fields on all objects that need them."""
        print("=" * 60)
        print("CREATING EXTERNAL ID FIELDS")
        print("=" * 60)
        
        created_count = 0
        exists_count = 0
        failed_count = 0
        
        for object_name in self.objects_needing_external_id:
            print(f"\nChecking {object_name}...")
            
            # Check if field already exists
            if self.check_field_exists(object_name, 'External_ID__c'):
                print(f"  ✓ External_ID__c already exists")
                exists_count += 1
            else:
                print(f"  ✗ External_ID__c does not exist")
                # Try to create it
                if self.create_external_id_field(object_name):
                    created_count += 1
                else:
                    failed_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Already existed: {exists_count}")
        print(f"Created new: {created_count}")
        print(f"Failed: {failed_count}")
        print(f"Total objects: {len(self.objects_needing_external_id)}")
        
        if failed_count > 0:
            print("\nNote: Some fields failed to create. This might be because:")
            print("- The object doesn't exist in this org")
            print("- You don't have permission to create fields")
            print("- The object doesn't support custom fields")
        
        return failed_count == 0

def main():
    creator = ExternalIdFieldCreator()
    success = creator.create_all_external_id_fields()
    
    if success:
        print("\nAll External_ID__c fields are ready!")
        print("You can now run the upsert process.")
    else:
        print("\nSome External_ID__c fields could not be created.")
        print("The upsert may fail for those objects.")

if __name__ == '__main__':
    main()