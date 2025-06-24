#!/usr/bin/env python3
"""
Generate Pass2 files with proper ID mappings from the imported Pass1 records.
"""

import json
import csv
from pathlib import Path

class Pass2WithMappingsGenerator:
    def __init__(self):
        self.output_dir = Path('json_tree_output/pass2_mapped')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # These are the actual IDs from our successful Pass1 import
        self.product_ids = [
            '01tdp000006HfphAAC', '01tdp000006HfpiAAC', '01tdp000006HfpjAAC', '01tdp000006HfpkAAC',
            '01tdp000006HfplAAC', '01tdp000006HfpmAAC', '01tdp000006HfpnAAC', '01tdp000006HfpoAAC',
            '01tdp000006HfppAAC', '01tdp000006HfpqAAC', '01tdp000006HfprAAC', '01tdp000006HfpsAAC',
            '01tdp000006HfptAAC', '01tdp000006HfpuAAC', '01tdp000006HfpvAAC', '01tdp000006HfpwAAC',
            '01tdp000006HfpxAAC', '01tdp000006HfpyAAC', '01tdp000006HfpzAAC', '01tdp000006Hfq0AAC',
            '01tdp000006Hfq1AAC'
        ]
        
        self.category_ids = [
            '0ZGdp00000007JFGAY',  # Core Offerings
            '0ZGdp00000007JGGAY',  # Software  
            '0ZGdp00000007JHGAY',  # Managed Services
            '0ZGdp00000007JIGAY'   # Other Services
        ]
        
        self.attribute_ids = [
            '0tjdp00000000XtAAI',  # Managed Service?
            '0tjdp00000000XuAAI',  # Term
            '0tjdp00000000XvAAI'   # Users
        ]
        
        # Read product codes from CSV to create mapping
        self.product_mapping = self.create_product_mapping()
        
    def create_product_mapping(self):
        """Create a mapping of product codes to new IDs."""
        mapping = {}
        csv_path = Path('data/csv_output/pass1/13_Product2.csv')
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Map by index (in order of CSV)
        for idx, row in enumerate(rows):
            if idx < len(self.product_ids):
                product_code = row.get('ProductCode', '').strip()
                if product_code:
                    mapping[product_code] = self.product_ids[idx]
                    
        return mapping
    
    def generate_product_category_products(self):
        """Generate ProductCategoryProduct with smart category assignments."""
        records = []
        
        # Map products to categories based on their characteristics
        # First 3 products (DCS bundles) -> Core Offerings
        for i in range(3):
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[i],
                "ProductCategoryId": self.category_ids[0]  # Core Offerings
            })
        
        # Next 8 products (DCS components) -> Software
        for i in range(3, 11):
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[i],
                "ProductCategoryId": self.category_ids[1]  # Software
            })
        
        # Next 4 products (Mail, Policy Manager) -> Software
        for i in range(11, 15):
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[i],
                "ProductCategoryId": self.category_ids[1]  # Software
            })
        
        # Professional Services -> Other Services
        for i in range(15, 18):
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[i],
                "ProductCategoryId": self.category_ids[3]  # Other Services
            })
        
        # Training -> Other Services
        if len(self.product_ids) > 18:
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[18],
                "ProductCategoryId": self.category_ids[3]  # Other Services
            })
        
        # Support products -> Managed Services
        for i in range(19, min(21, len(self.product_ids))):
            records.append({
                "attributes": {
                    "type": "ProductCategoryProduct",
                    "referenceId": f"ProductCategoryProduct_Ref{len(records)+1}"
                },
                "ProductId": self.product_ids[i],
                "ProductCategoryId": self.category_ids[2]  # Managed Services
            })
        
        with open(self.output_dir / 'ProductCategoryProduct.json', 'w') as f:
            json.dump({"records": records}, f, indent=2)
        
        print(f"Generated ProductCategoryProduct.json with {len(records)} records")
        
    def generate_product_attribute_definitions(self):
        """Generate ProductAttributeDefinition for relevant products."""
        records = []
        
        # Add "Managed Service?" attribute to support products
        for i in range(19, min(21, len(self.product_ids))):
            records.append({
                "attributes": {
                    "type": "ProductAttributeDefinition",
                    "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
                },
                "Product2Id": self.product_ids[i],
                "AttributeDefinitionId": self.attribute_ids[0],  # Managed Service?
                "Status": "Active",
                "IsRequired": False,
                "Sequence": 1
            })
        
        # Add "Term" attribute to subscription products (first 3)
        for i in range(3):
            records.append({
                "attributes": {
                    "type": "ProductAttributeDefinition",
                    "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
                },
                "Product2Id": self.product_ids[i],
                "AttributeDefinitionId": self.attribute_ids[1],  # Term
                "Status": "Active",
                "IsRequired": True,
                "Sequence": 2,
                "DefaultValue": "12"
            })
        
        # Add "Users" attribute to software products
        for i in range(3, 15):
            records.append({
                "attributes": {
                    "type": "ProductAttributeDefinition",
                    "referenceId": f"ProductAttributeDefinition_Ref{len(records)+1}"
                },
                "Product2Id": self.product_ids[i],
                "AttributeDefinitionId": self.attribute_ids[2],  # Users
                "Status": "Active",
                "IsRequired": False,
                "Sequence": 3
            })
        
        with open(self.output_dir / 'ProductAttributeDefinition.json', 'w') as f:
            json.dump({"records": records}, f, indent=2)
        
        print(f"Generated ProductAttributeDefinition.json with {len(records)} records")
    
    def generate_product_related_components(self):
        """Generate ProductRelatedComponent for bundle products."""
        records = []
        
        # Use the Bundle to Bundle Component Relationship type
        relationship_type_id = "0yoa5000000gTtdAAE"
        
        # DCS Essentials bundle includes basic components
        if len(self.product_ids) >= 8:
            # DCS Essentials includes Data Detection Engine
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[0],  # DCS Essentials
                "ChildProductId": self.product_ids[3],   # Data Detection Engine
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsDefaultComponent": True,
                "Sequence": 1
            })
            
            # DCS Essentials includes DCS for Windows
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[0],  # DCS Essentials
                "ChildProductId": self.product_ids[7],   # DCS for Windows
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsComponentRequired": True,
                "Sequence": 2,
                "DoesBundlePriceIncludeChild": True
            })
        
        # DCS Advanced bundle includes more components
        if len(self.product_ids) >= 10:
            # All components from Essentials
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[1],  # DCS Advanced
                "ChildProductId": self.product_ids[3],   # Data Detection Engine
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsDefaultComponent": True,
                "Sequence": 1
            })
            
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[1],  # DCS Advanced
                "ChildProductId": self.product_ids[7],   # DCS for Windows
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsComponentRequired": True,
                "Sequence": 2,
                "DoesBundlePriceIncludeChild": True
            })
            
            # Plus Unlimited Classification
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[1],  # DCS Advanced
                "ChildProductId": self.product_ids[4],   # Unlimited Classification
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsComponentRequired": True,
                "Sequence": 3,
                "DoesBundlePriceIncludeChild": True
            })
            
            # Plus Admin Console
            records.append({
                "attributes": {
                    "type": "ProductRelatedComponent",
                    "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                },
                "ParentProductId": self.product_ids[1],  # DCS Advanced
                "ChildProductId": self.product_ids[6],   # DCS Admin Console
                "ProductRelationshipTypeId": relationship_type_id,
                "Quantity": 1.0,
                "IsComponentRequired": True,
                "Sequence": 4,
                "DoesBundlePriceIncludeChild": True
            })
        
        # DCS Elite bundle includes everything
        if len(self.product_ids) >= 12:
            # Include all software components
            for idx, child_idx in enumerate([3, 4, 5, 6, 7, 8, 9]):
                if child_idx < len(self.product_ids):
                    records.append({
                        "attributes": {
                            "type": "ProductRelatedComponent",
                            "referenceId": f"ProductRelatedComponent_Ref{len(records)+1}"
                        },
                        "ParentProductId": self.product_ids[2],  # DCS Elite
                        "ChildProductId": self.product_ids[child_idx],
                        "ProductRelationshipTypeId": relationship_type_id,
                        "Quantity": 1.0,
                        "IsComponentRequired": True,
                        "Sequence": idx + 1,
                        "DoesBundlePriceIncludeChild": True
                    })
        
        with open(self.output_dir / 'ProductRelatedComponent.json', 'w') as f:
            json.dump({"records": records}, f, indent=2)
        
        print(f"Generated ProductRelatedComponent.json with {len(records)} records")
    
    def generate_import_plan(self):
        """Generate the import plan for mapped Pass2 files."""
        plan = [
            {
                "sobject": "ProductCategoryProduct",
                "files": ["../json_tree_output/pass2_mapped/ProductCategoryProduct.json"]
            },
            {
                "sobject": "ProductAttributeDefinition",
                "files": ["../json_tree_output/pass2_mapped/ProductAttributeDefinition.json"]
            },
            {
                "sobject": "ProductRelatedComponent",
                "files": ["../json_tree_output/pass2_mapped/ProductRelatedComponent.json"]
            }
        ]
        
        plan_path = Path('plans_tree/pass2_mapped_import.json')
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        print(f"Generated import plan: {plan_path}")
    
    def generate_all(self):
        """Generate all Pass2 files with proper mappings."""
        self.generate_product_category_products()
        self.generate_product_attribute_definitions()
        self.generate_product_related_components()
        self.generate_import_plan()

def main():
    generator = Pass2WithMappingsGenerator()
    generator.generate_all()
    print("\nAll Pass2 files generated with proper ID mappings!")

if __name__ == '__main__':
    main()