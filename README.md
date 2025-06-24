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

## Documentation

- [Upload Guide](docs/REVENUE_CLOUD_UPLOAD_GUIDE.md) - Detailed upload instructions
- [UI Guide](docs/UI_README.md) - Web interface documentation

## Requirements

- Python 3.8+
- Salesforce CLI
- Valid Salesforce org with Revenue Cloud enabled
- Required Python packages: pandas, openpyxl