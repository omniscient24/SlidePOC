/**
 * AddNodeManager - Handles the addition of new nodes to the product hierarchy
 * 
 * This class manages the UI flow for adding new nodes, including:
 * - Displaying appropriate modal dialogs based on node type
 * - Validating form inputs
 * - Generating temporary IDs for staging
 * - Integrating with ChangeTracker for undo/redo support
 */
class AddNodeManager {
    constructor() {
        this.tempIdCounter = {
            catalog: 0,
            category: 0,
            product: 0,
            component: 0
        };
        this.initializeModals();
    }

    /**
     * Initialize modal HTML for different node types
     */
    initializeModals() {
        // Check if modals already exist
        if (!document.getElementById('add-catalog-modal')) {
            this.createAddCatalogModal();
        }
        // Future: Add other modal types
    }

    /**
     * Create the Add Catalog modal HTML
     */
    createAddCatalogModal() {
        // Add modal styles if not already present
        if (!document.getElementById('add-node-modal-styles')) {
            const styles = `
                <style id="add-node-modal-styles">
                    /* Modal overlay - follows UI guidelines */
                    .modal-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0, 0, 0, 0.5);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        z-index: 1000;
                    }
                    
                    /* Modal content - standard modal sizing */
                    .modal-overlay .modal-content {
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
                        min-width: 600px;
                        max-width: 800px;
                        max-height: 90vh;
                        display: flex;
                        flex-direction: column;
                        z-index: 1001;
                    }
                    
                    /* Modal header */
                    .modal-overlay .modal-header {
                        padding: 20px;
                        border-bottom: 1px solid #e8e8e8;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    }
                    
                    .modal-overlay .modal-header h3 {
                        margin: 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: #181818;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    
                    .modal-overlay .modal-close {
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #999;
                        padding: 0;
                        width: 32px;
                        height: 32px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 4px;
                        transition: all 0.2s;
                    }
                    
                    .modal-overlay .modal-close:hover {
                        background-color: #f5f5f5;
                        color: #333;
                    }
                    
                    /* Modal body */
                    .modal-overlay .modal-body {
                        padding: 20px;
                        overflow-y: auto;
                        flex: 1;
                    }
                    
                    /* Modal footer */
                    .modal-overlay .modal-footer {
                        padding: 20px;
                        border-top: 1px solid #e8e8e8;
                        display: flex;
                        justify-content: flex-end;
                        gap: 8px;
                    }
                    
                    /* Form styling */
                    .modal-overlay .form-group {
                        margin-bottom: 16px;
                    }
                    
                    .modal-overlay .form-group label {
                        display: block;
                        margin-bottom: 8px;
                        font-weight: 500;
                        color: #333;
                    }
                    
                    .modal-overlay .form-control {
                        width: 100%;
                        padding: 8px 12px;
                        border: 1px solid #d9d9d9;
                        border-radius: 4px;
                        font-size: 14px;
                        transition: all 0.3s;
                    }
                    
                    .modal-overlay .form-control:focus {
                        outline: none;
                        border-color: #1890ff;
                        box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
                    }
                    
                    .modal-overlay .form-control.error {
                        border-color: #ff4d4f;
                    }
                    
                    .modal-overlay .error-message {
                        color: #ff4d4f;
                        font-size: 12px;
                        margin-top: 4px;
                    }
                    
                    .modal-overlay .checkbox-label {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        cursor: pointer;
                    }
                    
                    .modal-overlay .checkbox-label input[type="checkbox"] {
                        cursor: pointer;
                    }
                    
                    .modal-overlay .required {
                        color: #ff4d4f;
                    }
                    
                    /* Button styling */
                    .modal-overlay .btn {
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-size: 14px;
                        cursor: pointer;
                        transition: all 0.3s;
                        border: 1px solid transparent;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                    }
                    
                    .modal-overlay .btn-primary {
                        background-color: #1890ff;
                        color: white;
                        border-color: #1890ff;
                    }
                    
                    .modal-overlay .btn-primary:hover {
                        background-color: #40a9ff;
                        border-color: #40a9ff;
                    }
                    
                    .modal-overlay .btn-secondary {
                        background-color: white;
                        color: #333;
                        border-color: #d9d9d9;
                    }
                    
                    .modal-overlay .btn-secondary:hover {
                        border-color: #1890ff;
                        color: #1890ff;
                    }
                </style>
            `;
            document.head.insertAdjacentHTML('beforeend', styles);
        }
        
        const modalHtml = `
            <div id="add-catalog-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3><i class="anticon"><svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor"><path d="M482 152h60q8 0 8 8v704q0 8-8 8h-60q-8 0-8-8V160q0-8 8-8z"></path><path d="M176 474h672q8 0 8 8v60q0 8-8 8H176q-8 0-8-8v-60q0-8 8-8z"></path></svg></i> Add New Catalog</h3>
                        <button class="modal-close" onclick="window.addNodeManager.closeModal('add-catalog-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="add-catalog-form" onsubmit="return false;">
                            <div class="form-group">
                                <label for="catalog-name">Name <span class="required">*</span></label>
                                <input type="text" id="catalog-name" name="name" class="form-control" required maxlength="255">
                                <div class="error-message" id="catalog-name-error"></div>
                            </div>
                            <div class="form-group">
                                <label for="catalog-code">Code</label>
                                <input type="text" id="catalog-code" name="code" class="form-control" maxlength="255" placeholder="Auto-generated from name if empty">
                                <div class="error-message" id="catalog-code-error"></div>
                            </div>
                            <div class="form-group">
                                <label for="catalog-description">Description</label>
                                <textarea id="catalog-description" name="description" class="form-control" rows="3" maxlength="1000"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="catalog-type">Catalog Type</label>
                                <select id="catalog-type" name="catalogType" class="form-control">
                                    <option value="Sales" selected>Sales</option>
                                    <option value="ServiceProcess">Service Process</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="catalog-effective-start-date">Effective Start Date</label>
                                <input type="datetime-local" id="catalog-effective-start-date" name="effectiveStartDate" class="form-control">
                                <div class="error-message" id="catalog-effective-start-date-error"></div>
                            </div>
                            <div class="form-group">
                                <label for="catalog-effective-end-date">Effective End Date</label>
                                <input type="datetime-local" id="catalog-effective-end-date" name="effectiveEndDate" class="form-control">
                                <div class="error-message" id="catalog-effective-end-date-error"></div>
                            </div>
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="catalog-active" name="isActive" checked>
                                    <span>Active</span>
                                </label>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="window.addNodeManager.closeModal('add-catalog-modal')">Cancel</button>
                        <button class="btn btn-primary" onclick="window.addNodeManager.submitAddCatalog()">
                            <i class="anticon"><svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor"><path d="M482 152h60q8 0 8 8v704q0 8-8 8h-60q-8 0-8-8V160q0-8 8-8z"></path><path d="M176 474h672q8 0 8 8v60q0 8-8 8H176q-8 0-8-8v-60q0-8 8-8z"></path></svg></i>
                            Add Catalog
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to document body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add click handler to close modal when clicking overlay
        const modal = document.getElementById('add-catalog-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal('add-catalog-modal');
            }
        });
        
        // Add ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                this.closeModal('add-catalog-modal');
            }
        };
        document.addEventListener('keydown', escHandler);
        
        // Store handler for cleanup
        modal.escHandler = escHandler;
    }

    /**
     * Create the Add Category modal HTML
     */
    createAddCategoryModal() {
        const modalHtml = `
            <div id="add-category-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3><i class="anticon"><svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor"><path d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zM704 536h-64v64c0 4.4-3.6 8-8 8h-56c-4.4 0-8-3.6-8-8v-64h-64c-4.4 0-8-3.6-8-8v-56c0-4.4 3.6-8 8-8h64v-64c0-4.4 3.6-8 8-8h56c4.4 0 8 3.6 8 8v64h64c4.4 0 8 3.6 8 8v56c0 4.4-3.6 8-8 8z"></path></svg></i> Add Product Category</h3>
                        <button class="modal-close" onclick="window.addNodeManager.closeModal('add-category-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="add-category-form" onsubmit="return false;">
                            <div class="form-group">
                                <label for="category-name">Name <span class="required">*</span></label>
                                <input type="text" id="category-name" name="name" class="form-control" required maxlength="255">
                                <div class="error-message" id="category-name-error"></div>
                            </div>
                            <div class="parent-info">
                                <!-- Parent context will be inserted here dynamically -->
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="window.addNodeManager.closeModal('add-category-modal')">Cancel</button>
                        <button class="btn btn-primary" onclick="window.addNodeManager.submitAddCategory()">
                            <i class="anticon"><svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor"><path d="M482 152h60q8 0 8 8v704q0 8-8 8h-60q-8 0-8-8V160q0-8 8-8z"></path><path d="M176 474h672q8 0 8 8v60q0 8-8 8H176q-8 0-8-8v-60q0-8 8-8z"></path></svg></i>
                            Add Category
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to document body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add click handler to close modal when clicking overlay
        const modal = document.getElementById('add-category-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal('add-category-modal');
            }
        });
        
        // Add ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                this.closeModal('add-category-modal');
            }
        };
        document.addEventListener('keydown', escHandler);
        
        // Store handler for cleanup
        modal.escHandler = escHandler;
    }

    /**
     * Show the appropriate add modal based on parent node type
     * @param {Object} parentNode - The parent node where the new node will be added
     */
    showAddModal(parentNode) {
        console.log('ShowAddModal called for parent:', parentNode);
        
        // Determine what type of node can be added based on parent
        if (!parentNode || parentNode.type === 'root') {
            // Root level or Product Catalogs node - can add catalog
            this.showAddCatalogModal(parentNode);
        } else if (parentNode.type === 'catalog') {
            // Under catalog - can add category
            this.showAddCategoryModal(parentNode);
        } else if (parentNode.type === 'category' || parentNode.type === 'subcategory') {
            // Under category - can add subcategory or product
            this.showAddOptionsModal(parentNode);
        } else if (parentNode.type === 'product') {
            // Under product - can add component
            this.showAddComponentModal(parentNode);
        }
    }

    /**
     * Show the Add Catalog modal
     * @param {Object} parentNode - The parent node (should be root)
     */
    showAddCatalogModal(parentNode) {
        const modal = document.getElementById('add-catalog-modal');
        if (!modal) {
            console.error('Add Catalog modal not found');
            return;
        }

        // Reset form
        const form = document.getElementById('add-catalog-form');
        form.reset();
        
        // Clear any previous errors
        this.clearFormErrors('add-catalog-form');
        
        // Store parent reference
        this.currentParentNode = parentNode;
        
        // Set up event handlers for auto-generation and validation
        this.setupCatalogFormHandlers();
        
        // Show modal - it's already a flex container
        modal.style.display = 'flex';
        
        // Focus on name field
        setTimeout(() => {
            document.getElementById('catalog-name').focus();
        }, 100);
        
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Set up event handlers for catalog form
     */
    setupCatalogFormHandlers() {
        const nameField = document.getElementById('catalog-name');
        const codeField = document.getElementById('catalog-code');
        const startDateField = document.getElementById('catalog-effective-start-date');
        const endDateField = document.getElementById('catalog-effective-end-date');
        
        // Auto-generate code from name if code is empty
        if (nameField && codeField) {
            nameField.addEventListener('input', () => {
                if (!codeField.value || codeField.value === this.lastGeneratedCode) {
                    // Generate code by replacing spaces with underscores and removing special chars
                    const generatedCode = nameField.value
                        .replace(/[^a-zA-Z0-9\s_-]/g, '') // Remove special chars except space, underscore, hyphen
                        .replace(/\s+/g, '_') // Replace spaces with underscores
                        .toUpperCase(); // Convert to uppercase
                    codeField.value = generatedCode;
                    this.lastGeneratedCode = generatedCode;
                }
            });
            
            // Validate code field - only allow alphanumeric and underscore
            codeField.addEventListener('input', () => {
                codeField.value = codeField.value.replace(/[^a-zA-Z0-9_]/g, '');
            });
        }
        
        // Date validation
        if (startDateField && endDateField) {
            const validateDates = () => {
                if (startDateField.value && endDateField.value) {
                    const startDate = new Date(startDateField.value);
                    const endDate = new Date(endDateField.value);
                    
                    if (endDate < startDate) {
                        this.showFieldError('catalog-effective-end-date', 'End date cannot be before start date');
                        return false;
                    } else {
                        // Clear error if dates are valid
                        const errorElem = document.getElementById('catalog-effective-end-date-error');
                        if (errorElem) errorElem.textContent = '';
                        endDateField.classList.remove('error');
                        return true;
                    }
                }
                return true;
            };
            
            startDateField.addEventListener('change', validateDates);
            endDateField.addEventListener('change', validateDates);
        }
    }

    /**
     * Show Add Category modal
     * @param {Object} parentNode - The parent node (catalog or category)
     */
    showAddCategoryModal(parentNode) {
        console.log('ShowAddCategoryModal called for parent:', parentNode);
        
        // Store parent info
        this.currentParentNode = parentNode;
        
        // Create modal if it doesn't exist
        if (!document.getElementById('add-category-modal')) {
            this.createAddCategoryModal();
        }
        
        // Update parent context in modal
        const parentInfo = document.querySelector('#add-category-modal .parent-info');
        if (parentInfo) {
            const parentType = parentNode.type === 'catalog' ? 'Catalog' : 'Category';
            parentInfo.innerHTML = `<p>Adding to ${parentType}: <strong>${parentNode.name}</strong></p>`;
        }
        
        // Reset form
        const form = document.getElementById('add-category-form');
        if (form) {
            form.reset();
            // Clear any previous error messages
            const errorMessages = form.querySelectorAll('.error-message');
            errorMessages.forEach(err => {
                err.textContent = '';
                err.style.display = 'none';
            });
        }
        
        // Show modal
        const modal = document.getElementById('add-category-modal');
        modal.style.display = 'flex';
        
        // Focus on name field
        setTimeout(() => {
            const nameField = document.getElementById('category-name');
            if (nameField) {
                nameField.focus();
            }
        }, 100);
    }

    /**
     * Show options modal for adding subcategory or product (placeholder)
     */
    showAddOptionsModal(parentNode) {
        console.log('Add Options modal not yet implemented');
        // TODO: Implement when extending to subcategories/products
    }

    /**
     * Show Add Component modal (placeholder)
     */
    showAddComponentModal(parentNode) {
        console.log('Add Component modal not yet implemented');
        // TODO: Implement when extending to components
    }

    /**
     * Close a modal
     * @param {string} modalId - The ID of the modal to close
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            // Restore body scroll
            document.body.style.overflow = '';
            
            // Clean up ESC handler if it exists
            if (modal.escHandler) {
                document.removeEventListener('keydown', modal.escHandler);
            }
        }
    }

    /**
     * Clear all error messages in a form
     * @param {string} formId - The ID of the form
     */
    clearFormErrors(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.querySelectorAll('.error-message').forEach(elem => {
                elem.textContent = '';
            });
            form.querySelectorAll('.form-control').forEach(elem => {
                elem.classList.remove('error');
            });
        }
    }

    /**
     * Validate the Add Catalog form
     * @returns {Object|null} Validated data or null if invalid
     */
    validateAddCatalogForm() {
        const name = document.getElementById('catalog-name').value.trim();
        const code = document.getElementById('catalog-code').value.trim();
        const description = document.getElementById('catalog-description').value.trim();
        const catalogType = document.getElementById('catalog-type').value;
        const effectiveStartDate = document.getElementById('catalog-effective-start-date').value;
        const effectiveEndDate = document.getElementById('catalog-effective-end-date').value;
        const isActive = document.getElementById('catalog-active').checked;
        
        // Clear previous errors
        this.clearFormErrors('add-catalog-form');
        
        let isValid = true;
        
        // Validate name
        if (!name) {
            this.showFieldError('catalog-name', 'Name is required');
            isValid = false;
        } else if (name.length > 255) {
            this.showFieldError('catalog-name', 'Name must be 255 characters or less');
            isValid = false;
        }
        
        // Validate code (if provided)
        if (code && code.length > 255) {
            this.showFieldError('catalog-code', 'Code must be 255 characters or less');
            isValid = false;
        }
        
        // Validate description
        if (description.length > 1000) {
            this.showFieldError('catalog-description', 'Description must be 1000 characters or less');
            isValid = false;
        }
        
        // Validate dates
        if (effectiveStartDate && effectiveEndDate) {
            const startDate = new Date(effectiveStartDate);
            const endDate = new Date(effectiveEndDate);
            
            if (endDate < startDate) {
                this.showFieldError('catalog-effective-end-date', 'End date cannot be before start date');
                isValid = false;
            }
        }
        
        if (!isValid) {
            return null;
        }
        
        // Auto-generate code if not provided
        const finalCode = code || name.replace(/[^a-zA-Z0-9\s_-]/g, '').replace(/\s+/g, '_').toUpperCase();
        
        return {
            name,
            code: finalCode,
            description,
            catalogType,
            effectiveStartDate,
            effectiveEndDate,
            isActive
        };
    }

    /**
     * Show an error message for a specific field
     * @param {string} fieldId - The ID of the field
     * @param {string} message - The error message
     */
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const errorElem = document.getElementById(fieldId + '-error');
        
        if (field) {
            field.classList.add('error');
        }
        if (errorElem) {
            errorElem.textContent = message;
        }
    }

    /**
     * Submit the Add Category form
     */
    async submitAddCategory() {
        console.log('Submitting Add Category form');
        
        // Validate form
        const nameInput = document.getElementById('category-name');
        if (!nameInput || !nameInput.value.trim()) {
            this.showFieldError('category-name', 'Name is required');
            return;
        }
        
        const categoryName = nameInput.value.trim();
        
        // Validate name length
        if (categoryName.length > 255) {
            this.showFieldError('category-name', 'Name must be 255 characters or less');
            return;
        }
        
        // Clear any previous errors
        this.clearFormErrors('add-category-form');
        
        // Generate temporary ID
        const tempId = this.generateTempId('category');
        
        // Create new category data
        const newCategory = {
            id: tempId,
            nodeId: tempId,
            name: categoryName,
            type: 'category',
            parentType: this.currentParentNode.type,
            parentId: this.currentParentNode.id,
            // Only set ParentCategoryId if parent is a category
            parentCategoryId: (this.currentParentNode.type === 'category' || this.currentParentNode.type === 'subcategory') 
                ? this.currentParentNode.id : null,
            children: [],
            isNew: true,  // Flag to indicate this is a newly added node
            isSynced: false,
            tempId: tempId,
            timestamp: new Date().toISOString()
        };
        
        // Add to hierarchy and track change
        if (window.changeTracker) {
            // Track the addition
            window.changeTracker.trackAddition(tempId, newCategory);
            
            // Update the visualization
            if (window.hierarchyVisualization && window.hierarchyVisualization.addNode) {
                window.hierarchyVisualization.addNode(newCategory, this.currentParentNode);
            } else {
                console.error('Hierarchy visualization not ready for adding nodes');
            }
        }
        
        // Close modal
        this.closeModal('add-category-modal');
        
        // Show success message
        console.log('Category staged for addition:', newCategory);
        
        // Show toast notification if available
        if (window.showToast) {
            window.showToast(`Category "${categoryName}" added successfully`, 'success');
        }
    }

    /**
     * Submit the Add Catalog form
     */
    async submitAddCatalog() {
        console.log('Submitting Add Catalog form');
        
        // Validate form
        const formData = this.validateAddCatalogForm();
        if (!formData) {
            return;
        }
        
        // Generate temporary ID
        const tempId = this.generateTempId('catalog');
        
        // Create new node data
        const newNode = {
            id: tempId,
            name: formData.name,
            code: formData.code,
            description: formData.description,
            catalogType: formData.catalogType,
            effectiveStartDate: formData.effectiveStartDate,
            effectiveEndDate: formData.effectiveEndDate,
            isActive: formData.isActive,
            type: 'catalog',
            children: [],
            isNew: true,  // Flag to indicate this is a newly added node
            isSynced: false
        };
        
        // Add to hierarchy and track change
        if (window.changeTracker) {
            // Track the addition
            window.changeTracker.trackAddition(tempId, newNode);
            
            // Update the visualization
            if (window.hierarchyVisualization && window.hierarchyVisualization.addNode) {
                window.hierarchyVisualization.addNode(newNode, this.currentParentNode);
            } else {
                console.error('Hierarchy visualization not ready for adding nodes');
            }
        }
        
        // Close modal
        this.closeModal('add-catalog-modal');
        
        // Show success message (optional)
        console.log('Catalog staged for addition:', newNode);
    }

    /**
     * Generate a temporary ID for a new node
     * @param {string} type - The type of node (catalog, category, product, component)
     * @returns {string} The temporary ID
     */
    generateTempId(type) {
        this.tempIdCounter[type]++;
        return `temp_${type}_${this.tempIdCounter[type]}`;
    }

    /**
     * Handle the add icon click from the visualization
     * @param {Object} d3Node - The D3 node data
     */
    handleAddClick(d3Node) {
        console.log('Add icon clicked for node:', d3Node);
        
        // Convert D3 node to our expected format
        const parentNode = d3Node.data || d3Node;
        
        // Show appropriate modal
        this.showAddModal(parentNode);
    }
}

// Create global instance
window.addNodeManager = new AddNodeManager();