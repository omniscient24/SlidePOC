# Revenue Cloud Migration Tool - UI/UX Style Guide

## 1. Design Principles

### Core Principles
1. **Clarity**: Every element should have a clear purpose
2. **Consistency**: Similar actions should look and behave similarly
3. **Feedback**: Users should always know what's happening
4. **Efficiency**: Common tasks should be quick and easy
5. **Error Prevention**: Design to prevent mistakes before they happen

## 2. Visual Design System

### Color Palette

#### Primary Colors
- **Primary Blue**: `#0066cc` - Main CTAs, links, active states
- **Primary Dark**: `#004499` - Hover states, emphasis
- **Primary Light**: `#3399ff` - Backgrounds, subtle highlights

#### Semantic Colors
- **Success Green**: `#28a745` - Success messages, completed states
- **Warning Orange**: `#ff6b35` - Warnings, attention needed
- **Error Red**: `#dc3545` - Errors, destructive actions
- **Info Blue**: `#17a2b8` - Information, tips

#### Neutral Colors
- **Text Primary**: `#333333` - Main body text
- **Text Secondary**: `#666666` - Secondary text, descriptions
- **Border**: `#e0e0e0` - Borders, dividers
- **Background**: `#f8f9fa` - Page background
- **White**: `#ffffff` - Cards, content areas

### Typography

#### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

#### Type Scale
- **Heading 1**: 2rem (32px) - Page titles
- **Heading 2**: 1.5rem (24px) - Section headings
- **Heading 3**: 1.25rem (20px) - Subsection headings
- **Body**: 1rem (16px) - Regular text
- **Small**: 0.875rem (14px) - Helper text, labels
- **Tiny**: 0.75rem (12px) - Timestamps, metadata

### Spacing System
- **Base unit**: 8px
- **Spacing scale**: 0, 4px, 8px, 16px, 24px, 32px, 48px, 64px
- **Common patterns**:
  - Component padding: 16px
  - Section margins: 32px
  - Inline spacing: 8px

### Layout Grid
- **Container max-width**: 1200px
- **Grid columns**: 12
- **Gutter**: 24px
- **Breakpoints**:
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px

## 3. Component Library

### Buttons

#### Primary Button
```css
.btn-primary {
    background-color: #0066cc;
    color: white;
    padding: 10px 20px;
    border-radius: 4px;
    border: none;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}
.btn-primary:hover {
    background-color: #004499;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

#### Secondary Button
```css
.btn-secondary {
    background-color: white;
    color: #0066cc;
    border: 1px solid #0066cc;
    /* Same padding and properties as primary */
}
```

#### Button States
- **Default**: Normal appearance
- **Hover**: Darker shade, subtle lift
- **Active**: Pressed appearance
- **Disabled**: 50% opacity, cursor not-allowed
- **Loading**: Show spinner, disable interaction

### Cards
```css
.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 24px;
    margin-bottom: 24px;
    transition: box-shadow 0.2s ease;
}
.card:hover {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

### Forms

#### Input Fields
```css
.form-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    font-size: 16px;
    transition: border-color 0.2s ease;
}
.form-input:focus {
    outline: none;
    border-color: #0066cc;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
}
```

#### Labels
```css
.form-label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
    color: #333333;
}
```

### Progress Indicators

#### Progress Bar
```css
.progress-bar {
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    background: #0066cc;
    transition: width 0.3s ease;
}
```

#### Stepper
```css
.stepper-item {
    display: flex;
    align-items: center;
}
.stepper-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.stepper-circle.completed {
    background: #28a745;
    color: white;
}
.stepper-circle.active {
    background: #0066cc;
    color: white;
}
.stepper-circle.pending {
    background: white;
    border: 2px solid #e0e0e0;
    color: #666666;
}
```

### Alerts
```css
.alert {
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
}
.alert-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
.alert-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
.alert-info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}
```

### Tables
```css
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}
.data-table th {
    background: #f8f9fa;
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #e0e0e0;
}
.data-table td {
    padding: 12px;
    border-bottom: 1px solid #e0e0e0;
}
.data-table tr:hover {
    background: #f8f9fa;
}
```

### Modal Dialogs
```css
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}
.modal-content {
    background: white;
    border-radius: 8px;
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow: auto;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.modal-header {
    padding: 24px;
    border-bottom: 1px solid #e0e0e0;
}
.modal-body {
    padding: 24px;
}
.modal-footer {
    padding: 16px 24px;
    border-top: 1px solid #e0e0e0;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
```

## 4. Interaction Patterns

### Loading States
1. **Inline Loading**: Replace content with spinner
2. **Overlay Loading**: Semi-transparent overlay with spinner
3. **Progress Loading**: Show progress bar with percentage
4. **Skeleton Loading**: Show placeholder shapes

### Form Validation
1. **Real-time**: Validate as user types (debounced)
2. **On Blur**: Validate when field loses focus
3. **On Submit**: Final validation before submission
4. **Error Display**: Show errors below fields with red text

### Navigation
1. **Primary Nav**: Horizontal top navigation
2. **Secondary Nav**: Sidebar for sub-navigation
3. **Breadcrumbs**: Show current location
4. **Back Links**: Always provide way back

### Feedback Patterns
1. **Success**: Green toast notification, auto-dismiss after 5s
2. **Error**: Red alert box, must be dismissed
3. **Progress**: Modal with progress bar
4. **Confirmation**: Modal dialog with clear actions

## 5. Accessibility Guidelines

### WCAG 2.1 AA Compliance
1. **Color Contrast**: Minimum 4.5:1 for normal text
2. **Focus Indicators**: Visible focus states for all interactive elements
3. **Keyboard Navigation**: Full keyboard accessibility
4. **Screen Reader Support**: Proper ARIA labels and roles

### Best Practices
1. Use semantic HTML elements
2. Provide alternative text for images
3. Ensure forms have proper labels
4. Include skip navigation links
5. Test with keyboard only
6. Test with screen readers

## 6. Icons

### Icon Library
Use Font Awesome 5 or similar icon font:
- **Success**: ✓ (check mark)
- **Error**: ✕ (x mark)
- **Warning**: ⚠ (triangle exclamation)
- **Info**: ⓘ (circle i)
- **Upload**: ↑ (arrow up)
- **Download**: ↓ (arrow down)
- **Sync**: ⟲ (circular arrows)
- **Delete**: 🗑 (trash can)
- **Edit**: ✎ (pencil)
- **Search**: 🔍 (magnifying glass)

## 7. Responsive Behavior

### Mobile First Approach
1. Design for mobile screens first
2. Enhance for larger screens
3. Test on real devices

### Breakpoint Behaviors
- **Mobile**: Stack elements vertically, full-width buttons
- **Tablet**: 2-column layouts where appropriate
- **Desktop**: Full layouts with sidebars

## 8. Animation Guidelines

### Principles
1. **Purpose**: Every animation should have a purpose
2. **Performance**: Keep animations smooth (60fps)
3. **Duration**: Most transitions 200-300ms
4. **Easing**: Use ease-out for most animations

### Common Animations
```css
/* Standard transition */
transition: all 0.2s ease-out;

/* Hover lift */
transform: translateY(-2px);

/* Fade in */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Slide in */
@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
```

## 9. Code Standards

### CSS Architecture
1. Use BEM naming convention
2. Keep specificity low
3. Use CSS variables for theming
4. Mobile-first media queries

### HTML Standards
1. Semantic HTML5 elements
2. Proper heading hierarchy
3. Valid HTML markup
4. Accessibility attributes

### JavaScript Standards
1. Progressive enhancement
2. Event delegation where appropriate
3. Debounce expensive operations
4. Handle errors gracefully

## 10. Testing Checklist

### Visual Testing
- [ ] Colors meet contrast requirements
- [ ] Typography is readable
- [ ] Spacing is consistent
- [ ] Components align properly

### Interaction Testing
- [ ] All buttons are clickable
- [ ] Forms validate properly
- [ ] Loading states display
- [ ] Error states are clear

### Responsive Testing
- [ ] Mobile layout works
- [ ] Tablet layout works
- [ ] Desktop layout works
- [ ] No horizontal scroll

### Accessibility Testing
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Focus indicators visible
- [ ] Color not sole indicator