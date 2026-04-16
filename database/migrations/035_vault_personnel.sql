-- Vault Personnel HR Sync — 인사 데이터 관리
-- Syncs personnel data from Supabase auth.users + organizational HR records
-- Tracks expertise, availability, project participation, and performance

CREATE TABLE vault_personnel (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- HR Identity
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID UNIQUE NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Basic Info
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  department TEXT,  -- 부서명 (영업, 기술, 컨설팅 등)
  role TEXT NOT NULL,  -- 직급 (사원, 주임, 과장, 부장, 이사 등)
  position TEXT,  -- 직책 (PM, 기술이사, 영업이사 등)

  -- Expertise & Skills (JSONB)
  -- Structure: [{ skill: "제안서 작성", proficiency: "expert", years: 8 }, ...]
  skills JSONB DEFAULT '[]'::jsonb,

  -- Availability & Status
  is_active BOOLEAN NOT NULL DEFAULT true,
  employment_status TEXT NOT NULL DEFAULT 'employed',  -- employed, leave, retired
  available_from TIMESTAMPTZ,
  available_until TIMESTAMPTZ,
  max_concurrent_projects INT DEFAULT 3,
  current_project_count INT NOT NULL DEFAULT 0,  -- Auto-updated by trigger

  -- Performance Metrics (Auto-updated by triggers)
  total_proposals INT NOT NULL DEFAULT 0,  -- 참여한 제안 수
  won_proposals INT NOT NULL DEFAULT 0,  -- 낙찰된 제안 수
  win_rate NUMERIC(5,2) GENERATED ALWAYS AS (
    CASE
      WHEN total_proposals = 0 THEN 0
      ELSE ROUND(won_proposals * 100.0 / total_proposals, 2)
    END
  ) STORED,

  -- Experience Summary
  years_in_company INT,
  years_in_role INT,
  primary_expertise TEXT,  -- 주력 기술 영역

  -- HR Management
  manager_id UUID REFERENCES vault_personnel(id) ON DELETE SET NULL,
  hr_notes TEXT,  -- 인사 관리 메모 (평가, 특이사항 등)

  -- Metadata
  last_synced_at TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'::jsonb,  -- HR 시스템 연동 메타 (직원ID, 조직코드 등)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT valid_employment_status CHECK (employment_status IN ('employed', 'leave', 'retired', 'terminated')),
  CONSTRAINT valid_availability CHECK (available_from IS NULL OR available_until IS NULL OR available_from <= available_until)
);

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX idx_vault_personnel_org ON vault_personnel(org_id);
CREATE INDEX idx_vault_personnel_user ON vault_personnel(user_id);
CREATE INDEX idx_vault_personnel_email ON vault_personnel(email);
CREATE INDEX idx_vault_personnel_is_active ON vault_personnel(is_active, org_id);
CREATE INDEX idx_vault_personnel_manager ON vault_personnel(manager_id);
CREATE INDEX idx_vault_personnel_skills ON vault_personnel USING GIN (skills);

-- ============================================
-- Views for Analytics
-- ============================================

-- Personnel ranked by win rate and proposal count (top contributors)
CREATE VIEW vault_personnel_top_contributors AS
SELECT
  id,
  name,
  email,
  org_id,
  role,
  primary_expertise,
  total_proposals,
  won_proposals,
  win_rate,
  years_in_company,
  current_project_count,
  skills
FROM vault_personnel
WHERE is_active = true AND employment_status = 'employed' AND total_proposals > 0
ORDER BY win_rate DESC, total_proposals DESC;

-- Department-level personnel statistics
CREATE VIEW vault_personnel_by_department AS
SELECT
  department,
  COUNT(*) as total_count,
  COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
  ROUND(AVG(win_rate), 2) as avg_win_rate,
  ROUND(AVG(years_in_company), 1) as avg_tenure,
  STRING_AGG(DISTINCT primary_expertise, ', ') as key_skills,
  ARRAY_AGG(id) as personnel_ids
FROM vault_personnel
WHERE deleted_at IS NULL
GROUP BY department;

-- Expertise distribution across organization
CREATE VIEW vault_personnel_expertise_inventory AS
SELECT
  org_id,
  jsonb_agg(DISTINCT skills) as all_skills,
  COUNT(DISTINCT CASE WHEN skills @> '[{"proficiency":"expert"}]'::jsonb THEN id END) as expert_count,
  COUNT(DISTINCT CASE WHEN skills @> '[{"proficiency":"advanced"}]'::jsonb THEN id END) as advanced_count
FROM vault_personnel
WHERE is_active = true AND employment_status = 'employed'
GROUP BY org_id;

-- Personnel utilization and capacity
CREATE VIEW vault_personnel_utilization AS
SELECT
  id,
  name,
  email,
  max_concurrent_projects,
  current_project_count,
  ROUND(current_project_count * 100.0 / NULLIF(max_concurrent_projects, 0), 1) as utilization_percent,
  CASE
    WHEN current_project_count >= max_concurrent_projects THEN 'at-capacity'
    WHEN current_project_count >= max_concurrent_projects * 0.8 THEN 'high-utilization'
    WHEN current_project_count > 0 THEN 'available'
    ELSE 'free'
  END as capacity_status
FROM vault_personnel
WHERE is_active = true AND employment_status = 'employed';

-- ============================================
-- Triggers for Auto-Update
-- ============================================

-- Trigger 1: Update personnel proposal counts when proposal completes
CREATE OR REPLACE FUNCTION update_personnel_proposal_stats()
RETURNS TRIGGER AS $$
BEGIN
  -- Update win/loss counts for all participants
  UPDATE vault_personnel vp
  SET
    total_proposals = (
      SELECT COUNT(DISTINCT pp.proposal_id)
      FROM proposal_participants pp
      WHERE pp.user_id = vp.user_id AND pp.deleted_at IS NULL
    ),
    won_proposals = (
      SELECT COUNT(DISTINCT pp.proposal_id)
      FROM proposal_participants pp
      JOIN proposals p ON pp.proposal_id = p.id
      WHERE pp.user_id = vp.user_id
        AND pp.deleted_at IS NULL
        AND p.status = 'won'
        AND p.deleted_at IS NULL
    ),
    updated_at = now()
  WHERE org_id = NEW.org_id AND deleted_at IS NULL;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_personnel_stats_on_proposal_change
AFTER INSERT OR UPDATE ON proposals
FOR EACH ROW
EXECUTE FUNCTION update_personnel_proposal_stats();

-- Trigger 2: Update project count when user is added to proposal
CREATE OR REPLACE FUNCTION update_personnel_project_count()
RETURNS TRIGGER AS $$
BEGIN
  -- Count active projects for user
  UPDATE vault_personnel vp
  SET
    current_project_count = (
      SELECT COUNT(DISTINCT p.id)
      FROM proposals p
      JOIN proposal_participants pp ON p.id = pp.proposal_id
      WHERE pp.user_id = vp.user_id
        AND p.status IN ('in_progress', 'review', 'approval')
        AND pp.deleted_at IS NULL
        AND p.deleted_at IS NULL
    ),
    updated_at = now()
  WHERE user_id = NEW.user_id AND deleted_at IS NULL;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_personnel_project_count
AFTER INSERT OR UPDATE OR DELETE ON proposal_participants
FOR EACH ROW
EXECUTE FUNCTION update_personnel_project_count();

-- Trigger 3: Auto-deactivate if employment ends
CREATE OR REPLACE FUNCTION auto_deactivate_ended_employment()
RETURNS TRIGGER AS $$
BEGIN
  -- Auto-deactivate if employment_status changes to terminated/retired
  IF NEW.employment_status IN ('terminated', 'retired') THEN
    NEW.is_active := false;
  END IF;

  -- Check availability dates
  IF NEW.available_until IS NOT NULL AND NEW.available_until <= now() THEN
    NEW.is_active := false;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_deactivate_employment
BEFORE UPDATE ON vault_personnel
FOR EACH ROW
EXECUTE FUNCTION auto_deactivate_ended_employment();

-- Trigger 4: Soft delete support
ALTER TABLE vault_personnel ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;

CREATE INDEX idx_vault_personnel_deleted ON vault_personnel(deleted_at);

-- ============================================
-- RLS Policies
-- ============================================

ALTER TABLE vault_personnel ENABLE ROW LEVEL SECURITY;

CREATE POLICY vault_personnel_select_own_org ON vault_personnel
FOR SELECT
USING (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
);

CREATE POLICY vault_personnel_insert_own_org ON vault_personnel
FOR INSERT
WITH CHECK (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
  AND (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'hr_manager')
);

CREATE POLICY vault_personnel_update_own_org ON vault_personnel
FOR UPDATE
USING (
  org_id IN (
    SELECT org_id FROM users WHERE id = auth.uid()
  )
  AND (SELECT role FROM users WHERE id = auth.uid()) IN ('admin', 'hr_manager')
);

-- ============================================
-- Seed Initial HR Data
-- ============================================

-- Insert sample personnel (commented out — run manually after data setup)
-- INSERT INTO vault_personnel (org_id, user_id, name, email, role, primary_expertise, years_in_company)
-- SELECT
--   u.org_id,
--   u.id,
--   u.name,
--   u.email,
--   'employee',
--   'General Consulting',
--   1
-- FROM users u
-- WHERE u.deleted_at IS NULL
-- ON CONFLICT(user_id) DO NOTHING;
