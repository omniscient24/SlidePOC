#!/bin/bash

# Create External_ID__c field on Product2
cat > product2_field.json << EOF
{
  "Metadata": {
    "label": "External ID",
    "fullName": "Product2.External_ID__c",
    "type": "Text",
    "length": 255,
    "externalId": true,
    "unique": true,
    "caseSensitive": false,
    "description": "External ID field for data migration and integration purposes"
  }
}
EOF

# Use Salesforce CLI to create the field via REST API
sf data create record --sobject CustomField --file product2_field.json --target-org fortradp2 --use-tooling-api