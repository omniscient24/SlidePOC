#!/usr/bin/env python3
"""
Fix CSV files by removing fields that don't exist in Salesforce.
"""

import pandas as pd
from pathlib import Path

class CSVFieldFixer:
    def __init__(self):
        self.csv_dir = Path('data/csv_clean_output')
        self.fixed_dir = Path('data/csv_fixed_output')
        self.fixed_dir.mkdir(parents=True, exist_ok=True)
        
        # Fields to remove per object
        self.fields_to_remove = {
            'Product2': ['IsSerialized', 'ProductClass', 'IsPriceEditable', 'ExcludeFromSitemap', 
                        'QuantityInstallmentPeriod', 'NumberOfQuantityInstallments', 
                        'QuantityInstallmentType', 'BillingPolicyId', 'CanUseQuantitySchedule',
                        'CanUseRevenueSchedule', 'ConnectionReceivedId', 'ConnectionSentId',
                        'ModelCode__c', 'External_ID__c', 'LegalEntityId', 'TaxPolicyId',
                        'ProductClassId', 'ProductSellingModelId'],
            'ProductCategoryProduct': ['External_ID__c', 'Name'],
            'ProductRelatedComponent': ['External_ID__c', 'Name', 'ProductRelationshipTypeId', 
                                      'IsDefaultComponent', 'ProductComponentGroupId',
                                      'DoesBundlePriceIncludeChild'],
            'PricebookEntry': ['External_ID__c', 'Name'],
            'AttributeDefinition': ['Type', 'MinimumCharacterLength', 'MaximumCharacterLength',
                                  'MinimumNumberValue', 'MaximumNumberValue', 'PicklistId',
                                  'Unit', 'HelpText', 'External_ID__c'],
            'AttributeCategory': ['External_ID__c'],
            'ProductSellingModel': ['External_ID__c'],
            'Pricebook2': ['External_ID__c', 'ExternalId__c', 'IsArchived']
        }
    
    def fix_csv_files(self):
        """Remove non-existent fields from CSV files."""
        print("Fixing CSV files...")
        print(f"Input: {self.csv_dir}")
        print(f"Output: {self.fixed_dir}\n")
        
        # Map sheet names to object names
        sheet_to_object = {
            '13_Product2.csv': 'Product2',
            '26_ProductCategoryProduct.csv': 'ProductCategoryProduct',
            '25_ProductRelatedComponent.csv': 'ProductRelatedComponent',
            '20_PricebookEntry.csv': 'PricebookEntry',
            '09_AttributeDefinition.csv': 'AttributeDefinition',
            '10_AttributeCategory.csv': 'AttributeCategory',
            '15_ProductSellingModel.csv': 'ProductSellingModel',
            '19_Pricebook2.csv': 'Pricebook2'
        }
        
        # Process each CSV file
        for csv_file in self.csv_dir.glob('*.csv'):
            object_name = sheet_to_object.get(csv_file.name)
            
            if object_name and object_name in self.fields_to_remove:
                print(f"Processing {csv_file.name}...")
                
                # Read CSV
                df = pd.read_csv(csv_file)
                original_cols = df.columns.tolist()
                
                # Remove fields
                fields_to_drop = []
                for field in self.fields_to_remove[object_name]:
                    if field in df.columns:
                        fields_to_drop.append(field)
                        print(f"  - Removing field: {field}")
                
                if fields_to_drop:
                    df = df.drop(columns=fields_to_drop)
                
                # Save fixed CSV
                output_file = self.fixed_dir / csv_file.name
                df.to_csv(output_file, index=False)
                print(f"  ✓ Saved fixed file with {len(df.columns)} columns (removed {len(fields_to_drop)})")
            else:
                # Just copy the file
                import shutil
                shutil.copy2(csv_file, self.fixed_dir / csv_file.name)
                print(f"Copied {csv_file.name} (no changes needed)")
        
        print("\nAll CSV files fixed!")

def main():
    fixer = CSVFieldFixer()
    fixer.fix_csv_files()

if __name__ == '__main__':
    main()