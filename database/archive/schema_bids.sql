-- ============================================================
-- Tenopa Proposer -- Bid Recommendation Schema
-- ============================================================
-- 의존성: teams 테이블 (schema.sql 또는 supabase_schema.sql)
-- 적용 순서: schema.sql → schema_bids.sql

-- ── 1. 입찰 공고 원문 (전역 캐시, 팀 구분 없음) ──────────────

CREATE TABLE IF NOT EXISTS bid_announcements (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_no                  TEXT UNIQUE NOT NULL,          -- 입찰공고번호 (bidNtceNo)
    bid_title               TEXT NOT NULL,                 -- 공고명 (bidNtceNm)
    agency                  TEXT NOT NULL,                 -- 발주기관 (ntcInsttNm)
    bid_type                TEXT,                          -- 공고종류 (bidClsfcNm)
    budget_amount           BIGINT,                        -- 추정가격 (원, presmptPrceAmt)
    announce_date           DATE,                          -- 공고일
    deadline_date           TIMESTAMPTZ,                   -- 입찰마감일시 (bfSpecRgstDt)
    days_remaining          INTEGER,                       -- 수집 시점 잔여일 (계산값)
    content_text            TEXT,                          -- 공고 상세내용 (규격서, 자격요건)
    qualification_available BOOLEAN NOT NULL DEFAULT true, -- 자격요건 텍스트 확보 여부
    raw_data                JSONB,                         -- API 원본 응답
    fetched_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bid_announcements_deadline_idx  ON bid_announcements(deadline_date);
CREATE INDEX IF NOT EXISTS bid_announcements_bid_type_idx  ON bid_announcements(bid_type);
CREATE INDEX IF NOT EXISTS bid_announcements_agency_idx    ON bid_announcements(agency);
CREATE INDEX IF NOT EXISTS bid_announcements_fetched_at_idx ON bid_announcements(fetched_at);

-- 만료 공고 정리: deadline_date < now() - interval '7 days' 건 앱 레벨에서 주기적 삭제

-- ── 2. 팀 입찰 프로필 (AI 매칭·자격 판정용, 팀 단위 소유) ───

CREATE TABLE IF NOT EXISTS team_bid_profiles (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                     UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    expertise_areas             TEXT[] NOT NULL DEFAULT '{}',  -- 전문분야 배열
    tech_keywords               TEXT[] NOT NULL DEFAULT '{}',  -- 보유기술 키워드 배열
    past_projects               TEXT NOT NULL DEFAULT '',      -- 수행실적 요약 (자유 텍스트)
    company_size                TEXT,                          -- 개인/소기업/중기업/대기업
    certifications              TEXT[] NOT NULL DEFAULT '{}',  -- 보유 인증·자격 배열
    business_registration_type  TEXT,                          -- 개인/법인/중소기업/중견기업
    employee_count              INTEGER,                       -- 임직원 수
    founded_year                INTEGER,                       -- 설립연도
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(team_id)                                            -- 팀당 프로필 1개
);

CREATE INDEX IF NOT EXISTS team_bid_profiles_team_idx ON team_bid_profiles(team_id);

-- ── 3. 검색 조건 프리셋 (나라장터 필터용, 팀 단위 소유) ──────

CREATE TABLE IF NOT EXISTS search_presets (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id            UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name               TEXT NOT NULL,                     -- 프리셋명
    keywords           TEXT[] NOT NULL,                   -- 검색 키워드 배열 (최대 5개)
    min_budget         BIGINT NOT NULL DEFAULT 100000000, -- 최소 사업금액 (기본: 1억)
    min_days_remaining INTEGER NOT NULL DEFAULT 5,        -- 최소 잔여일 (기본: 5일)
    bid_types          TEXT[] NOT NULL DEFAULT '{용역}',  -- 공고종류 필터
    preferred_agencies        TEXT[] NOT NULL DEFAULT '{}',      -- 선호 발주기관 (빈 배열 = 전체)
    announce_date_range_days  INTEGER NOT NULL DEFAULT 14,       -- 공고 등록일 기준 검색 기간 (일, 0=제한없음)
    is_active          BOOLEAN NOT NULL DEFAULT false,
    last_fetched_at    TIMESTAMPTZ,                       -- 마지막 수집 시각 (Rate Limit용)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 기존 테이블에 컬럼 추가 (이미 존재하는 경우 무시)
ALTER TABLE search_presets ADD COLUMN IF NOT EXISTS announce_date_range_days INTEGER NOT NULL DEFAULT 14;

CREATE INDEX IF NOT EXISTS search_presets_team_idx ON search_presets(team_id);

-- 팀당 활성 프리셋 1개 보장 (partial unique index)
CREATE UNIQUE INDEX IF NOT EXISTS idx_search_presets_active
    ON search_presets(team_id) WHERE is_active = true;

-- ── 4. AI 분석 결과 캐시 (팀 + 공고 + 프리셋 단위) ──────────

CREATE TABLE IF NOT EXISTS bid_recommendations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                 UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    bid_no                  TEXT NOT NULL REFERENCES bid_announcements(bid_no) ON DELETE CASCADE,
    preset_id               UUID NOT NULL REFERENCES search_presets(id) ON DELETE CASCADE,

    -- 1단계: 자격 판정
    qualification_status    TEXT NOT NULL
                              CHECK (qualification_status IN ('pass', 'fail', 'ambiguous')),
    disqualification_reason TEXT,              -- fail일 때 제외 이유
    qualification_notes     TEXT,              -- ambiguous일 때 불명확 사유

    -- 2단계: 매칭 점수 (qualification_status = 'fail'이면 NULL)
    match_score             INTEGER CHECK (match_score >= 0 AND match_score <= 100),
    match_grade             TEXT CHECK (match_grade IN ('S', 'A', 'B', 'C', 'D')),
    recommendation_summary  TEXT,              -- 1줄 추천 요약
    recommendation_reasons  JSONB,             -- [{category, reason, strength}] 1개 이상
    risk_factors            JSONB,             -- [{risk, level}]
    win_probability_hint    TEXT,              -- 상/중상/중/중하/하
    recommended_action      TEXT,              -- 적극 검토/검토/보류

    analyzed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ,                  -- 24h TTL
    UNIQUE(team_id, bid_no, preset_id)
);

CREATE INDEX IF NOT EXISTS bid_recommendations_team_idx     ON bid_recommendations(team_id);
CREATE INDEX IF NOT EXISTS bid_recommendations_preset_idx   ON bid_recommendations(preset_id);
CREATE INDEX IF NOT EXISTS bid_recommendations_score_idx    ON bid_recommendations(match_score DESC);
CREATE INDEX IF NOT EXISTS bid_recommendations_expires_idx  ON bid_recommendations(expires_at);
CREATE INDEX IF NOT EXISTS bid_recommendations_status_idx   ON bid_recommendations(qualification_status);
