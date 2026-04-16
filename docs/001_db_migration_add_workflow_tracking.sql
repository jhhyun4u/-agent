/**
 * DB 마이그레이션: 워크플로우 시간 및 토큰 비용 추적
 *
 * 실행 절차:
 * 1. Supabase 대시보드 → SQL Editor
 * 2. 아래 SQL 복사 후 실행
 * 3. 변경사항 확인
 */

-- ═══════════════════════════════════════════════════════════════
-- 1. proposals 테이블에 컬럼 추가
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE public.proposals
ADD COLUMN IF NOT EXISTS workflow_started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS workflow_completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS elapsed_seconds INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_token_usage INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_token_cost DECIMAL(10, 2) DEFAULT 0.0;

-- ═══════════════════════════════════════════════════════════════
-- 2. 새로운 테이블: proposal_members (참여자 관리)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.proposal_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES public.proposals(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role VARCHAR(50) DEFAULT 'contributor',
  joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(proposal_id, user_id)
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_proposal_members_proposal_id
  ON public.proposal_members(proposal_id);

CREATE INDEX IF NOT EXISTS idx_proposal_members_user_id
  ON public.proposal_members(user_id);

-- ═══════════════════════════════════════════════════════════════
-- 3. RLS (Row Level Security) 정책 설정
-- ═══════════════════════════════════════════════════════════════

-- proposal_members 테이블 RLS 활성화
ALTER TABLE public.proposal_members ENABLE ROW LEVEL SECURITY;

-- 정책 1: 자신의 조직에 속한 proposal_members만 조회
CREATE POLICY "Users can view members of their org's proposals"
  ON public.proposal_members
  FOR SELECT
  USING (
    proposal_id IN (
      SELECT id FROM public.proposals
      WHERE org_id = (
        SELECT org_id FROM auth.users WHERE id = auth.uid()
      )
    )
  );

-- 정책 2: Proposal 소유자만 멤버 추가 가능
CREATE POLICY "Only proposal owner can add members"
  ON public.proposal_members
  FOR INSERT
  WITH CHECK (
    proposal_id IN (
      SELECT id FROM public.proposals
      WHERE owner_id = auth.uid()
    )
  );

-- 정책 3: Proposal 소유자만 멤버 삭제 가능
CREATE POLICY "Only proposal owner can remove members"
  ON public.proposal_members
  FOR DELETE
  USING (
    proposal_id IN (
      SELECT id FROM public.proposals
      WHERE owner_id = auth.uid()
    )
  );

-- ═══════════════════════════════════════════════════════════════
-- 4. 기존 데이터 마이그레이션 (선택사항)
-- ═══════════════════════════════════════════════════════════════

-- 기존 제안서들의 created_at을 workflow_started_at으로 초기화
UPDATE public.proposals
SET workflow_started_at = created_at
WHERE workflow_started_at IS NULL AND status = 'completed';

-- ═══════════════════════════════════════════════════════════════
-- 5. 확인 쿼리 (마이그레이션 후 실행)
-- ═══════════════════════════════════════════════════════════════

-- 컬럼 확인
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'proposals'
-- AND column_name IN ('workflow_started_at', 'workflow_completed_at', 'elapsed_seconds', 'total_token_usage', 'total_token_cost');

-- proposal_members 테이블 확인
-- SELECT COUNT(*) FROM public.proposal_members;
