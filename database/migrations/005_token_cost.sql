-- 005: ai_task_logs에 캐시 토큰 + 비용 컬럼 추가
ALTER TABLE ai_task_logs
ADD COLUMN IF NOT EXISTS cache_read_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cache_create_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(10, 6) DEFAULT 0;
