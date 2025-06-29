#!/usr/bin/env python3
"""Check what sheets are actually in the workbook"""

import pandas as pd
import os

workbook_path = os.path.join(os.path.dirname(__file__), 'data', 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx')

print(f"Reading workbook: {workbook_path}")

xl_file = pd.ExcelFile(workbook_path)
sheets = xl_file.sheet_names

print(f"\nTotal sheets found: {len(sheets)}")
print("\nAll sheets in workbook:")
print("-" * 40)

for i, sheet in enumerate(sheets, 1):
    print(f"{i:2d}. {sheet}")

# Check for missing mapped objects
missing_from_mapping = ['Order', 'OrderItem', 'Asset', 'AssetAction', 'AssetActionSource', 'Contract', 'ProductSellingModelOption']

print("\n\nLooking for sheets that might match missing objects:")
print("-" * 40)

for missing in missing_from_mapping:
    found = False
    for sheet in sheets:
        if missing.lower() in sheet.lower():
            print(f"Possible match for {missing}: {sheet}")
            found = True
    if not found:
        print(f"No match found for: {missing}")