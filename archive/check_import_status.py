#!/usr/bin/env python3
"""
Check the status of all imports and summarize what's been completed.
"""

import subprocess
import json

class ImportStatusChecker:
    def __init__(self):
        self.target_org = 'fortradp2'
        
    def get_count(self, query):
        """Get count from a query."""
        cmd = ['sf', 'data', 'query', '--query', query, '--target-org', self.target_org, '--json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result'] and len(data['result']['records']) > 0:
                return data['result']['records'][0].get('cnt', 0)
        return 0
    
    def check_all_objects(self):
        """Check all Revenue Cloud objects."""
        print("=" * 60)
        print("REVENUE CLOUD IMPORT STATUS")
        print("=" * 60)
        print(f"Target Org: {self.target_org}\n")
        
        checks = [
            ("CORE OBJECTS", [
                ('Product Catalogs', 'SELECT COUNT(Id) cnt FROM ProductCatalog'),
                ('Product Categories', 'SELECT COUNT(Id) cnt FROM ProductCategory'),
                ('Products', 'SELECT COUNT(Id) cnt FROM Product2'),
                ('Price Books', 'SELECT COUNT(Id) cnt FROM Pricebook2'),
                ('Product Classifications', 'SELECT COUNT(Id) cnt FROM ProductClassification'),
            ]),
            
            ("ATTRIBUTE OBJECTS", [
                ('Attribute Definitions', 'SELECT COUNT(Id) cnt FROM AttributeDefinition'),
                ('Attribute Categories', 'SELECT COUNT(Id) cnt FROM AttributeCategory'),
                ('Product Attribute Definitions', 'SELECT COUNT(Id) cnt FROM ProductAttributeDefinition'),
            ]),
            
            ("PRICING OBJECTS", [
                ('Product Selling Models', 'SELECT COUNT(Id) cnt FROM ProductSellingModel'),
                ('Price Book Entries', 'SELECT COUNT(Id) cnt FROM PricebookEntry WHERE Pricebook2.IsStandard = false'),
                ('Standard Price Book Entries', 'SELECT COUNT(Id) cnt FROM PricebookEntry WHERE Pricebook2.IsStandard = true'),
            ]),
            
            ("RELATIONSHIP OBJECTS", [
                ('Product Category Products', 'SELECT COUNT(Id) cnt FROM ProductCategoryProduct'),
                ('Product Related Components', 'SELECT COUNT(Id) cnt FROM ProductRelatedComponent'),
                ('Product Relationship Types', 'SELECT COUNT(Id) cnt FROM ProductRelationshipType'),
            ])
        ]
        
        total_records = 0
        
        for section, queries in checks:
            print(f"\n{section}")
            print("-" * 40)
            
            for name, query in queries:
                count = self.get_count(query)
                total_records += count
                status = "✓" if count > 0 else "✗"
                print(f"{status} {name}: {count}")
        
        print(f"\n{'=' * 60}")
        print(f"TOTAL RECORDS IMPORTED: {total_records}")
        print(f"{'=' * 60}")
        
        # Show sample data
        print("\nSAMPLE DATA:")
        print("-" * 40)
        
        # Show sample products
        cmd = ['sf', 'data', 'query', '--query', 
               'SELECT Name, ProductCode, Type FROM Product2 LIMIT 5',
               '--target-org', self.target_org, '--result-format', 'table']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            print("\nProducts:")
            print(result.stdout)
        
        # Show product categories
        cmd = ['sf', 'data', 'query', '--query', 
               'SELECT Name, Code FROM ProductCategory LIMIT 5',
               '--target-org', self.target_org, '--result-format', 'table']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            print("\nProduct Categories:")
            print(result.stdout)

def main():
    checker = ImportStatusChecker()
    checker.check_all_objects()

if __name__ == '__main__':
    main()