-- Vault AI Chat Phase 1 Week 3 Module-6 (C.3) — Bookmarks/Favorites
-- Allows users to bookmark messages, documents, and conversations
-- Design Ref: §C.3 — Bookmarks

BEGIN;

-- Create vault_bookmarks table
CREATE TABLE IF NOT EXISTS vault_bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bookmark_type TEXT NOT NULL CHECK (bookmark_type IN ('message', 'document', 'conversation')),
    target_id TEXT NOT NULL,   -- message UUID / document UUID / conversation UUID
    note TEXT,                  -- Optional user note
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Unique constraint: user cannot bookmark same target twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_vault_bookmarks_unique
    ON vault_bookmarks (user_id, bookmark_type, target_id);

-- Index for listing bookmarks by user
CREATE INDEX IF NOT EXISTS idx_vault_bookmarks_user
    ON vault_bookmarks (user_id, created_at DESC);

-- Index for filtering by type
CREATE INDEX IF NOT EXISTS idx_vault_bookmarks_type
    ON vault_bookmarks (user_id, bookmark_type);

-- Enable RLS
ALTER TABLE vault_bookmarks ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see/manage their own bookmarks
CREATE POLICY IF NOT EXISTS "Users own their bookmarks"
    ON vault_bookmarks
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Add comments
COMMENT ON TABLE vault_bookmarks IS 'User bookmarks for messages, documents, and conversations';
COMMENT ON COLUMN vault_bookmarks.bookmark_type IS 'Type of bookmarked item: message, document, or conversation';
COMMENT ON COLUMN vault_bookmarks.target_id IS 'ID of the bookmarked item (message/document/conversation UUID)';
COMMENT ON COLUMN vault_bookmarks.note IS 'Optional note or tag added by user';

COMMIT;
