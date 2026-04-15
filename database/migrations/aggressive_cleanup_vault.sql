-- Aggressive cleanup: Remove ALL vault-related objects
-- This handles dependencies and lingering indexes

-- Drop function first
DROP FUNCTION IF EXISTS vault_search_documents CASCADE;

-- Drop all indexes explicitly
DROP INDEX IF EXISTS idx_vault_conversations_user_id CASCADE;
DROP INDEX IF EXISTS idx_vault_conversations_updated_at CASCADE;
DROP INDEX IF EXISTS idx_vault_messages_conversation_id CASCADE;
DROP INDEX IF EXISTS idx_vault_messages_created_at CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_section CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_created_at CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_expires_at CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_embedding CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_content_fts CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_metadata_industry CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_metadata_tech_stack CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_metadata_team_size CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_metadata_duration_months CASCADE;
DROP INDEX IF EXISTS idx_vault_documents_metadata_general CASCADE;
DROP INDEX IF EXISTS idx_vault_audit_logs_user_id CASCADE;
DROP INDEX IF EXISTS idx_vault_audit_logs_timestamp CASCADE;

-- Drop policies
DROP POLICY IF EXISTS vault_conversations_select_by_user ON vault_conversations;
DROP POLICY IF EXISTS vault_conversations_insert_by_user ON vault_conversations;
DROP POLICY IF EXISTS vault_conversations_update_by_user ON vault_conversations;
DROP POLICY IF EXISTS vault_conversations_delete_by_user ON vault_conversations;
DROP POLICY IF EXISTS vault_messages_select_by_user ON vault_messages;
DROP POLICY IF EXISTS vault_messages_insert_by_user ON vault_messages;
DROP POLICY IF EXISTS vault_documents_view ON vault_documents;

-- Drop tables
DROP TABLE IF EXISTS vault_audit_logs CASCADE;
DROP TABLE IF EXISTS vault_messages CASCADE;
DROP TABLE IF EXISTS vault_conversations CASCADE;
DROP TABLE IF EXISTS vault_documents CASCADE;

-- Verify all vault objects are gone
SELECT 'Tables remaining:' as status, count(*) as count
FROM pg_tables
WHERE tablename LIKE 'vault_%'
UNION ALL
SELECT 'Indexes remaining:', count(*)
FROM pg_indexes
WHERE indexname LIKE 'idx_vault%';
