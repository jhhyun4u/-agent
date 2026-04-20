-- ============================================
-- Migration: Scheduler Integration Tables
-- Version: 1.0
-- Date: 2026-04-20
-- Description: 정기 문서 마이그레이션 스케줄러
-- ============================================

-- 1. migration_batches 테이블 생성
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
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- 제약조건
    CONSTRAINT status_valid CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial_failed'))
);

-- migration_batches 인덱스
CREATE INDEX IF NOT EXISTS idx_migration_batches_status ON migration_batches(status);
CREATE INDEX IF NOT EXISTS idx_migration_batches_scheduled ON migration_batches(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_migration_batches_created_by ON migration_batches(created_by);

-- 2. migration_schedule 테이블 생성
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
    last_batch_id UUID REFERENCES migration_batches(id),

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
    updated_by UUID REFERENCES users(id),

    -- 제약조건
    CONSTRAINT schedule_type_valid CHECK (schedule_type IN ('cron', 'once', 'interval'))
);

-- migration_schedule 인덱스
CREATE INDEX IF NOT EXISTS idx_migration_schedule_enabled ON migration_schedule(enabled);
CREATE INDEX IF NOT EXISTS idx_migration_schedule_next_run ON migration_schedule(next_run_at);

-- 3. document_chunks 테이블 확장 (선택)
ALTER TABLE IF EXISTS document_chunks ADD COLUMN IF NOT EXISTS
    migration_batch_id UUID REFERENCES migration_batches(id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_migration_batch
ON document_chunks(migration_batch_id);

-- 4. Row Level Security 활성화
ALTER TABLE migration_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_schedule ENABLE ROW LEVEL SECURITY;

-- RLS Policy for migration_batches (SELECT)
CREATE POLICY IF NOT EXISTS migration_batches_select
ON migration_batches
FOR SELECT
USING (
    -- 프로젝트 멤버는 조회 가능
    auth.uid() IN (
        SELECT user_id FROM project_members
        WHERE project_id IS NOT NULL
    )
    OR
    -- 시스템 관리자는 항상 조회 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- RLS Policy for migration_batches (INSERT)
CREATE POLICY IF NOT EXISTS migration_batches_insert
ON migration_batches
FOR INSERT
WITH CHECK (
    -- 프로젝트 관리자만 삽입 가능
    auth.uid() IN (
        SELECT user_id FROM project_members
        WHERE role = 'admin'
    )
    OR
    -- 시스템 관리자는 항상 삽입 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- RLS Policy for migration_schedule (SELECT)
CREATE POLICY IF NOT EXISTS migration_schedule_select
ON migration_schedule
FOR SELECT
USING (
    -- 시스템 관리자만 조회 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- RLS Policy for migration_schedule (UPDATE)
CREATE POLICY IF NOT EXISTS migration_schedule_update
ON migration_schedule
FOR UPDATE
USING (
    -- 시스템 관리자만 업데이트 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- 초기 스케줄 데이터 삽입 (옵션)
INSERT INTO migration_schedule (
    schedule_name,
    cron_expression,
    schedule_type,
    enabled,
    notify_on_success,
    notify_on_failure
) VALUES (
    'Monthly Intranet Migration',
    '0 0 1 * *',  -- 매월 1일 자정
    'cron',
    true,
    false,
    true
) ON CONFLICT DO NOTHING;

-- 5. 마이그레이션 상태 추적 테이블
CREATE TABLE IF NOT EXISTS migration_status_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES migration_batches(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    details JSONB,
    logged_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_migration_status_logs_batch ON migration_status_logs(batch_id);
CREATE INDEX IF NOT EXISTS idx_migration_status_logs_logged_at ON migration_status_logs(logged_at);
