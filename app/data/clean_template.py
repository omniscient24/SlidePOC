#!/usr/bin/env python3
"""
Clean up the Revenue Cloud Complete Upload Template by removing hardcoded IDs
and making it a proper template for reuse.
"""

import pandas as pd
import os
from pathlib import Path

def clean_template():
    input_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
    output_file = Path('data/Revenue_Cloud_Clean_Template.xlsx')
    
    # Load all sheets
    xl_file = pd.ExcelFile(input_file)
    
    # Dictionary to store cleaned dataframes
    cleaned_sheets = {}
    
    # Define ID columns to clean per sheet
    id_columns_to_clean = {
        '26_ProductCategoryProduct': ['ProductCategoryId*', 'ProductId*'],
        '25_ProductRelatedComponent': ['ParentProductId*', 'ChildProductId*', 'ProductRelationshipTypeId*'],
        '17_ProductAttributeDef': ['ProductId*', 'ProductClassificationAttributeId*', 'AttributeDefinitionId', 'AttributeCategoryId'],
        '20_PricebookEntry': ['Product2Id*', 'Pricebook2Id*'],
        '15_CostBookEntry': ['Product2Id*', 'CostBookId*'],
        '22_PriceAdjustmentTier': ['PriceAdjustmentScheduleId*'],
        '24_AttributeBasedAdj': ['AttributeBasedAdjRuleId*', 'ProductAttributeDefinitionId*'],
        '14_ProductComponentGroup': ['ParentProductId*'],
    }
    
    # Define reference columns (that should be changed to placeholders)
    reference_columns = {
        '11_ProductCatalog': ['HierarchyId', 'CatalogId'],
        '12_ProductCategory': ['CatalogId*', 'ParentCategoryId'],
        '15_ProductSellingModel': ['PricingTermUnit', 'PricingTerm'],
        '09_AttributeDefinition': ['PicklistId'],
        '13_Product2': ['BasedOnId', 'ProductClassId', 'ProductSellingModelId', 'TaxPolicyId', 'LegalEntityId'],
        '19_Pricebook2': ['ExternalId__c'],
        '01_CostBook': ['LegalEntityId*'],
        '21_PriceAdjustmentSchedule': ['PriceBook2Id*', 'ProductId*', 'ProductSellingModelId*'],
        '06_BillingPolicy': [],
        '07_BillingTreatment': ['BillingLegalEntityId*', 'BillingPolicyId*'],
        '02_LegalEntity': [],
        '05_TaxTreatment': ['TaxEngineId*', 'TaxPolicyId*', 'LegalEntityId*'],
        '04_TaxPolicy': ['DefaultTaxTreatmentId'],
        '03_TaxEngine': ['LegalEntityId*'],
    }
    
    print("Cleaning Revenue Cloud Template...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    for sheet_name in xl_file.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        
        # Read the sheet
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        
        # Skip instructions and picklist sheets
        if sheet_name in ['Instructions', 'Picklist Values']:
            cleaned_sheets[sheet_name] = df
            continue
            
        # Clean ID columns (replace with placeholder text)
        if sheet_name in id_columns_to_clean:
            for col in id_columns_to_clean[sheet_name]:
                if col in df.columns:
                    # Replace with descriptive placeholder
                    if 'Product' in col:
                        placeholder = 'PRODUCT_ID_HERE'
                    elif 'Category' in col:
                        placeholder = 'CATEGORY_ID_HERE'
                    elif 'Attribute' in col:
                        placeholder = 'ATTRIBUTE_ID_HERE'
                    elif 'Pricebook' in col:
                        placeholder = 'PRICEBOOK_ID_HERE'
                    elif 'CostBook' in col:
                        placeholder = 'COSTBOOK_ID_HERE'
                    elif 'Relationship' in col:
                        placeholder = 'RELATIONSHIP_TYPE_ID_HERE'
                    elif 'Schedule' in col:
                        placeholder = 'SCHEDULE_ID_HERE'
                    elif 'Rule' in col:
                        placeholder = 'RULE_ID_HERE'
                    else:
                        placeholder = 'ID_HERE'
                    
                    # Replace all data rows with placeholder
                    if len(df) > 1:  # Skip header row
                        # Replace all non-header rows
                        for idx in range(1, len(df)):
                            df.loc[idx, col] = placeholder
                        print(f"  - Cleaned column: {col}")
        
        # Clean reference columns
        if sheet_name in reference_columns:
            for col in reference_columns[sheet_name]:
                if col in df.columns:
                    # Clear these columns or set to null/placeholder
                    if len(df) > 0:
                        if 'Id' in col:
                            df.loc[1:, col] = ''
                        print(f"  - Cleared column: {col}")
        
        # Additional cleanup for specific sheets
        if sheet_name == '13_Product2':
            # Clear Type field if it exists (should be set based on use case)
            if 'Type' in df.columns:
                df.loc[1:, 'Type'] = ''
                
        if sheet_name == '09_AttributeDefinition':
            # Keep only non-picklist attributes as examples
            if 'Type' in df.columns:
                # Keep first few rows as examples
                df = df.head(5)
                
        if sheet_name == '15_ProductSellingModel':
            # Keep basic examples only
            df = df.head(3)
            
        if sheet_name == '26_ProductCategoryProduct':
            # Keep just headers and a few example rows
            df = df.head(5)
            
        if sheet_name == '25_ProductRelatedComponent':
            # Keep just headers and a few example rows
            df = df.head(5)
            
        if sheet_name == '20_PricebookEntry':
            # Keep just headers and a few example rows
            df = df.head(5)
            
        # Clear any columns that end with __c (custom fields with IDs)
        for col in df.columns:
            if col.endswith('__c') and 'External' in col:
                if len(df) > 0:
                    # Generate sequential external IDs
                    df[col] = [f"{sheet_name}_{i+1}" for i in range(len(df))]
                    print(f"  - Reset external ID column: {col}")
        
        cleaned_sheets[sheet_name] = df
    
    # Write all sheets to new file
    print("\nWriting cleaned template...")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in cleaned_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"\nTemplate cleaned successfully!")
    print(f"Output saved to: {output_file}")
    
    # Create a summary of what was cleaned
    summary = """
    CLEANED TEMPLATE SUMMARY
    ========================
    
    The following changes were made to create a reusable template:
    
    1. Removed all hardcoded Salesforce IDs and replaced with placeholders:
       - PRODUCT_ID_HERE
       - CATEGORY_ID_HERE
       - ATTRIBUTE_ID_HERE
       - PRICEBOOK_ID_HERE
       - etc.
    
    2. Cleared reference fields that point to other records
    
    3. Reset External ID fields to use sequential numbering
    
    4. Reduced example rows in junction object sheets
    
    5. Kept sheet structure and column headers intact
    
    To use this template:
    1. Fill in your actual Salesforce IDs where placeholders exist
    2. Add your product and configuration data
    3. Set appropriate relationships between objects
    4. Import in the correct order (see Instructions sheet)
    """
    
    print(summary)
    
    # Save summary to file
    with open('data/template_cleanup_summary.txt', 'w') as f:
        f.write(summary)

if __name__ == '__main__':
    clean_template()