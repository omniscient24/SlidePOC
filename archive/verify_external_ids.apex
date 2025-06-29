// Verify External_ID__c fields were created
List<String> objectsToCheck = new List<String>{
    'Product2',
    'Pricebook2', 
    'PricebookEntry',
    'ProductSellingModel',
    'ProductCategory',
    'TaxTreatment',
    'ProductAttributeDefinition'
};

System.debug('=== External_ID__c Field Verification ===');
Integer successCount = 0;
Integer failCount = 0;

for (String objName : objectsToCheck) {
    try {
        // Query FieldDefinition to check if External_ID__c exists
        List<FieldDefinition> fields = [
            SELECT Id, QualifiedApiName 
            FROM FieldDefinition 
            WHERE EntityDefinition.QualifiedApiName = :objName 
            AND QualifiedApiName = 'External_ID__c'
            LIMIT 1
        ];
        
        if (!fields.isEmpty()) {
            System.debug('✓ ' + objName + '.External_ID__c EXISTS');
            successCount++;
        } else {
            System.debug('✗ ' + objName + '.External_ID__c NOT FOUND');
            failCount++;
        }
    } catch (Exception e) {
        System.debug('ERROR checking ' + objName + ': ' + e.getMessage());
        failCount++;
    }
}

System.debug('=== Summary ===');
System.debug('Successfully created: ' + successCount + ' fields');
System.debug('Failed/Not found: ' + failCount + ' fields');