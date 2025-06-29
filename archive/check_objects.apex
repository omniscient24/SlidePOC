// Check which objects support custom fields
List<String> objectsToCheck = new List<String>{
    'Product2',
    'Pricebook2', 
    'PricebookEntry',
    'ProductSellingModel',
    'ProductSellingModelOption',
    'ProductCategory',
    'TaxTreatment',
    'ProductAttributeDefinition'
};

for (String objName : objectsToCheck) {
    try {
        Schema.DescribeSObjectResult describe = Schema.getGlobalDescribe().get(objName).getDescribe();
        System.debug(objName + ' - Is custom: ' + describe.isCustom());
        
        // Check if External_ID__c already exists
        Map<String, Schema.SObjectField> fields = describe.fields.getMap();
        if (fields.containsKey('external_id__c')) {
            System.debug('  --> External_ID__c already exists on ' + objName);
        } else {
            System.debug('  --> External_ID__c does NOT exist on ' + objName);
        }
    } catch (Exception e) {
        System.debug(objName + ' - Error: ' + e.getMessage());
    }
}