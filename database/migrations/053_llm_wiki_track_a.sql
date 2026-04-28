-- Migration 053: LLM-Wiki Track A
-- Feature: wiki_suggestion_node integration (evaluation_feedbacks + wiki columns)
-- Date: 2026-04-28

-- 1. evaluation_feedbacks 테이블 생성
CREATE TABLE IF NOT EXISTS evaluation_feedbacks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id VARCHAR(255),
  proposal_id VARCHAR(255),
  section_id VARCHAR(255),
  round INTEGER,
  human_feedback TEXT,
  confidence_feedback TEXT,
  wiki_suggestion_accepted BOOLEAN,
  wiki_suggestion_id VARCHAR(255),
  metrics_before JSONB,
  metrics_after JSONB,
  created_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT idx_eval_feedback_proposal UNIQUE (proposal_id, section_id, round)
);

CREATE INDEX IF NOT EXISTS idx_evaluation_feedbacks_proposal
  ON evaluation_feedbacks(proposal_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_feedbacks_section
  ON evaluation_feedbacks(proposal_id, section_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_feedbacks_org
  ON evaluation_feedbacks(org_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_feedbacks_wiki_accepted
  ON evaluation_feedbacks(wiki_suggestion_accepted);

-- 2. proposal_sections 에 wiki 컬럼 추가
ALTER TABLE proposal_sections
  ADD COLUMN IF NOT EXISTS wiki_suggestion_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS wiki_suggestions JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS wiki_suggestion_accepted BOOLEAN;

-- 3. section_diagnostics 에 wiki 컬럼 추가
ALTER TABLE section_diagnostics
  ADD COLUMN IF NOT EXISTS wiki_suggestion_id VARCHAR(255);

-- 검증 쿼리 (실행 후 확인)
-- SELECT COUNT(*) FROM evaluation_feedbacks;
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'proposal_sections' AND column_name LIKE 'wiki%';
