-- 006: E2E 테스트에서 발견된 누락 컬럼/테이블 추가
-- 2026-03-18: proposals.positioning, ai_task_logs.cache_*_tokens,
--             competitors, labor_rates 테이블 확인

-- 1. proposals에 positioning 컬럼 (워크플로 상태 추적)
ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS positioning TEXT;

-- 2. ai_task_logs에 cache 토큰 컬럼
ALTER TABLE ai_task_logs
  ADD COLUMN IF NOT EXISTS cache_read_tokens INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cache_create_tokens INTEGER DEFAULT 0;

-- 3. competitors 테이블 (strategy_generate에서 조회)
-- 이미 schema_v3.4.sql에 정의되어 있으나 미적용된 경우
CREATE TABLE IF NOT EXISTS competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    company_name    TEXT NOT NULL,
    scale           TEXT,
    primary_area    TEXT,
    strengths       TEXT,
    weaknesses      TEXT,
    price_pattern   TEXT,
    win_count       INTEGER DEFAULT 0,
    source          TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 4. labor_rates 테이블 (plan_price에서 조회)
CREATE TABLE IF NOT EXISTS labor_rates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year            INTEGER NOT NULL,
    grade           TEXT NOT NULL,
    monthly_rate    BIGINT NOT NULL,
    daily_rate      BIGINT,
    source          TEXT DEFAULT 'SW기술자 평균임금',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(year, grade)
);
