-- 009_proposal_files.sql
-- 프로젝트 파일 관리 체계 (GAP-1~6)
-- proposal_files: RFP 원본, 참고자료, G2B 첨부 등 프로젝트 파일 통합 관리

CREATE TABLE IF NOT EXISTS proposal_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    category        TEXT NOT NULL DEFAULT 'reference',  -- rfp | reference | attachment
    filename        TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    file_type       TEXT,
    file_size       BIGINT,
    uploaded_by     UUID REFERENCES users(id),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_proposal_files_proposal ON proposal_files(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_files_category ON proposal_files(proposal_id, category);
