#!/usr/bin/env python3
"""
Investigate PricebookEntry sheet to understand why records aren't inserting.
"""

import pandas as pd
import subprocess
import json
from pathlib import Path

class PricebookEntryInvestigator:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        
    def analyze_sheet_data(self):
        """Analyze the PricebookEntry sheet data."""
        print("=" * 60)
        print("PRICEBOOKENTRY SHEET ANALYSIS")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        
        print(f"\nSheet contains {len(df)} total rows")
        print(f"Columns: {list(df.columns)}")
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Analyze ID patterns
        print("\n" + "-" * 40)
        print("ID Analysis:")
        
        # Check for records with and without IDs
        has_id = df[df['Id'].notna()]
        no_id = df[df['Id'].isna()]
        
        print(f"- Records with existing IDs: {len(has_id)}")
        print(f"- Records without IDs (new): {len(no_id)}")
        
        # Show new records that should be inserted
        if len(no_id) > 0:
            print("\nNEW RECORDS (without IDs) that should be inserted:")
            for idx, row in no_id.iterrows():
                print(f"\nRow {idx + 2}:")
                print(f"  Product2Id: {row.get('Product2Id', 'None')}")
                print(f"  Pricebook2Id: {row.get('Pricebook2Id', 'None')}")
                print(f"  ProductSellingModelId: {row.get('ProductSellingModelId', 'None')}")
                print(f"  UnitPrice: {row.get('UnitPrice', 'None')}")
                if 'Product2.Name' in df.columns:
                    print(f"  Product Name: {row.get('Product2.Name', 'None')}")
        
        return df
    
    def check_current_state(self):
        """Check current PricebookEntry records in org."""
        print("\n" + "=" * 60)
        print("CURRENT PRICEBOOKENTRY RECORDS IN ORG")
        print("=" * 60)
        
        query = """
        SELECT Id, Product2Id, Product2.Name, Product2.ProductCode,
               Pricebook2Id, ProductSellingModelId, UnitPrice
        FROM PricebookEntry
        ORDER BY Product2.Name
        """
        
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
                
                print(f"\nTotal PricebookEntry records in org: {data['result']['totalSize']}")
                
                # Create a set of existing product IDs
                existing_product_ids = {rec['Product2Id'] for rec in records}
                
                return existing_product_ids
        
        return set()
    
    def identify_missing_entries(self, df, existing_product_ids):
        """Identify which entries are missing from the org."""
        print("\n" + "=" * 60)
        print("MISSING PRICEBOOKENTRY ANALYSIS")
        print("=" * 60)
        
        # Check which products in the sheet don't have PBE in org
        missing_entries = []
        
        for idx, row in df.iterrows():
            product_id = row.get('Product2Id')
            if pd.notna(product_id) and product_id not in existing_product_ids:
                missing_entries.append(row)
        
        print(f"\nProducts in sheet without PricebookEntry in org: {len(missing_entries)}")
        
        if missing_entries:
            print("\nMissing entries (first 5):")
            for i, row in enumerate(missing_entries[:5]):
                print(f"\n{i+1}. Product2Id: {row.get('Product2Id')}")
                if 'Product2.Name' in df.columns:
                    print(f"   Product Name: {row.get('Product2.Name', 'Unknown')}")
                print(f"   ProductSellingModelId: {row.get('ProductSellingModelId', 'None')}")
                print(f"   UnitPrice: {row.get('UnitPrice', 'None')}")
        
        return missing_entries
    
    def check_product_references(self, missing_entries):
        """Check if the referenced products exist."""
        print("\n" + "=" * 60)
        print("VALIDATING PRODUCT REFERENCES")
        print("=" * 60)
        
        if not missing_entries:
            print("No missing entries to validate")
            return
        
        # Get unique product IDs
        product_ids = list({row['Product2Id'] for row in missing_entries if pd.notna(row.get('Product2Id'))})
        
        if product_ids:
            # Check first few products
            check_ids = product_ids[:5]
            id_list = "', '".join(check_ids)
            
            query = f"SELECT Id, Name, ProductCode, Type FROM Product2 WHERE Id IN ('{id_list}')"
            
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
                    found_products = data['result']['records']
                    
                    print(f"\nProducts found: {len(found_products)}/{len(check_ids)}")
                    
                    # Show which products exist
                    found_ids = {p['Id'] for p in found_products}
                    for pid in check_ids:
                        if pid in found_ids:
                            prod = next(p for p in found_products if p['Id'] == pid)
                            print(f"  ✓ {prod['Name']} ({prod['ProductCode']}) - Type: {prod.get('Type', 'None')}")
                        else:
                            print(f"  ✗ Product ID not found: {pid}")
    
    def test_insert_new_entries(self):
        """Test inserting only the new entries."""
        print("\n" + "=" * 60)
        print("TESTING NEW ENTRY INSERT")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Get only records without IDs (new records)
        new_records = df[df['Id'].isna()].copy()
        
        if len(new_records) == 0:
            print("No new records to insert (all records have IDs)")
            
            # Check if there are bundle products without entries
            self.check_bundle_products_without_entries()
            return
        
        # Remove non-field columns
        valid_fields = ['Product2Id', 'Pricebook2Id', 'ProductSellingModelId', 'UnitPrice', 'IsActive']
        
        # Keep only valid fields
        insert_df = new_records[valid_fields].copy()
        
        # Remove rows with missing required fields
        insert_df = insert_df.dropna(subset=['Product2Id', 'Pricebook2Id', 'UnitPrice'])
        
        print(f"\nPreparing to insert {len(insert_df)} new PricebookEntry records")
        
        if len(insert_df) > 0:
            # Save to CSV
            csv_file = Path('data/new_pricebook_entries.csv')
            insert_df.to_csv(csv_file, index=False)
            
            # Try insert
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', 'PricebookEntry',
                '--file', str(csv_file),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            print("\nInserting new entries...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Successfully inserted new PricebookEntry records")
            else:
                print(f"✗ Insert failed: {result.stderr}")
            
            # Clean up
            csv_file.unlink()
    
    def check_bundle_products_without_entries(self):
        """Check if bundle products have PricebookEntry records."""
        print("\n" + "-" * 40)
        print("Checking Bundle Products...")
        
        query = """
        SELECT p.Id, p.Name, p.ProductCode, p.Type,
               (SELECT Id FROM PricebookEntries LIMIT 1) 
        FROM Product2 p
        WHERE p.Type = 'Bundle'
        ORDER BY p.Name
        """
        
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
                bundles = data['result']['records']
                
                print(f"\nBundle products: {len(bundles)}")
                for bundle in bundles:
                    has_pbe = bundle.get('PricebookEntries') is not None
                    status = "✓ Has PBE" if has_pbe else "✗ No PBE"
                    print(f"  - {bundle['Name']} ({bundle['ProductCode']}): {status}")

def main():
    investigator = PricebookEntryInvestigator()
    
    # Analyze sheet data
    df = investigator.analyze_sheet_data()
    
    # Check current state
    existing_ids = investigator.check_current_state()
    
    # Identify missing entries
    missing = investigator.identify_missing_entries(df, existing_ids)
    
    # Validate references
    investigator.check_product_references(missing)
    
    # Test insert
    investigator.test_insert_new_entries()

if __name__ == '__main__':
    main()