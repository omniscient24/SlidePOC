#!/usr/bin/env python3
"""
Export core Revenue Cloud objects from Salesforce and populate the template.
"""

import pandas as pd
import subprocess
import json
from pathlib import Path
from datetime import datetime
import os

class CoreObjectExporter:
    def __init__(self):
        self.template_file = Path('data/Revenue_Cloud_Clean_Template.xlsx')
        self.output_file = Path(f'data/Revenue_Cloud_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        self.target_org = 'fortradp2'
        
        # Core objects with known fields
        self.core_queries = {
            'ProductCatalog': "SELECT Id, Name, Code FROM ProductCatalog",
            'ProductCategory': "SELECT Id, Name, Code, CatalogId, ParentCategoryId FROM ProductCategory",
            'Product2': "SELECT Id, Name, ProductCode, Description, Family, Type, BasedOnId, IsActive FROM Product2",
            'AttributeDefinition': "SELECT Id, Name, Code, Label FROM AttributeDefinition",
            'ProductClassification': "SELECT Id, Name, Code, Status FROM ProductClassification",
            'ProductClassificationAttr': "SELECT Id, Name, ProductClassificationId, AttributeDefinitionId, Status FROM ProductClassificationAttr",
            'Pricebook2': "SELECT Id, Name, Description, IsActive, IsStandard FROM Pricebook2",
            'PricebookEntry': "SELECT Id, Product2Id, Pricebook2Id, UnitPrice, IsActive FROM PricebookEntry WHERE IsActive = true",
            'ProductCategoryProduct': "SELECT Id, ProductCategoryId, ProductId FROM ProductCategoryProduct",
            'ProductAttributeDefinition': "SELECT Id, Name, Product2Id, ProductClassificationAttributeId, AttributeDefinitionId, Status FROM ProductAttributeDefinition",
            'ProductSellingModel': "SELECT Id, Name, SellingModelType, Status, PricingTermUnit, PricingTerm FROM ProductSellingModel",
            'ProductRelatedComponent': "SELECT Id, ParentProductId, ChildProductId, ProductRelationshipTypeId, Quantity, IsDefaultComponent, Sequence FROM ProductRelatedComponent",
            'ProductRelationshipType': "SELECT Id, Name FROM ProductRelationshipType"
        }
    
    def query_salesforce_simple(self, query):
        """Execute a simple query and return results."""
        try:
            cmd = [
                'sf', 'data', 'query',
                '--query', query,
                '--target-org', self.target_org,
                '--result-format', 'csv'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse CSV output
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Has header and at least one data row
                    # Remove the status line if present
                    data_lines = [line for line in lines if not line.startswith('Total number of records') and line.strip()]
                    if data_lines:
                        import io
                        import csv
                        csv_data = '\n'.join(data_lines)
                        reader = csv.DictReader(io.StringIO(csv_data))
                        return list(reader)
                return []
            else:
                print(f"Error: {result.stderr}")
                return []
        except Exception as e:
            print(f"Exception: {str(e)}")
            return []
    
    def export_and_populate(self):
        """Export data and populate the template."""
        print(f"Starting core object export from org: {self.target_org}")
        print(f"Output: {self.output_file}\n")
        
        # Load template
        xl_file = pd.ExcelFile(self.template_file)
        all_sheets = {}
        
        # First, query all core objects
        exported_data = {}
        for obj_name, query in self.core_queries.items():
            print(f"Querying {obj_name}...")
            data = self.query_salesforce_simple(query)
            if data:
                print(f"  Found {len(data)} records")
                exported_data[obj_name] = data
            else:
                print(f"  No records found")
                exported_data[obj_name] = []
        
        print("\nPopulating template sheets...")
        
        # Map data to template sheets
        sheet_mappings = {
            '11_ProductCatalog': 'ProductCatalog',
            '12_ProductCategory': 'ProductCategory',
            '13_Product2': 'Product2',
            '09_AttributeDefinition': 'AttributeDefinition',
            '08_ProductClassification': 'ProductClassification',
            '19_Pricebook2': 'Pricebook2',
            '20_PricebookEntry': 'PricebookEntry',
            '26_ProductCategoryProduct': 'ProductCategoryProduct',
            '17_ProductAttributeDef': 'ProductAttributeDefinition',
            '15_ProductSellingModel': 'ProductSellingModel',
            '25_ProductRelatedComponent': 'ProductRelatedComponent'
        }
        
        # Process each sheet
        for sheet_name in xl_file.sheet_names:
            # Read template sheet
            template_df = pd.read_excel(self.template_file, sheet_name=sheet_name)
            
            if sheet_name in sheet_mappings and sheet_mappings[sheet_name] in exported_data:
                object_name = sheet_mappings[sheet_name]
                data = exported_data[object_name]
                
                if data:
                    print(f"Populating {sheet_name} with {len(data)} records from {object_name}")
                    
                    # Create DataFrame from data
                    data_df = pd.DataFrame(data)
                    
                    # Map columns - keep template structure
                    new_df = pd.DataFrame(columns=template_df.columns)
                    
                    # Map available columns
                    for col in template_df.columns:
                        clean_col = col.replace('*', '')
                        if clean_col in data_df.columns:
                            new_df[col] = data_df[clean_col].values[:len(data_df)]
                        elif col == 'External_ID__c':
                            # Generate external IDs
                            new_df[col] = [f"{sheet_name}_{i+1}" for i in range(len(data_df))]
                        elif col == 'Name' and 'Name' not in data_df.columns and 'Id' in data_df.columns:
                            # Use ID as name if no name field
                            new_df[col] = data_df['Id'].values[:len(data_df)]
                    
                    # Fill missing required columns with placeholders
                    for col in template_df.columns:
                        if col not in new_df.columns or new_df[col].isna().all():
                            if 'Id' in col and col != 'Id':
                                new_df[col] = 'ID_PLACEHOLDER'
                            elif col in ['IsActive', 'IsRequired', 'IsHidden']:
                                new_df[col] = True
                            elif col in ['Sequence', 'MinQuantity', 'MaxQuantity']:
                                new_df[col] = 0
                            elif col == 'Quantity':
                                new_df[col] = 1
                    
                    all_sheets[sheet_name] = new_df
                else:
                    # Keep template structure with one example row
                    all_sheets[sheet_name] = template_df.head(1)
            else:
                # Keep original template
                all_sheets[sheet_name] = template_df
        
        # Write output
        print(f"\nWriting output to: {self.output_file}")
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("\nExport completed!")
        print(f"You can now edit the file: {self.output_file}")
        print("After editing, use the file for upsert operations.")
        
        return self.output_file

def main():
    exporter = CoreObjectExporter()
    exporter.export_and_populate()

if __name__ == '__main__':
    main()