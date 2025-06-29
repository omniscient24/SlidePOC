import pandas as pd
import os

input_excel = "/Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload/data/Revenue_Cloud_Complete_Upload_Template.xlsx"
output_dir = "/Users/marcdebrey/cpq-revenue-cloud-migration/fortradp2Upload/data/csv_output"
pass1_dir = os.path.join(output_dir, "pass1")
pass2_dir = os.path.join(output_dir, "pass2")
report_path = os.path.join(output_dir, "external_id_report.csv")

os.makedirs(pass1_dir, exist_ok=True)
os.makedirs(pass2_dir, exist_ok=True)

external_id_fields = {'13_Product2': ('ProductCode__c', 'PROD'), '12_ProductCategory': ('CategoryCode__c', 'CAT'), '11_ProductCatalog': ('CatalogCode__c', 'CATALOG'), '09_AttributeDefinition': ('AttributeCode__c', 'ATTR'), '15_ProductSellingModel': ('ModelCode__c', 'MODEL')}
report_rows = []

excel_file = pd.ExcelFile(input_excel)
for sheet_name in excel_file.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Inject or overwrite external ID if the sheet is mapped
    if sheet_name in external_id_fields:
        ext_id_field, prefix = external_id_fields[sheet_name]
        df[ext_id_field] = [f"{prefix}{str(i+1).zfill(3)}" for i in range(len(df))]
        for i, value in enumerate(df[ext_id_field]):
            report_rows.append({
                "Sheet": sheet_name,
                "Row": i + 1,
                "External ID Field": ext_id_field,
                "Generated Value": value
            })

    pass1_cols = [col for col in df.columns if "__r." not in col]
    pass2_cols = [col for col in df.columns if "__r." in col or col in pass1_cols]

    df[pass1_cols].to_csv(os.path.join(pass1_dir, f"{sheet_name}.csv"), index=False)
    df[pass2_cols].to_csv(os.path.join(pass2_dir, f"{sheet_name}.csv"), index=False)

report_df = pd.DataFrame(report_rows)
report_df.to_csv(report_path, index=False)
print(f"Verification report saved to: {report_path}")
