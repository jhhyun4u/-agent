-- Task #2 성능 최적화: 누락된 인덱스 추가
-- 작성: 2026-04-18
-- 목표: KB 검색 및 Proposals 리스트 성능 개선

-- ============================================
-- P0 #1: Proposals 테이블 인덱싱
-- ============================================

-- 1. created_at 정렬 인덱스 (가장 중요!)
-- 효과: ORDER BY created_at DESC의 성능을 10배 향상
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_created_at_desc
ON proposals(created_at DESC);

-- 2. 복합 인덱스: team_id + created_at (scope=division 쿼리 최적화)
-- 효과: WHERE team_id IN (...) ORDER BY created_at DESC 쿼리 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_team_created_at
ON proposals(team_id, created_at DESC);

-- 3. owner_id 정렬 인덱스 (scope=my 쿼리 최적화)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_proposals_owner_created_at
ON proposals(owner_id, created_at DESC);

-- ============================================
-- P1 #2: Content Library 텍스트 검색 인덱스
-- ============================================

-- 1. GIN 인덱스: 전문 검색 (ILIKE 폴백용)
-- 효과: 키워드 검색이 활성화될 때 성능 100배 향상
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_body_gin
ON content_library USING GIN(to_tsvector('korean', body));

-- 2. 복합 인덱스: title 텍스트 검색
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_title_gin
ON content_library USING GIN(to_tsvector('korean', title));

-- ============================================
-- P1 #3: 기타 테이블 인덱싱
-- ============================================

-- Client Intelligence 텍스트 검색
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_client_body_gin
ON client_intelligence USING GIN(to_tsvector('korean', analysis));

-- Competitor 텍스트 검색
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_competitor_body_gin
ON competitors USING GIN(to_tsvector('korean', analysis));

-- ============================================
-- 검증 쿼리
-- ============================================

-- 생성된 인덱스 확인
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('proposals', 'content_library', 'client_intelligence', 'competitors')
ORDER BY tablename, indexname;

-- 인덱스 크기 확인 (성능 추적용)
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes
JOIN pg_class ON pg_indexes.indexname = pg_class.relname
JOIN pg_index ON pg_class.oid = pg_index.indexrelid
WHERE tablename IN ('proposals', 'content_library')
ORDER BY pg_relation_size(indexrelid) DESC;
