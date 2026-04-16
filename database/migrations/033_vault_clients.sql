-- Vault AI Chat Phase 2 Week 2 — Clients (발주처) Management with Auto-Update Triggers
-- Stores client/issuing agency information with performance tracking
-- Design Ref: §Phase 2 Week 2-2 — vault_clients table with auto-sync triggers

BEGIN;

-- Create vault_clients table
CREATE TABLE IF NOT EXISTS vault_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Client identification
    agency_name TEXT NOT NULL,  -- 발주처명 (e.g., "서울시청", "국방부")
    agency_id TEXT,  -- External ID from G2B or other system
    agency_code TEXT,  -- Government agency code if applicable

    -- Auto-updated Performance Metrics (updated by triggers)
    win_count INTEGER DEFAULT 0,  -- Number of won proposals
    loss_count INTEGER DEFAULT 0,  -- Number of lost proposals
    total_bid_count INTEGER DEFAULT 0,  -- Total proposals submitted
    win_rate DECIMAL(5,2) DEFAULT 0,  -- Percentage: win_count / total_bid_count * 100
    avg_bid_amount DECIMAL(15,0),  -- Average bid amount across all projects

    -- Auto-tracked dates
    first_bid_date DATE,  -- Date of first proposal
    last_bid_date DATE,  -- Date of most recent proposal
    last_win_date DATE,  -- Date of most recent win

    -- Manual Fields (user-maintained)
    contact_person TEXT,  -- 담당자명
    contact_email TEXT,  -- 담당자 이메일
    contact_phone TEXT,  -- 담당자 전화

    -- Relationship and history
    relationship_notes TEXT,  -- 발주처와의 관계 노트 (자유 텍스트)
    preferences JSONB DEFAULT '{}'::jsonb,  -- {
                                             --   "preferred_team": "...",
                                             --   "submission_requirements": [],
                                             --   "preferred_formats": [],
                                             --   "special_notes": "..."
                                             -- }
    lessons_learned TEXT,  -- 과거 제안에서 배운 교훈 (자유 텍스트)

    -- Agency classification
    agency_type TEXT,  -- 중앙부처, 지자체, 공기업, 민간기업, 기타
    industry TEXT,  -- 산업분류 (건설, IT, 방위사업, 등)
    region TEXT,  -- 지역 (서울, 경기, 부산, 등)

    -- Metadata and audit
    metadata JSONB DEFAULT '{}'::jsonb,  -- Additional flexible fields
    last_review_date TIMESTAMPTZ,  -- When relationship was last reviewed
    review_notes TEXT,  -- Latest review comments

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vault_clients_agency_name
    ON vault_clients (agency_name) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_clients_agency_id
    ON vault_clients (agency_id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_clients_win_rate
    ON vault_clients (win_rate DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_clients_last_bid_date
    ON vault_clients (last_bid_date DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_clients_agency_type
    ON vault_clients (agency_type) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_clients_region
    ON vault_clients (region) WHERE deleted_at IS NULL;

-- GIN index for JSONB search
CREATE INDEX IF NOT EXISTS idx_vault_clients_metadata
    ON vault_clients USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_vault_clients_preferences
    ON vault_clients USING GIN (preferences);

-- Enable RLS
ALTER TABLE vault_clients ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Organization members can see clients their org has bid to
CREATE POLICY IF NOT EXISTS "Org members see their organization's clients"
    ON vault_clients
    FOR SELECT
    USING (
        id IN (
            SELECT DISTINCT vc.id FROM vault_clients vc
            INNER JOIN proposals p ON p.budget IS NOT NULL
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
        OR created_by = auth.uid()
    );

-- RLS Policy: Team leads can insert/update client info
CREATE POLICY IF NOT EXISTS "Team leads manage client information"
    ON vault_clients
    FOR INSERT
    WITH CHECK (
        auth.uid() IN (
            SELECT id FROM users
            WHERE role IN ('lead', 'director', 'executive', 'admin')
            AND org_id = (SELECT org_id FROM users WHERE id = auth.uid())
        )
    );

CREATE POLICY IF NOT EXISTS "Team leads can update client information"
    ON vault_clients
    FOR UPDATE
    USING (
        auth.uid() IN (
            SELECT id FROM users
            WHERE role IN ('lead', 'director', 'executive', 'admin')
            AND org_id = (SELECT org_id FROM users WHERE id = auth.uid())
        )
    );

-- Add created_by column for audit
ALTER TABLE vault_clients ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- Update timestamp trigger
CREATE TRIGGER update_vault_clients_updated_at
    BEFORE UPDATE ON vault_clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Auto-Update Triggers
-- ============================================

-- Trigger: Update client win/loss/bid counts when proposal is completed
CREATE OR REPLACE FUNCTION update_client_statistics()
RETURNS TRIGGER AS $$
DECLARE
    v_client_id UUID;
    v_client_agency_name TEXT;
BEGIN
    -- Only process completed proposals
    IF NEW.status NOT IN ('won', 'lost') THEN
        RETURN NEW;
    END IF;

    -- Find or create client record
    SELECT id, agency_name INTO v_client_id, v_client_agency_name
    FROM vault_clients
    WHERE agency_name ILIKE (
        SELECT COALESCE(new.client_name, '') FROM proposals WHERE id = NEW.id
    )
    LIMIT 1;

    -- If client not found, create one
    IF v_client_id IS NULL THEN
        INSERT INTO vault_clients (agency_name, created_by)
        VALUES (
            COALESCE((SELECT client_name FROM proposals WHERE id = NEW.id), 'Unknown Client'),
            NEW.owner_id
        )
        ON CONFLICT (agency_name) DO NOTHING
        RETURNING id INTO v_client_id;
    END IF;

    -- Update statistics
    UPDATE vault_clients
    SET
        win_count = CASE WHEN NEW.status = 'won' THEN win_count + 1 ELSE win_count END,
        loss_count = CASE WHEN NEW.status = 'lost' THEN loss_count + 1 ELSE loss_count END,
        total_bid_count = total_bid_count + 1,
        last_bid_date = CURRENT_DATE,
        last_win_date = CASE WHEN NEW.status = 'won' THEN CURRENT_DATE ELSE last_win_date END,
        first_bid_date = COALESCE(first_bid_date, CURRENT_DATE),
        updated_at = NOW()
    WHERE id = v_client_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on proposals
DROP TRIGGER IF EXISTS trg_update_client_stats ON proposals;
CREATE TRIGGER trg_update_client_stats
    AFTER UPDATE ON proposals
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_client_statistics();

-- ============================================
-- Auto-Update: Average Bid Amount
-- ============================================

CREATE OR REPLACE FUNCTION update_client_avg_bid_amount()
RETURNS TRIGGER AS $$
DECLARE
    v_client_id UUID;
    v_avg_amount DECIMAL;
BEGIN
    -- Find client for this proposal
    SELECT id INTO v_client_id
    FROM vault_clients
    WHERE agency_name ILIKE (
        SELECT COALESCE(client_name, '') FROM proposals WHERE id = NEW.id
    )
    LIMIT 1;

    IF v_client_id IS NOT NULL AND NEW.budget IS NOT NULL THEN
        -- Calculate average bid amount for this client
        SELECT AVG(budget)::DECIMAL INTO v_avg_amount
        FROM proposals
        WHERE status IN ('won', 'lost')
        AND client_name = (
            SELECT agency_name FROM vault_clients WHERE id = v_client_id
        );

        UPDATE vault_clients
        SET avg_bid_amount = v_avg_amount
        WHERE id = v_client_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_client_avg_bid ON proposals;
CREATE TRIGGER trg_update_client_avg_bid
    AFTER INSERT OR UPDATE ON proposals
    FOR EACH ROW
    WHEN (NEW.budget IS NOT NULL AND NEW.status IN ('won', 'lost'))
    EXECUTE FUNCTION update_client_avg_bid_amount();

-- ============================================
-- Auto-Compute: Win Rate
-- ============================================

CREATE OR REPLACE FUNCTION update_client_win_rate()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE vault_clients
    SET win_rate = CASE
        WHEN total_bid_count > 0
        THEN ROUND((win_count::DECIMAL / total_bid_count * 100)::NUMERIC, 2)
        ELSE 0
    END
    WHERE id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_win_rate ON vault_clients;
CREATE TRIGGER trg_update_win_rate
    AFTER UPDATE ON vault_clients
    FOR EACH ROW
    WHEN (OLD.total_bid_count IS DISTINCT FROM NEW.total_bid_count
        OR OLD.win_count IS DISTINCT FROM NEW.win_count)
    EXECUTE FUNCTION update_client_win_rate();

-- ============================================
-- View: Client Performance Summary
-- ============================================

CREATE OR REPLACE VIEW vault_clients_performance AS
SELECT
    vc.id,
    vc.agency_name,
    vc.agency_type,
    vc.region,
    vc.win_count,
    vc.loss_count,
    vc.total_bid_count,
    vc.win_rate,
    vc.avg_bid_amount,
    vc.last_bid_date,
    vc.last_win_date,
    CASE
        WHEN vc.total_bid_count = 0 THEN 'no_history'
        WHEN vc.win_rate >= 80 THEN 'excellent'
        WHEN vc.win_rate >= 60 THEN 'good'
        WHEN vc.win_rate >= 40 THEN 'fair'
        WHEN vc.win_rate >= 20 THEN 'poor'
        ELSE 'very_poor'
    END AS performance_tier
FROM vault_clients vc
WHERE vc.deleted_at IS NULL
ORDER BY vc.win_rate DESC, vc.total_bid_count DESC;

-- Add comments
COMMENT ON TABLE vault_clients IS '발주처 (Client/Issuing Agency) information with auto-updated performance metrics';
COMMENT ON COLUMN vault_clients.agency_name IS 'Official name of the issuing agency (발주처명)';
COMMENT ON COLUMN vault_clients.win_count IS 'Number of proposals won with this client (auto-updated)';
COMMENT ON COLUMN vault_clients.loss_count IS 'Number of proposals lost with this client (auto-updated)';
COMMENT ON COLUMN vault_clients.win_rate IS 'Percentage of won proposals (auto-computed)';
COMMENT ON COLUMN vault_clients.avg_bid_amount IS 'Average bid amount across all proposals with this client';
COMMENT ON COLUMN vault_clients.relationship_notes IS 'Free-text notes about relationship and historical interactions';
COMMENT ON COLUMN vault_clients.lessons_learned IS 'Key lessons from past proposals with this client';
COMMENT ON COLUMN vault_clients.preferences IS 'Client-specific preferences and requirements in JSONB format';
COMMENT ON VIEW vault_clients_performance IS 'Aggregated client performance metrics with performance tier classification';

COMMIT;
