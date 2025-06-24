#!/usr/bin/env python3
"""
Add External ID values from Excel to CSV files for proper upsert.
"""

import pandas as pd
from pathlib import Path

class ExternalIdMapper:
    def __init__(self):
        self.excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.csv_dir = Path('data/csv_final_output')
        self.output_dir = Path('data/csv_with_external_ids')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def add_external_ids(self):
        """Add External ID values from Excel to CSV files."""
        print("=" * 60)
        print("ADDING EXTERNAL IDS FROM EXCEL TO CSV FILES")
        print("=" * 60)
        
        # Define the mapping of sheets to CSV files and External ID fields
        mappings = [
            # Sheet name, CSV file, Excel External ID column, Salesforce field
            ('13_Product2', '13_Product2.csv', 'External_ID__c', 'ExternalId'),
            ('12_ProductCategory', '12_ProductCategory.csv', 'External_ID__c', 'ExternalId__c'),
            ('09_AttributeDefinition', '09_AttributeDefinition.csv', 'External_ID__c', 'Code'),
            ('10_AttributeCategory', '10_AttributeCategory.csv', 'External_ID__c', None),
            ('15_ProductSellingModel', '15_ProductSellingModel.csv', 'External_ID__c', None),
            ('19_Pricebook2', '19_Pricebook2.csv', 'External_ID__c', None),
            ('26_ProductCategoryProduct', '26_ProductCategoryProduct.csv', 'External_ID__c', None),
            ('25_ProductRelatedComponent', '25_ProductRelatedComponent.csv', 'External_ID__c', None),
        ]
        
        for sheet_name, csv_file, excel_col, sf_field in mappings:
            print(f"\n{sheet_name}:")
            
            # Read Excel sheet
            try:
                excel_df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            except:
                print(f"  ⚠️  Sheet not found in Excel")
                continue
            
            # Read CSV file
            csv_path = self.csv_dir / csv_file
            if not csv_path.exists():
                print(f"  ⚠️  CSV file not found")
                continue
                
            csv_df = pd.read_csv(csv_path)
            
            # Check if External ID column exists in Excel
            if excel_col not in excel_df.columns:
                print(f"  - No {excel_col} column in Excel")
                # Copy file as-is
                csv_df.to_csv(self.output_dir / csv_file, index=False)
                continue
            
            # Get External ID values from Excel
            external_ids = excel_df[excel_col]
            non_empty = external_ids.notna().sum()
            
            if non_empty > 0:
                print(f"  - Found {non_empty} External ID values in Excel")
                
                # Add External ID column to CSV
                if sf_field:
                    # Use the Salesforce field name
                    csv_df[sf_field] = external_ids[:len(csv_df)]
                    print(f"  - Added {sf_field} column to CSV")
                else:
                    # Keep the original column name for reference
                    csv_df['External_ID__c'] = external_ids[:len(csv_df)]
                    print(f"  - Added External_ID__c column to CSV")
                
                # For Product2, also populate ProductCode if empty
                if sheet_name == '13_Product2' and 'ProductCode' in csv_df.columns:
                    empty_codes = csv_df['ProductCode'].isna()
                    if empty_codes.any():
                        # Use External ID values for empty ProductCodes
                        csv_df.loc[empty_codes, 'ProductCode'] = csv_df.loc[empty_codes, 'ExternalId']
                        print(f"  - Populated {empty_codes.sum()} empty ProductCode values")
                
                # For AttributeDefinition, ensure Code is populated
                if sheet_name == '09_AttributeDefinition' and sf_field == 'Code':
                    empty_codes = csv_df['Code'].isna()
                    if empty_codes.any() and 'Name' in csv_df.columns:
                        # Generate Code from Name
                        csv_df.loc[empty_codes, 'Code'] = csv_df.loc[empty_codes, 'Name'].str.upper().str.replace(' ', '_')
                        print(f"  - Generated {empty_codes.sum()} Code values from Name")
            else:
                print(f"  - No External ID values in Excel")
            
            # Save updated CSV
            csv_df.to_csv(self.output_dir / csv_file, index=False)
            print(f"  ✓ Saved to {self.output_dir / csv_file}")
        
        # Copy files that don't need External IDs
        other_files = ['11_ProductCatalog.csv', '08_ProductClassification.csv', 
                      '17_ProductAttributeDef.csv', '20_PricebookEntry.csv']
        
        print("\nCopying other files:")
        for file in other_files:
            src = self.csv_dir / file
            if src.exists():
                import shutil
                shutil.copy2(src, self.output_dir / file)
                print(f"  - Copied {file}")
        
        print(f"\n✓ All files processed and saved to: {self.output_dir}")

def main():
    mapper = ExternalIdMapper()
    mapper.add_external_ids()

if __name__ == '__main__':
    main()