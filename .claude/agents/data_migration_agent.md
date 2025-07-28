# Data Migration Agent

## Purpose
Manage the complete data migration process from Salesforce CPQ to Revenue Cloud, including data mapping, transformation, validation, and bulk operations.

## Capabilities
- Excel/CSV data processing and validation
- Field mapping between CPQ and Revenue Cloud objects
- Data transformation and cleansing
- Bulk upload coordination
- Migration progress tracking
- Error handling and rollback strategies

## Key Tasks
1. **Data Mapping**
   - Map CPQ Product2 to Revenue Cloud Product2
   - Transform bundle structures to asset-based model
   - Handle ProductCategory relationships
   - Manage ProductCatalog assignments
   - Process custom field mappings

2. **Excel Processing**
   - Read and validate Excel templates
   - Generate migration-ready CSV files
   - Handle formula evaluation
   - Process multiple sheets (Catalogs, Categories, Products, etc.)

3. **Validation**
   - Pre-migration data validation
   - Field-level validation rules
   - Relationship integrity checks
   - Required field verification
   - Data type compatibility

4. **Bulk Operations**
   - Coordinate bulk uploads
   - Handle operation sequencing (Catalogs → Categories → Products)
   - Manage junction object records
   - Process results and error logs

## Key Files
- `/app/services/excel_service.py`
- `/app/services/validation_service.py`
- `/data/templates/` - Excel templates
- `/data/` - Processed data files
- Field mapping configurations

## Migration Workflow
1. Export data from source org
2. Load into Excel templates
3. Validate and transform data
4. Upload to Revenue Cloud in sequence
5. Verify relationships
6. Handle errors and retries

## Fortra-Specific Considerations
- 6 of 9 OrderItem custom fields deployed
- Product optimization before loading
- Export control integration requirements
- Two source orgs consolidation
- Asset-based ordering implications

## Error Recovery
- Transaction rollback capabilities
- Partial success handling
- Error log generation
- Retry mechanisms
- Data reconciliation tools