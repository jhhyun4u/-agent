-- ============================================
-- Migration 005: 조직구조 + 입찰 모니터링 + users
-- Supabase SQL Editor에서 실행
-- ============================================

-- 0. 확장
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 0-1. 조직
CREATE TABLE IF NOT EXISTS organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 0-2. 본부
CREATE TABLE IF NOT EXISTS divisions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 0-3. 팀
CREATE TABLE IF NOT EXISTS teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) NOT NULL,
    name        TEXT NOT NULL,
    teams_webhook_url TEXT,
    specialty   TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id),
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',
    team_id     UUID REFERENCES teams(id),
    division_id UUID REFERENCES divisions(id),
    org_id      UUID REFERENCES organizations(id),
    azure_ad_oid TEXT UNIQUE,
    interests   TEXT[],
    must_change_password BOOLEAN DEFAULT false,
    notification_settings JSONB DEFAULT '{"teams": true, "in_app": true}'::jsonb,
    status      TEXT DEFAULT 'active',
    deactivated_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- 2. bid_announcements
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
CREATE INDEX IF NOT EXISTS bid_announcements_deadline_idx ON bid_announcements(deadline_date);
CREATE INDEX IF NOT EXISTS bid_announcements_days_idx ON bid_announcements(days_remaining);

-- 3. team_bid_profiles
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

-- 4. search_presets
CREATE TABLE IF NOT EXISTS search_presets (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id            UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name               TEXT NOT NULL,
    keywords           TEXT[] NOT NULL,
    min_budget         BIGINT NOT NULL DEFAULT 100000000,
    min_days_remaining INTEGER NOT NULL DEFAULT 5,
    bid_types          TEXT[] NOT NULL DEFAULT '{용역}',
    preferred_agencies TEXT[] NOT NULL DEFAULT '{}',
    announce_date_range_days INTEGER NOT NULL DEFAULT 14,
    is_active          BOOLEAN NOT NULL DEFAULT false,
    last_fetched_at    TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_search_presets_active
    ON search_presets(team_id) WHERE is_active = true;

-- 5. bid_recommendations
CREATE TABLE IF NOT EXISTS bid_recommendations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id                 UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    bid_no                  TEXT NOT NULL REFERENCES bid_announcements(bid_no) ON DELETE CASCADE,
    preset_id               UUID NOT NULL REFERENCES search_presets(id) ON DELETE CASCADE,
    qualification_status    TEXT NOT NULL CHECK (qualification_status IN ('pass', 'fail', 'ambiguous')),
    disqualification_reason TEXT,
    qualification_notes     TEXT,
    match_score             INTEGER CHECK (match_score >= 0 AND match_score <= 100),
    match_grade             TEXT CHECK (match_grade IN ('S', 'A', 'B', 'C', 'D')),
    recommendation_summary  TEXT,
    recommendation_reasons  JSONB,
    risk_factors            JSONB,
    win_probability_hint    TEXT,
    recommended_action      TEXT,
    analyzed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ,
    UNIQUE(team_id, bid_no, preset_id)
);
CREATE INDEX IF NOT EXISTS bid_recommendations_team_idx ON bid_recommendations(team_id);
CREATE INDEX IF NOT EXISTS bid_recommendations_score_idx ON bid_recommendations(match_score DESC);

-- 6. bid_bookmarks
CREATE TABLE IF NOT EXISTS bid_bookmarks (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id  UUID NOT NULL REFERENCES auth.users(id),
    bid_no   TEXT NOT NULL REFERENCES bid_announcements(bid_no) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, bid_no)
);
