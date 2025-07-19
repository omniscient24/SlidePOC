# Changelog

All notable changes to the Revenue Cloud Migration Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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