-- 012_prompt_admin.sql
-- 프롬프트 Admin 기능 — 시뮬레이션 + AI 제안 이력 + 카테고리

-- ═══ 1. prompt_registry 카테고리 확장 ═══
ALTER TABLE prompt_registry ADD COLUMN IF NOT EXISTS category VARCHAR(30);

UPDATE prompt_registry SET category = 'bid_analysis' WHERE prompt_id LIKE 'bid_review.%';
UPDATE prompt_registry SET category = 'strategy' WHERE prompt_id LIKE 'strategy.%';
UPDATE prompt_registry SET category = 'planning' WHERE prompt_id LIKE 'plan.%';
UPDATE prompt_registry SET category = 'proposal_writing'
  WHERE prompt_id LIKE 'section_prompts.%'
     OR prompt_id LIKE 'proposal_prompts.%';
UPDATE prompt_registry SET category = 'presentation'
  WHERE prompt_id LIKE 'ppt_pipeline.%';
UPDATE prompt_registry SET category = 'quality_assurance'
  WHERE prompt_id LIKE 'trustworthiness.%'
     OR prompt_id LIKE 'submission_docs.%';

CREATE INDEX IF NOT EXISTS idx_pr_category ON prompt_registry(category);

-- ═══ 2. 시뮬레이션 이력 ═══
CREATE TABLE IF NOT EXISTS prompt_simulations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER,
    prompt_text     TEXT NOT NULL,
    data_source     VARCHAR(20) NOT NULL CHECK (data_source IN ('sample', 'project', 'custom')),
    data_source_id  VARCHAR(200),
    input_variables JSONB DEFAULT '{}',
    output_text     TEXT,
    output_meta     JSONB DEFAULT '{}',
    quality_score   DECIMAL(5,2),
    quality_detail  JSONB,
    compared_with   INTEGER,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_psim_prompt ON prompt_simulations(prompt_id);
CREATE INDEX IF NOT EXISTS idx_psim_created ON prompt_simulations(created_at DESC);

-- ═══ 3. AI 개선 제안 이력 ═══
CREATE TABLE IF NOT EXISTS prompt_improvement_suggestions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER NOT NULL,
    analysis        TEXT,
    suggestions     JSONB NOT NULL,
    accepted_index  INTEGER,
    feedback        TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pis_prompt ON prompt_improvement_suggestions(prompt_id);

-- ═══ 4. 시뮬레이션 토큰 한도 ═══
CREATE TABLE IF NOT EXISTS simulation_token_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    date            DATE DEFAULT CURRENT_DATE,
    simulations_count INTEGER DEFAULT 0,
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- upsert 함수
CREATE OR REPLACE FUNCTION upsert_simulation_quota(
    p_user_id UUID,
    p_tokens_in INTEGER,
    p_tokens_out INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO simulation_token_usage (user_id, simulations_count, tokens_input, tokens_output)
    VALUES (p_user_id, 1, p_tokens_in, p_tokens_out)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        simulations_count = simulation_token_usage.simulations_count + 1,
        tokens_input = simulation_token_usage.tokens_input + p_tokens_in,
        tokens_output = simulation_token_usage.tokens_output + p_tokens_out;
END;
$$ LANGUAGE plpgsql;
