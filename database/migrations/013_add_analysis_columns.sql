-- 공고 분석 관련 컬럼 추가
ALTER TABLE bid_announcements
ADD COLUMN IF NOT EXISTS analysis_status TEXT DEFAULT 'pending',  -- pending|analyzing|analyzed|failed
ADD COLUMN IF NOT EXISTS rfp_summary TEXT,                        -- RFP 요약
ADD COLUMN IF NOT EXISTS rfp_sections JSONB,                      -- RFP 섹션 구조
ADD COLUMN IF NOT EXISTS suitability_score FLOAT,                 -- 적합도 점수 (0-100)
ADD COLUMN IF NOT EXISTS verdict TEXT,                            -- Go/No-Go 판정
ADD COLUMN IF NOT EXISTS fit_level TEXT,                          -- 적합도 레벨 (High/Medium/Low)
ADD COLUMN IF NOT EXISTS positive JSONB DEFAULT '[]'::JSONB,     -- 긍정 요소
ADD COLUMN IF NOT EXISTS negative JSONB DEFAULT '[]'::JSONB,     -- 부정 요소
ADD COLUMN IF NOT EXISTS action_plan TEXT,                        -- 실행 계획
ADD COLUMN IF NOT EXISTS recommended_teams JSONB DEFAULT '[]'::JSONB, -- 추천 팀
ADD COLUMN IF NOT EXISTS rfp_period JSONB,                        -- RFP 기간 정보
ADD COLUMN IF NOT EXISTS analysis_completed_at TIMESTAMPTZ,       -- 분석 완료 시간
ADD COLUMN IF NOT EXISTS analysis_started_at TIMESTAMPTZ,         -- 분석 시작 시간
ADD COLUMN IF NOT EXISTS analysis_error TEXT;                     -- 분석 실패 메시지

-- 분석 상태 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_bid_announcements_analysis_status ON bid_announcements(analysis_status);
