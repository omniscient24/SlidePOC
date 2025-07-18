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

The Data Management page now supports bulk record deletion with the following features:

- **Bulk Selection**: Select multiple records using checkboxes in View modals
- **Delete Records Button**: Dynamic button showing count of selected records
- **Dependency Checking**: Automatic detection of related records that would block deletion
- **Cascade Delete**: Option to delete records along with their dependencies when needed
- **Modal-Based Error Handling**: All errors displayed in formatted modal dialogs with:
  - Clear error descriptions in plain English
  - Suggested solutions for common issues
  - Related record listings for dependency errors
- **Excel Synchronization**: Automatic Excel file updates after successful deletions
- **View Refresh**: Automatic view refresh to show updated data after operations

### Salesforce Data Synchronization

The Sync Data functionality includes:

- **Object-Level Sync**: Sync individual objects from Salesforce to local Excel files
- **Real-Time Updates**: Pull latest data from Salesforce org to ensure accuracy
- **Field Mapping**: Intelligent field mapping for each Revenue Cloud object
- **Error Recovery**: Graceful handling of sync failures with detailed error messages
- **Progress Tracking**: Visual indicators for sync status per object

## Documentation

- [Upload Guide](docs/REVENUE_CLOUD_UPLOAD_GUIDE.md) - Detailed upload instructions
- [UI Guide](docs/UI_README.md) - Web interface documentation

## Requirements

- Python 3.8+
- Salesforce CLI
- Valid Salesforce org with Revenue Cloud enabled
- Required Python packages: pandas, openpyxl