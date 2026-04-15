-- ============================================
-- Migration 019: Unified State System
-- 10개 Business Status + 3-Layer Architecture
-- ============================================
-- Layer 1 (Business Status): proposals.status — 10개 통합 비즈니스 상태
-- Layer 2 (Workflow Phase) : proposals.current_phase — LangGraph 노드
-- Layer 3 (AI Runtime)     : ai_task_status 테이블 — 임시 AI 실행 상태
-- ============================================

BEGIN;

-- ============================================
-- Phase 1a: status 컬럼 CHECK constraint 재정의
-- ============================================

-- 기존 CHECK constraint 제거 (있을 경우)
DO $$
BEGIN
    ALTER TABLE proposals DROP CONSTRAINT IF EXISTS status_check;
    ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_status_check;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- 10개 통합 비즈니스 상태로 CHECK constraint 재정의
ALTER TABLE proposals ADD CONSTRAINT status_check CHECK (
    status IN (
        'initialized',   -- 0. 제안서 초기 생성 (기존 데이터 호환)
        'waiting',       -- 1. 생성 후 대기
        'in_progress',   -- 2. AI 워크플로우 진행 중
        'completed',     -- 3. 내부 완성 (제출 전)
        'submitted',     -- 4. 고객/발주기관에 제출
        'presentation',  -- 5. 발표/입찰 진행 중
        'closed',        -- 6. 최종 종료 (win_result로 세부 구분)
        'archived',      -- 7. 보관 (closed 후 30일 경과)
        'on_hold',       -- 8. 일시 보류
        'expired'        -- 9. 마감일 초과 자동 만료
    )
);

-- ============================================
-- Phase 1b: win_result 컬럼 추가 + CHECK constraint
-- ============================================

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS win_result VARCHAR(50);

-- win_result CHECK constraint 추가
DO $$
BEGIN
    ALTER TABLE proposals ADD CONSTRAINT win_result_check CHECK (
        win_result IS NULL OR
        win_result IN ('won', 'lost', 'no_go', 'abandoned', 'cancelled')
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- Phase 1c: 타임스탬프 컬럼 추가 (8개)
-- ============================================

-- 기존 4개 (migration 019 이전에 추가된 것 포함)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS created_at              TIMESTAMPTZ DEFAULT now();
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS started_at             TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS last_activity_at       TIMESTAMPTZ DEFAULT now();
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS completed_at           TIMESTAMPTZ;

-- 신규 5개 (Phase 1c 추가)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS submitted_at            TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_started_at TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS closed_at               TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS archived_at             TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS expired_at              TIMESTAMPTZ;

-- ============================================
-- Phase 1d: PM/PL 할당 컬럼 추가
-- ============================================

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS project_manager_id UUID;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS project_leader_id  UUID;

-- ============================================
-- Phase 1e: proposal_timelines 테이블 생성
-- ============================================

CREATE TABLE IF NOT EXISTS proposal_timelines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id         UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- State Transition
    event_type          TEXT NOT NULL CHECK (event_type IN (
                            'status_change', 'phase_change', 'review_comment',
                            'ai_complete', 'archive', 'expire', 'hold', 'release',
                            'approval'
                        )),
    from_status         TEXT,           -- NULL for first entry
    to_status           TEXT,           -- Current status (null if not status event)
    from_phase          TEXT,           -- NULL for first entry
    to_phase            TEXT,           -- Current phase (null if not phase event)

    -- Actor & Comment
    triggered_by        UUID REFERENCES auth.users(id),  -- User who triggered
    actor_type          TEXT CHECK (actor_type IN ('user', 'system', 'ai', 'workflow', 'cron')),
    trigger_reason      TEXT,           -- Why the transition happened
    notes               TEXT,           -- Comments/feedback

    -- Metadata
    metadata            JSONB,          -- Extra data (win_result, decision_comment, etc.)
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_proposal_timelines_proposal_id
    ON proposal_timelines(proposal_id);

CREATE INDEX IF NOT EXISTS idx_proposal_timelines_created_at
    ON proposal_timelines(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_proposal_timelines_event_type
    ON proposal_timelines(event_type);

-- ============================================
-- Phase 1f: ai_task_status 테이블 생성 (Layer 3)
-- ============================================
-- AI 임시 실행 상태를 proposals.status와 완전 분리

CREATE TABLE IF NOT EXISTS ai_task_status (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id      UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    status           VARCHAR(50) NOT NULL CHECK (status IN (
                         'running', 'paused', 'error', 'no_response', 'complete'
                     )),
    current_node     TEXT,
    error_message    TEXT,

    started_at       TIMESTAMPTZ DEFAULT now(),
    last_heartbeat   TIMESTAMPTZ,
    ended_at         TIMESTAMPTZ,

    session_id       TEXT    -- LangGraph 스레드/세션 ID
);

CREATE INDEX IF NOT EXISTS idx_ai_task_status_proposal_id
    ON ai_task_status(proposal_id);

CREATE INDEX IF NOT EXISTS idx_ai_task_status_status
    ON ai_task_status(status);

-- ============================================
-- Phase 1g: ai_task_logs 기존 테이블 CHECK constraint
-- ============================================

DO $$
BEGIN
    ALTER TABLE ai_task_logs ADD CONSTRAINT ai_task_logs_status_check
        CHECK (status IN ('running', 'complete', 'error', 'paused', 'no_response'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN undefined_table  THEN NULL;
END $$;

-- ============================================
-- Phase 1h: 기존 데이터 초기화
-- ============================================

-- created_at 누락 보정
UPDATE proposals
SET created_at = COALESCE(created_at, updated_at, now())
WHERE created_at IS NULL;

-- last_activity_at 누락 보정
UPDATE proposals
SET last_activity_at = COALESCE(last_activity_at, updated_at, now())
WHERE last_activity_at IS NULL;

-- proposal_timelines 초기 스냅샷 (기존 proposals)
INSERT INTO proposal_timelines (
    proposal_id, event_type, to_status, to_phase, actor_type, created_at
)
SELECT
    id,
    'status_change',
    status,
    current_phase,
    'system',
    COALESCE(created_at, now())
FROM proposals
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================
-- Summary
-- ============================================
-- Layer 1 Business Status (10개):
--   initialized, waiting, in_progress, completed, submitted, presentation,
--   closed, archived, on_hold, expired
--
-- win_result (5개, closed 시 세부 구분):
--   won, lost, no_go, abandoned, cancelled
--
-- Timestamp columns (총 9개):
--   created_at, started_at, last_activity_at, completed_at,
--   submitted_at, presentation_started_at, closed_at, archived_at, expired_at
--
-- 신규 테이블:
--   proposal_timelines — 전체 상태 전환 감사 이력
--   ai_task_status     — Layer 3 AI 임시 실행 상태 (proposals.status와 분리)
--
-- 다음 단계:
--   1. scripts/migrate_states_unified.py 실행 (기존 데이터 매핑)
--   2. app/services/state_validator.py 통합 Enum 사용 확인
--   3. routes_workflow.py status='running'/'cancelled' → ai_task_status로 이관
