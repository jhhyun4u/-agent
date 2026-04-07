-- 015: 프론트엔드 에러 수집 테이블 (MON-10, MON-11)
-- 2026-03-26

CREATE TABLE IF NOT EXISTS client_error_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    url         TEXT NOT NULL,
    error       TEXT NOT NULL,
    stack       TEXT,
    user_agent  TEXT,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_errors_created ON client_error_logs(created_at DESC);
