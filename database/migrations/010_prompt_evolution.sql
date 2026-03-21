-- 010_prompt_evolution.sql
-- 프롬프트 자가평가 & 지속적 진화 시스템
-- Phase A: 프롬프트 레지스트리 + 산출물 링크
-- Phase B: 성과 집계 뷰
-- Phase C: 사람 수정 추적
-- Phase D: A/B 실험

-- ════════════════════════════════════════════════════════
-- Phase A: 프롬프트 레지스트리
-- ════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS prompt_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    source_file     VARCHAR(200) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,
    content_text    TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    status          VARCHAR(20) DEFAULT 'active',
    parent_version  INTEGER,
    change_reason   TEXT,
    created_by      VARCHAR(50) DEFAULT 'system',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(prompt_id, version)
);

CREATE INDEX IF NOT EXISTS idx_pr_prompt_id ON prompt_registry(prompt_id);
CREATE INDEX IF NOT EXISTS idx_pr_status ON prompt_registry(status);

-- 프롬프트→산출물 링크
CREATE TABLE IF NOT EXISTS prompt_artifact_link (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL,
    artifact_step   TEXT NOT NULL,
    section_id      TEXT,
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER NOT NULL,
    prompt_hash     VARCHAR(64) NOT NULL,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    duration_ms     INTEGER,
    quality_score   DECIMAL(5,2),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pal_proposal ON prompt_artifact_link(proposal_id);
CREATE INDEX IF NOT EXISTS idx_pal_prompt ON prompt_artifact_link(prompt_id, prompt_version);

-- ai_task_logs 확장
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS prompt_id VARCHAR(100);
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS prompt_version INTEGER;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS prompt_hash VARCHAR(64);

-- ════════════════════════════════════════════════════════
-- Phase B: 성과 집계 뷰
-- ════════════════════════════════════════════════════════

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_prompt_effectiveness AS
SELECT
    pal.prompt_id,
    pal.prompt_version,
    COUNT(DISTINCT pal.proposal_id) AS proposals_used,
    COUNT(DISTINCT pal.proposal_id) FILTER (WHERE pr.result = 'won') AS won,
    COUNT(DISTINCT pal.proposal_id) FILTER (WHERE pr.result = 'lost') AS lost,
    ROUND(
        COUNT(DISTINCT pal.proposal_id) FILTER (WHERE pr.result = 'won')::numeric
        / NULLIF(
            COUNT(DISTINCT pal.proposal_id) FILTER (WHERE pr.result = 'won')
            + COUNT(DISTINCT pal.proposal_id) FILTER (WHERE pr.result = 'lost'),
            0
        ) * 100, 1
    ) AS win_rate,
    AVG(pal.quality_score) AS avg_quality_score,
    AVG(pal.input_tokens) AS avg_input_tokens,
    AVG(pal.output_tokens) AS avg_output_tokens,
    AVG(pal.duration_ms) AS avg_duration_ms
FROM prompt_artifact_link pal
LEFT JOIN proposal_results pr ON pr.proposal_id = pal.proposal_id
GROUP BY pal.prompt_id, pal.prompt_version;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pe_prompt ON mv_prompt_effectiveness(prompt_id, prompt_version);

-- ════════════════════════════════════════════════════════
-- Phase C: 사람 수정 추적
-- ════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS human_edit_tracking (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL,
    section_id      TEXT NOT NULL,
    prompt_id       VARCHAR(100),
    prompt_version  INTEGER,
    action          VARCHAR(20) NOT NULL,
    original_length INTEGER,
    edited_length   INTEGER,
    edit_ratio      DECIMAL(5,4),
    user_id         UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_het_proposal ON human_edit_tracking(proposal_id);
CREATE INDEX IF NOT EXISTS idx_het_prompt ON human_edit_tracking(prompt_id, prompt_version);

-- ════════════════════════════════════════════════════════
-- Phase D: A/B 실험
-- ════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS prompt_ab_experiments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name TEXT NOT NULL,
    prompt_id       VARCHAR(100) NOT NULL,
    baseline_version INTEGER NOT NULL,
    candidate_version INTEGER NOT NULL,
    traffic_pct     INTEGER DEFAULT 20,
    status          VARCHAR(20) DEFAULT 'running',
    min_samples     INTEGER DEFAULT 5,
    promote_threshold DECIMAL(5,2) DEFAULT 5.0,
    conclusion      TEXT,
    promoted_version INTEGER,
    started_at      TIMESTAMPTZ DEFAULT now(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pab_status ON prompt_ab_experiments(status);
CREATE INDEX IF NOT EXISTS idx_pab_prompt ON prompt_ab_experiments(prompt_id);
