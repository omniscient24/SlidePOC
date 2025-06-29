#!/usr/bin/env python3
"""
Check error details for failed upsert operations.
"""

import subprocess
import json
import pandas as pd
from pathlib import Path

class ErrorChecker:
    def __init__(self):
        self.csv_dir = Path('data/csv_fixed_output')
        
        # Known failed jobs from the output
        self.failed_jobs = [
            ('ProductClassification', 'likely job ID from previous runs'),
            ('AttributeDefinition', 'likely job ID from previous runs'),
            ('AttributeCategory', 'likely job ID from previous runs'),
            ('ProductSellingModel', 'likely job ID from previous runs'),
            ('Product2', 'likely job ID from previous runs'),
            ('Pricebook2', 'likely job ID from previous runs'),
            ('ProductCategoryProduct', 'likely job ID from previous runs'),
            ('PricebookEntry', 'likely job ID from previous runs'),
            ('ProductRelatedComponent', 'likely job ID from previous runs')
        ]
    
    def check_object_fields(self, object_name):
        """Check which fields exist on an object."""
        print(f"\nChecking fields for {object_name}...")
        
        cmd = [
            'sf', 'sobject', 'describe',
            '--sobject', object_name,
            '--target-org', 'fortradp2',
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'fields' in data['result']:
                fields = data['result']['fields']
                field_names = [f['name'] for f in fields if f.get('createable', False)]
                print(f"  Found {len(field_names)} createable fields")
                return field_names
        return []
    
    def analyze_csv_issues(self):
        """Analyze CSV files for potential issues."""
        print("=" * 60)
        print("ANALYZING CSV FILES FOR ISSUES")
        print("=" * 60)
        
        issues = {}
        
        # Check each failed object's CSV
        failed_objects = {
            'ProductClassification': '08_ProductClassification.csv',
            'AttributeDefinition': '09_AttributeDefinition.csv',
            'AttributeCategory': '10_AttributeCategory.csv',
            'ProductSellingModel': '15_ProductSellingModel.csv',
            'Product2': '13_Product2.csv',
            'Pricebook2': '19_Pricebook2.csv',
            'ProductCategoryProduct': '26_ProductCategoryProduct.csv',
            'PricebookEntry': '20_PricebookEntry.csv',
            'ProductRelatedComponent': '25_ProductRelatedComponent.csv'
        }
        
        for object_name, csv_file in failed_objects.items():
            print(f"\n{object_name}:")
            csv_path = self.csv_dir / csv_file
            
            if not csv_path.exists():
                print(f"  ⚠️  CSV file not found")
                continue
            
            # Read CSV
            df = pd.read_csv(csv_path)
            print(f"  Records: {len(df)}")
            print(f"  Columns: {', '.join(df.columns)}")
            
            # Get valid fields from Salesforce
            valid_fields = self.check_object_fields(object_name)
            
            if valid_fields:
                # Check for invalid fields
                invalid_fields = [col for col in df.columns if col not in valid_fields and col != 'Id']
                if invalid_fields:
                    print(f"  ❌ Invalid fields: {', '.join(invalid_fields)}")
                    issues[object_name] = invalid_fields
                
                # Check for missing required fields
                required_fields = self.get_required_fields(object_name)
                missing_required = [f for f in required_fields if f not in df.columns]
                if missing_required:
                    print(f"  ❌ Missing required fields: {', '.join(missing_required)}")
            
            # Check for empty required values
            for col in df.columns:
                if df[col].isna().all():
                    print(f"  ⚠️  Column '{col}' is completely empty")
        
        return issues
    
    def get_required_fields(self, object_name):
        """Get required fields for common objects."""
        required_fields = {
            'ProductClassification': ['Name', 'Code'],
            'AttributeDefinition': ['Name', 'Code', 'Label'],
            'AttributeCategory': ['Name', 'Code'],
            'ProductSellingModel': ['Name', 'SellingModelType', 'Status'],
            'Product2': ['Name'],
            'Pricebook2': ['Name'],
            'ProductCategoryProduct': ['ProductId', 'ProductCategoryId'],
            'PricebookEntry': ['Product2Id', 'Pricebook2Id', 'UnitPrice'],
            'ProductRelatedComponent': ['ParentProductId', 'ChildProductId', 'ProductRelationshipTypeId']
        }
        return required_fields.get(object_name, [])
    
    def check_specific_issues(self):
        """Check specific known issues."""
        print("\n\nCHECKING SPECIFIC ISSUES")
        print("=" * 60)
        
        # Check if ProductRelationshipType exists
        print("\nChecking ProductRelationshipType records...")
        cmd = [
            'sf', 'data', 'query',
            '--query', 'SELECT Id, Name FROM ProductRelationshipType',
            '--target-org', 'fortradp2',
            '--result-format', 'csv'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("ProductRelationshipType records:")
            print(result.stdout)
        
        # Check Product Type field
        print("\nChecking Product2 Type field values...")
        cmd = [
            'sf', 'data', 'query',
            '--query', "SELECT Id, Name, Type FROM Product2 WHERE Name LIKE 'DCS%' LIMIT 5",
            '--target-org', 'fortradp2',
            '--result-format', 'csv'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Product2 Type values:")
            print(result.stdout)

def main():
    checker = ErrorChecker()
    issues = checker.analyze_csv_issues()
    checker.check_specific_issues()
    
    if issues:
        print("\n\nSUMMARY OF ISSUES TO FIX:")
        print("=" * 60)
        for obj, invalid_fields in issues.items():
            print(f"{obj}: Remove fields {invalid_fields}")

if __name__ == '__main__':
    main()