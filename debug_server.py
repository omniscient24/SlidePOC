#\!/usr/bin/env python3
"""Debug the server to see what products are being assigned"""

import pandas as pd
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, 'data', 'templates', 'master')
excel_file = os.path.join(data_dir, 'Revenue_Cloud_Complete_Upload_Template.xlsx')

# Load the Excel file
print(f"Loading: {excel_file}")
products_df = pd.read_excel(excel_file, sheet_name='13_Product2')
print(f"Total products: {len(products_df)}")

# Check DCS products
dcs_products = products_df[
    (products_df['Name'].str.contains('DCS', na=False)) & 
    (~products_df['Name'].str.contains('HRM|Professional|Support|Training', na=False))
]
print(f"\nDCS products for Data Classification: {len(dcs_products)}")
for _, p in dcs_products.head(5).iterrows():
    print(f"  - {p['Name']}")

# Check HRM/Service products  
hrm_products = products_df[
    (products_df['Name'].str.contains('HRM', na=False)) |
    (products_df['Name'].str.contains('Professional Services|Support|Training', na=False))
]
print(f"\nHRM/Service products for Human Risk Management: {len(hrm_products)}")
for _, p in hrm_products.head(5).iterrows():
    print(f"  - {p['Name']}")

# Check for overlap
overlap_ids = set(dcs_products['Id'].tolist()) & set(hrm_products['Id'].tolist())
print(f"\nOverlapping products: {len(overlap_ids)}")

# Check all products
print(f"\nAll products:")
for i, (_, p) in enumerate(products_df.iterrows()):
    print(f"{i+1}. {p['Name']}")
EOF < /dev/null