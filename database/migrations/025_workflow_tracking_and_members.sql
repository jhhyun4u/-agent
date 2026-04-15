-- Migration: 025_workflow_tracking_and_members.sql
-- Description: 워크플로우 시간 추적 및 제안서 참여자 관리
-- Purpose:
--   1. proposals 테이블에 workflow 관련 컬럼 추가 (시작/종료/경과시간/토큰비용)
--   2. proposal_members 테이블 생성 (제안서별 참여자 추적)
--   3. RLS 정책 설정
-- Date: 2026-04-13

BEGIN;

-- ============================================
-- 1. proposals 테이블 확장: 워크플로우 추적 컬럼
-- ============================================

ALTER TABLE proposals
ADD COLUMN IF NOT EXISTS workflow_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS workflow_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS elapsed_seconds INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_token_usage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_token_cost DECIMAL(10, 2) DEFAULT 0.0;

-- 인덱스: 워크플로우 상태 조회 최적화
CREATE INDEX IF NOT EXISTS idx_proposals_workflow_status
ON proposals(org_id, workflow_started_at, workflow_completed_at);

-- ============================================
-- 2. proposal_members 테이블: 제안서별 참여자
-- ============================================

CREATE TABLE IF NOT EXISTS proposal_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 역할 및 기여도
    role VARCHAR(50) DEFAULT 'contributor'
        CHECK (role IN ('lead', 'contributor', 'reviewer', 'observer')),

    -- 참여 시간
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,

    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 중복 방지: 한 제안서에 같은 사용자 1회만 추가
    UNIQUE(proposal_id, user_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_proposal_members_proposal
ON proposal_members(proposal_id);

CREATE INDEX IF NOT EXISTS idx_proposal_members_user
ON proposal_members(user_id);

CREATE INDEX IF NOT EXISTS idx_proposal_members_role
ON proposal_members(proposal_id, role);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_proposal_members_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_proposal_members_updated_at ON proposal_members;

CREATE TRIGGER trg_proposal_members_updated_at
BEFORE UPDATE ON proposal_members
FOR EACH ROW EXECUTE FUNCTION update_proposal_members_updated_at();

-- ============================================
-- 3. RLS (Row Level Security) 정책
-- ============================================

-- proposal_members 테이블 RLS 활성화
ALTER TABLE proposal_members ENABLE ROW LEVEL SECURITY;

-- SELECT: 같은 조직의 제안서에만 접근
CREATE POLICY proposal_members_select ON proposal_members
FOR SELECT USING (
    proposal_id IN (
        SELECT id FROM proposals
        WHERE org_id = (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    )
);

-- INSERT: 제안서 소유 조직에만 추가 가능
CREATE POLICY proposal_members_insert ON proposal_members
FOR INSERT WITH CHECK (
    proposal_id IN (
        SELECT id FROM proposals
        WHERE org_id = (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    )
);

-- UPDATE: 제안서 소유 조직만 수정 가능
CREATE POLICY proposal_members_update ON proposal_members
FOR UPDATE USING (
    proposal_id IN (
        SELECT id FROM proposals
        WHERE org_id = (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    )
)
WITH CHECK (
    proposal_id IN (
        SELECT id FROM proposals
        WHERE org_id = (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    )
);

-- DELETE: 제안서 소유 조직만 삭제 가능
CREATE POLICY proposal_members_delete ON proposal_members
FOR DELETE USING (
    proposal_id IN (
        SELECT id FROM proposals
        WHERE org_id = (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    )
);

-- ============================================
-- 4. 뷰: 제안서별 참여자 목록 조회용
-- ============================================

CREATE OR REPLACE VIEW proposal_members_summary AS
SELECT
    pm.proposal_id,
    COUNT(DISTINCT pm.user_id) AS member_count,
    STRING_AGG(DISTINCT u.name, ', ' ORDER BY u.name) AS member_names,
    ARRAY_AGG(
        JSON_BUILD_OBJECT(
            'user_id', pm.user_id,
            'name', u.name,
            'email', u.email,
            'role', pm.role,
            'joined_at', pm.joined_at
        ) ORDER BY pm.joined_at
    ) AS members
FROM proposal_members pm
JOIN auth.users u ON pm.user_id = u.id
WHERE pm.left_at IS NULL
GROUP BY pm.proposal_id;

COMMIT;
