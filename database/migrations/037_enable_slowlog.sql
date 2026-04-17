-- Phase 1 성능 최적화: 느린 쿼리 로깅 활성화
-- 목적: 1초 이상 소요되는 쿼리 식별
-- 작성일: 2026-04-17

-- PostgreSQL 설정 변경 (슈퍼유저 필요)
-- Supabase: Database > Settings > Postgres Version에서 직접 수정

-- 1. 슬로우 쿼리 로깅 활성화 (1초 이상)
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- 2. 쿼리 실행 계획 로깅 (EXPLAIN 자동 추가)
ALTER SYSTEM SET auto_explain.log_min_duration = 1000;
ALTER SYSTEM SET auto_explain.log_analyze = true;

-- 3. 변경사항 적용
SELECT pg_reload_conf();

-- 4. 확인 쿼리
SHOW log_min_duration_statement;
SHOW auto_explain.log_min_duration;

-- ────────────────────────────────────────
-- PostgreSQL 로그 조회 (pgAdmin 또는 CLI)
-- ────────────────────────────────────────

-- 느린 쿼리 상위 10개
SELECT 
    query,
    COUNT(*) as execution_count,
    ROUND(AVG(mean_exec_time)::numeric, 2) as avg_exec_time_ms,
    ROUND(MAX(mean_exec_time)::numeric, 2) as max_exec_time_ms,
    ROUND((SUM(total_exec_time) / 1000)::numeric, 2) as total_exec_time_sec
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- 100ms 이상
ORDER BY total_exec_time DESC
LIMIT 10;

-- 특정 테이블의 느린 쿼리
SELECT 
    query,
    mean_exec_time,
    max_exec_time,
    calls
FROM pg_stat_statements
WHERE query LIKE '%proposals%'
    AND mean_exec_time > 100
ORDER BY mean_exec_time DESC;

-- ────────────────────────────────────────
-- 성능 최적화를 위한 인덱스 제안
-- ────────────────────────────────────────

-- 현재 인덱스 확인
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- N+1 쿼리 패턴 감지 (같은 쿼리가 반복됨)
SELECT 
    query,
    calls,
    ROUND(mean_exec_time::numeric, 2) as mean_exec_time_ms
FROM pg_stat_statements
WHERE calls > 50  -- 50회 이상 반복된 쿼리
ORDER BY calls DESC
LIMIT 10;

-- ────────────────────────────────────────
-- 자주 접근하는 테이블의 성능 분석
-- ────────────────────────────────────────

-- proposals 테이블 분석
ANALYZE proposals;

-- 테이블 통계 확인
SELECT 
    schemaname,
    tablename,
    live_tup,
    dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE tablename = 'proposals';

-- ────────────────────────────────────────
-- 권장 인덱스 추가 (Phase 1 최적화)
-- ────────────────────────────────────────

-- 1. 제안서 목록 조회 최적화 (owner_id + created_at)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_owner_created 
    ON proposals(owner_id, created_at DESC) 
    WHERE status != 'archived';

-- 2. 팀 기반 제안서 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_team_created 
    ON proposals(team_id, created_at DESC) 
    WHERE status != 'archived';

-- 3. 상태별 제안서 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_status 
    ON proposals(status, created_at DESC);

-- 4. 검색 쿼리 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_title 
    ON proposals USING GIN(to_tsvector('korean', title));

-- 인덱스 생성 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'proposals'
ORDER BY indexname;

-- ────────────────────────────────────────
-- 쿼리 계획 분석
-- ────────────────────────────────────────

-- EXPLAIN + ANALYZE로 실제 성능 확인
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT 
    id, title, status, owner_id, created_at
FROM proposals
WHERE owner_id = 'sample-user-id'
ORDER BY created_at DESC
LIMIT 10;

-- 실행 계획만 확인 (ANALYZE 없음)
EXPLAIN (BUFFERS, FORMAT TEXT)
SELECT 
    p.id, 
    p.title, 
    p.status,
    p.owner_id,
    p.created_at,
    u.name as owner_name,
    t.name as team_name
FROM proposals p
LEFT JOIN users u ON p.owner_id = u.id
LEFT JOIN teams t ON p.team_id = t.id
WHERE p.owner_id = 'sample-user-id'
ORDER BY p.created_at DESC
LIMIT 10;
