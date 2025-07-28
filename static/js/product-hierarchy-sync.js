/**
 * Product Hierarchy Sync Module
 * Handles synchronization of product hierarchy data with Salesforce
 */

(function() {
    'use strict';

    let syncInProgress = false;
    let syncAborted = false;

    // Main sync function
    window.syncProductHierarchy = async function() {
        if (syncInProgress) {
            showAlert('Sync is already in progress', 'warning');
            return;
        }

        console.log('[SYNC] Starting product hierarchy sync...');
        
        // Create and show progress modal
        createSyncProgressModal();
        syncInProgress = true;
        syncAborted = false;
        
        try {
            await performSync();
        } catch (error) {
            console.error('[SYNC] Error during sync:', error);
            showSyncError(error.message || 'An error occurred during sync');
        } finally {
            syncInProgress = false;
        }
    };

    // Create the sync progress modal
    function createSyncProgressModal() {
        // Add styles if not already added
        addSyncStyles();
        
        // Remove any existing modal
        const existingModal = document.getElementById('sync-progress-modal');
        if (existingModal) {
            existingModal.remove();
        }

        const modalHtml = `
            <div class="modal-overlay active" id="sync-progress-modal">
                <div class="modal-content modal-wide" style="max-width: 800px;">
                    <div class="modal-header">
                        <h3>
                            <i class="anticon">
                                <svg viewBox="64 64 896 896" width="1em" height="1em" fill="currentColor">
                                    <path d="M168 504.2c1-43.7 10-86.1 26.9-126 17.3-41 42.1-77.7 73.7-109.4S337 212.3 378 195c42.4-17.9 87.4-27 133.9-27s91.5 9.1 133.8 27A341.5 341.5 0 01755 268.8c31.9 31.9 56.9 68.6 73.9 109.3 16.5 39.8 25.6 82.1 26.7 125.9 1.1 42.9-6.7 84.9-23 124.7a355.5 355.5 0 01-66.2 105.5 353.4 353.4 0 01-96.4 75.8c-37.3 19.3-77.3 32.6-119 39.6-114 19.2-229.7-15.1-310.1-95.5-49.6-49.6-83.1-110.6-97.1-176.5-13.5-63.4-9.5-129.5 11.5-191.1a21.6 21.6 0 0132.6-9.1 21.6 21.6 0 019.1 32.6c-16.9 48.1-20.1 100.2-9.3 150.6 11.1 51.9 37.2 99.7 75.6 138.1 62.7 62.7 153.3 90.5 243 74.5 32.8-5.8 64.2-16.3 93.4-31.2 28.6-14.6 54.7-33.5 77.6-56.4 23.4-23.4 42.6-50.3 57-80 14.8-30.4 24.4-62.8 28.7-96.4 4.2-33 3.2-66.4-2.9-99.1-6.3-33.7-18.3-65.9-35.6-95.8-34.3-59.3-86.5-106.1-149.3-133.8-32.1-14.2-66.1-23.4-101.1-27.5-69.8-8.1-139.6 9.6-196.8 49.9-29.5 20.8-55.1 46.6-75.8 76.6-20.3 29.4-35.5 62.1-45.1 96.8-19.5 70.5-13.1 144.8 18.2 210.5a21.6 21.6 0 01-7.5 29.6 21.6 21.6 0 01-29.6-7.5c-38.3-76.7-46.2-163.5-22.4-245.8 11.4-39.4 29.1-76.6 52.6-110.5 23.9-34.5 53.6-64.6 88.1-89.1 66.6-47.2 149.5-68 233.5-58.5 41.1 4.7 81.1 16 118.6 33.7 73.5 34.7 134.1 91.6 173.3 162.6 20.4 37 34.3 76.8 41.3 118.2 7.2 42.4 8.3 85.7 3.4 128.2-4.9 42-16.5 82.9-34.5 121.3-17.5 37.3-40.8 71.7-69.1 102.2a408.8 408.8 0 01-91.5 68.8 407.1 407.1 0 01-107.9 36.9c-38 7.1-76.7 9.3-115.2 6.6-78.3-5.5-153.7-33.8-215.2-80.8a21.6 21.6 0 01-5.5-30 21.6 21.6 0 0130-5.5c55.1 42.1 122.7 67.4 193 72.3 34.5 2.4 69.2 0.5 103.2-5.9 33.1-6.2 65.1-16.7 95.3-31.2 30.8-14.8 59.4-33.9 85.1-56.6 25.5-22.5 47.9-48.3 66.6-76.9 19.3-29.4 34.3-61.3 44.7-94.8 10.7-34.5 16.4-70.3 17-106.6z"></path>
                                </svg>
                            </i>
                            Syncing Product Hierarchy
                        </h3>
                        <button class="modal-close" onclick="cancelSync()" ${syncInProgress ? '' : 'style="display: none;"'}>
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="padding: 30px;">
                        <div class="sync-status-section">
                            <div class="progress-container">
                                <div class="progress-bar">
                                    <div id="sync-progress-bar" class="progress-fill" style="width: 0%;">
                                        <span id="sync-progress-text">0%</span>
                                    </div>
                                </div>
                            </div>
                            <div id="sync-status-text" class="sync-status-text" style="margin-top: 15px; text-align: center; color: #666;">
                                Preparing sync...
                            </div>
                        </div>
                        
                        <div id="sync-details" style="margin-top: 30px;">
                            <table class="sync-details-table" style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="border-bottom: 2px solid #e8e8e8;">
                                        <th style="text-align: left; padding: 10px;">Object</th>
                                        <th style="text-align: center; padding: 10px; width: 120px;">Status</th>
                                        <th style="text-align: right; padding: 10px; width: 100px;">Records</th>
                                    </tr>
                                </thead>
                                <tbody id="sync-details-body">
                                    <tr id="sync-row-catalogs">
                                        <td style="padding: 10px;">Product Catalogs</td>
                                        <td style="text-align: center; padding: 10px;">
                                            <span class="status-badge status-pending">Pending</span>
                                        </td>
                                        <td style="text-align: right; padding: 10px;">-</td>
                                    </tr>
                                    <tr id="sync-row-categories">
                                        <td style="padding: 10px;">Product Categories</td>
                                        <td style="text-align: center; padding: 10px;">
                                            <span class="status-badge status-pending">Pending</span>
                                        </td>
                                        <td style="text-align: right; padding: 10px;">-</td>
                                    </tr>
                                    <tr id="sync-row-groups">
                                        <td style="padding: 10px;">Product Component Groups</td>
                                        <td style="text-align: center; padding: 10px;">
                                            <span class="status-badge status-pending">Pending</span>
                                        </td>
                                        <td style="text-align: right; padding: 10px;">-</td>
                                    </tr>
                                    <tr id="sync-row-components">
                                        <td style="padding: 10px;">Product Components</td>
                                        <td style="text-align: center; padding: 10px;">
                                            <span class="status-badge status-pending">Pending</span>
                                        </td>
                                        <td style="text-align: right; padding: 10px;">-</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <div id="sync-result" style="display: none; margin-top: 30px; padding: 20px; background: #f0f9ff; border-radius: 8px; border: 1px solid #0176d3;">
                            <h4 style="margin: 0 0 10px 0; color: #0176d3;">
                                <i class="fas fa-check-circle"></i> Sync Complete!
                            </h4>
                            <p id="sync-result-message" style="margin: 0; color: #333;"></p>
                        </div>
                        
                        <div id="sync-error" style="display: none; margin-top: 30px; padding: 20px; background: #fef3f2; border-radius: 8px; border: 1px solid #ea001e;">
                            <h4 style="margin: 0 0 10px 0; color: #ea001e;">
                                <i class="fas fa-exclamation-circle"></i> Sync Error
                            </h4>
                            <p id="sync-error-message" style="margin: 0; color: #333;"></p>
                        </div>
                    </div>
                    <div class="modal-footer" style="padding: 20px; border-top: 1px solid #e8e8e8;">
                        <button id="sync-cancel-btn" class="btn btn-secondary" onclick="cancelSync()" style="margin-right: 10px;">
                            Cancel
                        </button>
                        <button id="sync-close-btn" class="btn btn-primary" onclick="closeSyncModal()" style="display: none;">
                            Close & Refresh View
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Perform the actual sync
    async function performSync() {
        const syncItems = [
            { id: 'catalogs', name: 'Product Catalogs', object: 'ProductCatalog' },
            { id: 'categories', name: 'Product Categories', object: 'ProductCategory' },
            { id: 'groups', name: 'Product Component Groups', object: 'ProductComponentGroup' },
            { id: 'components', name: 'Product Components', object: 'ProductComponent' }
        ];
        
        let totalSynced = 0;
        let successCount = 0;
        let totalRecords = 0;
        
        updateSyncStatus('Connecting to Salesforce...');
        
        for (let i = 0; i < syncItems.length; i++) {
            if (syncAborted) break;
            
            const item = syncItems[i];
            updateItemStatus(item.id, 'syncing');
            updateSyncStatus(`Syncing ${item.name}...`);
            
            try {
                const response = await fetch(`/api/sync/${item.object}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to sync ${item.name}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    updateItemStatus(item.id, 'synced', result.recordCount || 0);
                    successCount++;
                    totalRecords += (result.recordCount || 0);
                } else {
                    updateItemStatus(item.id, 'error');
                    console.error(`[SYNC] Error syncing ${item.name}:`, result.error);
                }
                
            } catch (error) {
                updateItemStatus(item.id, 'error');
                console.error(`[SYNC] Error syncing ${item.name}:`, error);
            }
            
            totalSynced++;
            const progress = Math.round((totalSynced / syncItems.length) * 100);
            updateProgressBar(progress);
        }
        
        // Show results
        if (syncAborted) {
            showSyncError('Sync was cancelled by user');
        } else if (successCount === syncItems.length) {
            showSyncSuccess(`Successfully synced all product hierarchy data. ${totalRecords} total records processed.`);
        } else if (successCount > 0) {
            showSyncSuccess(`Partially completed. ${successCount} of ${syncItems.length} objects synced successfully. ${totalRecords} records processed.`);
        } else {
            showSyncError('Failed to sync any objects. Please check your connection and try again.');
        }
    }

    // Update sync status text
    function updateSyncStatus(text) {
        const statusElement = document.getElementById('sync-status-text');
        if (statusElement) {
            statusElement.textContent = text;
        }
    }

    // Update progress bar
    function updateProgressBar(percentage) {
        const progressBar = document.getElementById('sync-progress-bar');
        const progressText = document.getElementById('sync-progress-text');
        if (progressBar && progressText) {
            progressBar.style.width = percentage + '%';
            progressText.textContent = percentage + '%';
        }
    }

    // Update item status in the table
    function updateItemStatus(itemId, status, recordCount) {
        const row = document.getElementById(`sync-row-${itemId}`);
        if (!row) return;
        
        const statusCell = row.querySelector('td:nth-child(2) .status-badge');
        const countCell = row.querySelector('td:nth-child(3)');
        
        if (statusCell) {
            statusCell.className = `status-badge status-${status}`;
            switch (status) {
                case 'pending':
                    statusCell.textContent = 'Pending';
                    break;
                case 'syncing':
                    statusCell.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Syncing';
                    break;
                case 'synced':
                    statusCell.innerHTML = '<i class="fas fa-check"></i> Synced';
                    break;
                case 'error':
                    statusCell.innerHTML = '<i class="fas fa-times"></i> Error';
                    break;
            }
        }
        
        if (countCell && recordCount !== undefined) {
            countCell.textContent = recordCount.toLocaleString();
        }
    }

    // Show sync success
    function showSyncSuccess(message) {
        const resultDiv = document.getElementById('sync-result');
        const resultMessage = document.getElementById('sync-result-message');
        const errorDiv = document.getElementById('sync-error');
        const cancelBtn = document.getElementById('sync-cancel-btn');
        const closeBtn = document.getElementById('sync-close-btn');
        
        if (resultDiv && resultMessage) {
            resultMessage.textContent = message;
            resultDiv.style.display = 'block';
        }
        
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
        
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (closeBtn) closeBtn.style.display = 'inline-block';
        
        updateSyncStatus('Sync complete!');
    }

    // Show sync error
    function showSyncError(message) {
        const errorDiv = document.getElementById('sync-error');
        const errorMessage = document.getElementById('sync-error-message');
        const resultDiv = document.getElementById('sync-result');
        const cancelBtn = document.getElementById('sync-cancel-btn');
        const closeBtn = document.getElementById('sync-close-btn');
        
        if (errorDiv && errorMessage) {
            errorMessage.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        if (resultDiv) {
            resultDiv.style.display = 'none';
        }
        
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (closeBtn) closeBtn.style.display = 'inline-block';
        
        updateSyncStatus('Sync failed');
    }

    // Cancel sync
    window.cancelSync = function() {
        if (confirm('Are you sure you want to cancel the sync?')) {
            syncAborted = true;
            closeSyncModal();
        }
    };

    // Close sync modal
    window.closeSyncModal = function() {
        const modal = document.getElementById('sync-progress-modal');
        if (modal) {
            modal.remove();
        }
        
        // Refresh the hierarchy view
        if (window.refreshHierarchy) {
            window.refreshHierarchy();
        }
    };

    // Add CSS styles for sync modal
    function addSyncStyles() {
        if (document.getElementById('sync-modal-styles')) return;
        
        const styles = `
            <style id="sync-modal-styles">
                .progress-container {
                    width: 100%;
                    height: 30px;
                    background: #f0f0f0;
                    border-radius: 15px;
                    overflow: hidden;
                    position: relative;
                }
                
                .progress-bar {
                    width: 100%;
                    height: 100%;
                    background: #f0f0f0;
                    border-radius: 15px;
                    overflow: hidden;
                }
                
                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #0176D3 0%, #0B5CAB 100%);
                    transition: width 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 500;
                    font-size: 14px;
                    position: relative;
                    overflow: hidden;
                }
                
                .progress-fill:after {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    bottom: 0;
                    right: 0;
                    background: linear-gradient(
                        -45deg,
                        rgba(255, 255, 255, 0.2) 25%,
                        transparent 25%,
                        transparent 50%,
                        rgba(255, 255, 255, 0.2) 50%,
                        rgba(255, 255, 255, 0.2) 75%,
                        transparent 75%,
                        transparent
                    );
                    background-size: 30px 30px;
                    animation: stripes 1s linear infinite;
                }
                
                @keyframes stripes {
                    0% { background-position: 0 0; }
                    100% { background-position: 30px 0; }
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .status-pending {
                    background: #f0f0f0;
                    color: #666;
                }
                
                .status-syncing {
                    background: #e3f2fd;
                    color: #1976d2;
                }
                
                .status-synced {
                    background: #e8f5e9;
                    color: #388e3c;
                }
                
                .status-error {
                    background: #ffebee;
                    color: #d32f2f;
                }
                
                .sync-details-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                
                .sync-details-table th {
                    background: #f5f5f5;
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 12px;
                    letter-spacing: 0.5px;
                    color: #666;
                }
                
                .sync-details-table td {
                    border-bottom: 1px solid #e8e8e8;
                }
                
                .sync-details-table tr:last-child td {
                    border-bottom: none;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }

    // Show alert modal
    function showAlert(message, type = 'info') {
        const alertModal = `
            <div class="modal-overlay active" onclick="this.remove()">
                <div class="modal-content" style="max-width: 400px;">
                    <div class="modal-header">
                        <h3>${type === 'warning' ? '<i class="fas fa-exclamation-triangle"></i> ' : ''}${type.charAt(0).toUpperCase() + type.slice(1)}</h3>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">OK</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', alertModal);
    }

})();