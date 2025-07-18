# Data Management View Modal Enhancements

This document describes the technical implementation of the enhanced View modals in the Data Management page.

## Overview

The View modals have been significantly enhanced to provide better data visualization and manipulation capabilities, including column reordering, sorting, filtering, and improved UI/UX.

## Features Implemented

### 1. Column Reordering (Drag & Drop)

**Implementation**: Uses HTML5 Drag and Drop API with a namespaced `ModalColumnManager` object to avoid conflicts.

```javascript
const ModalColumnManager = {
    draggedElement: null,
    draggedIndex: null,
    objectApiName: null,
    
    initializeColumnDragging(modalId, objectApiName) {
        // Initialization logic
    }
};
```

**Key Features**:
- Drag any column header to reorder
- Visual feedback during drag (opacity change)
- Column order persisted in localStorage
- Reset button to restore original order

**Technical Details**:
- Uses `draggable="true"` attribute on table headers
- Implements dragstart, dragover, drop, and dragend events
- Stores column order as array in localStorage with key pattern: `modalColumnOrder_${objectApiName}`

### 2. Column Sorting

**Implementation**: Three-state sorting (ascending, descending, original) on all columns except Id.

```javascript
function sortModalColumn(column) {
    // Cycles through: original -> ascending -> descending -> original
}
```

**Features**:
- Click column header to sort
- Visual indicators (▲ ▼) for sort direction
- Maintains sort state across filter operations

### 3. Column Filtering

**Implementation**: Dropdown filters with checkbox selections for specific column types.

**Filtered Columns**:
- Type
- Family  
- IsActive
- IsRequired
- DataType
- IsDefault
- Status

**Filter Structure**:
```html
<div class="filter-dropdown">
    <div class="filter-search">
        <input type="text" placeholder="Search...">
    </div>
    <div class="filter-options">
        <!-- Checkbox options -->
    </div>
    <div class="filter-actions">
        <button class="btn-clear">Clear</button>
        <button class="btn-apply">Apply</button>
    </div>
</div>
```

**Key Behaviors**:
- Dropdowns stay open during selection (only close on Apply/Clear/outside click)
- Search within filter options
- Toggle all functionality
- Proper boolean value handling

### 4. Boolean Value Handling

**Problem**: Boolean false values were being stringified as empty strings, causing filtering issues.

**Solution**:
```javascript
// Explicit boolean to string conversion
if (value === false) {
    value = 'false';
} else if (value === true) {
    value = 'true';
} else {
    value = String(value || '');
}
```

### 5. Data Preservation

**Server-side fix** in `/app/web/server.py`:
```python
# Preserve all columns even with null values
for key, value in record.items():
    if pd.isna(value):
        cleaned_record[key] = None  # Keep the key with None value
    else:
        cleaned_record[key] = value
```

### 6. UI/UX Improvements

**Visual Enhancements**:
- Vertical separators between columns: `border-right: 1px solid #e0e0e0`
- Wider modals: 40% increase (1175px → 1645px, 1600px → 2240px)
- Darker icons for better visibility
- Light blue themed Reset button (#e3f2fd background, #1890ff hover)

**Responsive Design**:
- Minimum table height (400px) ensures filter dropdowns remain accessible
- Applied to `.table-wrapper` instead of modal itself for better layout

## Technical Architecture

### State Management
- Column order: localStorage
- Sort state: In-memory JavaScript variables
- Filter state: In-memory with initialization on first access

### Event Handling
- Uses event delegation for dynamic content
- `stopPropagation()` to prevent event bubbling conflicts
- Separate handlers for sort and filter actions

### Performance Considerations
- Filters applied client-side for responsive UI
- Column reordering uses efficient DOM manipulation
- No server round-trips for view operations

## Browser Compatibility
- HTML5 Drag and Drop API (all modern browsers)
- localStorage (all modern browsers)
- CSS flexbox and modern properties

## Additional Features

### 7. Excel Integration

**View Spreadsheet Functionality**:
- Replaced "Download Full Workbook" button with "View Spreadsheet"
- Opens Excel directly at the correct sheet for the selected object
- Uses AppleScript on macOS for sheet navigation

**Implementation**:
```javascript
async function viewSpreadsheet(apiName, sheetName) {
    const response = await fetch('/api/workbook/open', {
        method: 'POST',
        body: JSON.stringify({ 
            path: workbookPath,
            sheet: sheetName,
            apiName: apiName
        })
    });
}
```

**Server-side AppleScript**:
```python
applescript = f'''
tell application "Microsoft Excel"
    open "{workbook_path}"
    activate
    tell active workbook
        try
            activate object worksheet "{sheet_name}"
        on error
            -- Sheet not found, just open the workbook
        end try
    end tell
end tell
'''
```

### 8. UI Refinements

**Checkbox Sizing**:
- Reduced category row checkboxes from 18px to 14px for better visual proportions
- Applied to both checkbox and label elements

**Org Dropdown Enhancement**:
- Increased width from auto to 250px for better visibility
- Fixed "Loading..." issue by implementing /api/session endpoint
- Displays actual connected Salesforce org name

### 9. API Endpoints

**New Endpoints Added**:
- `/api/workbook/open` - Opens Excel at specific sheet
- `/api/session` - Provides current org connection info
- `/api/objects/counts` - Returns record counts for each object

## Future Enhancements
- Column width adjustment
- Export filtered/sorted data
- Save custom view configurations
- Server-side sorting/filtering for large datasets
- Cross-platform Excel integration (Windows support)
- Multi-sheet navigation history