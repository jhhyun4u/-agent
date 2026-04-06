-- 012_project_archive.sql
-- 프로젝트 아카이브: 중간 산출물 파일 관리 + 마스터 인덱스
-- 모든 중요 산출물을 Supabase Storage에 파일로 보관하고 DB에서 추적

-- ═══════════════════════════════════════════
-- 1. project_archive 테이블
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS project_archive (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- 분류
    category        TEXT NOT NULL
        CHECK (category IN (
            'rfp', 'analysis', 'strategy', 'plan',
            'proposal', 'presentation', 'bidding',
            'review', 'submission', 'reference'
        )),
    doc_type        TEXT NOT NULL,
        -- rfp: rfp_original, rfp_raw_text
        -- analysis: rfp_analysis, compliance_matrix, go_no_go, research_brief
        -- strategy: strategy, bid_plan, evaluation_simulation
        -- plan: team_plan, schedule, storyline, price_plan
        -- proposal: proposal_full_md, proposal_docx, proposal_hwpx
        -- presentation: ppt_slides_md, presentation_strategy, ppt_pptx
        -- bidding: cost_sheet
        -- review: feedback_history
        -- submission: (submission_documents 연동)
        -- reference: (proposal_files 연동)

    -- 메타
    title           TEXT NOT NULL,
    description     TEXT,
    file_format     TEXT NOT NULL,          -- md, txt, docx, hwpx, pptx, pdf, json, xlsx
    storage_path    TEXT,                   -- Supabase Storage 경로 (null = 아직 미업로드)
    file_size       BIGINT,

    -- 버전 관리
    version         INTEGER DEFAULT 1,
    is_latest       BOOLEAN DEFAULT TRUE,   -- 최신 버전 여부

    -- 출처 추적
    source          TEXT DEFAULT 'ai'       -- ai | human | system
        CHECK (source IN ('ai', 'human', 'system')),
    graph_step      TEXT,                   -- LangGraph 노드명 (rfp_analyze, strategy_generate 등)

    -- 감사
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_project_archive_proposal ON project_archive(proposal_id);
CREATE INDEX idx_project_archive_category ON project_archive(proposal_id, category);
CREATE INDEX idx_project_archive_doc_type ON project_archive(proposal_id, doc_type, is_latest);
CREATE UNIQUE INDEX idx_project_archive_latest ON project_archive(proposal_id, doc_type)
    WHERE is_latest = TRUE;

-- updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_project_archive_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_archive_updated_at
    BEFORE UPDATE ON project_archive
    FOR EACH ROW EXECUTE FUNCTION update_project_archive_updated_at();

-- RLS
ALTER TABLE project_archive ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_archive_select ON project_archive
    FOR SELECT USING (
        proposal_id IN (
            SELECT id FROM proposals WHERE org_id = (
                SELECT org_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY project_archive_insert ON project_archive
    FOR INSERT WITH CHECK (
        proposal_id IN (
            SELECT id FROM proposals WHERE org_id = (
                SELECT org_id FROM users WHERE id = auth.uid()
            )
        )
    );

CREATE POLICY project_archive_update ON project_archive
    FOR UPDATE USING (
        proposal_id IN (
            SELECT id FROM proposals WHERE org_id = (
                SELECT org_id FROM users WHERE id = auth.uid()
            )
        )
    );

-- ═══════════════════════════════════════════
-- 2. proposals 테이블 확장: 산출내역서 경로 추가
-- ═══════════════════════════════════════════

ALTER TABLE proposals
    ADD COLUMN IF NOT EXISTS storage_path_cost_sheet TEXT,
    ADD COLUMN IF NOT EXISTS archive_snapshot_at TIMESTAMPTZ;

-- ═══════════════════════════════════════════
-- 3. 기존 proposal_files에 archive 연동 컬럼 추가
-- ═══════════════════════════════════════════

ALTER TABLE proposal_files
    ADD COLUMN IF NOT EXISTS archive_id UUID REFERENCES project_archive(id);
