-- ============================================
-- Rollback: Migration 019 Unified State System
-- ============================================
-- 이 스크립트는 019_unified_state_system.sql 마이그레이션을 되돌립니다.
-- 주의: 데이터 손실이 발생할 수 있습니다. 롤백 전 반드시 백업하세요.
--
-- 실행 방법:
--   psql $DATABASE_URL < database/migrations/019_unified_state_system_rollback.sql
-- ============================================

BEGIN;

-- ============================================
-- Step 1: Layer 3 AI 상태 테이블 삭제
-- ============================================

DROP TABLE IF EXISTS ai_task_status CASCADE;

-- ============================================
-- Step 2: proposal_timelines 테이블 삭제
-- ============================================

DROP TABLE IF EXISTS proposal_timelines CASCADE;

-- ============================================
-- Step 3: proposals 테이블 신규 컬럼 제거
-- ============================================

-- 신규 타임스탬프 컬럼 (Phase 1c에서 추가된 것)
ALTER TABLE proposals DROP COLUMN IF EXISTS submitted_at;
ALTER TABLE proposals DROP COLUMN IF EXISTS presentation_started_at;
ALTER TABLE proposals DROP COLUMN IF EXISTS closed_at;
ALTER TABLE proposals DROP COLUMN IF EXISTS archived_at;
ALTER TABLE proposals DROP COLUMN IF EXISTS expired_at;

-- win_result 컬럼
ALTER TABLE proposals DROP COLUMN IF EXISTS win_result;

-- PM/PL 할당 컬럼
ALTER TABLE proposals DROP COLUMN IF EXISTS project_manager_id;
ALTER TABLE proposals DROP COLUMN IF EXISTS project_leader_id;

-- ============================================
-- Step 4: status CHECK constraint 복원
-- ============================================

-- 신규 constraint 제거
ALTER TABLE proposals DROP CONSTRAINT IF EXISTS status_check;
ALTER TABLE proposals DROP CONSTRAINT IF EXISTS win_result_check;

-- 기존 constraint 복원 (이전 16개 상태값 허용)
-- 주의: 실제 기존 constraint 이름은 환경마다 다를 수 있습니다
ALTER TABLE proposals ADD CONSTRAINT status_check CHECK (
    status IN (
        'initialized', 'processing', 'searching', 'analyzing', 'strategizing',
        'completed', 'submitted', 'presented', 'won', 'lost', 'no_go',
        'abandoned', 'retrospect', 'on_hold', 'expired',
        'running', 'failed', 'cancelled', 'paused'
    )
);

-- ============================================
-- Step 5: ai_task_logs constraint 제거
-- ============================================

DO $$
BEGIN
    ALTER TABLE ai_task_logs DROP CONSTRAINT IF EXISTS ai_task_logs_status_check;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

COMMIT;

-- ============================================
-- 롤백 완료 확인
-- ============================================
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name='proposals'
-- ORDER BY ordinal_position;
-- -- ai_task_status, proposal_timelines 테이블이 삭제되었는지 확인
-- SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename='ai_task_status');  -- false
-- SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename='proposal_timelines');  -- false
