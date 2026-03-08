-- ============================================================
-- 마이그레이션: bid 추천 테이블 최초 생성 + 검색 기간 컬럼 추가
-- 실행 위치: Supabase Dashboard > SQL Editor
-- URL: https://supabase.com/dashboard/project/inuuyaxddgbxexljfykg/sql/new
-- ============================================================

-- ── 1. bid_announcements ────────────────────────────────────

CREATE TABLE IF NOT EXISTS bid_announcements (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_no                  TEXT UNIQUE NOT NULL,
    bid_title               TEXT NOT NULL,
    agency                  TEXT NOT NULL,
    bid_type                TEXT,
    budget_amount           BIGINT,
    announce_date           DATE,
    deadline_date           TIMESTAMPTZ,
    days_remaining          INTEGER,
    content_text            TEXT,
    qualification_available BOOLEAN NOT NULL DEFAULT true,
    raw_data                JSONB,
    fetched_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bid_announcements_deadline_idx   ON bid_announcements(deadline_date);
CREATE INDEX IF NOT EXISTS bid_announcements_bid_type_idx   ON bid_announcements(bid_type);
CREATE INDEX IF NOT EXISTS bid_announcements_agency_idx     ON bid_announcements(agency);
CREATE INDEX IF NOT EXISTS bid_announcements_fetched_at_idx ON bid_announcements(fetched_at);

-- ── 2. team_bid_profiles ────────────────────────────────────

CREATE TABLE IF NOT EXISTS team_bid_profiles (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                     UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    expertise_areas             TEXT[] NOT NULL DEFAULT '{}',
    tech_keywords               TEXT[] NOT NULL DEFAULT '{}',
    past_projects               TEXT NOT NULL DEFAULT '',
    company_size                TEXT,
    certifications              TEXT[] NOT NULL DEFAULT '{}',
    business_registration_type  TEXT,
    employee_count              INTEGER,
    founded_year                INTEGER,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(team_id)
);

CREATE INDEX IF NOT EXISTS team_bid_profiles_team_idx ON team_bid_profiles(team_id);

-- ── 3. search_presets (announce_date_range_days 포함) ───────

CREATE TABLE IF NOT EXISTS search_presets (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                   UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name                      TEXT NOT NULL,
    keywords                  TEXT[] NOT NULL,
    min_budget                BIGINT NOT NULL DEFAULT 100000000,
    min_days_remaining        INTEGER NOT NULL DEFAULT 5,
    bid_types                 TEXT[] NOT NULL DEFAULT '{용역}',
    preferred_agencies        TEXT[] NOT NULL DEFAULT '{}',
    announce_date_range_days  INTEGER NOT NULL DEFAULT 14,
    is_active                 BOOLEAN NOT NULL DEFAULT false,
    last_fetched_at           TIMESTAMPTZ,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS search_presets_team_idx ON search_presets(team_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_search_presets_active
    ON search_presets(team_id) WHERE is_active = true;

-- 기존 search_presets 테이블이 있는 경우 컬럼만 추가
ALTER TABLE search_presets
    ADD COLUMN IF NOT EXISTS announce_date_range_days INTEGER NOT NULL DEFAULT 14;

-- ── 4. bid_recommendations ──────────────────────────────────

CREATE TABLE IF NOT EXISTS bid_recommendations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                 UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    bid_no                  TEXT NOT NULL REFERENCES bid_announcements(bid_no) ON DELETE CASCADE,
    preset_id               UUID NOT NULL REFERENCES search_presets(id) ON DELETE CASCADE,

    qualification_status    TEXT NOT NULL CHECK (qualification_status IN ('pass','fail','ambiguous')),
    disqualification_reason TEXT,
    qualification_notes     TEXT,

    match_score             INTEGER CHECK (match_score BETWEEN 0 AND 100),
    match_grade             TEXT CHECK (match_grade IN ('S','A','B','C','D')),
    recommendation_summary  TEXT,
    recommendation_reasons  JSONB NOT NULL DEFAULT '[]',
    risk_factors            JSONB NOT NULL DEFAULT '[]',
    win_probability_hint    TEXT,
    recommended_action      TEXT,

    analyzed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at              TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '24 hours'),

    UNIQUE(team_id, bid_no, preset_id)
);

CREATE INDEX IF NOT EXISTS bid_recommendations_team_preset_idx ON bid_recommendations(team_id, preset_id);
CREATE INDEX IF NOT EXISTS bid_recommendations_score_idx       ON bid_recommendations(match_score DESC);
CREATE INDEX IF NOT EXISTS bid_recommendations_expires_idx     ON bid_recommendations(expires_at);
