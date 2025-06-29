#\!/usr/bin/env python3
"""
Check remaining issues after read-only field removal.
"""

import subprocess
import json

def check_object_issues(object_name, sample_id=None):
    """Check specific issues for an object."""
    print(f"\n{object_name}:")
    print("-" * 40)
    
    # Get field info
    cmd = [
        'sf', 'sobject', 'describe',
        '--sobject', object_name,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data:
            # Check for external ID fields
            external_ids = []
            updateable_fields = []
            
            for field in data['result']['fields']:
                if field.get('externalId', False):
                    external_ids.append(field['name'])
                if field.get('updateable', False):
                    updateable_fields.append(field['name'])
            
            print(f"External ID fields: {external_ids if external_ids else 'None'}")
            print(f"Sample updateable fields: {updateable_fields[:5]}...")
            
            # For specific objects, check additional info
            if object_name == 'AttributeDefinition':
                readonly_fields = []
                for field in data['result']['fields']:
                    if field['name'] in ['DataType', 'DeveloperName'] and not field.get('updateable', False):
                        readonly_fields.append(field['name'])
                if readonly_fields:
                    print(f"Known read-only fields still causing issues: {readonly_fields}")

def main():
    print("=" * 60)
    print("CHECKING REMAINING UPSERT ISSUES")
    print("=" * 60)
    
    # Check specific problematic objects
    problematic_objects = [
        'ProductCategory',
        'AttributePicklist', 
        'AttributeDefinition',
        'ProductSellingModel',
        'Product2',
        'ProductCategoryProduct',
        'ProductRelatedComponent'
    ]
    
    for obj in problematic_objects:
        check_object_issues(obj)

if __name__ == '__main__':
    main()
