-- Migration 054: 성공 섹션 라이브러리 — 학술연구용역 특화
-- Date: 2026-04-28
-- content_library 테이블에 학술연구용역 메타데이터 컬럼 추가

ALTER TABLE content_library
  ADD COLUMN IF NOT EXISTS study_type      TEXT,    -- 과제유형: 기초조사|실태조사|정책연구|타당성분석|성과평가|계획수립|중장기전략|기타
  ADD COLUMN IF NOT EXISTS section_category TEXT,   -- 섹션분류: UNDERSTAND|METHODOLOGY|TRACK_RECORD|PERSONNEL|MANAGEMENT|기타
  ADD COLUMN IF NOT EXISTS is_winning      BOOLEAN DEFAULT false,  -- 수주 과제 섹션 여부
  ADD COLUMN IF NOT EXISTS client_type     TEXT,    -- 발주기관 유형: 중앙부처|지자체|공공기관|민간|기타
  ADD COLUMN IF NOT EXISTS diagnosis_score NUMERIC(5,2); -- 섹션 진단 점수 (0-100)

-- 수주 섹션 조회 인덱스
CREATE INDEX IF NOT EXISTS idx_content_winning ON content_library(org_id, is_winning)
  WHERE is_winning = true;

CREATE INDEX IF NOT EXISTS idx_content_study_type ON content_library(org_id, study_type);
CREATE INDEX IF NOT EXISTS idx_content_section_category ON content_library(org_id, section_category);

-- 검증 쿼리
-- SELECT COUNT(*) FROM content_library WHERE is_winning = true;
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'content_library' AND column_name IN ('study_type','is_winning','client_type','diagnosis_score','section_category');
