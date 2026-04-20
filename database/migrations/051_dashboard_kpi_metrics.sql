-- ============================================
-- Migration: Dashboard KPI Materialized Views
-- Version: 1.0
-- Date: 2026-04-20
-- Description: 팀/본부/경영진 KPI 대시보드용 3개 뷰 생성
-- ============================================

-- ============================================
-- 1. mv_dashboard_individual: 개인 대시보드
-- ============================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_individual AS
SELECT
    p.id AS proposal_id,
    p.owner_id,
    p.team_id,
    p.status,
    -- 진행률 (0-100%)
    ROUND(
        CASE
            WHEN p.status IN ('won', 'lost', 'cancelled', 'completed') THEN 100
            WHEN p.status IN ('submitted', 'presented') THEN 80
            WHEN p.status IN ('strategizing') THEN 60
            WHEN p.status IN ('analyzing') THEN 40
            WHEN p.status IN ('searching', 'initialized') THEN 20
            ELSE 0
        END::numeric, 1
    ) AS progress_pct,
    -- 경과 일수
    EXTRACT(DAY FROM (NOW() - p.created_at))::integer AS days_elapsed,
    p.created_at,
    p.updated_at,
    pr.result AS result_type,
    pr.final_price
FROM proposals p
LEFT JOIN proposal_results pr ON pr.proposal_id = p.id
WHERE p.owner_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_individual_owner
    ON mv_dashboard_individual(owner_id);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_individual_status
    ON mv_dashboard_individual(status);

-- ============================================
-- 2. mv_dashboard_team: 팀 대시보드
-- ============================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_team AS
SELECT
    t.id AS team_id,
    t.name AS team_name,
    t.division_id,
    d.name AS division_name,
    d.org_id,
    -- 기본 메트릭
    COUNT(*) FILTER (WHERE p.status IN ('won', 'lost', 'cancelled')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won_count,
    COUNT(*) FILTER (WHERE p.status = 'lost') AS lost_count,
    -- 수주율 (YTD)
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won' AND DATE_TRUNC('year', p.created_at) = DATE_TRUNC('year', NOW()))::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won', 'lost') AND DATE_TRUNC('year', p.created_at) = DATE_TRUNC('year', NOW())), 0) * 100, 1
    ) AS win_rate_ytd,
    -- 월별 수주율 (최근 완료 건 기준)
    ROUND(
        COUNT(*) FILTER (
            WHERE p.status = 'won'
              AND DATE_TRUNC('month', p.updated_at) = DATE_TRUNC('month', NOW())
        )::numeric /
        NULLIF(COUNT(*) FILTER (
            WHERE p.status IN ('won', 'lost')
              AND DATE_TRUNC('month', p.updated_at) = DATE_TRUNC('month', NOW())
        ), 0) * 100, 1
    ) AS win_rate_mtd,
    -- 수주 금액
    COALESCE(SUM(pr.final_price) FILTER (WHERE p.status = 'won'), 0) AS total_won_amount,
    -- 평균 건당 수주 금액
    ROUND(
        COALESCE(AVG(pr.final_price) FILTER (WHERE p.status = 'won'), 0)::numeric, 0
    ) AS avg_deal_size,
    -- 기술 점수
    ROUND(AVG(pr.tech_score) FILTER (WHERE pr.tech_score IS NOT NULL)::numeric, 1) AS avg_tech_score,
    -- 진행 중인 제안 건수
    COUNT(*) FILTER (WHERE p.status NOT IN ('won', 'lost', 'cancelled', 'completed')) AS in_progress_count,
    -- 생성 기준 연
    DATE_TRUNC('year', p.created_at)::date AS year
FROM teams t
LEFT JOIN divisions d ON d.id = t.division_id
LEFT JOIN proposals p ON p.team_id = t.id
LEFT JOIN proposal_results pr ON pr.proposal_id = p.id
GROUP BY t.id, t.name, t.division_id, d.name, d.org_id, DATE_TRUNC('year', p.created_at)::date;

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_team_team_id
    ON mv_dashboard_team(team_id);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_team_division
    ON mv_dashboard_team(division_id);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_team_org
    ON mv_dashboard_team(org_id);

-- ============================================
-- 3. mv_dashboard_executive: 경영진 대시보드 (분기/월별)
-- ============================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_executive AS
SELECT
    o.id AS org_id,
    o.name AS org_name,
    -- 기간
    DATE_TRUNC('quarter', p.created_at)::date AS quarter,
    DATE_TRUNC('month', p.created_at)::date AS month,
    -- 기본 메트릭
    COUNT(*) FILTER (WHERE p.status IN ('won', 'lost', 'cancelled')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won_count,
    COUNT(*) FILTER (WHERE p.status = 'lost') AS lost_count,
    -- 전체 수주율
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won', 'lost')), 0) * 100, 1
    ) AS win_rate_pct,
    -- 수주 금액 합계
    COALESCE(SUM(pr.final_price) FILTER (WHERE p.status = 'won'), 0) AS total_won_amount,
    -- 평균 제안 금액
    ROUND(
        COALESCE(AVG(pr.final_price) FILTER (WHERE p.status IN ('won', 'lost')), 0)::numeric, 0
    ) AS avg_proposal_value,
    -- 제안 투입 리소스 시간 (추정)
    COUNT(*) FILTER (WHERE p.status IN ('won', 'lost', 'cancelled')) AS completed_proposals,
    -- 본부별 최고 수주율 팀
    (
        SELECT t.name
        FROM teams t
        JOIN proposals tp ON tp.team_id = t.id
        WHERE t.division_id IN (SELECT id FROM divisions WHERE org_id = o.id)
          AND tp.status = 'won'
          AND DATE_TRUNC('quarter', tp.created_at) = DATE_TRUNC('quarter', p.created_at)
        GROUP BY t.id, t.name
        ORDER BY ROUND(
            COUNT(*) FILTER (WHERE tp.status = 'won')::numeric /
            NULLIF(COUNT(*) FILTER (WHERE tp.status IN ('won', 'lost')), 0) * 100, 1
        ) DESC
        LIMIT 1
    ) AS top_performing_team
FROM organizations o
LEFT JOIN proposals p ON p.org_id = o.id
LEFT JOIN proposal_results pr ON pr.proposal_id = p.id
WHERE p.status IN ('won', 'lost', 'cancelled')
GROUP BY o.id, o.name, DATE_TRUNC('quarter', p.created_at), DATE_TRUNC('month', p.created_at);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_executive_org
    ON mv_dashboard_executive(org_id);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_executive_quarter
    ON mv_dashboard_executive(quarter DESC);

CREATE INDEX IF NOT EXISTS idx_mv_dashboard_executive_month
    ON mv_dashboard_executive(month DESC);

-- ============================================
-- 4. dashboard_metrics_history: 월별 메트릭 이력 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS dashboard_metrics_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 메타데이터
    metric_type TEXT NOT NULL,           -- 'team_performance' | 'positioning_accuracy' | 'competitor_analysis'
    period DATE NOT NULL,                -- YYYY-MM-01 (월별)

    -- 조직 구조
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    division_id UUID REFERENCES divisions(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,

    -- 메트릭 값
    metric_key TEXT NOT NULL,            -- 'win_rate' | 'total_proposals' | 'total_won_amount' | ...
    metric_value DECIMAL(15,2),          -- 수치 값
    metric_string TEXT,                  -- 문자열 값 (예: positioning name)

    -- 메타
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT unique_history UNIQUE(metric_type, period, org_id, division_id, team_id, metric_key)
);

CREATE INDEX IF NOT EXISTS idx_dmh_period
    ON dashboard_metrics_history(period DESC);

CREATE INDEX IF NOT EXISTS idx_dmh_team_period
    ON dashboard_metrics_history(team_id, period DESC);

CREATE INDEX IF NOT EXISTS idx_dmh_division_period
    ON dashboard_metrics_history(division_id, period DESC);

CREATE INDEX IF NOT EXISTS idx_dmh_org_period
    ON dashboard_metrics_history(org_id, period DESC);

CREATE INDEX IF NOT EXISTS idx_dmh_metric_type
    ON dashboard_metrics_history(metric_type, period DESC);

-- RLS
ALTER TABLE dashboard_metrics_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "dashboard_metrics_history_read" ON dashboard_metrics_history
    FOR SELECT USING (
        -- 경영진: 전체 조직 데이터
        (SELECT role FROM users WHERE id = auth.uid()) = 'executive'
        -- 본부장: 자신 본부 데이터
        OR division_id IN (SELECT division_id FROM users WHERE id = auth.uid())
        -- 팀장: 자신 팀 데이터
        OR team_id IN (SELECT team_id FROM users WHERE id = auth.uid())
        -- admin: 전체
        OR (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
    );

-- ============================================
-- 5. MV 갱신 함수
-- ============================================

CREATE OR REPLACE FUNCTION refresh_dashboard_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_individual;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_team;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_executive;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. 월별 이력 자동 기록 함수 (매월 1일 자정)
-- ============================================

CREATE OR REPLACE FUNCTION populate_dashboard_metrics_history()
RETURNS void AS $$
BEGIN
    -- 팀별 성과 기록
    INSERT INTO dashboard_metrics_history (metric_type, period, team_id, division_id, org_id, metric_key, metric_value)
    SELECT
        'team_performance',
        DATE_TRUNC('month', NOW())::date,
        team_id,
        division_id,
        (SELECT org_id FROM divisions WHERE id = division_id),
        'win_rate_ytd',
        win_rate_ytd
    FROM mv_dashboard_team
    ON CONFLICT (metric_type, period, org_id, division_id, team_id, metric_key) DO UPDATE
    SET metric_value = EXCLUDED.metric_value, updated_at = NOW();

    -- 팀별 수주 금액 기록
    INSERT INTO dashboard_metrics_history (metric_type, period, team_id, division_id, org_id, metric_key, metric_value)
    SELECT
        'team_performance',
        DATE_TRUNC('month', NOW())::date,
        team_id,
        division_id,
        (SELECT org_id FROM divisions WHERE id = division_id),
        'total_won_amount',
        total_won_amount
    FROM mv_dashboard_team
    ON CONFLICT (metric_type, period, org_id, division_id, team_id, metric_key) DO UPDATE
    SET metric_value = EXCLUDED.metric_value, updated_at = NOW();

    -- 전사 수주율 기록
    INSERT INTO dashboard_metrics_history (metric_type, period, org_id, metric_key, metric_value)
    SELECT
        'positioning_accuracy',
        DATE_TRUNC('month', NOW())::date,
        org_id,
        'win_rate_pct',
        win_rate_pct
    FROM mv_dashboard_executive
    ON CONFLICT (metric_type, period, org_id, division_id, team_id, metric_key) DO UPDATE
    SET metric_value = EXCLUDED.metric_value, updated_at = NOW();
END;
$$ LANGUAGE plpgsql;
