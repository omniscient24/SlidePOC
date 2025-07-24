# Salesforce Integration Documentation

## Overview

This document describes the unified Salesforce integration architecture implemented for the CPQ to Revenue Cloud Migration POC. The integration provides a centralized service for all Salesforce operations, supporting both the Data Management and Product Hierarchy sections of the application.

## Architecture

### Core Components

1. **SalesforceService** (`/app/services/salesforce_service.py`)
   - Unified interface for all Salesforce operations
   - Singleton pattern for consistent access
   - Delegates to specialized services when appropriate

2. **ConnectionManager** (`/app/services/connection_manager.py`)
   - Manages Salesforce CLI connections
   - Stores connection metadata
   - Handles session-based authentication

3. **SyncService** (`/app/services/sync_service.py`)
   - Downloads data from Salesforce
   - Handles bulk data retrieval
   - Manages sync status tracking

4. **UploadService** (`/app/services/upload_service.py`)
   - Uploads data to Salesforce
   - Supports insert, update, upsert operations
   - Handles bulk operations

## Salesforce Service API

### Connection Management

```python
# Get active connection alias for current session
connection_alias = salesforce_service.get_active_connection(session)

# Verify connection is valid
is_valid = salesforce_service.verify_connection(session)
```

### Query Operations

```python
# Execute SOQL query
success, records = salesforce_service.query(
    "SELECT Id, Name FROM Product2 WHERE IsActive = true",
    connection_alias
)

# Get object metadata
success, metadata = salesforce_service.describe_object('Product2', connection_alias)
```

### CRUD Operations

#### Create Records
```python
# Create single record
record_data = {
    'Name': 'New Product',
    'ProductCode': 'PROD-001',
    'IsActive': True
}
success, result = salesforce_service.create_record(
    'Product2', record_data, connection_alias
)
```

#### Update Records
```python
# Update single record
updates = {
    'Name': 'Updated Product Name',
    'Description': 'New description'
}
success, result = salesforce_service.update_record(
    'Product2', record_id, updates, connection_alias
)
```

#### Delete Records
```python
# Delete single record
success, result = salesforce_service.delete_record(
    'Product2', record_id, connection_alias
)

# Delete multiple records
record_ids = ['01t1234...', '01t5678...']
success, result = salesforce_service.delete_records_bulk(
    'Product2', record_ids, connection_alias
)
```

### Product Hierarchy Operations

#### Delete with Children
```python
# Delete node with options for children
success, result = salesforce_service.delete_with_children(
    node_id='01t1234...',
    node_type='product',
    delete_children=True,  # or False to reparent
    new_parent_id='01t5678...',  # if reparenting
    connection_alias=connection_alias
)
```

The delete_with_children method handles:
- **ProductCategory**: Deletes or reparents child categories
- **Product2**: Removes related components and associations
- **ProductCatalog**: Handles catalog-level deletions

#### Get Child Records
```python
# Get children of a parent record
success, children = salesforce_service.get_child_records(
    parent_id='01t1234...',
    child_relationship='ChildProducts',
    connection_alias=connection_alias
)
```

## Integration Points

### Product Hierarchy Editor

The Product Hierarchy section integrates with Salesforce for:

1. **Field Updates**: Real-time editing of product attributes
2. **Node Deletion**: Smart deletion with parent-child handling
3. **Change Tracking**: Local changes tracked until commit
4. **Batch Operations**: Multiple changes committed together

### Data Management

The Data Management section uses the same service for:

1. **Data Sync**: Downloading Salesforce data
2. **Bulk Upload**: Uploading Excel data to Salesforce
3. **Object Discovery**: Listing available objects
4. **Field Mapping**: Understanding object schemas

## API Endpoints

### Change Management Endpoints

#### Validate Changes
`POST /api/edit/changes/validate`

Request:
```json
{
  "changes": [
    {
      "nodeId": "01t1234...",
      "nodeType": "product",
      "fieldName": "Name",
      "oldValue": "Old Name",
      "newValue": "New Name"
    }
  ],
  "deletions": [
    {
      "nodeId": "01t5678...",
      "nodeType": "product",
      "deleteChildren": false,
      "newParentId": null
    }
  ]
}
```

#### Commit Changes
`POST /api/edit/changes/commit`

Request: Same as validate

Response:
```json
{
  "success": true,
  "changes_processed": 1,
  "deletions_processed": 1,
  "deletion_details": [
    {
      "deleted": [{"id": "01t5678...", "type": "Product2"}],
      "reparented": []
    }
  ],
  "errors": []
}
```

## Error Handling

The service provides detailed error handling for common Salesforce errors:

- **ENTITY_IS_DELETED**: Record already deleted
- **INSUFFICIENT_ACCESS**: Missing permissions
- **DELETE_FAILED**: Constraint violations
- **CASCADE_DELETE_FAILED**: Child record restrictions

## CLI Integration

All operations use Salesforce CLI (SFDX) commands:

```bash
# Query
sfdx data query --query "SELECT..." --target-org alias --json

# Update
sfdx data update record --sobject Product2 --record-id 01t... --values "Name='New'" --target-org alias

# Delete
sfdx data delete record --sobject Product2 --record-id 01t... --target-org alias

# Bulk Delete
sfdx data delete bulk --sobject Product2 --file ids.csv --target-org alias
```

## Security Considerations

1. **Authentication**: All operations require valid session
2. **Connection Validation**: Connections verified before use
3. **Permission Checks**: Salesforce permissions enforced
4. **Input Validation**: All inputs sanitized before CLI execution

## Performance Optimizations

1. **Bulk Operations**: Multiple records processed together
2. **Lazy Loading**: Data fetched only when needed
3. **Connection Pooling**: Reuses CLI connections
4. **Async Processing**: Long operations don't block UI

## Future Enhancements

1. **Async Job Monitoring**: Track long-running operations
2. **Retry Logic**: Automatic retry for transient failures
3. **Caching**: Cache metadata for better performance
4. **WebSocket Updates**: Real-time progress updates
5. **Conflict Resolution**: Handle concurrent edits

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Session expired, need to re-login
2. **No Active Connection**: Select a Salesforce org first
3. **Delete Failed**: Check for child records or constraints
4. **Timeout Errors**: Large operations may need bulk API

### Debug Logging

Enable debug logging by checking server logs:
```bash
tail -f server.log
```

Look for prefixed log entries:
- `[COMMIT]` - Change commit operations
- `[SYNC]` - Data synchronization
- `[UPLOAD]` - Data upload operations

## Testing

To test the integration:

1. Start the server: `./start_slide.sh`
2. Login to the application
3. Connect to a Salesforce org
4. Navigate to Product Hierarchy
5. Make changes (edit/delete)
6. Commit changes to Salesforce

The integration supports both sandbox and production orgs.