"""
Salesforce Upload Service
Handles uploading data to Salesforce and updating the workbook with results
"""
import subprocess
import json
import pandas as pd
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from config.settings.app_config import CLI_COMMAND, DATA_ROOT
from app.services.sync_service import sync_service
from config.upload_field_config import SPREADSHEET_ONLY_FIELDS, FIELD_TRANSFORMATIONS

class UploadService:
    """Service for uploading data to Salesforce and updating workbook"""
    
    def __init__(self):
        self.workbook_path = DATA_ROOT / 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx'
        self.upload_log_dir = DATA_ROOT / 'upload-logs'
        self.upload_log_dir.mkdir(exist_ok=True)
        
        # Reuse object to sheet mapping from sync service
        self.object_sheet_mapping = sync_service.object_sheet_mapping
    
    def upload_to_salesforce(self, file_path: str, object_name: str, operation: str,
                           external_id: str, connection_alias: str) -> Tuple[bool, Dict]:
        """
        Upload data to Salesforce and update workbook with results
        
        Args:
            file_path: Path to the file to upload
            object_name: Salesforce object API name
            operation: Operation type (insert, update, upsert)
            external_id: External ID field for upsert
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            print(f"[UPLOAD] Starting upload for {object_name}")
            
            # Validate connection alias
            if not connection_alias:
                return False, {'error': 'No active connection alias. Please ensure you are connected to Salesforce.'}
            
            # Convert Excel to CSV if needed
            csv_path = self._prepare_csv_for_upload(file_path, object_name)
            if not csv_path:
                return False, {'error': 'Failed to prepare file for upload'}
            
            # Perform the upload using Salesforce CLI
            upload_result = self._execute_salesforce_upload(
                csv_path, object_name, operation, external_id, connection_alias
            )
            
            # Check for complete failure (no success at all)
            if not upload_result['success'] and not upload_result.get('partial_success'):
                return False, upload_result
            
            # If successful (including partial success), update the workbook with any new IDs or changes
            if operation in ['insert', 'upsert']:
                self._update_workbook_with_results(object_name, upload_result, connection_alias)
            
            # Save upload log
            self._save_upload_log(object_name, operation, upload_result)
            
            # Return success for both full and partial success
            return upload_result.get('success', False) or upload_result.get('partial_success', False), upload_result
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False, {'error': str(e)}
    
    def _prepare_csv_for_upload(self, file_path: str, object_name: str = None) -> Optional[str]:
        """Convert Excel to CSV for Salesforce CLI upload"""
        try:
            path = Path(file_path)
            
            # Check if this is the main workbook
            if path.name == 'Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx' and object_name:
                # Use the object to sheet mapping to get the right sheet
                sheet_name = self.object_sheet_mapping.get(object_name)
                if sheet_name:
                    print(f"[UPLOAD] Reading sheet '{sheet_name}' for object '{object_name}'")
                    df = pd.read_excel(path, sheet_name=sheet_name)
                else:
                    print(f"[WARN] No sheet mapping found for object '{object_name}', reading first sheet")
                    df = pd.read_excel(path, sheet_name=0)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                # For other Excel files, read the first sheet
                df = pd.read_excel(path, sheet_name=0)
            else:
                df = pd.read_csv(path)
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Clean column names - remove asterisks and other special characters that indicate required fields
            df.columns = df.columns.str.replace('*', '', regex=False)
            df.columns = df.columns.str.strip()  # Remove any leading/trailing spaces
            
            print(f"[UPLOAD] Cleaned column names: {list(df.columns)}")
            
            # Replace empty strings with None (null) for Salesforce
            # This ensures empty cells are treated as NULL rather than empty strings
            df = df.replace('', None)
            df = df.where(pd.notnull(df), None)
            
            print(f"[UPLOAD] Replaced empty values with NULL for proper Salesforce handling")
            
            # Apply field transformations (e.g., boolean to picklist conversions)
            if object_name in FIELD_TRANSFORMATIONS:
                transformations = FIELD_TRANSFORMATIONS[object_name]
                for field_name, transform_func in transformations.items():
                    if field_name in df.columns:
                        print(f"[UPLOAD] Applying transformation to {field_name} field")
                        
                        # Special handling for Product2 field generation that needs row context
                        if object_name == 'Product2' and field_name in ['ProductCode', 'StockKeepingUnit']:
                            # Apply row-based transformation for Product2 fields
                            df[field_name] = df.apply(lambda row: transform_func(row[field_name], row.get('Name', '')), axis=1)
                        else:
                            # Standard single-field transformation
                            df[field_name] = df[field_name].apply(transform_func)
                        
                        print(f"[UPLOAD] Transformed values in {field_name}: {df[field_name].unique()}")
            
            # Remove spreadsheet-only fields that shouldn't be uploaded
            # These are fields that exist in the workbook for user reference but aren't actual Salesforce fields
            if object_name in SPREADSHEET_ONLY_FIELDS:
                fields_to_exclude = SPREADSHEET_ONLY_FIELDS[object_name]
                existing_columns = df.columns.tolist()
                columns_to_remove = [col for col in fields_to_exclude if col in existing_columns]
                
                if columns_to_remove:
                    print(f"[UPLOAD] Excluding spreadsheet-only fields from {object_name}: {columns_to_remove}")
                    df = df.drop(columns=columns_to_remove)
            
            # Create CSV file
            # Check if we already have .upload.csv suffix to avoid double suffix
            if path.suffix == '.csv' and path.stem.endswith('.upload'):
                csv_path = path
            else:
                csv_path = path.with_suffix('.upload.csv')
            df.to_csv(csv_path, index=False)
            
            print(f"[UPLOAD] Prepared CSV with {len(df)} records")
            return str(csv_path)
            
        except Exception as e:
            print(f"[ERROR] Failed to prepare CSV: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _execute_salesforce_upload(self, csv_path: str, object_name: str, 
                                 operation: str, external_id: str, 
                                 connection_alias: str) -> Dict:
        """Execute the actual upload to Salesforce using CLI"""
        try:
            # Build the CLI command based on operation
            if operation == 'insert':
                cmd = [
                    CLI_COMMAND, 'data', 'import', 'bulk',
                    '--sobject', object_name,
                    '--file', csv_path,
                    '--target-org', connection_alias,
                    '--wait', '10',  # Wait up to 10 minutes
                    '--json'
                ]
            elif operation == 'update':
                cmd = [
                    CLI_COMMAND, 'data', 'update', 'bulk',
                    '--sobject', object_name,
                    '--file', csv_path,
                    '--target-org', connection_alias,
                    '--wait', '10',  # Wait up to 10 minutes
                    '--json'
                ]
            else:  # upsert
                cmd = [
                    CLI_COMMAND, 'data', 'upsert', 'bulk',
                    '--sobject', object_name,
                    '--file', csv_path,
                    '--external-id', external_id or 'Id',
                    '--target-org', connection_alias,
                    '--wait', '10',  # Wait up to 10 minutes
                    '--json'
                ]
            
            print(f"[UPLOAD] Executing: {' '.join(str(x) for x in cmd if x is not None)}")
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"[ERROR] Upload failed with return code {result.returncode}")
                print(f"[ERROR] STDERR: {result.stderr}")
                print(f"[ERROR] STDOUT: {result.stdout}")
                
                # Try to parse error from JSON response
                try:
                    error_data = json.loads(result.stdout)
                    error_name = error_data.get('name', '')
                    
                    # Check if this is a FailedRecordDetailsError (partial failure)
                    if error_name == 'FailedRecordDetailsError' and 'actions' in error_data:
                        # Extract job ID from the actions
                        import re
                        job_id_match = re.search(r'--job-id ([a-zA-Z0-9]+)', error_data.get('actions', [''])[0])
                        if job_id_match:
                            job_id = job_id_match.group(1)
                            
                            # Parse the message to get counts
                            message = error_data.get('message', '')
                            failed_match = re.search(r'failed to process (\d+) records', message)
                            records_failed = int(failed_match.group(1)) if failed_match else 0
                            
                            # Get the actual job results
                            job_cmd = [
                                CLI_COMMAND, 'data', 'bulk', 'results',
                                '--job-id', job_id,
                                '--target-org', connection_alias,
                                '--json'
                            ]
                            
                            job_result = subprocess.run(job_cmd, capture_output=True, text=True, timeout=60)
                            
                            # Parse job data to get total records
                            try:
                                job_data = json.loads(job_result.stdout)
                                job_info = job_data.get('result', {})
                                records_processed = job_info.get('numberRecordsProcessed', records_failed)
                            except:
                                # Estimate processed records
                                records_processed = records_failed * 2  # Rough estimate
                            
                            # Build partial success result
                            result = {
                                'success': True,
                                'partial_success': True,
                                'job_id': job_id,
                                'records_processed': records_processed,
                                'records_failed': records_failed,
                                'records_created': 0,
                                'message': f'Processed {records_processed} records, {records_failed} failed'
                            }
                            
                            # Get failure details
                            failure_details = self._get_bulk_job_failures(job_id, connection_alias)
                            if failure_details:
                                result['failure_details'] = failure_details
                                result['message'] = self._format_failure_message(failure_details, records_processed, records_failed)
                            
                            return result
                    
                    error_msg = error_data.get('message', 'Upload failed')
                except:
                    error_msg = result.stderr or 'Upload failed'
                
                return {
                    'success': False,
                    'error': error_msg,
                    'details': result.stdout
                }
            
            # Parse the success response
            try:
                data = json.loads(result.stdout)
                
                # Extract results based on operation type
                if operation == 'upsert':
                    # Bulk upsert returns job info
                    job_id = data.get('result', {}).get('id')
                    records_processed = data.get('result', {}).get('numberRecordsProcessed', 0)
                    records_failed = data.get('result', {}).get('numberRecordsFailed', 0)
                    records_created = data.get('result', {}).get('numberRecordsCreated', 0)
                    
                    result = {
                        'success': True,
                        'job_id': job_id,
                        'records_processed': records_processed,
                        'records_failed': records_failed,
                        'records_created': records_created,
                        'message': f'Processed {records_processed} records, {records_failed} failed'
                    }
                    
                    # If there were failures, try to get details
                    if records_failed > 0:
                        failure_details = self._get_bulk_job_failures(job_id, connection_alias)
                        if failure_details:
                            result['failure_details'] = failure_details
                            result['message'] = self._format_failure_message(failure_details, records_processed, records_failed)
                        
                        # Still consider it a success if some records succeeded
                        result['partial_success'] = records_processed > records_failed
                    
                    return result
                else:
                    # Other operations
                    return {
                        'success': True,
                        'result': data.get('result', {}),
                        'message': 'Upload completed successfully'
                    }
                    
            except json.JSONDecodeError:
                print(f"[ERROR] Failed to parse upload response")
                return {
                    'success': False,
                    'error': 'Failed to parse upload response'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Upload timeout - operation took too long'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload error: {str(e)}'
            }
    
    def _update_workbook_with_results(self, object_name: str, upload_result: Dict, 
                                    connection_alias: str):
        """After successful upload, sync the data back to update the workbook"""
        try:
            print(f"[UPLOAD] Updating workbook with results for {object_name}")
            
            # Check if we had any successful records or duplicate errors with IDs
            records_processed = upload_result.get('records_processed', 0)
            records_failed = upload_result.get('records_failed', 0)
            records_succeeded = records_processed - records_failed
            
            # Also check for duplicate errors that provide existing IDs
            duplicate_ids = {}
            if 'failure_details' in upload_result:
                for error_type, details in upload_result['failure_details'].items():
                    if 'existing_ids' in details:
                        duplicate_ids.update(details['existing_ids'])
            
            if records_succeeded > 0 or duplicate_ids:
                print(f"[UPLOAD] {records_succeeded} records succeeded, updating workbook...")
                
                # For bulk operations, we need to parse the success records CSV
                job_id = upload_result.get('job_id')
                if job_id:
                    success_file = f"{job_id}-success-records.csv"
                    if Path(success_file).exists():
                        # Read the success records to get the new IDs
                        df_success = pd.read_csv(success_file)
                        
                        # Update the workbook directly with the new IDs
                        if 'sf__Created' in df_success.columns and 'sf__Id' in df_success.columns:
                            # Get the sheet name for this object
                            sheet_name = sync_service.object_sheet_mapping.get(object_name)
                            if sheet_name:
                                # Read the current workbook
                                workbook_path = self.workbook_path
                                with pd.ExcelFile(workbook_path) as xls:
                                    # Read all sheets
                                    all_sheets = {sheet: pd.read_excel(xls, sheet_name=sheet) 
                                                for sheet in xls.sheet_names}
                                
                                # Update the specific sheet
                                if sheet_name in all_sheets:
                                    df_sheet = all_sheets[sheet_name]
                                    
                                    # For each created record, update the ID in the sheet
                                    for _, row in df_success[df_success['sf__Created'] == 'true'].iterrows():
                                        # Find the row by matching other fields (e.g., Name)
                                        if 'Name' in row and pd.notna(row['Name']):
                                            # Check for Name column (with or without asterisk)
                                            name_col = None
                                            if 'Name' in df_sheet.columns:
                                                name_col = 'Name'
                                            elif 'Name*' in df_sheet.columns:
                                                name_col = 'Name*'
                                            
                                            if name_col:
                                                mask = df_sheet[name_col] == row['Name']
                                                if mask.any():
                                                    df_sheet.loc[mask, 'Id'] = row['sf__Id']
                                                    print(f"[UPLOAD] Updated ID for {row['Name']}: {row['sf__Id']}")
                                    
                                    # Also update IDs from duplicate errors
                                    if duplicate_ids:
                                        print(f"[UPLOAD] Processing {len(duplicate_ids)} duplicate record IDs...")
                                        for name, existing_id in duplicate_ids.items():
                                            # Find the row by name
                                            name_col = None
                                            if 'Name' in df_sheet.columns:
                                                name_col = 'Name'
                                            elif 'Name*' in df_sheet.columns:
                                                name_col = 'Name*'
                                            
                                            if name_col:
                                                mask = df_sheet[name_col] == name
                                                if mask.any():
                                                    df_sheet.loc[mask, 'Id'] = existing_id
                                                    print(f"[UPLOAD] Updated ID for duplicate {name}: {existing_id}")
                                    
                                    # Save the updated workbook
                                    all_sheets[sheet_name] = df_sheet
                                    with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
                                        for sheet, df in all_sheets.items():
                                            df.to_excel(writer, sheet_name=sheet, index=False)
                                    
                                    print(f"[UPLOAD] Workbook updated with new IDs")
                                    
                                    # Apply formatting
                                    sync_service._apply_workbook_formatting(str(workbook_path))
                                    
                        # Clean up the CSV files
                        Path(success_file).unlink(missing_ok=True)
                        failed_file = f"{job_id}-failed-records.csv"
                        Path(failed_file).unlink(missing_ok=True)
                else:
                    # For non-bulk operations, use sync to get the latest data
                    print(f"[UPLOAD] Using sync service to update workbook")
                    success, sync_result = sync_service.sync_objects([object_name], connection_alias)
                    
                    if success:
                        print(f"[UPLOAD] Workbook updated successfully via sync")
                    else:
                        print(f"[WARN] Failed to update workbook via sync: {sync_result}")
            else:
                print(f"[UPLOAD] No successful records to update in workbook")
                
        except Exception as e:
            print(f"[ERROR] Failed to update workbook: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_upload_log(self, object_name: str, operation: str, result: Dict):
        """Save upload results to a log file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = self.upload_log_dir / f'upload_{object_name}_{operation}_{timestamp}.json'
            
            with open(log_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'object': object_name,
                    'operation': operation,
                    'result': result
                }, f, indent=2)
                
            print(f"[UPLOAD] Upload log saved to {log_file}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save upload log: {e}")
    
    def _get_bulk_job_failures(self, job_id: str, connection_alias: str) -> Optional[Dict]:
        """Get detailed failure information from a bulk job"""
        try:
            # Run the command to get job results
            cmd = [
                CLI_COMMAND, 'data', 'bulk', 'results',
                '--job-id', job_id,
                '--target-org', connection_alias,
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse the CSV files that were created
                failed_file = f"{job_id}-failed-records.csv"
                if Path(failed_file).exists():
                    df = pd.read_csv(failed_file)
                    
                    # Group errors by type
                    error_summary = {}
                    for _, row in df.iterrows():
                        error = row.get('sf__Error', 'Unknown error')
                        # Extract the main error type
                        if 'INVALID_FIELD_FOR_INSERT_UPDATE' in error:
                            # Extract field name
                            import re
                            match = re.search(r'Unable to create/update fields: ([^.]+)', error)
                            if match:
                                field = match.group(1).strip()
                                key = f"Field permission issue: {field}"
                                if key not in error_summary:
                                    error_summary[key] = {
                                        'count': 0,
                                        'message': f"The field '{field}' cannot be updated. This may be due to field-level security settings or the field being read-only.",
                                        'example_records': []
                                    }
                                error_summary[key]['count'] += 1
                                if len(error_summary[key]['example_records']) < 3:
                                    error_summary[key]['example_records'].append(row.get('Name', row.get('Id', 'Unknown')))
                        elif 'DUPLICATE_VALUE' in error:
                            # Extract the duplicate field and existing ID
                            import re
                            field_match = re.search(r'duplicate value found: (\w+)', error)
                            id_match = re.search(r'record with id: ([a-zA-Z0-9]+)', error)
                            if field_match and id_match:
                                field = field_match.group(1)
                                existing_id = id_match.group(1)
                                key = f"Duplicate {field}"
                                if key not in error_summary:
                                    error_summary[key] = {
                                        'count': 0,
                                        'message': f"The {field} value already exists in Salesforce",
                                        'example_records': [],
                                        'existing_ids': {}
                                    }
                                error_summary[key]['count'] += 1
                                # Store the existing ID for potential workbook update
                                record_name = row.get('Name', 'Unknown')
                                error_summary[key]['existing_ids'][record_name] = existing_id
                        else:
                            # Generic error
                            key = error.split(':')[0] if ':' in error else 'Other errors'
                            if key not in error_summary:
                                error_summary[key] = {
                                    'count': 0,
                                    'message': error,
                                    'example_records': []
                                }
                            error_summary[key]['count'] += 1
                    
                    # Note: CSV files are cleaned up later in _get_bulk_job_failures
                    pass
                    
                    return error_summary
                    
        except Exception as e:
            print(f"[ERROR] Failed to get bulk job failures: {e}")
        
        return None
    
    def _format_failure_message(self, failure_details: Dict, records_processed: int, records_failed: int) -> str:
        """Format a user-friendly failure message"""
        lines = [f"Upload completed with errors: {records_processed - records_failed} succeeded, {records_failed} failed."]
        
        lines.append("\nError Summary:")
        for error_type, details in failure_details.items():
            lines.append(f"\n• {error_type} ({details['count']} records)")
            lines.append(f"  {details['message']}")
            if details['example_records']:
                lines.append(f"  Affected records: {', '.join(details['example_records'][:3])}")
                if details['count'] > 3:
                    lines.append(f"  ...and {details['count'] - 3} more")
        
        lines.append("\nTo resolve field permission issues:")
        lines.append("1. Check field-level security settings in Setup > Object Manager > [Object] > Fields & Relationships")
        lines.append("2. Ensure your profile or permission set has 'Edit' access to these fields")
        lines.append("3. For Revenue Cloud specific fields, ensure Revenue Cloud features are enabled")
        
        return '\n'.join(lines)

# Singleton instance
upload_service = UploadService()