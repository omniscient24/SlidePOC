# Test Plan: Add Product Category Feature

## Overview
This test plan covers the implementation of the "Add Product Category" feature in the Product Hierarchy visualization. This feature allows users to add new categories to catalogs and subcategories to existing categories.

## Scope
- Add category button functionality on catalog and category nodes
- Modal form for category creation
- Field validation and business rules
- Backend API integration
- Real-time UI updates
- Excel synchronization

## Test Strategy
Following Test-Driven Development (TDD) principles:
1. Write failing tests first
2. Implement minimum code to pass tests
3. Refactor while keeping tests green
4. End-to-end testing

## ProductCategory Object Analysis
Based on the Excel template data:

### Fields
1. **Id** (String)
   - Salesforce ID (auto-generated)
   - Format: 0ZGdp0000000XXXGAE
   
2. **Name** (String)
   - Required field
   - Category display name
   - Examples: "Defensive Security", "Data Protection"
   
3. **ParentCategoryId** (String) 
   - Optional field (null for root categories)
   - References another ProductCategory Id
   - Establishes hierarchy

### Hierarchy Rules
- Categories can be added to:
  - Catalogs (creates root category with no ParentCategoryId)
  - Other categories (creates subcategory with ParentCategoryId)
- Categories support multiple levels of nesting
- Each category can have multiple child categories

## Test Cases

### 1. UI Component Tests

#### Test 1.1: Add Icon Visibility
- **Given**: User hovers over a catalog node
- **When**: Mouse enters the node area
- **Then**: + icon should appear on the right side of the node

#### Test 1.2: Add Icon on Categories
- **Given**: User hovers over a category node
- **When**: Mouse enters the node area  
- **Then**: + icon should appear on the right side of the node

#### Test 1.3: Icon Click Handler
- **Given**: + icon is visible on a node
- **When**: User clicks the icon
- **Then**: Add Category modal should open

### 2. Modal Form Tests

#### Test 2.1: Modal Structure
- **Given**: Add Category modal is open
- **When**: Modal renders
- **Then**: Should display:
  - Title: "Add Product Category"
  - Name field (required)
  - Parent context (e.g., "Adding to Catalog: Cyber" or "Adding to Category: Data Protection")
  - Cancel and Add Category buttons

#### Test 2.2: Required Field Validation
- **Given**: Modal is open with empty Name field
- **When**: User clicks Add Category
- **Then**: Error message "Name is required" should appear

#### Test 2.3: Name Field Character Limit
- **Given**: Modal is open
- **When**: User enters name longer than 255 characters
- **Then**: Field should limit input to 255 characters

#### Test 2.4: Special Characters in Name
- **Given**: Modal is open
- **When**: User enters "Test & Category (2025)"
- **Then**: Name should be accepted without modification

### 3. Business Logic Tests

#### Test 3.1: Root Category Creation
- **Given**: User is adding category to a catalog
- **When**: Category is created
- **Then**: ParentCategoryId should be null/empty

#### Test 3.2: Subcategory Creation
- **Given**: User is adding category to an existing category
- **When**: Category is created
- **Then**: ParentCategoryId should equal the parent category's Id

#### Test 3.3: Temporary ID Assignment
- **Given**: New category is created
- **When**: Before committing to Salesforce
- **Then**: Category should have temporary ID format: "temp_category_[timestamp]"

### 4. Integration Tests

#### Test 4.1: Change Tracker Integration
- **Given**: New category is added
- **When**: Addition is tracked
- **Then**: changeTracker.additions should contain the new category

#### Test 4.2: Commit Process
- **Given**: New category in change tracker
- **When**: User commits changes
- **Then**: 
  - Category should be created in Salesforce
  - Temporary ID replaced with real Salesforce ID
  - Excel file updated

#### Test 4.3: UI Update After Commit
- **Given**: Category successfully committed
- **When**: Commit completes
- **Then**: 
  - New category appears in hierarchy
  - No page reload required
  - Category positioned correctly under parent

### 5. Edge Case Tests

#### Test 5.1: Adding to Deleted Parent
- **Given**: Parent category is marked for deletion
- **When**: User tries to add subcategory
- **Then**: Warning message should appear

#### Test 5.2: Duplicate Names
- **Given**: Category "Data Protection" exists
- **When**: User tries to add another "Data Protection"
- **Then**: System should allow (Salesforce handles uniqueness)

#### Test 5.3: Deep Nesting
- **Given**: Category hierarchy 5 levels deep
- **When**: User adds 6th level
- **Then**: Should work normally (no artificial depth limit)

### 6. Error Handling Tests

#### Test 6.1: Network Error
- **Given**: Network connection fails
- **When**: Committing new category
- **Then**: Error modal with retry option

#### Test 6.2: Salesforce Validation Error
- **Given**: Salesforce rejects category
- **When**: Commit response received
- **Then**: Error modal with specific error message

## Test Data

### Sample Categories to Create
1. **Root Category**
   - Name: "Test Category Root"
   - Parent: Cyber catalog
   - Expected ParentCategoryId: null

2. **Subcategory Level 1**
   - Name: "Test Subcategory L1"
   - Parent: "Test Category Root"
   - Expected ParentCategoryId: [ID of Test Category Root]

3. **Subcategory Level 2**
   - Name: "Test Subcategory L2"
   - Parent: "Test Subcategory L1"
   - Expected ParentCategoryId: [ID of Test Subcategory L1]

## Success Criteria
- All tests pass
- Feature works in Chrome, Firefox, Safari
- No console errors
- Smooth user experience
- Excel file stays synchronized
- Changes persist after page reload

## Test Execution Plan
1. Unit tests for individual components
2. Integration tests for component interaction
3. End-to-end tests for complete workflow
4. Manual exploratory testing
5. Performance testing with large hierarchies

## Dependencies
- Change Tracker system
- Excel synchronization
- Salesforce API connectivity
- D3.js visualization framework