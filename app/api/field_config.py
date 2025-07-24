from flask import Blueprint, request, jsonify, session
import sqlite3
import json
from datetime import datetime
from ..utils.auth import login_required, get_current_user_id
from ..utils.db import get_db_connection
from .edit_permissions import require_admin, require_permission, log_audit_action

field_config_bp = Blueprint('field_config', __name__)

# Default Salesforce field types
FIELD_TYPES = [
    'text', 'textarea', 'number', 'currency', 'percent', 
    'checkbox', 'date', 'datetime', 'picklist', 'multipicklist',
    'url', 'email', 'phone', 'reference'
]

# Default validation rule templates
VALIDATION_TEMPLATES = {
    'required': {'type': 'required', 'message': 'This field is required'},
    'min_length': {'type': 'min_length', 'value': 3, 'message': 'Minimum length is {value} characters'},
    'max_length': {'type': 'max_length', 'value': 255, 'message': 'Maximum length is {value} characters'},
    'pattern': {'type': 'pattern', 'value': '', 'message': 'Invalid format'},
    'number_range': {'type': 'range', 'min': 0, 'max': 100, 'message': 'Value must be between {min} and {max}'}
}

@field_config_bp.route('/api/edit/field-config', methods=['GET'])
@login_required
def get_field_configuration():
    """Get field configuration for current org"""
    try:
        org_id = request.args.get('org_id', session.get('active_connection_id'))
        object_type = request.args.get('object_type', 'Product2')
        
        if not org_id:
            return jsonify({'error': 'No organization selected'}), 400
            
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
            
        return jsonify({
            'org_id': org_id,
            'object_type': object_type,
            'fields': fields,
            'total': len(fields)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@field_config_bp.route('/api/edit/field-config', methods=['POST'])
@login_required
@require_admin()
def update_field_configuration():
    """Update field configuration (admin only)"""
    try:
        data = request.json
        org_id = data.get('org_id', session.get('active_connection_id'))
        object_type = data.get('object_type', 'Product2')
        fields = data.get('fields', [])
        
        if not org_id:
            return jsonify({'error': 'No organization selected'}), 400
            
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
            
            # Log the action
            log_audit_action(
                'update_field_config',
                'field_config',
                object_type,
                {
                    'org_id': org_id,
                    'object_type': object_type,
                    'field_count': len(fields)
                }
            )
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Field configuration updated for {object_type}',
                'fields_configured': len(fields)
            })
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@field_config_bp.route('/api/edit/field-config/defaults', methods=['GET'])
@login_required
@require_admin()
def get_default_field_config():
    """Get default Salesforce field configuration"""
    try:
        object_type = request.args.get('object_type', 'Product2')
        
        # Define default configurations for different objects
        defaults = {
            'Product2': [
                {'field_name': 'Name', 'field_label': 'Product Name', 'field_type': 'text', 'required': True},
                {'field_name': 'ProductCode', 'field_label': 'Product Code', 'field_type': 'text'},
                {'field_name': 'Description', 'field_label': 'Description', 'field_type': 'textarea'},
                {'field_name': 'IsActive', 'field_label': 'Active', 'field_type': 'checkbox'},
                {'field_name': 'Family', 'field_label': 'Product Family', 'field_type': 'picklist'},
                {'field_name': 'QuantityUnitOfMeasure', 'field_label': 'Unit of Measure', 'field_type': 'text'},
                {'field_name': 'DisplayUrl', 'field_label': 'Display URL', 'field_type': 'url'},
                {'field_name': 'ExternalId', 'field_label': 'External ID', 'field_type': 'text'}
            ],
            'ProductCategory': [
                {'field_name': 'Name', 'field_label': 'Category Name', 'field_type': 'text', 'required': True},
                {'field_name': 'Description', 'field_label': 'Description', 'field_type': 'textarea'},
                {'field_name': 'IsActive', 'field_label': 'Active', 'field_type': 'checkbox'},
                {'field_name': 'SortOrder', 'field_label': 'Sort Order', 'field_type': 'number'}
            ]
        }
        
        fields = defaults.get(object_type, [])
        
        # Add default properties
        for idx, field in enumerate(fields):
            field.setdefault('is_editable', True)
            field.setdefault('permission_level', 'edit_basic')
            field.setdefault('display_order', idx)
            field.setdefault('validation_rules', [])
            
        return jsonify({
            'object_type': object_type,
            'fields': fields,
            'available_field_types': FIELD_TYPES,
            'validation_templates': VALIDATION_TEMPLATES
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@field_config_bp.route('/api/edit/field-config/validate', methods='POST'])
@login_required
def validate_field_value():
    """Validate a field value against configured rules"""
    try:
        data = request.json
        org_id = data.get('org_id', session.get('active_connection_id'))
        object_type = data.get('object_type', 'Product2')
        field_name = data.get('field_name')
        value = data.get('value')
        
        if not all([org_id, field_name]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
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
            return jsonify({'valid': True, 'errors': []})
            
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
                    error = apply_validation_rule(value, rule, field_type)
                    if error:
                        errors.append(error)
                        
            except Exception as e:
                print(f"Error parsing validation rules: {e}")
                
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def apply_validation_rule(value, rule, field_type):
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

@field_config_bp.route('/api/edit/field-config/picklist-values', methods=['GET'])
@login_required
def get_picklist_values():
    """Get picklist values for a field"""
    try:
        org_id = request.args.get('org_id', session.get('active_connection_id'))
        object_type = request.args.get('object_type', 'Product2')
        field_name = request.args.get('field_name')
        
        if not field_name:
            return jsonify({'error': 'Field name required'}), 400
            
        # For now, return hardcoded values. In production, this would
        # query Salesforce for actual picklist values
        picklist_values = {
            'Product2': {
                'Family': ['Hardware', 'Software', 'Services', 'Training', 'Support'],
                'Type': ['Base', 'Option', 'Bundle', 'Component']
            },
            'ProductCategory': {
                'Type': ['Parent', 'Child', 'Standalone']
            }
        }
        
        values = picklist_values.get(object_type, {}).get(field_name, [])
        
        return jsonify({
            'field_name': field_name,
            'values': values
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500