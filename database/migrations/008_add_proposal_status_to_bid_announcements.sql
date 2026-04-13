-- 008_add_proposal_status_to_bid_announcements.sql
-- bid_announcements 테이블에 제안결정 추적용 컬럼 추가

-- proposal_status: 공고별 제안 의사결정 상태
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS proposal_status VARCHAR(50) DEFAULT '신규' CHECK (proposal_status IN ('신규', '제안결정', '제안포기', '제안유보', '관련없음'));

-- decided_by: 의사결정자 이름
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS decided_by VARCHAR(255);

-- verdict: Go/No-Go 판정 (이미 있을 수 있음)
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS verdict VARCHAR(20) CHECK (verdict IN ('Go', 'No-Go', NULL));

-- 인덱스 추가 (모니터링 리스트 필터링 성능 개선)
CREATE INDEX IF NOT EXISTS idx_bid_announcements_proposal_status
ON bid_announcements(proposal_status);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_status_days
ON bid_announcements(proposal_status, days_remaining);
