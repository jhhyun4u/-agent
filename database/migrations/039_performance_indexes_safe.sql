-- Task #2: Performance indexes (Supabase-safe version)
-- Note: Removed CONCURRENTLY for Supabase SQL Editor compatibility
-- Each index should be created separately

-- 1. Proposals sorting index
CREATE INDEX IF NOT EXISTS idx_proposals_created_at_desc
ON public.proposals(created_at DESC);

-- Verify
SELECT indexname FROM pg_indexes 
WHERE tablename = 'proposals' AND indexname = 'idx_proposals_created_at_desc';
