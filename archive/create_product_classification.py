#!/usr/bin/env python3
"""
Create ProductClassification and ProductClassificationAttr records
to properly link attributes to products.
"""

import json
from pathlib import Path

def create_product_classification():
    output_dir = Path('json_tree_output/product_classification')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Our imported AttributeDefinition IDs
    attribute_ids = [
        '0tjdp00000000XtAAI',  # Managed Service?
        '0tjdp00000000XuAAI',  # Term
        '0tjdp00000000XvAAI'   # Users
    ]
    
    # Create a ProductClassification
    product_classification = {
        "records": [{
            "attributes": {
                "type": "ProductClassification",
                "referenceId": "ProductClassification_Ref1"
            },
            "Name": "Product Attributes",
            "Code": "PROD_ATTRS"
        }]
    }
    
    with open(output_dir / 'ProductClassification.json', 'w') as f:
        json.dump(product_classification, f, indent=2)
    
    # Create ProductClassificationAttr records linking to our AttributeDefinition records
    classification_attrs = {
        "records": [
            {
                "attributes": {
                    "type": "ProductClassificationAttr",
                    "referenceId": f"ProductClassificationAttr_Ref{idx+1}"
                },
                "Name": name,
                "ProductClassificationId": "@ProductClassification_Ref1",
                "AttributeDefinitionId": attr_id,
                "Status": "Active",
                "Sequence": idx + 1,
                "IsRequired": False,
                "IsHidden": False,
                "IsReadOnly": False,
                "IsPriceImpacting": False
            }
            for idx, (attr_id, name) in enumerate([
                (attribute_ids[0], "Managed Service?"),
                (attribute_ids[1], "Term"),
                (attribute_ids[2], "Users")
            ])
        ]
    }
    
    with open(output_dir / 'ProductClassificationAttr.json', 'w') as f:
        json.dump(classification_attrs, f, indent=2)
    
    # Create import plan
    plan = [
        {
            "sobject": "ProductClassification",
            "files": ["../json_tree_output/product_classification/ProductClassification.json"]
        },
        {
            "sobject": "ProductClassificationAttr", 
            "files": ["../json_tree_output/product_classification/ProductClassificationAttr.json"]
        }
    ]
    
    plan_path = Path('plans_tree/product_classification_import.json')
    with open(plan_path, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print("Created:")
    print("- ProductClassification.json (1 record)")
    print("- ProductClassificationAttr.json (3 records)")
    print("- product_classification_import.json")

if __name__ == '__main__':
    create_product_classification()