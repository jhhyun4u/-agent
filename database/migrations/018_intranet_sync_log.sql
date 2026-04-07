-- ==========================================
-- 018: 인트라넷 동기화 이력 추적
-- 매월 자동 동기화 실행 기록 + 미실행 알림 지원
-- ==========================================

-- 1) 동기화 실행 이력
CREATE TABLE IF NOT EXISTS intranet_sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,

    -- 동기화 실행 정보
    sync_type       TEXT NOT NULL DEFAULT 'incremental'
        CHECK (sync_type IN ('full', 'incremental')),
    status          TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),

    -- 실행 통계
    projects_found      INTEGER DEFAULT 0,
    projects_created    INTEGER DEFAULT 0,
    projects_updated    INTEGER DEFAULT 0,
    projects_skipped    INTEGER DEFAULT 0,
    files_uploaded      INTEGER DEFAULT 0,
    files_failed        INTEGER DEFAULT 0,
    error_message       TEXT,

    -- 실행 환경 (어느 PC에서 실행했는지 추적)
    source_host     TEXT,
    triggered_by    TEXT,           -- 'scheduler' | 'manual' | 'api'

    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sync_log_org ON intranet_sync_log(org_id);
CREATE INDEX IF NOT EXISTS idx_sync_log_started ON intranet_sync_log(started_at DESC);

-- 2) RLS 정책
ALTER TABLE intranet_sync_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY intranet_sync_log_user ON intranet_sync_log
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY intranet_sync_log_service ON intranet_sync_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);
