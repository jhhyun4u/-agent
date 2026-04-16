-- Vault AI Chat Phase 1 Week 3 Module-5 (C.2) — Conversation Sharing
-- Adds share token and public visibility to conversations
-- Design Ref: §C.2 — Conversation Sharing

BEGIN;

-- Add sharing columns to vault_conversations
ALTER TABLE vault_conversations
    ADD COLUMN IF NOT EXISTS share_token TEXT UNIQUE DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

ALTER TABLE vault_conversations
ADD COLUMN IF NOT EXISTS shared_at TIMESTAMPTZ DEFAULT NULL;

-- Create index for share_token lookups (only non-null entries)
CREATE INDEX IF NOT EXISTS idx_vault_conversations_share_token
    ON vault_conversations (share_token)
    WHERE share_token IS NOT NULL;

-- Create index for filtering public conversations
CREATE INDEX IF NOT EXISTS idx_vault_conversations_is_public
    ON vault_conversations (is_public)
    WHERE is_public = TRUE;

-- Add comments for clarity
COMMENT ON COLUMN vault_conversations.share_token IS 'Unique token for sharing conversation publicly (e.g., /vault/shared/{token})';
COMMENT ON COLUMN vault_conversations.is_public IS 'Whether conversation is publicly accessible via share_token';

COMMIT;
