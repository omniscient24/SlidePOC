#!/bin/bash

echo "Creating External_ID__c fields for Revenue Cloud objects..."

# List of objects to add External_ID__c field
OBJECTS=(
    "Product2"
    "Pricebook2"
    "PricebookEntry"
    "ProductSellingModel"
    "ProductCategory"
    "TaxTreatment"
    "ProductAttributeDefinition"
)

# Create SFDX project
echo "Creating SFDX project..."
rm -rf external-id-fields-deploy
sf project generate --name external-id-fields-deploy --output-dir . --manifest

# Create field metadata for each object
for obj in "${OBJECTS[@]}"; do
    echo "Creating metadata for $obj..."
    mkdir -p "external-id-fields-deploy/force-app/main/default/objects/$obj/fields"
    
    cat > "external-id-fields-deploy/force-app/main/default/objects/$obj/fields/External_ID__c.field-meta.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>External_ID__c</fullName>
    <externalId>true</externalId>
    <label>External ID</label>
    <length>255</length>
    <required>false</required>
    <trackHistory>false</trackHistory>
    <type>Text</type>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
    <description>External ID field for data migration and integration purposes</description>
</CustomField>
EOF
done

# Deploy to org
echo "Deploying to fortradp2..."
cd external-id-fields-deploy
sf project deploy start --target-org fortradp2 --wait 10

# Verify deployment
echo "Verifying fields were created..."
sleep 5

for obj in "${OBJECTS[@]}"; do
    echo -n "Checking $obj... "
    if sf data query --query "SELECT COUNT() FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '$obj' AND QualifiedApiName = 'External_ID__c'" --target-org fortradp2 --json | grep -q '"totalSize":1'; then
        echo "✓ External_ID__c exists"
    else
        echo "✗ External_ID__c NOT found"
    fi
done