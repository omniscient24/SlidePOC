/**
 * Inline Field Editor for Product Hierarchy
 * Enables double-click editing of product node fields with validation
 */

class InlineEditor {
    constructor() {
        this.activeEditor = null;
        this.permissions = null;
        this.fieldConfig = null;
        this.changeTracker = null; // Will be initialized from change-tracker.js
        this.editableFields = [
            'name', 'description', 'status', 'code', 
            'isActive', 'quantityUnitOfMeasure', 
            'family', 'displayUrl', 'externalDataSourceId',
            'stockKeepingUnit', 'productClass'
        ];
    }

    async initialize() {
        // Load user permissions and field configuration
        await this.loadPermissions();
        await this.loadFieldConfig();
        
        // Enable edit mode for nodes
        this.enableEditMode();
        
        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        console.log('InlineEditor initialized');
    }

    async loadPermissions() {
        try {
            const response = await fetch('/api/edit/permissions');
            const data = await response.json();
            this.permissions = data;
        } catch (error) {
            console.error('Failed to load permissions:', error);
            this.permissions = { permission_level: 'view_only' };
        }
    }

    async loadFieldConfig() {
        try {
            const response = await fetch('/api/edit/field-config');
            const data = await response.json();
            this.fieldConfig = data.fields || [];
        } catch (error) {
            console.error('Failed to load field config:', error);
            this.fieldConfig = [];
        }
    }

    canEditField(fieldName) {
        // Check if user has edit permissions
        if (!this.permissions || this.permissions.permission_level === 'view_only') {
            return false;
        }

        // Check field-specific configuration
        const fieldConf = this.fieldConfig.find(f => f.field_name === fieldName);
        if (fieldConf && !fieldConf.is_editable) {
            return false;
        }

        // Check permission level requirements
        if (fieldConf && fieldConf.permission_level) {
            const requiredLevel = this.getPermissionValue(fieldConf.permission_level);
            const userLevel = this.getPermissionValue(this.permissions.permission_level);
            return userLevel >= requiredLevel;
        }

        return true;
    }

    getPermissionValue(level) {
        const levels = {
            'view_only': 0,
            'edit_basic': 1,
            'edit_structure': 2,
            'full_edit': 3,
            'admin': 4
        };
        return levels[level] || 0;
    }

    enableEditMode() {
        // Enable editing for detail panel fields
        const detailPanel = document.getElementById('details-content');
        if (detailPanel) {
            // Add hover indicators for editable fields in detail panel
            const detailFields = detailPanel.querySelectorAll('[data-field]');
            detailFields.forEach(field => {
                const fieldName = field.getAttribute('data-field');
                if (this.canEditField(fieldName)) {
                    // Add hover effect
                    field.style.cursor = 'pointer';
                    field.addEventListener('mouseenter', () => {
                        this.showFieldEditIndicator(field);
                    });
                    field.addEventListener('mouseleave', () => {
                        this.hideFieldEditIndicator(field);
                    });
                    
                    // Add double-click handler
                    field.addEventListener('dblclick', (event) => {
                        event.stopPropagation();
                        // Get the current selected node data
                        if (window.selectedNode && window.selectedNode.data) {
                            this.activateFieldEdit(window.selectedNode.data, fieldName, field);
                        }
                    });
                }
            });
        }
        
        // Also enable for hierarchy nodes (original functionality)
        d3.selectAll('.node').on('mouseover', (event, d) => {
            this.showEditIndicators(event.currentTarget, d);
        }).on('mouseout', (event, d) => {
            this.hideEditIndicators(event.currentTarget);
        });

        // Enable double-click editing on nodes
        d3.selectAll('.node').on('dblclick', (event, d) => {
            event.stopPropagation();
            const target = event.target;
            
            // Find which field was clicked
            const fieldElement = target.closest('[data-field]');
            if (fieldElement) {
                const fieldName = fieldElement.getAttribute('data-field');
                if (this.canEditField(fieldName)) {
                    this.activateFieldEdit(d, fieldName, fieldElement);
                }
            }
        });
    }

    showFieldEditIndicator(field) {
        // Add pencil icon if not already present
        if (!field.querySelector('.edit-icon')) {
            const icon = document.createElement('span');
            icon.className = 'edit-icon';
            icon.innerHTML = '✏️';
            icon.style.marginLeft = '5px';
            icon.style.opacity = '0.7';
            icon.style.cursor = 'pointer';
            field.appendChild(icon);
        }
    }
    
    hideFieldEditIndicator(field) {
        const icon = field.querySelector('.edit-icon');
        if (icon) {
            icon.remove();
        }
    }

    showEditIndicators(nodeElement, nodeData) {
        if (this.permissions.permission_level === 'view_only') return;

        const fields = nodeElement.querySelectorAll('[data-field]');
        fields.forEach(field => {
            const fieldName = field.getAttribute('data-field');
            if (this.canEditField(fieldName)) {
                // Add pencil icon
                if (!field.querySelector('.edit-icon')) {
                    const icon = document.createElement('span');
                    icon.className = 'edit-icon';
                    icon.innerHTML = '✏️';
                    icon.style.marginLeft = '5px';
                    icon.style.opacity = '0.7';
                    icon.style.cursor = 'pointer';
                    field.appendChild(icon);
                }
                field.style.cursor = 'pointer';
            }
        });
    }

    hideEditIndicators(nodeElement) {
        const icons = nodeElement.querySelectorAll('.edit-icon');
        icons.forEach(icon => icon.remove());
        
        const fields = nodeElement.querySelectorAll('[data-field]');
        fields.forEach(field => {
            field.style.cursor = '';
        });
    }

    activateFieldEdit(nodeData, fieldName, fieldElement) {
        // If another field is being edited, save it first
        if (this.activeEditor) {
            this.saveActiveField();
        }

        const currentValue = nodeData[fieldName] || '';
        const fieldConfig = this.fieldConfig.find(f => f.field_name === fieldName) || {};
        
        // Create input element based on field type
        const input = this.createInputElement(fieldName, currentValue, fieldConfig);
        
        // Store original value
        input.dataset.originalValue = currentValue;
        input.dataset.nodeId = nodeData.id;
        input.dataset.fieldName = fieldName;
        
        // Replace field content with input
        const originalContent = fieldElement.innerHTML;
        fieldElement.innerHTML = '';
        fieldElement.appendChild(input);
        
        // Apply edit mode styling
        fieldElement.classList.add('field-editing');
        
        // Focus and select input
        input.focus();
        if (input.select) input.select();
        
        // Set up event handlers
        this.setupFieldEventHandlers(input, fieldElement, originalContent);
        
        this.activeEditor = {
            input: input,
            fieldElement: fieldElement,
            originalContent: originalContent,
            nodeData: nodeData
        };
    }

    createInputElement(fieldName, value, config) {
        let input;
        
        switch (config.field_type) {
            case 'boolean':
            case 'checkbox':
                input = document.createElement('input');
                input.type = 'checkbox';
                input.checked = value === true || value === 'true';
                break;
                
            case 'picklist':
                input = document.createElement('select');
                if (config.picklist_values) {
                    config.picklist_values.forEach(option => {
                        const opt = document.createElement('option');
                        opt.value = option.value || option;
                        opt.textContent = option.label || option;
                        if (opt.value === value) opt.selected = true;
                        input.appendChild(opt);
                    });
                }
                break;
                
            case 'textarea':
            case 'longtext':
                input = document.createElement('textarea');
                input.value = value;
                input.rows = 3;
                break;
                
            case 'number':
            case 'currency':
            case 'percent':
                input = document.createElement('input');
                input.type = 'number';
                input.value = value;
                if (config.precision !== undefined) {
                    input.step = Math.pow(10, -config.precision);
                }
                break;
                
            default:
                input = document.createElement('input');
                input.type = 'text';
                input.value = value;
                if (config.max_length) {
                    input.maxLength = config.max_length;
                }
        }
        
        input.className = 'inline-edit-input';
        return input;
    }

    setupFieldEventHandlers(input, fieldElement, originalContent) {
        // Save on Enter (except for textarea)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && input.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.saveField(input);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelEdit(input, fieldElement, originalContent);
            } else if (e.key === 'Tab') {
                e.preventDefault();
                this.saveField(input);
                this.moveToNextField(e.shiftKey);
            }
        });

        // Save on blur
        input.addEventListener('blur', (e) => {
            // Small delay to allow for clicks on validation messages
            setTimeout(() => {
                if (this.activeEditor && this.activeEditor.input === input) {
                    this.saveField(input);
                }
            }, 200);
        });
    }

    saveField(input) {
        const nodeId = input.dataset.nodeId;
        const fieldName = input.dataset.fieldName;
        const originalValue = input.dataset.originalValue;
        let newValue = input.value;
        
        // Handle checkbox values
        if (input.type === 'checkbox') {
            newValue = input.checked;
        }
        
        // Validate field
        const validation = this.validateField(fieldName, newValue);
        if (!validation.valid) {
            this.showValidationError(input, validation.errors);
            return false;
        }
        
        // Check if value changed
        if (String(newValue) !== String(originalValue)) {
            // Add to change tracker
            if (this.changeTracker) {
                this.changeTracker.addChange(nodeId, fieldName, originalValue, newValue);
            }
            
            // Update node data
            const node = window.hierarchyData.nodes.find(n => n.id === nodeId);
            if (node) {
                node[fieldName] = newValue;
            }
            
            // Mark node as modified
            this.markNodeAsModified(nodeId);
        }
        
        // Clean up
        this.cleanupEditor();
        
        // Update display
        this.updateFieldDisplay(nodeId, fieldName, newValue);
        
        return true;
    }

    cancelEdit(input, fieldElement, originalContent) {
        fieldElement.innerHTML = originalContent;
        fieldElement.classList.remove('field-editing');
        this.activeEditor = null;
    }

    cleanupEditor() {
        if (this.activeEditor) {
            this.activeEditor.fieldElement.classList.remove('field-editing');
            this.activeEditor = null;
        }
    }

    saveActiveField() {
        if (this.activeEditor) {
            this.saveField(this.activeEditor.input);
        }
    }

    validateField(fieldName, value) {
        const errors = [];
        const fieldConfig = this.fieldConfig.find(f => f.field_name === fieldName) || {};
        
        // Required field validation
        if (fieldConfig.required && (!value || value === '')) {
            errors.push(`${fieldConfig.field_label || fieldName} is required`);
        }
        
        // Field type validation
        if (fieldConfig.field_type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                errors.push('Invalid email format');
            }
        }
        
        if (fieldConfig.field_type === 'url' && value) {
            try {
                new URL(value);
            } catch {
                errors.push('Invalid URL format');
            }
        }
        
        // Custom validation rules
        if (fieldConfig.validation_rules) {
            try {
                const rules = JSON.parse(fieldConfig.validation_rules);
                
                if (rules.min_length && value.length < rules.min_length) {
                    errors.push(`Minimum length is ${rules.min_length} characters`);
                }
                
                if (rules.max_length && value.length > rules.max_length) {
                    errors.push(`Maximum length is ${rules.max_length} characters`);
                }
                
                if (rules.pattern) {
                    const regex = new RegExp(rules.pattern);
                    if (!regex.test(value)) {
                        errors.push(rules.pattern_message || 'Invalid format');
                    }
                }
            } catch (e) {
                console.error('Invalid validation rules:', e);
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    showValidationError(input, errors) {
        // Remove existing error tooltip
        const existingTooltip = document.querySelector('.validation-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }
        
        // Add error styling
        input.classList.add('field-error');
        
        // Create error tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'validation-tooltip';
        tooltip.innerHTML = errors.join('<br>');
        
        // Position tooltip
        const rect = input.getBoundingClientRect();
        tooltip.style.position = 'fixed';
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.bottom + 5) + 'px';
        
        document.body.appendChild(tooltip);
        
        // Remove tooltip after 3 seconds
        setTimeout(() => {
            tooltip.remove();
            input.classList.remove('field-error');
        }, 3000);
    }

    updateFieldDisplay(nodeId, fieldName, newValue) {
        // Update the D3 visualization node
        const nodeElement = d3.select(`[data-node-id="${nodeId}"]`).node();
        if (nodeElement) {
            const fieldElement = nodeElement.querySelector(`[data-field="${fieldName}"]`);
            if (fieldElement) {
                if (typeof newValue === 'boolean') {
                    fieldElement.textContent = newValue ? 'Yes' : 'No';
                } else {
                    fieldElement.textContent = newValue || '';
                }
            }
            
            // Special handling for name field in D3 nodes
            if (fieldName === 'name') {
                const textElement = d3.select(nodeElement).select('text');
                if (!textElement.empty()) {
                    textElement.text(newValue);
                }
            }
        }
        
        // Also update the details panel if it's showing this node
        if (window.selectedNode && window.selectedNode.data && window.selectedNode.data.id === nodeId) {
            const detailsPanel = document.getElementById('details-content');
            if (detailsPanel) {
                const detailField = detailsPanel.querySelector(`[data-field="${fieldName}"]`);
                if (detailField) {
                    if (typeof newValue === 'boolean') {
                        detailField.textContent = newValue ? 'Yes' : 'No';
                    } else {
                        detailField.textContent = newValue || '';
                    }
                }
            }
        }
    }

    markNodeAsModified(nodeId) {
        const nodeElement = d3.select(`[data-node-id="${nodeId}"]`);
        nodeElement.classed('node-modified', true);
        
        // Update change count
        if (this.changeTracker) {
            const changeCount = this.changeTracker.getNodeChangeCount(nodeId);
            
            // Remove existing icon if any
            nodeElement.select('.node-modified-icon').remove();
            
            if (changeCount > 0) {
                // Add modified icon
                const iconGroup = nodeElement.append('g')
                    .attr('class', 'node-modified-icon')
                    .attr('data-change-count', changeCount);
                
                // Position relative to node rect
                const rect = nodeElement.select('rect').node();
                if (rect) {
                    const bbox = rect.getBBox();
                    iconGroup.attr('transform', `translate(${bbox.x + bbox.width - 10}, ${bbox.y + 10})`);
                }
                
                // Add background circle
                iconGroup.append('circle')
                    .attr('r', 10)
                    .attr('fill', '#FF0000')
                    .style('filter', 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))');
                
                // Add edit icon (using path for Ant Design EditOutlined icon)
                iconGroup.append('path')
                    .attr('d', 'M257.7 752c2 0 4-.2 6-.5L431.9 722c2-.4 3.9-1.3 5.3-2.8l423.9-423.9a9.96 9.96 0 0 0 0-14.1L694.9 114.9c-1.9-1.9-4.4-2.9-7.1-2.9s-5.2 1-7.1 2.9L256.8 538.8c-1.5 1.5-2.4 3.3-2.8 5.3l-29.5 168.2a33.5 33.5 0 0 0 9.4 29.8c6.6 6.4 14.9 9.9 23.8 9.9z')
                    .attr('fill', 'white')
                    .attr('transform', 'translate(-6, -6) scale(0.012)');
            }
        }
    }

    moveToNextField(reverse = false) {
        // Get all editable fields in the current node
        const currentNode = this.activeEditor?.fieldElement.closest('.node');
        if (!currentNode) return;
        
        const editableFields = Array.from(currentNode.querySelectorAll('[data-field]'))
            .filter(field => {
                const fieldName = field.getAttribute('data-field');
                return this.canEditField(fieldName);
            });
        
        const currentIndex = editableFields.indexOf(this.activeEditor.fieldElement);
        let nextIndex = reverse ? currentIndex - 1 : currentIndex + 1;
        
        if (nextIndex >= 0 && nextIndex < editableFields.length) {
            const nextField = editableFields[nextIndex];
            const fieldName = nextField.getAttribute('data-field');
            const nodeData = this.activeEditor.nodeData;
            
            // Activate edit on next field
            setTimeout(() => {
                this.activateFieldEdit(nodeData, fieldName, nextField);
            }, 100);
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + E to edit selected node
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const selectedNode = d3.select('.node-selected').node();
                if (selectedNode) {
                    const firstEditableField = selectedNode.querySelector('[data-field]');
                    if (firstEditableField) {
                        firstEditableField.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
                    }
                }
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.inlineEditor = new InlineEditor();
});