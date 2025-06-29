# Transaction Objects Behavior

## Overview
Transaction objects like Order, OrderItem, Asset, etc. don't have sheets in the Revenue Cloud upload workbook because they are typically created through the application interface or API, not through bulk upload.

## Expected Behavior

### 1. Sync Status
After syncing, transaction objects should show:
- Status: **◯ No Data** 
- Record Count: **0**
- Last Synced: **[timestamp]**

This is correct behavior because:
- These objects have no upload template sheets
- They contain 0 records in the context of the upload workbook
- The sync was successful (it correctly identified there's no data to sync)

### 2. View Modal
When clicking "View" on a transaction object:
- Shows an informational message explaining why there's no sheet
- Message: "No sheet available for [Object] in the workbook"
- Additional context about transaction objects

This is the expected behavior, not an error.

### 3. Objects Affected
The following objects are transaction objects without sheets:
- Order
- OrderItem
- Asset
- AssetAction
- AssetActionSource
- Contract
- ProductSellingModelOption

## Technical Implementation

### Simulated Sync Counts
```javascript
// Transaction objects (no sheets in workbook)
'Order': 0,
'OrderItem': 0,
'Asset': 0,
'AssetAction': 0,
'AssetActionSource': 0,
'Contract': 0,
'ProductSellingModelOption': 0
```

### Status Display
- These objects correctly show "◯ No Data" after sync
- This differentiates them from configuration objects that have sheets but no data

## User Guidance
For transaction objects, users should:
1. Create them through the Salesforce UI or API
2. Use the Revenue Cloud transaction creation flows
3. Not expect to bulk upload these objects

## Summary
The current behavior is correct and intentional. Transaction objects showing "◯ No Data" status and an informational message when viewing is the expected behavior, not a bug.