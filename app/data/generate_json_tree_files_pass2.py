#!/usr/bin/env python3
"""
Generate JSON tree import files for pass2 (dependent objects) for Salesforce Revenue Cloud migration.
"""

import json
import csv
import os
from pathlib import Path

class Pass2JSONTreeGenerator:
    def __init__(self, csv_dir, json_output_dir):
        self.csv_dir = Path(csv_dir)
        self.json_output_dir = Path(json_output_dir)
        self.json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Field mappings for pass2 objects (dependent on pass1)
        self.field_mappings = {
            'ProductCategoryProduct': {
                'sobject': 'ProductCategoryProduct',
                'csv_file': '26_ProductCategoryProduct.csv',
                'external_id_field': 'External_ID__c',
                'required_fields': ['ProductId', 'ProductCategoryId'],
                'field_map': {
                    'ProductId': 'ProductId*',  # Note the asterisk in CSV
                    'ProductCategoryId': 'ProductCategoryId*',  # Note the asterisk in CSV
                    'External_ID__c': 'External_ID__c'
                },
                'reference_fields': {
                    'ProductId': 'Product2.Id',  # These are already Salesforce IDs
                    'ProductCategoryId': 'ProductCategory.Id'  # These are already Salesforce IDs
                }
            },
            'ProductAttributeDefinition': {
                'sobject': 'ProductAttributeDefinition',
                'csv_file': '17_ProductAttributeDef.csv',
                'external_id_field': 'Id',  # Using the SF ID as external ID
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
                },
                'reference_fields': {
                    'Product2Id': 'Product2.Id',  # Already a Salesforce ID
                    'AttributeDefinitionId': 'AttributeDefinition.Id',  # Already a Salesforce ID
                    'AttributeCategoryId': 'AttributeCategory.Id'  # Already a Salesforce ID
                }
            },
            'ProductRelatedComponent': {
                'sobject': 'ProductRelatedComponent',
                'csv_file': '25_ProductRelatedComponent.csv',
                'external_id_field': 'External_ID__c',
                'required_fields': ['ParentProductId', 'ChildProductId'],
                'field_map': {
                    'ParentProductId': 'ParentProductId*',  # Note the asterisk
                    'ChildProductId': 'ChildProductId*',  # Note the asterisk
                    'ProductComponentGroupId': 'ProductComponentGroupId',
                    'MinQuantity': 'MinQuantity',
                    'MaxQuantity': 'MaxQuantity',
                    'Quantity': 'Quantity',
                    'IsComponentRequired': 'IsComponentRequired',
                    'Sequence': 'Sequence',
                    'DoesBundlePriceIncludeChild': 'DoesBundlePriceIncludeChild',
                    'External_ID__c': 'External_ID__c'
                },
                'reference_fields': {
                    'ParentProductId': 'Product2.Id',  # Already Salesforce IDs
                    'ChildProductId': 'Product2.Id',  # Already Salesforce IDs
                    'ProductComponentGroupId': 'ProductComponentGroup.Id'  # Already a Salesforce ID
                }
            },
            'ProductSellingModel': {
                'sobject': 'ProductSellingModel',
                'csv_file': '15_ProductSellingModel.csv',
                'external_id_field': 'ModelCode__c',
                'required_fields': ['Name', 'SellingModelType', 'Status'],
                'field_map': {
                    'Name': 'Name',
                    'SellingModelType': 'SellingModelType',
                    'Status': 'Status',
                    'PricingTermUnit': 'PricingTermUnit',
                    'PricingTerm': 'PricingTerm',
                    'ModelCode__c': 'ModelCode__c'
                }
            },
            'PricebookEntry': {
                'sobject': 'PricebookEntry',
                'csv_file': '20_PricebookEntry.csv',
                'external_id_field': 'ExternalId__c',
                'required_fields': ['Product2Id', 'Pricebook2Id', 'UnitPrice'],
                'field_map': {
                    'Product2Id': 'Product2Id',
                    'Pricebook2Id': 'Pricebook2Id',
                    'UnitPrice': 'UnitPrice',
                    'IsActive': 'IsActive',
                    'ExternalId__c': 'ExternalId__c'
                },
                'reference_fields': {
                    'Product2Id': 'Product2.Id',  # Already Salesforce IDs
                    'Pricebook2Id': 'Pricebook2.Id'  # Already Salesforce IDs
                }
            }
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
    
    def create_reference(self, ref_object, ref_external_id, value):
        """Create a reference for lookup fields."""
        if not value or value.strip() == '':
            return None
        # For pass2, most fields contain actual Salesforce IDs (18 chars starting with 0)
        if len(value) in [15, 18] and (value.startswith('0') or value.startswith('a')):
            return value  # It's already a Salesforce ID, use it directly
        # Otherwise create a reference
        return f"@{ref_object}_{value}"
    
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
                
                # Handle reference fields
                if 'reference_fields' in object_config and json_field in object_config['reference_fields']:
                    ref_info = object_config['reference_fields'][json_field].split('.')
                    ref_object = ref_info[0]
                    cleaned_value = self.create_reference(ref_object, ref_info[1], value)
                
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
            'ProductSellingModel',  # This needs to be imported before ProductSellingModelOption
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
            'ProductSellingModel',  # Import this first
            'ProductCategoryProduct',
            'ProductAttributeDefinition',
            'ProductRelatedComponent',
            'PricebookEntry'
        ]
        
        for obj_name in pass2_order:
            if obj_name in self.field_mappings:
                plan.append({
                    "sobject": obj_name,
                    "files": [f"json_tree_output/pass2/{obj_name}.json"]
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
    generator = Pass2JSONTreeGenerator(csv_dir, json_output_dir)
    generator.generate_all_pass2_files()
    generator.generate_import_plan()

if __name__ == '__main__':
    main()