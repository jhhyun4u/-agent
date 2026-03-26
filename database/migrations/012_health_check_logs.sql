-- 자가검증 이력 테이블
CREATE TABLE IF NOT EXISTS health_check_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    check_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('infra', 'data', 'external', 'api')),
    status TEXT NOT NULL CHECK (status IN ('pass', 'warn', 'fail', 'fixed')),
    message TEXT,
    detail JSONB DEFAULT '{}',
    auto_recovered BOOLEAN DEFAULT FALSE,
    duration_ms REAL DEFAULT 0,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_logs_checked
    ON health_check_logs (checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_health_logs_failures
    ON health_check_logs (status, checked_at DESC)
    WHERE status IN ('fail', 'warn', 'fixed');

CREATE INDEX IF NOT EXISTS idx_health_logs_check_id
    ON health_check_logs (check_id, checked_at DESC);
