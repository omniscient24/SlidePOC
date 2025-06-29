# Sync API Specification

## Overview
The sync functionality retrieves data from Salesforce and stores it in local Excel workbooks for offline manipulation and migration planning.

## API Endpoints

### 1. Initialize Sync Session
**POST** `/api/sync`
```json
{
  "objects": ["Product2", "Pricebook2", "LegalEntity"]
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "sync_123456",
  "message": "Sync session initiated"
}
```

### 2. Sync Individual Object
**POST** `/api/sync/{objectApiName}`

**Headers:**
- `X-Connection-Id`: Active connection ID
- `Content-Type`: application/json

**Response Success:**
```json
{
  "success": true,
  "objectApiName": "Product2",
  "recordCount": 1234,
  "records": [...], // Optional: first 100 records for preview
  "hasMore": true,
  "totalSize": 1234,
  "done": true,
  "nextRecordsUrl": null,
  "syncedAt": "2024-01-15T10:30:00Z"
}
```

**Response Error:**
```json
{
  "success": false,
  "error": "INVALID_SESSION_ID",
  "details": "Session expired or invalid. Please reconnect to Salesforce.",
  "objectApiName": "Product2"
}
```

## Backend Implementation Requirements

### 1. Salesforce Query Logic
```python
def sync_object(connection_id, object_api_name):
    # Get connection details
    connection = get_connection(connection_id)
    sf = Salesforce(instance_url=connection.instance_url, 
                   session_id=connection.access_token)
    
    # Build SOQL query
    fields = get_object_fields(sf, object_api_name)
    query = f"SELECT {','.join(fields)} FROM {object_api_name}"
    
    # Execute query with query_all for large datasets
    result = sf.query_all(query)
    
    # Store in Excel workbook
    save_to_workbook(object_api_name, result['records'])
    
    return {
        'success': True,
        'recordCount': result['totalSize'],
        'syncedAt': datetime.now().isoformat()
    }
```

### 2. Field Discovery
```python
def get_object_fields(sf, object_api_name):
    # Get object describe
    obj_describe = getattr(sf, object_api_name).describe()
    
    # Filter fields (exclude system fields, non-queryable)
    fields = []
    for field in obj_describe['fields']:
        if field['type'] not in ['address', 'location'] and \
           field.get('queryable', False):
            fields.append(field['name'])
    
    return fields
```

### 3. Excel Workbook Structure
```
Revenue_Cloud_Data.xlsx
├── Product2 (sheet)
├── Pricebook2 (sheet)
├── LegalEntity (sheet)
└── _Metadata (sheet)
    ├── Object Name
    ├── Record Count
    ├── Last Synced
    └── Fields List
```

## Error Handling

### Common Errors:
1. **INVALID_SESSION_ID** - Session expired
2. **INSUFFICIENT_ACCESS** - No permission to object
3. **MALFORMED_QUERY** - Invalid SOQL
4. **REQUEST_LIMIT_EXCEEDED** - API limits hit
5. **OBJECT_NOT_FOUND** - Invalid object API name

## Frontend Integration Points

### Progress Updates
The frontend expects progress updates via:
1. Status updates: pending → syncing → synced/error
2. Record count updates
3. Progress bar updates (0-100%)

### Status Storage
Sync status is stored in localStorage:
```javascript
objectSyncStatus = {
  "Product2": {
    "status": "synced",
    "lastSynced": "2024-01-15T10:30:00Z",
    "recordCount": 1234
  }
}
```

## Performance Considerations

1. **Batch Processing**: For large objects, implement pagination
2. **Rate Limiting**: Respect Salesforce API limits
3. **Timeout Handling**: Long-running syncs need progress tracking
4. **Compression**: Consider compressing large Excel files
5. **Parallel Processing**: Sync multiple objects concurrently when possible

## Security Requirements

1. Validate connection ownership
2. Sanitize object API names
3. Log all sync operations
4. Implement request throttling
5. Secure Excel file storage