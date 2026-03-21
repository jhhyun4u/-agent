-- 007: 누락 테이블 전체 생성 (schema_v3.4.sql 기반)
-- Supabase SQL Editor에서 실행
-- 2026-03-18

-- ============================================
-- §15-2. 자사 역량 DB
-- ============================================
CREATE TABLE IF NOT EXISTS capabilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    type        TEXT NOT NULL,
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL,
    keywords    TEXT[],
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- §15-5b. 콘텐츠 라이브러리
-- ============================================
CREATE TABLE IF NOT EXISTS content_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    source_project_id UUID REFERENCES proposals(id),
    author_id       UUID REFERENCES users(id),
    industry        TEXT,
    tech_area       TEXT,
    rfp_type        TEXT,
    tags            TEXT[],
    status          TEXT DEFAULT 'draft',
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    version         INTEGER DEFAULT 1,
    parent_id       UUID REFERENCES content_library(id),
    quality_score   NUMERIC(5,2) DEFAULT 0,
    reuse_count     INTEGER DEFAULT 0,
    won_count       INTEGER DEFAULT 0,
    lost_count      INTEGER DEFAULT 0,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_content_embedding ON content_library USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_library(status);
CREATE INDEX IF NOT EXISTS idx_content_org ON content_library(org_id);

-- ============================================
-- §15-5c. 발주기관 DB
-- ============================================
CREATE TABLE IF NOT EXISTS client_intelligence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    client_name     TEXT NOT NULL,
    client_type     TEXT,
    scale           TEXT,
    parent_ministry TEXT,
    location        TEXT,
    relationship    TEXT DEFAULT 'neutral',
    relationship_history JSONB DEFAULT '[]',
    eval_tendency   TEXT,
    contact_info    JSONB,
    notes           TEXT,
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS client_bid_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES client_intelligence(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    positioning     TEXT,
    result          TEXT,
    bid_year        INTEGER,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_client_embedding ON client_intelligence USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ============================================
-- §15-5d. 경쟁사 DB
-- ============================================
CREATE TABLE IF NOT EXISTS competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    company_name    TEXT NOT NULL,
    scale           TEXT,
    primary_area    TEXT,
    strengths       TEXT,
    weaknesses      TEXT,
    price_pattern   TEXT,
    avg_win_rate    NUMERIC(5,2),
    notes           TEXT,
    embedding       vector(1536),
    win_count       INTEGER DEFAULT 0,
    source          TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS competitor_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID REFERENCES competitors(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_used   TEXT,
    our_result      TEXT,
    competitor_result TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_competitor_embedding ON competitors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ============================================
-- §15-5e. 교훈 아카이브
-- ============================================
CREATE TABLE IF NOT EXISTS lessons_learned (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_summary TEXT,
    effective_points TEXT,
    weak_points     TEXT,
    improvements    TEXT,
    failure_category TEXT,
    failure_detail  TEXT,
    positioning     TEXT,
    client_name     TEXT,
    industry        TEXT,
    result          TEXT,
    embedding       vector(1536),
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lessons_embedding ON lessons_learned USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ============================================
-- §15-5f. 크로스팀 + 컨소시엄
-- ============================================
CREATE TABLE IF NOT EXISTS project_teams (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    team_id     UUID REFERENCES teams(id),
    role        TEXT DEFAULT 'participating',
    PRIMARY KEY (proposal_id, team_id)
);

CREATE TABLE IF NOT EXISTS consortium_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    company_name    TEXT NOT NULL,
    role            TEXT NOT NULL,
    scope           TEXT,
    personnel_count INTEGER,
    share_amount    BIGINT,
    contact_name    TEXT,
    contact_email   TEXT,
    contact_phone   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- §15-5g. 동시 편집 잠금 + 회사 템플릿 + Q&A
-- ============================================
CREATE TABLE IF NOT EXISTS section_locks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    section_id      TEXT NOT NULL,
    locked_by       UUID REFERENCES users(id),
    locked_at       TIMESTAMPTZ DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    UNIQUE(proposal_id, section_id)
);

CREATE TABLE IF NOT EXISTS company_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,
    version         INTEGER DEFAULT 1,
    is_active       BOOLEAN DEFAULT true,
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS presentation_qa (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    evaluator_reaction TEXT,
    memo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    -- PSM-16 확장
    embedding       vector(1536),
    content_library_id UUID REFERENCES content_library(id),
    category        TEXT DEFAULT 'general',
    created_by      UUID REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_presentation_qa_proposal_id ON presentation_qa (proposal_id);
CREATE INDEX IF NOT EXISTS idx_presentation_qa_category ON presentation_qa (category);

-- ============================================
-- §15-5h. 노임단가 (v3.3)
-- ============================================
CREATE TABLE IF NOT EXISTS labor_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_org VARCHAR(100) NOT NULL DEFAULT 'KOSA',
    year INTEGER NOT NULL,
    grade VARCHAR(50) NOT NULL,
    monthly_rate BIGINT NOT NULL,
    daily_rate BIGINT,
    effective_date DATE,
    source_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_labor_rates_lookup ON labor_rates(standard_org, year, grade);

-- ============================================
-- §15-5i. 시장 낙찰가 벤치마크 (v3.3)
-- ============================================
CREATE TABLE IF NOT EXISTS market_price_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    project_title VARCHAR(500),
    client_org VARCHAR(200),
    domain VARCHAR(100) NOT NULL,
    budget BIGINT,
    winning_price BIGINT,
    bid_ratio DECIMAL(5,4),
    num_bidders INTEGER,
    tech_price_ratio VARCHAR(20),
    evaluation_method VARCHAR(100),
    year INTEGER NOT NULL,
    source VARCHAR(200),
    collected_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_market_price_domain_year ON market_price_data(domain, year);

-- ============================================
-- 006: 누락 컬럼 추가
-- ============================================
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS positioning TEXT;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS cache_read_tokens INTEGER DEFAULT 0;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS cache_create_tokens INTEGER DEFAULT 0;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(10,6) DEFAULT 0;

-- ============================================
-- PSM-16: Q&A 시맨틱 검색 RPC
-- ============================================
CREATE OR REPLACE FUNCTION search_qa_by_embedding(
  query_embedding vector(1536), match_org_id UUID,
  match_count INT DEFAULT 10, filter_category TEXT DEFAULT NULL
) RETURNS TABLE (
  id UUID, proposal_id UUID, question TEXT, answer TEXT, category TEXT,
  evaluator_reaction TEXT, memo TEXT, created_at TIMESTAMPTZ, similarity FLOAT
) AS $$ BEGIN RETURN QUERY
  SELECT pq.id, pq.proposal_id, pq.question, pq.answer, pq.category,
    pq.evaluator_reaction, pq.memo, pq.created_at,
    1 - (pq.embedding <=> query_embedding) AS similarity
  FROM presentation_qa pq JOIN proposals p ON p.id = pq.proposal_id
  WHERE p.org_id = match_org_id AND pq.embedding IS NOT NULL
    AND (filter_category IS NULL OR pq.category = filter_category)
  ORDER BY pq.embedding <=> query_embedding LIMIT match_count;
END; $$ LANGUAGE plpgsql STABLE;
