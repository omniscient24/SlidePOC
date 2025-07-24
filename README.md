# Revenue Cloud Migration Tool

A comprehensive solution for migrating from Salesforce CPQ to Revenue Cloud with a structured, phased approach.

## Project Structure

```
fortradp2Upload/
├── src/                              # Source code
│   ├── web-ui/                      # Web interface
│   ├── data-processing/             # Data processing scripts
│   └── utilities/                   # Utility scripts
├── data/                            # Data files
│   ├── templates/                   # Excel templates
│   │   ├── master/                 # Complete template
│   │   └── phase-templates/        # Phase-specific templates
│   ├── exports/                    # Export results
│   └── imports/                    # Import staging
├── salesforce/                     # Salesforce project files
├── docs/                          # Documentation
│   ├── SALESFORCE_INTEGRATION.md  # Salesforce integration guide
│   └── PRODUCT_HIERARCHY_DELETE.md # Delete functionality guide
├── logs/                          # Log files
└── archive/                       # Archived files
```

## Quick Start

1. **Launch the Web UI:**
   ```bash
   python3 launch_ui.py
   ```
   Then open http://localhost:8080 in your browser.

2. **Choose Your Path:**
   - **New Implementation**: Follow the guided 4-phase process
   - **Data Management**: Direct access to all Revenue Cloud objects

## Implementation Phases

### Phase 1: Foundation
Core objects that must be configured first:
- Legal Entity
- Tax Treatment
- Tax Policy  
- Tax Engine

### Phase 2: Products & Pricing
Product catalog and pricing configuration:
- Product Catalog, Categories, Products
- Product Attributes and Classifications
- Price Books and Entries

### Phase 3: Operations
Operational configurations:
- Cost Books
- Price Adjustments
- Billing Policies

### Phase 4: Finalization
Validation and go-live preparation

## Phase-Specific Templates

Individual Excel templates are available for each phase in:
`data/templates/phase-templates/`

Each phase folder contains:
- A consolidated phase template with all objects for that phase
- Individual object templates for granular uploads

## Features

- **Structured Implementation Process**: Ensures objects are created in correct dependency order
- **Phase-Specific Templates**: Smaller, focused workbooks for each implementation phase
- **Web-Based Interface**: Easy-to-use UI for both new implementations and ongoing management
- **Bulk Data Upload**: Supports Excel/CSV uploads to Salesforce
- **Progress Tracking**: Visual indicators for implementation progress
- **Integrated Validation**: Built-in validation directly in Sync Data page for immediate feedback
- **Column Filtering**: Advanced filtering with search, sort, and filter icons using Ant Design
- **Enhanced UI/UX**: Improved modal dialogs, responsive tables, and better visual feedback
- **Real-time Status Updates**: Live progress tracking during sync operations
- **Error Handling**: Comprehensive error messages and recovery options

### Data Management View Modal Enhancements

The View modals in the Data Management page now include:

- **Column Reordering**: Drag and drop table columns to reorder them. Column order is persisted in local storage
- **Column Sorting**: Click column headers to sort ascending/descending (all columns except Id)
- **Column Filtering**: Filter dropdowns on Type, Family, IsActive, IsRequired, DataType, IsDefault, and Status columns
- **Visual Enhancements**:
  - Vertical separators between columns for better readability
  - Wider modals (40% increase) for improved data visibility
  - Darker, more visible sort and filter icons
  - Reset Columns button to restore original column order
  - Reduced checkbox sizes on object category rows for better proportions
- **Improved Filter Behavior**:
  - Filter dropdowns stay open when selecting/deselecting checkboxes
  - Only close on Apply, Clear, or clicking outside
  - Proper boolean value handling (true/false filtering works correctly)
  - Search within filter options
- **Data Preservation**: All Excel columns preserved, even with null values
- **Responsive Design**: Minimum table height ensures filter dropdowns remain accessible
- **Excel Integration**: 
  - View Spreadsheet button opens Excel directly at the correct sheet for each object
  - Automatic sheet navigation using AppleScript (macOS)
  - Graceful handling of missing sheets with informative messages
- **Org Connection Display**: Current Salesforce org shown in header with wider dropdown for better visibility

### Data Management Delete Functionality

The Data Management page now supports advanced bulk record deletion with comprehensive dependency management:

- **Bulk Selection**: Select multiple records using checkboxes in View modals
- **Delete Records Button**: Dynamic button showing count of selected records
- **Smart Dependency Checking**: Automatic detection of related records that would block deletion
- **Hierarchical Dependency Visualization**:
  - Interactive tree-view showing all related records
  - Drill-down capability to explore nested dependencies
  - Record counts and details for each relationship level
  - Expand/collapse controls for managing complex dependency chains
- **Advanced Cascade Delete**:
  - Visual preview of all records that will be deleted
  - Transaction-based deletion with automatic rollback on errors
  - Progress tracking for multi-record cascade operations
  - Intelligent deletion ordering based on object relationships
- **Enhanced Modal-Based Error Handling**:
  - All errors displayed in formatted modal dialogs
  - Clear error descriptions in plain English
  - Context-aware suggested solutions
  - Detailed dependency information with record names and relationships
  - No toast notifications - all feedback through consistent modal interface
- **Excel Synchronization**: Automatic Excel file updates after successful deletions
- **View Refresh**: Automatic view refresh to show updated data after operations
- **Configurable Object Display**: Custom fields shown per object type for better context

### Salesforce Data Synchronization

The Sync Data functionality includes:

- **Object-Level Sync**: Sync individual objects from Salesforce to local Excel files
- **Real-Time Updates**: Pull latest data from Salesforce org to ensure accuracy
- **Field Mapping**: Intelligent field mapping for each Revenue Cloud object
- **Error Recovery**: Graceful handling of sync failures with detailed error messages
- **Progress Tracking**: Visual indicators for sync status per object
- **Enhanced Table Features**:
  - **Column Sorting**: Click column headers to sort data ascending/descending
  - **Status Filtering**: Filter objects by sync status (Synced, Not Synced, Empty)
  - **Visual Enhancements**: Improved icon visibility with drop shadows and proper contrast
  - **Column Separators**: Subtle vertical lines between columns for better readability
  - **Improved Category Rows**: Fixed hover behavior to maintain consistent styling

### Product Hierarchy Visualization

A powerful D3.js-based visualization tool for exploring and managing Salesforce product hierarchies:

- **Interactive Tree View**: Visual representation of product relationships and bundle structures
- **Fixed Column Layout**: Products organized by hierarchy level with color-coded columns
- **Default Collapsed State**: Always loads with hierarchy collapsed - users expand nodes as needed for optimal performance
- **Drag & Drop**: Vertically reposition nodes while maintaining hierarchical structure
- **Expand/Collapse**: Navigate complex hierarchies with +/- controls
- **Bundle Support**: Automatic visualization of bundle components and relationships
- **Node Details**: Click any product to view detailed information
- **Zoom Controls**: Mouse wheel zoom for detailed inspection
- **Responsive Design**: Full-width layout that adapts to screen size

#### Add Catalog Feature

The Product Hierarchy page now includes the ability to create new catalogs directly from the UI:

- **Add Catalog Button**: Hover over any existing catalog to reveal a + icon
- **Comprehensive Modal Form**: Create new catalogs with all required fields:
  - Name (required)
  - Code (auto-generated from Name, editable)
  - Description
  - Catalog Type (Sales/Service)
  - Effective Start Date
  - Effective End Date
  - Is Active toggle
- **Field Validation**: 
  - Auto-generation of Code field from Name (uppercase, special chars removed)
  - Date range validation (end date must be after start date)
  - Required field validation
- **Real-time UI Updates**: 
  - New catalogs appear immediately in the hierarchy without page reload
  - Temporary IDs are replaced with Salesforce IDs after commit
  - Excel file automatically synchronized
- **Empty Catalog Creation**: New catalogs start empty without inheriting categories/products
- **Change Tracking**: All additions tracked and can be committed to Salesforce
- **Visual Feedback**: Success modals with "Close & Update View" button for seamless workflow

Access the visualization at `product-hierarchy-visualization.html` or through the web UI.

## Documentation

- [Upload Guide](docs/REVENUE_CLOUD_UPLOAD_GUIDE.md) - Detailed upload instructions
- [UI Guide](docs/UI_README.md) - Web interface documentation
- [Product Hierarchy Visualization](docs/features/product-hierarchy-visualization.md) - Interactive product tree visualization

## Requirements

- Python 3.8+
- Salesforce CLI
- Valid Salesforce org with Revenue Cloud enabled
- Required Python packages: pandas, openpyxl