#!/usr/bin/env python3
"""
Discover which Revenue Cloud objects are available in the Salesforce org
"""

import subprocess
import json
import sys

# List of potential Revenue Cloud objects to check
REVENUE_CLOUD_OBJECTS = [
    'ProductCatalog',
    'ProductCategory',
    'ProductCategoryProduct',
    'ProductSellingModel',
    'ProductSellingModelOption',
    'ProductComponentGroup',
    'ProductRelatedComponent',
    'ProductClassification',
    'ProductAttributeDefinition',
    'AttributeDefinition',
    'AttributePicklist',
    'AttributePicklistValue',
    'AttributeCategory',
    'LegalEntity',
    'TaxTreatment',
    'TaxPolicy',
    'TaxEngine',
    'BillingPolicy',
    'BillingTreatment',
    'BillingSchedule',
    'BillingScheduleGroup',
    'CostBook',
    'CostBookEntry',
    'PriceAdjustmentSchedule',
    'PriceAdjustmentTier',
    'AttributeBasedAdjRule',
    'AttributeBasedAdj',
    'Order',
    'OrderItem',
    'Asset',
    'AssetAction',
    'AssetActionSource',
    'Contract'
]

def check_object_exists(org, object_name):
    """Check if an object exists and get its field information"""
    cmd = [
        'sf', 'sobject', 'describe',
        '--sobject', object_name,
        '--target-org', org,
        '--json'
    ]
    
    try:
        with open('/dev/null', 'w') as devnull:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=devnull, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('status') == 0:
                fields = data.get('result', {}).get('fields', [])
                field_names = [f['name'] for f in fields if f.get('name')]
                return True, field_names
    except:
        pass
    
    return False, []

def get_sample_data(org, object_name, fields):
    """Get sample data to verify object accessibility"""
    field_list = ', '.join(fields[:5])  # Get first 5 fields
    query = f"SELECT {field_list} FROM {object_name} LIMIT 1"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', org,
        '--json'
    ]
    
    try:
        with open('/dev/null', 'w') as devnull:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=devnull, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('status') == 0:
                total_size = data.get('result', {}).get('totalSize', 0)
                return True, total_size
    except:
        pass
    
    return False, 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python discover_revenue_cloud_objects.py <org_alias>")
        sys.exit(1)
    
    org = sys.argv[1]
    print(f"Discovering Revenue Cloud objects in org: {org}\n")
    
    available_objects = {}
    
    for obj in REVENUE_CLOUD_OBJECTS:
        print(f"Checking {obj}...", end=' ')
        exists, fields = check_object_exists(org, obj)
        
        if exists:
            # Check if we can query the object
            queryable, record_count = get_sample_data(org, obj, fields)
            
            if queryable:
                print(f"✓ Available ({len(fields)} fields, {record_count} records)")
                
                # Find important fields
                important_fields = []
                for field in fields:
                    if field in ['Id', 'Name', 'IsActive', 'Status', 'Description']:
                        important_fields.append(field)
                    elif 'Name' in field or 'Code' in field or 'Number' in field:
                        important_fields.append(field)
                    elif field.endswith('Id') and not field.startswith('Last'):
                        important_fields.append(field)
                
                # Check for External_ID__c
                if 'External_ID__c' in fields:
                    important_fields.insert(1, 'External_ID__c')
                
                available_objects[obj] = {
                    'total_fields': len(fields),
                    'record_count': record_count,
                    'important_fields': important_fields[:10],  # Limit to 10 fields
                    'all_fields': fields
                }
            else:
                print("✗ Not queryable")
        else:
            print("✗ Not available")
    
    print("\n" + "="*60)
    print("SUMMARY - Available Revenue Cloud Objects:")
    print("="*60)
    
    for obj, info in available_objects.items():
        print(f"\n{obj}:")
        print(f"  Records: {info['record_count']}")
        print(f"  Key fields: {', '.join(info['important_fields'])}")
    
    # Save results to file
    output_file = 'revenue_cloud_objects_discovery.json'
    with open(output_file, 'w') as f:
        json.dump(available_objects, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()