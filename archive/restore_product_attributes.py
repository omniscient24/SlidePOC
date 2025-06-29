#!/usr/bin/env python3
"""
Restore ProductAttributeDefinition records from backup.
"""

import subprocess
import pandas as pd

def main():
    print("Restoring ProductAttributeDefinition records from backup...")
    
    # Read backup file
    df = pd.read_csv('data/product_attributes_backup.csv')
    
    # Remove Id column for insert
    df_insert = df.drop('Id', axis=1)
    
    # Save for insert
    df_insert.to_csv('data/restore_attributes.csv', index=False)
    
    print(f"Restoring {len(df)} records...")
    
    # Bulk insert
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductAttributeDefinition',
        '--file', 'data/restore_attributes.csv',
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully restored records")
    else:
        print(f"✗ Restore failed: {result.stderr}")

if __name__ == '__main__':
    main()