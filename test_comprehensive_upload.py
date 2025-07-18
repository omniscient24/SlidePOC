#!/usr/bin/env python3
"""
Comprehensive test of upload functionality
Tests all major scenarios and edge cases
"""
import os
import sys
import pandas as pd
from pathlib import Path
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.upload_service import upload_service

def test_scenario(name: str, test_func):
    """Run a test scenario and report results"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    try:
        result = test_func()
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"\nResult: {status}")
        return result
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_boolean_transformation():
    """Test that boolean values are transformed to picklist values"""
    # Create test data
    test_data = pd.DataFrame({
        'Id': ['', ''],
        'Name': ['Test Active', 'Test Inactive'],
        'Code': ['TEST1', 'TEST2'],
        'Status': [True, False]
    })
    
    # Save to temporary file
    test_file = 'test_boolean.xlsx'
    test_data.to_excel(test_file, index=False, sheet_name='Sheet1')
    
    try:
        # Prepare CSV
        csv_path = upload_service._prepare_csv_for_upload(test_file, 'ProductClassification')
        
        # Read the CSV
        df_csv = pd.read_csv(csv_path)
        
        # Check transformations
        print(f"Original Status values: {test_data['Status'].tolist()}")
        print(f"Transformed Status values: {df_csv['Status'].tolist()}")
        
        # Verify transformation
        success = (df_csv['Status'].tolist() == ['Active', 'Inactive'])
        
        # Cleanup
        Path(test_file).unlink()
        Path(csv_path).unlink()
        
        return success
        
    except Exception as e:
        Path(test_file).unlink(missing_ok=True)
        raise e

def test_readonly_field_exclusion():
    """Test that read-only fields are excluded"""
    # Test ProductCatalog with NumberOfCategories
    csv_path = upload_service._prepare_csv_for_upload(
        str(upload_service.workbook_path),
        'ProductCatalog'
    )
    
    try:
        # Read the CSV
        df_csv = pd.read_csv(csv_path)
        
        # Check that NumberOfCategories is excluded
        print(f"CSV columns: {list(df_csv.columns)}")
        
        success = 'NumberOfCategories' not in df_csv.columns
        
        # Cleanup
        Path(csv_path).unlink()
        
        return success
        
    except Exception as e:
        Path(csv_path).unlink(missing_ok=True)
        raise e

def test_spreadsheet_only_fields():
    """Test that spreadsheet-only fields are excluded"""
    # Test Product2 with Type, CanRamp, UsageModelType
    csv_path = upload_service._prepare_csv_for_upload(
        str(upload_service.workbook_path),
        'Product2'
    )
    
    try:
        # Read the CSV
        df_csv = pd.read_csv(csv_path)
        
        # Check that spreadsheet-only fields are excluded
        print(f"CSV columns: {list(df_csv.columns)}")
        
        excluded_fields = ['Type', 'CanRamp', 'UsageModelType']
        success = all(field not in df_csv.columns for field in excluded_fields)
        
        print(f"Excluded fields: {excluded_fields}")
        print(f"Successfully excluded: {success}")
        
        # Cleanup
        Path(csv_path).unlink()
        
        return success
        
    except Exception as e:
        Path(csv_path).unlink(missing_ok=True)
        raise e

def test_null_value_handling():
    """Test that empty values are converted to NULL"""
    # Create test data with empty values
    test_data = pd.DataFrame({
        'Id': ['123', '456'],
        'Name': ['Test1', 'Test2'],
        'Description': ['Has value', ''],  # Empty string
        'Code': ['', 'CODE2']  # Empty string
    })
    
    # Save to temporary file
    test_file = 'test_null.xlsx'
    test_data.to_excel(test_file, index=False, sheet_name='Sheet1')
    
    try:
        # Prepare CSV
        csv_path = upload_service._prepare_csv_for_upload(test_file)
        
        # Read the CSV and check for None values
        df_csv = pd.read_csv(csv_path, keep_default_na=False)
        
        print(f"Original Description: {test_data['Description'].tolist()}")
        print(f"CSV Description: {df_csv['Description'].tolist()}")
        
        # In CSV, None values are saved as empty strings
        success = df_csv.iloc[1]['Description'] == '' and df_csv.iloc[0]['Code'] == ''
        
        # Cleanup
        Path(test_file).unlink()
        Path(csv_path).unlink()
        
        return success
        
    except Exception as e:
        Path(test_file).unlink(missing_ok=True)
        raise e

def test_column_name_cleaning():
    """Test that column names with asterisks are cleaned"""
    # Create test data with asterisk in column name
    test_data = pd.DataFrame({
        'Id': ['123'],
        'Name*': ['Required Field'],
        'Code': ['TEST']
    })
    
    # Save to temporary file
    test_file = 'test_asterisk.xlsx'
    test_data.to_excel(test_file, index=False, sheet_name='Sheet1')
    
    try:
        # Prepare CSV
        csv_path = upload_service._prepare_csv_for_upload(test_file)
        
        # Read the CSV
        df_csv = pd.read_csv(csv_path)
        
        print(f"Original columns: {list(test_data.columns)}")
        print(f"Cleaned columns: {list(df_csv.columns)}")
        
        # Check that asterisk was removed
        success = 'Name' in df_csv.columns and 'Name*' not in df_csv.columns
        
        # Cleanup
        Path(test_file).unlink()
        Path(csv_path).unlink()
        
        return success
        
    except Exception as e:
        Path(test_file).unlink(missing_ok=True)
        raise e

def test_workbook_sheets():
    """Test that correct sheets are used for each object"""
    object_mappings = [
        ('ProductCatalog', '11_ProductCatalog'),
        ('ProductCategory', '12_ProductCategory'),
        ('ProductClassification', '08_ProductClassification'),
        ('Product2', '13_Product2')
    ]
    
    all_success = True
    
    for object_name, expected_sheet in object_mappings:
        sheet_name = upload_service.object_sheet_mapping.get(object_name)
        if sheet_name == expected_sheet:
            print(f"✅ {object_name} → {sheet_name}")
        else:
            print(f"❌ {object_name} → {sheet_name} (expected {expected_sheet})")
            all_success = False
    
    return all_success

def main():
    """Run all tests"""
    tests = [
        ("Boolean to Picklist Transformation", test_boolean_transformation),
        ("Read-only Field Exclusion", test_readonly_field_exclusion),
        ("Spreadsheet-only Field Exclusion", test_spreadsheet_only_fields),
        ("NULL Value Handling", test_null_value_handling),
        ("Column Name Cleaning", test_column_name_cleaning),
        ("Workbook Sheet Mapping", test_workbook_sheets)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_scenario(test_name, test_func)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())