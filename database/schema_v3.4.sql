-- ============================================
-- TENOPA v3.4 통합 스키마
-- 설계 문서 §15 기반
-- ============================================

-- 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector 시맨틱 검색

-- ============================================
-- 자동 업데이트 트리거 함수
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- §15-1. 조직·사용자 테이블
-- ============================================

CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE divisions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) NOT NULL,
    name        TEXT NOT NULL,
    teams_webhook_url TEXT,  -- 팀별 Teams Incoming Webhook URL
    monitor_keywords  TEXT[] DEFAULT '{}',  -- G2B 모니터링 검색 키워드
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id),
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',  -- member | lead | director | executive | admin
    team_id     UUID REFERENCES teams(id),
    division_id UUID REFERENCES divisions(id),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    azure_ad_oid TEXT UNIQUE,
    notification_settings JSONB DEFAULT '{"teams": true, "in_app": true}'::jsonb,
    status      TEXT DEFAULT 'active',  -- active | inactive | suspended (ULM)
    deactivated_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §15-2. 자사 역량 DB
-- ============================================

CREATE TABLE capabilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    type        TEXT NOT NULL,  -- track_record | tech | personnel
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL,
    keywords    TEXT[],
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TRIGGER update_capabilities_updated_at BEFORE UPDATE ON capabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §15-3. 제안 프로젝트 테이블
-- ============================================

CREATE TABLE proposals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT,
    status          TEXT DEFAULT 'initialized',
    owner_id        UUID REFERENCES users(id),
    team_id         UUID REFERENCES teams(id),
    -- RFP 관련
    rfp_filename    TEXT,
    rfp_content     TEXT,
    rfp_content_truncated BOOLEAN DEFAULT false,
    -- 진행 상태
    current_phase   TEXT,
    phases_completed INTEGER DEFAULT 0,
    failed_phase    TEXT,
    -- Storage 업로드 경로
    storage_path_docx TEXT,
    storage_path_pptx TEXT,
    storage_path_hwpx TEXT,
    storage_path_rfp TEXT,
    storage_upload_failed BOOLEAN DEFAULT false,
    -- 결과
    win_result      TEXT,        -- 수주 | 패찰 | 유찰
    bid_amount      BIGINT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT proposals_status_check CHECK (
        status IN ('initialized','processing','searching','analyzing','strategizing',
                   'submitted','presented','won','lost','no_go','on_hold','expired',
                   'abandoned','retrospect','completed')
    )
);

CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_proposals_team ON proposals(team_id);
CREATE INDEX idx_proposals_division ON proposals(division_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_org ON proposals(org_id);

-- 프로젝트 참여자 (다대다)
CREATE TABLE project_participants (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id),
    role_in_project TEXT DEFAULT 'member',  -- member | section_lead
    assigned_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (proposal_id, user_id)
);

-- ============================================
-- §15-4. 산출물·피드백·승인·Compliance
-- ============================================

CREATE TABLE artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER DEFAULT 1,
    content         TEXT NOT NULL,
    created_by      UUID REFERENCES users(id),
    -- v3.3: 버전 관리 강화
    change_summary  TEXT,
    change_source   VARCHAR(50),  -- ai_generated | human_edited | quality_gate | final
    quality_score   DECIMAL(5,2),
    diff_from_previous JSONB,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, step, version)
);

CREATE TABLE feedbacks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER,
    feedback        TEXT NOT NULL,
    comments        JSONB,
    rework_targets  JSONB,
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    approved_by     UUID REFERENCES users(id),
    approver_role   TEXT,  -- lead | director | executive
    approved_at     TIMESTAMPTZ,
    decision        TEXT,  -- approved | rejected
    positioning     TEXT,
    chain_status    JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE compliance_matrix (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    req_id          TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_step     TEXT NOT NULL,
    status          TEXT DEFAULT '미확인',
    proposal_section TEXT,
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, req_id)
);

-- ============================================
-- §15-5. 검색·캐시·알림·감사
-- ============================================

CREATE TABLE search_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    bid_no          TEXT NOT NULL,
    project_name    TEXT NOT NULL,
    client          TEXT,
    budget          TEXT,
    deadline        TEXT,
    project_summary TEXT,
    key_requirements JSONB,
    eval_method     TEXT,
    competition_level TEXT,
    fit_score       INTEGER,
    fit_rationale   TEXT,
    expected_positioning TEXT,
    brief_analysis  TEXT,
    picked          BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE g2b_cache (
    cache_key       TEXT PRIMARY KEY,
    endpoint        TEXT,
    response        JSONB NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE g2b_monitor_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id         UUID REFERENCES teams(id),
    bid_notice_no   TEXT NOT NULL,          -- 공고번호
    title           TEXT,                   -- 공고명
    notified_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(team_id, bid_notice_no)
);

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    type            TEXT NOT NULL,  -- approval_request | approval_result | deadline | result
    title           TEXT NOT NULL,
    body            TEXT,
    link            TEXT,
    is_read         BOOLEAN DEFAULT false,
    teams_sent      BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          TEXT NOT NULL,  -- approve | reject | create | update | delete
    resource_type   TEXT NOT NULL,  -- proposal | capability | user | approval
    resource_id     UUID,
    detail          JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ============================================
-- §15-5b. KB Part B — 콘텐츠 라이브러리
-- ============================================

CREATE TABLE content_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,  -- section_block | paragraph | standard_answer | diagram_desc | performance_desc | qa_record
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    source_project_id UUID REFERENCES proposals(id),
    author_id       UUID REFERENCES users(id),
    industry        TEXT,
    tech_area       TEXT,
    rfp_type        TEXT,
    tags            TEXT[],
    status          TEXT DEFAULT 'draft',  -- draft | published | archived
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

CREATE INDEX idx_content_embedding ON content_library USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_content_status ON content_library(status);
CREATE INDEX idx_content_org ON content_library(org_id);

CREATE TRIGGER update_content_library_updated_at BEFORE UPDATE ON content_library
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §15-5c. KB Part C — 발주기관 DB
-- ============================================

CREATE TABLE client_intelligence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    client_name     TEXT NOT NULL,
    client_type     TEXT,       -- 중앙부처 | 지자체 | 공공기관 | 기타
    scale           TEXT,       -- 대규모 | 중규모 | 소규모
    parent_ministry TEXT,
    location        TEXT,
    relationship    TEXT DEFAULT 'neutral',  -- new | neutral | friendly | close
    relationship_history JSONB DEFAULT '[]',
    eval_tendency   TEXT,
    contact_info    JSONB,
    notes           TEXT,
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE client_bid_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES client_intelligence(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    positioning     TEXT,
    result          TEXT,  -- won | lost | no_go | expired
    bid_year        INTEGER,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_embedding ON client_intelligence USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TRIGGER update_client_intelligence_updated_at BEFORE UPDATE ON client_intelligence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §15-5d. KB Part D — 경쟁사 DB
-- ============================================

CREATE TABLE competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    company_name    TEXT NOT NULL,
    scale           TEXT,       -- 대기업 | 중견 | 중소
    primary_area    TEXT,
    strengths       TEXT,
    weaknesses      TEXT,
    price_pattern   TEXT,       -- aggressive | conservative | moderate
    avg_win_rate    NUMERIC(5,2),
    notes           TEXT,
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE competitor_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID REFERENCES competitors(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_used   TEXT,
    our_result      TEXT,       -- won | lost
    competitor_result TEXT,     -- won | lost | unknown
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_competitor_embedding ON competitors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TRIGGER update_competitors_updated_at BEFORE UPDATE ON competitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §15-5e. KB Part E — 교훈 아카이브
-- ============================================

CREATE TABLE lessons_learned (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_summary TEXT,
    effective_points TEXT,
    weak_points     TEXT,
    improvements    TEXT,
    failure_category TEXT,  -- price | tech | track_record | strategy | format
    failure_detail  TEXT,
    positioning     TEXT,
    client_name     TEXT,
    industry        TEXT,
    result          TEXT,  -- won | lost | no_go | expired | abandoned
    embedding       vector(1536),
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lessons_embedding ON lessons_learned USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- ============================================
-- §15-5f. 크로스팀 + 컨소시엄
-- ============================================

CREATE TABLE project_teams (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    team_id     UUID REFERENCES teams(id),
    role        TEXT DEFAULT 'participating',  -- lead | participating
    PRIMARY KEY (proposal_id, team_id)
);

CREATE TABLE consortium_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    company_name    TEXT NOT NULL,
    role            TEXT NOT NULL,  -- lead | partner
    scope           TEXT,
    personnel_count INTEGER,
    share_amount    BIGINT,
    contact_name    TEXT,
    contact_email   TEXT,
    contact_phone   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- §15-5g. AI 실행 상태 + 동시 편집 잠금 + 회사 템플릿
-- ============================================

CREATE TABLE ai_task_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    sub_task        TEXT,
    status          TEXT NOT NULL,  -- running | complete | error | paused | no_response
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    model           TEXT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ai_task_proposal ON ai_task_logs(proposal_id, step);

CREATE TABLE section_locks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    section_id      TEXT NOT NULL,
    locked_by       UUID REFERENCES users(id),
    locked_at       TIMESTAMPTZ DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    UNIQUE(proposal_id, section_id)
);

CREATE TABLE company_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,  -- docx | pptx
    name            TEXT NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,
    version         INTEGER DEFAULT 1,
    is_active       BOOLEAN DEFAULT true,
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE presentation_qa (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    evaluator_reaction TEXT,  -- positive | neutral | negative
    memo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 임시 위임 (ULM-07)
CREATE TABLE approval_delegations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delegator_id    UUID REFERENCES users(id) NOT NULL,
    delegate_id     UUID REFERENCES users(id) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    reason          TEXT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================
-- §15-5h. 노임단가 테이블 (v3.3)
-- ============================================

CREATE TABLE labor_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_org VARCHAR(100) NOT NULL,  -- KOSA | KEA | MOEF
    year INTEGER NOT NULL,
    grade VARCHAR(50) NOT NULL,  -- 기술사 | 특급 | 고급 | 중급 | 초급
    monthly_rate BIGINT NOT NULL,
    daily_rate BIGINT,
    effective_date DATE,
    source_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_labor_rates_lookup ON labor_rates(standard_org, year, grade);

-- ============================================
-- §15-5i. 시장 낙찰가 벤치마크 (v3.3)
-- ============================================

CREATE TABLE market_price_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    project_title VARCHAR(500),
    client_org VARCHAR(200),
    domain VARCHAR(100) NOT NULL,  -- SI/SW개발 | 정책연구 | 성과분석 | 컨설팅
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

CREATE INDEX idx_market_price_domain_year ON market_price_data(domain, year);
CREATE INDEX idx_market_price_budget ON market_price_data(budget);

-- ============================================
-- §15-6. RLS (Row Level Security) 정책
-- ============================================

-- RLS 활성화
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_library ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons_learned ENABLE ROW LEVEL SECURITY;
ALTER TABLE labor_rates ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_price_data ENABLE ROW LEVEL SECURITY;

-- Service Role 전체 접근
CREATE POLICY "service_role_all" ON organizations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON divisions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON teams FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON users FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON capabilities FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON proposals FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON artifacts FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON feedbacks FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON approvals FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON notifications FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON content_library FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON client_intelligence FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON competitors FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON lessons_learned FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON labor_rates FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_role_all" ON market_price_data FOR ALL USING (auth.role() = 'service_role');

-- 조직: 같은 org만 조회
CREATE POLICY "org_read_self" ON organizations FOR SELECT
  USING (id = (SELECT org_id FROM users WHERE id = auth.uid()));

-- 본부: 같은 org만 조회
CREATE POLICY "org_divisions" ON divisions FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));

-- 팀: 같은 org만 조회
CREATE POLICY "org_teams" ON teams FOR SELECT
  USING (division_id IN (SELECT id FROM divisions WHERE org_id = (SELECT org_id FROM users WHERE id = auth.uid())));

-- 사용자: 같은 org만 조회
CREATE POLICY "org_users" ON users FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));

-- 역량 DB: 같은 org 조회
CREATE POLICY "org_capabilities" ON capabilities FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
CREATE POLICY "admin_manage_capabilities" ON capabilities FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- 프로젝트: 참여자 또는 생성자
CREATE POLICY "member_select_proposals" ON proposals FOR SELECT
  USING (
    id IN (SELECT proposal_id FROM project_participants WHERE user_id = auth.uid())
    OR created_by = auth.uid()
  );
-- 팀장: 소속 팀 전체
CREATE POLICY "lead_select_proposals" ON proposals FOR SELECT
  USING (
    team_id = (SELECT team_id FROM users WHERE id = auth.uid())
    AND (SELECT role FROM users WHERE id = auth.uid()) IN ('lead', 'admin')
  );
-- 본부장: 소속 본부 전체
CREATE POLICY "director_select_proposals" ON proposals FOR SELECT
  USING (
    division_id = (SELECT division_id FROM users WHERE id = auth.uid())
    AND (SELECT role FROM users WHERE id = auth.uid()) IN ('director', 'admin')
  );
-- 경영진: 전사
CREATE POLICY "executive_select_proposals" ON proposals FOR SELECT
  USING (
    (SELECT role FROM users WHERE id = auth.uid()) IN ('executive', 'admin')
  );

-- 알림: 본인 것만
CREATE POLICY "own_notifications" ON notifications FOR ALL
  USING (user_id = auth.uid());

-- KB: 같은 org
CREATE POLICY "org_content_published" ON content_library FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()) AND status = 'published');
CREATE POLICY "author_content_draft" ON content_library FOR SELECT
  USING (author_id = auth.uid() AND status = 'draft');

CREATE POLICY "org_clients" ON client_intelligence FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "org_competitors" ON competitors FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "org_lessons" ON lessons_learned FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));

-- 노임단가/낙찰가: 전체 읽기, admin만 관리
CREATE POLICY "all_users_read_labor_rates" ON labor_rates FOR SELECT USING (true);
CREATE POLICY "admin_manage_labor_rates" ON labor_rates FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "all_users_read_market_price" ON market_price_data FOR SELECT USING (true);
CREATE POLICY "admin_manage_market_price" ON market_price_data FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- ============================================
-- §15-7. 성과 추적 Materialized View
-- ============================================

CREATE MATERIALIZED VIEW team_performance AS
SELECT
    p.team_id,
    t.name AS team_name,
    d.name AS division_name,
    COUNT(*) FILTER (WHERE p.status IN ('draft','searching','analyzing','strategizing','submitted','presented','won','lost')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status IN ('draft','searching','analyzing','strategizing')) AS active_proposals,
    COUNT(*) FILTER (WHERE p.result = '수주') AS won_count,
    COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰')) AS decided_count,
    CASE
        WHEN COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰')) > 0
        THEN ROUND(
            COUNT(*) FILTER (WHERE p.result = '수주')::numeric /
            COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰'))::numeric * 100, 1
        )
        ELSE 0
    END AS win_rate,
    COALESCE(SUM(p.result_amount) FILTER (WHERE p.result = '수주'), 0) AS total_won_amount,
    AVG(EXTRACT(DAY FROM (p.result_at - p.created_at)))
        FILTER (WHERE p.result IS NOT NULL) AS avg_days_to_result
FROM proposals p
JOIN teams t ON p.team_id = t.id
JOIN divisions d ON p.division_id = d.id
GROUP BY p.team_id, t.name, d.name;

-- ============================================
-- Supabase RPC: 초기화 함수
-- ============================================

CREATE OR REPLACE FUNCTION mark_stale_running_proposals()
RETURNS void AS $$
BEGIN
    UPDATE proposals
    SET status = 'on_hold', hold_reason = '서버 재시작으로 인한 자동 보류'
    WHERE status IN ('searching', 'analyzing', 'strategizing')
    AND updated_at < now() - INTERVAL '30 minutes';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_expired_g2b_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM g2b_cache WHERE expires_at < now();
END;
$$ LANGUAGE plpgsql;
