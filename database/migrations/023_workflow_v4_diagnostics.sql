-- Migration: 023_workflow_v4_diagnostics.sql
-- Description: Add v4.0 diagnostic and gap analysis result columns
-- Date: 2026-04-10
-- Phase: v4.0 Workflow Restructuring

BEGIN;

-- ============================================
-- STEP 4A: 섹션별 진단 + 갭 분석 결과 저장
-- ============================================

-- 1. proposals 테이블에 진단/갭 분석 결과 컬럼 추가
ALTER TABLE proposals
ADD COLUMN IF NOT EXISTS diagnosis_result JSONB,
ADD COLUMN IF NOT EXISTS gap_report JSONB,
ADD COLUMN IF NOT EXISTS diagnosis_summary TEXT;

-- 2. 별도 테이블: 섹션별 진단 이력 (트렌드 추적용)
CREATE TABLE IF NOT EXISTS section_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL,
    section_title TEXT,
    section_index INTEGER,
    -- 4축 진단 결과
    compliance_ok BOOLEAN,
    storyline_gap TEXT,
    evidence_score DECIMAL(5,2),
    diff_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    -- 상세 분석
    issues JSONB DEFAULT '[]'::jsonb,  -- 식별된 문제점 목록
    recommendation TEXT,  -- approve | needs_revision | needs_rework
    -- 감사 추적
    diagnosed_at TIMESTAMPTZ DEFAULT NOW(),
    diagnosed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (diagnosed_by) REFERENCES auth.users(id)
);

-- 3. 별도 테이블: 제안서 갭 분석 (스토리라인 vs 실제 내용)
CREATE TABLE IF NOT EXISTS proposal_gap_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    -- 갭 분석 결과
    missing_points JSONB DEFAULT '[]'::jsonb,  -- 빠진 핵심 포인트
    logic_gaps JSONB DEFAULT '[]'::jsonb,  -- 논리적 연결 고리 단절
    weak_transitions JSONB DEFAULT '[]'::jsonb,  -- 섹션간 전환 약함
    inconsistencies JSONB DEFAULT '[]'::jsonb,  -- 메시지 불일관성
    overall_assessment TEXT,  -- 전체 평가 (한 문장)
    recommended_actions JSONB DEFAULT '[]'::jsonb,  -- 권장 조치 목록
    -- 상태 관리
    status TEXT DEFAULT 'pending',  -- pending | approved | rework_section | rework_strategy
    -- 감사 추적
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    analyzed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (analyzed_by) REFERENCES auth.users(id)
);

-- ============================================
-- 인덱스 생성 (조회 성능 최적화)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_section_diagnostics_proposal
    ON section_diagnostics(proposal_id);

CREATE INDEX IF NOT EXISTS idx_section_diagnostics_section
    ON section_diagnostics(proposal_id, section_id);

CREATE INDEX IF NOT EXISTS idx_section_diagnostics_score
    ON section_diagnostics(proposal_id, overall_score DESC);

CREATE INDEX IF NOT EXISTS idx_proposal_gap_analyses_proposal
    ON proposal_gap_analyses(proposal_id);

CREATE INDEX IF NOT EXISTS idx_proposal_gap_analyses_status
    ON proposal_gap_analyses(proposal_id, status);

-- RLS 설정 (Supabase Row Level Security)
-- section_diagnostics
ALTER TABLE section_diagnostics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view diagnostics of accessible proposals"
    ON section_diagnostics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = section_diagnostics.proposal_id
            AND pp.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert diagnostics for accessible proposals"
    ON section_diagnostics FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = section_diagnostics.proposal_id
            AND pp.user_id = auth.uid()
        )
    );

-- proposal_gap_analyses
ALTER TABLE proposal_gap_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view gap analyses of accessible proposals"
    ON proposal_gap_analyses FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_gap_analyses.proposal_id
            AND pp.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert gap analyses for accessible proposals"
    ON proposal_gap_analyses FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            INNER JOIN proposal_participants pp ON p.id = pp.proposal_id
            WHERE p.id = proposal_gap_analyses.proposal_id
            AND pp.user_id = auth.uid()
        )
    );

-- ============================================
-- 코멘트 추가 (문서화)
-- ============================================

COMMENT ON TABLE section_diagnostics IS
    'STEP 4A: 섹션별 품질 진단 결과 (4축 평가: compliance, storyline, evidence, differentiation)';

COMMENT ON TABLE proposal_gap_analyses IS
    'STEP 4A: 제안서 갭 분석 결과 (plan_story vs 실제 작성 내용 비교)';

COMMENT ON COLUMN proposals.diagnosis_result IS
    'STEP 4A: 최종 진단 결과 (DiagnosisResult JSONB)';

COMMENT ON COLUMN proposals.gap_report IS
    'STEP 4A: 갭 분석 결과 (GapReport JSONB)';

COMMIT;
