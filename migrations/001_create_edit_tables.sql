-- Create tables for Product Hierarchy Edit Functionality
-- Migration: 001_create_edit_tables.sql

-- User Permissions Table
CREATE TABLE IF NOT EXISTS edit_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('view_only', 'edit_basic', 'edit_structure', 'full_edit', 'admin')),
    org_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    UNIQUE(user_id, org_id)
);

-- Field Configuration Table
CREATE TABLE IF NOT EXISTS field_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL DEFAULT 'Product2',
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    is_editable BOOLEAN DEFAULT TRUE,
    required BOOLEAN DEFAULT FALSE,
    validation_rules JSON,
    permission_level VARCHAR(20),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, object_type, field_name)
);

-- Change History Table
CREATE TABLE IF NOT EXISTS change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    org_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('create', 'update', 'delete', 'move', 'clone')),
    field_changes JSON,
    old_values JSON,
    new_values JSON,
    parent_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'validated', 'committed', 'failed', 'rolled_back')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    committed_at TIMESTAMP,
    salesforce_id VARCHAR(50),
    batch_id VARCHAR(50)
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    org_id VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    object_type VARCHAR(50),
    object_id VARCHAR(50),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Edit Conflicts Table
CREATE TABLE IF NOT EXISTS edit_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    user1_id VARCHAR(50) NOT NULL,
    user1_value TEXT,
    user1_timestamp TIMESTAMP,
    user2_id VARCHAR(50) NOT NULL,
    user2_value TEXT,
    user2_timestamp TIMESTAMP,
    resolution_status VARCHAR(20) DEFAULT 'unresolved',
    resolved_by VARCHAR(50),
    resolved_value TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_permissions_user ON edit_permissions(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_changes_status ON change_history(status, org_id);
CREATE INDEX IF NOT EXISTS idx_changes_user ON change_history(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conflicts_node ON edit_conflicts(node_id, resolution_status);

-- Insert default field configurations for Product2 object
INSERT OR IGNORE INTO field_config (org_id, object_type, field_name, field_label, field_type, is_editable, required, permission_level, display_order) VALUES
('default', 'Product2', 'Name', 'Product Name', 'text', TRUE, TRUE, 'edit_basic', 1),
('default', 'Product2', 'ProductCode', 'Product Code', 'text', TRUE, FALSE, 'edit_basic', 2),
('default', 'Product2', 'Description', 'Description', 'textarea', TRUE, FALSE, 'edit_basic', 3),
('default', 'Product2', 'IsActive', 'Active', 'checkbox', TRUE, FALSE, 'edit_basic', 4),
('default', 'Product2', 'Family', 'Product Family', 'picklist', TRUE, FALSE, 'edit_structure', 5),
('default', 'Product2', 'QuantityUnitOfMeasure', 'Unit of Measure', 'text', TRUE, FALSE, 'edit_basic', 6),
('default', 'Product2', 'DisplayUrl', 'Display URL', 'url', TRUE, FALSE, 'edit_basic', 7),
('default', 'Product2', 'ExternalId', 'External ID', 'text', TRUE, FALSE, 'edit_structure', 8);