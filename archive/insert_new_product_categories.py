#\!/usr/bin/env python3
"""
Insert only the new ProductCategoryProduct records.
"""

import pandas as pd
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("INSERTING NEW PRODUCTCATEGORYPRODUCT RECORDS")
    print("=" * 60)
    
    # Read the sheet
    df = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='26_ProductCategoryProduct')
    
    # Clean column names
    df.columns = df.columns.str.strip().str.replace('*', '', regex=False)
    
    # Get only records without IDs (new records)
    new_records = df[df['Id'].isna()].copy()
    
    print(f"Found {len(new_records)} new records to insert")
    
    if len(new_records) == 0:
        print("No new records to insert")
        return
    
    # Keep only required fields for insert
    insert_df = new_records[['ProductCategoryId', 'ProductId']].copy()
    
    # Save to CSV
    csv_file = Path('data/new_product_categories.csv')
    insert_df.to_csv(csv_file, index=False)
    
    # Insert records
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductCategoryProduct',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    print("\nInserting new ProductCategoryProduct records...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully inserted new records")
        
        # Verify new count
        query = "SELECT COUNT() FROM ProductCategoryProduct"
        cmd_count = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', 'fortradp2',
            '--json'
        ]
        
        import json
        result_count = subprocess.run(cmd_count, capture_output=True, text=True)
        if result_count.returncode == 0:
            data = json.loads(result_count.stdout)
            count = data['result']['totalSize']
            print(f"\nTotal ProductCategoryProduct records now: {count}")
            print("(Was 8, should now be 19)")
    else:
        print(f"✗ Insert failed: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
