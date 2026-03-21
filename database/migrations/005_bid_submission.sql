-- 005: 투찰 관리 컬럼 추가
-- bid_plan 확정가 + 실제 투찰 기록

-- 확정 입찰가 (워크플로에서 결정된 가격)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_confirmed_price   BIGINT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_confirmed_ratio   NUMERIC(5,2);
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_confirmed_scenario TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_confirmed_at      TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_confirmed_by      UUID REFERENCES users(id);

-- 실제 투찰 기록 (나라장터에 실제 입력한 가격)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_submitted_price   BIGINT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_submitted_at      TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_submitted_by      UUID REFERENCES users(id);
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_submission_note   TEXT;

-- 투찰 상태: ready(확정) → submitted(투찰완료) → verified(확인)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS bid_submission_status TEXT DEFAULT NULL;
ALTER TABLE proposals ADD CONSTRAINT bid_submission_status_check
    CHECK (bid_submission_status IS NULL OR bid_submission_status IN ('ready', 'submitted', 'verified'));

-- 투찰 이력 테이블 (가격 변경 추적)
CREATE TABLE IF NOT EXISTS bid_price_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,  -- confirmed | override | submitted | verified
    price           BIGINT NOT NULL,
    ratio           NUMERIC(5,2),
    scenario_name   TEXT,
    reason          TEXT,
    actor_id        UUID REFERENCES users(id),
    actor_name      TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bid_price_history_proposal ON bid_price_history(proposal_id);
CREATE INDEX IF NOT EXISTS idx_bid_price_history_event ON bid_price_history(event_type);

-- RLS: 입찰가 이력은 같은 팀 멤버만 조회
ALTER TABLE bid_price_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON bid_price_history FOR ALL
    USING (auth.role() = 'service_role');

CREATE POLICY "team_members_read_bid_history" ON bid_price_history FOR SELECT
    USING (
        proposal_id IN (
            SELECT id FROM proposals WHERE team_id IN (
                SELECT team_id FROM team_members WHERE user_id = auth.uid()
            )
        )
    );
