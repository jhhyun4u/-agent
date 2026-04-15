-- Migration: Vector search RPC function for master_projects
-- Date: 2026-04-14
-- Purpose: pgvector 기반 자연어 검색 RPC 함수

-- ═══════════════════════════════════════════════════════════
-- RPC: search_master_projects
-- Vector cosine similarity 기반 프로젝트 검색
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION search_master_projects(
    query_embedding vector(1536),
    org_id_param uuid,
    similarity_threshold float DEFAULT 0.6,
    limit_count integer DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    project_name text,
    client_name text,
    project_year integer,
    start_date date,
    end_date date,
    budget_krw bigint,
    summary text,
    project_type text,
    proposal_status text,
    result_status text,
    execution_status text,
    actual_teams jsonb,
    actual_participants jsonb,
    proposal_teams jsonb,
    proposal_participants jsonb,
    keywords text[],
    similarity_score float
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mp.id,
        mp.project_name,
        mp.client_name,
        mp.project_year,
        mp.start_date,
        mp.end_date,
        mp.budget_krw,
        mp.summary,
        mp.project_type,
        mp.proposal_status,
        mp.result_status,
        mp.execution_status,
        mp.actual_teams,
        mp.actual_participants,
        mp.proposal_teams,
        mp.proposal_participants,
        mp.keywords,
        (1 - (mp.embedding <=> query_embedding))::float AS similarity_score
    FROM master_projects mp
    WHERE mp.org_id = org_id_param
        AND mp.embedding IS NOT NULL
        AND (1 - (mp.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY mp.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$;

-- 인덱스 (이미 있으면 스킵)
-- CREATE INDEX idx_master_projects_embedding ON master_projects USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS 보안 정책 (RPC는 권한 상속)
-- search_master_projects는 master_projects 테이블의 RLS를 준수
