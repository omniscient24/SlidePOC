#!/usr/bin/env python3
"""
Run complete upsert process using the exported Excel file.
Converts Excel sheets to CSV and runs upsert in proper order.
"""

import pandas as pd
import subprocess
import os
from pathlib import Path
from datetime import datetime

class CompleteUpsertRunner:
    def __init__(self):
        # Use the original template file (which now contains the exported data)
        self.excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.csv_output_dir = Path('data/csv_upsert_output')
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define import order (dependencies first)
        self.pass1_objects = [
            ('01_CostBook', 'CostBook'),
            ('02_LegalEntity', 'LegalEntity'),
            ('03_TaxEngine', 'TaxEngine'),
            ('04_TaxPolicy', 'TaxPolicy'),
            ('05_TaxTreatment', 'TaxTreatment'),
            ('06_BillingPolicy', 'BillingPolicy'),
            ('07_BillingTreatment', 'BillingTreatment'),
            ('08_ProductClassification', 'ProductClassification'),
            ('09_AttributeDefinition', 'AttributeDefinition'),
            ('10_AttributeCategory', 'AttributeCategory'),
            ('11_ProductCatalog', 'ProductCatalog'),
            ('12_ProductCategory', 'ProductCategory'),
            ('15_ProductSellingModel', 'ProductSellingModel'),
            ('13_Product2', 'Product2'),
            ('19_Pricebook2', 'Pricebook2')
        ]
        
        self.pass2_objects = [
            ('14_ProductComponentGroup', 'ProductComponentGroup'),
            ('17_ProductAttributeDef', 'ProductAttributeDefinition'),
            ('20_PricebookEntry', 'PricebookEntry'),
            ('15_CostBookEntry', 'CostBookEntry'),
            ('21_PriceAdjustmentSchedule', 'PriceAdjustmentSchedule'),
            ('22_PriceAdjustmentTier', 'PriceAdjustmentTier'),
            ('23_AttributeBasedAdjRule', 'AttributeBasedAdjRule'),
            ('24_AttributeBasedAdj', 'AttributeBasedAdj'),
            ('25_ProductRelatedComponent', 'ProductRelatedComponent'),
            ('26_ProductCategoryProduct', 'ProductCategoryProduct')
        ]
    
    def excel_to_csv(self):
        """Convert Excel sheets to CSV files."""
        print(f"Converting Excel to CSV files...")
        print(f"Input: {self.excel_file}")
        print(f"Output directory: {self.csv_output_dir}\n")
        
        # Load Excel file
        xl_file = pd.ExcelFile(self.excel_file)
        
        # Convert each data sheet to CSV
        for sheet_name in xl_file.sheet_names:
            if sheet_name in ['Instructions', 'Picklist Values']:
                continue
                
            # Read sheet
            df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            # Remove empty rows
            df = df.dropna(how='all')
            
            # Save as CSV
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            df.to_csv(csv_file, index=False)
            print(f"Created: {csv_file.name} ({len(df)} records)")
    
    def run_upsert(self, object_name, csv_file, external_id_field='External_ID__c'):
        """Run upsert for a single object."""
        print(f"\nUpserting {object_name}...")
        
        # Check if file has data
        df = pd.read_csv(csv_file)
        if len(df) == 0:
            print(f"  No records to upsert")
            return True
            
        cmd = [
            'sf', 'data', 'upsert', 'bulk',
            '--sobject', object_name,
            '--file', str(csv_file),
            '--external-id', external_id_field,
            '--target-org', 'fortradp2',
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  Success! Output: {result.stdout.strip()}")
            return True
        else:
            print(f"  Error: {result.stderr}")
            # Try without external ID for standard objects
            if 'No such column' in result.stderr and external_id_field == 'External_ID__c':
                print(f"  Retrying with Id field...")
                cmd[6] = 'Id'  # Change external ID field
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  Success with Id field!")
                    return True
                else:
                    print(f"  Still failed: {result.stderr}")
            return False
    
    def run_complete_upsert(self):
        """Run the complete upsert process."""
        print("=" * 60)
        print("COMPLETE UPSERT PROCESS")
        print("=" * 60)
        
        # Step 1: Convert Excel to CSV
        print("\nSTEP 1: Converting Excel to CSV")
        print("-" * 40)
        self.excel_to_csv()
        
        # Step 2: Run Pass 1 upserts
        print("\n\nSTEP 2: Pass 1 - Base Objects")
        print("-" * 40)
        
        pass1_success = True
        for sheet_name, object_name in self.pass1_objects:
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            if csv_file.exists():
                success = self.run_upsert(object_name, csv_file)
                if not success:
                    pass1_success = False
                    print(f"  Warning: Failed to upsert {object_name}")
            else:
                print(f"\nSkipping {object_name} - no CSV file")
        
        # Step 3: Run Pass 2 upserts
        print("\n\nSTEP 3: Pass 2 - Dependent Objects")
        print("-" * 40)
        
        pass2_success = True
        for sheet_name, object_name in self.pass2_objects:
            csv_file = self.csv_output_dir / f"{sheet_name}.csv"
            if csv_file.exists():
                success = self.run_upsert(object_name, csv_file)
                if not success:
                    pass2_success = False
                    print(f"  Warning: Failed to upsert {object_name}")
            else:
                print(f"\nSkipping {object_name} - no CSV file")
        
        # Summary
        print("\n" + "=" * 60)
        print("UPSERT COMPLETE")
        print("=" * 60)
        print(f"Pass 1 Status: {'SUCCESS' if pass1_success else 'PARTIAL SUCCESS'}")
        print(f"Pass 2 Status: {'SUCCESS' if pass2_success else 'PARTIAL SUCCESS'}")
        
        if pass1_success and pass2_success:
            print("\nAll objects upserted successfully!")
        else:
            print("\nSome objects failed to upsert. Check the errors above.")
        
        print(f"\nCSV files saved in: {self.csv_output_dir}")

def main():
    runner = CompleteUpsertRunner()
    runner.run_complete_upsert()

if __name__ == '__main__':
    main()