#!/usr/bin/env python3
"""
Generate JSON tree import files for Salesforce Revenue Cloud migration.
This version removes custom fields to avoid field-level security issues.
"""

import json
import csv
import os
from pathlib import Path

class JSONTreeGeneratorNoCustom:
    def __init__(self, csv_dir, json_output_dir):
        self.csv_dir = Path(csv_dir)
        self.json_output_dir = Path(json_output_dir)
        self.json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Field mappings - removing custom fields
        self.field_mappings = {
            'ProductCatalog': {
                'sobject': 'ProductCatalog',
                'csv_file': '11_ProductCatalog.csv',
                'required_fields': ['Name'],
                'field_map': {
                    'Name': 'Name*',
                    'Code': 'Code',
                    'Description': 'Description',
                    # Removed CatalogType as it has invalid picklist values
                    'EffectiveStartDate': 'EffectiveStartDate',
                    'EffectiveEndDate': 'EffectiveEndDate'
                    # Removed CatalogCode__c
                }
            },
            'ProductCategory': {
                'sobject': 'ProductCategory',
                'csv_file': '12_ProductCategory.csv',
                'required_fields': ['Name'],
                'field_map': {
                    'Name': 'Name',
                    'Code': 'Code',
                    'CatalogId': 'CatalogId',
                    'ParentCategoryId': 'ParentCategoryId',
                    'SortOrder': 'SortOrder'
                    # Removed CategoryCode__c
                },
                'reference_fields': {
                    'CatalogId': 'ProductCatalog.Id',
                    'ParentCategoryId': 'ProductCategory.Id'
                }
            },
            'AttributeDefinition': {
                'sobject': 'AttributeDefinition',
                'csv_file': '09_AttributeDefinition.csv',
                'required_fields': ['Name', 'Code'],
                'field_map': {
                    'Name': 'Name',
                    'Code': 'Code',
                    'DataType': 'DataType',
                    'Description': 'Description',
                    'IsActive': 'IsActive'
                    # Removed ExternalId__c
                }
            },
            'Product2': {
                'sobject': 'Product2',
                'csv_file': '13_Product2.csv',
                'required_fields': ['Name'],
                'field_map': {
                    'Name': 'Name',
                    'ProductCode': 'ProductCode',
                    'Description': 'Description',
                    'IsActive': 'IsActive',
                    'Family': 'Family',
                    'ProductClass': 'ProductClass',
                    'QuantityUnitOfMeasure': 'QuantityUnitOfMeasure',
                    'StockKeepingUnit': 'StockKeepingUnit'
                }
            },
            'Pricebook2': {
                'sobject': 'Pricebook2',
                'csv_file': '19_Pricebook2.csv',
                'required_fields': ['Name'],
                'field_map': {
                    'Name': 'Name',
                    'Description': 'Description',
                    'IsActive': 'IsActive'
                    # Removed ExternalId__c
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
        """Create a reference for lookup fields using @referenceId."""
        if not value or value.strip() == '':
            return None
        # For standard objects like Pricebook2, use direct reference
        if len(value) in [15, 18] and (value.startswith('0') or value.startswith('a')):
            return value  # It's already a Salesforce ID
        # For custom objects, use reference
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
                # Add default values for missing required fields
                for field in missing_required:
                    if field == 'Name':
                        record[field] = f"Default {object_config['sobject']} {idx+1}"
                    elif field == 'Code':
                        record[field] = f"CODE{idx+1:03d}"
            
            json_records.append(record)
        
        # Write JSON file with proper structure
        output_path = self.json_output_dir / f"{object_config['sobject']}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"records": json_records}, f, indent=2)
        
        print(f"Generated {output_path} with {len(json_records)} records")
    
    def generate_all_pass1_files(self):
        """Generate all pass1 JSON tree files."""
        pass1_objects = ['ProductCatalog', 'ProductCategory', 'AttributeDefinition', 'Product2', 'Pricebook2']
        
        for obj_name in pass1_objects:
            if obj_name in self.field_mappings:
                self.generate_tree_json(self.field_mappings[obj_name])
    
    def generate_import_plan(self):
        """Generate the import plan JSON file."""
        plan = []
        
        # Define import order for pass1
        pass1_order = [
            'ProductCatalog',
            'ProductCategory', 
            'AttributeDefinition',
            'Product2',
            'Pricebook2'
        ]
        
        for obj_name in pass1_order:
            if obj_name in self.field_mappings:
                plan.append({
                    "sobject": obj_name,
                    "files": [f"../json_tree_output/pass1/{obj_name}.json"]
                })
        
        # Write import plan
        plan_path = Path('plans_tree/pass1_import.json')
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2)
        
        print(f"Generated import plan: {plan_path}")

def main():
    # Set paths
    csv_dir = Path('data/csv_output/pass1')
    json_output_dir = Path('json_tree_output/pass1')
    
    # Create generator and run
    generator = JSONTreeGeneratorNoCustom(csv_dir, json_output_dir)
    generator.generate_all_pass1_files()
    generator.generate_import_plan()

if __name__ == '__main__':
    main()