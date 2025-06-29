#!/usr/bin/env python3
"""
Create ProductSellingModelOption records to link Products with ProductSellingModels.
This is required before we can create PricebookEntry records.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

class ProductSellingModelOptionCreator:
    def __init__(self):
        self.target_org = 'fortradp2'
        
    def analyze_requirements(self):
        """Analyze what ProductSellingModelOptions we need."""
        print("=" * 60)
        print("ANALYZING PRODUCTSELLINGMODELOPTION REQUIREMENTS")
        print("=" * 60)
        
        # Read PricebookEntry data to see what combinations we need
        pbe_df = pd.read_csv('data/csv_final_output/20_PricebookEntry.csv')
        
        # Get unique Product-SellingModel combinations
        if 'ProductSellingModelId' in pbe_df.columns:
            # Group by Product and SellingModel
            combinations = pbe_df[['Product2Id', 'ProductSellingModelId']].drop_duplicates()
            print(f"\nUnique Product-SellingModel combinations needed: {len(combinations)}")
            
            # Get selling model info
            selling_models = combinations['ProductSellingModelId'].unique()
            print(f"Unique ProductSellingModels referenced: {len(selling_models)}")
            
            # Check if these selling models exist
            for psm_id in selling_models[:3]:  # Check first 3
                cmd = [
                    'sf', 'data', 'query',
                    '--query', f"SELECT Id, Name, SellingModelType FROM ProductSellingModel WHERE Id = '{psm_id}'",
                    '--target-org', self.target_org,
                    '--json'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data['result']['totalSize'] > 0:
                        rec = data['result']['records'][0]
                        print(f"\n  {psm_id}:")
                        print(f"    Name: {rec.get('Name')}")
                        print(f"    Type: {rec.get('SellingModelType')}")
            
            return combinations
        else:
            print("No ProductSellingModelId found in PricebookEntry data")
            return pd.DataFrame()
    
    def create_selling_model_options(self, combinations):
        """Create ProductSellingModelOption records."""
        if len(combinations) == 0:
            print("\nNo ProductSellingModelOptions to create")
            return
            
        print(f"\n\nCREATING {len(combinations)} PRODUCTSELLINGMODELOPTIONS")
        print("=" * 60)
        
        # Prepare data for import
        psmo_data = []
        
        for idx, (_, row) in enumerate(combinations.iterrows()):
            psmo_data.append({
                'Product2Id': row['Product2Id'],
                'ProductSellingModelId': row['ProductSellingModelId']
                # Note: Name is auto-generated, IsDefault might have specific logic
            })
        
        # Save to CSV
        psmo_df = pd.DataFrame(psmo_data)
        psmo_file = Path('data/ProductSellingModelOption.csv')
        psmo_df.to_csv(psmo_file, index=False)
        
        print(f"\nImporting {len(psmo_df)} ProductSellingModelOption records...")
        
        # Import
        cmd = [
            'sf', 'data', 'import', 'bulk',
            '--sobject', 'ProductSellingModelOption',
            '--file', str(psmo_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Successfully created ProductSellingModelOptions!")
            
            # Now try PricebookEntry import again
            self.retry_pricebook_entry()
        else:
            print("  ✗ Failed to create ProductSellingModelOptions")
            if 'job-id' in result.stderr:
                print(f"  Check job details: {result.stderr}")
    
    def retry_pricebook_entry(self):
        """Retry PricebookEntry import after creating ProductSellingModelOptions."""
        print("\n\nRETRYING PRICEBOOKENTRY IMPORT")
        print("=" * 60)
        
        pbe_file = Path('data/csv_final_output/20_PricebookEntry.csv')
        
        cmd = [
            'sf', 'data', 'import', 'bulk',
            '--sobject', 'PricebookEntry',
            '--file', str(pbe_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Successfully imported PricebookEntry records!")
        else:
            print("  ✗ PricebookEntry import still failed")
            print("  This might require additional configuration")

def main():
    creator = ProductSellingModelOptionCreator()
    combinations = creator.analyze_requirements()
    
    if len(combinations) > 0:
        creator.create_selling_model_options(combinations)
    else:
        print("\nNo ProductSellingModelOption data found to create")

if __name__ == '__main__':
    main()