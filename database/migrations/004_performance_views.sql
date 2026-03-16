-- Phase 4: 성과 추적 테이블 + Materialized View
-- proposal_results 테이블 + mv_team_performance + mv_positioning_accuracy

-- ============================================
-- proposal_results: 제안 결과 상세 (scores, ranking, competitor info)
-- ============================================

CREATE TABLE IF NOT EXISTS proposal_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE UNIQUE NOT NULL,
    result          TEXT NOT NULL CHECK (result IN ('won', 'lost', 'void')),
    final_price     BIGINT,
    competitor_count INTEGER,
    ranking         INTEGER,
    tech_score      DECIMAL(5,2),
    price_score     DECIMAL(5,2),
    total_score     DECIMAL(5,2),
    feedback_notes  TEXT,
    won_by          TEXT,
    registered_by   UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_proposal_results_proposal ON proposal_results(proposal_id);
CREATE INDEX idx_proposal_results_result ON proposal_results(result);

CREATE TRIGGER update_proposal_results_updated_at BEFORE UPDATE ON proposal_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS
ALTER TABLE proposal_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON proposal_results FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- mv_team_performance: 부서별 성과 집계
-- ============================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_team_performance AS
SELECT
    t.id AS team_id,
    t.name AS team_name,
    d.name AS division_name,
    COUNT(*) FILTER (WHERE p.status IN ('won', 'lost', 'cancelled')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won_count,
    COUNT(*) FILTER (WHERE p.status = 'lost') AS lost_count,
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won', 'lost')), 0) * 100, 1
    ) AS win_rate,
    COALESCE(SUM(p.result_amount) FILTER (WHERE p.status = 'won'), 0) AS total_won_amount,
    AVG(pr.tech_score) FILTER (WHERE pr.tech_score IS NOT NULL) AS avg_tech_score,
    DATE_TRUNC('quarter', p.created_at) AS quarter
FROM proposals p
LEFT JOIN proposal_results pr ON pr.proposal_id = p.id
JOIN teams t ON t.id = p.team_id
JOIN divisions d ON d.id = t.division_id
WHERE p.status IN ('won', 'lost', 'cancelled')
GROUP BY t.id, t.name, d.name, DATE_TRUNC('quarter', p.created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_team_perf_unique
    ON mv_team_performance(team_id, quarter);

-- ============================================
-- mv_positioning_accuracy: 포지셔닝별 성과 (LRN-08)
-- ============================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_positioning_accuracy AS
SELECT
    p.positioning,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won,
    COUNT(*) FILTER (WHERE p.status = 'lost') AS lost,
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won', 'lost')), 0) * 100, 1
    ) AS win_rate
FROM proposals p
WHERE p.positioning IS NOT NULL
  AND p.status IN ('won', 'lost', 'cancelled')
GROUP BY p.positioning;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pos_unique
    ON mv_positioning_accuracy(positioning);

-- ============================================
-- MV 갱신 함수
-- ============================================

CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_team_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_positioning_accuracy;
END;
$$ LANGUAGE plpgsql;

-- 레거시 호환: refresh_team_performance → refresh_performance_views 래핑
CREATE OR REPLACE FUNCTION refresh_team_performance()
RETURNS void AS $$
BEGIN
    PERFORM refresh_performance_views();
END;
$$ LANGUAGE plpgsql;
