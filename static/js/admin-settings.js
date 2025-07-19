// Admin Settings JavaScript

let currentOrgId = null;
let currentPermissions = [];
let currentFields = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    loadConnections();
    checkAdminPermission();
});

// Check if user has admin permission
async function checkAdminPermission() {
    try {
        const response = await fetch('/api/edit/permissions');
        if (!response.ok) {
            window.location.href = '/';
            return;
        }
        
        const data = await response.json();
        if (data.permission_level !== 'admin') {
            alert('Admin permission required to access this page');
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error checking admin permission:', error);
        window.location.href = '/';
    }
}

// Initialize tabs
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show/hide content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Load tab data
            if (tabName === 'permissions') {
                loadPermissions();
            } else if (tabName === 'fields') {
                loadFieldConfig();
            } else if (tabName === 'audit') {
                loadAuditLog();
            }
        });
    });
}

// Load connections for org selector
async function loadConnections() {
    try {
        const response = await fetch('/api/connections');
        const data = await response.json();
        
        if (data.connections && data.connections.length > 0) {
            currentOrgId = data.active_connection_id || data.connections[0].id;
            
            // Create org selectors
            createOrgSelector('org-selector-permissions', data.connections, currentOrgId);
            createOrgSelector('org-selector-fields', data.connections, currentOrgId);
            
            // Load initial data
            loadPermissions();
        } else {
            showError('No organizations connected. Please connect to an organization first.');
        }
    } catch (error) {
        console.error('Error loading connections:', error);
        showError('Failed to load organizations');
    }
}

// Create org selector
function createOrgSelector(containerId, connections, activeId) {
    const container = document.getElementById(containerId);
    
    // Try to use Ant Design Select if available
    if (window.antd && window.React && window.ReactDOM) {
        const { Select } = window.antd;
        const { createElement } = window.React;
        
        const options = connections.map(conn => ({
            value: conn.id,
            label: conn.name || conn.username
        }));
        
        const handleChange = (value) => {
            currentOrgId = value;
            if (containerId === 'org-selector-permissions') {
                loadPermissions();
            } else {
                loadFieldConfig();
            }
        };
        
        ReactDOM.render(
            createElement(Select, {
                defaultValue: currentOrgId,
                value: currentOrgId,
                onChange: handleChange,
                options: options,
                style: { width: 300 }
            }),
            container
        );
    } else {
        // Fallback to native select
        const select = document.createElement('select');
        select.className = 'org-select';
        select.style.width = '300px';
        
        connections.forEach(conn => {
            const option = document.createElement('option');
            option.value = conn.id;
            option.textContent = conn.name || conn.username;
            if (conn.id === activeId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            currentOrgId = e.target.value;
            if (containerId === 'org-selector-permissions') {
                loadPermissions();
            } else {
                loadFieldConfig();
            }
        });
        
        container.appendChild(select);
    }
}

// Load permissions
async function loadPermissions() {
    const grid = document.getElementById('permissions-grid');
    grid.innerHTML = '<div class="loading">Loading permissions...</div>';
    
    try {
        const response = await fetch(`/api/edit/permissions?org_id=${currentOrgId}`);
        const userPermission = await response.json();
        
        // For now, show current user's permission
        // In a full implementation, we'd have an API to list all users
        currentPermissions = [{
            user_id: userPermission.user_id,
            permission_level: userPermission.permission_level,
            created_at: userPermission.created_at,
            updated_at: userPermission.updated_at
        }];
        
        renderPermissionsGrid();
    } catch (error) {
        console.error('Error loading permissions:', error);
        grid.innerHTML = '<div class="error">Failed to load permissions</div>';
    }
}

// Render permissions grid
function renderPermissionsGrid() {
    const grid = document.getElementById('permissions-grid');
    
    if (currentPermissions.length === 0) {
        grid.innerHTML = '<div class="empty">No permissions configured</div>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'permissions-table';
    
    table.innerHTML = `
        <thead>
            <tr>
                <th>User ID</th>
                <th>Permission Level</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${currentPermissions.map(perm => `
                <tr>
                    <td>${perm.user_id}</td>
                    <td><span class="permission-level ${perm.permission_level}">${formatPermissionLevel(perm.permission_level)}</span></td>
                    <td>${formatDate(perm.created_at)}</td>
                    <td>${formatDate(perm.updated_at)}</td>
                    <td>
                        <button class="btn btn-sm" onclick="editPermission('${perm.user_id}', '${perm.permission_level}')">Edit</button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    grid.innerHTML = '';
    grid.appendChild(table);
}

// Format permission level
function formatPermissionLevel(level) {
    const labels = {
        'view_only': 'View Only',
        'edit_basic': 'Edit Basic',
        'edit_structure': 'Edit Structure',
        'full_edit': 'Full Edit',
        'admin': 'Admin'
    };
    return labels[level] || level;
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Show add user dialog
function showAddUserDialog() {
    document.getElementById('add-user-dialog').style.display = 'flex';
}

// Close add user dialog
function closeAddUserDialog() {
    document.getElementById('add-user-dialog').style.display = 'none';
    document.getElementById('new-user-id').value = '';
    document.getElementById('new-permission-level').value = 'view_only';
}

// Add user permission
async function addUserPermission() {
    const userId = document.getElementById('new-user-id').value.trim();
    const permissionLevel = document.getElementById('new-permission-level').value;
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    try {
        const response = await fetch('/api/edit/permissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                org_id: currentOrgId,
                permission_level: permissionLevel
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to add permission');
            return;
        }
        
        closeAddUserDialog();
        loadPermissions();
    } catch (error) {
        console.error('Error adding permission:', error);
        alert('Failed to add permission');
    }
}

// Edit permission
function editPermission(userId, currentLevel) {
    document.getElementById('new-user-id').value = userId;
    document.getElementById('new-permission-level').value = currentLevel;
    showAddUserDialog();
}

// Refresh permissions
function refreshPermissions() {
    loadPermissions();
}

// Load field configuration
async function loadFieldConfig() {
    const container = document.getElementById('fields-config');
    container.innerHTML = '<div class="loading">Loading field configuration...</div>';
    
    const objectType = document.getElementById('object-type-selector').value;
    
    try {
        const response = await fetch(`/api/edit/field-config?org_id=${currentOrgId}&object_type=${objectType}`);
        const data = await response.json();
        
        currentFields = data.fields || [];
        renderFieldConfig();
    } catch (error) {
        console.error('Error loading field config:', error);
        container.innerHTML = '<div class="error">Failed to load field configuration</div>';
    }
}

// Render field configuration
function renderFieldConfig() {
    const container = document.getElementById('fields-config');
    
    if (currentFields.length === 0) {
        container.innerHTML = '<div class="empty">No fields configured</div>';
        return;
    }
    
    const fieldsHtml = currentFields.map((field, index) => `
        <div class="field-item" data-index="${index}">
            <input type="text" value="${field.field_label}" placeholder="Field Label" onchange="updateField(${index}, 'field_label', this.value)">
            <select onchange="updateField(${index}, 'field_type', this.value)">
                ${['text', 'textarea', 'number', 'checkbox', 'date', 'picklist', 'url', 'email'].map(type => 
                    `<option value="${type}" ${field.field_type === type ? 'selected' : ''}>${type}</option>`
                ).join('')}
            </select>
            <label>
                <input type="checkbox" ${field.is_editable ? 'checked' : ''} onchange="updateField(${index}, 'is_editable', this.checked)">
                Editable
            </label>
            <label>
                <input type="checkbox" ${field.required ? 'checked' : ''} onchange="updateField(${index}, 'required', this.checked)">
                Required
            </label>
            <select onchange="updateField(${index}, 'permission_level', this.value)">
                ${['edit_basic', 'edit_structure', 'full_edit', 'admin'].map(level => 
                    `<option value="${level}" ${field.permission_level === level ? 'selected' : ''}>${formatPermissionLevel(level)}</option>`
                ).join('')}
            </select>
            <span class="field-name">${field.field_name}</span>
        </div>
    `).join('');
    
    container.innerHTML = fieldsHtml;
}

// Update field
function updateField(index, property, value) {
    currentFields[index][property] = value;
}

// Save field configuration
async function saveFieldConfig() {
    const objectType = document.getElementById('object-type-selector').value;
    
    try {
        const response = await fetch('/api/edit/field-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                org_id: currentOrgId,
                object_type: objectType,
                fields: currentFields
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to save configuration');
            return;
        }
        
        alert('Field configuration saved successfully');
    } catch (error) {
        console.error('Error saving field config:', error);
        alert('Failed to save configuration');
    }
}

// Reset field configuration
function resetFieldConfig() {
    if (confirm('Are you sure you want to reset to default configuration?')) {
        loadFieldConfig();
    }
}

// Load audit log
async function loadAuditLog() {
    const container = document.getElementById('audit-log');
    container.innerHTML = '<div class="loading">Loading audit log...</div>';
    
    // In a full implementation, this would fetch from an audit log API
    container.innerHTML = '<div class="empty">Audit log coming soon</div>';
}

// Filter audit log
function filterAuditLog() {
    // Implementation for filtering audit log
    console.log('Filter audit log');
}

// Logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        fetch('/api/logout', { method: 'POST' })
            .then(() => {
                window.location.href = '/login';
            })
            .catch(error => {
                console.error('Error logging out:', error);
            });
    }
}

// Show error message
function showError(message) {
    alert(message);
}

// Object type selector change
document.getElementById('object-type-selector')?.addEventListener('change', loadFieldConfig);