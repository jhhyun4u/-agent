-- Vault AI Chat Phase 2 Week 3 — Bidding Analysis (입찰 분석)
-- Stores bidding data and analysis results from G2B and historical proposals
-- Design Ref: §Phase 2 Week 2-3 — vault_bidding_analysis table

BEGIN;

-- Create vault_bidding_analysis table
CREATE TABLE IF NOT EXISTS vault_bidding_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to proposal
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- Project classification for analysis
    industry TEXT NOT NULL,  -- 건설, IT, 방위사업, 용역, 기타
    budget DECIMAL(15,0) NOT NULL,  -- 예정가 (estimated project budget)
    budget_range TEXT,  -- Auto-computed range: <100M, 100M-500M, 500M-1B, 1B+

    -- Historical similar projects (last 10 completed projects in same industry/budget range)
    similar_projects JSONB DEFAULT '[]'::jsonb,  -- [
                                                   --   {
                                                   --     "project_id": "uuid",
                                                   --     "title": "...",
                                                   --     "budget": 500000000,
                                                   --     "winning_bid": 450000000,
                                                   --     "bid_ratio": 0.90,
                                                   --     "bidders_count": 5,
                                                   --     "completion_date": "2026-01-15"
                                                   --   }
                                                   -- ]

    -- G2B Data (if fetched)
    g2b_entry_id TEXT,  -- G2B public entry ID
    g2b_data JSONB DEFAULT NULL,  -- {
                                   --   "estimated_amount": 500000000,
                                   --   "agency": "...",
                                   --   "category": "...",
                                   --   "bidders": [{name, bid_amount}],
                                   --   "winning_bid": 450000000,
                                   --   "winner": "...",
                                   --   "published_date": "2026-01-01"
                                   -- }

    -- AI Analysis Results
    analysis_result JSONB DEFAULT NULL,  -- {
                                          --   "avg_bid_ratio": 0.88,
                                          --   "avg_bid_amount": 440000000,
                                          --   "recommended_bid": 420000000,
                                          --   "confidence_score": 0.85,
                                          --   "reasoning": "...",
                                          --   "pricing_strategy": "aggressive|moderate|conservative",
                                          --   "risk_level": "low|medium|high",
                                          --   "comparable_projects": 8,
                                          --   "market_competitiveness": "intense|moderate|weak",
                                          --   "recommendation": "..."
                                          -- }

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,  -- {
                                          --   "data_sources": ["similar_projects", "g2b", "historical"],
                                          --   "analysis_timestamp": "2026-04-16T10:00:00Z",
                                          --   "model_version": "v1.0",
                                          --   "notes": "..."
                                          -- }

    -- Audit and timestamps
    analyzed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- User or AI who performed analysis
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vault_bidding_proposal
    ON vault_bidding_analysis (proposal_id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_bidding_industry
    ON vault_bidding_analysis (industry) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_bidding_budget_range
    ON vault_bidding_analysis (budget_range) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_bidding_analyzed_at
    ON vault_bidding_analysis (analyzed_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_bidding_g2b_entry
    ON vault_bidding_analysis (g2b_entry_id) WHERE g2b_entry_id IS NOT NULL;

-- GIN index for JSONB search
CREATE INDEX IF NOT EXISTS idx_vault_bidding_analysis_result
    ON vault_bidding_analysis USING GIN (analysis_result);

CREATE INDEX IF NOT EXISTS idx_vault_bidding_g2b_data
    ON vault_bidding_analysis USING GIN (g2b_data);

-- Enable RLS
ALTER TABLE vault_bidding_analysis ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can see bidding analysis for their team's proposals
CREATE POLICY IF NOT EXISTS "Users see bidding analysis for their team projects"
    ON vault_bidding_analysis
    FOR SELECT
    USING (
        proposal_id IN (
            SELECT p.id FROM proposals p
            WHERE p.team_id IN (
                SELECT t.id FROM teams t
                WHERE t.division_id IN (
                    SELECT d.id FROM divisions d
                    WHERE d.org_id = (
                        SELECT org_id FROM users WHERE id = auth.uid()
                    )
                )
            )
        )
    );

-- RLS Policy: Users can insert bidding analysis for their team's proposals
CREATE POLICY IF NOT EXISTS "Users can create bidding analysis for their team projects"
    ON vault_bidding_analysis
    FOR INSERT
    WITH CHECK (
        proposal_id IN (
            SELECT p.id FROM proposals p
            WHERE p.team_id IN (
                SELECT t.id FROM teams t
                WHERE t.division_id IN (
                    SELECT d.id FROM divisions d
                    WHERE d.org_id = (
                        SELECT org_id FROM users WHERE id = auth.uid()
                    )
                )
            )
        )
    );

-- RLS Policy: Users can update their own analysis
CREATE POLICY IF NOT EXISTS "Users can update their analysis"
    ON vault_bidding_analysis
    FOR UPDATE
    USING (analyzed_by = auth.uid() OR analyzed_by IS NULL)
    WITH CHECK (analyzed_by = auth.uid() OR analyzed_by IS NULL);

-- Update timestamp trigger
CREATE TRIGGER update_vault_bidding_updated_at
    BEFORE UPDATE ON vault_bidding_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Views for Aggregated Analysis
-- ============================================

-- View: Bidding statistics by industry
CREATE OR REPLACE VIEW vault_bidding_by_industry AS
SELECT
    industry,
    COUNT(*) as total_projects,
    AVG(CAST(budget AS NUMERIC)) as avg_budget,
    MIN(budget) as min_budget,
    MAX(budget) as max_budget,
    ROUND(AVG((analysis_result->>'avg_bid_ratio')::NUMERIC), 4) as avg_bid_ratio,
    ROUND(AVG((analysis_result->>'recommended_bid')::NUMERIC), 0) as avg_recommended_bid,
    ROUND(AVG((analysis_result->>'confidence_score')::NUMERIC), 2) as avg_confidence,
    COUNT(CASE WHEN (analysis_result->>'risk_level')::TEXT = 'high' THEN 1 END) as high_risk_count,
    COUNT(CASE WHEN (analysis_result->>'risk_level')::TEXT = 'medium' THEN 1 END) as medium_risk_count,
    COUNT(CASE WHEN (analysis_result->>'risk_level')::TEXT = 'low' THEN 1 END) as low_risk_count
FROM vault_bidding_analysis
WHERE deleted_at IS NULL AND analysis_result IS NOT NULL
GROUP BY industry
ORDER BY total_projects DESC;

-- View: Bidding statistics by budget range
CREATE OR REPLACE VIEW vault_bidding_by_budget_range AS
SELECT
    budget_range,
    COUNT(*) as total_projects,
    AVG(CAST(budget AS NUMERIC)) as avg_budget,
    ROUND(AVG((analysis_result->>'avg_bid_ratio')::NUMERIC), 4) as avg_bid_ratio,
    ROUND(AVG((analysis_result->>'recommended_bid')::NUMERIC), 0) as avg_recommended_bid,
    ROUND(AVG((analysis_result->>'confidence_score')::NUMERIC), 2) as avg_confidence,
    ROUND(AVG((analysis_result->>'recommended_bid')::NUMERIC) / AVG(CAST(budget AS NUMERIC)), 4) as ratio_to_budget
FROM vault_bidding_analysis
WHERE deleted_at IS NULL AND analysis_result IS NOT NULL
GROUP BY budget_range
ORDER BY
    CASE budget_range
        WHEN '<100M' THEN 1
        WHEN '100M-500M' THEN 2
        WHEN '500M-1B' THEN 3
        WHEN '1B+' THEN 4
        ELSE 5
    END;

-- View: High-risk bidding opportunities (market competitiveness analysis)
CREATE OR REPLACE VIEW vault_bidding_high_risk_opportunities AS
SELECT
    vba.id,
    vba.proposal_id,
    vba.industry,
    vba.budget,
    vba.budget_range,
    (vba.analysis_result->>'risk_level') as risk_level,
    (vba.analysis_result->>'market_competitiveness') as competitiveness,
    (vba.analysis_result->>'confidence_score')::NUMERIC as confidence,
    (vba.analysis_result->>'recommended_bid')::NUMERIC as recommended_bid,
    (vba.analysis_result->>'reasoning') as reasoning,
    p.title as proposal_title,
    p.created_at
FROM vault_bidding_analysis vba
INNER JOIN proposals p ON vba.proposal_id = p.id
WHERE vba.deleted_at IS NULL
    AND vba.analysis_result IS NOT NULL
    AND (vba.analysis_result->>'risk_level')::TEXT IN ('high', 'medium')
    AND (vba.analysis_result->>'confidence_score')::NUMERIC >= 0.7
ORDER BY vba.analyzed_at DESC;

-- View: Comparison with similar projects
CREATE OR REPLACE VIEW vault_bidding_project_comparison AS
SELECT
    vba.id as analysis_id,
    vba.proposal_id,
    vba.industry,
    vba.budget as current_budget,
    (vba.analysis_result->>'recommended_bid')::NUMERIC as recommended_bid,
    (vba.analysis_result->>'avg_bid_ratio')::NUMERIC as historical_avg_ratio,
    jsonb_array_length(vba.similar_projects) as similar_projects_count,
    CASE
        WHEN jsonb_array_length(vba.similar_projects) >= 8 THEN 'high'
        WHEN jsonb_array_length(vba.similar_projects) >= 5 THEN 'medium'
        ELSE 'low'
    END as data_quality,
    (vba.analysis_result->>'confidence_score')::NUMERIC as confidence_score
FROM vault_bidding_analysis vba
WHERE vba.deleted_at IS NULL
ORDER BY vba.analyzed_at DESC;

-- Add comments
COMMENT ON TABLE vault_bidding_analysis IS '입찰 분석 (Bidding Analysis) with AI recommendations and historical comparisons';
COMMENT ON COLUMN vault_bidding_analysis.industry IS 'Project industry classification: 건설, IT, 방위사업, 용역, 기타';
COMMENT ON COLUMN vault_bidding_analysis.budget IS 'Estimated project budget (예정가)';
COMMENT ON COLUMN vault_bidding_analysis.similar_projects IS 'Last 10 completed projects in same industry/budget range with bid ratios';
COMMENT ON COLUMN vault_bidding_analysis.analysis_result IS 'AI analysis with bid ratio, recommended price, confidence score, and strategy recommendation';
COMMENT ON COLUMN vault_bidding_analysis.g2b_data IS 'Data collected from G2B API including bidders and winning bid';
COMMENT ON VIEW vault_bidding_by_industry IS 'Aggregated bidding statistics grouped by industry with risk analysis';
COMMENT ON VIEW vault_bidding_by_budget_range IS 'Bidding statistics grouped by budget range for market segmentation analysis';
COMMENT ON VIEW vault_bidding_high_risk_opportunities IS 'High-risk bidding opportunities requiring special attention';
COMMENT ON VIEW vault_bidding_project_comparison IS 'Comparison of current project with similar historical projects';

COMMIT;
