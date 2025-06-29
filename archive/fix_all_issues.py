#!/usr/bin/env python3
"""
Fix all identified issues in CSV files for successful upsert.
"""

import pandas as pd
from pathlib import Path

class ComprehensiveFixer:
    def __init__(self):
        self.input_dir = Path('data/csv_fixed_output')
        self.output_dir = Path('data/csv_final_output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ProductRelationshipType ID for bundles
        self.bundle_relationship_type_id = '0yoa5000000gTtdAAE'
    
    def fix_product2(self):
        """Fix Product2 CSV issues."""
        print("Fixing Product2...")
        df = pd.read_csv(self.input_dir / '13_Product2.csv')
        
        # Remove invalid fields
        invalid_fields = ['RecordTypeId', 'TransferRecordMode', 'FulfillmentQtyCalcMethod', 
                         'SpecificationType', 'TransferRecordMode.1', 'CanRamp']
        
        for field in invalid_fields:
            if field in df.columns:
                df = df.drop(columns=[field])
                print(f"  - Removed {field}")
        
        # Remove empty columns
        empty_cols = []
        for col in df.columns:
            if df[col].isna().all():
                empty_cols.append(col)
        
        if empty_cols:
            df = df.drop(columns=empty_cols)
            print(f"  - Removed empty columns: {', '.join(empty_cols)}")
        
        df.to_csv(self.output_dir / '13_Product2.csv', index=False)
        print(f"  ✓ Fixed Product2 ({len(df)} records, {len(df.columns)} columns)")
    
    def fix_pricebook2(self):
        """Fix Pricebook2 CSV issues."""
        print("\nFixing Pricebook2...")
        df = pd.read_csv(self.input_dir / '19_Pricebook2.csv')
        
        # Remove IsStandard (read-only field)
        if 'IsStandard' in df.columns:
            df = df.drop(columns=['IsStandard'])
            print("  - Removed IsStandard (read-only)")
        
        # Remove empty date columns
        for col in ['ValidFrom', 'ValidTo']:
            if col in df.columns and df[col].isna().all():
                df = df.drop(columns=[col])
                print(f"  - Removed empty {col}")
        
        df.to_csv(self.output_dir / '19_Pricebook2.csv', index=False)
        print(f"  ✓ Fixed Pricebook2 ({len(df)} records)")
    
    def fix_pricebook_entry(self):
        """Fix PricebookEntry CSV issues."""
        print("\nFixing PricebookEntry...")
        df = pd.read_csv(self.input_dir / '20_PricebookEntry.csv')
        
        # Remove ProductCode (not a field on PricebookEntry)
        if 'ProductCode' in df.columns:
            df = df.drop(columns=['ProductCode'])
            print("  - Removed ProductCode")
        
        # Remove empty UseStandardPrice
        if 'UseStandardPrice' in df.columns and df['UseStandardPrice'].isna().all():
            df = df.drop(columns=['UseStandardPrice'])
            print("  - Removed empty UseStandardPrice")
        
        # Remove ID column for inserts
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
            print("  - Removed Id column for insert")
        
        df.to_csv(self.output_dir / '20_PricebookEntry.csv', index=False)
        print(f"  ✓ Fixed PricebookEntry ({len(df)} records)")
    
    def fix_product_related_component(self):
        """Fix ProductRelatedComponent CSV issues."""
        print("\nFixing ProductRelatedComponent...")
        df = pd.read_csv(self.input_dir / '25_ProductRelatedComponent.csv')
        
        # Add required ProductRelationshipTypeId
        df['ProductRelationshipTypeId'] = self.bundle_relationship_type_id
        print(f"  - Added ProductRelationshipTypeId: {self.bundle_relationship_type_id}")
        
        # Set default values for empty fields
        if 'IsComponentRequired' in df.columns:
            df['IsComponentRequired'] = df['IsComponentRequired'].fillna(False)
        
        if 'Quantity' in df.columns:
            df['Quantity'] = df['Quantity'].fillna(1.0)
        
        if 'Sequence' in df.columns:
            df['Sequence'] = df['Sequence'].fillna(1)
        
        # Remove ID column for inserts
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
            print("  - Removed Id column for insert")
        
        df.to_csv(self.output_dir / '25_ProductRelatedComponent.csv', index=False)
        print(f"  ✓ Fixed ProductRelatedComponent ({len(df)} records)")
    
    def fix_attribute_definition(self):
        """Fix AttributeDefinition CSV issues."""
        print("\nFixing AttributeDefinition...")
        df = pd.read_csv(self.input_dir / '09_AttributeDefinition.csv')
        
        # Remove empty columns
        empty_cols = ['DeveloperName', 'SourceSystemIdentifier']
        for col in empty_cols:
            if col in df.columns and df[col].isna().all():
                df = df.drop(columns=[col])
                print(f"  - Removed empty {col}")
        
        df.to_csv(self.output_dir / '09_AttributeDefinition.csv', index=False)
        print(f"  ✓ Fixed AttributeDefinition ({len(df)} records)")
    
    def fix_product_category_product(self):
        """Fix ProductCategoryProduct - ensure it's insert only."""
        print("\nFixing ProductCategoryProduct...")
        df = pd.read_csv(self.input_dir / '26_ProductCategoryProduct.csv')
        
        # Remove ID column for inserts
        if 'Id' in df.columns:
            df = df.drop(columns=['Id'])
            print("  - Removed Id column for insert")
        
        df.to_csv(self.output_dir / '26_ProductCategoryProduct.csv', index=False)
        print(f"  ✓ Fixed ProductCategoryProduct ({len(df)} records)")
    
    def copy_unchanged_files(self):
        """Copy files that don't need changes."""
        unchanged_files = [
            '11_ProductCatalog.csv',
            '12_ProductCategory.csv',
            '08_ProductClassification.csv',
            '10_AttributeCategory.csv',
            '15_ProductSellingModel.csv',
            '17_ProductAttributeDef.csv'
        ]
        
        print("\nCopying unchanged files...")
        for file in unchanged_files:
            src = self.input_dir / file
            if src.exists():
                import shutil
                shutil.copy2(src, self.output_dir / file)
                print(f"  - Copied {file}")
    
    def fix_all(self):
        """Fix all issues."""
        print("=" * 60)
        print("FIXING ALL CSV ISSUES")
        print("=" * 60)
        
        self.fix_product2()
        self.fix_pricebook2()
        self.fix_pricebook_entry()
        self.fix_product_related_component()
        self.fix_attribute_definition()
        self.fix_product_category_product()
        self.copy_unchanged_files()
        
        print("\n✓ All fixes applied!")
        print(f"Fixed files saved to: {self.output_dir}")

def main():
    fixer = ComprehensiveFixer()
    fixer.fix_all()

if __name__ == '__main__':
    main()