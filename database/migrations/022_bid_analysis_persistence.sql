-- ============================================
-- Migration 022: Bid Analysis Persistence
-- ============================================
-- 공고 분석 결과를 bid_announcements에 직접 저장하여
-- 페이지 로드 시 실시간 분석 대신 DB 조회로 즉시 응답

-- 1) AI 분석 결과 컬럼 추가
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_status         TEXT DEFAULT 'pending'     -- pending | analyzing | analyzed | failed
        CHECK (analysis_status IN ('pending', 'analyzing', 'analyzed', 'failed'));

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    rfp_summary             JSONB,                      -- [{label, value?, items?}] 구조

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    rfp_sections            JSONB,                      -- 추출된 섹션 배열

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    suitability_score       INT,                        -- 0-100 적합성 점수

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    verdict                 TEXT,                       -- 추천 | 검토 필요 | 제외

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    fit_level               TEXT,                       -- 적극 추천 | 추천 | 보통 | 낮음

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    positive                TEXT[],                     -- 긍정 요소 배열

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    negative                TEXT[],                     -- 부정 요소 배열

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    recommended_teams       TEXT[],                     -- 추천 팀 배열

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    action_plan             TEXT,                       -- 권장 액션 계획

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    rfp_period              TEXT,                       -- 과업 기간

-- 2) 첨부파일 정보 컬럼
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    attachment_urls         JSONB,                      -- {분류: [{name, url, type}]} 구조

-- 3) 분석 메타데이터
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_started_at     TIMESTAMPTZ,                -- 분석 시작 시간

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_completed_at   TIMESTAMPTZ,                -- 분석 완료 시간

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_duration_seconds INT,                      -- 분석 소요 시간

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_error          TEXT,                       -- 분석 실패 시 에러 메시지

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    analysis_retry_count    INT DEFAULT 0,              -- 재시도 횟수

-- 4) Supabase Storage 경로
ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    md_rfp_analysis_path    TEXT,                       -- RFP分析.md 경로

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    md_notice_path          TEXT,                       -- 공고문.md 경로

ALTER TABLE bid_announcements ADD COLUMN IF NOT EXISTS
    md_instruction_path     TEXT;                       -- 과업지시서.md 경로

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_bid_announcements_analysis_status 
    ON bid_announcements(analysis_status);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_analysis_completed 
    ON bid_announcements(analysis_completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_suitability_score 
    ON bid_announcements(suitability_score DESC) 
    WHERE analysis_status = 'analyzed';

-- 성능용 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_announcements_status_score 
    ON bid_announcements(analysis_status, suitability_score DESC);
