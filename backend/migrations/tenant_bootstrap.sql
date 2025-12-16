-- Backfill tenant_id on existing tables and create bootstrap admin user

-- Ensure tenant container exists
INSERT OR IGNORE INTO tenants(id, name, created_at) VALUES('default', 'Default Tenant', CURRENT_TIMESTAMP);

-- Add tenant_id columns if they are missing
ALTER TABLE IF NOT EXISTS mcp_servers ADD COLUMN tenant_id TEXT DEFAULT 'default';
ALTER TABLE IF NOT EXISTS tasks ADD COLUMN tenant_id TEXT DEFAULT 'default';
ALTER TABLE IF NOT EXISTS analytics_events ADD COLUMN tenant_id TEXT DEFAULT 'default';

-- Backfill existing rows
UPDATE mcp_servers SET tenant_id = COALESCE(tenant_id, 'default');
UPDATE tasks SET tenant_id = COALESCE(tenant_id, 'default');
UPDATE analytics_events SET tenant_id = COALESCE(tenant_id, 'default');

-- Bootstrap admin user (password hash must be replaced in production)
INSERT OR IGNORE INTO users(id, email, full_name, hashed_password, is_active, role, tenant_id, created_at)
VALUES (1, 'admin@hisper.local', 'Platform Admin', '$2b$12$H2aZSc0YyB0yfhGGcvR0nO6Hm6IZ28lTrU9mZ4VHKpL5LG4JnPUWS', 1, 'admin', 'default', CURRENT_TIMESTAMP);

