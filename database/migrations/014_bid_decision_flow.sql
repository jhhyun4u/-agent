-- 014: 제안결정 플로우 수정
-- bid_announcements에 proposal_status/decided_by 컬럼 추가
-- proposals에 bid_no 컬럼 추가 (공고 연결 추적)

-- 1. bid_announcements: 제안여부 상태를 DB에도 저장
ALTER TABLE bid_announcements
  ADD COLUMN IF NOT EXISTS proposal_status TEXT,
  ADD COLUMN IF NOT EXISTS decided_by TEXT;

CREATE INDEX IF NOT EXISTS idx_bid_ann_proposal_status
  ON bid_announcements(proposal_status);

-- 2. proposals: 공고 연결 컬럼 (from-bid 진입 경로 추적)
ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS bid_no TEXT,
  ADD COLUMN IF NOT EXISTS client_name TEXT,
  ADD COLUMN IF NOT EXISTS deadline TEXT;

CREATE INDEX IF NOT EXISTS idx_proposals_bid_no
  ON proposals(bid_no);
