from flask import Blueprint, request, jsonify, session, abort
from functools import wraps
import sqlite3
import json
from datetime import datetime
from ..utils.auth import login_required, get_current_user_id
from ..utils.db import get_db_connection

edit_permissions_bp = Blueprint('edit_permissions', __name__)

# Permission level hierarchy
PERMISSION_LEVELS = {
    'view_only': 0,
    'edit_basic': 1,
    'edit_structure': 2,
    'delete': 3,
    'full_edit': 4,
    'admin': 5
}

def require_permission(min_level):
    """Decorator to check if user has required permission level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_current_user_id()
            org_id = session.get('active_connection_id')
            
            if not user_id or not org_id:
                abort(401, "Authentication required")
                
            user_permission = get_user_permission(user_id, org_id)
            
            if not user_permission:
                abort(403, "No permissions configured for this user")
                
            if PERMISSION_LEVELS.get(user_permission, 0) < PERMISSION_LEVELS.get(min_level, 0):
                abort(403, f"Insufficient permissions. Required: {min_level}, Current: {user_permission}")
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin():
    """Decorator to check if user has admin permission"""
    return require_permission('admin')

def require_delete():
    """Decorator to check if user has delete permission"""
    return require_permission('delete')

def can_delete(user_id, org_id):
    """Check if user has delete permission"""
    user_permission = get_user_permission(user_id, org_id)
    if not user_permission:
        return False
    
    capabilities = get_permission_capabilities(user_permission)
    return capabilities.get('can_delete', False)

def get_user_permission(user_id, org_id):
    """Get user's permission level for an organization"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT permission_level 
        FROM edit_permissions 
        WHERE user_id = ? AND org_id = ?
    """, (user_id, org_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

@edit_permissions_bp.route('/api/edit/permissions', methods=['GET'])
@login_required
def get_user_permissions():
    """Get current user's edit permissions"""
    try:
        user_id = get_current_user_id()
        org_id = request.args.get('org_id', session.get('active_connection_id'))
        
        if not org_id:
            return jsonify({'error': 'No organization selected'}), 400
            
        permission = get_user_permission(user_id, org_id)
        
        # Get all permission details
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                permission_level,
                created_at,
                updated_at,
                created_by
            FROM edit_permissions 
            WHERE user_id = ? AND org_id = ?
        """, (user_id, org_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Return default view-only permission if not configured
            return jsonify({
                'user_id': user_id,
                'org_id': org_id,
                'permission_level': 'view_only',
                'is_default': True,
                'capabilities': get_permission_capabilities('view_only')
            })
            
        return jsonify({
            'user_id': user_id,
            'org_id': org_id,
            'permission_level': result[0],
            'created_at': result[1],
            'updated_at': result[2],
            'created_by': result[3],
            'capabilities': get_permission_capabilities(result[0])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@edit_permissions_bp.route('/api/edit/permissions', methods=['POST'])
@login_required
@require_admin()
def update_user_permissions():
    """Update user permissions (admin only)"""
    try:
        data = request.json
        target_user_id = data.get('user_id')
        org_id = data.get('org_id', session.get('active_connection_id'))
        permission_level = data.get('permission_level')
        
        # Validate inputs
        if not all([target_user_id, org_id, permission_level]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if permission_level not in PERMISSION_LEVELS:
            return jsonify({'error': f'Invalid permission level. Must be one of: {list(PERMISSION_LEVELS.keys())}'}), 400
            
        # Update permission
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO edit_permissions 
            (user_id, org_id, permission_level, updated_at, created_by)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (target_user_id, org_id, permission_level, get_current_user_id()))
        
        conn.commit()
        
        # Log the action
        log_audit_action(
            'update_permission',
            'edit_permissions',
            target_user_id,
            {
                'target_user': target_user_id,
                'org_id': org_id,
                'permission_level': permission_level
            }
        )
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Permission updated for user {target_user_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@edit_permissions_bp.route('/api/edit/permissions/bulk', methods=['POST'])
@login_required
@require_admin()
def bulk_update_permissions():
    """Bulk update permissions for multiple users"""
    try:
        data = request.json
        updates = data.get('updates', [])
        org_id = data.get('org_id', session.get('active_connection_id'))
        
        if not updates:
            return jsonify({'error': 'No updates provided'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        errors = []
        
        for update in updates:
            try:
                user_id = update.get('user_id')
                permission_level = update.get('permission_level')
                
                if not user_id or not permission_level:
                    errors.append(f"Missing data for update: {update}")
                    continue
                    
                if permission_level not in PERMISSION_LEVELS:
                    errors.append(f"Invalid permission level for user {user_id}: {permission_level}")
                    continue
                    
                cursor.execute("""
                    INSERT OR REPLACE INTO edit_permissions 
                    (user_id, org_id, permission_level, updated_at, created_by)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (user_id, org_id, permission_level, get_current_user_id()))
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Error updating user {user_id}: {str(e)}")
                
        conn.commit()
        
        # Log bulk action
        log_audit_action(
            'bulk_update_permissions',
            'edit_permissions',
            None,
            {
                'org_id': org_id,
                'total_updates': len(updates),
                'success_count': success_count,
                'error_count': len(errors)
            }
        )
        
        conn.close()
        
        return jsonify({
            'success': True,
            'updated': success_count,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@edit_permissions_bp.route('/api/edit/permissions/users', methods=['GET'])
@login_required
@require_admin()
def list_users_permissions():
    """List all users and their permissions for an organization"""
    try:
        org_id = request.args.get('org_id', session.get('active_connection_id'))
        
        if not org_id:
            return jsonify({'error': 'No organization selected'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                user_id,
                permission_level,
                created_at,
                updated_at,
                created_by
            FROM edit_permissions 
            WHERE org_id = ?
            ORDER BY 
                CASE permission_level
                    WHEN 'admin' THEN 0
                    WHEN 'full_edit' THEN 1
                    WHEN 'edit_structure' THEN 2
                    WHEN 'edit_basic' THEN 3
                    WHEN 'view_only' THEN 4
                END,
                user_id
        """, (org_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        users = []
        for row in results:
            users.append({
                'user_id': row[0],
                'permission_level': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'created_by': row[4],
                'capabilities': get_permission_capabilities(row[1])
            })
            
        return jsonify({
            'org_id': org_id,
            'users': users,
            'total': len(users)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_permission_capabilities(permission_level):
    """Get capabilities for a permission level"""
    capabilities = {
        'view_only': {
            'can_view': True,
            'can_edit_basic': False,
            'can_edit_structure': False,
            'can_delete': False,
            'can_admin': False
        },
        'edit_basic': {
            'can_view': True,
            'can_edit_basic': True,
            'can_edit_structure': False,
            'can_delete': False,
            'can_admin': False
        },
        'edit_structure': {
            'can_view': True,
            'can_edit_basic': True,
            'can_edit_structure': True,
            'can_delete': False,
            'can_admin': False
        },
        'delete': {
            'can_view': True,
            'can_edit_basic': True,
            'can_edit_structure': True,
            'can_delete': True,
            'can_admin': False
        },
        'full_edit': {
            'can_view': True,
            'can_edit_basic': True,
            'can_edit_structure': True,
            'can_delete': True,
            'can_admin': False
        },
        'admin': {
            'can_view': True,
            'can_edit_basic': True,
            'can_edit_structure': True,
            'can_delete': True,
            'can_admin': True
        }
    }
    
    return capabilities.get(permission_level, capabilities['view_only'])

def log_audit_action(action, object_type, object_id, details):
    """Log an audit action"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log 
            (user_id, org_id, action, object_type, object_id, details, ip_address, user_agent, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            get_current_user_id(),
            session.get('active_connection_id'),
            action,
            object_type,
            object_id,
            json.dumps(details),
            request.remote_addr,
            request.headers.get('User-Agent'),
            session.get('session_id')
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging audit action: {str(e)}")