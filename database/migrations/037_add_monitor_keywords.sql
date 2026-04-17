-- Migration 037: Add monitor_keywords column to teams table
-- Purpose: Enable keyword-based bid monitoring for teams
-- Date: 2026-04-17

-- Add monitor_keywords column if it doesn't exist
ALTER TABLE teams
ADD COLUMN IF NOT EXISTS monitor_keywords text[] DEFAULT '{}';

-- Add comment
COMMENT ON COLUMN teams.monitor_keywords IS 'Array of keywords for automatic bid monitoring';

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_teams_monitor_keywords
ON teams USING GIN (monitor_keywords);

-- Log migration
INSERT INTO public._schema_migrations (version, name, description)
VALUES (
  '037',
  'add_monitor_keywords',
  'Add monitor_keywords column to teams table for keyword-based bid filtering'
)
ON CONFLICT (version) DO NOTHING;
