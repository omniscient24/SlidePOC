#!/usr/bin/env python3
"""
Generate JSON tree import files with proper references instead of hardcoded IDs.
"""

import json
import csv
from pathlib import Path
import time

class JSONTreeGeneratorWithRefs:
    def __init__(self, csv_dir, json_output_dir):
        self.csv_dir = Path(csv_dir)
        self.json_output_dir = Path(json_output_dir)
        self.json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track external IDs for creating references
        self.external_ids = {
            'ProductCatalog': {},
            'ProductCategory': {},
            'Product2': {},
            'AttributeDefinition': {}
        }
        
    def read_csv(self, csv_path):
        """Read CSV file and return rows as list of dictionaries."""
        records = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
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
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value.strip()
    
    def generate_pass1(self):
        """Generate Pass 1 files with proper references."""
        
        # 1. ProductCatalog - no dependencies
        catalogs = []
        csv_path = self.csv_dir / '11_ProductCatalog.csv'
        records = self.read_csv(csv_path)
        
        for idx, row in enumerate(records):
            ref_id = f"ProductCatalog_Ref{idx+1}"
            catalog = {
                "attributes": {
                    "type": "ProductCatalog",
                    "referenceId": ref_id
                },
                "Name": row.get('Name*', '').strip(),
                "Code": f"{row.get('Code', '').strip()}_IMPORT_{int(time.time())}_{idx+1}",  # Add timestamp to avoid duplicates
                "Description": row.get('Description', '').strip()
            }
            
            # Store the mapping for later reference
            if row.get('CatalogCode__c'):
                self.external_ids['ProductCatalog'][row['CatalogCode__c']] = ref_id
            
            # Add optional fields
            if row.get('EffectiveStartDate'):
                catalog['EffectiveStartDate'] = row['EffectiveStartDate']
            if row.get('EffectiveEndDate'):
                catalog['EffectiveEndDate'] = row['EffectiveEndDate']
                
            catalogs.append(catalog)
        
        with open(self.json_output_dir / 'ProductCatalog.json', 'w') as f:
            json.dump({"records": catalogs}, f, indent=2)
        print(f"Generated ProductCatalog.json with {len(catalogs)} records")
        
        # 2. ProductCategory - references ProductCatalog
        categories = []
        csv_path = self.csv_dir / '12_ProductCategory.csv'
        records = self.read_csv(csv_path)
        
        # First pass - create all categories
        for idx, row in enumerate(records):
            ref_id = f"ProductCategory_Ref{idx+1}"
            category = {
                "attributes": {
                    "type": "ProductCategory",
                    "referenceId": ref_id
                },
                "Name": row.get('Name', '').strip(),
                "Code": f"{row.get('Code', '').strip()}_IMPORT_{int(time.time())}_{idx+1}"  # Add timestamp to avoid duplicates
            }
            
            # Store mapping
            if row.get('CategoryCode__c'):
                self.external_ids['ProductCategory'][row['CategoryCode__c']] = ref_id
            
            # For now, link all categories to the first catalog
            if catalogs:
                category['CatalogId'] = f"@{catalogs[0]['attributes']['referenceId']}"
            
            # Add sort order
            if row.get('SortOrder'):
                category['SortOrder'] = self.clean_value(row['SortOrder'])
                
            categories.append(category)
        
        with open(self.json_output_dir / 'ProductCategory.json', 'w') as f:
            json.dump({"records": categories}, f, indent=2)
        print(f"Generated ProductCategory.json with {len(categories)} records")
        
        # 3. AttributeDefinition - no dependencies
        attributes = []
        csv_path = self.csv_dir / '09_AttributeDefinition.csv'
        records = self.read_csv(csv_path)
        
        for idx, row in enumerate(records):
            ref_id = f"AttributeDefinition_Ref{idx+1}"
            attr = {
                "attributes": {
                    "type": "AttributeDefinition",
                    "referenceId": ref_id
                },
                "Name": row.get('Name', '').strip(),
                "Code": row.get('Code', '').strip() or f'ATTR{idx+1:03d}',  # Default code if missing or empty
                "Label": row.get('Name', '').strip(),  # Use Name as Label
                "DataType": row.get('DataType', 'Text').strip(),
                "IsActive": self.clean_value(row.get('IsActive', 'true'))
            }
            
            if row.get('Description'):
                attr['Description'] = row['Description'].strip()
                
            # Skip picklist types for now since they need PicklistId
            if attr['DataType'] == 'Picklist':
                continue
                
            attributes.append(attr)
        
        with open(self.json_output_dir / 'AttributeDefinition.json', 'w') as f:
            json.dump({"records": attributes}, f, indent=2)
        print(f"Generated AttributeDefinition.json with {len(attributes)} records")
        
        # 4. Product2 - no dependencies for basic fields
        products = []
        csv_path = self.csv_dir / '13_Product2.csv'
        records = self.read_csv(csv_path)
        
        for idx, row in enumerate(records):
            ref_id = f"Product2_Ref{idx+1}"
            product = {
                "attributes": {
                    "type": "Product2",
                    "referenceId": ref_id
                },
                "Name": row.get('Name', '').strip(),
                "ProductCode": row.get('ProductCode', '').strip(),
                "IsActive": self.clean_value(row.get('IsActive', 'true'))
            }
            
            # Add optional fields
            optional_fields = ['Description', 'Family', 'ProductClass', 'QuantityUnitOfMeasure', 'StockKeepingUnit']
            for field in optional_fields:
                if row.get(field):
                    product[field] = row[field].strip()
                    
            products.append(product)
        
        with open(self.json_output_dir / 'Product2.json', 'w') as f:
            json.dump({"records": products}, f, indent=2)
        print(f"Generated Product2.json with {len(products)} records")
        
        # 5. Pricebook2 - no dependencies
        pricebooks = []
        csv_path = self.csv_dir / '19_Pricebook2.csv'
        records = self.read_csv(csv_path)
        
        for idx, row in enumerate(records):
            ref_id = f"Pricebook2_Ref{idx+1}"
            pricebook = {
                "attributes": {
                    "type": "Pricebook2",
                    "referenceId": ref_id
                },
                "Name": row.get('Name', '').strip(),
                "IsActive": self.clean_value(row.get('IsActive', 'true'))
            }
            
            if row.get('Description'):
                pricebook['Description'] = row['Description'].strip()
                
            pricebooks.append(pricebook)
        
        with open(self.json_output_dir / 'Pricebook2.json', 'w') as f:
            json.dump({"records": pricebooks}, f, indent=2)
        print(f"Generated Pricebook2.json with {len(pricebooks)} records")
        
        # Generate import plan
        plan = [
            {
                "sobject": "ProductCatalog",
                "files": ["../json_tree_output/pass1/ProductCatalog.json"]
            },
            {
                "sobject": "ProductCategory",
                "files": ["../json_tree_output/pass1/ProductCategory.json"]
            },
            {
                "sobject": "AttributeDefinition",
                "files": ["../json_tree_output/pass1/AttributeDefinition.json"]
            },
            {
                "sobject": "Product2",
                "files": ["../json_tree_output/pass1/Product2.json"]
            },
            {
                "sobject": "Pricebook2",
                "files": ["../json_tree_output/pass1/Pricebook2.json"]
            }
        ]
        
        plan_path = Path('plans_tree/pass1_import.json')
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"Generated import plan: {plan_path}")

def main():
    csv_dir = Path('data/csv_output/pass1')
    json_output_dir = Path('json_tree_output/pass1')
    
    generator = JSONTreeGeneratorWithRefs(csv_dir, json_output_dir)
    generator.generate_pass1()

if __name__ == '__main__':
    main()