-- Vault AI Chat System - Database Migration
-- Phase 1 Implementation
-- 
-- Creates tables for:
-- - vault_conversations: Chat sessions
-- - vault_messages: Individual chat messages
-- - vault_documents: Knowledge base documents with vector embeddings

-- ============================================================================
-- Vault Conversations Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS vault_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for common queries
    CONSTRAINT user_conversations_unique UNIQUE(id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_vault_conversations_user_id 
ON vault_conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_vault_conversations_updated_at 
ON vault_conversations(updated_at DESC);

-- RLS: Users can only access their own conversations
ALTER TABLE vault_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_conversations_select_by_user ON vault_conversations
FOR SELECT
USING (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY vault_conversations_insert_by_user ON vault_conversations
FOR INSERT
WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY vault_conversations_update_by_user ON vault_conversations
FOR UPDATE
USING (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY vault_conversations_delete_by_user ON vault_conversations
FOR DELETE
USING (auth.jwt() ->> 'sub' = user_id::text);


-- ============================================================================
-- Vault Messages Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS vault_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES vault_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,  -- Array of {document_id, section, title, snippet, url_path}
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT message_content_not_empty CHECK (LENGTH(TRIM(content)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_vault_messages_conversation_id 
ON vault_messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_vault_messages_created_at 
ON vault_messages(created_at DESC);

-- RLS: Users can only access messages from their conversations
ALTER TABLE vault_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_messages_select_by_user ON vault_messages
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM vault_conversations vc
        WHERE vc.id = vault_messages.conversation_id
        AND vc.user_id = auth.uid()
    )
);

CREATE POLICY vault_messages_insert_by_user ON vault_messages
FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM vault_conversations vc
        WHERE vc.id = vault_messages.conversation_id
        AND vc.user_id = auth.uid()
    )
);


-- ============================================================================
-- Vault Documents Table (with pgvector support)
-- ============================================================================

-- First, ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS vault_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core content
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
    
    -- Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding VECTOR(1536),
    
    -- Metadata and tracking
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Retention policy
    retention_policy TEXT CHECK (retention_policy IN ('permanent', '3_months', '6_months')),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT document_content_not_empty CHECK (
        content IS NULL OR LENGTH(TRIM(content)) > 0
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_vault_documents_section 
ON vault_documents(section);

CREATE INDEX IF NOT EXISTS idx_vault_documents_created_at 
ON vault_documents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vault_documents_expires_at 
ON vault_documents(expires_at) 
WHERE retention_policy = '3_months';

-- Vector similarity index (IVFFLAT for pgvector)
CREATE INDEX IF NOT EXISTS idx_vault_documents_embedding 
ON vault_documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Full-text search index for content (using default English config - Korean config not available in Supabase)
CREATE INDEX IF NOT EXISTS idx_vault_documents_content_fts
ON vault_documents USING GIN(to_tsvector('english', content));

-- RLS: All documents visible to authenticated users (team-based access in app layer)
ALTER TABLE vault_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_documents_select_all ON vault_documents
FOR SELECT
USING (auth.role() = 'authenticated');

CREATE POLICY vault_documents_insert_by_admin ON vault_documents
FOR INSERT
WITH CHECK (auth.jwt() ->> 'role' = 'vault_admin');

CREATE POLICY vault_documents_update_by_admin ON vault_documents
FOR UPDATE
USING (auth.jwt() ->> 'role' = 'vault_admin');

CREATE POLICY vault_documents_delete_by_admin ON vault_documents
FOR DELETE
USING (auth.jwt() ->> 'role' = 'vault_admin');


-- ============================================================================
-- Audit Logging (Optional - for compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS vault_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    action TEXT NOT NULL CHECK (action IN ('search', 'view', 'export', 'feedback')),
    section TEXT,
    query TEXT,
    result_count INT,
    response_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vault_audit_logs_user_id 
ON vault_audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_vault_audit_logs_created_at 
ON vault_audit_logs(created_at DESC);

-- Auto-cleanup: keep 90 days of audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM vault_audit_logs
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Search vault documents using vector similarity
CREATE OR REPLACE FUNCTION vault_vector_search(
    query_embedding vector(1536),
    search_section TEXT DEFAULT NULL,
    limit_results INT DEFAULT 10,
    distance_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    document_id UUID,
    title TEXT,
    content TEXT,
    section TEXT,
    distance FLOAT,
    confidence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        title,
        content,
        section,
        (1 - (embedding <=> query_embedding))::FLOAT,
        (1 - (embedding <=> query_embedding))::FLOAT
    FROM vault_documents
    WHERE 
        (search_section IS NULL OR section = search_section)
        AND embedding <=> query_embedding < distance_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function: Full-text search vault documents
CREATE OR REPLACE FUNCTION vault_full_text_search(
    search_query TEXT,
    search_section TEXT DEFAULT NULL,
    limit_results INT DEFAULT 10
)
RETURNS TABLE (
    document_id UUID,
    title TEXT,
    content TEXT,
    section TEXT,
    relevance FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        id,
        title,
        content,
        section,
        ts_rank(to_tsvector('english', content), plainto_tsquery('english', search_query))::FLOAT
    FROM vault_documents
    WHERE
        (search_section IS NULL OR section = search_section)
        AND to_tsvector('english', content) @@ plainto_tsquery('english', search_query)
    ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', search_query)) DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- Initial Data Seed (Optional)
-- ============================================================================

-- This would be populated during data migration Phase 1
-- See docs/01-plan/vault-phase1-implementation.md Section 4.1 for migration steps


-- ============================================================================
-- Permissions
-- ============================================================================

-- Grant appropriate permissions
GRANT SELECT ON vault_conversations TO authenticated;
GRANT SELECT ON vault_messages TO authenticated;
GRANT SELECT ON vault_documents TO authenticated;
GRANT SELECT ON vault_audit_logs TO authenticated;

-- Admin role (created via Supabase Dashboard)
-- GRANT INSERT, UPDATE, DELETE ON vault_documents TO vault_admin;
