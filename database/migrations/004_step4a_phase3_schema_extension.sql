-- STEP 4A Phase 3: DB 스키마 확장
-- 3개 테이블 추가: evaluation_feedback, harness_metrics_log, weight_configs

-- 1. evaluation_feedback 테이블
CREATE TABLE IF NOT EXISTS evaluation_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_decision VARCHAR(20) NOT NULL CHECK (user_decision IN ('approved', 'rejected')),
    reason TEXT,
    corrected_hallucination DECIMAL(3,2),
    corrected_persuasiveness DECIMAL(3,2),
    corrected_completeness DECIMAL(3,2),
    corrected_clarity DECIMAL(3,2),
    section_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_evaluation_feedback_user_id ON evaluation_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_feedback_section_type ON evaluation_feedback(section_type);
CREATE INDEX IF NOT EXISTS idx_evaluation_feedback_created_at ON evaluation_feedback(created_at);

-- 2. harness_metrics_log 테이블
CREATE TABLE IF NOT EXISTS harness_metrics_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id VARCHAR(255),
    precision DECIMAL(4,3),
    recall DECIMAL(4,3),
    f1_score DECIMAL(4,3),
    false_negative_count INT,
    false_positive_count INT,
    avg_latency_ms INT,
    confidence_score DECIMAL(4,3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_harness_metrics_log_timestamp ON harness_metrics_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_harness_metrics_log_evaluation_id ON harness_metrics_log(evaluation_id);

-- 3. weight_configs 테이블
CREATE TABLE IF NOT EXISTS weight_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    hallucination_weight DECIMAL(4,3),
    persuasiveness_weight DECIMAL(4,3),
    completeness_weight DECIMAL(4,3),
    clarity_weight DECIMAL(4,3),
    section_type VARCHAR(50),
    f1_score DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_weight_configs_name ON weight_configs(name);
CREATE INDEX IF NOT EXISTS idx_weight_configs_section_type ON weight_configs(section_type);
CREATE INDEX IF NOT EXISTS idx_weight_configs_is_active ON weight_configs(is_active);

-- RLS 정책 (Row Level Security)
ALTER TABLE evaluation_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own feedback"
    ON evaluation_feedback FOR SELECT
    USING (auth.uid() = user_id OR auth.uid() IS NULL);

CREATE POLICY "Users can create feedback"
    ON evaluation_feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 메타데이터 테이블 (마이그레이션 추적)
CREATE TABLE IF NOT EXISTS migration_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_name VARCHAR(255) NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO migration_history (migration_name) VALUES ('004_step4a_phase3_schema_extension');
