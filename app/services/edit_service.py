"""
Edit functionality service for product hierarchy
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from ..utils.db import get_db_connection

class EditService:
    """Service for managing edit permissions and field configurations"""
    
    # Permission level hierarchy
    PERMISSION_LEVELS = {
        'view_only': 0,
        'edit_basic': 1,
        'edit_structure': 2,
        'full_edit': 3,
        'admin': 4
    }
    
    # Default Salesforce field types
    FIELD_TYPES = [
        'text', 'textarea', 'number', 'currency', 'percent', 
        'checkbox', 'date', 'datetime', 'picklist', 'multipicklist',
        'url', 'email', 'phone', 'reference'
    ]
    
    def get_user_permission(self, user_id, org_id):
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
        
        return result[0] if result else 'view_only'
    
    def check_permission(self, user_id, org_id, required_level):
        """Check if user has required permission level"""
        user_permission = self.get_user_permission(user_id, org_id)
        user_level = self.PERMISSION_LEVELS.get(user_permission, 0)
        required = self.PERMISSION_LEVELS.get(required_level, 0)
        return user_level >= required
    
    def get_user_permissions_details(self, user_id, org_id):
        """Get detailed permissions for a user"""
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
            return {
                'user_id': user_id,
                'org_id': org_id,
                'permission_level': 'view_only',
                'is_default': True,
                'capabilities': self.get_permission_capabilities('view_only')
            }
            
        return {
            'user_id': user_id,
            'org_id': org_id,
            'permission_level': result[0],
            'created_at': result[1],
            'updated_at': result[2],
            'created_by': result[3],
            'capabilities': self.get_permission_capabilities(result[0])
        }
    
    def update_user_permission(self, target_user_id, org_id, permission_level, admin_user_id):
        """Update user permission"""
        if permission_level not in self.PERMISSION_LEVELS:
            raise ValueError(f'Invalid permission level: {permission_level}')
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO edit_permissions 
            (user_id, org_id, permission_level, updated_at, created_by)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (target_user_id, org_id, permission_level, admin_user_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_all_user_permissions(self, org_id):
        """Get all users and their permissions for an organization"""
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
                'capabilities': self.get_permission_capabilities(row[1])
            })
            
        return users
    
    def get_field_configuration(self, org_id, object_type='Product2'):
        """Get field configuration for an organization"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get configured fields for the org
        cursor.execute("""
            SELECT 
                field_name,
                field_label,
                field_type,
                is_editable,
                required,
                validation_rules,
                permission_level,
                display_order
            FROM field_config 
            WHERE org_id = ? AND object_type = ?
            ORDER BY display_order, field_name
        """, (org_id, object_type))
        
        results = cursor.fetchall()
        
        # If no custom configuration, get defaults
        if not results:
            cursor.execute("""
                SELECT 
                    field_name,
                    field_label,
                    field_type,
                    is_editable,
                    required,
                    validation_rules,
                    permission_level,
                    display_order
                FROM field_config 
                WHERE org_id = 'default' AND object_type = ?
                ORDER BY display_order, field_name
            """, (object_type,))
            
            results = cursor.fetchall()
            
        conn.close()
        
        fields = []
        for row in results:
            validation_rules = []
            if row[5]:
                try:
                    validation_rules = json.loads(row[5])
                except:
                    validation_rules = []
                    
            fields.append({
                'field_name': row[0],
                'field_label': row[1],
                'field_type': row[2],
                'is_editable': bool(row[3]),
                'required': bool(row[4]),
                'validation_rules': validation_rules,
                'permission_level': row[6],
                'display_order': row[7]
            })
            
        return fields
    
    def update_field_configuration(self, org_id, object_type, fields):
        """Update field configuration"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Delete existing configuration for this org/object
            cursor.execute("""
                DELETE FROM field_config 
                WHERE org_id = ? AND object_type = ?
            """, (org_id, object_type))
            
            # Insert new configuration
            for idx, field in enumerate(fields):
                validation_rules = field.get('validation_rules', [])
                
                cursor.execute("""
                    INSERT INTO field_config 
                    (org_id, object_type, field_name, field_label, field_type, 
                     is_editable, required, validation_rules, permission_level, 
                     display_order, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    org_id,
                    object_type,
                    field['field_name'],
                    field.get('field_label', field['field_name']),
                    field.get('field_type', 'text'),
                    field.get('is_editable', True),
                    field.get('required', False),
                    json.dumps(validation_rules) if validation_rules else None,
                    field.get('permission_level', 'edit_basic'),
                    field.get('display_order', idx)
                ))
                
            cursor.execute("COMMIT")
            conn.close()
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            conn.close()
            raise e
    
    def get_permission_capabilities(self, permission_level):
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
    
    def log_audit_action(self, user_id, org_id, action, object_type, object_id, details, request_info=None):
        """Log an audit action"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_log 
                (user_id, org_id, action, object_type, object_id, details, 
                 ip_address, user_agent, session_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                org_id,
                action,
                object_type,
                object_id,
                json.dumps(details),
                request_info.get('ip_address') if request_info else None,
                request_info.get('user_agent') if request_info else None,
                request_info.get('session_id') if request_info else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error logging audit action: {str(e)}")
    
    def validate_field_value(self, org_id, object_type, field_name, value):
        """Validate a field value against configured rules"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get field configuration
        cursor.execute("""
            SELECT 
                field_type,
                required,
                validation_rules
            FROM field_config 
            WHERE org_id = ? AND object_type = ? AND field_name = ?
        """, (org_id, object_type, field_name))
        
        result = cursor.fetchone()
        
        # If no custom config, check defaults
        if not result:
            cursor.execute("""
                SELECT 
                    field_type,
                    required,
                    validation_rules
                FROM field_config 
                WHERE org_id = 'default' AND object_type = ? AND field_name = ?
            """, (object_type, field_name))
            
            result = cursor.fetchone()
            
        conn.close()
        
        if not result:
            return {'valid': True, 'errors': []}
            
        field_type, required, validation_rules_json = result
        
        errors = []
        
        # Check required
        if required and not value:
            errors.append({
                'type': 'required',
                'message': 'This field is required'
            })
            
        # Parse and apply validation rules
        if validation_rules_json and value:
            try:
                validation_rules = json.loads(validation_rules_json)
                
                for rule in validation_rules:
                    error = self._apply_validation_rule(value, rule, field_type)
                    if error:
                        errors.append(error)
                        
            except Exception as e:
                print(f"Error parsing validation rules: {e}")
                
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _apply_validation_rule(self, value, rule, field_type):
        """Apply a single validation rule to a value"""
        rule_type = rule.get('type')
        
        if rule_type == 'min_length':
            min_val = rule.get('value', 0)
            if len(str(value)) < min_val:
                return {
                    'type': 'min_length',
                    'message': rule.get('message', f'Minimum length is {min_val} characters')
                }
                
        elif rule_type == 'max_length':
            max_val = rule.get('value', 255)
            if len(str(value)) > max_val:
                return {
                    'type': 'max_length',
                    'message': rule.get('message', f'Maximum length is {max_val} characters')
                }
                
        elif rule_type == 'pattern':
            import re
            pattern = rule.get('value', '')
            if pattern and not re.match(pattern, str(value)):
                return {
                    'type': 'pattern',
                    'message': rule.get('message', 'Invalid format')
                }
                
        elif rule_type == 'range' and field_type in ['number', 'currency', 'percent']:
            try:
                num_value = float(value)
                min_val = rule.get('min', float('-inf'))
                max_val = rule.get('max', float('inf'))
                
                if num_value < min_val or num_value > max_val:
                    return {
                        'type': 'range',
                        'message': rule.get('message', f'Value must be between {min_val} and {max_val}')
                    }
            except ValueError:
                return {
                    'type': 'number',
                    'message': 'Invalid number format'
                }
                
        return None

# Create singleton instance
edit_service = EditService()