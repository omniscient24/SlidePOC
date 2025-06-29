#!/usr/bin/env python3
"""
Restore ProductAttributeDefinition with existing ProductClassificationAttr references.
"""

import pandas as pd
import subprocess
import json

def get_existing_classification_attrs():
    """Get all existing ProductClassificationAttr records."""
    print("Getting existing ProductClassificationAttr records...")
    
    query = "SELECT Id, Name, AttributeDefinitionId FROM ProductClassificationAttr"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    mapping = {}
    existing_attrs = set()
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            for rec in data['result']['records']:
                mapping[rec['AttributeDefinitionId']] = rec['Id']
                existing_attrs.add(rec['AttributeDefinitionId'])
                print(f"  Found: {rec['Name']} -> {rec['Id']}")
    
    return mapping, existing_attrs

def create_missing_classification_attrs(missing_attrs):
    """Create ProductClassificationAttr records for missing attributes."""
    if not missing_attrs:
        return {}
    
    print(f"\nCreating {len(missing_attrs)} missing ProductClassificationAttr records...")
    
    # Get ProductClassification ID
    df_pc = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='08_ProductClassification')
    df_pc.columns = df_pc.columns.str.replace('*', '', regex=False).str.strip()
    prod_attr_class = df_pc[df_pc['Code'] == 'PROD_ATTRS']['Id'].iloc[0]
    
    # Get AttributeDefinition details
    df_ad = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='09_AttributeDefinition')
    df_ad.columns = df_ad.columns.str.replace('*', '', regex=False).str.strip()
    
    # Create records for missing attributes
    records = []
    for attr_id in missing_attrs:
        attr_row = df_ad[df_ad['Id'] == attr_id]
        if not attr_row.empty:
            records.append({
                'Name': attr_row['Name'].iloc[0],
                'ProductClassificationId': prod_attr_class,
                'AttributeDefinitionId': attr_id
            })
    
    if not records:
        return {}
    
    # Save to CSV
    df_new = pd.DataFrame(records)
    df_new.to_csv('data/new_classification_attrs.csv', index=False)
    
    # Insert
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductClassificationAttr',
        '--file', 'data/new_classification_attrs.csv',
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created missing ProductClassificationAttr records")
        # Get the new mappings
        return get_existing_classification_attrs()[0]
    else:
        print(f"✗ Failed: {result.stderr}")
        return {}

def restore_product_attributes():
    """Restore ProductAttributeDefinition with proper references."""
    print("\n\nRestoring ProductAttributeDefinition records...")
    
    # Get existing mappings
    mapping, existing_attrs = get_existing_classification_attrs()
    
    # Read ProductAttributeDef data
    df = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='17_ProductAttributeDef')
    df.columns = df.columns.str.replace('*', '', regex=False).str.strip()
    
    # Find missing attributes
    all_attr_ids = set(df['AttributeDefinitionId'].unique())
    missing_attrs = all_attr_ids - existing_attrs
    
    if missing_attrs:
        print(f"\nFound {len(missing_attrs)} attributes without ProductClassificationAttr records")
        # Create missing records
        new_mapping = create_missing_classification_attrs(missing_attrs)
        mapping.update(new_mapping)
    
    # Add ProductClassificationAttributeId
    df['ProductClassificationAttributeId'] = df['AttributeDefinitionId'].map(mapping)
    
    # Check for any still missing
    missing = df[df['ProductClassificationAttributeId'].isna()]
    if len(missing) > 0:
        print(f"\n⚠️  WARNING: {len(missing)} records still missing ProductClassificationAttributeId")
        print(missing[['Name', 'AttributeDefinitionId']])
        return False
    
    # Remove Id column for insert
    if 'Id' in df.columns:
        df = df.drop('Id', axis=1)
    
    # Save for insert
    df.to_csv('data/product_attributes_final.csv', index=False)
    
    print(f"\nInserting {len(df)} ProductAttributeDefinition records...")
    
    # Insert
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductAttributeDefinition',
        '--file', 'data/product_attributes_final.csv',
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductAttributeDefinition records!")
        return True
    else:
        print(f"✗ Failed: {result.stderr}")
        return False

def verify_categories():
    """Verify that categories were assigned."""
    print("\n\nVerifying AttributeCategory assignments...")
    
    query = """
    SELECT AttributeCategoryId, COUNT(Id) count
    FROM ProductAttributeDefinition
    GROUP BY AttributeCategoryId
    """
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            print("\nFinal AttributeCategory distribution:")
            total_with_category = 0
            for rec in data['result']['records']:
                cat_id = rec.get('AttributeCategoryId')
                count = rec.get('count', 0)
                if cat_id:
                    print(f"  - {cat_id}: {count} attributes")
                    total_with_category += count
                else:
                    print(f"  - NULL: {count} attributes")
            
            if total_with_category > 0:
                print(f"\n✓ SUCCESS: {total_with_category} attributes have categories assigned!")
            else:
                print("\n⚠️  WARNING: No attributes have categories assigned")

def main():
    print("=" * 70)
    print("RESTORING PRODUCT ATTRIBUTES WITH CATEGORIES")
    print("=" * 70)
    
    if restore_product_attributes():
        verify_categories()
        
        print("\n" + "=" * 70)
        print("✓ RESTORATION COMPLETE")
        print("=" * 70)
        
        # Update spreadsheet
        print("\nUpdating spreadsheet with new IDs...")
        subprocess.run(['python3', 'export_to_same_template.py'], 
                      capture_output=True, text=True)
        print("✓ Spreadsheet updated")

if __name__ == '__main__':
    main()