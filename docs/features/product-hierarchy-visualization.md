# Product Hierarchy Visualization

## Overview

The Product Hierarchy Visualization is an interactive web-based tool that displays Salesforce product hierarchies in a clear, organized tree structure. Built with D3.js, it provides a visual representation of product relationships, making it easy to understand complex product structures, bundle compositions, and organizational hierarchies.

## Important Requirements

### Default Collapsed State
- **CRITICAL REQUIREMENT**: The product hierarchy visualization page MUST always load with the hierarchy in a collapsed/retracted state
- Only top-level catalogs should be visible on initial page load
- Users must manually expand nodes to see their children
- This ensures optimal performance and provides a cleaner initial view, especially important for large hierarchies
- This requirement is permanent and should not be changed without explicit authorization

## Key Features

### 1. Fixed Column Layout with D3.js Tree Visualization
- Products are organized into distinct vertical columns based on their hierarchy level
- Each column represents a specific depth in the product tree:
  - **Column 1**: Root-level products (typically main product families)
  - **Column 2**: Sub-products or product categories
  - **Column 3**: Individual products or variants
  - **Column 4+**: Bundle components and nested items
- Fixed column widths ensure consistent alignment across all hierarchy levels

### 2. Vertical-Only Drag Functionality
- Nodes can be dragged vertically within their assigned column
- When dragging a parent node, all child nodes move together maintaining their relative positions
- Horizontal movement is restricted to preserve the hierarchical column structure
- Manual positions are preserved across expand/collapse operations

### 3. Expand/Collapse with Visual Indicators
- Each parent node features a +/- icon for expanding/collapsing child nodes
- **Plus (+)**: Indicates collapsed state with hidden children
- **Minus (-)**: Indicates expanded state with visible children
- Icons are positioned on the left side of nodes for easy access
- Smooth animations provide visual feedback during expand/collapse operations

### 4. Column Headers with Color Coding
- Each column has a header displaying the hierarchy level name
- Color-coded headers provide visual separation:
  - Level 1: Blue (#4A90E2)
  - Level 2: Green (#7ED321)
  - Level 3: Orange (#F5A623)
  - Level 4+: Purple (#9013FE)
- Headers remain fixed at the top for easy reference while scrolling

### 5. Bundle Components Support
- Special handling for product bundles with component relationships
- Bundle components are displayed as child nodes under their parent bundle
- Hardcoded mappings ensure proper bundle structure representation
- Visual indicators distinguish bundle products from regular products

### 6. Parent-Aligned Expansion
- When expanding a node, children appear directly below the parent
- Subsequent sibling nodes automatically shift down to accommodate
- Maintains visual hierarchy and reading flow

### 7. Full-Width Responsive Design
- Visualization spans the entire browser width
- Automatically adjusts to different screen sizes
- Maintains column proportions across various displays

### 8. Zoom Functionality
- Mouse wheel zoom for detailed inspection
- Zoom is centered on cursor position
- No pan functionality to maintain focus on vertical scrolling
- Zoom controls in the top-right corner for accessibility

### 9. Node Details Panel
- Click any node to view detailed information
- Details panel displays:
  - Product Name
  - Product Code
  - Product Family
  - Description (if available)
  - Active status
  - Additional metadata
- Panel appears on the right side of the screen

### 10. Left-Aligned Text in Nodes
- All text within nodes is left-aligned for better readability
- Consistent text positioning across all hierarchy levels
- Truncation with ellipsis for long product names

## Technical Implementation

### Architecture
```
product-hierarchy-visualization.html
├── D3.js v7 (Data visualization library)
├── Custom CSS (Styling and animations)
├── JavaScript modules
│   ├── Data processing
│   ├── Tree layout calculation
│   ├── Drag behavior handlers
│   └── Event management
└── Bundle mapping configuration
```

### Core Technologies
- **D3.js v7**: Powers the tree visualization and interactive behaviors
- **SVG**: Renders the visual elements with scalable graphics
- **CSS3**: Provides styling, animations, and responsive design
- **Vanilla JavaScript**: Handles data processing and user interactions

### Key Components

#### 1. Data Structure
```javascript
{
  name: "Product Name",
  code: "PROD-001",
  family: "Product Family",
  description: "Product description",
  isActive: true,
  level: 1,
  children: [
    // Child products
  ]
}
```

#### 2. Fixed Column Layout Algorithm
- Calculates node positions based on hierarchy depth
- Maintains consistent column spacing (300px default)
- Dynamically adjusts vertical spacing based on node count

#### 3. Drag Behavior Implementation
- Custom drag handler restricts horizontal movement
- Maintains relative positions of child nodes
- Updates stored positions for persistence

#### 4. Bundle Component Mappings
- Hardcoded relationships define bundle structures
- Mapping format: `parentCode: [childCode1, childCode2, ...]`
- Automatically creates hierarchy for bundle products

## Data Flow

### 1. Salesforce Organization
- Product2 records contain the source data
- Fields captured:
  - Name
  - ProductCode
  - Family
  - Description
  - IsActive
  - Custom hierarchy fields

### 2. Data Export Process
1. SOQL query extracts product data from Salesforce
2. Results exported to Excel format
3. Excel file includes all product attributes and relationships

### 3. Excel to Visualization Pipeline
1. Excel data is converted to JSON format
2. Hierarchy relationships are established
3. Bundle mappings are applied
4. Final tree structure is generated

### 4. Visualization Rendering
1. D3.js processes the hierarchical data
2. Tree layout is calculated with fixed columns
3. SVG elements are created for nodes and links
4. Interactive behaviors are attached

## Bundle Component Hardcoded Mappings

### Purpose
Bundle component mappings define the relationship between bundle products and their components when this information isn't directly available in the Salesforce data.

### Implementation
```javascript
const bundleMappings = {
  'BUNDLE-001': ['COMP-001', 'COMP-002', 'COMP-003'],
  'BUNDLE-002': ['COMP-004', 'COMP-005'],
  // Additional mappings as needed
};
```

### Usage
- Applied during data processing phase
- Creates parent-child relationships for bundle products
- Ensures components appear under their respective bundles
- Can be updated to reflect new bundle configurations

## Usage Instructions

### 1. Preparing Your Data
1. Export Product2 data from Salesforce to Excel
2. Ensure the following columns are present:
   - Name (Product name)
   - ProductCode (Unique identifier)
   - Family (Product family/category)
   - Description (Optional)
   - IsActive (Boolean)
   - Any custom hierarchy fields

### 2. Loading the Visualization
1. Open `product-hierarchy-visualization.html` in a modern web browser
2. The visualization will automatically render with sample data
3. To use your own data:
   - Convert Excel data to JSON format
   - Update the data source in the HTML file
   - Refresh the page

### 3. Interacting with the Visualization

#### Navigation
- **Scroll**: Use mouse wheel or trackpad to navigate vertically
- **Zoom**: Hold Ctrl/Cmd and scroll to zoom in/out
- **Click**: Select any node to view details

#### Organizing Nodes
- **Drag**: Click and hold a node to drag it vertically
- **Drop**: Release to place the node in its new position
- Position is maintained when collapsing/expanding

#### Exploring Hierarchy
- **Expand**: Click the + icon to show child nodes
- **Collapse**: Click the - icon to hide child nodes
- **Expand All**: Use the control button to expand entire tree
- **Collapse All**: Use the control button to collapse to root level

### 4. Customization Options

#### Styling
- Modify CSS variables for colors and dimensions
- Adjust column widths in the configuration
- Customize node appearance and animations

#### Data Mappings
- Update bundle component mappings in the code
- Add custom attributes to node display
- Modify hierarchy logic for specific needs

### 5. Best Practices
- Keep product codes unique and consistent
- Maintain clear product family categorization
- Regular updates to bundle mappings
- Test with various data sizes for performance

## Troubleshooting

### Common Issues

1. **Nodes not appearing**
   - Check data format and structure
   - Verify product codes are unique
   - Ensure hierarchy relationships are valid

2. **Drag not working**
   - Confirm JavaScript is enabled
   - Check browser console for errors
   - Verify D3.js library is loaded

3. **Bundle components missing**
   - Review bundle mappings configuration
   - Ensure component product codes match
   - Check for typos in mapping definitions

4. **Performance issues**
   - Limit initial expanded nodes
   - Consider pagination for large datasets
   - Optimize rendering for deep hierarchies

### Browser Compatibility
- Chrome 90+ (Recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

### Planned Features
1. **Search Functionality**: Find products by name or code
2. **Export Options**: Save visualization as image or PDF
3. **Real-time Updates**: Connect directly to Salesforce
4. **Filtering**: Show/hide products by criteria
5. **Custom Layouts**: Alternative visualization styles

### Integration Possibilities
1. **Salesforce Lightning**: Embed as Lightning component
2. **API Integration**: Direct connection to Salesforce APIs
3. **Collaborative Features**: Multi-user editing support
4. **Analytics**: Usage tracking and insights

## Conclusion

The Product Hierarchy Visualization provides a powerful way to understand and manage complex product structures in Salesforce. Its intuitive interface and rich feature set make it an essential tool for product managers, administrators, and anyone working with Salesforce product catalogs.