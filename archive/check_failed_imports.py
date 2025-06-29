#!/usr/bin/env python3
"""
Check specific failures from the last import attempts.
"""

import subprocess
import pandas as pd
from pathlib import Path

def get_job_failures(job_id, object_name):
    """Get failure details for a specific job."""
    print(f"\n{'='*60}")
    print(f"CHECKING {object_name} FAILURES (Job: {job_id})")
    print('='*60)
    
    cmd = [
        'sf', 'data', 'bulk', 'results',
        '--job-id', job_id,
        '--target-org', 'fortradp2'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Look for the failed records CSV
        failed_file = Path(f"{job_id}-failed-records.csv")
        if failed_file.exists():
            df = pd.read_csv(failed_file)
            
            # Show first few failures
            print(f"\nFound {len(df)} failed records. First 5:")
            for idx, row in df.head().iterrows():
                print(f"\nRecord {idx + 1}:")
                if 'Name' in df.columns:
                    print(f"  Name: {row.get('Name', 'N/A')}")
                if 'Code' in df.columns:
                    print(f"  Code: {row.get('Code', 'N/A')}")
                print(f"  Error: {row.get('sf__Error', 'Unknown error')}")
            
            # Clean up
            failed_file.unlink()
            success_file = Path(f"{job_id}-success-records.csv")
            if success_file.exists():
                success_file.unlink()
        else:
            print("No failed records file found")
    else:
        print(f"Error getting job results: {result.stderr}")

def find_recent_job_ids():
    """Find recent bulk job IDs from the console output."""
    print("\nLooking for recent failed bulk jobs...")
    
    # Get recent jobs
    cmd = [
        'sf', 'data', 'bulk', 'status',
        '--target-org', 'fortradp2',
        '--json'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        import json
        data = json.loads(result.stdout)
        if 'result' in data and isinstance(data['result'], list):
            # Filter for failed jobs
            failed_jobs = [
                job for job in data['result']
                if job.get('state') == 'JobComplete' and 
                   job.get('numberRecordsFailed', 0) > 0
            ]
            
            # Show recent failures
            print(f"\nFound {len(failed_jobs)} jobs with failures:")
            for job in failed_jobs[:5]:  # Show last 5
                print(f"\n- Object: {job.get('object')}")
                print(f"  Job ID: {job.get('id')}")
                print(f"  Failed: {job.get('numberRecordsFailed')}")
                print(f"  Created: {job.get('createdDate')}")
                
                # Get details for this job
                if job.get('object') in ['AttributeDefinition', 'ProductCategory', 'Product2']:
                    get_job_failures(job.get('id'), job.get('object'))

def check_attribute_definition_sheet():
    """Check the current state of AttributeDefinition sheet."""
    print("\n" + "="*60)
    print("CHECKING ATTRIBUTEDEFINITION SHEET")
    print("="*60)
    
    excel_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
    df = pd.read_excel(excel_file, sheet_name='09_AttributeDefinition')
    
    # Clean column names
    df.columns = df.columns.str.replace('*', '', regex=False)
    
    # Check picklist records
    picklist_records = df[df['DataType'] == 'Picklist']
    print(f"\nFound {len(picklist_records)} Picklist-type AttributeDefinitions:")
    
    for idx, row in picklist_records.iterrows():
        print(f"\n{row['Name']}:")
        print(f"  Code: {row['Code']}")
        print(f"  PicklistId: {row.get('PicklistId', 'NOT SET')}")

def main():
    # Check AttributeDefinition sheet state
    check_attribute_definition_sheet()
    
    # Find and analyze recent failures
    find_recent_job_ids()

if __name__ == '__main__':
    main()