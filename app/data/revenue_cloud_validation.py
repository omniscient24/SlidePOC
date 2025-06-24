#!/usr/bin/env python3
"""
Revenue Cloud Data Validation Module
Provides comprehensive validation for migration data.
"""

import pandas as pd
import re
from datetime import datetime
from pathlib import Path

class DataValidator:
    def __init__(self, workbook_path):
        self.workbook_path = Path(workbook_path)
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
        # Define validation rules for each object
        self.validation_rules = {
            'Product2': {
                'required_fields': ['Name', 'ProductCode'],
                'unique_fields': ['ProductCode', 'StockKeepingUnit'],
                'field_formats': {
                    'ProductCode': r'^[A-Z0-9\-_]+$',
                    'StockKeepingUnit': r'^[A-Z0-9\-_]+$'
                },
                'field_lengths': {
                    'Name': 255,
                    'ProductCode': 255,
                    'Description': 4000
                }
            },
            'ProductCategory': {
                'required_fields': ['Name', 'Code'],
                'unique_fields': ['Code'],
                'parent_child': {
                    'parent_field': 'ParentCategoryId',
                    'self_field': 'Id'
                }
            },
            'AttributeDefinition': {
                'required_fields': ['Name', 'Code'],
                'unique_fields': ['Code'],
                'field_formats': {
                    'Code': r'^[A-Z0-9_]+$'
                }
            },
            'PricebookEntry': {
                'required_fields': ['Pricebook2Id', 'Product2Id', 'UnitPrice'],
                'numeric_fields': {
                    'UnitPrice': {'min': 0, 'max': 999999999}
                },
                'relationships': {
                    'Product2Id': 'Product2',
                    'Pricebook2Id': 'Pricebook2'
                }
            },
            'ProductAttributeDefinition': {
                'required_fields': ['Product2Id', 'AttributeDefinitionId'],
                'relationships': {
                    'Product2Id': 'Product2',
                    'AttributeDefinitionId': 'AttributeDefinition',
                    'AttributeCategoryId': 'AttributeCategory'
                }
            },
            'ProductRelatedComponent': {
                'required_fields': ['ParentProductId', 'ChildProductId'],
                'numeric_fields': {
                    'MinQuantity': {'min': 0, 'max': 999999},
                    'MaxQuantity': {'min': 0, 'max': 999999}
                },
                'custom_validations': ['validate_quantity_range']
            }
        }
    
    def validate_all(self):
        """Run all validations on the workbook."""
        print("Starting comprehensive data validation...")
        
        # Load all sheets
        xl_file = pd.ExcelFile(self.workbook_path)
        sheet_object_mapping = {
            '13_Product2': 'Product2',
            '12_ProductCategory': 'ProductCategory',
            '09_AttributeDefinition': 'AttributeDefinition',
            '20_PricebookEntry': 'PricebookEntry',
            '17_ProductAttributeDef': 'ProductAttributeDefinition',
            '25_ProductRelatedComponent': 'ProductRelatedComponent'
        }
        
        for sheet_name, object_name in sheet_object_mapping.items():
            if sheet_name in xl_file.sheet_names:
                print(f"\nValidating {object_name}...")
                df = pd.read_excel(self.workbook_path, sheet_name=sheet_name)
                self.validate_object(object_name, df)
        
        return self.get_validation_summary()
    
    def validate_object(self, object_name, df):
        """Validate a specific object's data."""
        if object_name not in self.validation_rules:
            return
        
        rules = self.validation_rules[object_name]
        results = {
            'total_records': len(df),
            'errors': [],
            'warnings': []
        }
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False).str.strip()
        
        # 1. Check required fields
        if 'required_fields' in rules:
            self.validate_required_fields(df, rules['required_fields'], object_name, results)
        
        # 2. Check unique fields
        if 'unique_fields' in rules:
            self.validate_unique_fields(df, rules['unique_fields'], object_name, results)
        
        # 3. Check field formats
        if 'field_formats' in rules:
            self.validate_field_formats(df, rules['field_formats'], object_name, results)
        
        # 4. Check field lengths
        if 'field_lengths' in rules:
            self.validate_field_lengths(df, rules['field_lengths'], object_name, results)
        
        # 5. Check numeric fields
        if 'numeric_fields' in rules:
            self.validate_numeric_fields(df, rules['numeric_fields'], object_name, results)
        
        # 6. Check relationships
        if 'relationships' in rules:
            self.validate_relationships(df, rules['relationships'], object_name, results)
        
        # 7. Run custom validations
        if 'custom_validations' in rules:
            for validation_func in rules['custom_validations']:
                if hasattr(self, validation_func):
                    getattr(self, validation_func)(df, object_name, results)
        
        self.validation_results[object_name] = results
    
    def validate_required_fields(self, df, required_fields, object_name, results):
        """Check for missing required fields."""
        for field in required_fields:
            if field in df.columns:
                missing = df[df[field].isna() | (df[field] == '')]
                if len(missing) > 0:
                    error = f"Missing required field '{field}' in {len(missing)} records"
                    results['errors'].append(error)
                    self.errors.append(f"{object_name}: {error}")
            else:
                error = f"Required column '{field}' not found"
                results['errors'].append(error)
                self.errors.append(f"{object_name}: {error}")
    
    def validate_unique_fields(self, df, unique_fields, object_name, results):
        """Check for duplicate values in unique fields."""
        for field in unique_fields:
            if field in df.columns:
                # Check for duplicates (excluding empty values)
                non_empty = df[df[field].notna() & (df[field] != '')]
                duplicates = non_empty[non_empty.duplicated(subset=[field], keep=False)]
                
                if len(duplicates) > 0:
                    duplicate_values = duplicates[field].unique()
                    error = f"Duplicate values in unique field '{field}': {', '.join(map(str, duplicate_values[:5]))}"
                    if len(duplicate_values) > 5:
                        error += f" and {len(duplicate_values) - 5} more"
                    results['errors'].append(error)
                    self.errors.append(f"{object_name}: {error}")
    
    def validate_field_formats(self, df, field_formats, object_name, results):
        """Validate field format using regex patterns."""
        for field, pattern in field_formats.items():
            if field in df.columns:
                # Check non-empty values against pattern
                non_empty = df[df[field].notna() & (df[field] != '')]
                if len(non_empty) > 0:
                    invalid = non_empty[~non_empty[field].astype(str).str.match(pattern)]
                    if len(invalid) > 0:
                        warning = f"Invalid format in field '{field}' for {len(invalid)} records"
                        results['warnings'].append(warning)
                        self.warnings.append(f"{object_name}: {warning}")
    
    def validate_field_lengths(self, df, field_lengths, object_name, results):
        """Check field length constraints."""
        for field, max_length in field_lengths.items():
            if field in df.columns:
                # Check string length
                non_empty = df[df[field].notna() & (df[field] != '')]
                if len(non_empty) > 0:
                    too_long = non_empty[non_empty[field].astype(str).str.len() > max_length]
                    if len(too_long) > 0:
                        error = f"Field '{field}' exceeds maximum length ({max_length}) in {len(too_long)} records"
                        results['errors'].append(error)
                        self.errors.append(f"{object_name}: {error}")
    
    def validate_numeric_fields(self, df, numeric_fields, object_name, results):
        """Validate numeric field ranges."""
        for field, constraints in numeric_fields.items():
            if field in df.columns:
                numeric_values = pd.to_numeric(df[field], errors='coerce')
                
                # Check for non-numeric values
                non_numeric = df[numeric_values.isna() & df[field].notna()]
                if len(non_numeric) > 0:
                    error = f"Non-numeric values in numeric field '{field}' for {len(non_numeric)} records"
                    results['errors'].append(error)
                    self.errors.append(f"{object_name}: {error}")
                
                # Check min/max constraints
                if 'min' in constraints:
                    below_min = numeric_values < constraints['min']
                    if below_min.any():
                        error = f"Values below minimum ({constraints['min']}) in field '{field}'"
                        results['errors'].append(error)
                        self.errors.append(f"{object_name}: {error}")
                
                if 'max' in constraints:
                    above_max = numeric_values > constraints['max']
                    if above_max.any():
                        error = f"Values above maximum ({constraints['max']}) in field '{field}'"
                        results['errors'].append(error)
                        self.errors.append(f"{object_name}: {error}")
    
    def validate_relationships(self, df, relationships, object_name, results):
        """Validate foreign key relationships."""
        # This is a simplified check - in a real scenario, you'd check against actual org data
        for field, related_object in relationships.items():
            if field in df.columns:
                non_empty = df[df[field].notna() & (df[field] != '')]
                if len(non_empty) > 0:
                    # Check if IDs follow Salesforce format
                    invalid_ids = non_empty[~non_empty[field].astype(str).str.match(r'^[a-zA-Z0-9]{15,18}$')]
                    if len(invalid_ids) > 0:
                        warning = f"Invalid Salesforce ID format in field '{field}' for {len(invalid_ids)} records"
                        results['warnings'].append(warning)
                        self.warnings.append(f"{object_name}: {warning}")
    
    def validate_quantity_range(self, df, object_name, results):
        """Custom validation for quantity ranges."""
        if 'MinQuantity' in df.columns and 'MaxQuantity' in df.columns:
            # Check that MinQuantity <= MaxQuantity
            both_present = df[(df['MinQuantity'].notna()) & (df['MaxQuantity'].notna())]
            if len(both_present) > 0:
                invalid_range = both_present[both_present['MinQuantity'] > both_present['MaxQuantity']]
                if len(invalid_range) > 0:
                    error = f"MinQuantity > MaxQuantity in {len(invalid_range)} records"
                    results['errors'].append(error)
                    self.errors.append(f"{object_name}: {error}")
    
    def get_validation_summary(self):
        """Get a summary of all validation results."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'workbook': str(self.workbook_path),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'objects': self.validation_results,
            'can_proceed': len(self.errors) == 0
        }
        
        return summary
    
    def generate_validation_report(self, output_file=None):
        """Generate a detailed validation report."""
        if not output_file:
            output_file = f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(output_file, 'w') as f:
            f.write("REVENUE CLOUD DATA VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Workbook: {self.workbook_path}\n\n")
            
            if len(self.errors) == 0 and len(self.warnings) == 0:
                f.write("✓ No issues found! Data is ready for migration.\n")
            else:
                if self.errors:
                    f.write(f"ERRORS ({len(self.errors)})\n")
                    f.write("-" * 40 + "\n")
                    for error in self.errors:
                        f.write(f"✗ {error}\n")
                    f.write("\n")
                
                if self.warnings:
                    f.write(f"WARNINGS ({len(self.warnings)})\n")
                    f.write("-" * 40 + "\n")
                    for warning in self.warnings:
                        f.write(f"⚠ {warning}\n")
                    f.write("\n")
            
            f.write("\nOBJECT DETAILS\n")
            f.write("-" * 80 + "\n")
            
            for object_name, results in self.validation_results.items():
                f.write(f"\n{object_name}:\n")
                f.write(f"  Total Records: {results['total_records']}\n")
                f.write(f"  Errors: {len(results['errors'])}\n")
                f.write(f"  Warnings: {len(results['warnings'])}\n")
        
        return output_file

def validate_workbook(workbook_path):
    """Convenience function to validate a workbook."""
    validator = DataValidator(workbook_path)
    summary = validator.validate_all()
    
    print("\nValidation Summary:")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    print(f"Can Proceed: {'Yes' if summary['can_proceed'] else 'No'}")
    
    if not summary['can_proceed']:
        print("\n⚠️  Errors must be resolved before migration!")
    
    return summary

if __name__ == '__main__':
    # Test validation
    workbook = 'data/Revenue_Cloud_Complete_Upload_Template.xlsx'
    if Path(workbook).exists():
        validator = DataValidator(workbook)
        summary = validator.validate_all()
        report_file = validator.generate_validation_report()
        print(f"\nValidation report saved to: {report_file}")