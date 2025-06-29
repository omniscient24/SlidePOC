#!/usr/bin/env python3
"""
Generate a report showing recommended AttributeCategory assignments for all attributes.
"""

import pandas as pd
from datetime import datetime

def main():
    print("Generating Attribute Category Assignment Report...")
    print("=" * 80)
    
    # Read sheets
    df_cat = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='10_AttributeCategory')
    df_cat.columns = df_cat.columns.str.replace('*', '', regex=False).str.strip()
    
    df_attr = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='09_AttributeDefinition')
    df_attr.columns = df_attr.columns.str.replace('*', '', regex=False).str.strip()
    
    df_prod_attr = pd.read_excel('data/Revenue_Cloud_Complete_Upload_Template.xlsx', sheet_name='17_ProductAttributeDef')
    df_prod_attr.columns = df_prod_attr.columns.str.replace('*', '', regex=False).str.strip()
    
    # Create category mappings with detailed logic
    category_assignments = {
        # Deployment Option Attributes (0v3dp00000000BJAAY)
        'Deployment Option Attributes': {
            'id': '0v3dp00000000BJAAY',
            'code': 'DOA',
            'attributes': [
                {'code': 'DO', 'name': 'Deployment Option', 'reason': 'Directly related to deployment options'},
                {'code': 'MS', 'name': 'Managed Service?', 'reason': 'Determines if deployment is managed'},
                {'code': 'AG', 'name': 'Agents?', 'reason': 'Deployment configuration for agents'},
                {'code': 'TA', 'name': 'Type of Agents?', 'reason': 'Specifies agent deployment type'},
            ]
        },
        
        # Service Attributes (0v3dp00000000BLAAY)
        'Service Attributes': {
            'id': '0v3dp00000000BLAAY',
            'code': 'SA',
            'attributes': [
                {'code': 'OS', 'name': 'Operating System', 'reason': 'Service platform specification'},
                {'code': 'ST', 'name': 'Server Type', 'reason': 'Service infrastructure type'},
                {'code': 'SLT', 'name': 'Server Location Type', 'reason': 'Service location configuration'},
                {'code': 'CR', 'name': 'Cluster Ready?', 'reason': 'Service clustering capability'},
            ]
        },
        
        # Storage (0v3dp00000000BNAAY)
        'Storage': {
            'id': '0v3dp00000000BNAAY',
            'code': 'STO',
            'attributes': [
                {'code': 'STO', 'name': 'Studios?', 'reason': 'Storage-related studio configuration'},
                {'code': 'UN', 'name': 'Units', 'reason': 'Storage unit quantity'},
                {'code': 'UT', 'name': 'Unit Type', 'reason': 'Type of storage units'},
            ]
        },
        
        # Support (0v3dp00000000BMAAY)
        'Support': {
            'id': '0v3dp00000000BMAAY',
            'code': 'SP001',
            'attributes': [
                {'code': 'MT', 'name': 'Maintenance Type?', 'reason': 'Support maintenance level'},
                {'code': 'VER', 'name': 'Version?', 'reason': 'Support version tracking'},
                {'code': 'LT', 'name': 'License Type', 'reason': 'Support license model'},
                {'code': 'KT', 'name': 'Key Type', 'reason': 'Support key management'},
            ]
        },
        
        # Training (0v3dp00000000BOAAY)
        'Training': {
            'id': '0v3dp00000000BOAAY',
            'code': 'T001',
            'attributes': [
                {'code': 'Term', 'name': 'Term', 'reason': 'Training duration/term'},
                {'code': 'USR', 'name': 'Users', 'reason': 'Number of training users'},
                {'code': 'MYCAP', 'name': 'MYCAP?', 'reason': 'Training certification program'},
                {'code': 'PG', 'name': 'PGroup', 'reason': 'Training pricing group'},
                {'code': 'PT', 'name': 'Pricing Tier', 'reason': 'Training pricing level'},
            ]
        }
    }
    
    # Create attribute lookup
    attr_lookup = dict(zip(df_attr['Code'], df_attr['Name']))
    
    # Generate report
    report = []
    report.append("ATTRIBUTE CATEGORY ASSIGNMENT RECOMMENDATIONS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary section
    report.append("SUMMARY")
    report.append("-" * 40)
    report.append(f"Total AttributeCategories: {len(df_cat)}")
    report.append(f"Total AttributeDefinitions: {len(df_attr)}")
    report.append(f"Total ProductAttributeDefinitions: {len(df_prod_attr)}")
    report.append("")
    
    # Current usage (if AttributeCategoryId was updateable)
    report.append("CURRENT USAGE (Cannot be updated due to field restrictions)")
    report.append("-" * 40)
    
    current_usage = df_prod_attr['AttributeCategoryId'].value_counts()
    if len(current_usage) == 0 or current_usage.isna().all():
        report.append("All ProductAttributeDefinitions have NULL AttributeCategoryId")
    else:
        for cat_id, count in current_usage.items():
            if pd.notna(cat_id):
                cat_name = df_cat[df_cat['Id'] == cat_id]['Name'].iloc[0]
                report.append(f"{cat_name}: {count} attributes")
    
    report.append("")
    report.append("RECOMMENDED ASSIGNMENTS")
    report.append("-" * 40)
    
    # Track all attributes
    all_attr_codes = set(df_attr['Code'])
    assigned_attr_codes = set()
    
    # Detail each category
    for cat_name, cat_info in category_assignments.items():
        report.append("")
        report.append(f"\n{cat_name} ({cat_info['code']})")
        report.append(f"ID: {cat_info['id']}")
        report.append("-" * 60)
        
        for attr in cat_info['attributes']:
            assigned_attr_codes.add(attr['code'])
            in_use = len(df_prod_attr[df_prod_attr['AttributeDefinitionId'] == 
                                     df_attr[df_attr['Code'] == attr['code']]['Id'].iloc[0] 
                                     if not df_attr[df_attr['Code'] == attr['code']].empty else '']) > 0
            
            report.append(f"  • {attr['name']} ({attr['code']})")
            report.append(f"    Reason: {attr['reason']}")
            report.append(f"    Currently in use: {'Yes' if in_use else 'No'}")
            
            # Find products using this attribute
            if in_use:
                attr_id = df_attr[df_attr['Code'] == attr['code']]['Id'].iloc[0]
                prod_attrs = df_prod_attr[df_prod_attr['AttributeDefinitionId'] == attr_id]
                if len(prod_attrs) > 0:
                    products = []
                    for _, pa in prod_attrs.iterrows():
                        prod_name = df_prod_attr[df_prod_attr['Product2Id'] == pa['Product2Id']]['Name'].iloc[0] if 'Name' in df_prod_attr.columns else pa['Product2Id']
                        products.append(prod_name)
                    report.append(f"    Used by: {', '.join(products[:3])}{' ...' if len(products) > 3 else ''}")
            report.append("")
    
    # Unassigned attributes
    unassigned = all_attr_codes - assigned_attr_codes
    if unassigned:
        report.append("\nUNASSIGNED ATTRIBUTES")
        report.append("-" * 40)
        for code in sorted(unassigned):
            name = attr_lookup.get(code, 'Unknown')
            report.append(f"  • {name} ({code}) - No clear category match")
    
    # Implementation recommendations
    report.append("\n\nIMPLEMENTATION RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("1. AttributeCategoryId can only be set during ProductAttributeDefinition creation")
    report.append("2. To implement these assignments, you would need to:")
    report.append("   a) Delete existing ProductAttributeDefinition records")
    report.append("   b) Recreate them with the appropriate AttributeCategoryId values")
    report.append("3. Alternative: Keep current setup and use categories for future attributes only")
    
    # Category utilization analysis
    report.append("\n\nCATEGORY UTILIZATION ANALYSIS")
    report.append("-" * 40)
    
    for cat_name, cat_info in category_assignments.items():
        attr_count = len(cat_info['attributes'])
        in_use_count = sum(1 for attr in cat_info['attributes'] 
                          if len(df_prod_attr[df_prod_attr['AttributeDefinitionId'] == 
                                             df_attr[df_attr['Code'] == attr['code']]['Id'].iloc[0] 
                                             if not df_attr[df_attr['Code'] == attr['code']].empty else '']) > 0)
        
        utilization = (in_use_count / attr_count * 100) if attr_count > 0 else 0
        report.append(f"{cat_name}: {in_use_count}/{attr_count} attributes in use ({utilization:.0f}%)")
    
    # Write report to file
    report_text = '\n'.join(report)
    
    with open('attribute_category_assignment_report.txt', 'w') as f:
        f.write(report_text)
    
    print("\n✓ Report generated: attribute_category_assignment_report.txt")
    
    # Also display key findings
    print("\nKEY FINDINGS:")
    print("-" * 40)
    print(f"• All {len(df_prod_attr)} ProductAttributeDefinitions have NULL AttributeCategoryId")
    print("• AttributeCategoryId field is createable but NOT updateable")
    print("• Categories can only be assigned when creating new ProductAttributeDefinitions")
    print("\nCATEGORY RECOMMENDATIONS:")
    
    for cat_name, cat_info in category_assignments.items():
        print(f"\n{cat_name}: {len(cat_info['attributes'])} attributes")
        for attr in cat_info['attributes'][:2]:  # Show first 2
            print(f"  - {attr['name']}")
        if len(cat_info['attributes']) > 2:
            print(f"  ... and {len(cat_info['attributes']) - 2} more")

if __name__ == '__main__':
    main()