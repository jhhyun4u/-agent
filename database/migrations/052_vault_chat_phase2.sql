-- ============================================================================
-- Vault Chat Phase 2 — Database Migration
-- Date: 2026-04-20
-- New tables: teams_bot_config, teams_bot_messages
-- Extended tables: vault_messages, vault_documents, vault_conversations, vault_audit_logs
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. New Tables
-- ============================================================================

-- 1.1 Teams Bot Configuration
CREATE TABLE IF NOT EXISTS teams_bot_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) NOT NULL UNIQUE,

    -- Bot activation and modes
    bot_enabled BOOLEAN DEFAULT true,
    bot_modes TEXT[] DEFAULT ARRAY['adaptive', 'digest']
    CHECK (bot_modes <@ ARRAY['adaptive', 'digest', 'matching']),

    -- Webhook and authentication
    webhook_url TEXT NOT NULL,
    webhook_validated_at TIMESTAMPTZ,

    -- Digest settings
    digest_time TIME DEFAULT '09:00'::time,        -- Dispatch time (UTC)
    digest_keywords TEXT[] DEFAULT '{}',           -- Keywords to monitor
    digest_enabled BOOLEAN DEFAULT true,

    -- Recommendation (RFP matching) settings
    matching_enabled BOOLEAN DEFAULT true,
    matching_threshold FLOAT DEFAULT 0.75,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_teams_bot_config_team_id
  ON teams_bot_config(team_id);
CREATE INDEX idx_teams_bot_config_digest_enabled
  ON teams_bot_config(digest_enabled);

-- 1.2 Teams Bot Messages (audit trail)
CREATE TABLE IF NOT EXISTS teams_bot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) NOT NULL,

    -- Connection info
    conversation_id UUID REFERENCES vault_conversations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Message content
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    mode TEXT CHECK (mode IN ('adaptive', 'digest', 'matching')),

    -- Teams message ID (tracking)
    teams_message_id TEXT,
    teams_thread_id TEXT,

    -- Status
    delivery_status TEXT DEFAULT 'pending'
    CHECK (delivery_status IN ('pending', 'sent', 'failed', 'archived')),
    delivery_error TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_teams_bot_messages_team_id
  ON teams_bot_messages(team_id, created_at DESC);
CREATE INDEX idx_teams_bot_messages_status
  ON teams_bot_messages(delivery_status);
CREATE INDEX idx_teams_bot_messages_teams_message_id
  ON teams_bot_messages(teams_message_id) WHERE teams_message_id IS NOT NULL;

-- ============================================================================
-- 2. Extended Existing Tables
-- ============================================================================

-- 2.1 vault_messages - Context and language support
ALTER TABLE vault_messages ADD COLUMN IF NOT EXISTS
  context_embedding VECTOR(1536);  -- Context embedding for semantic search

ALTER TABLE vault_messages ADD COLUMN IF NOT EXISTS
  is_question BOOLEAN DEFAULT true;  -- true=user question, false=assistant response

ALTER TABLE vault_messages ADD COLUMN IF NOT EXISTS
  language TEXT DEFAULT 'ko'
  CHECK (language IN ('ko', 'en', 'zh', 'ja'));

-- Indexes for context queries
CREATE INDEX IF NOT EXISTS idx_vault_messages_context
  ON vault_messages(conversation_id, created_at DESC, is_question);

CREATE INDEX IF NOT EXISTS idx_vault_messages_language
  ON vault_messages(language) WHERE language != 'ko';

-- 2.2 vault_documents - Role-based access and language support
ALTER TABLE vault_documents ADD COLUMN IF NOT EXISTS
  min_required_role TEXT DEFAULT 'member'
  CHECK (min_required_role IN ('member', 'lead', 'director', 'executive', 'admin'));

ALTER TABLE vault_documents ADD COLUMN IF NOT EXISTS
  language TEXT DEFAULT 'ko'
  CHECK (language IN ('ko', 'en', 'zh', 'ja'));

ALTER TABLE vault_documents ADD COLUMN IF NOT EXISTS
  translated_from UUID REFERENCES vault_documents(id) ON DELETE SET NULL;

ALTER TABLE vault_documents ADD COLUMN IF NOT EXISTS
  is_sensitive BOOLEAN DEFAULT false;  -- Data classification

-- Indexes for permission-based queries
CREATE INDEX IF NOT EXISTS idx_vault_documents_min_required_role
  ON vault_documents(min_required_role);

CREATE INDEX IF NOT EXISTS idx_vault_documents_language
  ON vault_documents(language) WHERE language != 'ko';

CREATE INDEX IF NOT EXISTS idx_vault_documents_translated_from
  ON vault_documents(translated_from) WHERE translated_from IS NOT NULL;

-- 2.3 vault_conversations - Language and context control
ALTER TABLE vault_conversations ADD COLUMN IF NOT EXISTS
  primary_language TEXT DEFAULT 'ko'
  CHECK (primary_language IN ('ko', 'en', 'zh', 'ja'));

ALTER TABLE vault_conversations ADD COLUMN IF NOT EXISTS
  context_enabled BOOLEAN DEFAULT true;  -- Context injection toggle

-- 2.4 vault_audit_logs - Permission denial tracking
ALTER TABLE vault_audit_logs ADD COLUMN IF NOT EXISTS
  action_denied BOOLEAN DEFAULT false;  -- Denied access flag

ALTER TABLE vault_audit_logs ADD COLUMN IF NOT EXISTS
  denied_reason TEXT;  -- "insufficient_role" | "sensitive_document" | etc

ALTER TABLE vault_audit_logs ADD COLUMN IF NOT EXISTS
  user_role TEXT;  -- User role at time of access attempt

-- Index for denied access tracking
CREATE INDEX IF NOT EXISTS idx_vault_audit_logs_action_denied
  ON vault_audit_logs(action_denied) WHERE action_denied = true;

-- 2.5 users - Language preference
ALTER TABLE users ADD COLUMN IF NOT EXISTS
  preferred_language TEXT DEFAULT 'ko'
  CHECK (preferred_language IN ('ko', 'en', 'zh', 'ja'));

-- ============================================================================
-- 3. RLS Policies for New Tables
-- ============================================================================

-- Enable RLS
ALTER TABLE teams_bot_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams_bot_messages ENABLE ROW LEVEL SECURITY;

-- Teams bot config: Team members can view/edit team config
CREATE POLICY IF NOT EXISTS teams_bot_config_view_policy ON teams_bot_config
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    ) OR
    auth.jwt() ->> 'role' = 'admin'
  );

CREATE POLICY IF NOT EXISTS teams_bot_config_edit_policy ON teams_bot_config
  FOR UPDATE
  USING (
    team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role IN ('admin', 'manager')
    ) OR
    auth.jwt() ->> 'role' = 'admin'
  );

-- Teams bot messages: Users can view messages from their teams
CREATE POLICY IF NOT EXISTS teams_bot_messages_view_policy ON teams_bot_messages
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    ) OR
    user_id = auth.uid() OR
    auth.jwt() ->> 'role' = 'admin'
  );

-- ============================================================================
-- 4. Trigger for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_teams_bot_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_teams_bot_config_updated_at
  BEFORE UPDATE ON teams_bot_config
  FOR EACH ROW
  EXECUTE FUNCTION update_teams_bot_config_timestamp();

CREATE OR REPLACE FUNCTION update_teams_bot_messages_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_teams_bot_messages_updated_at
  BEFORE UPDATE ON teams_bot_messages
  FOR EACH ROW
  EXECUTE FUNCTION update_teams_bot_messages_timestamp();

-- ============================================================================
-- 5. Data Migration (backfill existing documents)
-- ============================================================================

-- Set all existing documents to member level (public)
UPDATE vault_documents
SET min_required_role = 'member'
WHERE min_required_role IS NULL;

-- Set all existing messages to Korean (default)
UPDATE vault_messages
SET language = 'ko'
WHERE language IS NULL;

COMMIT;
