-- Migration: 020_step8_feedback.sql
-- Description: Create STEP 8 feedback system for proposal review
-- Date: 2026-03-31
-- Phase: Phase 5 (STEP 8 Review)

BEGIN;

-- Create step8_feedback table for review feedback submission
CREATE TABLE IF NOT EXISTS step8_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    feedback_text TEXT NOT NULL,
    issue_ids VARCHAR[] DEFAULT '{}',  -- Array of issue IDs resolved
    submitted_by UUID NOT NULL REFERENCES users(id),
    submitted_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for efficient lookup
CREATE INDEX IF NOT EXISTS idx_step8_feedback_proposal
    ON step8_feedback(proposal_id);

CREATE INDEX IF NOT EXISTS idx_step8_feedback_submitted_at
    ON step8_feedback(proposal_id, submitted_at DESC);

-- Enable RLS
ALTER TABLE step8_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view feedback for accessible proposals
CREATE POLICY "Users can view step8 feedback for accessible proposals"
    ON step8_feedback FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = step8_feedback.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = step8_feedback.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- RLS Policy: Users can create feedback for accessible proposals
CREATE POLICY "Users can create step8 feedback for accessible proposals"
    ON step8_feedback FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = step8_feedback.proposal_id
            AND pp.user_id = auth.uid()
        )
        OR
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN organizations o ON p.organization_id = o.id
            INNER JOIN organization_members om ON o.id = om.organization_id
            WHERE p.id = step8_feedback.proposal_id
            AND om.user_id = auth.uid()
        )
    );

-- Add STEP 8 columns to proposals table if not exist
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS step8_approved BOOLEAN DEFAULT FALSE;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS step8_approved_at TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS step8_approved_by UUID REFERENCES users(id);
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS ai_issues JSONB DEFAULT '{}'::jsonb;

COMMIT;
