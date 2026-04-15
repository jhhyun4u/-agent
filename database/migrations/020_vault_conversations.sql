-- Vault Conversations and Messages Tables
-- Migration: Create tables for Vault AI Chat feature

-- Create vault_conversations table
CREATE TABLE IF NOT EXISTS vault_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,
  
  CONSTRAINT vault_conversations_user_id_not_null CHECK (user_id IS NOT NULL)
);

CREATE INDEX idx_vault_conversations_user_id ON vault_conversations(user_id);
CREATE INDEX idx_vault_conversations_created_at ON vault_conversations(created_at DESC);
CREATE INDEX idx_vault_conversations_deleted_at ON vault_conversations(deleted_at) WHERE deleted_at IS NULL;

-- Create vault_messages table
CREATE TABLE IF NOT EXISTS vault_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES vault_conversations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  sources JSONB, -- Array of {section, content, confidence}
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  CONSTRAINT vault_messages_content_not_empty CHECK (content <> '')
);

CREATE INDEX idx_vault_messages_conversation_id ON vault_messages(conversation_id);
CREATE INDEX idx_vault_messages_user_id ON vault_messages(user_id);
CREATE INDEX idx_vault_messages_created_at ON vault_messages(created_at DESC);

-- Create vault_documents table for knowledge base
CREATE TABLE IF NOT EXISTS vault_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id TEXT NOT NULL, -- Reference to original document (proposal_id, etc)
  document_type TEXT NOT NULL, -- 'proposal', 'guideline', 'lesson', etc
  section TEXT NOT NULL, -- 'completed_projects', 'government_guidelines', etc
  title TEXT,
  content TEXT NOT NULL,
  metadata JSONB, -- Store additional metadata (budget, client, etc)
  
  -- Vector embeddings for similarity search
  embedding VECTOR(1536), -- OpenAI embedding dimension
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE,
  
  CONSTRAINT vault_documents_content_not_empty CHECK (content <> '')
);

CREATE INDEX idx_vault_documents_document_id ON vault_documents(document_id);
CREATE INDEX idx_vault_documents_section ON vault_documents(section);
CREATE INDEX idx_vault_documents_document_type ON vault_documents(document_type);
CREATE INDEX idx_vault_documents_created_at ON vault_documents(created_at DESC);
CREATE INDEX idx_vault_documents_deleted_at ON vault_documents(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_vault_documents_embedding ON vault_documents USING ivfflat (embedding vector_cosine_ops);

-- Add RLS policies
ALTER TABLE vault_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_conversations_user_isolation ON vault_conversations
  FOR ALL USING (user_id = auth.uid());

CREATE POLICY vault_messages_user_isolation ON vault_messages
  FOR ALL USING (user_id = auth.uid());

-- vault_documents is public (read-only for all users)
ALTER TABLE vault_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_documents_select ON vault_documents
  FOR SELECT USING (deleted_at IS NULL);

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add comment for documentation
COMMENT ON TABLE vault_conversations IS 'Stores AI chat conversations for the Vault feature';
COMMENT ON TABLE vault_messages IS 'Stores individual messages within Vault conversations';
COMMENT ON TABLE vault_documents IS 'Stores knowledge base documents with vector embeddings for similarity search';
COMMENT ON COLUMN vault_documents.embedding IS 'OpenAI text-embedding-3-small 1536-dimensional embedding';
