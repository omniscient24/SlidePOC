#!/usr/bin/env python3
"""
Generate minimal Pass 2 files that only reference the products we just imported.
"""

import json
from pathlib import Path

def generate_minimal_pass2():
    output_dir = Path('json_tree_output/pass2_minimal')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the imported Product and Category IDs from Pass 1
    # These are the actual IDs from the successful import
    product_ids = [
        '01tdp000006HfphAAC', '01tdp000006HfpiAAC', '01tdp000006HfpjAAC', '01tdp000006HfpkAAC',
        '01tdp000006HfplAAC', '01tdp000006HfpmAAC', '01tdp000006HfpnAAC', '01tdp000006HfpoAAC',
        '01tdp000006HfppAAC', '01tdp000006HfpqAAC', '01tdp000006HfprAAC', '01tdp000006HfpsAAC',
        '01tdp000006HfptAAC', '01tdp000006HfpuAAC', '01tdp000006HfpvAAC', '01tdp000006HfpwAAC',
        '01tdp000006HfpxAAC', '01tdp000006HfpyAAC', '01tdp000006HfpzAAC', '01tdp000006Hfq0AAC',
        '01tdp000006Hfq1AAC'
    ]
    
    category_ids = ['0ZGdp00000007JFGAY', '0ZGdp00000007JGGAY', '0ZGdp00000007JHGAY', '0ZGdp00000007JIGAY']
    
    pricebook_ids = ['01sdp000001Uf5BAAS', '01sdp000001Uf5CAAS', '01sdp000001Uf5DAAS']
    
    # 1. Create ProductSellingModel records
    selling_models = {
        "records": [
            {
                "attributes": {
                    "type": "ProductSellingModel",
                    "referenceId": "ProductSellingModel_Ref1"
                },
                "Name": "Monthly Subscription",
                "SellingModelType": "Evergreen",
                "Status": "Active",
                "PricingTermUnit": "Months",
                "PricingTerm": 1.0
            },
            {
                "attributes": {
                    "type": "ProductSellingModel",
                    "referenceId": "ProductSellingModel_Ref2"
                },
                "Name": "One Time Purchase",
                "SellingModelType": "OneTime",
                "Status": "Active"
            }
        ]
    }
    
    with open(output_dir / 'ProductSellingModel.json', 'w') as f:
        json.dump(selling_models, f, indent=2)
    
    # 2. Create ProductCategoryProduct - link first 4 products to first category
    category_products = {
        "records": [
            {
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{i+1}"
                },
                "ProductId": product_ids[i],
                "ProductCategoryId": category_ids[0]
            }
            for i in range(4)
        ]
    }
    
    with open(output_dir / 'ProductCategoryProduct.json', 'w') as f:
        json.dump(category_products, f, indent=2)
    
    # 3. Create PricebookEntry - first create standard prices, then custom prices
    standard_pricebook_id = '01sa5000001vuxlAAA'
    
    # Standard pricebook entries
    standard_entries = {
        "records": [
            {
                "attributes": {
                    "type": "PricebookEntry",
                    "referenceId": f"StandardPricebookEntry_Ref{i+1}"
                },
                "Product2Id": product_ids[i],
                "Pricebook2Id": standard_pricebook_id,
                "UnitPrice": 100.00 * (i + 1),
                "IsActive": True
            }
            for i in range(3)
        ]
    }
    
    with open(output_dir / 'StandardPricebookEntry.json', 'w') as f:
        json.dump(standard_entries, f, indent=2)
    
    # Custom pricebook entries
    pricebook_entries = {
        "records": [
            {
                "attributes": {
                    "type": "PricebookEntry",
                    "referenceId": f"PricebookEntry_Ref{i+1}"
                },
                "Product2Id": product_ids[i],
                "Pricebook2Id": pricebook_ids[0],
                "UnitPrice": 90.00 * (i + 1),  # Different price for custom pricebook
                "IsActive": True
            }
            for i in range(3)
        ]
    }
    
    with open(output_dir / 'PricebookEntry.json', 'w') as f:
        json.dump(pricebook_entries, f, indent=2)
    
    # Create import plan - only PricebookEntry for now
    plan = [
        {
            "sobject": "PricebookEntry",
            "files": ["../json_tree_output/pass2_minimal/StandardPricebookEntry.json"]
        },
        {
            "sobject": "PricebookEntry",
            "files": ["../json_tree_output/pass2_minimal/PricebookEntry.json"]
        }
    ]
    
    plan_path = Path('plans_tree/pass2_minimal_import.json')
    with open(plan_path, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print("Generated minimal Pass 2 files:")
    print("- ProductSellingModel.json (2 records)")
    print("- ProductCategoryProduct.json (4 records)")
    print("- StandardPricebookEntry.json (3 records)")
    print("- PricebookEntry.json (3 records)")
    print("- pass2_minimal_import.json")

if __name__ == '__main__':
    generate_minimal_pass2()