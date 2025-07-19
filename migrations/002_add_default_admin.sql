-- Add default admin user permissions
-- Migration: 002_add_default_admin.sql

-- Insert default admin permission for the default user
INSERT OR IGNORE INTO edit_permissions (user_id, org_id, permission_level, created_by) 
VALUES ('default_user', 'default', 'admin', 'system');