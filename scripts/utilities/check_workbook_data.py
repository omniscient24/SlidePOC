#!/usr/bin/env python3
"""Check which sheets have data in the workbook"""

import pandas as pd

workbook_path = 'data/Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx'

# Sheet mapping from server.py
sheet_mapping = {
    'ProductCatalog': '11_ProductCatalog',
    'ProductCategory': '12_ProductCategory',
    'Product2': '13_Product2',
    'ProductClassification': '08_ProductClassification',
    'AttributeDefinition': '09_AttributeDefinition',
    'AttributeCategory': '10_AttributeCategory',
    'AttributePicklist': '14_AttributePicklist',
    'AttributePicklistValue': '18_AttributePicklistValue',
    'ProductAttributeDefinition': '17_ProductAttributeDef',
    'Pricebook2': '19_Pricebook2',
    'PricebookEntry': '20_PricebookEntry',
    'CostBook': '01_CostBook',
    'CostBookEntry': '15_CostBookEntry',
    'PriceAdjustmentSchedule': '21_PriceAdjustmentSchedule',
    'PriceAdjustmentTier': '22_PriceAdjustmentTier',
    'LegalEntity': '02_LegalEntity',
    'TaxEngine': '03_TaxEngine',
    'TaxPolicy': '04_TaxPolicy',
    'TaxTreatment': '05_TaxTreatment',
    'BillingPolicy': '06_BillingPolicy',
    'BillingTreatment': '07_BillingTreatment',
    'ProductSellingModel': '15_ProductSellingModel',
    'ProductComponentGroup': '14_ProductComponentGroup',
    'ProductRelatedComponent': '25_ProductRelatedComponent',
    'ProductCategoryProduct': '26_ProductCategoryProduct'
}

print("Checking workbook data...")
print(f"Workbook: {workbook_path}\n")

xl_file = pd.ExcelFile(workbook_path)
data_summary = []

for api_name, sheet_name in sorted(sheet_mapping.items()):
    if sheet_name in xl_file.sheet_names:
        try:
            df = pd.read_excel(workbook_path, sheet_name=sheet_name)
            df_clean = df.dropna(how='all')
            data_summary.append({
                'Object': api_name,
                'Sheet': sheet_name,
                'Rows': len(df_clean),
                'Status': '✓ Has Data' if len(df_clean) > 0 else '✗ Empty'
            })
        except Exception as e:
            data_summary.append({
                'Object': api_name,
                'Sheet': sheet_name,
                'Rows': 0,
                'Status': f'Error: {str(e)}'
            })
    else:
        data_summary.append({
            'Object': api_name,
            'Sheet': sheet_name,
            'Rows': 0,
            'Status': '✗ Sheet Not Found'
        })

# Print summary
print("Data Summary:")
print("-" * 60)
print(f"{'Object':<25} {'Sheet':<25} {'Rows':>6} {'Status'}")
print("-" * 60)

for item in data_summary:
    print(f"{item['Object']:<25} {item['Sheet']:<25} {item['Rows']:>6} {item['Status']}")

# Count totals
has_data = sum(1 for item in data_summary if item['Rows'] > 0)
empty = sum(1 for item in data_summary if item['Rows'] == 0 and 'Error' not in item['Status'] and 'Not Found' not in item['Status'])
errors = sum(1 for item in data_summary if 'Error' in item['Status'] or 'Not Found' in item['Status'])

print("-" * 60)
print(f"Total: {len(data_summary)} objects")
print(f"  - With Data: {has_data}")
print(f"  - Empty: {empty}")
print(f"  - Errors: {errors}")