-- Cleanup script: Remove all Vault objects before re-applying migrations
-- Run this FIRST to clean up existing partial installations

-- Drop functions first (they depend on tables)
DROP FUNCTION IF EXISTS vault_search_documents(TEXT, TEXT, INT) CASCADE;
DROP FUNCTION IF EXISTS vault_search_documents(TEXT, INT) CASCADE;

-- Drop tables (will cascade drop indexes and constraints)
DROP TABLE IF EXISTS vault_audit_logs CASCADE;
DROP TABLE IF EXISTS vault_messages CASCADE;
DROP TABLE IF EXISTS vault_conversations CASCADE;
DROP TABLE IF EXISTS vault_documents CASCADE;

-- Verify cleanup (should show no results)
SELECT tablename FROM pg_tables
WHERE tablename LIKE 'vault_%'
ORDER BY tablename;
