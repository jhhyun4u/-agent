-- ============================================
-- Migration: Scheduler Integration Tables
-- Version: 1.0
-- Date: 2026-03-30
-- ============================================

-- 1. migration_batches 테이블
CREATE TABLE IF NOT EXISTS migration_batches (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name VARCHAR(255) NOT NULL,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- 시간 정보
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ NOT NULL,

    -- 처리 통계
    total_documents INT NOT NULL DEFAULT 0,
    processed_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    skipped_documents INT NOT NULL DEFAULT 0,

    -- 상세 정보
    source_system VARCHAR(100) NOT NULL DEFAULT 'intranet',
    batch_type VARCHAR(50) NOT NULL DEFAULT 'monthly',

    -- 에러 정보
    error_message TEXT,
    error_details JSONB,

    -- 메타데이터
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- 제약조건
    CONSTRAINT status_valid CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial_failed'))
);

-- 인덱스
CREATE INDEX idx_migration_batches_status ON migration_batches(status);
CREATE INDEX idx_migration_batches_scheduled ON migration_batches(scheduled_at);
CREATE INDEX idx_migration_batches_created_by ON migration_batches(created_by);
CREATE INDEX idx_migration_batches_batch_type ON migration_batches(batch_type);

-- 2. migration_schedule 테이블
CREATE TABLE IF NOT EXISTS migration_schedule (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 스케줄 설정
    enabled BOOLEAN NOT NULL DEFAULT true,
    cron_expression VARCHAR(100) NOT NULL DEFAULT '0 0 1 * *',
    schedule_name VARCHAR(255) NOT NULL DEFAULT 'monthly_intranet_migration',
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'cron',

    -- 실행 예정
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_batch_id UUID REFERENCES migration_batches(id) ON DELETE SET NULL,

    -- 설정
    timeout_seconds INT DEFAULT 3600,
    max_retries INT DEFAULT 3,
    retry_delay_seconds INT DEFAULT 300,

    -- 알림 설정
    notify_on_success BOOLEAN DEFAULT false,
    notify_on_failure BOOLEAN DEFAULT true,
    notification_channels JSONB DEFAULT '["email", "teams"]'::jsonb,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- 제약조건
    CONSTRAINT schedule_type_valid CHECK (schedule_type IN ('cron', 'once', 'interval'))
);

-- 인덱스
CREATE INDEX idx_migration_schedule_enabled ON migration_schedule(enabled);
CREATE INDEX idx_migration_schedule_next_run ON migration_schedule(next_run_at);
CREATE INDEX idx_migration_schedule_last_run ON migration_schedule(last_run_at);

-- 3. document_chunks 테이블 확장 (선택)
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS
    migration_batch_id UUID REFERENCES migration_batches(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_document_chunks_migration_batch
ON document_chunks(migration_batch_id);

-- 4. RLS 정책 활성화
ALTER TABLE migration_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_schedule ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policy: migration_batches SELECT (모든 인증 사용자)
DROP POLICY IF EXISTS migration_batches_select ON migration_batches;
CREATE POLICY migration_batches_select
ON migration_batches
FOR SELECT
USING (auth.uid() IS NOT NULL);

-- 6. RLS Policy: migration_batches INSERT (프로젝트 관리자)
DROP POLICY IF EXISTS migration_batches_insert ON migration_batches;
CREATE POLICY migration_batches_insert
ON migration_batches
FOR INSERT
WITH CHECK (
    auth.uid() IN (
        SELECT user_id FROM project_members
        WHERE role IN ('admin', 'manager')
    )
    OR
    auth.uid() IN (SELECT id FROM users WHERE role = 'admin')
);

-- 7. RLS Policy: migration_schedule SELECT (모든 인증 사용자)
DROP POLICY IF EXISTS migration_schedule_select ON migration_schedule;
CREATE POLICY migration_schedule_select
ON migration_schedule
FOR SELECT
USING (auth.uid() IS NOT NULL);

-- 8. RLS Policy: migration_schedule UPDATE (시스템 관리자만)
DROP POLICY IF EXISTS migration_schedule_update ON migration_schedule;
CREATE POLICY migration_schedule_update
ON migration_schedule
FOR UPDATE
USING (
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- 9. RLS Policy: migration_schedule INSERT (시스템 관리자만)
DROP POLICY IF EXISTS migration_schedule_insert ON migration_schedule;
CREATE POLICY migration_schedule_insert
ON migration_schedule
FOR INSERT
WITH CHECK (
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- 10. 초기 데이터 삽입 (첫 번째 스케줄)
INSERT INTO migration_schedule (
    id, enabled, cron_expression, schedule_name,
    next_run_at, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    true,
    '0 0 1 * *',
    'monthly_intranet_migration',
    NOW() + INTERVAL '1 month',
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM migration_schedule
    WHERE schedule_name = 'monthly_intranet_migration'
);

-- 11. 코멘트 추가 (문서화)
COMMENT ON TABLE migration_batches IS '인트라넷 문서 배치 마이그레이션 작업 기록';
COMMENT ON TABLE migration_schedule IS '정기적 문서 마이그레이션 스케줄 설정';
COMMENT ON COLUMN migration_batches.status IS '배치 상태: pending|processing|completed|failed|partial_failed';
COMMENT ON COLUMN migration_schedule.cron_expression IS 'Cron 표현식 (예: "0 0 1 * *" = 매달 1일 00:00)';
