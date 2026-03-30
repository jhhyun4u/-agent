-- 마이그레이션 추적 테이블 (가장 먼저 실행되어야 함)
-- 이 파일은 모든 마이그레이션 실행 기록을 추적합니다

CREATE TABLE IF NOT EXISTS public.migration_history (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'rolled_back')),
    error_message TEXT,
    created_by VARCHAR(255) DEFAULT 'system'
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_migration_history_version ON public.migration_history(version);
CREATE INDEX IF NOT EXISTS idx_migration_history_applied_at ON public.migration_history(applied_at DESC);
CREATE INDEX IF NOT EXISTS idx_migration_history_status ON public.migration_history(status);

-- 현재 마이그레이션 상태 조회용 함수
CREATE OR REPLACE FUNCTION get_migration_status()
RETURNS TABLE (
    total_migrations BIGINT,
    applied_migrations BIGINT,
    failed_migrations BIGINT,
    last_applied_at TIMESTAMPTZ
) AS $$
SELECT
    COUNT(DISTINCT version)                                         AS total_migrations,
    COUNT(*) FILTER (WHERE status = 'success')                     AS applied_migrations,
    COUNT(*) FILTER (WHERE status = 'failed')                      AS failed_migrations,
    MAX(applied_at) FILTER (WHERE status = 'success')              AS last_applied_at
FROM migration_history;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- 마이그레이션 적용 로그
INSERT INTO migration_history (version, name, status, execution_time_ms)
VALUES ('000', '000_init_migrations - Migration tracking table', 'success', 0)
ON CONFLICT (version) DO NOTHING;

COMMENT ON TABLE migration_history IS '마이그레이션 실행 이력 추적 테이블';
COMMENT ON COLUMN migration_history.version IS '마이그레이션 파일명 (e.g., 001_create_tables)';
COMMENT ON COLUMN migration_history.status IS '마이그레이션 상태: success, failed, rolled_back';
