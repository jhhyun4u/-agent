-- VAULT COMPLETE SETUP - One-shot installation
-- Run this SINGLE file in Supabase SQL Editor
-- This completely removes and rebuilds the entire Vault system

-- ============================================================================
-- STEP 0: AGGRESSIVE CLEANUP
-- ============================================================================

BEGIN;

-- Disable RLS temporarily to allow drops
ALTER TABLE IF EXISTS vault_conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS vault_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS vault_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS vault_audit_logs DISABLE ROW LEVEL SECURITY;

-- Drop function first
DROP FUNCTION IF EXISTS vault_search_documents CASCADE;

-- Force drop all indexes by recreating them in the drop process
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

-- Drop tables in dependency order
DROP TABLE IF EXISTS vault_audit_logs CASCADE;
DROP TABLE IF EXISTS vault_messages CASCADE;
DROP TABLE IF EXISTS vault_conversations CASCADE;
DROP TABLE IF EXISTS vault_documents CASCADE;

COMMIT;

-- ============================================================================
-- STEP 1: CREATE VAULT SYSTEM TABLES
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- Vault Conversations Table
CREATE TABLE vault_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT user_conversations_unique UNIQUE(id, user_id)
);

CREATE INDEX idx_vault_conversations_user_id ON vault_conversations(user_id);
CREATE INDEX idx_vault_conversations_updated_at ON vault_conversations(updated_at DESC);

ALTER TABLE vault_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_conversations_select_by_user ON vault_conversations
FOR SELECT USING (auth.jwt() ->> 'sub' = user_id::text);
CREATE POLICY vault_conversations_insert_by_user ON vault_conversations
FOR INSERT WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);
CREATE POLICY vault_conversations_update_by_user ON vault_conversations
FOR UPDATE USING (auth.jwt() ->> 'sub' = user_id::text);
CREATE POLICY vault_conversations_delete_by_user ON vault_conversations
FOR DELETE USING (auth.jwt() ->> 'sub' = user_id::text);

-- Vault Messages Table
CREATE TABLE vault_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES vault_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT message_content_not_empty CHECK (LENGTH(TRIM(content)) > 0)
);

CREATE INDEX idx_vault_messages_conversation_id ON vault_messages(conversation_id);
CREATE INDEX idx_vault_messages_created_at ON vault_messages(created_at DESC);

ALTER TABLE vault_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_messages_select_by_user ON vault_messages
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM vault_conversations vc
        WHERE vc.id = vault_messages.conversation_id
        AND vc.user_id = auth.uid()
    )
);

CREATE POLICY vault_messages_insert_by_user ON vault_messages
FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM vault_conversations vc
        WHERE vc.id = vault_messages.conversation_id
        AND vc.user_id = auth.uid()
    )
);

-- Vault Documents Table
CREATE TABLE vault_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section TEXT NOT NULL CHECK (section IN (
        'completed_projects',
        'company_internal',
        'credentials',
        'government_guidelines',
        'competitors',
        'success_cases',
        'clients_db',
        'research_materials'
    )),
    title TEXT NOT NULL,
    content TEXT,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    retention_policy TEXT CHECK (retention_policy IN ('permanent', '3_months', '6_months')),
    expires_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT document_content_not_empty CHECK (
        content IS NULL OR LENGTH(TRIM(content)) > 0
    )
);

CREATE INDEX idx_vault_documents_section ON vault_documents(section);
CREATE INDEX idx_vault_documents_created_at ON vault_documents(created_at DESC);
CREATE INDEX idx_vault_documents_expires_at ON vault_documents(expires_at) WHERE retention_policy = '3_months';
CREATE INDEX idx_vault_documents_embedding ON vault_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_vault_documents_content_fts ON vault_documents USING GIN(to_tsvector('english', content));

ALTER TABLE vault_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_documents_view ON vault_documents
FOR SELECT USING (true);

-- Vault Audit Logs Table
CREATE TABLE vault_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    query TEXT,
    section TEXT,
    result_count INT,
    response_time_ms FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_vault_audit_logs_user_id ON vault_audit_logs(user_id);
CREATE INDEX idx_vault_audit_logs_timestamp ON vault_audit_logs(created_at DESC);

-- ============================================================================
-- STEP 2: CREATE METADATA INDEXES (Migration 028)
-- ============================================================================

CREATE INDEX idx_vault_documents_metadata_industry ON vault_documents USING GIN ((metadata->'industry'));
CREATE INDEX idx_vault_documents_metadata_tech_stack ON vault_documents USING GIN ((metadata->'tech_stack'));
CREATE INDEX idx_vault_documents_metadata_team_size ON vault_documents (((metadata->>'team_size')::int));
CREATE INDEX idx_vault_documents_metadata_duration_months ON vault_documents (((metadata->>'duration_months')::int));
CREATE INDEX idx_vault_documents_metadata_general ON vault_documents USING GIN (metadata);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'Vault setup complete!' as status;
SELECT count(*) as vault_tables FROM pg_tables WHERE tablename LIKE 'vault_%';
SELECT count(*) as metadata_indexes FROM pg_indexes WHERE indexname LIKE 'idx_vault_documents_metadata_%';
