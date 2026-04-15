-- PHASE 1: Create master_projects table
-- Supabase SQL Editor에서 실행하세요

CREATE TABLE IF NOT EXISTS master_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    project_name TEXT NOT NULL,
    project_year INTEGER,
    start_date DATE,
    end_date DATE,
    client_name TEXT,
    summary TEXT,
    description TEXT,
    budget_krw BIGINT,
    project_type TEXT NOT NULL,
    CHECK (project_type IN ('historical', 'active_proposal', 'completed_proposal')),
    proposal_status TEXT,
    CHECK (proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED')),
    result_status TEXT,
    CHECK (result_status IN ('PENDING', 'WON', 'LOST')),
    execution_status TEXT,
    CHECK (execution_status IN ('IN_PROGRESS', 'COMPLETED')),
    legacy_idx INTEGER,
    legacy_code TEXT,
    proposal_id UUID REFERENCES proposals(id),
    actual_teams JSONB,
    actual_participants JSONB,
    proposal_teams JSONB,
    proposal_participants JSONB,
    document_count INTEGER DEFAULT 0,
    archive_count INTEGER DEFAULT 0,
    keywords TEXT[],
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Unique constraint (별도 정의)
CREATE UNIQUE INDEX IF NOT EXISTS idx_master_projects_org_legacy_idx
    ON master_projects(org_id, legacy_idx)
    WHERE project_type = 'historical';

CREATE UNIQUE INDEX IF NOT EXISTS idx_master_projects_proposal_id
    ON master_projects(proposal_id)
    WHERE proposal_id IS NOT NULL;

-- 일반 인덱스
CREATE INDEX IF NOT EXISTS idx_master_projects_org ON master_projects(org_id);
CREATE INDEX IF NOT EXISTS idx_master_projects_type ON master_projects(project_type);
CREATE INDEX IF NOT EXISTS idx_master_projects_proposal ON master_projects(proposal_id) WHERE proposal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_master_projects_year ON master_projects(project_year);
CREATE INDEX IF NOT EXISTS idx_master_projects_status ON master_projects(proposal_status, result_status, execution_status);

-- RLS 설정
ALTER TABLE master_projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "master_projects_select_own_org"
    ON master_projects FOR SELECT
    USING (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

CREATE POLICY IF NOT EXISTS "master_projects_insert_own_org"
    ON master_projects FOR INSERT
    WITH CHECK (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

CREATE POLICY IF NOT EXISTS "master_projects_update_own_org"
    ON master_projects FOR UPDATE
    USING (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin')
    WITH CHECK (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

-- Trigger 생성 (이미 존재하면 무시)
CREATE TRIGGER IF NOT EXISTS update_master_projects_updated_at
    BEFORE UPDATE ON master_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
