-- Sprint 1 Phase 2: Team Comments & Feedback
-- Enables team collaboration through global/step/inline comments with emoji reactions

-- ============================================
-- Comments Table
-- ============================================

CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Association
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
  proposal_step TEXT,  -- e.g., 'step_1', 'step_2', 'step_3' for step-scoped comments
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Scope & Position
  scope TEXT NOT NULL,  -- 'global' | 'step' | 'inline'
  inline_position INTEGER,  -- For inline comments: character offset in artifact content

  -- Author & Content
  author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,  -- Markdown support
  edited_count INTEGER NOT NULL DEFAULT 0,

  -- Soft Delete & Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ,

  -- Constraints
  CONSTRAINT valid_scope CHECK (scope IN ('global', 'step', 'inline')),
  CONSTRAINT inline_position_required CHECK (
    (scope = 'inline' AND inline_position IS NOT NULL) OR scope != 'inline'
  )
);

-- ============================================
-- Emoji Reactions Table
-- ============================================

CREATE TABLE emoji_reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Association
  comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Reaction
  emoji VARCHAR(10) NOT NULL,  -- e.g., '👍', '❤️', '🎉', '🤔'

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Constraints
  CONSTRAINT unique_user_emoji_per_comment UNIQUE (comment_id, user_id, emoji),
  CONSTRAINT valid_emoji CHECK (emoji ~ '^[\p{Emoji}]+$')
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Comments indexes
CREATE INDEX idx_comments_proposal ON comments(proposal_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_proposal_scope ON comments(proposal_id, scope) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_proposal_step ON comments(proposal_id, proposal_step) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_author ON comments(author_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_org ON comments(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_created ON comments(created_at DESC) WHERE deleted_at IS NULL;

-- Reactions indexes
CREATE INDEX idx_emoji_reactions_comment ON emoji_reactions(comment_id);
CREATE INDEX idx_emoji_reactions_user ON emoji_reactions(user_id);
CREATE INDEX idx_emoji_reactions_org ON emoji_reactions(org_id);

-- ============================================
-- Triggers for Auto-Update Timestamps
-- ============================================

CREATE OR REPLACE FUNCTION update_comments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_comments_updated_at
BEFORE UPDATE ON comments
FOR EACH ROW
EXECUTE FUNCTION update_comments_updated_at();

-- ============================================
-- Views for Comment Analytics
-- ============================================

-- Comments with reaction counts and author info
CREATE VIEW v_comments_with_reactions AS
SELECT
  c.id,
  c.proposal_id,
  c.proposal_step,
  c.scope,
  c.inline_position,
  c.author_id,
  u.email as author_email,
  u.name as author_name,
  c.content,
  c.created_at,
  c.updated_at,
  c.edited_count,
  COUNT(DISTINCT er.id) as reaction_count,
  JSON_BUILD_OBJECT(
    '👍', COUNT(CASE WHEN er.emoji = '👍' THEN 1 END),
    '❤️', COUNT(CASE WHEN er.emoji = '❤️' THEN 1 END),
    '🎉', COUNT(CASE WHEN er.emoji = '🎉' THEN 1 END),
    '🤔', COUNT(CASE WHEN er.emoji = '🤔' THEN 1 END),
    '👏', COUNT(CASE WHEN er.emoji = '👏' THEN 1 END)
  ) as reaction_summary
FROM comments c
LEFT JOIN users u ON c.author_id = u.id
LEFT JOIN emoji_reactions er ON c.id = er.comment_id
WHERE c.deleted_at IS NULL
GROUP BY c.id, u.id;

-- Comment statistics by proposal
CREATE VIEW v_comment_stats_by_proposal AS
SELECT
  c.proposal_id,
  COUNT(DISTINCT c.id) as total_comments,
  COUNT(DISTINCT c.author_id) as unique_authors,
  COUNT(DISTINCT CASE WHEN c.scope = 'global' THEN c.id END) as global_count,
  COUNT(DISTINCT CASE WHEN c.scope = 'step' THEN c.id END) as step_count,
  COUNT(DISTINCT CASE WHEN c.scope = 'inline' THEN c.id END) as inline_count,
  COUNT(DISTINCT er.id) as total_reactions,
  MAX(c.created_at) as last_comment_at
FROM comments c
LEFT JOIN emoji_reactions er ON c.id = er.comment_id
WHERE c.deleted_at IS NULL
GROUP BY c.proposal_id;

-- ============================================
-- RLS Policies
-- ============================================

ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE emoji_reactions ENABLE ROW LEVEL SECURITY;

-- Comments: Select if user is in same org and comment not deleted
CREATE POLICY comments_select_same_org ON comments
FOR SELECT
USING (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  ) AND deleted_at IS NULL
);

-- Comments: Insert if user is in same org and is proposal member
CREATE POLICY comments_insert_same_org ON comments
FOR INSERT
WITH CHECK (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
  AND author_id = auth.uid()
  AND proposal_id IN (
    SELECT id FROM proposals WHERE org_id = (
      SELECT org_id FROM users WHERE id = auth.uid()
    )
  )
);

-- Comments: Update own comments only
CREATE POLICY comments_update_own ON comments
FOR UPDATE
USING (
  author_id = auth.uid() AND deleted_at IS NULL
)
WITH CHECK (
  author_id = auth.uid()
);

-- Comments: Delete own comments (soft delete via trigger)
CREATE POLICY comments_delete_own ON comments
FOR DELETE
USING (
  author_id = auth.uid()
);

-- Reactions: Select
CREATE POLICY reactions_select_same_org ON emoji_reactions
FOR SELECT
USING (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
);

-- Reactions: Insert
CREATE POLICY reactions_insert_same_org ON emoji_reactions
FOR INSERT
WITH CHECK (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
  AND user_id = auth.uid()
);

-- Reactions: Delete own reactions
CREATE POLICY reactions_delete_own ON emoji_reactions
FOR DELETE
USING (
  user_id = auth.uid()
);

-- ============================================
-- Migration Status
-- ============================================

-- Log this migration
INSERT INTO migration_log (version, description, executed_at)
VALUES (
  '036',
  'Add comments and emoji_reactions tables with RLS for Sprint 1 Phase 2',
  now()
) ON CONFLICT DO NOTHING;
