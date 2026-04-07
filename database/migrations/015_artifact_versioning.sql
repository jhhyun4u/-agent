-- Migration: 015_artifact_versioning.sql
-- Description: Create artifact versioning system for node output management
-- Date: 2026-03-30
-- Phase: 1 (Core versioning storage)

BEGIN;

-- Create proposal_artifacts table (artifact versioning storage)
-- Stores all versions of artifacts produced by nodes
CREATE TABLE IF NOT EXISTS proposal_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    node_name VARCHAR NOT NULL,
    output_key VARCHAR NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    parent_node_name VARCHAR,
    parent_version INT,
    artifact_data JSONB,
    artifact_size INT,
    checksum VARCHAR,
    used_by JSONB DEFAULT '[]'::jsonb,
    created_reason VARCHAR,
    notes TEXT,
    UNIQUE(proposal_id, node_name, output_key, version),
    FOREIGN KEY (created_by) REFERENCES auth.users(id)
);

-- Create proposal_artifact_choices table (human decision history)
-- Tracks which versions humans selected when moving between nodes with conflicts
CREATE TABLE IF NOT EXISTS proposal_artifact_choices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    choice_point VARCHAR NOT NULL,
    from_node VARCHAR NOT NULL,
    to_node VARCHAR NOT NULL,
    required_input VARCHAR NOT NULL,
    available_versions JSONB,
    selected_version INT,
    decision_at TIMESTAMP,
    decided_by UUID NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (decided_by) REFERENCES auth.users(id)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_artifact_version
    ON proposal_artifacts(proposal_id, node_name, output_key, version DESC);

CREATE INDEX IF NOT EXISTS idx_artifact_active
    ON proposal_artifacts(proposal_id, is_active);

CREATE INDEX IF NOT EXISTS idx_artifact_node_name
    ON proposal_artifacts(proposal_id, node_name);

CREATE INDEX IF NOT EXISTS idx_artifact_checksum
    ON proposal_artifacts(proposal_id, checksum);

-- GIN index for used_by JSONB array (efficient dependency lookups)
CREATE INDEX IF NOT EXISTS idx_artifact_used_by_gin
    ON proposal_artifacts USING gin(used_by);

CREATE INDEX IF NOT EXISTS idx_artifact_choices_proposal
    ON proposal_artifact_choices(proposal_id, from_node, to_node);

CREATE INDEX IF NOT EXISTS idx_artifact_choices_decision
    ON proposal_artifact_choices(proposal_id, decision_at DESC);

-- Enable RLS for proposal_artifacts
ALTER TABLE proposal_artifacts ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view artifacts only if they have access to the proposal
CREATE POLICY "Users can view artifacts of accessible proposals"
    ON proposal_artifacts FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can create artifacts only if they have access to the proposal
CREATE POLICY "Users can create artifacts in accessible proposals"
    ON proposal_artifacts FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can update artifacts in accessible proposals
CREATE POLICY "Users can update artifacts in accessible proposals"
    ON proposal_artifacts FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = proposal_artifacts.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- Enable RLS for proposal_artifact_choices
ALTER TABLE proposal_artifact_choices ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view choices in accessible proposals
CREATE POLICY "Users can view artifact choices in accessible proposals"
    ON proposal_artifact_choices FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_artifact_choices.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = proposal_artifact_choices.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can create choices in accessible proposals
CREATE POLICY "Users can create artifact choices in accessible proposals"
    ON proposal_artifact_choices FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_artifact_choices.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = proposal_artifact_choices.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- Add NOT NULL constraint on artifact_data (data integrity)
-- Note: Uses ALTER COLUMN since CREATE TABLE above uses nullable JSONB.
-- If data already exists, set default before adding constraint.
ALTER TABLE proposal_artifacts
    ALTER COLUMN artifact_data SET DEFAULT '{}'::jsonb;

UPDATE proposal_artifacts SET artifact_data = '{}'::jsonb WHERE artifact_data IS NULL;

ALTER TABLE proposal_artifacts
    ALTER COLUMN artifact_data SET NOT NULL;

COMMIT;
