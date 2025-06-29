# Revenue Cloud Upload Process Guide

## Overview
This guide provides a repeatable, error-free process for uploading Revenue Cloud data to Salesforce.

## Prerequisites
- Salesforce CLI installed and authenticated to target org
- Python 3.x with pandas and openpyxl libraries
- Revenue_Cloud_Complete_Upload_Template.xlsx workbook

## Process Steps

### Step 1: Clean the Workbook
Remove all read-only and system-managed fields from the workbook.

```bash
python3 comprehensive_field_cleanup.py
```

This script will:
- Create a backup of your workbook
- Remove ALL non-updateable fields from ALL sheets
- Generate a detailed cleanup report
- Synchronize with Salesforce to ensure current data

### Step 2: Review and Prepare Data
1. Open the cleaned workbook: `data/Revenue_Cloud_Complete_Upload_Template.xlsx`
2. Review each sheet to ensure data is correct
3. For new records, leave the Id field empty
4. For updates, ensure the Id field contains the Salesforce record ID

### Step 3: Run the Upload Process
Execute the complete upload process:

```bash
python3 revenue_cloud_upload_process.py
```

This script will:
- Upload objects in the correct dependency order
- Handle special cases (Product2 Type field, junction objects, etc.)
- Provide detailed progress and error reporting
- Clean up temporary files automatically

## Object Upload Sequence

1. **Foundation Objects**
   - ProductCatalog
   - ProductCategory

2. **Classification and Attributes**
   - ProductClassification
   - AttributeCategory
   - AttributePicklist
   - AttributeDefinition

3. **Product Setup**
   - ProductSellingModel
   - Product2
   - Pricebook2

4. **Product Relationships**
   - ProductAttributeDefinition
   - AttributePicklistValue
   - ProductCategoryProduct

5. **Pricing and Components**
   - PricebookEntry
   - ProductComponentGroup
   - ProductRelatedComponent

## Special Handling Rules

### Product2
- `Type` field can only be set during record creation
- For updates, the Type field is automatically removed

### ProductAttributeDefinition
- `AttributeCategoryId` can only be set during record creation
- For updates, this field is automatically removed

### ProductCategoryProduct
- Junction object with limited updateable fields
- Only new records are inserted; existing records are not updated

### ProductComponentGroup
- Uses `Code` field as external ID for upsert operations
- Ensures no duplicate Code values are created

## Common Issues and Solutions

### Issue: "Field not updateable" errors
**Solution**: Run `comprehensive_field_cleanup.py` to remove non-updateable fields

### Issue: Duplicate key errors
**Solution**: The process uses upsert with external IDs to prevent duplicates

### Issue: Required field missing
**Solution**: Check the object's required fields using Salesforce Setup or the cleanup report

## Export Current Data
To synchronize your workbook with current Salesforce data:

```bash
python3 export_to_same_template.py
```

## File Descriptions

- `comprehensive_field_cleanup.py` - Removes all non-updateable fields from workbook
- `revenue_cloud_upload_process.py` - Main upload process with smart handling
- `export_to_same_template.py` - Exports current Salesforce data to workbook
- `field_cleanup_report.txt` - Generated report showing removed fields
- `Revenue_Cloud_Complete_Upload_Template.xlsx` - Main data workbook

## Best Practices

1. **Always run cleanup before upload** - Ensures no read-only fields cause errors
2. **Export before making changes** - Get latest data from Salesforce
3. **Review the cleanup report** - Understand which fields were removed
4. **Check upload results** - Review both success and failure messages
5. **Keep backups** - The cleanup process creates timestamped backups

## Support
For issues or questions:
1. Check the `field_cleanup_report.txt` for field-specific information
2. Review Salesforce object documentation for field requirements
3. Use Salesforce Setup to verify field-level security settings