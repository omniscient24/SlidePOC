# Add Product Category Feature Design

## Overview
This document outlines the design for adding Product Categories through the Product Hierarchy visualization interface.

## User Journey
1. User hovers over a catalog or category node
2. A + icon appears on the right side of the node
3. User clicks the + icon
4. Modal dialog opens with category creation form
5. User enters category name
6. User clicks "Add Category"
7. New category appears in the hierarchy immediately
8. User can continue adding more nodes or commit changes to Salesforce

## Technical Design

### Frontend Components

#### 1. Add Icon Enhancement
Extend the existing add icon functionality to work on category nodes:

```javascript
// In add-node-manager.js
addIconsToNodes() {
    d3.selectAll('g.node').each(function(d) {
        const node = d3.select(this);
        
        // Add icon to catalogs AND categories
        if (d.type === 'catalog' || d.type === 'category' || d.type === 'subcategory') {
            // Add the + icon
            node.append('text')
                .attr('class', 'add-icon')
                .attr('x', d.width / 2 + 20)
                .attr('y', 5)
                .text('+')
                .on('click', (event, d) => {
                    event.stopPropagation();
                    if (d.type === 'catalog') {
                        this.showAddCategoryModal(d);
                    } else if (d.type === 'category' || d.type === 'subcategory') {
                        this.showAddCategoryModal(d);
                    }
                });
        }
    });
}
```

#### 2. Add Category Modal
New modal specifically for category creation:

```javascript
showAddCategoryModal(parentNode) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay active';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Add Product Category</h2>
                <button class="close-button">&times;</button>
            </div>
            <div class="modal-body">
                <form id="addCategoryForm">
                    <div class="form-group">
                        <label for="categoryName">Name <span class="required">*</span></label>
                        <input type="text" id="categoryName" class="form-control" 
                               maxlength="255" required>
                        <div class="error-message" id="categoryNameError"></div>
                    </div>
                    
                    <div class="parent-info">
                        <p>Adding to ${parentNode.type === 'catalog' ? 'Catalog' : 'Category'}: 
                           <strong>${parentNode.name}</strong></p>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" 
                        onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button type="button" class="btn btn-primary" 
                        onclick="addNodeManager.submitAddCategory()">Add Category</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Store parent info for submission
    this.currentParentNode = parentNode;
    
    // Focus on name field
    document.getElementById('categoryName').focus();
}
```

#### 3. Category Submission
Handle category creation and tracking:

```javascript
submitAddCategory() {
    if (!this.validateAddCategoryForm()) {
        return;
    }
    
    const nameInput = document.getElementById('categoryName');
    const parentNode = this.currentParentNode;
    
    // Generate temporary ID
    const tempId = `temp_category_${Date.now()}`;
    
    // Create category data
    const categoryData = {
        nodeId: tempId,
        type: 'category',
        name: nameInput.value.trim(),
        parentType: parentNode.type,
        parentId: parentNode.id,
        // Only set ParentCategoryId if parent is a category
        parentCategoryId: (parentNode.type === 'category' || parentNode.type === 'subcategory') 
            ? parentNode.id : null,
        tempId: tempId,
        timestamp: new Date().toISOString()
    };
    
    // Track the addition
    if (window.changeTracker) {
        changeTracker.trackAddition(categoryData);
    }
    
    // Add to visualization immediately
    this.addCategoryToVisualization(categoryData, parentNode);
    
    // Close modal
    document.querySelector('.modal-overlay').remove();
    
    // Show success feedback
    this.showSuccessFeedback(`Category "${categoryData.name}" added successfully`);
}
```

### Backend Components

#### 1. Server Handler Update
Modify the commit handler to process category additions:

```python
# In server.py - handle_commit_changes()
elif addition.get('type') == 'category':
    # Create ProductCategory
    category_data = {
        'Name': addition.get('name'),
        'ParentCategoryId': addition.get('parentCategoryId') or ''
    }
    
    result = self.create_salesforce_record('ProductCategory', category_data)
    if result.get('success'):
        results['addition_details'].append({
            'temp_id': node_id,
            'real_id': result.get('id'),
            'type': 'category',
            'name': addition.get('name')
        })
```

#### 2. Hierarchy Building Update
Ensure new categories are properly integrated:

```python
# Handle temporary categories in hierarchy
if category_id.startswith('temp_category_'):
    # This is a newly added category
    is_temp = True
    # Still add to hierarchy for display
```

### Data Model

#### ProductCategory Structure
```javascript
{
    nodeId: "temp_category_1234567890",
    type: "category",
    name: "New Category Name",
    parentType: "catalog|category|subcategory",
    parentId: "parent-node-id",
    parentCategoryId: "parent-category-id or null",
    tempId: "temp_category_1234567890",
    timestamp: "2025-07-24T10:30:00.000Z"
}
```

### Visual Design

#### Add Icon Styling
- Same style as catalog add icon
- Green color (#4CAF50)
- Circle background
- Visible on hover
- Positioned to the right of node

#### Modal Design
- Consistent with Add Catalog modal
- Simpler form (only Name field required)
- Clear parent context display
- Standard modal controls

### Validation Rules

1. **Name Validation**
   - Required field
   - Maximum 255 characters
   - No special validation (allow any characters)

2. **Hierarchy Validation**
   - Categories can be added to catalogs (root level)
   - Categories can be added to other categories (nested)
   - No depth limit imposed by UI

3. **Parent Validation**
   - Cannot add to a node marked for deletion
   - Parent must exist in current hierarchy

### Error Handling

1. **Field Validation Errors**
   - Display inline under field
   - Prevent form submission
   - Clear on valid input

2. **Commit Errors**
   - Display in modal
   - Provide specific error messages
   - Option to retry

3. **Network Errors**
   - Graceful degradation
   - Preserve local changes
   - Retry mechanism

### Integration Points

1. **Change Tracker**
   - Use existing trackAddition method
   - Category stored in additions Map
   - Included in commit payload

2. **D3 Visualization**
   - Add node to parent's children array
   - Trigger hierarchy update
   - Maintain visual consistency

3. **Excel Sync**
   - New categories added to ProductCategory sheet
   - Parent relationships maintained
   - IDs updated after commit

## Implementation Phases

### Phase 1: Basic UI (Current)
- Add icon on category nodes
- Modal dialog creation
- Form validation

### Phase 2: Integration
- Change tracker integration
- Visualization updates
- Backend processing

### Phase 3: Polish
- Error handling
- Success feedback
- UI animations

## Success Criteria
- Users can add categories to any catalog or category
- Categories appear immediately in visualization
- Changes persist after commit
- Excel file stays synchronized
- No console errors
- Smooth user experience