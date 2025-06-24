#!/usr/bin/env python3
"""
Export data from Salesforce target org and populate the Revenue Cloud template.
"""

import pandas as pd
import subprocess
import json
import csv
from pathlib import Path
from datetime import datetime

class SalesforceToTemplateExporter:
    def __init__(self):
        self.template_file = Path('data/Revenue_Cloud_Clean_Template.xlsx')
        self.output_file = Path(f'data/Revenue_Cloud_Export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        self.target_org = 'fortradp2'
        
        # Define the mapping of sheet names to Salesforce objects and fields
        self.sheet_mappings = {
            '11_ProductCatalog': {
                'object': 'ProductCatalog',
                'fields': ['Id', 'Name', 'Code', 'Description', 'HierarchyId', 'CatalogId', 'CatalogType', 'External_ID__c'],
                'where': None
            },
            '12_ProductCategory': {
                'object': 'ProductCategory',
                'fields': ['Id', 'Name', 'Code', 'CatalogId', 'ParentCategoryId', 'External_ID__c'],
                'where': None
            },
            '15_ProductSellingModel': {
                'object': 'ProductSellingModel',
                'fields': ['Id', 'Name', 'SellingModelType', 'Status', 'PricingTermUnit', 'PricingTerm'],
                'where': None
            },
            '09_AttributeDefinition': {
                'object': 'AttributeDefinition',
                'fields': ['Id', 'Name', 'Code', 'Label', 'Type', 'Description', 'MinimumCharacterLength', 'MaximumCharacterLength', 
                          'MinimumNumberValue', 'MaximumNumberValue', 'PicklistId', 'Unit', 'HelpText', 'External_ID__c'],
                'where': None
            },
            '10_AttributeCategory': {
                'object': 'AttributeCategory',
                'fields': ['Id', 'Name', 'Code', 'External_ID__c'],
                'where': None
            },
            '08_ProductClassification': {
                'object': 'ProductClassification',
                'fields': ['Id', 'Name', 'Code', 'Description', 'Status'],
                'where': None
            },
            '13_Product2': {
                'object': 'Product2',
                'fields': ['Id', 'Name', 'ProductCode', 'Description', 'Family', 'Type', 'BasedOnId', 
                          'ProductClassId', 'ProductSellingModelId', 'QuantityUnitOfMeasure', 'StockKeepingUnit',
                          'TaxPolicyId', 'IsActive', 'LegalEntityId', 'CurrencyIsoCode', 'External_ID__c',
                          'IsPriceEditable', 'ExcludeFromSitemap', 'QuantityInstallmentPeriod', 
                          'NumberOfQuantityInstallments', 'QuantityInstallmentType', 'BillingPolicyId',
                          'CanUseQuantitySchedule', 'CanUseRevenueSchedule', 'ConnectionReceivedId', 
                          'ConnectionSentId', 'CreatedById'],
                'where': None
            },
            '14_ProductComponentGroup': {
                'object': 'ProductComponentGroup',
                'fields': ['Id', 'Name', 'ParentProductId', 'IsRequired', 'MinQuantity', 'MaxQuantity', 'Sequence', 'External_ID__c'],
                'where': None
            },
            '26_ProductCategoryProduct': {
                'object': 'ProductCategoryProduct',
                'fields': ['Id', 'Name', 'ProductCategoryId', 'ProductId', 'External_ID__c'],
                'where': None
            },
            '19_Pricebook2': {
                'object': 'Pricebook2',
                'fields': ['Id', 'Name', 'Description', 'IsActive', 'IsStandard', 'IsArchived', 'ExternalId__c', 'External_ID__c'],
                'where': None
            },
            '20_PricebookEntry': {
                'object': 'PricebookEntry',
                'fields': ['Id', 'Name', 'Product2Id', 'Pricebook2Id', 'UnitPrice', 'IsActive', 'UseStandardPrice', 
                          'IsArchived', 'External_ID__c'],
                'where': None
            },
            '01_CostBook': {
                'object': 'CostBook',
                'fields': ['Id', 'Name', 'LegalEntityId', 'Description', 'External_ID__c'],
                'where': None
            },
            '15_CostBookEntry': {
                'object': 'CostBookEntry',
                'fields': ['Id', 'Name', 'Product2Id', 'CostBookId', 'UnitCost', 'IsActive', 'IsArchived', 'External_ID__c'],
                'where': None
            },
            '21_PriceAdjustmentSchedule': {
                'object': 'PriceAdjustmentSchedule',
                'fields': ['Id', 'Name', 'PriceBook2Id', 'ProductId', 'ProductSellingModelId', 'Description', 
                          'AdjustmentMethod', 'IsActive', 'External_ID__c'],
                'where': None
            },
            '22_PriceAdjustmentTier': {
                'object': 'PriceAdjustmentTier',
                'fields': ['Id', 'Name', 'PriceAdjustmentScheduleId', 'LowerBound', 'UpperBound', 'AdjustmentType', 
                          'AdjustmentValue', 'External_ID__c'],
                'where': None
            },
            '23_AttributeBasedAdjRule': {
                'object': 'AttributeBasedAdjRule',
                'fields': ['Id', 'Name', 'IsActive'],
                'where': None
            },
            '24_AttributeBasedAdj': {
                'object': 'AttributeBasedAdj',
                'fields': ['Id', 'Name', 'AttributeBasedAdjRuleId', 'ProductAttributeDefinitionId', 'AttributeValue', 
                          'AdjustmentType', 'AdjustmentValue', 'IsActive', 'External_ID__c'],
                'where': None
            },
            '02_LegalEntity': {
                'object': 'LegalEntity',
                'fields': ['Id', 'Name', 'Status', 'CompanyName', 'Street', 'City', 'State', 'PostalCode', 
                          'Country', 'External_ID__c'],
                'where': None
            },
            '03_TaxEngine': {
                'object': 'TaxEngine',
                'fields': ['Id', 'Name', 'Status', 'TaxEngineProvider', 'ExternalReferenceNumber', 'IsDefault', 
                          'TaxEngineEndpointUrl', 'TaxEngineIntegrationClass', 'LegalEntityId', 'Description', 'External_ID__c'],
                'where': None
            },
            '04_TaxPolicy': {
                'object': 'TaxPolicy',
                'fields': ['Id', 'Name', 'Status', 'DefaultTaxTreatmentId', 'External_ID__c'],
                'where': None
            },
            '05_TaxTreatment': {
                'object': 'TaxTreatment',
                'fields': ['Id', 'Name', 'Status', 'TaxEngineId', 'TaxPolicyId', 'LegalEntityId', 'TaxTreatmentCode', 
                          'Description', 'External_ID__c'],
                'where': None
            },
            '06_BillingPolicy': {
                'object': 'BillingPolicy',
                'fields': ['Id', 'Name', 'Description', 'Status', 'External_ID__c'],
                'where': None
            },
            '07_BillingTreatment': {
                'object': 'BillingTreatment',
                'fields': ['Id', 'Name', 'Status', 'BillingLegalEntityId', 'BillingPolicyId', 'Description', 'External_ID__c'],
                'where': None
            },
            '25_ProductRelatedComponent': {
                'object': 'ProductRelatedComponent',
                'fields': ['Id', 'Name', 'ParentProductId', 'ChildProductId', 'ProductComponentGroupId', 
                          'MinQuantity', 'MaxQuantity', 'Quantity', 'IsComponentRequired', 'Sequence', 
                          'DoesBundlePriceIncludeChild', 'External_ID__c'],
                'where': None
            },
            '17_ProductAttributeDef': {
                'object': 'ProductAttributeDefinition',
                'fields': ['Id', 'Name', 'Product2Id', 'ProductClassificationAttributeId', 'AttributeDefinitionId', 
                          'AttributeCategoryId', 'Sequence', 'IsRequired', 'IsHidden', 'IsReadOnly', 
                          'IsPriceImpacting', 'DefaultValue', 'DefaultBoolValue', 'MinimumValue', 
                          'MaximumValue', 'DefaultNumberValue', 'Status', 'AttributeNameOverride', 
                          'MinimumCharacterCount', 'MaximumCharacterCount'],
                'where': None
            }
        }
    
    def query_salesforce(self, object_name, fields, where_clause=None):
        """Query Salesforce and return results as list of dictionaries."""
        try:
            # Build SOQL query
            field_list = ', '.join(fields)
            soql = f"SELECT {field_list} FROM {object_name}"
            if where_clause:
                soql += f" WHERE {where_clause}"
            soql += " ORDER BY CreatedDate DESC"
            
            # Execute query
            cmd = [
                'sf', 'data', 'query',
                '--query', soql,
                '--target-org', self.target_org,
                '--result-format', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data and 'records' in data['result']:
                    records = data['result']['records']
                    # Remove attributes field from each record
                    for record in records:
                        if 'attributes' in record:
                            del record['attributes']
                    return records
                return []
            else:
                print(f"Error querying {object_name}: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Exception querying {object_name}: {str(e)}")
            return []
    
    def export_all_data(self):
        """Export all data from Salesforce and populate the template."""
        print(f"Starting export from org: {self.target_org}")
        print(f"Template: {self.template_file}")
        print(f"Output: {self.output_file}")
        print()
        
        # Load the template
        xl_file = pd.ExcelFile(self.template_file)
        
        # Dictionary to store all sheets
        all_sheets = {}
        
        # Process each sheet
        for sheet_name in xl_file.sheet_names:
            print(f"Processing sheet: {sheet_name}")
            
            # Read the template sheet
            template_df = pd.read_excel(self.template_file, sheet_name=sheet_name)
            
            # Skip non-data sheets
            if sheet_name in ['Instructions', 'Picklist Values']:
                all_sheets[sheet_name] = template_df
                continue
            
            # Check if we have a mapping for this sheet
            if sheet_name in self.sheet_mappings:
                mapping = self.sheet_mappings[sheet_name]
                
                # Query Salesforce
                print(f"  - Querying {mapping['object']}...")
                records = self.query_salesforce(
                    mapping['object'],
                    mapping['fields'],
                    mapping.get('where')
                )
                
                if records:
                    print(f"  - Found {len(records)} records")
                    
                    # Convert to DataFrame
                    data_df = pd.DataFrame(records)
                    
                    # Map columns to match template
                    # First, get template columns
                    template_columns = template_df.columns.tolist()
                    
                    # Create new DataFrame with template structure
                    new_df = pd.DataFrame(columns=template_columns)
                    
                    # Map data columns to template columns
                    for col in template_columns:
                        # Handle special column mappings
                        if col in data_df.columns:
                            new_df[col] = data_df[col]
                        elif col.replace('*', '') in data_df.columns:
                            new_df[col] = data_df[col.replace('*', '')]
                        elif col == 'External_ID__c' and col not in data_df.columns:
                            # Generate external IDs if not present
                            new_df[col] = [f"{sheet_name}_{i+1}" for i in range(len(data_df))]
                    
                    # Replace the template data with actual data
                    all_sheets[sheet_name] = new_df
                    print(f"  - Populated {len(new_df)} rows")
                else:
                    print(f"  - No records found, keeping template structure")
                    # Keep just the header row
                    all_sheets[sheet_name] = template_df.head(1)
            else:
                print(f"  - No mapping defined, keeping template")
                all_sheets[sheet_name] = template_df
        
        # Write all sheets to output file
        print(f"\nWriting output file: {self.output_file}")
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("\nExport completed successfully!")
        print(f"Output file: {self.output_file}")
        
        return self.output_file

def main():
    exporter = SalesforceToTemplateExporter()
    exporter.export_all_data()

if __name__ == '__main__':
    main()