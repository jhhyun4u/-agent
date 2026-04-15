-- ============================================
-- 마이그레이션 007: bid_announcements에 적합도 점수 추가
-- ============================================
-- 목적:
--   공고 모니터링의 적합도 점수(fit_score)를 bid_announcements에 저장
--   제안 프로젝트 생성 시 적합도 점수 연동 가능
--
-- 배경:
--   search_results 테이블에만 fit_score가 있어서 bid_announcements로
--   제안을 생성할 때 적합도 점수를 활용할 수 없음
--
-- 실행 예상 시간: < 1초

BEGIN;

-- bid_announcements 테이블에 적합도 점수 추가
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS fit_score NUMERIC(5,2);  -- 적합도 점수 (0-100)

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_bid_announcements_fit_score ON bid_announcements(fit_score DESC);

-- search_results에서 fit_score를 복사하는 로직 (기존 데이터)
UPDATE bid_announcements ba
SET fit_score = sr.fit_score
FROM search_results sr
WHERE ba.bid_no = sr.bid_no
  AND ba.fit_score IS NULL
  AND sr.fit_score IS NOT NULL;

-- 마이그레이션 기록
INSERT INTO migration_history (version, name, execution_time_ms, status)
VALUES ('007', 'Add fit_score to bid_announcements', 0, 'success');

COMMIT;
