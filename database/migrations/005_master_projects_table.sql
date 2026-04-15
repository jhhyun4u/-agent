-- Migration: Create master_projects table (SSOT for all projects)
-- Date: 2026-04-11
-- Purpose: Unified table integrating historical intranet_projects and proposal archives
-- Schema: UUID-centered (immutable to org changes), 3-state status variables

CREATE TABLE master_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,

    -- 기본 정보
    project_name TEXT NOT NULL,
    project_year INTEGER,
    start_date DATE,
    end_date DATE,
    client_name TEXT,

    -- 요약/내용
    summary TEXT,                  -- 주요 내용 요약 (제안 최종 제출시점 입력)
    description TEXT,

    -- 기간
    budget_krw BIGINT,

    -- 프로젝트 유형
    project_type TEXT NOT NULL,    -- 'historical' | 'active_proposal' | 'completed_proposal'
    CHECK (project_type IN ('historical', 'active_proposal', 'completed_proposal')),

    -- 상태 (3개 독립 변수)
    proposal_status TEXT,          -- DRAFT | SUBMITTED | RESULT_ANNOUNCED (제안 상태)
    CHECK (proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED')),

    result_status TEXT,            -- PENDING | WON | LOST (수주 결과, active_proposal만)
    CHECK (result_status IN ('PENDING', 'WON', 'LOST')),

    execution_status TEXT,         -- IN_PROGRESS | COMPLETED (수행 상태, result_status=WON인 경우만)
    CHECK (execution_status IN ('IN_PROGRESS', 'COMPLETED')),

    -- === historical 프로젝트 전용 필드 ===
    legacy_idx INTEGER,            -- MSSQL idx_no
    legacy_code TEXT,              -- MSSQL pr_code

    -- === proposal 연동 필드 ===
    proposal_id UUID REFERENCES proposals(id),  -- active/completed만 존재

    -- === 참여자 정보 (두 그룹 분리!) ===
    -- 그룹 1: 용역수행팀 + 팀원 (intranet_projects)
    actual_teams JSONB,            -- [{team_id, team_name}] (1개 이상)
    actual_participants JSONB,     -- [{name, role, team_id, years_involved}] (여러명)

    -- 그룹 2: 제안팀 + 제안작업참여자 (proposals)
    proposal_teams JSONB,          -- [{team_id, team_name}] (1개 이상)
    proposal_participants JSONB,   -- [{user_id, name, role, team_id}] (여러명, 내부 직원 ID)

    -- 문서 & 자료
    document_count INTEGER DEFAULT 0,
    archive_count INTEGER DEFAULT 0,  -- proposals의 산출물 수

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
CREATE INDEX idx_master_projects_org ON master_projects(org_id);
CREATE INDEX idx_master_projects_type ON master_projects(project_type);
CREATE INDEX idx_master_projects_proposal ON master_projects(proposal_id) WHERE proposal_id IS NOT NULL;
CREATE INDEX idx_master_projects_year ON master_projects(project_year);
CREATE INDEX idx_master_projects_status ON master_projects(proposal_status, result_status, execution_status);
CREATE INDEX idx_master_projects_embedding ON master_projects USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS (Row Level Security)
ALTER TABLE master_projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "master_projects_select_own_org"
    ON master_projects FOR SELECT
    USING (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

CREATE POLICY "master_projects_insert_own_org"
    ON master_projects FOR INSERT
    WITH CHECK (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

CREATE POLICY "master_projects_update_own_org"
    ON master_projects FOR UPDATE
    USING (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin')
    WITH CHECK (org_id = auth.jwt->>'org_id'::uuid OR auth.jwt->>'role' = 'admin');

-- Trigger: 자동으로 updated_at 갱신
CREATE TRIGGER update_master_projects_updated_at
    BEFORE UPDATE ON master_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
