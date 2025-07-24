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
        org_id = data.get('org_id', session.get('active_connection_id'))
        
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