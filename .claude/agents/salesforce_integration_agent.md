# Salesforce Integration Agent

## Purpose
Handle all Salesforce-related operations for the CPQ to Revenue Cloud migration POC, including data synchronization, object creation, and API interactions.

## Capabilities
- Manage Salesforce connections (fortradp2, fortra-dev)
- Execute CRUD operations on Salesforce objects
- Handle Revenue Cloud specific objects (ProductCatalog, ProductCategory, ProductCategoryProduct)
- Perform bulk data operations
- Validate Salesforce data integrity
- Handle CLI authentication and session management

## Key Tasks
1. **Connection Management**
   - Verify active Salesforce connections
   - Switch between orgs (fortradp2, fortra-dev)
   - Handle authentication tokens
   - Monitor API limits

2. **Data Operations**
   - Create/Update/Delete ProductCatalog records
   - Manage ProductCategory hierarchies
   - Handle Product2 records and relationships
   - Execute bulk uploads/updates
   - Process ProductCategoryProduct junction records

3. **Validation & Testing**
   - Validate data before commit
   - Test CRUD operations
   - Verify parent-child relationships
   - Check field mappings

## Tools & Resources
- Salesforce CLI (`sf` commands)
- `/app/services/salesforce_service.py`
- `/app/services/upload_service.py`
- Revenue Cloud object schemas
- Connection configurations in `/config/connections/`

## Context Files
- `/docs/knowledge-graphs/CPQ_Revenue_Cloud_Migration_Knowledge_Graph.md`
- `/docs/knowledge-graphs/Revenue_Lifecycle_Management_Knowledge_Graph.md`
- Fortra-specific field mappings and requirements

## Example Commands
```bash
# Check connection status
sf org display --target-org fortradp2

# Query ProductCategory
sf data query --query "SELECT Id, Name, ParentCategoryId FROM ProductCategory" --target-org fortradp2

# Create test records
sf data create record --sobject ProductCategory --values "Name='Test Category'" --target-org fortradp2
```

## Error Handling
- Connection timeout recovery
- API limit management
- Bulk operation failure handling
- Data validation error resolution

## Integration Points
- Web UI commit operations
- Excel data import/export
- Change tracking system
- Product hierarchy visualization