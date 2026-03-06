-- ============================================================
-- Tenopa Proposer Platform v1 -- Database Schema v10
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- teams
CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_by  UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- team_members
CREATE TABLE team_members (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id    UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role       TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),  -- 설계 명세: viewer 추가
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (team_id, user_id)
);

-- invitations
CREATE TABLE invitations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id     UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member', 'viewer')),  -- 설계 명세: viewer 추가
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired')),
    invited_by  UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    expires_at  TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '7 days'),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (team_id, email)
);

-- proposals (owner_id ON DELETE RESTRICT: 계정 삭제 전 proposals 이관 필요)
CREATE TABLE proposals (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title                   TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'initialized'
                                CHECK (status IN (
                                    'initialized','processing','completed','failed',
                                    'pending','reviewing','approved'  -- 설계 명세 상태값 포함
                                )),
    owner_id                UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
    team_id                 UUID REFERENCES teams(id) ON DELETE SET NULL,
    current_phase           TEXT,
    phases_completed        INT NOT NULL DEFAULT 0,
    failed_phase            TEXT,
    rfp_filename            TEXT,
    rfp_content             TEXT,
    rfp_content_truncated   BOOLEAN NOT NULL DEFAULT false,
    storage_path_docx       TEXT,
    storage_path_pptx       TEXT,
    storage_path_rfp        TEXT,
    storage_upload_failed   BOOLEAN NOT NULL DEFAULT false,
    win_result              TEXT CHECK (win_result IN ('won', 'lost', 'pending')),  -- 설계 명세 CHECK 추가
    bid_amount              BIGINT,
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX proposals_title_trgm ON proposals USING GIN (title gin_trgm_ops);
ALTER TABLE proposals REPLICA IDENTITY FULL;

-- proposal_phases
CREATE TABLE proposal_phases (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id  UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    phase_number INT NOT NULL,
    phase_name   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed')),
    artifact     JSONB,
    error_msg    TEXT,
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE (proposal_id, phase_number)
);

-- comments
CREATE TABLE comments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id  UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    section      TEXT,                              -- 제안서 섹션 참조 (설계 명세 반영)
    resolved     BOOLEAN NOT NULL DEFAULT false,   -- 코멘트 해결 여부 (설계 명세 반영)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- usage_logs
CREATE TABLE usage_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id   UUID REFERENCES proposals(id) ON DELETE SET NULL,
    owner_id      UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    team_id       UUID REFERENCES teams(id) ON DELETE SET NULL,
    phase_number  INT,
    input_tokens  INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    model         TEXT,
    logged_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- g2b_cache
CREATE TABLE g2b_cache (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash   TEXT NOT NULL UNIQUE,
    endpoint     TEXT NOT NULL,
    response     JSONB NOT NULL,
    cached_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours')
);

-- Triggers + Functions
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE FUNCTION mark_stale_running_proposals()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    UPDATE proposals
    SET status = 'failed',
        notes  = COALESCE(notes, '') || ' [서버 재시작으로 중단됨]',
        updated_at = now()
    WHERE status = 'processing';
END;
$$;

CREATE OR REPLACE FUNCTION cleanup_expired_g2b_cache()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM g2b_cache WHERE expires_at < now();
END;
$$;

-- RLS
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
CREATE POLICY proposals_access ON proposals
    USING (
        owner_id = auth.uid()
        OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    );

ALTER TABLE proposal_phases ENABLE ROW LEVEL SECURITY;
CREATE POLICY phases_access ON proposal_phases
    USING (
        proposal_id IN (
            SELECT id FROM proposals
            WHERE owner_id = auth.uid()
               OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
        )
    );

ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY comments_access ON comments
    USING (
        proposal_id IN (
            SELECT id FROM proposals
            WHERE owner_id = auth.uid()
               OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
        )
    );

CREATE POLICY comments_insert ON comments FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND proposal_id IN (
            SELECT p.id FROM proposals p
            JOIN team_members tm ON p.team_id = tm.team_id
            WHERE tm.user_id = auth.uid()
            UNION
            SELECT id FROM proposals WHERE owner_id = auth.uid()
        )
    );

ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY usage_logs_access ON usage_logs
    USING (
        owner_id = auth.uid()
        OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    );

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
CREATE POLICY teams_access ON teams
    USING (
        id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
        OR created_by = auth.uid()
    );

ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY team_members_access ON team_members
    USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY invitations_access ON invitations
    USING (
        team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = auth.uid() AND role = 'admin'
        )
    );
