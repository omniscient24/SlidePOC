import pandas as pd
import os

input_excel = "/Users/marcdebrey/cpq-revenue-cloud-migration/data/Revenue_Cloud_Complete_Upload_Template.xlsx"
output_dir = "/Users/marcdebrey/cpq-revenue-cloud-migration/data/csv_output"
pass1_dir = os.path.join(output_dir, "pass1")
pass2_dir = os.path.join(output_dir, "pass2")

os.makedirs(pass1_dir, exist_ok=True)
os.makedirs(pass2_dir, exist_ok=True)

external_id_fields = {'Product2': ('ProductCode__c', 'PROD'), 'ProductCategory': ('CategoryCode__c', 'CAT'), 'ProductCatalog': ('CatalogCode__c', 'CATALOG'), 'AttributeDefinition': ('AttributeCode__c', 'ATTR'), 'ProductSellingModel': ('ModelCode__c', 'MODEL')}

excel_file = pd.ExcelFile(input_excel)
for sheet_name in excel_file.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Inject external ID if applicable
    if sheet_name in external_id_fields:
        ext_id_field, prefix = external_id_fields[sheet_name]
        df[ext_id_field] = [f"{prefix}{str(i+1).zfill(3)}" for i in range(len(df))]

    # Determine fields for pass1 (no __r.) and pass2 (includes __r.)
    pass1_cols = [col for col in df.columns if "__r." not in col]
    pass2_cols = [col for col in df.columns if "__r." in col or col in pass1_cols]

    # Save both passes
    df[pass1_cols].to_csv(os.path.join(pass1_dir, f"{sheet_name}.csv"), index=False)
    df[pass2_cols].to_csv(os.path.join(pass2_dir, f"{sheet_name}.csv"), index=False)

    print(f"Injected external IDs and exported {sheet_name}.csv to pass1 and pass2")
