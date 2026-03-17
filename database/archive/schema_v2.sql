-- ============================================================
-- Tenopa Proposer Platform v2 -- Additional Schema
-- ============================================================

-- 섹션 라이브러리
CREATE TABLE IF NOT EXISTS sections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id     UUID REFERENCES teams(id) ON DELETE CASCADE,
    owner_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN (
                    'company_intro','track_record','methodology',
                    'organization','schedule','cost','other'
                )),
    content     TEXT NOT NULL,
    tags        TEXT[] DEFAULT '{}',
    is_public   BOOLEAN NOT NULL DEFAULT false,
    use_count   INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sections_category_idx ON sections(category);
CREATE INDEX IF NOT EXISTS sections_team_idx ON sections(team_id);
CREATE INDEX IF NOT EXISTS sections_owner_idx ON sections(owner_id);

-- 회사 자료
CREATE TABLE IF NOT EXISTS company_assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id         UUID REFERENCES teams(id) ON DELETE CASCADE,
    owner_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'done'
                            CHECK (status IN ('pending','processing','done','failed')),
    extracted_sections  UUID[] DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE company_assets ADD COLUMN IF NOT EXISTS extracted_sections UUID[] DEFAULT '{}';

-- proposals v2 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS section_ids UUID[] DEFAULT '{}';
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES proposals(id) ON DELETE SET NULL;

-- RLS
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS sections_select ON sections FOR SELECT
    USING (
        is_public = true
        OR owner_id = auth.uid()
        OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    );
CREATE POLICY IF NOT EXISTS sections_insert ON sections FOR INSERT
    WITH CHECK (owner_id = auth.uid());
CREATE POLICY IF NOT EXISTS sections_update ON sections FOR UPDATE
    USING (owner_id = auth.uid() OR team_id IN (
        SELECT team_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin'
    ));
CREATE POLICY IF NOT EXISTS sections_delete ON sections FOR DELETE
    USING (owner_id = auth.uid());

ALTER TABLE company_assets ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS assets_access ON company_assets
    USING (
        owner_id = auth.uid()
        OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    );

-- updated_at trigger for sections
CREATE TRIGGER IF NOT EXISTS trg_sections_updated_at BEFORE UPDATE ON sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 공통서식 라이브러리 (Phase C)
CREATE TABLE IF NOT EXISTS form_templates (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  team_id      UUID REFERENCES teams(id) ON DELETE SET NULL,
  title        TEXT NOT NULL,
  agency       TEXT,
  category     TEXT,
  description  TEXT,
  storage_path TEXT NOT NULL,
  file_type    TEXT NOT NULL,
  is_public    BOOLEAN NOT NULL DEFAULT false,
  use_count    INT NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS form_template_id UUID REFERENCES form_templates(id);

ALTER TABLE form_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS templates_select ON form_templates FOR SELECT
  USING (
    is_public = true
    OR owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
  );
CREATE POLICY IF NOT EXISTS templates_insert ON form_templates FOR INSERT
  WITH CHECK (owner_id = auth.uid());
CREATE POLICY IF NOT EXISTS templates_delete ON form_templates FOR DELETE
  USING (owner_id = auth.uid());

-- RFP 캘린더 (Phase D)
CREATE TABLE IF NOT EXISTS rfp_calendar (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id      UUID REFERENCES teams(id) ON DELETE CASCADE,
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  agency       TEXT,
  deadline     TIMESTAMPTZ NOT NULL,
  proposal_id  UUID REFERENCES proposals(id) ON DELETE SET NULL,
  status       TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open','submitted','won','lost')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rfp_calendar_owner_idx ON rfp_calendar(owner_id);
CREATE INDEX IF NOT EXISTS rfp_calendar_deadline_idx ON rfp_calendar(deadline);

ALTER TABLE rfp_calendar ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS rfp_calendar_access ON rfp_calendar
  USING (
    owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
  );
CREATE POLICY IF NOT EXISTS rfp_calendar_insert ON rfp_calendar FOR INSERT
  WITH CHECK (owner_id = auth.uid());
CREATE POLICY IF NOT EXISTS rfp_calendar_update ON rfp_calendar FOR UPDATE
  USING (owner_id = auth.uid());
CREATE POLICY IF NOT EXISTS rfp_calendar_delete ON rfp_calendar FOR DELETE
  USING (owner_id = auth.uid());
