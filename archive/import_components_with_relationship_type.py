#\!/usr/bin/env python3
"""
Import ProductRelatedComponent records with ProductRelationshipTypeId.
"""

import pandas as pd
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("IMPORTING PRODUCTRELATEDCOMPONENT WITH RELATIONSHIP TYPE")
    print("=" * 60)
    
    # Read the original CSV
    df = pd.read_csv('data/product_related_components.csv')
    
    # Remove the Name field (read-only)
    if 'Name' in df.columns:
        df = df.drop('Name', axis=1)
    
    # Add ProductRelationshipTypeId
    # Using "Bundle to Product Classification Component Relationship"
    df['ProductRelationshipTypeId'] = '0yoa5000000gTs1AAE'
    
    print(f"Fields to import: {list(df.columns)}")
    print(f"Records to import: {len(df)}")
    
    # Save updated CSV
    csv_file = Path('data/product_components_with_type.csv')
    df.to_csv(csv_file, index=False)
    
    # Import records
    cmd = [
        'sf', 'data', 'import', 'bulk',
        '--sobject', 'ProductRelatedComponent',
        '--file', str(csv_file),
        '--target-org', 'fortradp2',
        '--wait', '10'
    ]
    
    print("\nImporting ProductRelatedComponent records...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Successfully imported ProductRelatedComponent records")
        
        # Verify and show results
        import json
        
        # Count query
        query_count = "SELECT COUNT() FROM ProductRelatedComponent"
        cmd_count = [
            'sf', 'data', 'query',
            '--query', query_count,
            '--target-org', 'fortradp2',
            '--json'
        ]
        
        result_count = subprocess.run(cmd_count, capture_output=True, text=True)
        if result_count.returncode == 0:
            data = json.loads(result_count.stdout)
            count = data['result']['totalSize']
            print(f"\nTotal ProductRelatedComponent records: {count}")
        
        # Show bundle structure
        print("\n" + "-" * 80)
        print("BUNDLE COMPONENT STRUCTURE:")
        print("-" * 80)
        
        query_structure = """
        SELECT Parent.Name, Parent.ProductCode,
               Child.Name, Child.ProductCode,
               Quantity, IsComponentRequired
        FROM ProductRelatedComponent
        ORDER BY Parent.Name, Sequence
        LIMIT 20
        """
        
        cmd_show = [
            'sf', 'data', 'query',
            '--query', query_structure,
            '--target-org', 'fortradp2'
        ]
        
        subprocess.run(cmd_show)
        
    else:
        print(f"✗ Import failed: {result.stderr}")
    
    # Clean up
    csv_file.unlink()

if __name__ == '__main__':
    main()
