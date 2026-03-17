# PostgreSQL 스키마 (Supabase)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [02-state-schema.md](02-state-schema.md), [14-services-v3.md](14-services-v3.md)
> **원본 섹션**: §15

---

## 15. PostgreSQL 스키마 (Supabase) — v2.0

> **v2.0 변경**: SQLite → Supabase PostgreSQL 전환. 조직·사용자·역할 테이블 추가, RLS 정책 적용.
> LangGraph checkpointer는 `PostgresSaver`가 자체 테이블을 생성하므로 여기서는 앱 데이터만 정의.

### 15-1. 조직·사용자 테이블

```sql
-- ── 조직 구조 ──

CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,              -- 회사명
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE divisions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    name        TEXT NOT NULL,              -- 본부명 (예: ICT사업본부)
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) NOT NULL,
    name        TEXT NOT NULL,              -- 팀명 (예: AI사업팀)
    teams_webhook_url TEXT,                 -- ★ 팀별 Teams Incoming Webhook URL
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id),  -- Supabase Auth 연동
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',  -- member | lead | director | executive | admin
    team_id     UUID REFERENCES teams(id),
    division_id UUID REFERENCES divisions(id),   -- 본부장·경영진은 team 없이 division만
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    azure_ad_oid TEXT UNIQUE,                    -- Azure AD Object ID (SSO 매핑)
    notification_settings JSONB DEFAULT '{"teams": true, "in_app": true}'::jsonb,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ★ 프로젝트 참여자 (다대다)
CREATE TABLE project_participants (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id),
    role_in_project TEXT DEFAULT 'member',  -- member | section_lead
    assigned_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (proposal_id, user_id)
);
```

### 15-2. 자사 역량 DB

```sql
CREATE TABLE capabilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,  -- 회사 소속
    type        TEXT NOT NULL,              -- track_record | tech | personnel
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL,
    keywords    TEXT[],                     -- ★ PostgreSQL 배열
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE capabilities ENABLE ROW LEVEL SECURITY;

-- 같은 회사 내 모든 사용자 조회 가능
CREATE POLICY "org_capabilities" ON capabilities FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
-- 수정은 admin만
CREATE POLICY "admin_manage_capabilities" ON capabilities FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-3. 제안 프로젝트 테이블

```sql
CREATE TABLE proposals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    client          TEXT,
    deadline        TIMESTAMPTZ,
    positioning     TEXT,                   -- defensive | offensive | adjacent
    mode            TEXT DEFAULT 'full',    -- lite | full
    picked_bid_no   TEXT,
    bid_detail      JSONB,                  -- BidDetail JSON
    search_query    JSONB,                  -- 초기 검색 조건
    sales_intel     TEXT,
    status          TEXT DEFAULT 'active',  -- active | no_go | completed | won | lost
    result          TEXT,                   -- ★ 수주 | 패찰 | 유찰 (팀장 입력)
    result_amount   BIGINT,                -- ★ 수주액 (원)
    result_reason   TEXT,                   -- ★ 패찰 사유
    result_at       TIMESTAMPTZ,
    thread_id       TEXT UNIQUE,
    -- ★ v2.0: 소유·조직
    team_id         UUID REFERENCES teams(id) NOT NULL,
    division_id     UUID REFERENCES divisions(id) NOT NULL,
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    created_by      UUID REFERENCES users(id) NOT NULL,
    budget_amount   BIGINT,                -- ★ 예산액 (원, 결재선 판단 기준)
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### 15-4. 산출물·피드백·승인·Compliance

```sql
CREATE TABLE artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER DEFAULT 1,
    content         TEXT NOT NULL,
    created_by      UUID REFERENCES users(id),
    -- ★ v3.3: 버전 관리 강화 (ProposalForge 비교 검토 반영)
    change_summary  TEXT,                -- 변경 요약 (AI 자동 생성 / 사람 피드백 / 품질게이트)
    change_source   VARCHAR(50),         -- 'ai_generated'|'human_edited'|'quality_gate'|'final'
    quality_score   DECIMAL(5,2),        -- 해당 버전의 자가진단 점수
    diff_from_previous JSONB,            -- 이전 버전 대비 변경 상세
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, step, version)
);

CREATE TABLE feedbacks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER,
    feedback        TEXT NOT NULL,
    comments        JSONB,                  -- 항목별 코멘트
    rework_targets  JSONB,                  -- 부분 재작업 대상
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    approved_by     UUID REFERENCES users(id),
    approver_role   TEXT,                   -- ★ lead | director | executive
    approved_at     TIMESTAMPTZ,
    decision        TEXT,                   -- approved | rejected
    positioning     TEXT,
    chain_status    JSONB,                  -- ★ 결재선 전체 이력 JSON
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
```

### 15-5. 검색·캐시·알림·감사

```sql
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
    response        JSONB NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ★ v2.0: 알림
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    type            TEXT NOT NULL,           -- approval_request | approval_result | deadline | result
    title           TEXT NOT NULL,
    body            TEXT,
    link            TEXT,                    -- 프로젝트 URL
    is_read         BOOLEAN DEFAULT false,
    teams_sent      BOOLEAN DEFAULT false,   -- Teams 발송 여부
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ★ v2.0: 감사 로그
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          TEXT NOT NULL,           -- approve | reject | create | update | delete
    resource_type   TEXT NOT NULL,           -- proposal | capability | user | approval
    resource_id     UUID,
    detail          JSONB,                   -- 변경 상세
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_proposals_team ON proposals(team_id);
CREATE INDEX idx_proposals_division ON proposals(division_id);
CREATE INDEX idx_proposals_status ON proposals(status);
```

### 15-5a. ★ v3.0: 프로젝트 상태 머신 확장

```sql
-- proposals 테이블 status 확장 (v2.0의 status 컬럼을 대체)
-- 유효값: draft | searching | analyzing | strategizing | submitted | presented | won | lost | no_go | on_hold | expired | abandoned | retrospect
-- + current_step 필드 추가 (PSM-01a)

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS current_step TEXT;  -- STEP 2/3/4/5 (strategizing 내 활성 단계)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS previous_status TEXT;  -- on_hold 전환 시 이전 상태 보존
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS hold_reason TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS abandon_reason TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_at TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_location TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presenter TEXT;

-- status 유효값 제약
ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_status_check;
ALTER TABLE proposals ADD CONSTRAINT proposals_status_check
  CHECK (status IN ('draft','searching','analyzing','strategizing','submitted','presented','won','lost','no_go','on_hold','expired','abandoned','retrospect'));
```

### 15-5b. ★ v3.0: KB Part B — 콘텐츠 라이브러리

```sql
CREATE TABLE content_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,           -- section_block | paragraph | standard_answer | diagram_desc | performance_desc | qa_record
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    -- 메타데이터
    source_project_id UUID REFERENCES proposals(id),  -- 출처 프로젝트
    author_id       UUID REFERENCES users(id),
    industry        TEXT,                    -- 산업분야 태그
    tech_area       TEXT,                    -- 기술영역 태그
    rfp_type        TEXT,                    -- RFP 유형 태그
    tags            TEXT[],                  -- 추가 태그
    -- 거버넌스
    status          TEXT DEFAULT 'draft',    -- draft | published | archived
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    version         INTEGER DEFAULT 1,
    parent_id       UUID REFERENCES content_library(id),  -- 버전 관리 (이전 버전 참조)
    -- 품질 점수
    quality_score   NUMERIC(5,2) DEFAULT 0,  -- 수주 기여도 + 재사용 횟수 + 최신성
    reuse_count     INTEGER DEFAULT 0,
    won_count       INTEGER DEFAULT 0,       -- 이 콘텐츠 포함 제안서 수주 횟수
    lost_count      INTEGER DEFAULT 0,
    -- 벡터
    embedding       vector(1536),            -- pgvector 시맨틱 검색용
    -- 타임스탬프
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_content_embedding ON content_library USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_content_status ON content_library(status);
CREATE INDEX idx_content_org ON content_library(org_id);

ALTER TABLE content_library ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_content_published" ON content_library FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()) AND status = 'published');
CREATE POLICY "author_content_draft" ON content_library FOR SELECT
  USING (author_id = auth.uid() AND status = 'draft');
```

### 15-5c. ★ v3.0: KB Part C — 발주기관 DB

```sql
CREATE TABLE client_intelligence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    client_name     TEXT NOT NULL,            -- 기관명
    client_type     TEXT,                     -- 중앙부처 | 지자체 | 공공기관 | 기타
    scale           TEXT,                     -- 대규모 | 중규모 | 소규모
    parent_ministry TEXT,                     -- 관할 부처
    location        TEXT,                     -- 소재지
    relationship    TEXT DEFAULT 'neutral',   -- new | neutral | friendly | close
    relationship_history JSONB DEFAULT '[]',  -- 관계 수준 변경 이력
    eval_tendency   TEXT,                     -- 평가 성향 메모 (기술중시/가격중시/혁신선호)
    contact_info    JSONB,                    -- 내부 영업 담당자, 기관 측 접점 (개인정보 최소화)
    notes           TEXT,                     -- 자유 텍스트 메모
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 발주기관 ↔ 프로젝트 자동 연결 (과거 입찰 이력)
CREATE TABLE client_bid_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES client_intelligence(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    positioning     TEXT,                     -- 이 기관에서의 포지셔닝
    result          TEXT,                     -- won | lost | no_go | expired
    bid_year        INTEGER,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_embedding ON client_intelligence USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE client_intelligence ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_clients" ON client_intelligence FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5d. ★ v3.0: KB Part D — 경쟁사 DB

```sql
CREATE TABLE competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    company_name    TEXT NOT NULL,
    scale           TEXT,                     -- 대기업 | 중견 | 중소
    primary_area    TEXT,                     -- 주력 분야
    strengths       TEXT,                     -- 강점 요약
    weaknesses      TEXT,                     -- 약점 요약
    price_pattern   TEXT,                     -- aggressive | conservative | moderate
    avg_win_rate    NUMERIC(5,2),             -- 평균 낙찰률
    notes           TEXT,
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 경쟁사 ↔ 프로젝트 경쟁 이력
CREATE TABLE competitor_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID REFERENCES competitors(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_used   TEXT,                     -- 이 업체와 경쟁 시 사용한 전략
    our_result      TEXT,                     -- won | lost
    competitor_result TEXT,                   -- won | lost | unknown
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_competitor_embedding ON competitors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_competitors" ON competitors FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5e. ★ v3.0: KB Part E — 교훈 아카이브

```sql
CREATE TABLE lessons_learned (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    -- 회고 데이터
    strategy_summary TEXT,                    -- 사용된 전략 요약
    effective_points TEXT,                    -- 효과적이었던 점
    weak_points     TEXT,                     -- 부족했던 점
    improvements    TEXT,                     -- 다음 개선 포인트
    -- 패찰 시 구조화 기록
    failure_category TEXT,                    -- price | tech | track_record | strategy | format
    failure_detail  TEXT,
    -- 메타
    positioning     TEXT,                     -- 사용된 포지셔닝
    client_name     TEXT,
    industry        TEXT,
    result          TEXT,                     -- won | lost | no_go | expired | abandoned
    embedding       vector(1536),
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lessons_embedding ON lessons_learned USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE lessons_learned ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_lessons" ON lessons_learned FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5f. ★ v3.0: 크로스팀 프로젝트 + 컨소시엄

```sql
-- 크로스팀: 참여 팀 (주관 팀은 proposals.team_id)
CREATE TABLE project_teams (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    team_id     UUID REFERENCES teams(id),
    role        TEXT DEFAULT 'participating',  -- lead | participating
    PRIMARY KEY (proposal_id, team_id)
);

-- 컨소시엄 구성
CREATE TABLE consortium_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    company_name    TEXT NOT NULL,             -- 참여사명
    role            TEXT NOT NULL,             -- lead(자사) | partner
    scope           TEXT,                      -- 담당 범위
    personnel_count INTEGER,                   -- 투입 인력 수
    share_amount    BIGINT,                    -- 분담 금액
    contact_name    TEXT,
    contact_email   TEXT,
    contact_phone   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 15-5g. ★ v3.0: AI 실행 상태 + 동시 편집 잠금 + 회사 템플릿

```sql
-- AI 작업 실행 이력 (AGT-09)
CREATE TABLE ai_task_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    sub_task        TEXT,                      -- 병렬 하위 작업명
    status          TEXT NOT NULL,             -- running | complete | error | paused | no_response
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

-- 섹션 편집 잠금 (GATE-17/18)
CREATE TABLE section_locks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    section_id      TEXT NOT NULL,
    locked_by       UUID REFERENCES users(id),
    locked_at       TIMESTAMPTZ DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,      -- locked_at + 5분 (자동 해제)
    UNIQUE(proposal_id, section_id)
);

-- 회사 템플릿 관리 (ART-07~10)
CREATE TABLE company_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,             -- docx | pptx
    name            TEXT NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,             -- Supabase Storage 경로
    version         INTEGER DEFAULT 1,
    is_active       BOOLEAN DEFAULT true,
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 발표 Q&A 기록 (PSM-07/08)
CREATE TABLE presentation_qa (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    evaluator_reaction TEXT,                   -- positive | neutral | negative
    memo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 사용자 라이프사이클 확장 (ULM)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';  -- active | inactive | suspended
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ;

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
```

### 15-5h. ★ v3.3: 노임단가 테이블

```sql
-- 노임단가 참조 테이블 (plan_price 노드에서 조회)
-- ProposalForge 비교 검토 반영: 프롬프트의 "[단가]" 플레이스홀더를 실제 DB 조회로 대체
CREATE TABLE labor_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_org VARCHAR(100) NOT NULL,  -- 'KOSA'(SW산업협회), 'KEA'(엔지니어링협회), 'MOEF'(기재부)
    year INTEGER NOT NULL,
    grade VARCHAR(50) NOT NULL,          -- '기술사', '특급', '고급', '중급', '초급'
    monthly_rate BIGINT NOT NULL,
    daily_rate BIGINT,
    effective_date DATE,
    source_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_labor_rates_lookup ON labor_rates(standard_org, year, grade);

-- RLS: 같은 조직 내 조회 (노임단가는 공개 데이터이지만 조직별 관리)
ALTER TABLE labor_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "all_users_read_labor_rates" ON labor_rates FOR SELECT USING (true);
CREATE POLICY "admin_manage_labor_rates" ON labor_rates FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-5i. ★ v3.3: 시장 낙찰가 벤치마크 테이블

```sql
-- 시장 낙찰가 벤치마크 (plan_price 노드에서 유사 도메인·규모 필터링 조회)
-- ProposalForge 비교 검토 반영: 입찰가격 시뮬레이션의 "유사과업 낙찰가 분석" 데이터 소스
CREATE TABLE market_price_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),  -- 수집한 조직 (NULL이면 공용)
    project_title VARCHAR(500),
    client_org VARCHAR(200),
    domain VARCHAR(100) NOT NULL,        -- 'SI/SW개발', '정책연구', '성과분석', '컨설팅' 등
    budget BIGINT,                       -- 예정가격
    winning_price BIGINT,                -- 낙찰가
    bid_ratio DECIMAL(5,4),              -- 낙찰률 (winning_price/budget)
    num_bidders INTEGER,
    tech_price_ratio VARCHAR(20),        -- '90:10', '80:20' 등
    evaluation_method VARCHAR(100),      -- '협상에 의한 계약', '적격심사', '2단계 경쟁입찰' 등
    year INTEGER NOT NULL,
    source VARCHAR(200),                 -- 데이터 출처 (나라장터, 조달청 등)
    collected_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_market_price_domain_year ON market_price_data(domain, year);
CREATE INDEX idx_market_price_budget ON market_price_data(budget);

ALTER TABLE market_price_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "all_users_read_market_price" ON market_price_data FOR SELECT USING (true);
CREATE POLICY "admin_manage_market_price" ON market_price_data FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-6. RLS (Row Level Security) 정책

```sql
-- ★ Supabase RLS 활성화
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- ── 프로젝트 접근 정책 ──

-- 팀원: 본인 참여 프로젝트만
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
```

### 15-7. 성과 추적 뷰 (Materialized View)

```sql
-- ★ 팀별 성과 집계 뷰
CREATE MATERIALIZED VIEW team_performance AS
SELECT
    p.team_id,
    t.name AS team_name,
    d.name AS division_name,
    COUNT(*) FILTER (WHERE p.status IN ('active', 'completed', 'won', 'lost')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'active') AS active_proposals,
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

-- 갱신: REFRESH MATERIALIZED VIEW team_performance;
-- (제안 결과 등록 시 트리거 또는 cron으로 갱신)
```

---
