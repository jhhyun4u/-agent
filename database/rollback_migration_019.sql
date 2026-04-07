-- ============================================
-- Rollback for Migration 019: Unified State System
-- ============================================

-- Drop indexes first
DROP INDEX IF EXISTS idx_proposal_timelines_created_at;
DROP INDEX IF EXISTS idx_proposal_timelines_event_type;
DROP INDEX IF EXISTS idx_proposal_timelines_proposal_id;

-- Drop new table
DROP TABLE IF EXISTS proposal_timelines CASCADE;

-- Remove timestamp columns from proposals
ALTER TABLE proposals
  DROP COLUMN IF EXISTS created_at,
  DROP COLUMN IF EXISTS started_at,
  DROP COLUMN IF EXISTS last_activity_at,
  DROP COLUMN IF EXISTS completed_at;

-- Remove ai_task_logs constraint if needed (optional)
-- Uncomment if needed, but be careful as it might be referenced elsewhere
-- ALTER TABLE ai_task_logs
--   DROP CONSTRAINT IF EXISTS ai_task_logs_status_check;

-- ============================================
-- Rollback Complete
-- ============================================
-- All tables and columns have been removed.
-- The database schema reverts to pre-migration state.
