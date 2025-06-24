import pandas as pd
import os

input_excel = "/Users/marcdebrey/cpq-revenue-cloud-migration/data/Revenue_Cloud_Complete_Upload_Template.xlsx"
output_dir = "/Users/marcdebrey/cpq-revenue-cloud-migration/data/csv_output"
os.makedirs(output_dir, exist_ok=True)

excel_file = pd.ExcelFile(input_excel)
for sheet_name in excel_file.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    csv_filename = os.path.join(output_dir, f"{sheet_name}.csv")
    df.to_csv(csv_filename, index=False)
    print(f"Exported {csv_filename}")
