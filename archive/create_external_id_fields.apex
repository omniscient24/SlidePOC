// Script to create External_ID__c fields on Revenue Cloud objects

// Helper method to create External ID field
public static void createExternalIdField(String objectName) {
    try {
        // Check if field already exists
        Map<String, Schema.SObjectField> fieldMap = Schema.getGlobalDescribe().get(objectName).getDescribe().fields.getMap();
        if (fieldMap.containsKey('External_ID__c')) {
            System.debug(objectName + ' already has External_ID__c field');
            return;
        }
        
        MetadataService.MetadataPort service = new MetadataService.MetadataPort();
        service.SessionHeader = new MetadataService.SessionHeader_element();
        service.SessionHeader.sessionId = UserInfo.getSessionId();
        
        MetadataService.CustomField customField = new MetadataService.CustomField();
        customField.fullName = objectName + '.External_ID__c';
        customField.label = 'External ID';
        customField.type_x = 'Text';
        customField.length = 255;
        customField.externalId = true;
        customField.unique = true;
        customField.caseSensitive = false;
        customField.description = 'External ID field for data migration and integration purposes';
        
        List<MetadataService.SaveResult> results = service.createMetadata(
            new MetadataService.Metadata[] { customField }
        );
        
        for (MetadataService.SaveResult sr : results) {
            if (sr.success) {
                System.debug('Successfully created External_ID__c on ' + objectName);
            } else {
                System.debug('Error creating field on ' + objectName + ': ' + sr.errors[0].message);
            }
        }
    } catch (Exception e) {
        System.debug('Exception for ' + objectName + ': ' + e.getMessage());
    }
}

// Create fields on Revenue Cloud objects
createExternalIdField('Product2');
createExternalIdField('Pricebook2');
createExternalIdField('PricebookEntry');
createExternalIdField('ProductSellingModel');
createExternalIdField('ProductCategory');
createExternalIdField('TaxTreatment');
createExternalIdField('ProductAttributeDefinition');