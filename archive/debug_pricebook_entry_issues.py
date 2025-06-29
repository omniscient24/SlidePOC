#!/usr/bin/env python3
"""
Debug PricebookEntry upsert issues.
"""

import pandas as pd
import subprocess
import json
from pathlib import Path

class PricebookEntryDebugger:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        
    def check_current_pricebook_entries(self):
        """Check current PricebookEntry records in org."""
        print("=" * 60)
        print("CURRENT PRICEBOOKENTRY RECORDS IN ORG")
        print("=" * 60)
        
        query = """
        SELECT Id, Product2Id, Product2.Name, Product2.ProductCode,
               Pricebook2Id, Pricebook2.Name, 
               ProductSellingModelId, ProductSellingModel.Name,
               UnitPrice, IsActive
        FROM PricebookEntry
        ORDER BY Product2.Name
        LIMIT 10
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
                
                print(f"\nFound {data['result']['totalSize']} PricebookEntry records")
                print("\nSample records:")
                for rec in records[:5]:
                    print(f"\n- Product: {rec.get('Product2', {}).get('Name')} ({rec.get('Product2', {}).get('ProductCode')})")
                    print(f"  Pricebook: {rec.get('Pricebook2', {}).get('Name')}")
                    print(f"  Selling Model: {rec.get('ProductSellingModel', {}).get('Name') if rec.get('ProductSellingModel') else 'None'}")
                    print(f"  Unit Price: ${rec.get('UnitPrice')}")
                    print(f"  ID: {rec.get('Id')}")
    
    def check_excel_data(self):
        """Check what's in the Excel sheet."""
        print("\n" + "=" * 60)
        print("EXCEL SHEET DATA (20_PricebookEntry)")
        print("=" * 60)
        
        # Read the sheet
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        
        print(f"\nTotal rows in Excel: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Check for key fields
        print("\nData validation:")
        print(f"- Rows with Id: {df['Id'].notna().sum()}")
        print(f"- Rows with Product2Id: {df['Product2Id'].notna().sum()}")
        print(f"- Rows with Pricebook2Id: {df['Pricebook2Id'].notna().sum()}")
        print(f"- Rows with ProductSellingModelId: {df['ProductSellingModelId'].notna().sum()}")
        print(f"- Rows with UnitPrice: {df['UnitPrice'].notna().sum()}")
        
        # Show sample data
        print("\nFirst 3 rows:")
        for idx, row in df.head(3).iterrows():
            print(f"\nRow {idx + 2}:")
            print(f"  Id: {row.get('Id', 'None')}")
            print(f"  Product2Id: {row.get('Product2Id', 'None')}")
            print(f"  ProductSellingModelId: {row.get('ProductSellingModelId', 'None')}")
            print(f"  UnitPrice: {row.get('UnitPrice', 'None')}")
    
    def validate_references(self):
        """Validate that referenced records exist."""
        print("\n" + "=" * 60)
        print("VALIDATING REFERENCES")
        print("=" * 60)
        
        # Read Excel data
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Get unique Product2Ids from Excel
        product_ids = df['Product2Id'].dropna().unique()
        print(f"\nUnique Product2Ids in Excel: {len(product_ids)}")
        
        # Check if these products exist
        if len(product_ids) > 0:
            # Build query for products
            id_list = "', '".join(product_ids[:10])  # Check first 10
            query = f"SELECT Id, Name, ProductCode FROM Product2 WHERE Id IN ('{id_list}')"
            
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
                    print(f"\nProducts found in org: {len(found_products)}/{min(10, len(product_ids))}")
                    
                    # Check which IDs are missing
                    found_ids = [p['Id'] for p in found_products]
                    for prod_id in product_ids[:10]:
                        if prod_id not in found_ids:
                            print(f"  ⚠️ Product ID not found: {prod_id}")
        
        # Check ProductSellingModelOption requirements
        self.check_psmo_requirements()
    
    def check_psmo_requirements(self):
        """Check ProductSellingModelOption requirements."""
        print("\n" + "-" * 40)
        print("Checking ProductSellingModelOption requirements...")
        
        # Read Excel data
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Get unique combinations
        unique_combos = df[['Product2Id', 'ProductSellingModelId']].dropna().drop_duplicates()
        
        print(f"\nUnique Product-SellingModel combinations in Excel: {len(unique_combos)}")
        
        # Check a few combinations
        for idx, row in unique_combos.head(3).iterrows():
            prod_id = row['Product2Id']
            psm_id = row['ProductSellingModelId']
            
            # Check if PSMO exists
            query = f"""
            SELECT Id FROM ProductSellingModelOption 
            WHERE Product2Id = '{prod_id}' 
            AND ProductSellingModelId = '{psm_id}'
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
                if 'result' in data:
                    count = data['result']['totalSize']
                    if count == 0:
                        print(f"\n  ⚠️ Missing PSMO for:")
                        print(f"     Product2Id: {prod_id}")
                        print(f"     ProductSellingModelId: {psm_id}")
    
    def test_single_upsert(self):
        """Test upserting a single PricebookEntry."""
        print("\n" + "=" * 60)
        print("TESTING SINGLE PRICEBOOKENTRY UPSERT")
        print("=" * 60)
        
        # Read Excel data
        df = pd.read_excel(self.workbook_path, sheet_name='20_PricebookEntry')
        df.columns = df.columns.str.replace('*', '', regex=False)
        
        # Get first row with data
        test_row = df.iloc[0]
        
        print("\nTest record:")
        print(f"  Id: {test_row['Id']}")
        print(f"  Product2Id: {test_row['Product2Id']}")
        print(f"  Pricebook2Id: {test_row['Pricebook2Id']}")
        print(f"  ProductSellingModelId: {test_row['ProductSellingModelId']}")
        print(f"  UnitPrice: {test_row['UnitPrice']}")
        
        # Create test CSV
        test_df = pd.DataFrame([test_row])
        csv_file = Path('data/test_pbe.csv')
        test_df.to_csv(csv_file, index=False)
        
        # Try upsert
        cmd = [
            'sf', 'data', 'upsert', 'bulk',
            '--sobject', 'PricebookEntry',
            '--file', str(csv_file),
            '--external-id', 'Id',
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        print("\nAttempting upsert...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Upsert successful")
        else:
            print(f"✗ Upsert failed: {result.stderr}")
            
            # Get detailed error
            if '--job-id' in result.stderr:
                import re
                match = re.search(r'--job-id (\w+)', result.stderr)
                if match:
                    job_id = match.group(1)
                    self.get_job_errors(job_id)
        
        # Clean up
        csv_file.unlink()
    
    def get_job_errors(self, job_id):
        """Get detailed job errors."""
        print(f"\nGetting detailed errors for job {job_id}...")
        
        cmd = [
            'sf', 'data', 'bulk', 'results',
            '--job-id', job_id,
            '--target-org', self.target_org
        ]
        
        subprocess.run(cmd)
        
        # Check for failed records file
        failed_file = Path(f"{job_id}-failed-records.csv")
        if failed_file.exists():
            df = pd.read_csv(failed_file)
            print("\nError details:")
            for idx, row in df.iterrows():
                print(f"\n{row.get('sf__Error', 'Unknown error')}")
            
            # Clean up
            failed_file.unlink()
            success_file = Path(f"{job_id}-success-records.csv")
            if success_file.exists():
                success_file.unlink()

def main():
    debugger = PricebookEntryDebugger()
    
    # Check current state
    debugger.check_current_pricebook_entries()
    
    # Check Excel data
    debugger.check_excel_data()
    
    # Validate references
    debugger.validate_references()
    
    # Test single upsert
    debugger.test_single_upsert()

if __name__ == '__main__':
    main()