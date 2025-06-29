#!/usr/bin/env python3
"""
Clean asterisks from Excel headers and prepare for upsert.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

class HeaderCleaner:
    def __init__(self):
        self.input_file = Path('data/Revenue_Cloud_Complete_Upload_Template.xlsx')
        self.output_file = Path(f'data/Revenue_Cloud_Clean_Headers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    
    def clean_headers(self):
        """Remove asterisks from all headers in the Excel file."""
        print(f"Cleaning headers in: {self.input_file}")
        print(f"Output file: {self.output_file}\n")
        
        # Load all sheets
        xl_file = pd.ExcelFile(self.input_file)
        
        # Process each sheet
        with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
            for sheet_name in xl_file.sheet_names:
                print(f"Processing sheet: {sheet_name}")
                
                # Read sheet
                df = pd.read_excel(self.input_file, sheet_name=sheet_name)
                
                # Clean column names - remove asterisks
                original_cols = df.columns.tolist()
                cleaned_cols = [col.replace('*', '') for col in original_cols]
                
                # Check if any columns were changed
                changed = False
                for orig, clean in zip(original_cols, cleaned_cols):
                    if orig != clean:
                        print(f"  - Changed: '{orig}' -> '{clean}'")
                        changed = True
                
                if not changed:
                    print(f"  - No asterisks found")
                
                # Rename columns
                df.columns = cleaned_cols
                
                # Write to output
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\nHeaders cleaned successfully!")
        print(f"Output saved to: {self.output_file}")
        
        return self.output_file

def main():
    cleaner = HeaderCleaner()
    output_file = cleaner.clean_headers()
    
    print(f"\nYou can now use the cleaned file for upsert operations:")
    print(f"  {output_file}")

if __name__ == '__main__':
    main()