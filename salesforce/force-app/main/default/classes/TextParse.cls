public class TextParse {
    
    @InvocableMethod(label='Parse Text Variables' 
                     description='Parse semicolon-delimited text into a collection variable or extract currency codes')
    public static List<OutputWrapper> parseText(List<InputWrapper> inputs) {
        List<OutputWrapper> outputs = new List<OutputWrapper>();
        
        for (InputWrapper input : inputs) {
            OutputWrapper output = new OutputWrapper();
            output.parsedValues = new List<String>();
            
            if (String.isNotBlank(input.inputText)) {
                // Split by semicolon and trim each value
                List<String> values = input.inputText.split(';');
                for (String value : values) {
                    String trimmedValue = value.trim();
                    if (String.isNotBlank(trimmedValue)) {
                        // If extractCurrencyCode is true, extract ISO code from each value
                        if (input.extractCurrencyCode != null && input.extractCurrencyCode) {
                            String isoCode = extractCurrencyCode(trimmedValue);
                            if (String.isNotBlank(isoCode)) {
                                output.parsedValues.add(isoCode);
                            }
                        } else {
                            // Otherwise add the full trimmed value
                            output.parsedValues.add(trimmedValue);
                        }
                    }
                }
                
                // Set single value if there's only one parsed value
                if (output.parsedValues.size() == 1) {
                    output.singleValue = output.parsedValues[0];
                    output.currencyCode = output.parsedValues[0]; // Also set currencyCode for backward compatibility
                }
            }
            
            outputs.add(output);
        }
        
        return outputs;
    }
    
    private static String extractCurrencyCode(String currencyString) {
        if (String.isBlank(currencyString)) {
            return null;
        }
        
        String trimmedInput = currencyString.trim();
        
        // Check if it's already just a 3-letter code
        if (trimmedInput.length() == 3 && trimmedInput.isAlpha()) {
            return trimmedInput.toUpperCase();
        }
        // Handle format "AUD - Australian Dollar" or "AUD-Australian Dollar"
        else if (trimmedInput.contains('-')) {
            String code = trimmedInput.substringBefore('-').trim();
            if (code.length() == 3 && code.isAlpha()) {
                return code.toUpperCase();
            }
        }
        // Handle format "AUD Australian Dollar" (space separator)
        else if (trimmedInput.contains(' ')) {
            String code = trimmedInput.substringBefore(' ').trim();
            if (code.length() == 3 && code.isAlpha()) {
                return code.toUpperCase();
            }
        }
        
        return null;
    }
    
    public class InputWrapper {
        @InvocableVariable(label='Input Text' 
                          description='Semicolon-delimited text to parse or currency string like "AUD - Australian Dollar"' 
                          required=true)
        public String inputText;
        
        @InvocableVariable(label='Extract Currency Code' 
                          description='Set to true to extract ISO currency code from strings like "AUD - Australian Dollar"' 
                          required=false)
        public Boolean extractCurrencyCode;
    }
    
    public class OutputWrapper {
        @InvocableVariable(label='Parsed Values' 
                          description='Collection of parsed text values')
        public List<String> parsedValues;
        
        @InvocableVariable(label='Single Value' 
                          description='Single string value (first parsed value or extracted currency code)')
        public String singleValue;
        
        @InvocableVariable(label='Currency Code' 
                          description='Extracted 3-letter ISO currency code when in currency extraction mode')
        public String currencyCode;
    }
}