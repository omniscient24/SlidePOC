#!/usr/bin/env python3
"""
Generate ProductAttributeDefinition records using the correct ProductClassificationAttributeId.
"""

import json
from pathlib import Path

def generate_product_attribute_definitions():
    output_dir = Path('json_tree_output/product_attributes')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Our imported Product IDs
    product_ids = [
        '01tdp000006HfphAAC', '01tdp000006HfpiAAC', '01tdp000006HfpjAAC', '01tdp000006HfpkAAC',
        '01tdp000006HfplAAC', '01tdp000006HfpmAAC', '01tdp000006HfpnAAC', '01tdp000006HfpoAAC',
        '01tdp000006HfppAAC', '01tdp000006HfpqAAC', '01tdp000006HfprAAC', '01tdp000006HfpsAAC',
        '01tdp000006HfptAAC', '01tdp000006HfpuAAC', '01tdp000006HfpvAAC', '01tdp000006HfpwAAC',
        '01tdp000006HfpxAAC', '01tdp000006HfpyAAC', '01tdp000006HfpzAAC', '01tdp000006Hfq0AAC',
        '01tdp000006Hfq1AAC'
    ]
    
    # ProductClassificationAttr IDs we just created
    classification_attr_ids = {
        'managed_service': '11Cdp000003aD8HEAU',  # Managed Service?
        'term': '11Cdp000003aD8IEAU',            # Term
        'users': '11Cdp000003aD8JEAU'            # Users
    }
    
    # Original AttributeDefinition IDs
    attribute_definition_ids = {
        'managed_service': '0tjdp00000000XtAAI',  # Managed Service?
        'term': '0tjdp00000000XuAAI',            # Term
        'users': '0tjdp00000000XvAAI'            # Users
    }
    
    records = []
    
    # Add "Managed Service?" attribute to support products (indices 19-20)
    for i in range(19, min(21, len(product_ids))):
        records.append({
            "attributes": {
                "type": "ProductAttributeDefinition",
                "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
            },
            "Name": f"Managed Service - {product_ids[i][-8:]}",  # Unique name
            "Product2Id": product_ids[i],
            "ProductClassificationAttributeId": classification_attr_ids['managed_service'],
            "AttributeDefinitionId": attribute_definition_ids['managed_service'],
            "Status": "Active",
            "IsRequired": False,
            "Sequence": 1
        })
    
    # Add "Term" attribute to subscription products (first 3 bundles)
    for i in range(3):
        records.append({
            "attributes": {
                "type": "ProductAttributeDefinition",
                "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
            },
            "Name": f"Term - {product_ids[i][-8:]}",  # Unique name
            "Product2Id": product_ids[i],
            "ProductClassificationAttributeId": classification_attr_ids['term'],
            "AttributeDefinitionId": attribute_definition_ids['term'],
            "Status": "Active",
            "IsRequired": True,
            "Sequence": 2,
            "DefaultValue": "12"
        })
    
    # Add "Users" attribute to software products (indices 3-14)
    for i in range(3, 15):
        if i < len(product_ids):
            records.append({
                "attributes": {
                    "type": "ProductAttributeDefinition",
                    "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
                },
                "Name": f"Users - {product_ids[i][-8:]}",  # Unique name
                "Product2Id": product_ids[i],
                "ProductClassificationAttributeId": classification_attr_ids['users'],
                "AttributeDefinitionId": attribute_definition_ids['users'],
                "Status": "Active",
                "IsRequired": False,
                "Sequence": 3
            })
    
    # Save the file
    with open(output_dir / 'ProductAttributeDefinition.json', 'w') as f:
        json.dump({"records": records}, f, indent=2)
    
    # Create import plan
    plan = [{
        "sobject": "ProductAttributeDefinition",
        "files": ["../json_tree_output/product_attributes/ProductAttributeDefinition.json"]
    }]
    
    plan_path = Path('plans_tree/product_attribute_definition_import.json')
    with open(plan_path, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"Generated ProductAttributeDefinition.json with {len(records)} records")
    print(f"Generated import plan: {plan_path}")

if __name__ == '__main__':
    generate_product_attribute_definitions()