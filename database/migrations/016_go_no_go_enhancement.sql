-- Go/No-Go Enhancement v4.0: 4축 정량 스코어링 지원

-- proposals 테이블에 domain 컬럼 추가 (유사실적 매칭용)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS domain TEXT;
COMMENT ON COLUMN proposals.domain IS 'SI/SW개발, 컨설팅, 감리, 인프라구축, 운영유지보수 등';

-- go_no_go_score 컬럼 추가 (4축 합산 스코어)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS go_no_go_score INTEGER;
COMMENT ON COLUMN proposals.go_no_go_score IS 'Go/No-Go 4축 합산 점수 (0~100)';

-- go_no_go_tag 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS go_no_go_tag TEXT;
COMMENT ON COLUMN proposals.go_no_go_tag IS 'priority|standard|below_threshold|disqualified';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_proposals_domain ON proposals(domain);
CREATE INDEX IF NOT EXISTS idx_proposals_gng_score ON proposals(go_no_go_score);
