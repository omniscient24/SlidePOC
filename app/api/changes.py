from flask import Blueprint, request, jsonify, session
from ..utils.auth import login_required
from ..utils.db import get_db_connection
from ..services.salesforce_service import salesforce_service
import json
from datetime import datetime

changes_bp = Blueprint('changes', __name__)

@changes_bp.route('/api/edit/changes/validate', methods=['POST'])
@login_required
def validate_changes():
    """Validate pending changes before commit"""
    try:
        data = request.json
        changes = data.get('changes', [])
        deletions = data.get('deletions', [])
        additions = data.get('additions', [])  # Add support for additions
        org_id = data.get('org_id', session.get('active_connection_id'))
        
        # TODO: Implement validation logic
        # For now, return success
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for any obvious issues
        for change in changes:
            if not change.get('nodeId'):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing nodeId in change: {change}")
        
        for deletion in deletions:
            if not deletion.get('nodeId'):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing nodeId in deletion: {deletion}")
        
        # Validate additions
        for addition in additions:
            if not addition.get('name'):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing name in addition: {addition}")
            if not addition.get('type'):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing type in addition: {addition}")
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@changes_bp.route('/api/edit/changes/commit', methods=['POST'])
@login_required
def commit_changes():
    """Commit pending changes to Salesforce"""
    try:
        data = request.json
        changes = data.get('changes', [])
        deletions = data.get('deletions', [])
        additions = data.get('additions', [])  # Add support for additions
        org_id = data.get('org_id', session.get('active_connection_id'))
        
        # Debug logging
        print(f"[COMMIT] Received request with {len(changes)} changes, {len(deletions)} deletions, {len(additions)} additions")
        if additions:
            print(f"[COMMIT] Additions: {json.dumps(additions, indent=2)}")
        
        if not org_id:
            return jsonify({'error': 'No organization selected'}), 400
        
        # Get the active connection alias
        connection_alias = salesforce_service.get_active_connection(session)
        if not connection_alias:
            return jsonify({'error': 'No active Salesforce connection'}), 400
            
        # Verify connection is valid
        if not salesforce_service.verify_connection(session):
            return jsonify({'error': 'Salesforce connection is invalid or expired'}), 400
        
        # Process results
        results = {
            'success': True,
            'changes_processed': 0,
            'deletions_processed': 0,
            'additions_processed': 0,  # Add counter for additions
            'addition_details': [],     # Add details for created records
            'errors': []
        }
        
        # Process field changes
        for change in changes:
            try:
                node_id = change.get('nodeId')
                node_type = change.get('nodeType', 'unknown')
                field_name = change.get('fieldName')
                new_value = change.get('newValue')
                
                # Map node type to Salesforce object
                object_name = salesforce_service._get_object_name_from_node_type(node_type)
                if not object_name:
                    raise ValueError(f"Unknown node type: {node_type}")
                
                # Update the record in Salesforce
                success, result = salesforce_service.update_record(
                    object_name,
                    node_id,
                    {field_name: new_value},
                    connection_alias
                )
                
                if success:
                    results['changes_processed'] += 1
                else:
                    results['errors'].append({
                        'type': 'change',
                        'nodeId': node_id,
                        'field': field_name,
                        'error': result
                    })
                    
            except Exception as e:
                results['errors'].append({
                    'type': 'change',
                    'nodeId': change.get('nodeId'),
                    'error': str(e)
                })
        
        # Process deletions
        for deletion in deletions:
            try:
                node_id = deletion.get('nodeId')
                node_type = deletion.get('nodeType')
                delete_children = deletion.get('deleteChildren', False)
                new_parent_id = deletion.get('newParentId')
                
                # Use the unified delete method
                success, result = salesforce_service.delete_with_children(
                    node_id,
                    node_type,
                    delete_children,
                    new_parent_id,
                    connection_alias
                )
                
                if success:
                    results['deletions_processed'] += 1
                    # Add details about what was deleted
                    if isinstance(result, dict):
                        results['deletion_details'] = results.get('deletion_details', [])
                        results['deletion_details'].append(result)
                else:
                    results['errors'].append({
                        'type': 'deletion',
                        'nodeId': node_id,
                        'error': result
                    })
                    
            except Exception as e:
                results['errors'].append({
                    'type': 'deletion',
                    'nodeId': deletion.get('nodeId'),
                    'error': str(e)
                })
        
        # Process additions
        print(f"[COMMIT] Processing {len(additions)} additions...")
        for addition in additions:
            try:
                node_type = addition.get('type', 'unknown')
                temp_id = addition.get('tempId') or addition.get('nodeId')
                print(f"[COMMIT] Processing addition: {addition.get('name')} (type: {node_type}, tempId: {temp_id})")
                
                # Map node type to Salesforce object
                object_name = salesforce_service._get_object_name_from_node_type(node_type)
                if not object_name:
                    raise ValueError(f"Unknown node type: {node_type}")
                
                # Prepare record data based on node type
                record_data = {
                    'Name': addition.get('name', ''),
                    'Description': addition.get('description', ''),
                    'IsActive': addition.get('isActive', True)
                }
                
                # Add type-specific fields
                if node_type == 'catalog':
                    record_data['Code'] = addition.get('code', '')
                    record_data['CatalogType'] = addition.get('catalogType', 'Sales')
                    if addition.get('effectiveStartDate'):
                        record_data['EffectiveStartDate'] = addition['effectiveStartDate']
                    if addition.get('effectiveEndDate'):
                        record_data['EffectiveEndDate'] = addition['effectiveEndDate']
                elif node_type in ['category', 'subcategory']:
                    # Categories need a parent catalog ID
                    # First check if catalogId was directly provided (lowercase from frontend)
                    if addition.get('catalogId'):
                        record_data['CatalogId'] = addition['catalogId']
                        print(f"[COMMIT] Using provided catalogId: {record_data['CatalogId']}")
                    else:
                        # Fall back to determining from parent
                        parent_node_id = addition.get('parentId')
                        if parent_node_id:
                            # We need to determine if parent is a catalog or category
                            # If it's a catalog, use it as CatalogId
                            # If it's a category, we need to find its catalog
                            
                            # Query the parent to determine its type
                            parent_query = f"SELECT Id, CatalogId FROM ProductCategory WHERE Id = '{parent_node_id}' LIMIT 1"
                            success, parent_results = salesforce_service.query(parent_query, connection_alias)
                            
                            if success and parent_results:
                                # Parent is a category, use its CatalogId
                                record_data['CatalogId'] = parent_results[0].get('CatalogId')
                                record_data['ParentCategoryId'] = parent_node_id
                            else:
                                # Parent might be a catalog, use it directly
                                record_data['CatalogId'] = parent_node_id
                    
                    if addition.get('parentCategoryId'):
                        # Override if explicitly provided
                        record_data['ParentCategoryId'] = addition['parentCategoryId']
                    
                    # Ensure we have a CatalogId for categories
                    if 'CatalogId' not in record_data:
                        print(f"[COMMIT] WARNING: No CatalogId found for category {addition.get('name')}")
                        raise ValueError(f"CatalogId is required for ProductCategory creation")
                elif node_type == 'product':
                    record_data['ProductCode'] = addition.get('productCode', '')
                    # Add additional product fields
                    if addition.get('stockKeepingUnit'):
                        record_data['StockKeepingUnit'] = addition['stockKeepingUnit']
                    if addition.get('family'):
                        record_data['Family'] = addition['family']
                
                # Create the record in Salesforce
                print(f"[COMMIT] Creating {object_name} record with data: {json.dumps(record_data, indent=2)}")
                success, result = salesforce_service.create_record(
                    object_name,
                    record_data,
                    connection_alias
                )
                print(f"[COMMIT] Create result - Success: {success}, Result: {result}")
                print(f"[COMMIT] Result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"[COMMIT] Result keys: {list(result.keys())}")
                    print(f"[COMMIT] Result content: {json.dumps(result, indent=2)}")
                
                if success:
                    results['additions_processed'] += 1
                    # Extract the new record ID from the result
                    real_id = None
                    if isinstance(result, dict):
                        real_id = result.get('id') or result.get('Id')
                        print(f"[COMMIT] Checking for ID in result: id={result.get('id')}, Id={result.get('Id')}")
                        if not real_id and result.get('results'):
                            # Handle bulk upload result format
                            upload_results = result.get('results', [])
                            print(f"[COMMIT] Found upload results array with {len(upload_results)} items")
                            if upload_results and len(upload_results) > 0:
                                real_id = upload_results[0].get('Id')
                                print(f"[COMMIT] Extracted ID from upload results: {real_id}")
                    
                    print(f"[COMMIT] After ID extraction - node_type: {node_type}, real_id: {real_id}, productCode: {addition.get('productCode')}")
                    
                    # For products, we may need to query for the ID if bulk upload doesn't return it
                    if node_type == 'product' and not real_id and addition.get('productCode'):
                        print(f"[COMMIT] Querying for product ID using ProductCode: {addition['productCode']}")
                        query = f"SELECT Id FROM Product2 WHERE ProductCode = '{addition['productCode']}' LIMIT 1"
                        query_success, query_results = salesforce_service.query(query, connection_alias)
                        if query_success and query_results:
                            real_id = query_results[0].get('Id')
                            print(f"[COMMIT] Found product ID: {real_id}")
                        else:
                            print(f"[COMMIT] Failed to find product by ProductCode: {addition['productCode']}")
                    
                    # For products, create ProductCategoryProduct junction record
                    print(f"[COMMIT] Junction check - node_type: {node_type}, real_id: {real_id}, categoryId: {addition.get('categoryId')}")
                    if node_type == 'product' and real_id and addition.get('categoryId'):
                        print(f"[COMMIT] Creating ProductCategoryProduct junction record for product {real_id} in category {addition['categoryId']}")
                        junction_data = {
                            'ProductId': real_id,
                            'ProductCategoryId': addition['categoryId']
                        }
                        junction_success, junction_result = salesforce_service.create_record(
                            'ProductCategoryProduct',
                            junction_data,
                            connection_alias
                        )
                        if junction_success:
                            print(f"[COMMIT] Successfully created ProductCategoryProduct junction record")
                        else:
                            print(f"[COMMIT] Warning: Failed to create ProductCategoryProduct junction: {junction_result}")
                            # We don't fail the whole operation if junction creation fails
                            results['warnings'] = results.get('warnings', [])
                            results['warnings'].append({
                                'type': 'junction',
                                'product_id': real_id,
                                'category_id': addition['categoryId'],
                                'error': junction_result
                            })
                    
                    results['addition_details'].append({
                        'tempId': temp_id,
                        'real_id': real_id,
                        'name': addition.get('name'),
                        'type': node_type,
                        'parent_id': addition.get('parentId') or addition.get('parentCategoryId') or addition.get('categoryId')
                    })
                else:
                    results['errors'].append({
                        'type': 'addition',
                        'nodeId': temp_id,
                        'name': addition.get('name'),
                        'error': result
                    })
                    
            except Exception as e:
                results['errors'].append({
                    'type': 'addition',
                    'nodeId': addition.get('tempId') or addition.get('nodeId'),
                    'name': addition.get('name'),
                    'error': str(e)
                })
        
        # Log to change history
        conn = get_db_connection()
        cursor = conn.cursor()
        
        batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Log changes
        for change in changes:
            cursor.execute("""
                INSERT INTO change_history 
                (user_id, org_id, node_id, node_type, operation_type, 
                 field_changes, status, batch_id)
                VALUES (?, ?, ?, ?, 'update', ?, 'committed', ?)
            """, (
                session.get('user_id', 'unknown'),
                org_id,
                change.get('nodeId'),
                change.get('nodeType', 'unknown'),
                json.dumps(change),
                batch_id
            ))
        
        # Log deletions
        for deletion in deletions:
            cursor.execute("""
                INSERT INTO change_history 
                (user_id, org_id, node_id, node_type, operation_type, 
                 field_changes, status, batch_id)
                VALUES (?, ?, ?, ?, 'delete', ?, 'committed', ?)
            """, (
                session.get('user_id', 'unknown'),
                org_id,
                deletion.get('nodeId'),
                deletion.get('nodeType', 'unknown'),
                json.dumps(deletion),
                batch_id
            ))
        
        # Log additions
        for i, addition in enumerate(additions):
            # Get the real ID from addition_details if available
            real_id = None
            if i < len(results['addition_details']):
                real_id = results['addition_details'][i].get('real_id')
            
            cursor.execute("""
                INSERT INTO change_history 
                (user_id, org_id, node_id, node_type, operation_type, 
                 field_changes, status, batch_id)
                VALUES (?, ?, ?, ?, 'insert', ?, 'committed', ?)
            """, (
                session.get('user_id', 'unknown'),
                org_id,
                real_id or addition.get('tempId') or addition.get('nodeId'),
                addition.get('type', 'unknown'),
                json.dumps(addition),
                batch_id
            ))
        
        conn.commit()
        conn.close()
        
        if results['errors']:
            results['success'] = False
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@changes_bp.route('/api/edit/changes/history', methods=['GET'])
@login_required
def get_change_history():
    """Get change history for the current org"""
    try:
        org_id = request.args.get('org_id', session.get('active_connection_id'))
        limit = int(request.args.get('limit', 50))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, user_id, node_id, node_type, operation_type,
                field_changes, status, created_at, batch_id
            FROM change_history
            WHERE org_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (org_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        history = []
        for row in results:
            history.append({
                'id': row[0],
                'user_id': row[1],
                'node_id': row[2],
                'node_type': row[3],
                'operation_type': row[4],
                'field_changes': json.loads(row[5]) if row[5] else {},
                'status': row[6],
                'created_at': row[7],
                'batch_id': row[8]
            })
        
        return jsonify({
            'history': history,
            'total': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500