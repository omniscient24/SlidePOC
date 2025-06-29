# Data Folder Structure

This folder contains all data files used by the Slide Revenue Cloud Data Load application.

## Main Files

### Active Templates
- `Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx` - The master Excel template used by the application. DO NOT MOVE OR DELETE.
- `revenue_cloud_objects_discovery.json` - Object metadata and configuration

## Subdirectories

### `/templates`
Contains template-related files and configurations:
- Master template storage
- Template variations
- Mapping configurations

### `/uploads`
Temporary storage for user-uploaded files during processing.

### `/workbooks`
Archive of previous template versions:
- `Revenue_Cloud_Clean_Template.xlsx`
- `Revenue_Cloud_Complete_Upload_Template.xlsx`

### `/csv-archives`
Historical CSV files and exports from development:
- Various CSV output directories
- Individual CSV files from testing
- Import/export results

### `/import-export-logs`
Log files from import/export operations:
- Summary reports
- Error logs
- Processing results

## Important Notes

1. The `Revenue_Cloud_Complete_Upload_Template_FINAL.xlsx` file must remain in the root of the data folder for the application to function correctly.

2. The `/uploads` folder is cleared periodically and should not be used for permanent storage.

3. Files in `/csv-archives` are historical and can be deleted if no longer needed.

4. The `revenue_cloud_objects_discovery.json` file contains the object configuration used by the application.