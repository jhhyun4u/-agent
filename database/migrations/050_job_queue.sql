-- ============================================
-- STEP 8: 비동기 Job Queue 시스템
-- 마이그레이션: 050_job_queue.sql
-- 작성일: 2026-04-20
-- ============================================

-- ============================================
-- §8-1. Job 테이블 (비동기 작업 단위)
-- ============================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    step VARCHAR(10) NOT NULL,  -- "4a", "4b", "5a", "5b", "6"
    type VARCHAR(50) NOT NULL,  -- "step4a_diagnosis", "step4a_regenerate" 등

    status VARCHAR(20) DEFAULT 'pending',  -- pending | running | success | failed | cancelled
    priority INTEGER DEFAULT 1,             -- 0=high, 1=normal, 2=low

    -- 입력 & 출력
    payload JSONB DEFAULT '{}'::jsonb,      -- 작업 파라미터 (< 1MB)
    result JSONB,                           -- 결과 (성공 시)
    error TEXT,                             -- 에러 메시지

    -- 재시도
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- 타이밍
    created_at TIMESTAMPTZ DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(10, 2),  -- NULL 계산: completed_at - started_at

    -- 추적
    created_by UUID NOT NULL REFERENCES users(id),
    assigned_worker_id VARCHAR(50),  -- "worker-0" 등

    -- 태그 (필터링용)
    tags JSONB DEFAULT '{}'::jsonb,

    -- 수정 추적
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_jobs_proposal_id ON jobs(proposal_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_step ON jobs(step);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_priority_status ON jobs(priority, status);  -- 큐 쿼리용

-- 자동 updated_at 갱신 트리거
CREATE OR REPLACE FUNCTION update_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_jobs_updated_at();

-- RLS 정책
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- admin은 모든 job 조회 가능
CREATE POLICY jobs_admin_read ON jobs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('admin', 'super_admin')
        )
    );

-- 사용자는 자신이 생성한 job만 조회 가능
CREATE POLICY jobs_user_read ON jobs
    FOR SELECT
    USING (created_by = auth.uid());

-- 사용자는 자신이 생성한 job만 수정 가능
CREATE POLICY jobs_user_update ON jobs
    FOR UPDATE
    USING (created_by = auth.uid());

-- ============================================
-- §8-2. Job Result 테이블 (결과 이력)
-- ============================================

CREATE TABLE IF NOT EXISTS job_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    result_data JSONB NOT NULL,  -- 상세 결과
    saved_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_results_job_id ON job_results(job_id);

-- RLS 정책
ALTER TABLE job_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY job_results_admin_read ON job_results
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('admin', 'super_admin')
        )
    );

CREATE POLICY job_results_user_read ON job_results
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.id = job_id
            AND j.created_by = auth.uid()
        )
    );

-- ============================================
-- §8-3. Job Metrics 테이블 (성과 추적)
-- ============================================

CREATE TABLE IF NOT EXISTS job_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    step VARCHAR(10),  -- "4a", "4b" 등
    type VARCHAR(50),  -- 작업 타입
    status VARCHAR(20),  -- "success", "failed"

    duration_seconds NUMERIC(10, 2),
    memory_mb NUMERIC(8, 2),  -- 메모리 사용량
    cpu_percent NUMERIC(5, 2),  -- CPU 사용률

    worker_id VARCHAR(50),
    recorded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_metrics_recorded_at ON job_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_metrics_step ON job_metrics(step);
CREATE INDEX IF NOT EXISTS idx_job_metrics_job_id ON job_metrics(job_id);

-- RLS 정책
ALTER TABLE job_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY job_metrics_admin_read ON job_metrics
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('admin', 'super_admin')
        )
    );

CREATE POLICY job_metrics_user_read ON job_metrics
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.id = job_id
            AND j.created_by = auth.uid()
        )
    );

-- ============================================
-- §8-4. Job Events 테이블 (감시 로그)
-- ============================================

CREATE TABLE IF NOT EXISTS job_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    event_type VARCHAR(50),  -- "created", "started", "progress", "completed", "failed", "cancelled"

    details JSONB,  -- {progress: 50, message: "...", ...}
    occurred_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_events_job_id ON job_events(job_id);
CREATE INDEX IF NOT EXISTS idx_job_events_occurred_at ON job_events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_events_event_type ON job_events(event_type);

-- RLS 정책
ALTER TABLE job_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY job_events_admin_read ON job_events
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.role IN ('admin', 'super_admin')
        )
    );

CREATE POLICY job_events_user_read ON job_events
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.id = job_id
            AND j.created_by = auth.uid()
        )
    );

-- ============================================
-- §8-5. 제약 조건 및 뷰
-- ============================================

-- Job 상태 체크 제약
ALTER TABLE jobs
ADD CONSTRAINT check_job_status
CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled'));

ALTER TABLE jobs
ADD CONSTRAINT check_job_priority
CHECK (priority IN (0, 1, 2));

-- 재시도 횟수 제약
ALTER TABLE jobs
ADD CONSTRAINT check_retries
CHECK (retries >= 0 AND retries <= max_retries);

-- ============================================
-- §8-6. 자동 정리 정책 주석
-- ============================================

-- 참고: 7일 이상 된 완료/실패 job 자동 삭제는 별도 cron job으로 관리
-- DELETE FROM jobs WHERE status IN ('success', 'failed', 'cancelled')
-- AND completed_at < now() - interval '7 days'

-- ============================================
-- 마이그레이션 완료
-- ============================================
