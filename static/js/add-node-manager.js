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
        if (!document.getElementById('add-category-modal')) {
            this.createAddCategoryModal();
        }
        if (!document.getElementById('add-product-modal')) {
            this.createAddProductModal();
        }
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
                        font-family: inherit;
                    }
                    
                    .modal-overlay textarea.form-control {
                        resize: vertical;
                        min-height: 60px;
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
                        <button class="modal-close" id="add-category-close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="add-category-form" onsubmit="return false;">
                            <!-- Required Fields Section -->
                            <div class="form-group">
                                <label for="category-name">Name <span class="required">*</span></label>
                                <input type="text" id="category-name" name="name" class="form-control" required maxlength="255">
                                <div class="error-message" id="category-name-error"></div>
                            </div>
                            
                            <div class="form-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="category-is-navigational" name="isNavigational" checked>
                                    <span>Show In Menu</span>
                                </label>
                                <small style="color: #666; display: block; margin-top: 4px;">Display this category in navigation menus</small>
                            </div>
                            
                            <!-- Optional Fields Section -->
                            <hr style="margin: 20px 0; border: none; border-top: 1px solid #e8e8e8;">
                            <h4 style="font-size: 14px; margin-bottom: 16px; color: #666;">Optional Fields</h4>
                            
                            <div class="form-group">
                                <label for="category-description">Description</label>
                                <textarea id="category-description" name="description" class="form-control" rows="3" maxlength="255" placeholder="Brief description of this category"></textarea>
                                <small style="color: #999; display: block; margin-top: 4px;">Maximum 255 characters</small>
                                <div class="error-message" id="category-description-error"></div>
                            </div>
                            
                            <div class="form-group">
                                <label for="category-sort-order">Sort Order</label>
                                <input type="number" id="category-sort-order" name="sortOrder" class="form-control" min="0" placeholder="Display order (e.g., 1, 2, 3)">
                                <small style="color: #999; display: block; margin-top: 4px;">Categories are sorted by this value in ascending order</small>
                                <div class="error-message" id="category-sort-order-error"></div>
                            </div>
                            
                            <div class="form-group">
                                <label for="category-code">Code</label>
                                <input type="text" id="category-code" name="code" class="form-control" maxlength="255" placeholder="Unique identifier code">
                                <small style="color: #999; display: block; margin-top: 4px;">Optional unique code for this category</small>
                                <div class="error-message" id="category-code-error"></div>
                            </div>
                            
                            <div class="form-group">
                                <label for="category-external-id">External ID</label>
                                <input type="text" id="category-external-id" name="externalId" class="form-control" maxlength="20" placeholder="External system reference">
                                <small style="color: #999; display: block; margin-top: 4px;">ID from external system (max 20 characters)</small>
                                <div class="error-message" id="category-external-id-error"></div>
                            </div>
                            
                            <div class="parent-info" style="margin-top: 20px; padding: 12px; background-color: #f5f5f5; border-radius: 4px;">
                                <!-- Parent context will be inserted here dynamically -->
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="add-category-cancel-btn">Cancel</button>
                        <button class="btn btn-primary" id="add-category-submit-btn">
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
        
        // Don't attach event listeners here - they will be attached in attachCategoryModalEventListeners
        // This prevents duplicate event listeners
        
        // Add ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                this.closeModal('add-category-modal');
            }
        };
        document.addEventListener('keydown', escHandler);
        
        // Store handler for cleanup
        modal.escHandler = escHandler;
        
        // Attach event listeners
        this.attachCategoryModalEventListeners();
    }
    
    /**
     * Attach event listeners to the Add Category modal
     */
    attachCategoryModalEventListeners() {
        console.log('[ADD CATEGORY] Attaching event listeners');
        
        // Store reference to this for use in event handlers
        const self = this;
        
        // Attach click handler to Add button
        const addButton = document.getElementById('add-category-submit-btn');
        if (addButton) {
            // Remove any existing listeners to avoid duplicates
            const newButton = addButton.cloneNode(true);
            addButton.parentNode.replaceChild(newButton, addButton);
            
            // Add new listener
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('[BUTTON CLICK] Add Category button clicked');
                self.submitAddCategory();
            });
            console.log('[ADD CATEGORY] Add button listener attached');
        } else {
            console.error('[ADD CATEGORY] Add button not found');
        }
        
        // Attach click handler to Cancel button
        const cancelButton = document.getElementById('add-category-cancel-btn');
        if (cancelButton) {
            const newCancelButton = cancelButton.cloneNode(true);
            cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
            
            newCancelButton.addEventListener('click', function(e) {
                e.preventDefault();
                self.closeModal('add-category-modal');
            });
        }
        
        // Attach click handler to Close (X) button
        const closeButton = document.getElementById('add-category-close-btn');
        if (closeButton) {
            const newCloseButton = closeButton.cloneNode(true);
            closeButton.parentNode.replaceChild(newCloseButton, closeButton);
            
            newCloseButton.addEventListener('click', function(e) {
                e.preventDefault();
                self.closeModal('add-category-modal');
            });
        }
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
            // For now, we'll add products to categories
            this.showAddProductModal(parentNode);
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
            // Attach event listeners only when creating the modal for the first time
            this.attachCategoryModalEventListeners();
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
            
            // Reset checkbox to default checked state
            const isNavigationalCheckbox = document.getElementById('category-is-navigational');
            if (isNavigationalCheckbox) {
                isNavigationalCheckbox.checked = true;  // Default to checked as per requirement
            }
            
            // Clear all form fields explicitly
            const fieldsToReset = [
                'category-name',
                'category-description',
                'category-sort-order',
                'category-code',
                'category-external-id'
            ];
            
            fieldsToReset.forEach(fieldId => {
                const field = document.getElementById(fieldId);
                if (field) {
                    field.value = '';
                    field.classList.remove('error');
                }
            });
            
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
     * Find the catalog ID by traversing up the hierarchy
     */
    findCatalogId(node) {
        console.log('[ADD CATEGORY] Finding catalog ID for node:', node);
        
        // If this is a catalog, return its ID
        if (node.type === 'catalog') {
            console.log('[ADD CATEGORY] Node is a catalog, returning ID:', node.id);
            return node.id;
        }
        
        // If node has catalogId property, use it directly
        if (node.catalogId) {
            console.log('[ADD CATEGORY] Node has catalogId property:', node.catalogId);
            return node.catalogId;
        }
        
        // If we have a parent ID, look up the parent node
        if (node.parentId) {
            console.log('[ADD CATEGORY] Node has parentId:', node.parentId);
            
            // Check if hierarchyData is available
            if (!window.hierarchyData) {
                console.warn('[ADD CATEGORY] window.hierarchyData not available, trying alternative approach');
                // If parent node is stored in our instance, use it
                if (this.currentParentNode && this.currentParentNode.type === 'catalog') {
                    return this.currentParentNode.id;
                }
                return null;
            }
            
            // Search through the hierarchy to find the parent
            const findNodeById = (searchNode, targetId) => {
                if (searchNode.id === targetId) {
                    return searchNode;
                }
                if (searchNode.children) {
                    for (const child of searchNode.children) {
                        const found = findNodeById(child, targetId);
                        if (found) return found;
                    }
                }
                return null;
            };
            
            const parent = findNodeById(window.hierarchyData, node.parentId);
            if (parent) {
                return this.findCatalogId(parent);
            }
        }
        
        // If we can't find a catalog, log error
        console.error('[ADD CATEGORY] Could not find catalog ID for node:', node);
        return null;
    }

    /**
     * Submit the Add Category form
     */
    async submitAddCategory() {
        try {
            console.log('[ADD CATEGORY] Starting submission...');
            console.log('[ADD CATEGORY] Current parent node:', this.currentParentNode);
            
            // Check if parent node is set
            if (!this.currentParentNode) {
                throw new Error('No parent node selected. Please try opening the modal again.');
            }
        
            // Get form values
            const nameInput = document.getElementById('category-name');
            const isNavigationalInput = document.getElementById('category-is-navigational');
            const descriptionInput = document.getElementById('category-description');
            const sortOrderInput = document.getElementById('category-sort-order');
            const codeInput = document.getElementById('category-code');
            const externalIdInput = document.getElementById('category-external-id');
            
            // Validate required fields
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
            
            // Validate optional fields
            let isValid = true;
            
            // Validate description
            const description = descriptionInput ? descriptionInput.value.trim() : '';
            if (description.length > 255) {
                this.showFieldError('category-description', 'Description must be 255 characters or less');
                isValid = false;
            }
            
            // Validate sort order (must be a positive integer if provided)
            const sortOrderValue = sortOrderInput ? sortOrderInput.value.trim() : '';
            let sortOrder = null;
            if (sortOrderValue) {
                sortOrder = parseInt(sortOrderValue, 10);
                if (isNaN(sortOrder) || sortOrder < 0) {
                    this.showFieldError('category-sort-order', 'Sort order must be a positive number');
                    isValid = false;
                }
            }
            
            // Validate code
            const code = codeInput ? codeInput.value.trim() : '';
            if (code.length > 255) {
                this.showFieldError('category-code', 'Code must be 255 characters or less');
                isValid = false;
            }
            
            // Validate external ID
            const externalId = externalIdInput ? externalIdInput.value.trim() : '';
            if (externalId.length > 20) {
                this.showFieldError('category-external-id', 'External ID must be 20 characters or less');
                isValid = false;
            }
            
            if (!isValid) {
                return;
            }
            
            // Find the catalog ID
            console.log('[ADD CATEGORY] Attempting to find catalog ID...');
            const catalogId = this.findCatalogId(this.currentParentNode);
            console.log('[ADD CATEGORY] findCatalogId returned:', catalogId);
            
            if (!catalogId) {
                console.error('[ADD CATEGORY] Cannot create category without catalog ID');
                console.log('[ADD CATEGORY] Parent node details:', JSON.stringify(this.currentParentNode, null, 2));
                this.showFieldError('category-name', 'Unable to determine catalog for this category');
                return;
            }
            console.log('[ADD CATEGORY] Found catalog ID:', catalogId);
            
            // Generate temporary ID
            const tempId = this.generateTempId('category');
            
            // Create new category data with all fields
            const newCategory = {
                id: tempId,
                nodeId: tempId,
                name: categoryName,
                type: 'category',
                parentType: this.currentParentNode.type,
                parentId: this.currentParentNode.id,
                catalogId: catalogId,
                // Only set ParentCategoryId if parent is a category
                parentCategoryId: (this.currentParentNode.type === 'category' || this.currentParentNode.type === 'subcategory') 
                    ? this.currentParentNode.id : null,
                // Add new fields
                isNavigational: isNavigationalInput ? isNavigationalInput.checked : false,
                description: description || null,
                sortOrder: sortOrder,
                code: code || null,
                externalId__c: externalId || null,
                children: [],
                isNew: true,  // Flag to indicate this is a newly added node
                isSynced: false,
                tempId: tempId,
                timestamp: new Date().toISOString()
            };
            
            console.log('[ADD CATEGORY] New category data with all fields:', newCategory);
            
            // Add to hierarchy and track change
            if (window.changeTracker) {
                console.log('[ADD CATEGORY] Tracking addition with changeTracker');
                // Track the addition
                window.changeTracker.trackAddition(tempId, newCategory);
                console.log('[ADD CATEGORY] Addition tracked successfully');
                
                // Update the visualization
                if (window.hierarchyVisualization && window.hierarchyVisualization.addNode) {
                    console.log('[ADD CATEGORY] Updating visualization');
                    window.hierarchyVisualization.addNode(newCategory, this.currentParentNode);
                    console.log('[ADD CATEGORY] Visualization updated');
                } else {
                    console.warn('[ADD CATEGORY] Hierarchy visualization not ready for adding nodes - this is OK if testing');
                }
            } else {
                console.warn('[ADD CATEGORY] ChangeTracker not available - this is OK if testing');
                console.log('[ADD CATEGORY] New category data:', newCategory);
                
                // For testing purposes, we can still close the modal and show success
                console.log('[ADD CATEGORY] Would have added category:', categoryName);
            }
            
            // Close modal
            this.closeModal('add-category-modal');
            
            // Show success message
            console.log('Category staged for addition:', newCategory);
            
            // Show toast notification if available
            if (window.showToast) {
                window.showToast(`Category "${categoryName}" added successfully`, 'success');
            }
        
        } catch (error) {
            console.error('[ADD CATEGORY] Error during submission:', error);
            console.error('[ADD CATEGORY] Stack trace:', error.stack);
            
            // Show error to user
            if (window.showToast) {
                window.showToast('Error adding category: ' + error.message, 'error');
            } else {
                alert('Error adding category: ' + error.message);
            }
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
     * Create the Add Product modal HTML
     */
    createAddProductModal() {
        const modalHtml = `
            <div id="add-product-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>
                            <i class="anticon">
                                <svg viewBox="64 64 896 896" width="20" height="20" fill="currentColor">
                                    <path d="M924.8 625.7l-65.5-56c3.1-19 4.7-38.4 4.7-57.8s-1.6-38.8-4.7-57.8l65.5-56a32.03 32.03 0 009.3-35.2l-.9-2.6a443.74 443.74 0 00-79.7-137.9l-1.8-2.1a32.12 32.12 0 00-35.1-9.5l-81.3 28.9c-30-24.6-63.5-44-99.7-57.6l-15.7-85a32.05 32.05 0 00-25.8-25.7l-2.7-.5c-52.1-9.4-106.9-9.4-159 0l-2.7.5a32.05 32.05 0 00-25.8 25.7l-15.8 85.4a351.86 351.86 0 00-99 57.4l-81.9-29.1a32 32 0 00-35.1 9.5l-1.8 2.1a446.02 446.02 0 00-79.7 137.9l-.9 2.6c-4.5 12.5-.8 26.5 9.3 35.2l66.3 56.6c-3.1 18.8-4.6 38-4.6 57.1 0 19.2 1.5 38.4 4.6 57.1L99 625.5a32.03 32.03 0 00-9.3 35.2l.9 2.6c18.1 50.4 44.9 96.9 79.7 137.9l1.8 2.1a32.12 32.12 0 0035.1 9.5l81.9-29.1c29.8 24.5 63.1 43.9 99 57.4l15.8 85.4a32.05 32.05 0 0025.8 25.7l2.7.5a449.4 449.4 0 00159 0l2.7-.5a32.05 32.05 0 0025.8-25.7l15.7-85a350 350 0 0099.7-57.6l81.3 28.9a32 32 0 0035.1-9.5l1.8-2.1c34.8-41.1 61.6-87.5 79.7-137.9l.9-2.6c4.5-12.3.8-26.3-9.3-35zM788.3 465.9c2.5 15.1 3.8 30.6 3.8 46.1s-1.3 31-3.8 46.1l-6.6 40.1 74.7 63.9a370.03 370.03 0 01-42.6 73.6L721 702.8l-31.4 25.8c-23.9 19.6-50.5 35-79.3 45.8l-38.1 14.3-17.9 97a377.5 377.5 0 01-85 0l-17.9-97.2-37.8-14.5c-28.5-10.8-55-26.2-78.7-45.7l-31.4-25.9-93.4 33.2c-17-22.9-31.2-47.6-42.6-73.6l75.5-64.5-6.5-40c-2.4-14.9-3.7-30.3-3.7-45.5 0-15.3 1.2-30.6 3.7-45.5l6.5-40-75.5-64.5c11.3-26.1 25.6-50.7 42.6-73.6l93.4 33.2 31.4-25.9c23.7-19.5 50.2-34.9 78.7-45.7l37.9-14.3 17.9-97.2c28.1-3.2 56.8-3.2 85 0l17.9 97 38.1 14.3c28.7 10.8 55.4 26.2 79.3 45.8l31.4 25.8 92.8-32.9c17 22.9 31.2 47.6 42.6 73.6L781.8 426l6.5 39.9zM512 326c-97.2 0-176 78.8-176 176s78.8 176 176 176 176-78.8 176-176-78.8-176-176-176zm79.2 255.2A111.6 111.6 0 01512 614c-29.9 0-58-11.7-79.2-32.8A111.6 111.6 0 01400 502c0-29.9 11.7-58 32.8-79.2C454 401.6 482.1 390 512 390c29.9 0 58 11.6 79.2 32.8A111.6 111.6 0 01624 502c0 29.9-11.7 58-32.8 79.2z"/>
                                </svg>
                            </i>
                            Add Product
                        </h3>
                        <button class="modal-close" aria-label="Close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="add-product-form">
                            <div class="parent-info">
                                Adding product to: <strong class="parent-name"></strong>
                            </div>
                            
                            <section class="form-section">
                                <h4>Required Information</h4>
                                
                                <div class="form-group">
                                    <label for="product-name">Name <span class="required">*</span></label>
                                    <input type="text" id="product-name" name="name" required maxlength="255">
                                    <div class="help-text">Product display name (max 255 characters)</div>
                                    <div class="error-message" style="display: none;"></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="product-code">Product Code <span class="required">*</span></label>
                                    <input type="text" id="product-code" name="productCode" required maxlength="255">
                                    <div class="help-text">Unique product identifier (auto-generated from name)</div>
                                    <div class="error-message" style="display: none;"></div>
                                </div>
                            </section>
                            
                            <section class="form-section">
                                <h4>Optional Information</h4>
                                
                                <div class="form-group">
                                    <label for="product-description">Description</label>
                                    <textarea id="product-description" name="description" maxlength="4000" rows="3"></textarea>
                                    <div class="help-text">Product description (max 4000 characters)</div>
                                    <div class="error-message" style="display: none;"></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="product-sku">Stock Keeping Unit (SKU)</label>
                                    <input type="text" id="product-sku" name="stockKeepingUnit" maxlength="180">
                                    <div class="help-text">SKU for inventory tracking (auto-generated)</div>
                                    <div class="error-message" style="display: none;"></div>
                                </div>
                                
                                <div class="form-group">
                                    <label for="product-family">Product Family</label>
                                    <input type="text" id="product-family" name="family" maxlength="40">
                                    <div class="help-text">Product family for grouping</div>
                                    <div class="error-message" style="display: none;"></div>
                                </div>
                                
                                <div class="form-group checkbox-group">
                                    <label>
                                        <input type="checkbox" id="product-is-active" name="isActive" checked>
                                        <span>Is Active</span>
                                    </label>
                                    <div class="help-text">Product is available for selection</div>
                                </div>
                            </section>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" id="add-product-cancel">Cancel</button>
                        <button type="button" class="btn btn-primary" id="add-product-submit">Add Product</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to the document
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add click handler to close modal when clicking overlay
        const modal = document.getElementById('add-product-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal('add-product-modal');
            }
        });
        
        // Add ESC key handler
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                this.closeModal('add-product-modal');
            }
        });
    }
    
    /**
     * Show the Add Product modal
     * @param {Object} parentNode - The parent category node
     */
    showAddProductModal(parentNode) {
        console.log('[ADD PRODUCT] showAddProductModal called for parent:', parentNode);
        
        // Create modal if it doesn't exist
        if (!document.getElementById('add-product-modal')) {
            this.createAddProductModal();
            // Attach event listeners only when creating the modal for the first time
            this.attachProductModalEventListeners();
        }
        
        // Update parent context in modal
        const parentInfo = document.querySelector('#add-product-modal .parent-info');
        if (parentInfo) {
            const parentName = parentInfo.querySelector('.parent-name');
            if (parentName) {
                parentName.textContent = parentNode.name;
            }
        }
        
        // Reset form
        const form = document.getElementById('add-product-form');
        form.reset();
        
        // Clear any previous errors
        this.clearFormErrors('add-product-form');
        
        // Store parent reference
        this.currentParentNode = parentNode;
        
        // Set up event handlers for auto-generation and validation
        this.setupProductFormHandlers();
        
        // Ensure button event listeners are attached
        this.attachProductModalEventListeners();
        
        // Show modal
        const modal = document.getElementById('add-product-modal');
        modal.style.display = 'flex';
        
        // Focus on name field
        setTimeout(() => {
            document.getElementById('product-name').focus();
        }, 100);
        
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Set up event handlers for product form
     */
    setupProductFormHandlers() {
        const nameField = document.getElementById('product-name');
        const codeField = document.getElementById('product-code');
        const skuField = document.getElementById('product-sku');
        
        // Auto-generate product code from name if code is empty
        if (nameField && codeField) {
            nameField.addEventListener('input', () => {
                if (!codeField.value || codeField.dataset.autoGenerated === 'true') {
                    // Generate code: uppercase, replace spaces and special chars with underscores
                    const generatedCode = nameField.value
                        .toUpperCase()
                        .replace(/[^A-Z0-9]/g, '_')
                        .replace(/_+/g, '_')
                        .replace(/^_|_$/g, '');
                    codeField.value = generatedCode;
                    codeField.dataset.autoGenerated = 'true';
                }
            });
            
            // Mark as manually edited if user types in code field
            codeField.addEventListener('input', () => {
                if (codeField.value) {
                    codeField.dataset.autoGenerated = 'false';
                }
            });
        }
        
        // Auto-generate SKU from product code
        if (codeField && skuField) {
            const updateSKU = () => {
                if (!skuField.value || skuField.dataset.autoGenerated === 'true') {
                    if (codeField.value) {
                        skuField.value = `SKU-${codeField.value}`;
                        skuField.dataset.autoGenerated = 'true';
                    }
                }
            };
            
            codeField.addEventListener('input', updateSKU);
            nameField.addEventListener('input', () => {
                setTimeout(updateSKU, 10); // Small delay to let code update first
            });
            
            // Mark as manually edited if user types in SKU field
            skuField.addEventListener('input', () => {
                if (skuField.value) {
                    skuField.dataset.autoGenerated = 'false';
                }
            });
        }
        
        // Add validation handlers
        this.addProductFieldValidation();
    }
    
    /**
     * Add field validation for product form
     */
    addProductFieldValidation() {
        const form = document.getElementById('add-product-form');
        const inputs = form.querySelectorAll('input[type="text"], textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateProductField(input);
            });
        });
    }
    
    /**
     * Validate a product form field
     */
    validateProductField(field) {
        const errorDiv = field.parentElement.querySelector('.error-message');
        let isValid = true;
        let errorMessage = '';
        
        // Required field validation
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
            errorMessage = 'This field is required';
        }
        
        // Length validation
        if (field.value && field.hasAttribute('maxlength')) {
            const maxLength = parseInt(field.getAttribute('maxlength'));
            if (field.value.length > maxLength) {
                isValid = false;
                errorMessage = `Maximum ${maxLength} characters allowed`;
            }
        }
        
        // Show/hide error
        if (errorDiv) {
            if (!isValid) {
                errorDiv.textContent = errorMessage;
                errorDiv.style.display = 'block';
                field.classList.add('error');
            } else {
                errorDiv.style.display = 'none';
                field.classList.remove('error');
            }
        }
        
        return isValid;
    }
    
    /**
     * Attach event listeners to product modal buttons
     */
    attachProductModalEventListeners() {
        console.log('[ADD PRODUCT] Attaching modal event listeners');
        const self = this;
        
        // Cancel button
        const cancelButton = document.getElementById('add-product-cancel');
        if (cancelButton) {
            // Clone and replace to remove any existing listeners
            const newCancelButton = cancelButton.cloneNode(true);
            cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
            
            newCancelButton.addEventListener('click', function(e) {
                e.preventDefault();
                self.closeModal('add-product-modal');
            });
        }
        
        // Submit button
        const submitButton = document.getElementById('add-product-submit');
        if (submitButton) {
            console.log('[ADD PRODUCT] Found submit button, attaching event listener');
            // Clone and replace to remove any existing listeners
            const newSubmitButton = submitButton.cloneNode(true);
            submitButton.parentNode.replaceChild(newSubmitButton, submitButton);
            
            newSubmitButton.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('[ADD PRODUCT] Submit button event listener triggered');
                self.submitAddProduct();
            });
        } else {
            console.error('[ADD PRODUCT] Submit button not found!');
        }
        
        // Close button in header
        const closeButton = document.querySelector('#add-product-modal .modal-close');
        if (closeButton) {
            // Clone and replace to remove any existing listeners
            const newCloseButton = closeButton.cloneNode(true);
            closeButton.parentNode.replaceChild(newCloseButton, closeButton);
            
            newCloseButton.addEventListener('click', function(e) {
                e.preventDefault();
                self.closeModal('add-product-modal');
            });
        }
    }
    
    /**
     * Submit the Add Product form
     */
    submitAddProduct() {
        console.log('[ADD PRODUCT] Submit button clicked');
        
        const form = document.getElementById('add-product-form');
        const formData = new FormData(form);
        
        // Validate required fields
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!this.validateProductField(field)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            console.log('[ADD PRODUCT] Validation failed');
            return;
        }
        
        // Get parent category information
        const parentNode = this.currentParentNode;
        if (!parentNode) {
            console.error('[ADD PRODUCT] No parent node found');
            return;
        }
        
        // Generate a single temp ID for the product
        const tempId = this.generateTempId('product');
        
        // Create product data object
        const productData = {
            nodeId: tempId,
            type: 'product',
            name: formData.get('name'),
            description: formData.get('description') || '',
            productCode: formData.get('productCode'),
            stockKeepingUnit: formData.get('stockKeepingUnit') || '',
            family: formData.get('family') || '',
            isActive: form.querySelector('#product-is-active').checked,
            tempId: tempId,
            timestamp: new Date().toISOString(),
            
            // Parent category information
            categoryId: parentNode.id,
            parentId: parentNode.id,
            
            // We might need catalog ID for some operations
            catalogId: this.findCatalogId(parentNode)
        };
        
        console.log('[ADD PRODUCT] Product data:', productData);
        
        try {
            // Track the addition with ChangeTracker
            if (window.changeTracker) {
                window.changeTracker.trackAddition(productData);
                console.log('[ADD PRODUCT] Addition tracked successfully');
            } else {
                console.error('[ADD PRODUCT] ChangeTracker not available');
                return;
            }
            
            // Add the node to the visualization immediately
            const newNode = {
                id: productData.tempId,
                name: productData.name,
                type: 'product',
                isActive: productData.isActive,
                productCode: productData.productCode,
                description: productData.description,
                isSynced: false,
                isNew: true,
                children: []
            };
            
            // Update the visualization
            if (window.hierarchyVisualization && window.hierarchyVisualization.addNode) {
                console.log('[ADD PRODUCT] Updating visualization');
                window.hierarchyVisualization.addNode(newNode, parentNode);
                console.log('[ADD PRODUCT] Visualization updated');
            } else {
                console.warn('[ADD PRODUCT] Hierarchy visualization not ready for adding nodes - this is OK if testing');
            }
            
            // Close modal
            this.closeModal('add-product-modal');
            
            // Show success message
            console.log('[ADD PRODUCT] Product staged for addition:', newNode);
            
        } catch (error) {
            console.error('[ADD PRODUCT] Error during submission:', error);
            this.showFieldError('product-name', 'An error occurred while adding the product');
        }
    }
    
    /**
     * Find the catalog ID by traversing up the hierarchy
     */
    findCatalogId(node) {
        let current = node;
        while (current) {
            if (current.type === 'catalog') {
                return current.id;
            }
            // For D3 nodes, parent might be in the parent property
            current = current.parent ? (current.parent.data || current.parent) : null;
        }
        
        // If we can't find a catalog, check if catalogId is already in the node
        if (node.catalogId) {
            return node.catalogId;
        }
        
        console.warn('[ADD PRODUCT] Could not find catalog ID for node:', node);
        return null;
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