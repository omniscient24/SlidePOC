#!/usr/bin/env python3
"""
Check requirements for setting Product2.Type to Bundle in Revenue Cloud.
"""

import subprocess
import json
from pathlib import Path

class BundleRequirementsChecker:
    def __init__(self):
        self.target_org = 'fortradp2'
        
    def check_product_type_field(self):
        """Check the Type field on Product2."""
        print("=" * 60)
        print("CHECKING PRODUCT2.TYPE FIELD")
        print("=" * 60)
        
        cmd = [
            'sf', 'sobject', 'describe',
            '--sobject', 'Product2', 
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'fields' in data['result']:
                fields = data['result']['fields']
                
                # Find Type field
                type_field = None
                for field in fields:
                    if field['name'] == 'Type':
                        type_field = field
                        break
                
                if type_field:
                    print("\nType field properties:")
                    print(f"  Label: {type_field.get('label')}")
                    print(f"  Type: {type_field.get('type')}")
                    print(f"  Updateable: {type_field.get('updateable')}")
                    print(f"  Createable: {type_field.get('createable')}")
                    print(f"  Nillable: {type_field.get('nillable')}")
                    
                    if 'picklistValues' in type_field:
                        print("\n  Available values:")
                        for val in type_field['picklistValues']:
                            active = "✓" if val.get('active') else "✗"
                            print(f"    {active} {val.get('value')} - {val.get('label')}")
                else:
                    print("Type field not found")
        else:
            print(f"Error: {result.stderr}")
    
    def check_current_products(self):
        """Check current Product2 records and their types."""
        print("\n" + "=" * 60)
        print("CURRENT PRODUCT2 RECORDS")
        print("=" * 60)
        
        query = """
        SELECT Id, Name, Type, ProductCode, 
               (SELECT Id FROM ProductRelatedComponents__r),
               (SELECT Id FROM ChildProductRelatedComponents__r)
        FROM Product2 
        ORDER BY Name
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                
                print(f"\nTotal products: {len(records)}")
                
                # Group by type
                type_counts = {}
                bundle_candidates = []
                
                for rec in records:
                    prod_type = rec.get('Type', 'None')
                    type_counts[prod_type] = type_counts.get(prod_type, 0) + 1
                    
                    # Check if product has child components
                    has_children = False
                    if 'ProductRelatedComponents__r' in rec and rec['ProductRelatedComponents__r']:
                        if rec['ProductRelatedComponents__r'].get('totalSize', 0) > 0:
                            has_children = True
                    
                    if has_children or prod_type == 'Bundle':
                        bundle_candidates.append({
                            'Name': rec.get('Name'),
                            'Type': prod_type,
                            'HasChildren': has_children
                        })
                
                print("\nProducts by Type:")
                for prod_type, count in type_counts.items():
                    print(f"  {prod_type}: {count}")
                
                if bundle_candidates:
                    print("\nBundle candidates (products with children or Bundle type):")
                    for prod in bundle_candidates:
                        children = "Has children" if prod['HasChildren'] else "No children"
                        print(f"  - {prod['Name']} (Type: {prod['Type']}, {children})")
        else:
            print(f"Query error: {result.stderr}")
    
    def check_related_objects(self):
        """Check ProductRelatedComponent for bundle structure."""
        print("\n" + "=" * 60)
        print("PRODUCTRELATEDCOMPONENT ANALYSIS")
        print("=" * 60)
        
        query = """
        SELECT Id, ParentProductId, ParentProduct.Name, ParentProduct.Type,
               ChildProductId, ChildProduct.Name, ChildProductRole,
               MinQuantity, MaxQuantity, DefaultQuantity
        FROM ProductRelatedComponent
        ORDER BY ParentProduct.Name, ChildProduct.Name
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'totalSize' in data['result']:
                total = data['result']['totalSize']
                
                if total > 0:
                    records = data['result']['records']
                    print(f"\nFound {total} ProductRelatedComponent records")
                    
                    # Group by parent
                    parents = {}
                    for rec in records:
                        parent_id = rec.get('ParentProductId')
                        parent_name = rec.get('ParentProduct', {}).get('Name', 'Unknown')
                        parent_type = rec.get('ParentProduct', {}).get('Type', 'None')
                        
                        if parent_id not in parents:
                            parents[parent_id] = {
                                'name': parent_name,
                                'type': parent_type,
                                'children': []
                            }
                        
                        parents[parent_id]['children'].append({
                            'name': rec.get('ChildProduct', {}).get('Name', 'Unknown'),
                            'role': rec.get('ChildProductRole', 'Component')
                        })
                    
                    print("\nBundle structure:")
                    for parent_id, info in parents.items():
                        print(f"\n  {info['name']} (Type: {info['type']})")
                        for child in info['children']:
                            print(f"    └─ {child['name']} ({child['role']})")
                else:
                    print("\nNo ProductRelatedComponent records found")
                    print("This means no bundle structures are defined yet")
        else:
            print(f"Query error: {result.stderr}")
    
    def check_revenue_cloud_settings(self):
        """Check Revenue Cloud specific settings."""
        print("\n" + "=" * 60)
        print("REVENUE CLOUD BUNDLE REQUIREMENTS")
        print("=" * 60)
        
        print("\nFor Product2.Type = 'Bundle' in Revenue Cloud:")
        print("\n1. Field Requirements:")
        print("   - Type field must have 'Bundle' as an active picklist value")
        print("   - Product must be associated with appropriate ProductSellingModel")
        print("   - ConfigureDuringSale field may need to be set appropriately")
        
        print("\n2. Related Object Requirements:")
        print("   - ProductRelatedComponent records define parent-child relationships")
        print("   - ChildProductRole field specifies the role (Component, Option, etc.)")
        print("   - Quantity fields (Min, Max, Default) control selection rules")
        
        print("\n3. Revenue Cloud Specific:")
        print("   - Bundle products often need ProductSellingModelOption records")
        print("   - Pricing may be controlled at bundle level or component level")
        print("   - Lifecycle policies may apply differently to bundles")
        
        # Check ConfigureDuringSale field
        self.check_configure_during_sale()
    
    def check_configure_during_sale(self):
        """Check ConfigureDuringSale field settings."""
        print("\n" + "-" * 40)
        print("Checking ConfigureDuringSale field...")
        
        query = """
        SELECT Type, ConfigureDuringSale, COUNT(Id) cnt
        FROM Product2
        GROUP BY Type, ConfigureDuringSale
        ORDER BY Type
        """
        
        cmd = [
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', self.target_org,
            '--json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'result' in data and 'records' in data['result']:
                records = data['result']['records']
                
                print("\nConfigureDuringSale by Product Type:")
                for rec in records:
                    print(f"  Type: {rec.get('Type', 'None')}, ConfigureDuringSale: {rec.get('ConfigureDuringSale', 'None')}, Count: {rec.get('cnt')}")

def main():
    checker = BundleRequirementsChecker()
    
    # Check field properties
    checker.check_product_type_field()
    
    # Check current products
    checker.check_current_products()
    
    # Check bundle structure
    checker.check_related_objects()
    
    # Check Revenue Cloud requirements
    checker.check_revenue_cloud_settings()

if __name__ == '__main__':
    main()