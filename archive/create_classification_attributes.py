#!/usr/bin/env python3
"""
Create ProductClassificationAttribute records and restore ProductAttributeDefinition.
"""

import pandas as pd
import subprocess
import json
import time

def create_classification_attributes():
    """Create ProductClassificationAttribute records first."""
    print("Creating ProductClassificationAttribute records...")
    
    # Read data
    df_pc = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='08_ProductClassification')
    df_pc.columns = df_pc.columns.str.replace('*', '', regex=False).str.strip()
    
    df_ad = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='09_AttributeDefinition')
    df_ad.columns = df_ad.columns.str.replace('*', '', regex=False).str.strip()
    
    # Use the "Product Attributes" classification for all attributes
    prod_attr_class = df_pc[df_pc['Code'] == 'PROD_ATTRS']['Id'].iloc[0]
    print(f"Using ProductClassification: Product Attributes ({prod_attr_class})")
    
    # Create records for each AttributeDefinition
    records = []
    for _, attr in df_ad.iterrows():
        records.append({
            'ProductClassificationId': prod_attr_class,
            'AttributeDefinitionId': attr['Id']
        })
    
    # Save to CSV
    df_pca = pd.DataFrame(records)
    df_pca.to_csv('data/product_classification_attributes.csv', index=False)
    
    print(f"Creating {len(records)} ProductClassificationAttribute records...")
    
    # Insert
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductClassificationAttribute',
        '--file', 'data/product_classification_attributes.csv',
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductClassificationAttribute records")
        return True
    else:
        print(f"✗ Failed: {result.stderr}")
        return False

def get_classification_attribute_mapping():
    """Get the mapping of AttributeDefinitionId to ProductClassificationAttributeId."""
    print("\nGetting ProductClassificationAttribute IDs...")
    
    query = "SELECT Id, AttributeDefinitionId FROM ProductClassificationAttribute"
    
    cmd = [
        'sf', 'data', 'query',
        '--query', query,
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    mapping = {}
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if 'result' in data and 'records' in data['result']:
            for rec in data['result']['records']:
                mapping[rec['AttributeDefinitionId']] = rec['Id']
    
    print(f"Found {len(mapping)} mappings")
    return mapping

def restore_product_attributes_with_classification():
    """Restore ProductAttributeDefinition with ProductClassificationAttributeId."""
    print("\nRestoring ProductAttributeDefinition records...")
    
    # Get the mapping
    pca_mapping = get_classification_attribute_mapping()
    
    if not pca_mapping:
        print("✗ No ProductClassificationAttribute mappings found")
        return False
    
    # Read the spreadsheet
    df = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='17_ProductAttributeDef')
    df.columns = df.columns.str.replace('*', '', regex=False).str.strip()
    
    # Add ProductClassificationAttributeId
    df['ProductClassificationAttributeId'] = df['AttributeDefinitionId'].map(pca_mapping)
    
    # Check for missing mappings
    missing = df[df['ProductClassificationAttributeId'].isna()]
    if len(missing) > 0:
        print(f"⚠️  WARNING: {len(missing)} records missing ProductClassificationAttributeId")
        print(missing[['Name', 'AttributeDefinitionId']])
    
    # Remove Id column for insert
    if 'Id' in df.columns:
        df = df.drop('Id', axis=1)
    
    # Save for insert
    df.to_csv('data/product_attributes_with_classification.csv', index=False)
    
    print(f"\nInserting {len(df)} ProductAttributeDefinition records...")
    
    # Insert
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductAttributeDefinition',
        '--file', 'data/product_attributes_with_classification.csv',
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully created ProductAttributeDefinition records with categories!")
        return True
    else:
        print(f"✗ Failed: {result.stderr}")
        # Check for specific errors
        if 'failed-records.csv' in result.stderr:
            import glob
            error_files = glob.glob('*failed-records.csv')
            if error_files:
                print(f"\nError details in: {error_files[0]}")
                with open(error_files[0], 'r') as f:
                    lines = f.readlines()[:3]
                    for line in lines:
                        print(f"  {line.strip()}")
        return False

def verify_final_state():
    """Verify the final state of category assignments."""
    print("\nVerifying final category assignments...")
    
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
            for rec in data['result']['records']:
                cat_id = rec.get('AttributeCategoryId', 'NULL')
                count = rec.get('count', 0)
                print(f"  - {cat_id}: {count} attributes")

def main():
    print("=" * 70)
    print("CREATING PRODUCT ATTRIBUTE RELATIONSHIPS")
    print("=" * 70)
    
    # Step 1: Create ProductClassificationAttribute records
    if not create_classification_attributes():
        print("\n✗ Failed to create ProductClassificationAttribute records")
        return
    
    time.sleep(2)
    
    # Step 2: Restore ProductAttributeDefinition with proper references
    if not restore_product_attributes_with_classification():
        print("\n✗ Failed to restore ProductAttributeDefinition records")
        return
    
    # Step 3: Verify
    verify_final_state()
    
    print("\n" + "=" * 70)
    print("✓ COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()