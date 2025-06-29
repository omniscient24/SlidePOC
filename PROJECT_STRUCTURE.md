# Project Structure - Slide Revenue Cloud Data Load Application

**Last Updated:** June 26, 2025

## Overview
This document describes the organized folder structure for the Slide POC application.

## Directory Structure

```
POC/                               # Root project directory
│
├── app/                           # Core application code
│   ├── web/                      # Web server components
│   │   └── server.py            # Main HTTP server
│   ├── services/                # Business logic services
│   │   ├── connection_manager.py    # Salesforce connection management
│   │   ├── session_manager.py       # User session handling
│   │   └── file_upload_service.py   # File processing service
│   └── data/                    # Data access layer
│
├── templates/                    # HTML templates
│   ├── login.html               # Login page
│   ├── home.html                # Dashboard/home page
│   ├── data-management.html     # Main data management interface
│   └── connections.html         # Connection management page
│
├── static/                      # Static assets
│   └── css/                    # Stylesheets
│       └── style.css           # Main application styles
│
├── data/                        # Data files and templates
│   ├── Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx  # Master template (DO NOT MOVE)
│   ├── revenue_cloud_objects_discovery.json              # Object metadata
│   ├── README.md               # Data folder documentation
│   ├── templates/              # Template storage and configs
│   ├── uploads/                # Temporary upload storage
│   ├── workbooks/              # Archive of template versions
│   ├── csv-archives/           # Historical CSV files
│   └── import-export-logs/     # Operation logs
│
├── config/                      # Configuration files
│   └── settings/               # Application settings
│       └── app_config.py       # Main configuration
│
├── docs/                        # Documentation
│   ├── functional-requirements.md          # Feature specifications
│   ├── implementation-plan.md              # Development roadmap
│   ├── implementation-checklist.md         # Detailed task list
│   ├── technical-architecture.md           # Architecture details
│   ├── Technical_Implementation_Guide.md   # Implementation patterns
│   ├── Slide_Application_PRD.md           # Product requirements
│   ├── ui-style-guide.md                  # UI/UX guidelines
│   ├── TRANSACTION_OBJECTS_BEHAVIOR.md    # Object behavior docs
│   └── development-logs/                  # Development history
│       ├── COMPLETE_STATUS_FIX_SUMMARY.md
│       ├── MODAL_ALERTS_UPDATE_SUMMARY.md
│       ├── MODAL_HEADER_STYLING_UPDATE.md
│       ├── MODAL_SPACING_FINAL.md
│       ├── MODAL_SPACING_UPDATE.md
│       ├── MODAL_WIDTH_SCROLLBAR_FIX_SUMMARY.md
│       ├── STATUS_FIX_SUMMARY.md
│       ├── VIEW_FUNCTIONALITY_FIX_SUMMARY.md
│       └── VIEW_FUNCTIONALITY_TEST_REPORT.md
│
├── scripts/                     # Utility scripts
│   ├── startup/                # Server startup scripts
│   │   ├── launch_ui.py       # Python launcher
│   │   ├── simple_server.py   # Simple server variant
│   │   ├── start.py           # Basic starter
│   │   ├── start_fresh_server.py  # Fresh start script
│   │   ├── start_server.py    # Standard server start
│   │   └── start_server.sh    # Shell startup script
│   └── utilities/              # Utility scripts
│       ├── check_actual_sheets.py      # Excel sheet checker
│       ├── check_workbook_data.py      # Workbook validator
│       ├── verify_modal_fix.py         # Modal testing
│       ├── memory_helper.py            # Memory utilities
│       └── quick_memory.sh             # Memory management
│
├── salesforce/                  # Salesforce-specific files
│   ├── config/                 # SF configuration
│   │   ├── .forceignore       # Force.com ignore rules
│   │   ├── .prettierignore    # Prettier ignore rules
│   │   └── .prettierrc        # Prettier config
│   └── force-app/              # Metadata structure
│       └── main/
│           └── default/        # Default metadata
│
├── sessions/                    # Session storage
│   └── sessions.json           # Active sessions
│
├── archive/                     # Archived/old files
│
├── src/                        # Additional source code
│   └── web-ui/                # UI experiments
│
├── .claude/                    # Claude-specific files
├── .git/                       # Git repository
├── .gitignore                  # Git ignore rules
├── .husky/                     # Git hooks
├── .sf/                        # Salesforce CLI
├── .sfdx/                      # SFDX configuration
├── .vscode/                    # VS Code settings
│
├── start_slide.sh              # Main startup script
├── README.md                   # Project documentation
├── CHANGELOG.md                # Version history
├── requirements.txt            # Python dependencies
├── PROJECT_STRUCTURE.md        # This file
└── Slide_Revenue_Cloud_Data_Load_PRD.docx  # Product requirements

```

## Key Directories Explained

### `/app`
Core application logic organized by responsibility:
- `web/` - HTTP server and request handling
- `services/` - Business logic and service layer
- `data/` - Data access and persistence

### `/templates`
HTML templates for the web interface. Each page has its own template file.

### `/static`
Static assets like CSS, JavaScript (if any), and images. Currently only contains stylesheets.

### `/data`
Contains the master Excel template and any data files. This is where uploaded files are processed.

### `/docs`
Comprehensive documentation including requirements, implementation plans, and development logs.

### `/scripts`
Organized utility scripts:
- `startup/` - Various ways to start the server
- `utilities/` - Helper scripts for development and testing

## Quick Start

To start the application:
```bash
./start_slide.sh
```

Or manually:
```bash
python3 app/web/server.py
```

The application will be available at: http://localhost:8080

## File Naming Conventions

- Python files: `snake_case.py`
- HTML templates: `kebab-case.html`
- Documentation: `Title-Case-With-Hyphens.md`
- Configuration: `snake_case.py` or `.dotfile`

## Notes

- Session data is stored in `/sessions/sessions.json`
- Uploaded files are temporarily stored in `/data/` during processing
- The main Excel template must remain in `/data/` for the application to function
- All development logs have been moved to `/docs/development-logs/` for cleaner root directory