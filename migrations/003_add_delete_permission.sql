-- Add delete permission level to existing permission system
-- Migration: 003_add_delete_permission.sql
-- Date: 2025-01-23

-- First, we need to update the check constraint on the edit_permissions table
-- SQLite doesn't support ALTER TABLE for constraints, so we need to recreate the table

-- Step 1: Create temporary table with new schema
CREATE TABLE IF NOT EXISTS edit_permissions_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) NOT NULL,
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('view_only', 'edit_basic', 'edit_structure', 'delete', 'full_edit', 'admin')),
    org_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    UNIQUE(user_id, org_id)
);

-- Step 2: Copy existing data
INSERT INTO edit_permissions_temp (id, user_id, permission_level, org_id, created_at, updated_at, created_by)
SELECT id, user_id, permission_level, org_id, created_at, updated_at, created_by
FROM edit_permissions;

-- Step 3: Drop old table
DROP TABLE edit_permissions;

-- Step 4: Rename new table
ALTER TABLE edit_permissions_temp RENAME TO edit_permissions;

-- Step 5: Update field_config permission_level check constraint (same process)
CREATE TABLE IF NOT EXISTS field_config_temp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id VARCHAR(50) NOT NULL,
    object_type VARCHAR(50) NOT NULL DEFAULT 'Product2',
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    is_editable BOOLEAN DEFAULT TRUE,
    required BOOLEAN DEFAULT FALSE,
    validation_rules JSON,
    permission_level VARCHAR(20) CHECK (permission_level IN ('view_only', 'edit_basic', 'edit_structure', 'delete', 'full_edit', 'admin')),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, object_type, field_name)
);

-- Copy existing field_config data
INSERT INTO field_config_temp
SELECT * FROM field_config;

-- Drop old table and rename
DROP TABLE field_config;
ALTER TABLE field_config_temp RENAME TO field_config;

-- Add audit log entry for this migration
INSERT INTO audit_log (user_id, org_id, action, object_type, object_id, details, created_at)
VALUES ('system', 'all', 'permission_update', 'system', 'delete_permission', 
        '{"description": "Added delete permission level to permission system"}', 
        CURRENT_TIMESTAMP);