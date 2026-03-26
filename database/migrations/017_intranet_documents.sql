-- ==========================================
-- 017: 인트라넷 문서 수집 스키마
-- 인트라넷 MSSQL Project_List → SaaS KB 연동
-- ==========================================

-- 1) 인트라넷 프로젝트 (Project_List 1:1 매핑, company_profile.json 대체)
CREATE TABLE IF NOT EXISTS intranet_projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,

    -- 인트라넷 원본 식별자
    legacy_idx      INTEGER NOT NULL,
    legacy_code     TEXT,
    board_id        TEXT DEFAULT 'PR_PG',

    -- 프로젝트 메타 (Project_List 전 컬럼)
    project_name    TEXT NOT NULL,
    client_name     TEXT,
    client_manager  TEXT,
    client_tel      TEXT,
    client_email    TEXT,
    start_date      DATE,
    end_date        DATE,
    budget_text     TEXT,
    budget_krw      BIGINT,
    manager         TEXT,
    attendants      TEXT,
    partner         TEXT,
    pm              TEXT,
    pm_members      TEXT,
    keywords        TEXT[],
    team            TEXT,
    status          TEXT,
    inout           TEXT,
    progress_pct    INTEGER DEFAULT 0,

    -- 보완 메타 (Excel 부처 매핑 등)
    department      TEXT,
    domain          TEXT,

    -- 마이그레이션 상태
    migration_status TEXT DEFAULT 'metadata_only'
        CHECK (migration_status IN ('metadata_only', 'files_uploading', 'completed', 'failed')),
    file_count       INTEGER DEFAULT 0,

    -- KB 시드 연동 추적
    capability_id    UUID REFERENCES capabilities(id),
    client_intel_id  UUID REFERENCES client_intelligence(id),

    -- 벡터 검색 (프로젝트 단위 유사도)
    embedding        vector(1536),

    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now(),

    UNIQUE(org_id, legacy_idx, board_id)
);

CREATE INDEX IF NOT EXISTS idx_intranet_projects_org ON intranet_projects(org_id);
CREATE INDEX IF NOT EXISTS idx_intranet_projects_client ON intranet_projects(client_name);
CREATE INDEX IF NOT EXISTS idx_intranet_projects_status ON intranet_projects(status);
CREATE INDEX IF NOT EXISTS idx_intranet_projects_embedding ON intranet_projects
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);


-- 2) 인트라넷 문서 (프로젝트당 최대 10개 파일 슬롯)
CREATE TABLE IF NOT EXISTS intranet_documents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        UUID REFERENCES intranet_projects(id) ON DELETE CASCADE NOT NULL,
    org_id            UUID REFERENCES organizations(id) NOT NULL,

    -- 파일 슬롯 정보
    file_slot         TEXT NOT NULL,
    doc_type          TEXT NOT NULL
        CHECK (doc_type IN ('proposal', 'report', 'presentation', 'contract', 'reference', 'other')),
    doc_subtype       TEXT,

    -- 파일 메타
    filename          TEXT NOT NULL,
    file_type         TEXT NOT NULL,
    file_size         BIGINT,
    storage_path      TEXT,
    source_hash       TEXT,

    -- 처리 상태
    processing_status TEXT DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'extracting', 'chunking', 'embedding', 'completed', 'failed')),
    extracted_text    TEXT,
    total_chars       INTEGER DEFAULT 0,
    chunk_count       INTEGER DEFAULT 0,
    error_message     TEXT,

    created_at        TIMESTAMPTZ DEFAULT now(),
    updated_at        TIMESTAMPTZ DEFAULT now(),

    UNIQUE(project_id, file_slot)
);

CREATE INDEX IF NOT EXISTS idx_intranet_docs_org ON intranet_documents(org_id);
CREATE INDEX IF NOT EXISTS idx_intranet_docs_project ON intranet_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_intranet_docs_status ON intranet_documents(processing_status);


-- 3) 문서 청크 (벡터 검색 대상)
CREATE TABLE IF NOT EXISTS document_chunks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id        UUID REFERENCES intranet_documents(id) ON DELETE CASCADE NOT NULL,
    org_id             UUID REFERENCES organizations(id) NOT NULL,

    chunk_index        INTEGER NOT NULL,
    chunk_type         TEXT NOT NULL DEFAULT 'section'
        CHECK (chunk_type IN ('section', 'slide', 'article', 'window')),
    section_title      TEXT,
    content            TEXT NOT NULL,
    char_count         INTEGER NOT NULL,

    embedding          vector(1536),

    content_library_id UUID REFERENCES content_library(id),

    created_at         TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_doc_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_org ON document_chunks(org_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- 4) content_library 확장: 소스 문서 추적
ALTER TABLE content_library
    ADD COLUMN IF NOT EXISTS source_document_id UUID REFERENCES intranet_documents(id);


-- 5) 벡터 검색 RPC: 문서 청크 검색
CREATE OR REPLACE FUNCTION search_document_chunks_by_embedding(
    query_embedding vector(1536),
    match_org_id UUID,
    match_count INT DEFAULT 5,
    filter_doc_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    section_title TEXT,
    content TEXT,
    doc_type TEXT,
    doc_subtype TEXT,
    project_name TEXT,
    client_name TEXT,
    filename TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.section_title,
        dc.content,
        ind.doc_type,
        ind.doc_subtype,
        ip.project_name,
        ip.client_name,
        ind.filename,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    JOIN intranet_documents ind ON dc.document_id = ind.id
    JOIN intranet_projects ip ON ind.project_id = ip.id
    WHERE dc.org_id = match_org_id
      AND dc.embedding IS NOT NULL
      AND (filter_doc_type IS NULL OR ind.doc_type = filter_doc_type)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 6) 벡터 검색 RPC: 프로젝트 단위 검색 (공고 매칭용)
CREATE OR REPLACE FUNCTION search_projects_by_embedding(
    query_embedding vector(1536),
    match_org_id UUID,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    project_name TEXT,
    client_name TEXT,
    department TEXT,
    budget_krw BIGINT,
    keywords TEXT[],
    start_date DATE,
    end_date DATE,
    status TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        ip.id, ip.project_name, ip.client_name, ip.department,
        ip.budget_krw, ip.keywords, ip.start_date, ip.end_date,
        ip.status,
        1 - (ip.embedding <=> query_embedding) AS similarity
    FROM intranet_projects ip
    WHERE ip.org_id = match_org_id
      AND ip.embedding IS NOT NULL
    ORDER BY ip.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- 7) RLS 정책
ALTER TABLE intranet_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE intranet_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- 사용자 정책
CREATE POLICY intranet_projects_user ON intranet_projects
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM users WHERE id = auth.uid())
    );
CREATE POLICY intranet_documents_user ON intranet_documents
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM users WHERE id = auth.uid())
    );
CREATE POLICY document_chunks_user ON document_chunks
    FOR SELECT USING (
        org_id IN (SELECT org_id FROM users WHERE id = auth.uid())
    );

-- 서비스 역할 정책 (백엔드)
CREATE POLICY intranet_projects_service ON intranet_projects
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY intranet_documents_service ON intranet_documents
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY document_chunks_service ON document_chunks
    FOR ALL TO service_role USING (true) WITH CHECK (true);
