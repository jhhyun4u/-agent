-- ============================================
-- Migration: 제안결정 및 작업 목록 기능 추가
-- 2026-04-10
-- ============================================

-- ① proposals 테이블에 제안결정 관련 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS go_decision BOOLEAN DEFAULT false;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS decision_date TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_tracked BOOLEAN DEFAULT true;

-- decision_date에 자동 업데이트 트리거 (go_decision=true일 때)
CREATE OR REPLACE FUNCTION update_proposal_decision_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.go_decision = true AND OLD.go_decision = false THEN
        NEW.decision_date = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS proposal_decision_trigger ON proposals;
CREATE TRIGGER proposal_decision_trigger
    BEFORE UPDATE ON proposals
    FOR EACH ROW
    WHEN (OLD.go_decision IS DISTINCT FROM NEW.go_decision)
    EXECUTE FUNCTION update_proposal_decision_date();

-- ② 제안 작업 목록 테이블 생성
CREATE TABLE IF NOT EXISTS proposal_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    assigned_team_id UUID NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'waiting',  -- waiting | in_progress | completed | blocked
    priority        TEXT DEFAULT 'normal',             -- low | normal | high
    due_date        TIMESTAMPTZ,
    created_by_id   UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT proposal_tasks_status_check CHECK (
        status IN ('waiting', 'in_progress', 'completed', 'blocked')
    ),
    CONSTRAINT proposal_tasks_priority_check CHECK (
        priority IN ('low', 'normal', 'high')
    )
);

-- proposal_tasks 자동 업데이트 트리거
DROP TRIGGER IF EXISTS proposal_tasks_updated_at ON proposal_tasks;
CREATE TRIGGER proposal_tasks_updated_at
    BEFORE UPDATE ON proposal_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- proposal_tasks 인덱스
CREATE INDEX IF NOT EXISTS idx_proposal_tasks_proposal_id ON proposal_tasks(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_tasks_team_id ON proposal_tasks(assigned_team_id);
CREATE INDEX IF NOT EXISTS idx_proposal_tasks_status ON proposal_tasks(status);

-- ③ RLS 정책 추가 (proposal_tasks)
ALTER TABLE proposal_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS proposal_tasks_read_policy ON proposal_tasks;
CREATE POLICY proposal_tasks_read_policy
    ON proposal_tasks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            WHERE p.id = proposal_tasks.proposal_id
            AND (
                p.owner_id = auth.uid()
                OR p.team_id IN (
                    SELECT team_id FROM users WHERE id = auth.uid()
                )
                OR (
                    SELECT org_id FROM users WHERE id = auth.uid()
                ) = (
                    SELECT org_id FROM users WHERE id = p.owner_id
                )
            )
        )
    );

DROP POLICY IF EXISTS proposal_tasks_insert_policy ON proposal_tasks;
CREATE POLICY proposal_tasks_insert_policy
    ON proposal_tasks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM proposals p
            WHERE p.id = proposal_tasks.proposal_id
            AND p.owner_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS proposal_tasks_update_policy ON proposal_tasks;
CREATE POLICY proposal_tasks_update_policy
    ON proposal_tasks FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM proposals p
            WHERE p.id = proposal_tasks.proposal_id
            AND p.owner_id = auth.uid()
        )
    );
