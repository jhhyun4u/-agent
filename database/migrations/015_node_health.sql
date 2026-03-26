-- 015: 노드별 헬스 메트릭 Materialized View (MON-07)
-- 2026-03-26

-- 노드별 성공률·지연·비용 집계 (최근 7일, 24h/7d 구분)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_node_health AS
SELECT
    step                                                    AS node_name,
    COUNT(*)                                                AS total_runs,
    COUNT(*) FILTER (WHERE status = 'complete')             AS success_count,
    COUNT(*) FILTER (WHERE status = 'error')                AS error_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'complete') / NULLIF(COUNT(*), 0),
        1
    )                                                       AS success_rate_pct,
    ROUND(AVG(duration_ms))                                 AS avg_duration_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms))
                                                            AS p95_duration_ms,
    SUM(COALESCE(cost_usd, 0))                              AS total_cost_usd,
    SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0))
                                                            AS total_tokens,
    CASE
        WHEN created_at >= NOW() - INTERVAL '24 hours' THEN '24h'
        WHEN created_at >= NOW() - INTERVAL '7 days'   THEN '7d'
    END                                                     AS period
FROM ai_task_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY step, period
ORDER BY step, period;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_node_health
    ON mv_node_health (node_name, period);

-- MV concurrent 리프레시용 RPC
CREATE OR REPLACE FUNCTION refresh_materialized_view_concurrently(view_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
