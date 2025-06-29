#!/usr/bin/env python3
"""
Revenue Cloud Complete Upload Process
A repeatable, error-free process for uploading Revenue Cloud data.
"""

import pandas as pd
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time

class RevenueCloudUploadProcess:
    def __init__(self):
        self.workbook_path = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.target_org = 'fortradp2'
        self.temp_dir = Path('data/temp_csv')
        self.temp_dir.mkdir(exist_ok=True)
        
        # Define upload order based on dependencies
        self.upload_sequence = [
            # 1. Foundation Objects
            {
                'name': 'ProductCatalog',
                'sheet': '11_ProductCatalog',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Product catalog containers'
            },
            {
                'name': 'ProductCategory',
                'sheet': '12_ProductCategory',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Product categorization'
            },
            
            # 2. Classification and Attributes
            {
                'name': 'ProductClassification',
                'sheet': '08_ProductClassification',
                'external_id': 'Code',
                'method': 'upsert',
                'description': 'Product classification definitions'
            },
            {
                'name': 'AttributeCategory',
                'sheet': '10_AttributeCategory',
                'external_id': 'Code',
                'method': 'upsert',
                'description': 'Attribute categorization'
            },
            {
                'name': 'AttributePicklist',
                'sheet': '14_AttributePicklist',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Picklist definitions for attributes'
            },
            {
                'name': 'AttributeDefinition',
                'sheet': '09_AttributeDefinition',
                'external_id': 'Code',
                'method': 'upsert',
                'description': 'Attribute definitions'
            },
            
            # 3. Product Setup
            {
                'name': 'ProductSellingModel',
                'sheet': '15_ProductSellingModel',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Selling model definitions'
            },
            {
                'name': 'Product2',
                'sheet': '13_Product2',
                'external_id': 'Id',
                'method': 'smart_upsert',  # Special handling for Type field
                'description': 'Product records'
            },
            {
                'name': 'Pricebook2',
                'sheet': '19_Pricebook2',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Price books'
            },
            
            # 4. Product Relationships
            {
                'name': 'ProductAttributeDefinition',
                'sheet': '17_ProductAttributeDef',
                'external_id': 'Id',
                'method': 'smart_upsert',  # Special handling for AttributeCategoryId
                'description': 'Product-attribute relationships'
            },
            {
                'name': 'AttributePicklistValue',
                'sheet': '18_AttributePicklistValue',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Picklist values'
            },
            {
                'name': 'ProductCategoryProduct',
                'sheet': '26_ProductCategoryProduct',
                'external_id': 'Id',
                'method': 'insert_only',  # Junction object - insert only
                'description': 'Product-category assignments'
            },
            
            # 5. Pricing and Components
            {
                'name': 'PricebookEntry',
                'sheet': '20_PricebookEntry',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Product pricing'
            },
            {
                'name': 'ProductComponentGroup',
                'sheet': '14_ProductComponentGroup',
                'external_id': 'Code',  # Use Code as external ID
                'method': 'smart_upsert',
                'description': 'Component groupings for bundles'
            },
            {
                'name': 'ProductRelatedComponent',
                'sheet': '25_ProductRelatedComponent',
                'external_id': 'Id',
                'method': 'upsert',
                'description': 'Bundle component relationships'
            }
        ]
        
        self.results = []
    
    def validate_sheet(self, sheet_name):
        """Validate that a sheet exists and has data."""
        try:
            df = pd.read_excel(self.workbook_path, sheet_name=sheet_name)
            if df.empty:
                return False, "No data in sheet"
            return True, f"{len(df)} records found"
        except Exception as e:
            return False, str(e)
    
    def smart_upsert(self, object_config, df):
        """Handle special upsert cases for specific objects."""
        object_name = object_config['name']
        
        if object_name == 'Product2':
            # Handle Product2 Type field - separate new vs existing
            if 'Id' in df.columns:
                has_id = df[df['Id'].notna()].copy()
                no_id = df[df['Id'].isna()].copy()
                
                # Remove Type field from updates
                if 'Type' in has_id.columns and len(has_id) > 0:
                    has_id = has_id.drop('Type', axis=1)
                
                return self.process_split_records(object_config, no_id, has_id)
            
        elif object_name == 'ProductAttributeDefinition':
            # Handle AttributeCategoryId - can't update after creation
            if 'Id' in df.columns:
                has_id = df[df['Id'].notna()].copy()
                no_id = df[df['Id'].isna()].copy()
                
                # Remove AttributeCategoryId from updates
                if 'AttributeCategoryId' in has_id.columns and len(has_id) > 0:
                    has_id = has_id.drop('AttributeCategoryId', axis=1)
                
                return self.process_split_records(object_config, no_id, has_id)
            
        elif object_name == 'ProductComponentGroup':
            # Use Code as external ID for proper upsert
            return self.standard_upsert(object_config, df)
        
        # Default to standard upsert
        return self.standard_upsert(object_config, df)
    
    def process_split_records(self, object_config, new_records, existing_records):
        """Process records split into new and existing."""
        object_name = object_config['name']
        success = True
        message_parts = []
        
        # Insert new records
        if len(new_records) > 0:
            if 'Id' in new_records.columns:
                new_records = new_records.drop('Id', axis=1)
            
            csv_file = self.temp_dir / f'{object_name}_insert.csv'
            new_records.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'import', 'bulk',
                '--sobject', object_name,
                '--file', str(csv_file),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                message_parts.append(f"Inserted {len(new_records)} new")
            else:
                success = False
                message_parts.append(f"Insert failed for {len(new_records)} records")
        
        # Update existing records
        if len(existing_records) > 0:
            csv_file = self.temp_dir / f'{object_name}_update.csv'
            existing_records.to_csv(csv_file, index=False)
            
            cmd = [
                'sf', 'data', 'upsert', 'bulk',
                '--sobject', object_name,
                '--external-id', 'Id',
                '--file', str(csv_file),
                '--target-org', self.target_org,
                '--wait', '10'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                message_parts.append(f"Updated {len(existing_records)} existing")
            else:
                success = False
                message_parts.append(f"Update failed for {len(existing_records)} records")
        
        return success, "; ".join(message_parts)
    
    def standard_upsert(self, object_config, df):
        """Perform standard upsert operation."""
        object_name = object_config['name']
        external_id = object_config['external_id']
        
        csv_file = self.temp_dir / f'{object_name}.csv'
        df.to_csv(csv_file, index=False)
        
        cmd = [
            'sf', 'data', 'upsert', 'bulk',
            '--sobject', object_name,
            '--external-id', external_id,
            '--file', str(csv_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Upserted {len(df)} records"
        else:
            # Extract error summary - get the actual error, not the warning
            error_lines = result.stderr.strip().split('\n') if result.stderr else []
            error_msg = "Unknown error"
            for line in error_lines:
                if 'Error' in line and 'Warning' not in line:
                    error_msg = line
                    break
            return False, error_msg
    
    def insert_only(self, object_config, df):
        """Handle insert-only objects (like junction objects)."""
        object_name = object_config['name']
        
        # Only process records without IDs
        if 'Id' in df.columns:
            new_records = df[df['Id'].isna()].copy()
            if 'Id' in new_records.columns:
                new_records = new_records.drop('Id', axis=1)
        else:
            new_records = df
        
        if len(new_records) == 0:
            return True, "No new records to insert"
        
        csv_file = self.temp_dir / f'{object_name}_insert.csv'
        new_records.to_csv(csv_file, index=False)
        
        cmd = [
            'sf', 'data', 'import', 'bulk',
            '--sobject', object_name,
            '--file', str(csv_file),
            '--target-org', self.target_org,
            '--wait', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, f"Inserted {len(new_records)} new records"
        else:
            return False, f"Insert failed"
    
    def process_object(self, object_config):
        """Process a single object upload."""
        print(f"\n{object_config['name']}:")
        print(f"  {object_config['description']}")
        
        # Validate sheet
        valid, message = self.validate_sheet(object_config['sheet'])
        if not valid:
            print(f"  ✗ Validation failed: {message}")
            self.results.append({
                'object': object_config['name'],
                'status': 'Failed',
                'message': f"Validation: {message}"
            })
            return False
        
        # Read data
        df = pd.read_excel(self.workbook_path, sheet_name=object_config['sheet'])
        
        # Clean column names
        df.columns = df.columns.str.replace('*', '', regex=False).str.strip()
        
        # Process based on method
        if object_config['method'] == 'smart_upsert':
            success, message = self.smart_upsert(object_config, df)
        elif object_config['method'] == 'insert_only':
            success, message = self.insert_only(object_config, df)
        else:
            success, message = self.standard_upsert(object_config, df)
        
        # Report result
        status = "Success" if success else "Failed"
        print(f"  {'✓' if success else '✗'} {status}: {message}")
        
        self.results.append({
            'object': object_config['name'],
            'status': status,
            'message': message
        })
        
        return success
    
    def run_upload(self):
        """Run the complete upload process."""
        print("=" * 80)
        print("REVENUE CLOUD UPLOAD PROCESS")
        print("=" * 80)
        print(f"Workbook: {self.workbook_path}")
        print(f"Target Org: {self.target_org}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Process each object in sequence
        success_count = 0
        failed_count = 0
        
        for object_config in self.upload_sequence:
            if self.process_object(object_config):
                success_count += 1
            else:
                failed_count += 1
            
            # Brief pause between objects
            time.sleep(1)
        
        # Summary
        print("\n" + "=" * 80)
        print("UPLOAD SUMMARY")
        print("=" * 80)
        print(f"✓ Successful: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.results:
            status_icon = "✓" if result['status'] == "Success" else "✗"
            print(f"  {status_icon} {result['object']}: {result['message']}")
        
        # Cleanup
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        return success_count, failed_count

def main():
    uploader = RevenueCloudUploadProcess()
    uploader.run_upload()

if __name__ == '__main__':
    main()