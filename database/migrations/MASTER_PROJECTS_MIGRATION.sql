-- ═══════════════════════════════════════════════════════════════════════════════
-- MASTER PROJECTS 통합 마이그레이션
-- ═══════════════════════════════════════════════════════════════════════════════
-- 실행 방법:
-- 1. Supabase 콘솔 → SQL Editor
-- 2. 이 파일의 전체 내용을 복사
-- 3. SQL Editor에 붙여넣기
-- 4. "RUN" 버튼 클릭
--
-- 실행 시간: ~30초
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 1: Create master_projects table (통합 프로젝트 테이블)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS master_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,

    -- 기본 정보
    project_name TEXT NOT NULL,
    project_year INTEGER,
    start_date DATE,
    end_date DATE,
    client_name TEXT,

    -- 요약/내용
    summary TEXT,
    description TEXT,

    -- 재정
    budget_krw BIGINT,

    -- 프로젝트 유형
    project_type TEXT NOT NULL,
    CHECK (project_type IN ('historical', 'active_proposal', 'completed_proposal')),

    -- 상태 (3개 독립 변수)
    proposal_status TEXT,
    CHECK (proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED')),

    result_status TEXT,
    CHECK (result_status IN ('PENDING', 'WON', 'LOST')),

    execution_status TEXT,
    CHECK (execution_status IN ('IN_PROGRESS', 'COMPLETED')),

    -- historical 전용 필드
    legacy_idx INTEGER,
    legacy_code TEXT,

    -- proposal 연동
    proposal_id UUID REFERENCES proposals(id),

    -- 참여자 정보 (두 그룹 분리)
    actual_teams JSONB,
    actual_participants JSONB,
    proposal_teams JSONB,
    proposal_participants JSONB,

    -- 문서/자료
    document_count INTEGER DEFAULT 0,
    archive_count INTEGER DEFAULT 0,

    -- 검색 필드
    keywords TEXT[],
    embedding vector(1536),

    -- 감사
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- 제약
    UNIQUE(org_id, legacy_idx) WHERE project_type = 'historical',
    UNIQUE(proposal_id) WHERE proposal_id IS NOT NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_master_projects_org ON master_projects(org_id);
CREATE INDEX IF NOT EXISTS idx_master_projects_type ON master_projects(project_type);
CREATE INDEX IF NOT EXISTS idx_master_projects_proposal ON master_projects(proposal_id) WHERE proposal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_master_projects_year ON master_projects(project_year);
CREATE INDEX IF NOT EXISTS idx_master_projects_status ON master_projects(proposal_status, result_status, execution_status);

-- RLS (Row Level Security)
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

-- Trigger: 자동 updated_at 갱신
CREATE TRIGGER IF NOT EXISTS update_master_projects_updated_at
    BEFORE UPDATE ON master_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 2: Migrate data from intranet_projects → master_projects
-- ═══════════════════════════════════════════════════════════════════════════════

INSERT INTO master_projects (
    id, org_id, project_name, project_year, start_date, end_date,
    client_name, summary, description, budget_krw, project_type,
    proposal_status, result_status, execution_status, legacy_idx,
    legacy_code, proposal_id, actual_teams, actual_participants,
    proposal_teams, proposal_participants, document_count, archive_count,
    keywords, embedding, created_at, updated_at
)
SELECT
    id, org_id, project_name, EXTRACT(YEAR FROM COALESCE(start_date, CURRENT_DATE))::integer,
    start_date, end_date, client_name, NULL, NULL, budget_krw,
    'historical', 'RESULT_ANNOUNCED', NULL, NULL, legacy_idx, legacy_code, NULL,
    CASE WHEN team IS NOT NULL AND team != ''
        THEN jsonb_build_array(jsonb_build_object('team_id', gen_random_uuid()::text, 'team_name', team))
        ELSE jsonb_build_array()
    END,
    (
        SELECT COALESCE(jsonb_agg(participant), '[]'::jsonb)
        FROM (
            SELECT jsonb_build_object('name', manager, 'role', 'PM', 'team_id', gen_random_uuid()::text, 'years_involved', 0) AS participant
            WHERE manager IS NOT NULL AND manager != ''
            UNION ALL
            SELECT jsonb_build_object('name', attendants, 'role', 'Member', 'team_id', gen_random_uuid()::text, 'years_involved', 0)
            WHERE attendants IS NOT NULL AND attendants != ''
            UNION ALL
            SELECT jsonb_build_object('name', pm, 'role', 'PM', 'team_id', gen_random_uuid()::text, 'years_involved', 0)
            WHERE pm IS NOT NULL AND pm != ''
        ) AS participants
    ),
    NULL, NULL, 0, 0,
    keywords, NULL, COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP)
FROM intranet_projects
WHERE org_id IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 3: Add master_project_id to intranet_documents and link
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE intranet_documents
ADD COLUMN IF NOT EXISTS master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_intranet_documents_master_project ON intranet_documents(master_project_id);

UPDATE intranet_documents
SET master_project_id = mp.id
FROM master_projects mp
WHERE intranet_documents.project_id = mp.legacy_idx
  AND intranet_documents.org_id = mp.org_id
  AND mp.project_type = 'historical'
  AND intranet_documents.master_project_id IS NULL;

UPDATE intranet_documents
SET storage_path = 'projects/' || master_project_id || '/intranet-documents/' || filename
WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 4: Add master_project_id to project_archive and link
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE project_archive
ADD COLUMN IF NOT EXISTS master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_project_archive_master_project ON project_archive(master_project_id);

UPDATE project_archive
SET master_project_id = mp.id
FROM master_projects mp
WHERE project_archive.proposal_id = mp.proposal_id
  AND project_archive.org_id = mp.org_id
  AND mp.project_type IN ('active_proposal', 'completed_proposal')
  AND project_archive.master_project_id IS NULL;

UPDATE project_archive
SET storage_path = 'projects/' || master_project_id || '/proposal-archive/' || COALESCE(category, 'other') || '/' || filename
WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 5: Update statistics (document_count, archive_count)
-- ═══════════════════════════════════════════════════════════════════════════════

UPDATE master_projects mp
SET document_count = (
    SELECT COUNT(*) FROM intranet_documents
    WHERE intranet_documents.master_project_id = mp.id
)
WHERE project_type = 'historical' AND document_count = 0;

UPDATE master_projects mp
SET archive_count = (
    SELECT COUNT(*) FROM project_archive
    WHERE project_archive.master_project_id = mp.id
)
WHERE project_type IN ('active_proposal', 'completed_proposal') AND archive_count = 0;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 6: Verification
-- ═══════════════════════════════════════════════════════════════════════════════

-- 검증 결과 (콘솔에서 확인할 수 있음)
SELECT
    (SELECT COUNT(*) FROM master_projects) as total_master_projects,
    (SELECT COUNT(*) FROM intranet_documents WHERE master_project_id IS NOT NULL) as linked_documents,
    (SELECT COUNT(*) FROM project_archive WHERE master_project_id IS NOT NULL) as linked_archives
AS migration_result;
