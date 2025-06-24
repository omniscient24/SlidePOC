#!/usr/bin/env python3
"""
Generate JSON tree import files for pass2 without custom fields to avoid FLS issues.
"""

import json
import csv
from pathlib import Path

class Pass2JSONTreeGeneratorNoCustom:
    def __init__(self, csv_dir, json_output_dir):
        self.csv_dir = Path(csv_dir)
        self.json_output_dir = Path(json_output_dir)
        self.json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the imported IDs from Pass 1
        self.pass1_ids = self.get_pass1_ids()
        
        # Field mappings for pass2 objects (without custom fields)
        self.field_mappings = {
            'ProductSellingModel': {
                'sobject': 'ProductSellingModel',
                'csv_file': '15_ProductSellingModel.csv',
                'required_fields': ['Name', 'SellingModelType', 'Status'],
                'field_map': {
                    'Name': 'Name',
                    'SellingModelType': 'SellingModelType',
                    'Status': 'Status',
                    'PricingTermUnit': 'PricingTermUnit',
                    'PricingTerm': 'PricingTerm'
                    # Removed ModelCode__c custom field
                }
            },
            'ProductCategoryProduct': {
                'sobject': 'ProductCategoryProduct',
                'csv_file': '26_ProductCategoryProduct.csv',
                'required_fields': ['ProductId', 'ProductCategoryId'],
                'field_map': {
                    'ProductId': 'ProductId*',
                    'ProductCategoryId': 'ProductCategoryId*'
                    # Removed External_ID__c custom field
                }
            },
            'ProductAttributeDefinition': {
                'sobject': 'ProductAttributeDefinition',
                'csv_file': '17_ProductAttributeDef.csv',
                'required_fields': ['Product2Id', 'AttributeDefinitionId'],
                'field_map': {
                    'Product2Id': 'Product2Id',
                    'AttributeDefinitionId': 'AttributeDefinitionId',
                    'AttributeCategoryId': 'AttributeCategoryId',
                    'Sequence': 'Sequence',
                    'IsRequired': 'IsRequired',
                    'IsHidden': 'IsHidden',
                    'IsReadOnly': 'IsReadOnly',
                    'IsPriceImpacting': 'IsPriceImpacting',
                    'DefaultValue': 'DefaultValue',
                    'HelpText': 'HelpText',
                    'MinimumValue': 'MinimumValue',
                    'MaximumValue': 'MaximumValue',
                    'DisplayType': 'DisplayType',
                    'Status': 'Status',
                    'AttributeNameOverride': 'AttributeNameOverride',
                    'Description': 'Description'
                }
            },
            'ProductRelatedComponent': {
                'sobject': 'ProductRelatedComponent',
                'csv_file': '25_ProductRelatedComponent.csv',
                'required_fields': ['ParentProductId', 'ChildProductId'],
                'field_map': {
                    'ParentProductId': 'ParentProductId*',
                    'ChildProductId': 'ChildProductId*',
                    'ProductComponentGroupId': 'ProductComponentGroupId',
                    'MinQuantity': 'MinQuantity',
                    'MaxQuantity': 'MaxQuantity',
                    'Quantity': 'Quantity',
                    'IsComponentRequired': 'IsComponentRequired',
                    'Sequence': 'Sequence',
                    'DoesBundlePriceIncludeChild': 'DoesBundlePriceIncludeChild'
                    # Removed External_ID__c custom field
                }
            },
            'PricebookEntry': {
                'sobject': 'PricebookEntry',
                'csv_file': '20_PricebookEntry.csv',
                'required_fields': ['Product2Id', 'Pricebook2Id', 'UnitPrice'],
                'field_map': {
                    'Product2Id': 'Product2Id',
                    'Pricebook2Id': 'Pricebook2Id',
                    'UnitPrice': 'UnitPrice',
                    'IsActive': 'IsActive'
                    # Removed ExternalId__c custom field
                }
            }
        }
    
    def get_pass1_ids(self):
        """Get the IDs from Pass 1 import results."""
        # These would normally be read from a file or API
        # For now, using the IDs from the successful import
        return {
            'ProductCatalog': ['0ZSdp00000007kfGAA', '0ZSdp00000007kgGAA'],
            'ProductCategory': ['0ZGdp00000007JFGAY', '0ZGdp00000007JGGAY', '0ZGdp00000007JHGAY', '0ZGdp00000007JIGAY'],
            'Product2': [
                '01tdp000006HfphAAC', '01tdp000006HfpiAAC', '01tdp000006HfpjAAC', '01tdp000006HfpkAAC',
                '01tdp000006HfplAAC', '01tdp000006HfpmAAC', '01tdp000006HfpnAAC', '01tdp000006HfpoAAC',
                '01tdp000006HfppAAC', '01tdp000006HfpqAAC', '01tdp000006HfprAAC', '01tdp000006HfpsAAC',
                '01tdp000006HfptAAC', '01tdp000006HfpuAAC', '01tdp000006HfpvAAC', '01tdp000006HfpwAAC',
                '01tdp000006HfpxAAC', '01tdp000006HfpyAAC', '01tdp000006HfpzAAC', '01tdp000006Hfq0AAC',
                '01tdp000006Hfq1AAC'
            ],
            'AttributeDefinition': ['0tjdp00000000XtAAI', '0tjdp00000000XuAAI', '0tjdp00000000XvAAI'],
            'Pricebook2': ['01sdp000001Uf5BAAS', '01sdp000001Uf5CAAS', '01sdp000001Uf5DAAS']
        }
        
    def read_csv(self, csv_path):
        """Read CSV file and return rows as list of dictionaries."""
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if any(v.strip() for v in row.values() if v):
                    records.append(row)
        return records
    
    def clean_value(self, value):
        """Clean and convert values for JSON."""
        if value is None or value == '':
            return None
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        try:
            # Try to convert to number
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value.strip()
    
    def generate_tree_json(self, object_config):
        """Generate JSON tree file for a specific object."""
        csv_path = self.csv_dir / object_config['csv_file']
        if not csv_path.exists():
            print(f"Warning: CSV file not found: {csv_path}")
            return
        
        records = self.read_csv(csv_path)
        if not records:
            print(f"Warning: No records found in {csv_path}")
            return
        
        json_records = []
        for idx, row in enumerate(records):
            # Create record with attributes
            record = {
                "attributes": {
                    "type": object_config['sobject'],
                    "referenceId": f"{object_config['sobject']}_Ref{idx+1}"
                }
            }
            
            # Map fields
            for json_field, csv_field in object_config['field_map'].items():
                value = row.get(csv_field, '')
                cleaned_value = self.clean_value(value)
                
                # Only add non-null values
                if cleaned_value is not None:
                    record[json_field] = cleaned_value
            
            # Check required fields
            missing_required = []
            for req_field in object_config['required_fields']:
                if req_field not in record or record[req_field] is None:
                    missing_required.append(req_field)
            
            if missing_required:
                print(f"Warning: Record {idx+1} in {object_config['sobject']} missing required fields: {missing_required}")
                # Skip records with missing required fields in pass2
                continue
            
            json_records.append(record)
        
        # Write JSON file with proper structure
        output_path = self.json_output_dir / f"{object_config['sobject']}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"records": json_records}, f, indent=2)
        
        print(f"Generated {output_path} with {len(json_records)} records")
    
    def generate_all_pass2_files(self):
        """Generate all pass2 JSON tree files."""
        pass2_objects = [
            'ProductSellingModel',
            'ProductCategoryProduct',
            'ProductAttributeDefinition',
            'ProductRelatedComponent',
            'PricebookEntry'
        ]
        
        for obj_name in pass2_objects:
            if obj_name in self.field_mappings:
                self.generate_tree_json(self.field_mappings[obj_name])
    
    def generate_import_plan(self):
        """Generate the import plan JSON file for pass2."""
        plan = []
        
        # Define import order for pass2
        pass2_order = [
            'ProductSellingModel',
            'ProductCategoryProduct',
            'ProductAttributeDefinition',
            'ProductRelatedComponent',
            'PricebookEntry'
        ]
        
        for obj_name in pass2_order:
            if obj_name in self.field_mappings:
                plan.append({
                    "sobject": obj_name,
                    "files": [f"../json_tree_output/pass2/{obj_name}.json"]
                })
        
        # Write import plan
        plan_path = Path('plans_tree/pass2_import.json')
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2)
        
        print(f"Generated import plan: {plan_path}")

def main():
    # Set paths
    csv_dir = Path('data/csv_output/pass2')
    json_output_dir = Path('json_tree_output/pass2')
    
    # Create generator and run
    generator = Pass2JSONTreeGeneratorNoCustom(csv_dir, json_output_dir)
    generator.generate_all_pass2_files()
    generator.generate_import_plan()

if __name__ == '__main__':
    main()