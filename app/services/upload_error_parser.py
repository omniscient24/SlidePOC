"""
Universal Upload Error Parser for Salesforce Objects
Parses and categorizes upload errors with intelligent resolution suggestions
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

class UniversalUploadErrorParser:
    """Parses and categorizes Salesforce upload errors for any object"""
    
    def __init__(self):
        self.error_patterns = self._initialize_patterns()
        self.object_identifier_fields = self._initialize_identifier_fields()
        
    def _initialize_patterns(self) -> List[Dict]:
        """Initialize error patterns with categories and resolutions"""
        return [
            # Permission errors
            {
                'pattern': r'Unable to create/update fields: (.+)',
                'category': 'PERMISSION',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Check field-level security in Setup > Object Manager > {object} > Fields & Relationships. Ensure your profile or permission set has Edit access to these fields.'
            },
            {
                'pattern': r"INVALID_FIELD.*Failed to deserialize field.*'[\d\.]+' is not a valid value for the type xsd:int",
                'category': 'DATA',
                'extract_field': None,
                'resolution': 'Integer field received decimal value. The data needs to be converted to whole numbers without decimals.'
            },
            {
                'pattern': r'INVALID_FIELD_FOR_INSERT_UPDATE',
                'category': 'PERMISSION',
                'extract_field': None,
                'resolution': 'One or more fields cannot be updated. Check field-level security and field accessibility.'
            },
            
            # Invalid input errors (often means duplicate for junction objects)
            {
                'pattern': r'INVALID_INPUT.*?The child product exists in the group',
                'category': 'ALREADY_EXISTS',
                'extract_field': None,
                'resolution': 'This ProductRelatedComponent relationship already exists. The product is already associated with this group.'
            },
            
            # Validation errors
            {
                'pattern': r"Sell only with other products|can't be assigned to the category because the Sell only with other products",
                'category': 'VALIDATION',
                'applies_to': ['ProductCategoryProduct'],
                'extract_field': None,
                'resolution': 'This product is configured as "Sell only with other products". Navigate to the Product2 record and uncheck this option to allow category assignment.'
            },
            {
                'pattern': r'FIELD_CUSTOM_VALIDATION_EXCEPTION.*?:(.+)',
                'category': 'VALIDATION',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Custom validation rule failed. Review the validation rules on {object} and ensure data meets all criteria.'
            },
            {
                'pattern': r'INVALID_OPERATION.*?:(.+)',
                'category': 'VALIDATION',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Operation not allowed due to object configuration or business rules.'
            },
            
            # Duplicate errors
            {
                'pattern': r'duplicate value found: (.+?) duplicates value on record with id: (.+)',
                'category': 'ALREADY_EXISTS',
                'extract_field': lambda m: {'field': m.group(1), 'existing_id': m.group(2)},
                'resolution': 'This record already exists in Salesforce. No action needed - the existing record remains unchanged.'
            },
            {
                'pattern': r'The child product exists in the group',
                'category': 'ALREADY_EXISTS',
                'extract_field': None,
                'resolution': 'This ProductRelatedComponent relationship already exists. The product is already associated with this group.'
            },
            {
                'pattern': r'DUPLICATE_VALUE',
                'category': 'ALREADY_EXISTS',
                'extract_field': None,
                'resolution': 'Record already exists. The existing record in Salesforce remains unchanged.'
            },
            
            # Required field errors
            {
                'pattern': r'Required fields are missing: \[(.+?)\]',
                'category': 'DATA',
                'extract_field': lambda m: [f.strip() for f in m.group(1).split(',')],
                'resolution': 'Provide values for all required fields. Check the object definition for required field list.'
            },
            {
                'pattern': r'REQUIRED_FIELD_MISSING.*?:(.+)',
                'category': 'DATA',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Required field is missing. Ensure all mandatory fields have values.'
            },
            
            # Relationship errors
            {
                'pattern': r'id value of incorrect type: (.+)',
                'category': 'RELATIONSHIP',
                'extract_field': lambda m: m.group(1),
                'resolution': 'The ID format is incorrect for the referenced object. Ensure you are using valid Salesforce IDs (18 or 15 characters).'
            },
            {
                'pattern': r'entity is deleted',
                'category': 'RELATIONSHIP',
                'extract_field': None,
                'resolution': 'The referenced record has been deleted. Use an active record or remove this reference.'
            },
            {
                'pattern': r'insufficient access rights on cross-reference id',
                'category': 'RELATIONSHIP',
                'extract_field': None,
                'resolution': 'You do not have access to the referenced record. Ensure you have at least Read access to all parent/related records.'
            },
            {
                'pattern': r'INVALID_CROSS_REFERENCE_KEY',
                'category': 'RELATIONSHIP',
                'extract_field': None,
                'resolution': 'Invalid reference to another record. Verify that all referenced records exist and are accessible.'
            },
            
            # Data type errors
            {
                'pattern': r'Invalid date.*?:(.+)',
                'category': 'DATA',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Date format is invalid. Use YYYY-MM-DD format for dates.'
            },
            {
                'pattern': r'Invalid number.*?:(.+)',
                'category': 'DATA',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Number format is invalid. Ensure numeric fields contain valid numbers without text.'
            },
            {
                'pattern': r'Invalid boolean.*?:(.+)',
                'category': 'DATA',
                'extract_field': lambda m: m.group(1).strip(),
                'resolution': 'Boolean value is invalid. Use true/false or TRUE/FALSE for boolean fields.'
            },
            
            # Picklist errors
            {
                'pattern': r'bad value for restricted picklist field: (.+)',
                'category': 'DATA',
                'extract_field': lambda m: m.group(1),
                'resolution': 'Invalid picklist value. Check Setup > Object Manager > {object} for valid picklist values.'
            },
            
            # Storage/Limit errors
            {
                'pattern': r'STORAGE_LIMIT_EXCEEDED',
                'category': 'SYSTEM',
                'extract_field': None,
                'resolution': 'Storage limit exceeded. Free up space in your org or increase storage limits.'
            },
            {
                'pattern': r'REQUEST_LIMIT_EXCEEDED',
                'category': 'SYSTEM',
                'extract_field': None,
                'resolution': 'API request limit exceeded. Wait and retry, or process in smaller batches.'
            }
        ]
    
    def _initialize_identifier_fields(self) -> Dict[str, List[str]]:
        """Define which fields to use as identifiers for each object type"""
        return {
            'Product2': ['Name', 'ProductCode'],
            'ProductCategory': ['Name', 'Code'],
            'ProductCatalog': ['Name', 'Code'],
            'ProductCategoryProduct': ['ProductId', 'ProductCategoryId'],
            'ProductRelatedComponent': ['ParentProductId', 'ChildProductId', 'Name'],
            'ProductComponentGroup': ['Name', 'Product2Id'],
            'ProductSellingModel': ['Name', 'Status'],
            'ProductSellingModelOption': ['Product2Id', 'ProductSellingModelId'],
            'PricebookEntry': ['Product2Id', 'Pricebook2Id', 'UnitPrice'],
            'Account': ['Name', 'AccountNumber'],
            'Contact': ['FirstName', 'LastName', 'Email'],
            'Opportunity': ['Name', 'StageName', 'CloseDate'],
            'Order': ['OrderNumber', 'AccountId'],
            'OrderItem': ['OrderId', 'Product2Id'],
            'Asset': ['Name', 'Product2Id', 'AccountId'],
            'Contract': ['ContractNumber', 'AccountId']
        }
    
    def parse_error(self, error_message: str, object_name: str = None, 
                   record_data: Dict = None) -> Dict[str, Any]:
        """
        Parse a single error and return categorized result
        
        Args:
            error_message: The error message from Salesforce
            object_name: The Salesforce object type
            record_data: The record data that failed
            
        Returns:
            Dictionary with categorized error information
        """
        if not error_message:
            error_message = 'Unknown error'
            
        for pattern_config in self.error_patterns:
            # Check if pattern applies to specific objects only
            if 'applies_to' in pattern_config:
                if not object_name or object_name not in pattern_config['applies_to']:
                    continue
            
            # Try to match the pattern
            pattern = pattern_config['pattern']
            match = re.search(pattern, error_message, re.IGNORECASE | re.DOTALL)
            
            if match:
                extracted = None
                if pattern_config['extract_field'] and callable(pattern_config['extract_field']):
                    try:
                        extracted = pattern_config['extract_field'](match)
                    except:
                        extracted = None
                
                resolution = pattern_config['resolution']
                if object_name and '{object}' in resolution:
                    resolution = resolution.format(object=object_name)
                
                return {
                    'category': pattern_config['category'],
                    'original_error': error_message[:500],  # Truncate very long errors
                    'extracted_info': extracted,
                    'resolution': resolution,
                    'record_identifier': self.get_record_identifier(record_data, object_name)
                }
        
        # Unknown error - couldn't match any pattern
        return {
            'category': 'SYSTEM',
            'original_error': error_message[:500],
            'extracted_info': None,
            'resolution': 'Unexpected error. Check Salesforce system status or contact your administrator.',
            'record_identifier': self.get_record_identifier(record_data, object_name)
        }
    
    def get_record_identifier(self, record_data: Dict, object_name: str) -> str:
        """
        Get a human-readable identifier for the record
        
        Args:
            record_data: The record data
            object_name: The Salesforce object type
            
        Returns:
            String identifier for the record
        """
        if not record_data:
            return 'Unknown record'
        
        # Get identifier fields for this object
        identifier_fields = self.object_identifier_fields.get(
            object_name, 
            ['Name', 'Id']  # Default fields
        )
        
        identifiers = []
        for field in identifier_fields:
            if field in record_data and record_data[field]:
                value = str(record_data[field])
                # Truncate long IDs for display
                if len(value) > 50:
                    value = value[:47] + '...'
                identifiers.append(value)
        
        if identifiers:
            return ' - '.join(identifiers)
        
        # Fall back to row number if available
        if '__row_num__' in record_data:
            return f'Row {record_data["__row_num__"]}'
        
        # Last resort
        return 'Unnamed record'
    
    def categorize_errors(self, errors: List[Tuple[str, Dict]], object_name: str) -> Dict[str, Dict]:
        """
        Categorize a list of errors by type
        
        Args:
            errors: List of tuples (error_message, record_data)
            object_name: The Salesforce object type
            
        Returns:
            Dictionary of categorized errors
        """
        categorized = {}
        
        for error_message, record_data in errors:
            parsed = self.parse_error(error_message, object_name, record_data)
            category = parsed['category']
            
            if category not in categorized:
                categorized[category] = {
                    'records': [],
                    'resolutions': set(),
                    'count': 0
                }
            
            categorized[category]['records'].append({
                'identifier': parsed['record_identifier'],
                'error': parsed['original_error'],
                'extracted_info': parsed['extracted_info']
            })
            categorized[category]['resolutions'].add(parsed['resolution'])
            categorized[category]['count'] += 1
        
        # Convert resolution sets to lists for JSON serialization
        for category in categorized:
            categorized[category]['resolutions'] = list(categorized[category]['resolutions'])
        
        return categorized
    
    def generate_recommendations(self, categorized_errors: Dict, object_name: str) -> List[Dict]:
        """
        Generate smart recommendations based on error patterns
        
        Args:
            categorized_errors: Errors grouped by category
            object_name: The Salesforce object type
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Permission errors - highest priority
        if 'PERMISSION' in categorized_errors:
            recommendations.append({
                'priority': 'high',
                'action': 'Review Field-Level Security',
                'steps': [
                    f'Navigate to Setup > Object Manager > {object_name}',
                    'Click on Fields & Relationships',
                    'Review field-level security for affected fields',
                    'Ensure your profile or permission set has Edit access',
                    'Consider using permission sets for granular access control'
                ]
            })
        
        # Validation errors
        if 'VALIDATION' in categorized_errors:
            if object_name == 'ProductCategoryProduct':
                recommendations.append({
                    'priority': 'high',
                    'action': 'Update Product Configuration',
                    'steps': [
                        'Navigate to the affected Product2 records',
                        'Edit each product',
                        'Uncheck "Sell only with other products" checkbox',
                        'Save the changes',
                        'Retry the upload for these records'
                    ]
                })
            else:
                recommendations.append({
                    'priority': 'high',
                    'action': 'Review Validation Rules',
                    'steps': [
                        f'Go to Setup > Object Manager > {object_name}',
                        'Click on Validation Rules',
                        'Review active validation rules',
                        'Ensure your data meets all validation criteria',
                        'Consider temporarily deactivating rules for bulk uploads'
                    ]
                })
        
        # Relationship errors
        if 'RELATIONSHIP' in categorized_errors:
            recommendations.append({
                'priority': 'medium',
                'action': 'Verify Parent Records',
                'steps': [
                    'Check that all referenced parent records exist',
                    'Ensure you have at least Read access to parent records',
                    'Upload parent records first if they are missing',
                    'Verify that record IDs are in the correct format',
                    'Check for any recently deleted records'
                ]
            })
        
        # Data errors
        if 'DATA' in categorized_errors:
            recommendations.append({
                'priority': 'medium',
                'action': 'Fix Data Format Issues',
                'steps': [
                    'Review the spreadsheet for data format issues',
                    'Ensure dates are in YYYY-MM-DD format',
                    'Verify numeric fields contain only numbers',
                    'Check that required fields are populated',
                    'Validate picklist values against Salesforce configuration'
                ]
            })
        
        # Duplicate errors
        if 'DUPLICATE' in categorized_errors:
            recommendations.append({
                'priority': 'low',
                'action': 'Handle Duplicate Records',
                'steps': [
                    'Review existing records in Salesforce',
                    'Use upsert operation with an external ID to update existing records',
                    'Remove duplicate rows from your upload file',
                    'Consider using duplicate rules to prevent future duplicates'
                ]
            })
        
        return recommendations