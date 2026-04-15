-- Migration: 024_knowledge_management.sql
-- Purpose: Create knowledge management system tables for llm-wiki feature
-- Created: 2026-04-13

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLE: knowledge_metadata
-- Purpose: Classification + freshness scoring for knowledge chunks
-- ============================================================================
CREATE TABLE IF NOT EXISTS knowledge_metadata (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  knowledge_type VARCHAR(50) NOT NULL CHECK (knowledge_type IN (
    'capability',
    'client_intel',
    'market_price',
    'lesson_learned'
  )),
  classification_confidence DECIMAL(3,2) DEFAULT 0.0 CHECK (classification_confidence >= 0.0 AND classification_confidence <= 1.0),
  is_deprecated BOOLEAN DEFAULT false,
  freshness_score DECIMAL(5,2) DEFAULT 100 CHECK (freshness_score >= 0.0 AND freshness_score <= 100.0),
  last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  multi_type_ids UUID[] DEFAULT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for knowledge_metadata
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata_chunk_id
  ON knowledge_metadata(chunk_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata_type
  ON knowledge_metadata(knowledge_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata_deprecated
  ON knowledge_metadata(is_deprecated);
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata_freshness
  ON knowledge_metadata(freshness_score);
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata_created_at
  ON knowledge_metadata(created_at DESC);

-- ============================================================================
-- TABLE: knowledge_sharing_audit
-- Purpose: Track team → org knowledge sharing decisions and audit trail
-- ============================================================================
CREATE TABLE IF NOT EXISTS knowledge_sharing_audit (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  shared_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  shared_from_team_id UUID NOT NULL,
  shared_to_org BOOLEAN DEFAULT false,
  shared_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  reason VARCHAR(500),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for knowledge_sharing_audit
CREATE INDEX IF NOT EXISTS idx_sharing_audit_chunk
  ON knowledge_sharing_audit(chunk_id);
CREATE INDEX IF NOT EXISTS idx_sharing_audit_team
  ON knowledge_sharing_audit(shared_from_team_id);
CREATE INDEX IF NOT EXISTS idx_sharing_audit_shared_to_org
  ON knowledge_sharing_audit(shared_to_org);
CREATE INDEX IF NOT EXISTS idx_sharing_audit_created_at
  ON knowledge_sharing_audit(created_at DESC);

-- ============================================================================
-- TABLE MODIFICATION: document_chunks
-- Purpose: Track if document has been classified for knowledge system
-- ============================================================================
ALTER TABLE document_chunks
  ADD COLUMN IF NOT EXISTS is_knowledge_indexed BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_document_chunks_knowledge_indexed
  ON document_chunks(is_knowledge_indexed);

-- ============================================================================
-- RLS POLICIES: knowledge_metadata
-- ============================================================================

-- Enable RLS on knowledge_metadata
ALTER TABLE knowledge_metadata ENABLE ROW LEVEL SECURITY;

-- Policy 1: Team Knowledge Access (Default)
-- Users can see knowledge from their own team
CREATE POLICY IF NOT EXISTS "team_knowledge_access" ON knowledge_metadata
  FOR SELECT
  USING (
    -- User can see team's own knowledge
    EXISTS (
      SELECT 1 FROM document_chunks dc
      JOIN documents d ON dc.document_id = d.id
      WHERE dc.id = knowledge_metadata.chunk_id
        AND d.team_id = (auth.jwt()->>'team_id')::UUID
    )
  );

-- Policy 2: Org Knowledge Access (Shared)
-- Users can see knowledge explicitly shared org-wide
-- OR knowledge from their own team
CREATE POLICY IF NOT EXISTS "org_knowledge_access" ON knowledge_metadata
  FOR SELECT
  USING (
    -- User can see knowledge marked as shared org-wide
    EXISTS (
      SELECT 1 FROM knowledge_sharing_audit ksa
      WHERE ksa.chunk_id = knowledge_metadata.chunk_id
        AND ksa.shared_to_org = true
    )
    OR
    -- User can see knowledge from their own team
    EXISTS (
      SELECT 1 FROM document_chunks dc
      JOIN documents d ON dc.document_id = d.id
      WHERE dc.id = knowledge_metadata.chunk_id
        AND d.team_id = (auth.jwt()->>'team_id')::UUID
    )
  );

-- Policy 3: Insert Permission for Knowledge Manager Role
CREATE POLICY IF NOT EXISTS "knowledge_manager_insert" ON knowledge_metadata
  FOR INSERT
  WITH CHECK (
    -- Only users with knowledge_manager role can insert
    auth.jwt()->>'role' = 'knowledge_manager'
    OR auth.jwt()->>'role' = 'admin'
  );

-- Policy 4: Update Permission for Knowledge Manager Role
CREATE POLICY IF NOT EXISTS "knowledge_manager_update" ON knowledge_metadata
  FOR UPDATE
  USING (
    -- Only users with knowledge_manager role can update
    auth.jwt()->>'role' = 'knowledge_manager'
    OR auth.jwt()->>'role' = 'admin'
  )
  WITH CHECK (
    -- Only users with knowledge_manager role can update
    auth.jwt()->>'role' = 'knowledge_manager'
    OR auth.jwt()->>'role' = 'admin'
  );

-- ============================================================================
-- RLS POLICIES: knowledge_sharing_audit
-- ============================================================================

-- Enable RLS on knowledge_sharing_audit
ALTER TABLE knowledge_sharing_audit ENABLE ROW LEVEL SECURITY;

-- Policy 1: Read audit trail (team can see their own audit trail)
CREATE POLICY IF NOT EXISTS "team_audit_read" ON knowledge_sharing_audit
  FOR SELECT
  USING (
    shared_from_team_id = (auth.jwt()->>'team_id')::UUID
    OR auth.jwt()->>'role' = 'admin'
  );

-- Policy 2: Knowledge managers can insert audit records
CREATE POLICY IF NOT EXISTS "knowledge_manager_audit_insert" ON knowledge_sharing_audit
  FOR INSERT
  WITH CHECK (
    auth.jwt()->>'role' = 'knowledge_manager'
    OR auth.jwt()->>'role' = 'admin'
  );

-- ============================================================================
-- FUNCTION: Update freshness score based on document age
-- Purpose: Auto-decay freshness score for documents older than 2 years
-- ============================================================================
CREATE OR REPLACE FUNCTION update_freshness_score()
RETURNS TRIGGER AS $$
BEGIN
  -- If document is more than 2 years old and not deprecated
  -- Auto-reduce freshness score
  IF NOT NEW.is_deprecated THEN
    IF (NOW() - NEW.created_at) > INTERVAL '2 years' THEN
      NEW.freshness_score := 50;
    ELSIF (NOW() - NEW.created_at) > INTERVAL '1 year' THEN
      NEW.freshness_score := 75;
    ELSE
      NEW.freshness_score := 100;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update freshness score on insert
DROP TRIGGER IF EXISTS trigger_update_freshness_on_insert ON knowledge_metadata;
CREATE TRIGGER trigger_update_freshness_on_insert
  BEFORE INSERT ON knowledge_metadata
  FOR EACH ROW
  EXECUTE FUNCTION update_freshness_score();

-- Trigger: Auto-update freshness score on update
DROP TRIGGER IF EXISTS trigger_update_freshness_on_update ON knowledge_metadata;
CREATE TRIGGER trigger_update_freshness_on_update
  BEFORE UPDATE ON knowledge_metadata
  FOR EACH ROW
  EXECUTE FUNCTION update_freshness_score();

-- ============================================================================
-- COMMENT: Document changes
-- ============================================================================
COMMENT ON TABLE knowledge_metadata IS
  'Stores knowledge classification and freshness metadata for document chunks.
   Used by llm-wiki feature for semantic search and recommendations.';

COMMENT ON TABLE knowledge_sharing_audit IS
  'Audit trail for knowledge sharing decisions. Tracks when and why knowledge
   is shared from team scope to organization scope.';

COMMENT ON COLUMN knowledge_metadata.knowledge_type IS
  'Classification type: capability (technical expertise),
   client_intel (client information), market_price (pricing data),
   lesson_learned (project lessons)';

COMMENT ON COLUMN knowledge_metadata.classification_confidence IS
  'LLM confidence score (0.0-1.0) for the classification.
   Used for filtering low-confidence classifications.';

COMMENT ON COLUMN knowledge_metadata.freshness_score IS
  'Freshness indicator (0-100): 100=recent, 50=1-2 years old,
   <50=deprecated or >2 years old. Auto-updated by trigger.';
