-- 011_three_streams.sql
-- 3-Stream 병행 업무: submission_documents + stream_progress + org_document_templates
-- + proposals 테이블 확장

-- ── Stream 3: 제출서류 체크리스트 ──

CREATE TABLE IF NOT EXISTS submission_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    doc_category TEXT NOT NULL DEFAULT 'other'
        CHECK (doc_category IN ('proposal', 'qualification', 'certification', 'financial', 'other')),
    required_format TEXT DEFAULT '자유'
        CHECK (required_format IN ('HWPX', 'PDF', '원본', '사본', '자유')),
    required_copies INT DEFAULT 1,
    source TEXT DEFAULT 'manual'
        CHECK (source IN ('rfp_extracted', 'manual', 'template_matched')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'assigned', 'in_progress', 'uploaded', 'verified', 'rejected', 'not_applicable', 'expired')),
    assignee_id UUID REFERENCES users(id),
    deadline TIMESTAMPTZ,
    priority TEXT DEFAULT 'medium'
        CHECK (priority IN ('high', 'medium', 'low')),
    notes TEXT,
    file_path TEXT,
    file_name TEXT,
    file_size BIGINT,
    file_format TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMPTZ,
    rejection_reason TEXT,
    sort_order INT DEFAULT 0,
    rfp_reference TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_submission_documents_proposal ON submission_documents(proposal_id);
CREATE INDEX IF NOT EXISTS idx_submission_documents_status ON submission_documents(status);
CREATE INDEX IF NOT EXISTS idx_submission_documents_assignee ON submission_documents(assignee_id);

-- ── 스트림 진행 상태 ──

CREATE TABLE IF NOT EXISTS stream_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    stream TEXT NOT NULL
        CHECK (stream IN ('proposal', 'bidding', 'documents')),
    status TEXT NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'blocked', 'completed', 'error')),
    progress_pct INT DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100),
    current_phase TEXT,
    blocked_reason TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proposal_id, stream)
);

CREATE INDEX IF NOT EXISTS idx_stream_progress_proposal ON stream_progress(proposal_id);

-- ── 조직 공통 서류 템플릿 ──

CREATE TABLE IF NOT EXISTS org_document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    doc_category TEXT NOT NULL DEFAULT 'qualification'
        CHECK (doc_category IN ('proposal', 'qualification', 'certification', 'financial', 'other')),
    required_format TEXT DEFAULT '사본',
    file_path TEXT,
    file_name TEXT,
    file_size BIGINT,
    valid_from DATE,
    valid_until DATE,
    auto_include BOOLEAN DEFAULT TRUE,
    uploaded_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, doc_type)
);

CREATE INDEX IF NOT EXISTS idx_org_document_templates_org ON org_document_templates(org_id);

-- ── proposals 테이블 확장 ──

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS streams_ready JSONB
    DEFAULT '{"proposal": false, "bidding": false, "documents": false}';
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS submission_gate_status TEXT DEFAULT 'pending';

-- ── RLS ──

ALTER TABLE submission_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE stream_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_document_templates ENABLE ROW LEVEL SECURITY;

-- service_role 전체 접근
CREATE POLICY IF NOT EXISTS "service_role_submission_documents" ON submission_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_stream_progress" ON stream_progress
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS "service_role_org_document_templates" ON org_document_templates
    FOR ALL TO service_role USING (true) WITH CHECK (true);
