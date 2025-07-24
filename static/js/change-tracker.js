/**
 * Change Tracker for Product Hierarchy Edits
 * Manages local state of all pending changes before commit
 */

class ChangeTracker {
    constructor() {
        this.pendingChanges = new Map(); // nodeId -> Map of field changes
        this.changeHistory = [];
        this.maxHistorySize = 50;
        this.historyIndex = -1;
        this.changeListeners = [];
        this.autoSaveTimer = null;
        this.autoSaveDelay = 5000; // 5 seconds
    }

    initialize() {
        // Load any persisted changes from session storage
        this.loadFromSession();
        
        // Set up auto-save
        this.setupAutoSave();
        
        // Add change summary button to UI
        this.addChangeSummaryButton();
        
        console.log('ChangeTracker initialized');
    }

    trackFieldChange(nodeId, nodeType, fieldName, oldValue, newValue) {
        // Alias for addChange with nodeType parameter
        this.addChange(nodeId, fieldName, oldValue, newValue);
    }
    
    addChange(nodeId, fieldName, oldValue, newValue) {
        // Create change object
        const change = {
            nodeId: nodeId,
            fieldName: fieldName,
            oldValue: oldValue,
            newValue: newValue,
            timestamp: new Date().toISOString(),
            id: this.generateChangeId()
        };
        
        // Get or create node changes map
        if (!this.pendingChanges.has(nodeId)) {
            this.pendingChanges.set(nodeId, new Map());
        }
        
        const nodeChanges = this.pendingChanges.get(nodeId);
        
        // If field was already changed, update old value to original
        if (nodeChanges.has(fieldName)) {
            const existingChange = nodeChanges.get(fieldName);
            change.oldValue = existingChange.oldValue;
        }
        
        // Store the change
        nodeChanges.set(fieldName, change);
        
        // Add to history for undo/redo
        this.addToHistory(change);
        
        // Notify listeners
        this.notifyListeners('change-added', change);
        
        // Update UI
        this.updateChangeSummaryBadge();
        
        // Reset auto-save timer
        this.resetAutoSave();
        
        // Save to session
        this.saveToSession();
    }

    getNodeChanges(nodeId) {
        return this.pendingChanges.get(nodeId) || new Map();
    }

    getNodeChangeCount(nodeId) {
        const nodeChanges = this.pendingChanges.get(nodeId);
        return nodeChanges ? nodeChanges.size : 0;
    }

    getTotalChangeCount() {
        let total = 0;
        this.pendingChanges.forEach(nodeChanges => {
            total += nodeChanges.size;
        });
        return total;
    }

    getAllChanges() {
        const allChanges = [];
        this.pendingChanges.forEach((nodeChanges, nodeId) => {
            nodeChanges.forEach(change => {
                allChanges.push(change);
            });
        });
        return allChanges;
    }

    discardNodeChanges(nodeId) {
        const nodeChanges = this.getNodeChanges(nodeId);
        
        // Restore original values
        nodeChanges.forEach((change, fieldName) => {
            const node = window.hierarchyData.nodes.find(n => n.id === nodeId);
            if (node) {
                node[fieldName] = change.oldValue;
            }
            
            // Update field display
            if (window.inlineEditor) {
                window.inlineEditor.updateFieldDisplay(nodeId, fieldName, change.oldValue);
            }
        });
        
        // Remove changes
        this.pendingChanges.delete(nodeId);
        
        // Update UI
        this.removeNodeModifiedIndicator(nodeId);
        this.updateChangeSummaryBadge();
        
        // Notify listeners
        this.notifyListeners('changes-discarded', { nodeId });
        
        // Save to session
        this.saveToSession();
    }

    discardAllChanges() {
        // Get all node IDs with changes
        const nodeIds = Array.from(this.pendingChanges.keys());
        
        // Discard each node's changes
        nodeIds.forEach(nodeId => {
            this.discardNodeChanges(nodeId);
        });
        
        // Clear history
        this.changeHistory = [];
        this.historyIndex = -1;
    }

    removeNodeModifiedIndicator(nodeId) {
        const nodeElement = d3.select(`[data-node-id="${nodeId}"]`);
        nodeElement.classed('node-modified', false);
        nodeElement.select('.node-modified-icon').remove();
    }
    
    addNodeModifiedIndicator(nodeId) {
        const nodeElement = d3.select(`[data-node-id="${nodeId}"]`);
        nodeElement.classed('node-modified', true);
        
        // Check if the indicator already exists
        if (!nodeElement.select('.node-modified-icon').empty()) {
            return;
        }
        
        // Add a visual indicator (e.g., a small icon or badge)
        const indicator = nodeElement.append('g')
            .attr('class', 'node-modified-icon')
            .attr('transform', d => {
                // Position in top-right corner of node
                const nodeWidth = 200; // Default node width
                return `translate(${nodeWidth / 2 - 15}, ${-15})`;
            });
        
        // Add a circle background
        indicator.append('circle')
            .attr('r', 8)
            .attr('fill', '#f0ad4e')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
        
        // Add an exclamation mark or pencil icon
        indicator.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .attr('fill', '#fff')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text('!');
    }

    generateChangeId() {
        return `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    addToHistory(change) {
        // Remove any changes after current index (for redo functionality)
        if (this.historyIndex < this.changeHistory.length - 1) {
            this.changeHistory = this.changeHistory.slice(0, this.historyIndex + 1);
        }
        
        // Add new change
        this.changeHistory.push({
            type: 'field-change',
            change: change
        });
        
        // Limit history size
        if (this.changeHistory.length > this.maxHistorySize) {
            this.changeHistory.shift();
        } else {
            this.historyIndex++;
        }
    }

    undo() {
        if (this.historyIndex < 0) return false;
        
        const historyItem = this.changeHistory[this.historyIndex];
        
        if (historyItem.type === 'field-change') {
            const change = historyItem.change;
            
            // Restore old value
            const node = window.hierarchyData.nodes.find(n => n.id === change.nodeId);
            if (node) {
                node[change.fieldName] = change.oldValue;
            }
            
            // Remove from pending changes
            const nodeChanges = this.pendingChanges.get(change.nodeId);
            if (nodeChanges) {
                nodeChanges.delete(change.fieldName);
                if (nodeChanges.size === 0) {
                    this.pendingChanges.delete(change.nodeId);
                    this.removeNodeModifiedIndicator(change.nodeId);
                }
            }
            
            // Update display
            if (window.inlineEditor) {
                window.inlineEditor.updateFieldDisplay(change.nodeId, change.fieldName, change.oldValue);
            }
        }
        
        this.historyIndex--;
        this.updateChangeSummaryBadge();
        this.saveToSession();
        
        return true;
    }

    redo() {
        if (this.historyIndex >= this.changeHistory.length - 1) return false;
        
        this.historyIndex++;
        const historyItem = this.changeHistory[this.historyIndex];
        
        if (historyItem.type === 'field-change') {
            const change = historyItem.change;
            
            // Re-apply change
            const node = window.hierarchyData.nodes.find(n => n.id === change.nodeId);
            if (node) {
                node[change.fieldName] = change.newValue;
            }
            
            // Add back to pending changes
            if (!this.pendingChanges.has(change.nodeId)) {
                this.pendingChanges.set(change.nodeId, new Map());
            }
            this.pendingChanges.get(change.nodeId).set(change.fieldName, change);
            
            // Update display
            if (window.inlineEditor) {
                window.inlineEditor.updateFieldDisplay(change.nodeId, change.fieldName, change.newValue);
                window.inlineEditor.markNodeAsModified(change.nodeId);
            }
        }
        
        this.updateChangeSummaryBadge();
        this.saveToSession();
        
        return true;
    }

    setupAutoSave() {
        // Auto-save changes to session storage
        this.autoSaveTimer = null;
    }

    resetAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.autoSaveTimer = setTimeout(() => {
            this.saveToSession();
            console.log('Changes auto-saved to session');
        }, this.autoSaveDelay);
    }

    saveToSession() {
        const data = {
            pendingChanges: Array.from(this.pendingChanges.entries()).map(([nodeId, changes]) => {
                return [nodeId, Array.from(changes.entries())];
            }),
            changeHistory: this.changeHistory,
            historyIndex: this.historyIndex,
            timestamp: new Date().toISOString()
        };
        
        sessionStorage.setItem('hierarchy-changes', JSON.stringify(data));
    }

    loadFromSession() {
        const saved = sessionStorage.getItem('hierarchy-changes');
        if (!saved) return;
        
        try {
            const data = JSON.parse(saved);
            
            // Restore pending changes
            this.pendingChanges.clear();
            data.pendingChanges.forEach(([nodeId, changes]) => {
                const nodeChanges = new Map(changes);
                this.pendingChanges.set(nodeId, nodeChanges);
            });
            
            // Restore history
            this.changeHistory = data.changeHistory || [];
            this.historyIndex = data.historyIndex || -1;
            
            // Update UI
            this.updateChangeSummaryBadge();
            
            console.log(`Restored ${this.getTotalChangeCount()} changes from session`);
        } catch (error) {
            console.error('Failed to restore changes from session:', error);
        }
    }

    applyRestoredChanges() {
        // Apply all pending changes to the loaded hierarchy data
        this.pendingChanges.forEach((nodeChanges, nodeId) => {
            nodeChanges.forEach((change, fieldName) => {
                // Apply to node data
                const node = window.hierarchyData.nodes.find(n => n.id === nodeId);
                if (node) {
                    node[fieldName] = change.newValue;
                }
                
                // Update D3 visualization
                const d3Node = window.hierarchyRoot.descendants().find(d => d.data.id === nodeId);
                if (d3Node) {
                    d3Node.data[fieldName] = change.newValue;
                    
                    // Update text element if it's the name field
                    if (fieldName === 'name') {
                        const nodeElement = d3.select(`[data-node-id="${nodeId}"]`);
                        const textElement = nodeElement.select('text');
                        if (!textElement.empty()) {
                            textElement.text(change.newValue);
                        }
                    }
                }
            });
            
            // Mark node as modified
            if (window.inlineEditor) {
                window.inlineEditor.markNodeAsModified(nodeId);
            }
        });
        
        // Ensure the button exists and update badge
        this.addChangeSummaryButton();
        this.updateChangeSummaryBadge();
        
        console.log('Applied restored changes to hierarchy');
    }

    addChangeSummaryButton() {
        // Add button to toolbar if not already present
        if (document.getElementById('change-summary-btn')) return;
        
        const toolbar = document.querySelector('.toolbar-right') || document.querySelector('.toolbar');
        if (!toolbar) return;
        
        const button = document.createElement('button');
        button.id = 'change-summary-btn';
        button.className = 'btn btn-primary change-summary-btn';
        button.innerHTML = `
            <span class="anticon">
                <svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor">
                    <path d="M854.6 288.6L639.4 73.4c-6-6-14.1-9.4-22.6-9.4H192c-17.7 0-32 14.3-32 32v832c0 17.7 14.3 32 32 32h640c17.7 0 32-14.3 32-32V311.3c0-8.5-3.4-16.7-9.4-22.7zM790.2 326H602V137.8L790.2 326zm1.8 562H232V136h302v216a42 42 0 0042 42h216v494z"/>
                </svg>
            </span>
            View Changes <span class="change-count-badge">0</span>
        `;
        
        button.onclick = () => this.showChangeSummary();
        toolbar.appendChild(button);
    }

    updateChangeSummaryBadge() {
        const badge = document.querySelector('.change-count-badge');
        if (badge) {
            const count = this.getTotalChangeCount();
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    showChangeSummary() {
        const changes = this.getAllChanges();
        
        if (changes.length === 0) {
            alert('No pending changes');
            return;
        }
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay active';
        modal.innerHTML = `
            <div class="modal-content modal-wide">
                <div class="modal-header">
                    <h2>Pending Changes Summary</h2>
                    <button class="close-button" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="change-summary-content">
                        <div class="summary-stats">
                            <span class="stat">Total Changes: <strong>${changes.length}</strong></span>
                            <span class="stat">Modified Nodes: <strong>${this.pendingChanges.size}</strong></span>
                        </div>
                        <table class="change-summary-table">
                            <thead>
                                <tr>
                                    <th>Node</th>
                                    <th>Field</th>
                                    <th>Original Value</th>
                                    <th>New Value</th>
                                    <th>Changed At</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.renderChangeRows()}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="window.changeTracker.discardAllChanges(); this.closest('.modal-overlay').remove()">
                        Discard All Changes
                    </button>
                    <button class="btn btn-success" onclick="window.changeTracker.handleCommitClick()">
                        Commit Changes to Salesforce
                    </button>
                    <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    renderChangeRows() {
        let html = '';
        
        this.pendingChanges.forEach((nodeChanges, nodeId) => {
            const node = window.hierarchyData.nodes.find(n => n.id === nodeId);
            const nodeName = node ? node.name : nodeId;
            
            nodeChanges.forEach((change, fieldName) => {
                const timestamp = new Date(change.timestamp).toLocaleString();
                
                if (fieldName === '__DELETE__') {
                    // Handle deletion change specially
                    const deleteInfo = change.oldValue;
                    const deleteType = deleteInfo.deleteChildren ? 'Delete with children' : 
                                     deleteInfo.newParentId ? 'Delete and reparent children' : 'Delete node';
                    html += `
                        <tr class="deletion-row">
                            <td>${nodeName}</td>
                            <td colspan="3" style="color: #dc3545;">
                                <strong>${deleteType}</strong>
                                ${deleteInfo.newParentId ? ` (move children to parent ID: ${deleteInfo.newParentId})` : ''}
                            </td>
                            <td>${timestamp}</td>
                            <td>
                                <button class="btn btn-sm" onclick="window.changeTracker.undoDeletion('${nodeId}')">
                                    Undo Delete
                                </button>
                            </td>
                        </tr>
                    `;
                } else {
                    // Regular field change
                    html += `
                        <tr>
                            <td>${nodeName}</td>
                            <td>${fieldName}</td>
                            <td>${this.formatValue(change.oldValue)}</td>
                            <td>${this.formatValue(change.newValue)}</td>
                            <td>${timestamp}</td>
                            <td>
                                <button class="btn btn-sm" onclick="window.changeTracker.discardFieldChange('${nodeId}', '${fieldName}')">
                                    Discard
                                </button>
                            </td>
                        </tr>
                    `;
                }
            });
        });
        
        return html;
    }

    formatValue(value) {
        if (value === null || value === undefined) return '<em>empty</em>';
        if (typeof value === 'boolean') return value ? 'Yes' : 'No';
        if (value === '') return '<em>empty</em>';
        return value;
    }

    discardFieldChange(nodeId, fieldName) {
        const nodeChanges = this.pendingChanges.get(nodeId);
        if (!nodeChanges) return;
        
        const change = nodeChanges.get(fieldName);
        if (!change) return;
        
        // Restore original value
        const node = window.hierarchyData.nodes.find(n => n.id === nodeId);
        if (node) {
            node[fieldName] = change.oldValue;
        }
        
        // Update display
        if (window.inlineEditor) {
            window.inlineEditor.updateFieldDisplay(nodeId, fieldName, change.oldValue);
        }
        
        // Remove change
        nodeChanges.delete(fieldName);
        if (nodeChanges.size === 0) {
            this.pendingChanges.delete(nodeId);
            this.removeNodeModifiedIndicator(nodeId);
        }
        
        // Update UI
        this.updateChangeSummaryBadge();
        
        // Refresh modal if open
        const modal = document.querySelector('.change-summary-table');
        if (modal) {
            modal.querySelector('tbody').innerHTML = this.renderChangeRows();
        }
        
        // Save to session
        this.saveToSession();
    }

    addChangeListener(callback) {
        this.changeListeners.push(callback);
    }

    removeChangeListener(callback) {
        const index = this.changeListeners.indexOf(callback);
        if (index > -1) {
            this.changeListeners.splice(index, 1);
        }
    }

    notifyListeners(event, data) {
        this.changeListeners.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Change listener error:', error);
            }
        });
    }
    
    // Track a node deletion
    trackDeletion(deletionInfo) {
        const nodeId = deletionInfo.nodeId;
        
        // Create a special deletion change
        const change = {
            nodeId: nodeId,
            fieldName: '__DELETE__',
            oldValue: {
                nodeType: deletionInfo.nodeType,
                nodeName: deletionInfo.nodeName,
                deleteChildren: deletionInfo.deleteChildren,
                newParentId: deletionInfo.newParentId
            },
            newValue: null,
            timestamp: deletionInfo.timestamp || new Date().toISOString(),
            id: this.generateChangeId(),
            isDeletion: true
        };
        
        // Store the deletion
        if (!this.pendingChanges.has(nodeId)) {
            this.pendingChanges.set(nodeId, new Map());
        }
        
        const nodeChanges = this.pendingChanges.get(nodeId);
        nodeChanges.set('__DELETE__', change);
        
        // Add to history
        this.addToHistory(change);
        
        // Notify listeners
        this.notifyListeners('deletion-tracked', change);
        
        // Update UI
        this.updateChangeSummaryBadge();
        this.addNodeModifiedIndicator(nodeId);
        
        // Save to session
        this.saveToSession();
    }
    
    // Undo a deletion
    undoDeletion(nodeId) {
        const nodeChanges = this.pendingChanges.get(nodeId);
        if (!nodeChanges) return;
        
        const deletionChange = nodeChanges.get('__DELETE__');
        if (!deletionChange) return;
        
        // Remove the deletion
        nodeChanges.delete('__DELETE__');
        
        // If no other changes, remove the node from pending changes
        if (nodeChanges.size === 0) {
            this.pendingChanges.delete(nodeId);
            this.removeNodeModifiedIndicator(nodeId);
        }
        
        // Notify listeners
        this.notifyListeners('deletion-undone', { nodeId });
        
        // Update UI
        this.updateChangeSummaryBadge();
        
        // Save to session
        this.saveToSession();
    }
    
    // Check if a node is marked for deletion
    isMarkedForDeletion(nodeId) {
        const nodeChanges = this.pendingChanges.get(nodeId);
        if (!nodeChanges) return false;
        
        return nodeChanges.has('__DELETE__');
    }
    
    // Get all pending deletions
    getPendingDeletions() {
        const deletions = [];
        
        this.pendingChanges.forEach((nodeChanges, nodeId) => {
            const deletionChange = nodeChanges.get('__DELETE__');
            if (deletionChange) {
                deletions.push({
                    nodeId: nodeId,
                    ...deletionChange.oldValue,
                    timestamp: deletionChange.timestamp
                });
            }
        });
        
        return deletions;
    }
    
    // Prepare changes for commit
    prepareChangesForCommit() {
        const changes = [];
        const deletions = [];
        
        this.pendingChanges.forEach((nodeChanges, nodeId) => {
            // Get node data to determine type
            const node = window.hierarchyData?.nodes?.find(n => n.id === nodeId);
            const nodeType = node?.type || 'unknown';
            
            nodeChanges.forEach((change, fieldName) => {
                if (fieldName === '__DELETE__') {
                    // Add to deletions
                    deletions.push({
                        nodeId: nodeId,
                        nodeType: nodeType,
                        ...change.oldValue,
                        timestamp: change.timestamp
                    });
                } else {
                    // Add to field changes
                    changes.push({
                        nodeId: change.nodeId,
                        nodeType: nodeType,
                        fieldName: change.fieldName,
                        oldValue: change.oldValue,
                        newValue: change.newValue,
                        timestamp: change.timestamp
                    });
                }
            });
        });
        
        return { changes, deletions };
    }
    
    // Validate changes before commit
    async validateChanges() {
        try {
            const { changes, deletions } = this.prepareChangesForCommit();
            
            const response = await fetch('/api/edit/changes/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ changes, deletions })
            });
            
            if (!response.ok) {
                throw new Error('Validation request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error validating changes:', error);
            return {
                valid: false,
                errors: [error.message],
                warnings: []
            };
        }
    }
    
    // Commit all pending changes
    async commitChanges() {
        try {
            // First validate
            const validation = await this.validateChanges();
            
            if (!validation.valid) {
                return {
                    success: false,
                    errors: validation.errors
                };
            }
            
            // If there are warnings, confirm with user
            if (validation.warnings && validation.warnings.length > 0) {
                const proceed = confirm(
                    'The following warnings were found:\n\n' + 
                    validation.warnings.join('\n') + 
                    '\n\nDo you want to proceed?'
                );
                
                if (!proceed) {
                    return {
                        success: false,
                        errors: ['User cancelled due to warnings']
                    };
                }
            }
            
            // Prepare and send changes
            const { changes, deletions } = this.prepareChangesForCommit();
            
            const response = await fetch('/api/edit/changes/commit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ changes, deletions })
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Commit failed with status:', response.status, errorText);
                throw new Error(`Commit request failed with status ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Commit successful, applying deletions...');
                
                // Apply deletions to the visualization
                const deletions = this.getPendingDeletions();
                console.log('Pending deletions:', deletions);
                
                deletions.forEach(deletion => {
                    console.log('Applying deletion for node:', deletion.nodeId);
                    this.applyDeletionToVisualization(deletion);
                });
                
                // Clear all pending changes
                this.pendingChanges.clear();
                this.clearSession();
                this.updateChangeSummaryBadge();
                
                // Notify listeners
                this.notifyListeners('changes-committed', result);
            }
            
            return result;
            
        } catch (error) {
            console.error('Error committing changes:', error);
            return {
                success: false,
                errors: [error.message]
            };
        }
    }
    
    // Apply deletion to visualization
    applyDeletionToVisualization(deletion) {
        const nodeId = deletion.nodeId;
        console.log('Applying deletion to visualization for node:', nodeId);
        
        // Find the node in D3 hierarchy
        const d3Node = window.hierarchyRoot.descendants().find(d => d.data.id === nodeId);
        console.log('Found D3 node:', d3Node);
        
        if (!d3Node) {
            console.log('Node not found in hierarchy:', nodeId);
            return;
        }
        
        // Handle different deletion types
        if (deletion.deleteChildren) {
            console.log('Deleting node with children');
            // Remove node and all its children
            this.removeNodeFromHierarchy(d3Node);
        } else if (deletion.newParentId) {
            console.log('Moving children to new parent:', deletion.newParentId);
            // Move children to new parent before removing
            const newParent = window.hierarchyRoot.descendants().find(d => d.data.id === deletion.newParentId);
            if (newParent && d3Node.children) {
                d3Node.children.forEach(child => {
                    child.parent = newParent;
                    if (!newParent.children) newParent.children = [];
                    newParent.children.push(child);
                });
            }
            this.removeNodeFromHierarchy(d3Node);
        } else {
            console.log('Deleting leaf node');
            // Just remove the node (leaf node)
            this.removeNodeFromHierarchy(d3Node);
        }
        
        // Update the visualization
        console.log('Updating visualization...');
        if (window.update) {
            window.update(window.hierarchyRoot);
        } else {
            console.log('window.update function not found!');
        }
    }
    
    // Remove node from hierarchy
    removeNodeFromHierarchy(node) {
        if (node.parent && node.parent.children) {
            const index = node.parent.children.indexOf(node);
            if (index > -1) {
                node.parent.children.splice(index, 1);
            }
            // If parent has no more children, remove children array
            if (node.parent.children.length === 0) {
                delete node.parent.children;
            }
        }
        
        // Also remove from _children if collapsed
        if (node.parent && node.parent._children) {
            const index = node.parent._children.indexOf(node);
            if (index > -1) {
                node.parent._children.splice(index, 1);
            }
            if (node.parent._children.length === 0) {
                delete node.parent._children;
            }
        }
        
        // Remove the visual element
        d3.select(`[data-node-id="${node.data.id}"]`).remove();
    }
    
    // Clear session storage
    clearSession() {
        sessionStorage.removeItem('hierarchy-changes');
    }
    
    // Handle commit button click
    async handleCommitClick() {
        // Close the change summary modal
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.remove();
        }
        
        // Show progress modal
        const progressModal = document.createElement('div');
        progressModal.className = 'modal-overlay active';
        progressModal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Committing Changes to Salesforce</h2>
                </div>
                <div class="modal-body">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <p class="progress-message">Connecting to Salesforce...</p>
                </div>
            </div>
        `;
        document.body.appendChild(progressModal);
        
        // Update progress
        const updateProgress = (percent, message) => {
            const progressFill = progressModal.querySelector('.progress-fill');
            const progressMsg = progressModal.querySelector('.progress-message');
            if (progressFill) progressFill.style.width = percent + '%';
            if (progressMsg) progressMsg.textContent = message;
        };
        
        // Perform commit
        updateProgress(25, 'Validating changes...');
        
        const result = await this.commitChanges();
        
        updateProgress(100, 'Processing complete!');
        
        // Show result
        setTimeout(() => {
            progressModal.remove();
            
            if (result.success) {
                // Success modal
                const successModal = document.createElement('div');
                successModal.className = 'modal-overlay';
                successModal.innerHTML = `
                    <div class="modal-content modal-success">
                        <div class="modal-header">
                            <h2>Changes Committed Successfully</h2>
                        </div>
                        <div class="modal-body">
                            <p><strong>Success!</strong> Your changes have been committed to Salesforce.</p>
                            <ul>
                                <li>${result.changes_processed || 0} field changes committed</li>
                                <li>${result.deletions_processed || 0} deletions completed</li>
                            </ul>
                            ${result.deletion_details ? `
                                <details>
                                    <summary>Deletion Details</summary>
                                    <ul>
                                        ${result.deletion_details.map(d => 
                                            `<li>${d.deleted ? d.deleted.length : 0} records deleted${d.reparented ? `, ${d.reparented.length} reparented` : ''}</li>`
                                        ).join('')}
                                    </ul>
                                </details>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove();window.location.reload();">
                                Close & Refresh
                            </button>
                        </div>
                    </div>
                `;
                document.body.appendChild(successModal);
            } else {
                // Error modal
                const errorModal = document.createElement('div');
                errorModal.className = 'modal-overlay';
                errorModal.innerHTML = `
                    <div class="modal-content modal-error">
                        <div class="modal-header">
                            <h2>Commit Failed</h2>
                        </div>
                        <div class="modal-body">
                            <p><strong>Error:</strong> Unable to commit changes to Salesforce.</p>
                            ${result.errors && result.errors.length > 0 ? `
                                <ul>
                                    ${result.errors.map(err => `<li>${err}</li>`).join('')}
                                </ul>
                            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">
                                Close
                            </button>
                        </div>
                    </div>
                `;
                document.body.appendChild(errorModal);
            }
        }, 500);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.changeTracker = new ChangeTracker();
    window.changeTracker.initialize();
    
    // Connect to inline editor
    if (window.inlineEditor) {
        window.inlineEditor.changeTracker = window.changeTracker;
    }
});