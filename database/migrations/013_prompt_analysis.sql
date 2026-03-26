-- 013: 프롬프트 패턴 분석 스냅샷 (prompt-admin v2.0)
-- 학습 사이클 2단계: 주기적 패턴 분석 결과 저장

CREATE TABLE IF NOT EXISTS prompt_analysis_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    -- 수치 메트릭
    proposals_used  INTEGER DEFAULT 0,
    win_count       INTEGER DEFAULT 0,
    loss_count      INTEGER DEFAULT 0,
    win_rate        DECIMAL(5,2),
    avg_quality     DECIMAL(5,2),
    avg_edit_ratio  DECIMAL(5,4),
    edit_count      INTEGER DEFAULT 0,
    -- 패턴 분석 (AI 생성)
    edit_patterns   JSONB DEFAULT '[]',
    feedback_summary JSONB DEFAULT '{}',
    win_loss_diff   JSONB DEFAULT '{}',
    hypothesis      TEXT,
    priority        VARCHAR(10) DEFAULT 'low',
    -- 메타
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pas_prompt ON prompt_analysis_snapshots(prompt_id, period_end DESC);
CREATE INDEX IF NOT EXISTS idx_pas_priority ON prompt_analysis_snapshots(priority, period_end DESC);
