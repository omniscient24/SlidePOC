#!/usr/bin/env python3
"""
Generate minimal JSON tree import files for initial import without dependencies.
"""

import json
import csv
from pathlib import Path

def generate_minimal_files():
    # Create output directory
    output_dir = Path('json_tree_output/pass1_minimal')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create ProductCatalog without dependencies
    product_catalogs = {
        "records": [
            {
                "attributes": {
                    "type": "ProductCatalog",
                    "referenceId": "ProductCatalog_Ref1"
                },
                "Name": "Standard Product Catalog",
                "Code": "STANDARD",
                "Description": "Standard product catalog for all products"
            }
        ]
    }
    
    with open(output_dir / 'ProductCatalog.json', 'w') as f:
        json.dump(product_catalogs, f, indent=2)
    
    # 2. Create AttributeDefinition without dependencies
    attr_defs = {
        "records": [
            {
                "attributes": {
                    "type": "AttributeDefinition",
                    "referenceId": "AttributeDefinition_Ref1"
                },
                "Name": "Color",
                "Code": "COLOR",
                "DataType": "Text",
                "Description": "Product color attribute",
                "IsActive": True
            },
            {
                "attributes": {
                    "type": "AttributeDefinition",
                    "referenceId": "AttributeDefinition_Ref2"
                },
                "Name": "Size",
                "Code": "SIZE",
                "DataType": "Text",
                "Description": "Product size attribute",
                "IsActive": True
            }
        ]
    }
    
    with open(output_dir / 'AttributeDefinition.json', 'w') as f:
        json.dump(attr_defs, f, indent=2)
    
    # 3. Create Product2 without dependencies
    products = {
        "records": [
            {
                "attributes": {
                    "type": "Product2",
                    "referenceId": "Product2_Ref1"
                },
                "Name": "Basic Product",
                "ProductCode": "PROD-001",
                "Description": "Basic product for testing",
                "IsActive": True,
                "QuantityUnitOfMeasure": "Each"
            },
            {
                "attributes": {
                    "type": "Product2",
                    "referenceId": "Product2_Ref2"
                },
                "Name": "Premium Product",
                "ProductCode": "PROD-002",
                "Description": "Premium product for testing",
                "IsActive": True,
                "QuantityUnitOfMeasure": "Each"
            }
        ]
    }
    
    with open(output_dir / 'Product2.json', 'w') as f:
        json.dump(products, f, indent=2)
    
    # 4. Create Pricebook2 without dependencies
    pricebooks = {
        "records": [
            {
                "attributes": {
                    "type": "Pricebook2",
                    "referenceId": "Pricebook2_Ref1"
                },
                "Name": "Standard Price Book",
                "Description": "Standard pricing",
                "IsActive": True,
                "IsStandard": False
            }
        ]
    }
    
    with open(output_dir / 'Pricebook2.json', 'w') as f:
        json.dump(pricebooks, f, indent=2)
    
    # Create import plan
    plan = [
        {
            "sobject": "ProductCatalog",
            "files": ["../json_tree_output/pass1_minimal/ProductCatalog.json"]
        },
        {
            "sobject": "AttributeDefinition",
            "files": ["../json_tree_output/pass1_minimal/AttributeDefinition.json"]
        },
        {
            "sobject": "Product2",
            "files": ["../json_tree_output/pass1_minimal/Product2.json"]
        },
        {
            "sobject": "Pricebook2",
            "files": ["../json_tree_output/pass1_minimal/Pricebook2.json"]
        }
    ]
    
    plan_path = Path('plans_tree/pass1_minimal_import.json')
    with open(plan_path, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print("Generated minimal import files:")
    print(f"- {output_dir}/ProductCatalog.json")
    print(f"- {output_dir}/AttributeDefinition.json")
    print(f"- {output_dir}/Product2.json")
    print(f"- {output_dir}/Pricebook2.json")
    print(f"- {plan_path}")

if __name__ == '__main__':
    generate_minimal_files()