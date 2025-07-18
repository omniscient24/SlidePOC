"""
Upload Field Configuration
Defines which fields should be excluded from uploads for each object
"""

import re
import pandas as pd

def _generate_product_code(current_value, product_name=''):
    """Generate ProductCode based on product name if not already set"""
    if pd.isna(current_value) or current_value == '' or current_value is None:
        # Generate ProductCode based on product name
        if product_name:
            # Convert product name to abbreviated code
            name_upper = product_name.upper()
            
            # Determine product line and type
            if 'HRM' in name_upper:
                product_line = 'HRM'
            elif 'DCS' in name_upper:
                product_line = 'DCS'
            else:
                product_line = 'CYB'
            
            # Determine type
            if 'BUNDLE' in name_upper:
                type_code = 'BUN'
            elif 'SERVICE' in name_upper:
                type_code = 'SVC'
            elif 'SUPPORT' in name_upper:
                type_code = 'SUP'
            else:
                type_code = 'CMP'
            
            # Generate abbreviation from product name
            # Remove common words and create abbreviation
            words = re.sub(r'[^A-Z0-9\s]', '', name_upper).split()
            filtered_words = [w for w in words if w not in ['THE', 'AND', 'FOR', 'OF', 'IN', 'ON', 'AT', 'TO', 'A', 'AN', 'MANAGED', 'PACK', 'PACKAGE']]
            
            if len(filtered_words) == 0:
                abbreviation = 'GEN'
            elif len(filtered_words) == 1:
                abbreviation = filtered_words[0][:4]
            elif len(filtered_words) == 2:
                # For 2 words, take first 2 letters of each
                abbreviation = filtered_words[0][:2] + filtered_words[1][:2]
            else:
                # For 3+ words, take first letter of each word, max 4 letters
                abbreviation = ''.join([w[0] for w in filtered_words[:4]])
            
            return f'CYB-{product_line}-{abbreviation}-{type_code}'
        else:
            return 'CYB-AUTO-GEN-CODE'
    return current_value

def _generate_sku(current_value, product_name=''):
    """Generate StockKeepingUnit based on product name if not already set"""
    if pd.isna(current_value) or current_value == '' or current_value is None:
        # Generate SKU based on ProductCode
        if product_name:
            # Generate ProductCode first, then prefix with SKU-
            product_code = _generate_product_code(None, product_name)
            return f'SKU-{product_code}'
        else:
            return 'SKU-CYB-AUTO-GEN-CODE'
    return current_value

# Fields that exist in the workbook for reference but shouldn't be uploaded to Salesforce
SPREADSHEET_ONLY_FIELDS = {
    'Product2': [
        'Type',  # For user reference to see product type in spreadsheet
        # Temporarily exclude Revenue Cloud fields if they're not available in your org
        # Comment these out once Revenue Cloud is enabled and permissions are set:
        'CanRamp',  # Revenue Cloud specific field
        'UsageModelType',  # Revenue Cloud specific field
    ],
    'ProductCatalog': [
        'NumberOfCategories',  # Read-only field that shows count of related categories
    ],
    'PricebookEntry': [
        'ProductName',  # For user reference - populated from Product2 Name
        'ProductSellingModelName',  # For user reference - populated from ProductSellingModel Name
    ],
    # Transaction objects - exclude calculated and system fields
    'Order': [
        'TotalAmount',  # Calculated from OrderItems
        'OrderNumber',  # Auto-generated
        'ActivatedById', 'ActivatedDate',  # System fields
        'CustomerAuthorizedById', 'CompanyAuthorizedById',  # Managed through UI
    ],
    'OrderItem': [
        'OrderItemNumber',  # Auto-generated
        'TotalPrice',  # Calculated field
        'IsDeleted',  # System field
    ],
    'Asset': [
        'CurrentMrr', 'CurrentLifecycleEndDate', 'CurrentQuantity', 'CurrentAmount',  # Calculated fields
        'TotalLifecycleAmount',  # Calculated field
        'AssetLevel',  # System field
    ],
    'AssetAction': [
        'AssetActionNumber',  # Auto-generated
        'MrrChange', 'QuantityChange',  # Calculated fields
    ],
    'AssetActionSource': [
        # Minimal exclusions for this junction object
    ],
    'Contract': [
        'ContractNumber',  # Auto-generated
        'ActivatedById', 'ActivatedDate',  # System fields
    ],
    
    # Fulfillment objects - exclude calculated and system fields
    'Location': [
        # Minimal exclusions for location configuration
    ],
    'AssociatedLocation': [
        # Junction object - minimal exclusions
    ],
    'OrderDeliveryMethod': [
        'ReferenceNumber',  # May be auto-generated
    ],
    'FulfillmentOrder': [
        'FulfillmentOrderNumber',  # Auto-generated
        'ItemCount',  # Calculated
        'TotalProductAmount', 'TotalProductTaxAmount',  # Calculated
        'TotalAdjustmentAmount', 'TotalAdjustmentTaxAmount',  # Calculated
        'TotalAmount', 'TotalTaxAmount', 'GrandTotalAmount',  # Calculated
    ],
    'FulfillmentOrderLineItem': [
        'TotalPrice', 'TotalLineAmount', 'TotalLineTaxAmount',  # Calculated
        'TotalAdjustmentAmount', 'TotalAdjustmentTaxAmount',  # Calculated
        'GrossUnitPrice', 'TotalAmount',  # Calculated
    ],
    'OrderDeliveryGroup': [
        'TotalAmount', 'TotalTaxAmount',  # Calculated
    ],
    'Shipment': [
        'ShipmentNumber',  # Auto-generated
    ],
    'ShipmentItem': [
        'ProductName',  # Reference field
    ],
    'WorkPlanTemplate': [
        # Template configuration - minimal exclusions
    ],
    'WorkPlanTemplateEntry': [
        # Template configuration - minimal exclusions
    ],
    'WorkPlan': [
        # Instance data - minimal exclusions
    ],
    'ActionPlan': [
        # Action plan configuration
    ],
    'FulfillmentStepDefinitionGroup': [
        # Definition configuration
    ],
    'FulfillmentStepDefinition': [
        # Definition configuration
    ],
    'FulfillmentStep': [
        'ActualDuration',  # Calculated
    ],
    'FulfillmentAsset': [
        # Asset tracking during fulfillment
    ],
    'FulfillmentOrderItemAdjustment': [
        # Adjustment records
    ],
    'FulfillmentOrderItemTax': [
        # Tax records
    ],
}

# Fields that require special handling or transformation
FIELD_TRANSFORMATIONS = {
    # Handle boolean values in Status picklist fields
    'ProductClassification': {
        'Status': lambda x: 'Active' if str(x).upper() in ['TRUE', 'ACTIVE'] else 'Inactive' if str(x).upper() in ['FALSE', 'INACTIVE'] else x
    },
    # Product2 auto-generation for ProductCode and StockKeepingUnit
    'Product2': {
        'ProductCode': _generate_product_code,
        'StockKeepingUnit': _generate_sku,
    },
    # Add other transformations as needed
}

# Fields that should be set to NULL if empty (already handled globally, but can override here)
REQUIRED_NULL_FIELDS = {
    # Example:
    # 'Product2': ['RequiredField1', 'RequiredField2']
}