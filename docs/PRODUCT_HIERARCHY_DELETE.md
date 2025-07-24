# Product Hierarchy Delete Functionality

## Overview

The Product Hierarchy editor now supports comprehensive delete operations with intelligent handling of parent-child relationships. This feature allows users to delete nodes from the hierarchy with options for handling dependent records.

## User Interface

### Delete Trigger

Users can delete a node by:
1. Right-clicking on any node in the hierarchy
2. Selecting "Delete" from the context menu
3. Confirming the deletion in the modal dialog

### Delete Options

When deleting a node with children, users are presented with three options:

1. **Delete node only** (leaf nodes)
   - Only available for nodes without children
   - Removes just the selected node

2. **Delete with all children**
   - Removes the node and all descendants
   - Cascade delete operation
   - Shows count of affected records

3. **Delete and move children to parent**
   - Removes only the selected node
   - Reparents children to the node's parent
   - Maintains hierarchy structure

## Implementation Details

### Frontend Components

#### ContextMenu (`/static/js/context-menu.js`)
- Checks delete permissions
- Shows delete option based on node type
- Triggers deletion dialog

#### DeleteManager (`/static/js/delete-manager.js`)
- Manages deletion UI flow
- Validates deletion options
- Stages deletions locally
- Provides undo capability

#### ChangeTracker (`/static/js/change-tracker.js`)
- Tracks pending deletions
- Manages undo/redo operations
- Prepares deletions for commit
- Updates visualization after commit

### Deletion Flow

1. **User initiates delete** → Context menu
2. **Confirmation dialog** → Select deletion type
3. **Local staging** → Mark for deletion
4. **Visual feedback** → Node marked with indicator
5. **Commit changes** → Send to backend
6. **Salesforce operation** → Actual deletion
7. **UI update** → Remove from visualization

### Backend Processing

#### Server Handler (`/app/web/server.py`)
```python
def handle_commit_changes(self):
    # Process deletions
    for deletion in deletions:
        node_id = deletion.get('nodeId')
        node_type = deletion.get('nodeType')
        delete_children = deletion.get('deleteChildren')
        new_parent_id = deletion.get('newParentId')
        
        # Use unified delete method
        success, result = salesforce_service.delete_with_children(
            node_id, node_type, delete_children, new_parent_id, connection_alias
        )
```

#### SalesforceService (`/app/services/salesforce_service.py`)

Handles three types of deletions:

1. **Product Deletion**
   ```python
   def _delete_product_with_components(self, product_id, delete_components, connection_alias):
       # Delete ProductRelatedComponent records
       # Delete ProductCategoryProduct associations
       # Delete the Product2 record
   ```

2. **Category Deletion**
   ```python
   def _delete_category_with_children(self, category_id, delete_children, new_parent_id, connection_alias):
       # Reparent or delete child categories
       # Handle recursive deletion
       # Delete the ProductCategory record
   ```

3. **Catalog Deletion**
   ```python
   def _delete_catalog_with_children(self, catalog_id, delete_children, connection_alias):
       # Handle catalog-level deletion
       # Delete the ProductCatalog record
   ```

## Salesforce Operations

### Object Relationships

1. **Product2**
   - Related: ProductRelatedComponent (as parent)
   - Related: ProductCategoryProduct
   - Children accessed via ProductRelatedComponent

2. **ProductCategory**
   - Self-referential via ParentCategoryId
   - Related: ProductCategoryProduct
   - Supports hierarchical structure

3. **ProductCatalog**
   - Top-level container
   - May have custom relationships

### Deletion Constraints

The system handles Salesforce constraints:

- **Cascade Delete**: Some relationships auto-delete
- **Restrict Delete**: Blocked if children exist
- **Reparent Option**: Move children before delete
- **Permission Checks**: User must have delete access

## Error Handling

### Common Errors

1. **INSUFFICIENT_ACCESS**
   - User lacks delete permission
   - Solution: Check user profile/permissions

2. **DELETE_FAILED - Cascade**
   - Child records prevent deletion
   - Solution: Use delete with children option

3. **ENTITY_IS_DELETED**
   - Record already deleted
   - Solution: Refresh the hierarchy

### Error Display

Errors are shown in a modal with:
- Clear error message
- Affected record details
- Suggested resolution
- Option to retry

## Undo/Redo Support

### Undo Deletion

Before commit:
1. Click undo button or press Ctrl+Z
2. Deletion is removed from pending changes
3. Node reappears in visualization

After commit:
- Cannot undo (Salesforce operation completed)
- Must manually recreate if needed

### Change Summary

View pending deletions:
1. Click "View Changes" button
2. See all staged deletions
3. Option to undo individual deletions
4. Commit all changes together

## Performance Considerations

### Bulk Operations

- Multiple deletions batched together
- Single API call for related records
- Efficient parent-child processing

### Large Hierarchies

- Recursive deletion optimized
- Progress feedback for long operations
- Chunking for very large deletes

## Best Practices

### User Guidelines

1. **Review children** before deleting parent nodes
2. **Use reparent option** to preserve data
3. **Commit regularly** to avoid large batches
4. **Check permissions** before bulk operations

### Administrator Guidelines

1. **Set appropriate permissions** for delete operations
2. **Configure cascade delete rules** in Salesforce
3. **Monitor bulk delete jobs** for large operations
4. **Backup critical data** before major changes

## Testing Scenarios

### Test Cases

1. **Delete leaf node**
   - Select product without children
   - Confirm deletion
   - Verify removal

2. **Delete with children**
   - Select category with subcategories
   - Choose "Delete with all children"
   - Verify cascade deletion

3. **Delete and reparent**
   - Select middle-tier node
   - Choose reparent option
   - Verify children moved up

4. **Undo deletion**
   - Stage deletion
   - Click undo
   - Verify node restored

5. **Error handling**
   - Attempt unauthorized delete
   - Verify error message
   - Check recovery options

## Future Enhancements

1. **Batch Selection**: Delete multiple nodes at once
2. **Soft Delete**: Archive instead of hard delete
3. **Deletion History**: Track who deleted what
4. **Restore Function**: Recover deleted records
5. **Cascade Preview**: Show all affected records
6. **Approval Workflow**: Require approval for deletions