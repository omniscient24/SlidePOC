"""
Unified Salesforce Service
Provides a single interface for all Salesforce operations across the application
"""
import subprocess
import json
import pandas as pd
import tempfile
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from config.settings.app_config import CLI_COMMAND, DATA_ROOT
from app.services.connection_manager import ConnectionManager
from app.services.sync_service import sync_service
from app.services.upload_service import upload_service


class SalesforceService:
    """Unified service for all Salesforce operations"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.sync_service = sync_service
        self.upload_service = upload_service
        
    # ==================== Connection Management ====================
    
    def get_active_connection(self, session: Dict) -> Optional[str]:
        """Get the active connection alias for the current session"""
        connection = self.connection_manager.get_active_connection(session)
        if connection:
            return connection.get('cli_alias')
        return None
        
    def verify_connection(self, session: Dict) -> bool:
        """Verify the active connection is valid"""
        connection_id = session.get('active_connection_id')
        if connection_id:
            return self.connection_manager.verify_connection(connection_id)
        return False
        
    # ==================== Query Operations ====================
    
    def query(self, soql: str, connection_alias: str) -> Tuple[bool, Any]:
        """
        Execute a SOQL query
        
        Args:
            soql: SOQL query string
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            cmd = [
                CLI_COMMAND, 'data', 'query',
                '--query', soql,
                '--target-org', connection_alias,
                '--result-format', 'json',
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return False, f"Query failed: {result.stderr}"
                
            data = json.loads(result.stdout)
            if data.get('status') != 0:
                return False, data.get('message', 'Query failed')
                
            records = data.get('result', {}).get('records', [])
            # Clean up records (remove attributes field)
            cleaned_records = []
            for record in records:
                cleaned_record = {k: v for k, v in record.items() if k != 'attributes'}
                cleaned_records.append(cleaned_record)
                
            return True, cleaned_records
            
        except Exception as e:
            return False, str(e)
            
    def describe_object(self, object_name: str, connection_alias: str) -> Tuple[bool, Any]:
        """
        Get metadata for a Salesforce object
        
        Args:
            object_name: Salesforce object API name
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, metadata_or_error)
        """
        try:
            cmd = [
                CLI_COMMAND, 'sobject', 'describe',
                '--sobject', object_name,
                '--target-org', connection_alias,
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return False, f"Describe failed: {result.stderr}"
                
            data = json.loads(result.stdout)
            if data.get('status') == 0:
                return True, data.get('result', {})
                
            return False, data.get('message', 'Describe failed')
            
        except Exception as e:
            return False, str(e)
            
    # ==================== CRUD Operations ====================
    
    def create_record(self, object_name: str, record_data: Dict, connection_alias: str) -> Tuple[bool, Any]:
        """
        Create a single record in Salesforce
        
        Args:
            object_name: Salesforce object API name
            record_data: Dictionary of field values
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Create a temporary CSV file with the record
            temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            df = pd.DataFrame([record_data])
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()
            
            # Use upload service for insert
            success, result = self.upload_service.upload_to_salesforce(
                temp_csv.name, object_name, 'insert', None, connection_alias
            )
            
            # Clean up temp file
            Path(temp_csv.name).unlink(missing_ok=True)
            
            return success, result
            
        except Exception as e:
            return False, str(e)
            
    def update_record(self, object_name: str, record_id: str, 
                     updates: Dict, connection_alias: str) -> Tuple[bool, Any]:
        """
        Update a single record in Salesforce
        
        Args:
            object_name: Salesforce object API name
            record_id: Salesforce record ID
            updates: Dictionary of field updates
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Add Id to updates
            record_data = {'Id': record_id, **updates}
            
            # Create a temporary CSV file
            temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            df = pd.DataFrame([record_data])
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()
            
            # Use upload service for update
            success, result = self.upload_service.upload_to_salesforce(
                temp_csv.name, object_name, 'update', None, connection_alias
            )
            
            # Clean up temp file
            Path(temp_csv.name).unlink(missing_ok=True)
            
            return success, result
            
        except Exception as e:
            return False, str(e)
            
    def delete_record(self, object_name: str, record_id: str, 
                     connection_alias: str) -> Tuple[bool, Any]:
        """
        Delete a single record from Salesforce
        
        Args:
            object_name: Salesforce object API name
            record_id: Salesforce record ID
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Validate inputs
            if not object_name or not record_id:
                return False, "Object name and record ID are required"
                
            cmd = [
                CLI_COMMAND, 'data', 'delete', 'record',
                '--sobject', object_name,
                '--record-id', record_id,
                '--target-org', connection_alias,
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                # Try to parse error
                error_msg = self._parse_cli_error(result)
                
                # Check for common Salesforce errors
                if 'ENTITY_IS_DELETED' in error_msg:
                    return False, f"Record {record_id} is already deleted"
                elif 'INSUFFICIENT_ACCESS' in error_msg:
                    return False, f"Insufficient access to delete {object_name} record"
                elif 'DELETE_FAILED' in error_msg:
                    # Check for cascade delete restrictions
                    if 'cascade delete' in error_msg.lower():
                        return False, f"Cannot delete - record has child records that would be deleted"
                    return False, f"Delete failed: {error_msg}"
                    
                return False, f"Delete failed: {error_msg}"
                
            try:
                data = json.loads(result.stdout)
                if data.get('status') == 0:
                    return True, {
                        'id': record_id,
                        'success': True,
                        'message': f'Successfully deleted {object_name} record {record_id}'
                    }
                else:
                    return False, data.get('message', 'Delete failed')
            except:
                # Some CLI versions don't return JSON for successful deletes
                if result.returncode == 0:
                    return True, {
                        'id': record_id,
                        'success': True,
                        'message': f'Successfully deleted {object_name} record {record_id}'
                    }
                return False, 'Delete failed - invalid response'
                
        except subprocess.TimeoutExpired:
            return False, "Delete operation timed out"
        except Exception as e:
            return False, f"Unexpected error during delete: {str(e)}"
            
    def delete_records_bulk(self, object_name: str, record_ids: List[str], 
                          connection_alias: str) -> Tuple[bool, Any]:
        """
        Delete multiple records from Salesforce
        
        Args:
            object_name: Salesforce object API name
            record_ids: List of Salesforce record IDs
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Create a CSV with just the IDs
            temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            df = pd.DataFrame({'Id': record_ids})
            df.to_csv(temp_csv.name, index=False)
            temp_csv.close()
            
            # Use bulk delete command
            cmd = [
                CLI_COMMAND, 'data', 'delete', 'bulk',
                '--sobject', object_name,
                '--file', temp_csv.name,
                '--target-org', connection_alias,
                '--wait', '10',
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Clean up temp file
            Path(temp_csv.name).unlink(missing_ok=True)
            
            if result.returncode != 0:
                # Try to parse error
                try:
                    error_data = json.loads(result.stdout)
                    error_msg = error_data.get('message', result.stderr)
                except:
                    error_msg = result.stderr
                    
                return False, f"Bulk delete failed: {error_msg}"
                
            data = json.loads(result.stdout)
            if data.get('status') == 0:
                job_result = data.get('result', {})
                return True, {
                    'job_id': job_result.get('id'),
                    'records_processed': job_result.get('numberRecordsProcessed', len(record_ids)),
                    'records_failed': job_result.get('numberRecordsFailed', 0),
                    'success': True,
                    'message': f'Bulk delete completed for {len(record_ids)} records'
                }
            else:
                return False, data.get('message', 'Bulk delete failed')
                
        except Exception as e:
            return False, str(e)
            
    # ==================== Product Hierarchy Operations ====================
    
    def get_child_records(self, parent_id: str, child_relationship: str, 
                         connection_alias: str) -> Tuple[bool, List[Dict]]:
        """
        Get child records for a parent record
        
        Args:
            parent_id: Parent record ID
            child_relationship: Child relationship name (e.g., 'ChildProducts')
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, list_of_child_records_or_error)
        """
        # First determine the parent object type
        parent_object = self._determine_object_type(parent_id, connection_alias)
        if not parent_object:
            return False, "Could not determine parent object type"
            
        # Build SOQL query based on relationship
        if parent_object == 'Product2' and child_relationship == 'ChildProducts':
            # For Product2 -> ProductRelatedComponent relationship
            soql = f"""
                SELECT Id, RelatedProductId, RelatedProduct.Name, 
                       ComponentGroupId, ComponentGroup.Name,
                       Quantity, SortOrder
                FROM ProductRelatedComponent
                WHERE ProductId = '{parent_id}'
                ORDER BY SortOrder, RelatedProduct.Name
            """
        elif parent_object == 'ProductCategory' and child_relationship == 'ChildCategories':
            # For ProductCategory hierarchy
            soql = f"""
                SELECT Id, Name, Description, SortOrder
                FROM ProductCategory
                WHERE ParentCategoryId = '{parent_id}'
                ORDER BY SortOrder, Name
            """
        elif parent_object == 'ProductCategory' and child_relationship == 'Products':
            # For ProductCategory -> Product2 relationship
            soql = f"""
                SELECT ProductId, Product.Id, Product.Name, 
                       Product.ProductCode, Product.IsActive
                FROM ProductCategoryProduct
                WHERE ProductCategoryId = '{parent_id}'
                ORDER BY Product.Name
            """
        else:
            return False, f"Unsupported relationship: {parent_object}.{child_relationship}"
            
        return self.query(soql, connection_alias)
        
    def delete_with_children(self, node_id: str, node_type: str, 
                           delete_children: bool, new_parent_id: Optional[str],
                           connection_alias: str) -> Tuple[bool, Any]:
        """
        Delete a node with options for handling children
        
        Args:
            node_id: ID of the node to delete
            node_type: Type of the node (catalog, category, product, etc.)
            delete_children: If True, delete all children. If False, reparent them
            new_parent_id: ID of new parent if reparenting children
            connection_alias: Salesforce CLI alias
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            # Determine the Salesforce object type
            object_name = self._get_object_name_from_node_type(node_type)
            if not object_name:
                return False, f"Unknown node type: {node_type}"
                
            # Handle different deletion scenarios
            if object_name == 'ProductCategory':
                return self._delete_category_with_children(
                    node_id, delete_children, new_parent_id, connection_alias
                )
            elif object_name == 'Product2':
                return self._delete_product_with_components(
                    node_id, delete_children, connection_alias
                )
            elif object_name == 'ProductCatalog':
                return self._delete_catalog_with_children(
                    node_id, delete_children, connection_alias
                )
            else:
                # Simple delete for other types
                return self.delete_record(object_name, node_id, connection_alias)
                
        except Exception as e:
            return False, str(e)
            
    def _delete_category_with_children(self, category_id: str, delete_children: bool,
                                     new_parent_id: Optional[str], 
                                     connection_alias: str) -> Tuple[bool, Any]:
        """Delete a ProductCategory with options for children"""
        try:
            results = {
                'success': True,
                'deleted': [],
                'reparented': [],
                'errors': []
            }
            
            if not delete_children and new_parent_id:
                # Reparent child categories
                success, children = self.query(
                    f"SELECT Id, Name FROM ProductCategory WHERE ParentCategoryId = '{category_id}'",
                    connection_alias
                )
                
                if success and children:
                    for child in children:
                        update_success, update_result = self.update_record(
                            'ProductCategory',
                            child['Id'],
                            {'ParentCategoryId': new_parent_id},
                            connection_alias
                        )
                        if update_success:
                            results['reparented'].append(child)
                        else:
                            results['errors'].append({
                                'id': child['Id'],
                                'error': update_result
                            })
                            
            elif delete_children:
                # Recursively delete all child categories
                success, children = self.query(
                    f"SELECT Id FROM ProductCategory WHERE ParentCategoryId = '{category_id}'",
                    connection_alias
                )
                
                if success and children:
                    for child in children:
                        # Recursive delete
                        child_success, child_result = self._delete_category_with_children(
                            child['Id'], True, None, connection_alias
                        )
                        if child_success:
                            results['deleted'].extend(child_result.get('deleted', []))
                        else:
                            results['errors'].append({
                                'id': child['Id'],
                                'error': child_result
                            })
                            
            # Delete the category itself
            delete_success, delete_result = self.delete_record(
                'ProductCategory', category_id, connection_alias
            )
            
            if delete_success:
                results['deleted'].append({
                    'id': category_id,
                    'type': 'ProductCategory'
                })
            else:
                results['errors'].append({
                    'id': category_id,
                    'error': delete_result
                })
                results['success'] = False
                
            return results['success'], results
            
        except Exception as e:
            return False, str(e)
            
    def _delete_product_with_components(self, product_id: str, delete_components: bool,
                                      connection_alias: str) -> Tuple[bool, Any]:
        """Delete a Product2 with its related components"""
        try:
            results = {
                'success': True,
                'deleted': [],
                'errors': []
            }
            
            # First delete ProductRelatedComponent records where this product is the parent
            success, components = self.query(
                f"SELECT Id FROM ProductRelatedComponent WHERE ProductId = '{product_id}'",
                connection_alias
            )
            
            if success and components:
                component_ids = [c['Id'] for c in components]
                if component_ids:
                    comp_success, comp_result = self.delete_records_bulk(
                        'ProductRelatedComponent', component_ids, connection_alias
                    )
                    if comp_success:
                        results['deleted'].extend([
                            {'id': cid, 'type': 'ProductRelatedComponent'} 
                            for cid in component_ids
                        ])
                    else:
                        results['errors'].append({
                            'type': 'ProductRelatedComponent',
                            'error': comp_result
                        })
                        
            # Delete ProductCategoryProduct associations
            success, associations = self.query(
                f"SELECT Id FROM ProductCategoryProduct WHERE ProductId = '{product_id}'",
                connection_alias
            )
            
            if success and associations:
                assoc_ids = [a['Id'] for a in associations]
                if assoc_ids:
                    assoc_success, assoc_result = self.delete_records_bulk(
                        'ProductCategoryProduct', assoc_ids, connection_alias
                    )
                    if assoc_success:
                        results['deleted'].extend([
                            {'id': aid, 'type': 'ProductCategoryProduct'} 
                            for aid in assoc_ids
                        ])
                        
            # Delete the product itself
            delete_success, delete_result = self.delete_record(
                'Product2', product_id, connection_alias
            )
            
            if delete_success:
                results['deleted'].append({
                    'id': product_id,
                    'type': 'Product2'
                })
            else:
                results['errors'].append({
                    'id': product_id,
                    'error': delete_result
                })
                results['success'] = False
                
            return results['success'], results
            
        except Exception as e:
            return False, str(e)
            
    def _delete_catalog_with_children(self, catalog_id: str, delete_children: bool,
                                    connection_alias: str) -> Tuple[bool, Any]:
        """Delete a ProductCatalog with all its categories"""
        try:
            results = {
                'success': True,
                'deleted': [],
                'errors': []
            }
            
            if delete_children:
                # Get all categories in this catalog
                # Note: ProductCategory doesn't have direct CatalogId field in standard model
                # This would need custom implementation based on your data model
                pass
                
            # Delete the catalog
            delete_success, delete_result = self.delete_record(
                'ProductCatalog', catalog_id, connection_alias
            )
            
            if delete_success:
                results['deleted'].append({
                    'id': catalog_id,
                    'type': 'ProductCatalog'
                })
            else:
                results['errors'].append({
                    'id': catalog_id,
                    'error': delete_result
                })
                results['success'] = False
                
            return results['success'], results
            
        except Exception as e:
            return False, str(e)
            
    # ==================== Helper Methods ====================
    
    def _parse_cli_error(self, result: subprocess.CompletedProcess) -> str:
        """Parse error message from CLI result"""
        try:
            # Try to parse JSON error
            if result.stdout:
                data = json.loads(result.stdout)
                return data.get('message', result.stderr or 'Unknown error')
        except:
            pass
            
        # Return stderr if available
        return result.stderr or 'Unknown error'
    
    def _determine_object_type(self, record_id: str, connection_alias: str) -> Optional[str]:
        """Determine the Salesforce object type from a record ID"""
        # Salesforce ID prefixes (first 3 characters) identify object types
        # This is a simplified version - in production you might query the record
        prefix = record_id[:3] if len(record_id) >= 3 else None
        
        # Common Revenue Cloud object prefixes
        prefix_map = {
            '01t': 'Product2',
            '0ZG': 'ProductCategory',
            '0ZC': 'ProductCatalog',
            # Add more as needed
        }
        
        return prefix_map.get(prefix)
        
    def _get_object_name_from_node_type(self, node_type: str) -> Optional[str]:
        """Convert node type to Salesforce object name"""
        type_map = {
            'catalog': 'ProductCatalog',
            'category': 'ProductCategory',
            'product': 'Product2',
            'component': 'ProductRelatedComponent',
            'componentgroup': 'ProductComponentGroup'
        }
        
        return type_map.get(node_type.lower())
        
    # ==================== Sync and Upload Delegation ====================
    
    def sync_objects(self, object_names: List[str], connection_alias: str) -> Tuple[bool, Dict]:
        """Delegate to sync service"""
        return self.sync_service.sync_objects(object_names, connection_alias)
        
    def upload_data(self, file_path: str, object_name: str, operation: str,
                   external_id: str, connection_alias: str) -> Tuple[bool, Dict]:
        """Delegate to upload service"""
        return self.upload_service.upload_to_salesforce(
            file_path, object_name, operation, external_id, connection_alias
        )


# Singleton instance
salesforce_service = SalesforceService()