// Debug script for Add Category button issue
console.log('=== Add Category Debug Script Loaded ===');

// Monitor when modal is shown
if (window.addNodeManager) {
    const originalShow = window.addNodeManager.showAddCategoryModal;
    window.addNodeManager.showAddCategoryModal = function(parentNode) {
        console.log('[DEBUG] showAddCategoryModal called with parent:', parentNode);
        
        // Call original method
        const result = originalShow.apply(this, [parentNode]);
        
        // After modal is shown, check button
        setTimeout(() => {
            const button = document.getElementById('add-category-submit-btn');
            if (button) {
                console.log('[DEBUG] Add Category button found:', button);
                console.log('[DEBUG] Button onclick:', button.onclick);
                console.log('[DEBUG] Button listeners:', button._listeners);
                
                // Check if button is clickable
                const rect = button.getBoundingClientRect();
                console.log('[DEBUG] Button position:', rect);
                console.log('[DEBUG] Button visible:', rect.width > 0 && rect.height > 0);
                console.log('[DEBUG] Button disabled:', button.disabled);
            } else {
                console.error('[DEBUG] Add Category button not found!');
            }
        }, 100);
        
        return result;
    };
    
    // Monitor submit method
    const originalSubmit = window.addNodeManager.submitAddCategory;
    window.addNodeManager.submitAddCategory = function() {
        console.log('[DEBUG] submitAddCategory called!');
        console.log('[DEBUG] this context:', this);
        console.log('[DEBUG] currentParentNode:', this.currentParentNode);
        
        try {
            return originalSubmit.apply(this, arguments);
        } catch (error) {
            console.error('[DEBUG] Error in submitAddCategory:', error);
            throw error;
        }
    };
    
    console.log('[DEBUG] Add Category monitoring installed');
} else {
    console.error('[DEBUG] addNodeManager not found!');
}

// Test function to manually trigger the modal
window.testAddCategory = function() {
    console.log('[DEBUG TEST] Testing Add Category modal...');
    
    if (!window.addNodeManager) {
        console.error('[DEBUG TEST] addNodeManager not available');
        return;
    }
    
    // Create test parent node
    const testParent = {
        id: '0ZSdp00000007kfGAA',
        name: 'Test Catalog',
        type: 'catalog'
    };
    
    console.log('[DEBUG TEST] Showing modal with test parent:', testParent);
    window.addNodeManager.showAddCategoryModal(testParent);
    
    // Try to click button after delay
    setTimeout(() => {
        const button = document.getElementById('add-category-submit-btn');
        if (button) {
            console.log('[DEBUG TEST] Found button, attempting click...');
            button.click();
        } else {
            console.error('[DEBUG TEST] Button not found');
        }
    }, 500);
};

console.log('=== Debug script ready. Use testAddCategory() to test ===');