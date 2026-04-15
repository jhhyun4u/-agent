-- ============================================
-- 마이그레이션 006: 제안서-공고 분석 메타데이터 연동
-- ============================================
-- 목적:
--   1. proposals 테이블에 분석 메타데이터 경로 추가
--   2. 적합도 점수(fit_score) 추가
--   3. 원본 공고번호(source_bid_no) 저장 (bid_announcements와 연결용)
--
-- 배경:
--   제안결정 후 공고 모니터링의 분석 정보(RFP 분석, 공고문 요약 등)가
--   제안 프로젝트로 연동되지 않아 분석 정보가 휘발되는 문제 해결
--
-- 실행 예상 시간: < 1초

BEGIN;

-- proposals 테이블에 컬럼 추가 (역방향 조인용)
ALTER TABLE proposals
ADD COLUMN IF NOT EXISTS source_bid_no TEXT,  -- 원본 공고번호 (bid_announcements.bid_no)
ADD COLUMN IF NOT EXISTS fit_score NUMERIC(5,2),  -- 적합도 점수 (0-100)
ADD COLUMN IF NOT EXISTS md_rfp_analysis_path TEXT,  -- RFP 분석 마크다운 경로
ADD COLUMN IF NOT EXISTS md_notice_path TEXT,  -- 공고문 요약 마크다운 경로
ADD COLUMN IF NOT EXISTS md_instruction_path TEXT;  -- 과업지시서 마크다운 경로

-- 인덱스 추가 (조회 성능)
CREATE INDEX IF NOT EXISTS idx_proposals_source_bid_no ON proposals(source_bid_no);
CREATE INDEX IF NOT EXISTS idx_proposals_fit_score ON proposals(fit_score DESC);

-- 마이그레이션 기록
INSERT INTO migration_history (version, name, execution_time_ms, status)
VALUES ('006', 'Add proposal analysis metadata fields', 0, 'success');

COMMIT;
