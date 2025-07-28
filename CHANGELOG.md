# Changelog

All notable changes to the Revenue Cloud Migration Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2025-07-28] - Add Product Functionality & Major Fixes

### Added
- **Complete Add Product Functionality**: Full implementation of product creation in hierarchy
  - Product modal with comprehensive form fields
  - Auto-generation for ProductCode and SKU with customizable patterns
  - Real-time validation and field formatting
  - Integration with ChangeTracker for staging
  - ProductCategoryProduct junction record creation
  - Automatic hierarchy refresh after product addition
  - Support for all Product2 fields: Name, Description, ProductCode, SKU, Family, IsActive

- **Enhanced Delete Functionality**: Improved deletion for all node types
  - Fixed delete modal for subcategory nodes
  - Proper cascade handling for nodes with children
  - Salesforce deletion with proper cleanup

- **Comprehensive Testing Suite**:
  - Puppeteer browser automation tests
  - Direct Salesforce query verification utilities
  - Manual testing guides and procedures
  - ProductCategoryProduct sync testing

### Fixed
- **Event Listener Attachment**: Fixed dynamic button event listeners not attaching properly
  - Add Product button now responds correctly
  - Event listeners re-attached when modals are shown
  
- **ChangeTracker Enhancements**:
  - Fixed circular reference error in saveToSession
  - Now preserves all product fields including categoryId
  - Better field handling for all node types
  
- **Product Creation Flow**:
  - Fixed bulk upload not returning product IDs
  - Implemented query-based ID retrieval after creation
  - Fixed junction record creation for product-category relationships
  
- **Hierarchy Refresh**: 
  - Fixed refresh reliability after commits
  - Proper node expansion state preservation
  - Consistent UI updates after operations

### Changed
- **Modal Management**: Improved modal state handling and transitions
- **Error Handling**: Enhanced error messages and recovery options
- **Logging**: Added comprehensive debug logging throughout commit flow

### Technical Details
- Created `/static/js/add-node-manager.js` enhancements for product handling
- Modified `/app/api/changes.py` for better product creation flow
- Updated `/static/js/change-tracker.js` with circular reference fixes
- Enhanced `/templates/product-hierarchy.html` with product modal

### Known Issues
- ProductCategoryProduct sheet may need manual column structure update
- Products may require manual sync to appear in hierarchy

## [2025-07-25] - Product Hierarchy Sync Feature

### Added
- **Manual Sync Button**: Added "Sync with Salesforce" button to Product Hierarchy page
  - Allows manual re-synchronization of hierarchy data with Salesforce
  - Essential for resolving out-of-sync states during development
  - Located in the top toolbar next to org selector
  
- **Sync Progress Modal**: Comprehensive progress tracking during sync
  - Real-time progress bar with percentage
  - Animated stripes showing active sync
  - Individual status tracking for each object type:
    - Product Catalogs
    - Product Categories
    - Product Component Groups
    - Product Components
  - Shows record counts for each synced object
  - Clear success/error messaging in plain English
  
- **Sync Implementation** (`product-hierarchy-sync.js`):
  - Reuses existing sync patterns from Data Management page
  - Calls existing `/api/sync/{objectName}` endpoints
  - Automatic page refresh after successful sync
  - Cancel functionality during sync operation
  - Error handling with detailed messages

### Technical Details
- Created `static/js/product-hierarchy-sync.js` module
- Added script reference to product-hierarchy.html
- No backend changes needed (uses existing sync endpoints)
- Progress modal follows UI/UX patterns from Data Management sync
- Test page created: `test-product-hierarchy-sync.html`

## [2025-07-25] - Add All ProductCategory Fields

### Added
- **Complete ProductCategory Field Support**: Added all available fields to Add Category modal
  - IsNavigational (checkbox) - Required field for menu display
  - Description (textarea, 255 chars) - Category description
  - SortOrder (number) - Display order in lists
  - Code (text, 255 chars) - Unique identifier code
  - ExternalId__c (text, 20 chars) - External system reference
  - All fields properly validated with max length constraints
  - Backend updated to handle all new fields in commit process
  - Field data correctly tracked in changeTracker for pending changes

### Technical Details
- Used Salesforce Integration Agent to query ProductCategory metadata
- Discovered 8 createable fields total (Name, CatalogId, IsNavigational required)
- Updated modal UI with proper field grouping (required vs optional)
- Enhanced backend record_data to include all new fields
- Created comprehensive test page (test-category-all-fields.html)
- Verified end-to-end functionality for all fields

## [2025-07-25] - Category Creation Critical Fixes

### Fixed (Update 2)
- **Add Category Button Not Working**: Fixed button click handler issues
  - Fixed malformed try-catch block in submitAddCategory method (indentation was breaking the code)
  - Added attachCategoryModalEventListeners method to properly attach event listeners
  - Event listeners are now re-attached each time modal is shown
  - Used proper function context binding with `self` reference
  - Replaced inline onclick with addEventListener for better reliability

## [2025-07-25] - Category Creation Critical Fix

### Fixed
- **ProductCategory Creation Failure**: Fixed categories not being created in Salesforce
  - Discovered that CatalogId is a required field for ProductCategory object
  - Added findCatalogId() method to traverse hierarchy and find parent catalog
  - Updated frontend to include catalogId in category data
  - Modified backend to pass CatalogId when creating ProductCategory records
  - ProductCategory now successfully creates with proper catalog association
  
- **Modal Freeze Issue**: Fixed "Close & Update View" button not responding after commit
  - Changed event handler from arrow function to regular function to preserve context
  - Removed duplicate modal removal that was causing the freeze
  - Added proper fallback to page reload if handleSuccessfulCommit is unavailable
  
- **Visualization Refresh**: Added updateData method to hierarchyVisualization
  - Properly refreshes the D3 visualization after successful commit
  - Clears and rebuilds the tree with new data
  - Updates column headers after data refresh

### Added
- **Debug Tools**: Created comprehensive debugging utilities
  - `test-category-creation.html` - Isolated test environment
  - `test-category-complete-flow.html` - Full flow testing with catalog ID
  - `debug-category-issue.md` - Comprehensive debugging guide
  - `debug-commit-flow.js` - Runtime debugging hooks
  - Enhanced console logging with [ADD CATEGORY] and [COMMIT] prefixes

## [2025-07-24] - Add Catalog & Category Features

### Added Product Category Feature
- **Add Category Functionality**: New feature to create Product Categories within the hierarchy
  - Hover-activated + icon on catalog and category nodes
  - Simple modal form with Name field (required, 255 char limit)
  - Parent context display showing where category will be added
  - Automatic ParentCategoryId assignment based on parent type
  - Real-time visualization updates without page reload
  - Change tracking integration for uncommitted changes
  - Backend support for ProductCategory creation in Salesforce
  - Comprehensive test suite following TDD principles

### Added Catalog Feature
- **Add Catalog Functionality**: New feature to create Product Catalogs directly from the Product Hierarchy visualization
  - Hover-activated + icon on catalog nodes
  - Comprehensive modal form with all ProductCatalog fields
  - Auto-generation of Code field from Name
  - Date range validation for Effective Start/End dates
  - Real-time UI updates without page reload
  - Automatic Excel file synchronization

### Fixed
- **Modal Visibility**: Added missing `active` class to success/error modals
- **Button Event Handling**: Fixed "Close & Update View" button click handler
- **New Catalog Isolation**: New catalogs now start empty without inheriting categories/products from existing catalogs
- **Circular JSON Error**: Resolved issue when serializing node additions for commit

### Changed
- **Change Tracker**: Enhanced with `handleSuccessfulCommit` and `refreshHierarchyData` methods
- **Server Response**: Commit endpoint now returns `addition_details` with temp_id to real_id mapping
- **Upload Service**: Improved result structure handling for both insert and upsert operations

### Technical Details
- Added comprehensive Test-Driven Development (TDD) instructions to CLAUDE.md
- Created test suite for new catalog fields validation
- Enhanced debugging with console logging for troubleshooting
- Implemented smart catalog filtering to prevent category inheritance for new catalogs

## [2025-07-23] - Product Hierarchy Visualization Enhancements

### Fixed

#### Bundle Components Display
- Fixed issue where all products were showing in the Bundle Components column instead of only actual bundle components
- Implemented proper filtering to ensure only components (children of bundle products) appear in the Bundle Components column
- Added `_positioned` flag to prevent nodes from being processed multiple times during layout calculation

#### Node Overlap Issues
- Fixed overlapping nodes when expanding/collapsing hierarchy levels
- Implemented dynamic spacing (15px) between all nodes
- Added `preventOverlaps()` function that ensures minimum spacing between nodes in the same column
- Updated drag behavior to include collision detection preventing nodes from overlapping during manual repositioning
- Reset manual Y positions when expanding/collapsing to allow proper automatic layout

#### Text Wrapping and Dynamic Node Heights
- Fixed text wrapping for all node titles
- Implemented dynamic node height calculation based on wrapped text content
- Added `calculateTextHeight()` function that measures required height for multi-line text
- Updated rectangle heights and Y positions to accommodate variable node heights
- Ensured text wrapping is reapplied when nodes are updated

#### Column Header Alignment
- Fixed column header misalignment when bundle components are expanded
- Changed column detection to use actual node X positions instead of recalculating
- Created dynamic `getColumnInfo()` function that adapts to variable category depths
- Synchronized header updates with node transition animations
- Headers now properly reflect actual column structure regardless of hierarchy depth

#### UI/UX Improvements
- Bundle products now appear first in the Product column, before non-bundle products
- Expand/collapse buttons properly positioned at the right edge of nodes
- Hierarchy starts in collapsed state (only root and catalog visible initially)
- Fixed initial positioning of products to be properly centered around their parent

### Technical Details
- Updated D3.js visualization with improved layout algorithm
- Enhanced collision detection for draggable nodes
- Improved transition timing for smooth animations
- Better separation of concerns between layout calculation and visual updates

## [2025-07-19] - Product Hierarchy Edit Functionality Phase 1

### Added

#### Database Schema and Migrations
- Created database migration system (`app/utils/db_migrate.py`)
- Added migration for edit functionality tables:
  - `edit_permissions` - User permission management
  - `field_config` - Field configuration per organization
  - `change_history` - Track all changes (for future phases)
  - `audit_log` - Comprehensive audit trail
  - `edit_conflicts` - Conflict resolution (for future phases)
- Added indexes for performance optimization
- Created migration to grant default admin permissions

#### Backend Services and APIs
- **Edit Service** (`app/services/edit_service.py`)
  - Permission management (5 levels: view_only, edit_basic, edit_structure, full_edit, admin)
  - Field configuration management
  - Validation framework
  - Audit logging
  
- **API Endpoints**:
  - `GET /api/edit/permissions` - Get user permissions
  - `POST /api/edit/permissions` - Update user permissions (admin only)
  - `GET /api/edit/field-config` - Get field configuration
  - `POST /api/edit/field-config` - Update field configuration (admin only)
  
- **Database Utilities** (`app/utils/db.py`)
  - Centralized database connection management

#### Admin Settings Page
- **Frontend** (`templates/admin-settings.html`)
  - Three-tab interface: User Permissions, Field Configuration, Audit Log
  - Ant Design integration for better UX
  - Organization selector for multi-org support
  - Responsive design
  
- **Styling** (`static/css/admin-settings.css`)
  - Custom styles for admin interface
  - Permission level color coding
  - Modal dialogs for user actions
  
- **JavaScript** (`static/js/admin-settings.js`)
  - Dynamic permission management
  - Field configuration editor
  - Real-time validation
  - Organization switching

### Documentation
- **Product Requirements Document** (`docs/PRD_Product_Hierarchy_Edit_Functionality.md`)
  - Comprehensive requirements for edit functionality
  - User stories and success metrics
  - Detailed functional requirements
  - Technical specifications
  
- **Implementation Plan** (`docs/Implementation_Plan_Edit_Functionality.md`)
  - Phased implementation approach
  - Detailed technical implementation guide
  - Code examples and patterns
  - Security considerations

### Modified
- **Server Routes** (`app/web/server.py`)
  - Added routes for admin settings page
  - Added edit API endpoints
  - Fixed `send_json_response` to support status codes
  - Enhanced `/api/connections` to include active connection ID

### Infrastructure
- **Migrations**:
  - `001_create_edit_tables.sql` - Core edit functionality schema
  - `002_add_default_admin.sql` - Default admin permissions

### Key Features Implemented

1. **Role-Based Access Control (RBAC)**
   - 5 permission levels with different capabilities
   - Per-organization permission management
   - Admin-only configuration access

2. **Field Configuration System**
   - Configure which fields are editable
   - Set required fields and validation rules
   - Permission-based field access
   - Support for multiple Salesforce objects

3. **Audit Trail**
   - All actions logged with user, timestamp, and details
   - IP address and session tracking
   - Prepared for compliance requirements

4. **Multi-Organization Support**
   - Separate configurations per Salesforce org
   - Easy switching between organizations
   - Isolated permission management

### Technical Improvements
- Database migration system for version control
- Centralized error handling
- Consistent API response format
- Security-first design approach

### Pending (Future Phases)
- Phase 2: Inline field editing in product hierarchy
- Phase 3: Drag-and-drop operations
- Phase 4: Two-stage commit process
- Phase 5: Change history and rollback
- Phase 6: Polish and testing

### Notes
- Admin settings accessible at `/admin-settings` (requires admin permissions)
- Default user granted admin permissions for all connected orgs
- Foundation laid for comprehensive edit functionality in product hierarchy visualization

## [Unreleased] - 2025-06-24

### Added
- **Integrated Validation in Sync Data Page**: Validation functionality now built directly into the Sync Data page, eliminating the need for a separate Validate tab
- **Column Filtering with Ant Design Icons**: Enhanced table filtering with search, sort, and filter icons for better data management
- **Real-time Sync Progress Tracking**: Live status updates showing records processed during sync operations
- **Enhanced Error Handling**: Improved error messages with clear recovery options

### Changed
- **Improved Modal Dialogs**: Better spacing, responsive design, and consistent styling across all modals
- **Table UI Enhancements**: Responsive tables with better column management and visual feedback
- **Status Display**: Fixed empty status issues and improved visual indicators
- **View Functionality**: Enhanced view modal with proper data loading and error handling

### Fixed
- **Modal Width and Scrollbar Issues**: Fixed horizontal scrollbars appearing unnecessarily in modals
- **Status Cell Display**: Resolved issues with empty status cells not showing proper styling
- **View Modal Data Loading**: Fixed data not loading properly when viewing records
- **Button Spacing**: Corrected button area margins and padding for consistent UI
- **Table Responsiveness**: Improved table layout on different screen sizes

### Technical Improvements
- **Code Organization**: Better separation of concerns between validation and sync logic
- **Performance**: Optimized data loading and rendering for large datasets
- **Error Recovery**: Added graceful error handling with user-friendly messages
- **UI Consistency**: Standardized spacing, colors, and component styling

## [1.0.0] - 2025-06-20

### Initial Release
- Structured 4-phase implementation process
- Web-based interface for Revenue Cloud migration
- Excel/CSV upload support
- Phase-specific templates
- Salesforce integration via CLI
- Progress tracking and reporting