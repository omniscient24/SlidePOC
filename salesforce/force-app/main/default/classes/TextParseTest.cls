@isTest
public class TextParseTest {
    
    @isTest
    static void testParseTextWithSingleValue() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'Value1';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(1, outputs[0].parsedValues.size(), 'Should have one parsed value');
        System.assertEquals('Value1', outputs[0].parsedValues[0], 'Should parse single value correctly');
    }
    
    @isTest
    static void testParseTextWithMultipleValues() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'Value1;Value2;Value3';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(3, outputs[0].parsedValues.size(), 'Should have three parsed values');
        System.assertEquals('Value1', outputs[0].parsedValues[0], 'First value should be Value1');
        System.assertEquals('Value2', outputs[0].parsedValues[1], 'Second value should be Value2');
        System.assertEquals('Value3', outputs[0].parsedValues[2], 'Third value should be Value3');
    }
    
    @isTest
    static void testParseTextWithSpaces() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = ' Value1 ; Value2 ; Value3 ';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(3, outputs[0].parsedValues.size(), 'Should have three parsed values');
        System.assertEquals('Value1', outputs[0].parsedValues[0], 'Should trim spaces from first value');
        System.assertEquals('Value2', outputs[0].parsedValues[1], 'Should trim spaces from second value');
        System.assertEquals('Value3', outputs[0].parsedValues[2], 'Should trim spaces from third value');
    }
    
    @isTest
    static void testParseTextWithEmptyValues() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'Value1;;Value3;';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(2, outputs[0].parsedValues.size(), 'Should ignore empty values');
        System.assertEquals('Value1', outputs[0].parsedValues[0], 'First value should be Value1');
        System.assertEquals('Value3', outputs[0].parsedValues[1], 'Second value should be Value3');
    }
    
    @isTest
    static void testParseTextWithNullInput() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = null;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(0, outputs[0].parsedValues.size(), 'Should return empty list for null input');
    }
    
    @isTest
    static void testParseTextWithEmptyString() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = '';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(0, outputs[0].parsedValues.size(), 'Should return empty list for empty string');
    }
    
    @isTest
    static void testParseTextWithMultipleInputs() {
        // Setup
        TextParse.InputWrapper input1 = new TextParse.InputWrapper();
        input1.inputText = 'A;B;C';
        TextParse.InputWrapper input2 = new TextParse.InputWrapper();
        input2.inputText = 'X;Y;Z';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input1, input2};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(2, outputs.size(), 'Should return two outputs');
        System.assertEquals(3, outputs[0].parsedValues.size(), 'First output should have three values');
        System.assertEquals(3, outputs[1].parsedValues.size(), 'Second output should have three values');
        System.assertEquals('A', outputs[0].parsedValues[0], 'First value of first output should be A');
        System.assertEquals('X', outputs[1].parsedValues[0], 'First value of second output should be X');
    }
    
    @isTest
    static void testParseTextWithSpecialCharacters() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'Value@1;Value#2;Value$3';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(3, outputs[0].parsedValues.size(), 'Should have three parsed values');
        System.assertEquals('Value@1', outputs[0].parsedValues[0], 'Should handle special characters');
        System.assertEquals('Value#2', outputs[0].parsedValues[1], 'Should handle special characters');
        System.assertEquals('Value$3', outputs[0].parsedValues[2], 'Should handle special characters');
    }
    
    @isTest
    static void testExtractCurrencyCodeWithDash() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'AUD - Australian Dollar';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals('AUD', outputs[0].currencyCode, 'Should extract currency code');
        System.assertEquals('AUD', outputs[0].singleValue, 'Should set single value to currency code');
    }
    
    @isTest
    static void testExtractCurrencyCodeWithSpace() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'EUR European Euro';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals('EUR', outputs[0].currencyCode, 'Should extract currency code');
        System.assertEquals('EUR', outputs[0].singleValue, 'Should set single value to currency code');
    }
    
    @isTest
    static void testExtractCurrencyCodeJustCode() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'USD';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals('USD', outputs[0].currencyCode, 'Should handle plain currency code');
        System.assertEquals('USD', outputs[0].singleValue, 'Should set single value to currency code');
    }
    
    @isTest
    static void testExtractCurrencyCodeLowerCase() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'gbp - British Pound';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals('GBP', outputs[0].currencyCode, 'Should uppercase currency code');
        System.assertEquals('GBP', outputs[0].singleValue, 'Should set single value to currency code');
    }
    
    @isTest
    static void testSingleValueWithOneParsedValue() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'SingleValue';
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(1, outputs[0].parsedValues.size(), 'Should have one parsed value');
        System.assertEquals('SingleValue', outputs[0].singleValue, 'Should set single value when only one parsed value');
    }
    
    @isTest
    static void testExtractMultipleCurrencyCodes() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'AUD - Australian Dollar;EUR - European Euro;USD - US Dollar;GBP - British Pound';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(4, outputs[0].parsedValues.size(), 'Should have four currency codes');
        System.assertEquals('AUD', outputs[0].parsedValues[0], 'First code should be AUD');
        System.assertEquals('EUR', outputs[0].parsedValues[1], 'Second code should be EUR');
        System.assertEquals('USD', outputs[0].parsedValues[2], 'Third code should be USD');
        System.assertEquals('GBP', outputs[0].parsedValues[3], 'Fourth code should be GBP');
    }
    
    @isTest
    static void testExtractMixedCurrencyFormats() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'AUD - Australian Dollar;EUR;usd - US Dollar;CAD Canadian Dollar';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals(4, outputs[0].parsedValues.size(), 'Should have four currency codes');
        System.assertEquals('AUD', outputs[0].parsedValues[0], 'First code should be AUD');
        System.assertEquals('EUR', outputs[0].parsedValues[1], 'Second code should be EUR');
        System.assertEquals('USD', outputs[0].parsedValues[2], 'Third code should be USD (uppercase)');
        System.assertEquals('CAD', outputs[0].parsedValues[3], 'Fourth code should be CAD');
    }
    
    @isTest
    static void testExtractCurrencyWithConversionRate() {
        // Setup
        TextParse.InputWrapper input = new TextParse.InputWrapper();
        input.inputText = 'USD';
        input.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs = new List<TextParse.InputWrapper>{input};
        
        // Execute
        Test.startTest();
        List<TextParse.OutputWrapper> outputs = TextParse.parseText(inputs);
        Test.stopTest();
        
        // Verify single currency
        System.assertEquals(1, outputs.size(), 'Should return one output');
        System.assertEquals('USD', outputs[0].currencyCode, 'Should extract currency code');
        System.assertEquals(1, outputs[0].conversionRates.size(), 'Should have one conversion rate');
        System.assertNotEquals(null, outputs[0].conversionRate, 'Single conversion rate should be populated');
        System.assertNotEquals(null, outputs[0].conversionRates[0], 'Conversion rate in collection should be populated');
        
        // Test with multiple currencies
        TextParse.InputWrapper input2 = new TextParse.InputWrapper();
        input2.inputText = 'USD - US Dollar;EUR - European Euro';
        input2.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs2 = new List<TextParse.InputWrapper>{input2};
        
        List<TextParse.OutputWrapper> outputs2 = TextParse.parseText(inputs2);
        System.assertEquals(2, outputs2[0].parsedValues.size(), 'Should extract two currency codes');
        System.assertEquals(2, outputs2[0].conversionRates.size(), 'Should have two conversion rates');
        System.assertEquals(2, outputs2[0].currencyDataList.size(), 'Should have two currency data objects');
        System.assertEquals(2, outputs2[0].currencyWithRates.size(), 'Should have two formatted currency:rate strings');
        System.assertEquals('USD', outputs2[0].parsedValues[0], 'First code should be USD');
        System.assertEquals('EUR', outputs2[0].parsedValues[1], 'Second code should be EUR');
        System.assertEquals('USD', outputs2[0].currencyDataList[0].isoCode, 'First currency data should have USD');
        System.assertEquals('EUR', outputs2[0].currencyDataList[1].isoCode, 'Second currency data should have EUR');
        System.assertNotEquals(null, outputs2[0].currencyDataList[0].conversionRate, 'First currency should have conversion rate');
        System.assertNotEquals(null, outputs2[0].currencyDataList[1].conversionRate, 'Second currency should have conversion rate');
        // Verify formatted strings
        System.assert(outputs2[0].currencyWithRates[0].startsWith('USD:'), 'First formatted string should start with USD:');
        System.assert(outputs2[0].currencyWithRates[1].startsWith('EUR:'), 'Second formatted string should start with EUR:');
        
        // Test with non-existent currency
        TextParse.InputWrapper input3 = new TextParse.InputWrapper();
        input3.inputText = 'XYZ';
        input3.extractCurrencyCode = true;
        List<TextParse.InputWrapper> inputs3 = new List<TextParse.InputWrapper>{input3};
        
        List<TextParse.OutputWrapper> outputs3 = TextParse.parseText(inputs3);
        System.assertEquals('XYZ', outputs3[0].currencyCode, 'Should extract currency code');
        System.assertEquals(1.0, outputs3[0].conversionRates[0], 'Should default to 1.0 for non-existent currency');
    }
}