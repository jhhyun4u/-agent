-- Vault AI Chat Phase 2 Week 1 — Credentials (실적증명서) Management
-- Stores project completion certificates with OCR extraction and file management
-- Design Ref: §Phase 2 Week 2-1 — vault_credentials table
-- Supports: 준공증명서, 실제완료증명서, 실적보증서, 기술보증서, 기타증명서

BEGIN;

-- Create vault_credentials table
CREATE TABLE IF NOT EXISTS vault_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Project reference
    completed_project_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- Credential metadata
    credential_type TEXT NOT NULL CHECK (credential_type IN (
        '준공증명서',
        '실제완료증명서',
        '실적보증서',
        '기술보증서',
        '검수증명',
        '납품증명',
        '기타증명서'
    )),
    title TEXT NOT NULL,

    -- File storage
    file_path TEXT NOT NULL,  -- Supabase Storage path
    file_format TEXT NOT NULL CHECK (file_format IN ('pdf', 'hwp', 'hwpx', 'docx', 'doc', 'png', 'jpg', 'jpeg')),
    file_size_bytes INTEGER,  -- Original file size

    -- OCR extraction
    extracted_text TEXT,  -- Full OCR extracted text
    extracted_text_updated_at TIMESTAMPTZ,  -- When OCR was last run
    ocr_status TEXT DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'processing', 'success', 'failed')),
    ocr_error_message TEXT,  -- Error details if OCR failed

    -- Key fields extracted by OCR
    credential_issue_date DATE,  -- 증명서 발급일
    credential_issuer TEXT,  -- 발급 기관 (예: OOO시 건설과)
    project_name TEXT,  -- 증명서상 프로젝트명
    project_amount DECIMAL(15,0),  -- 사업비 (있으면)
    project_end_date DATE,  -- 준공/완료일

    -- Metadata (flexible storage for additional fields)
    metadata JSONB DEFAULT '{}'::jsonb,  -- {
                                          --   "manual_review_needed": boolean,
                                          --   "quality_score": 0-100,
                                          --   "extracted_fields": {...},
                                          --   "review_notes": "..."
                                          -- }

    -- Audit fields
    uploaded_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Soft delete support
    deleted_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vault_credentials_project
    ON vault_credentials (completed_project_id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_credentials_type
    ON vault_credentials (credential_type) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_credentials_created
    ON vault_credentials (created_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_credentials_issuer
    ON vault_credentials (credential_issuer) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_vault_credentials_ocr_status
    ON vault_credentials (ocr_status) WHERE ocr_status IN ('pending', 'processing');

-- GIN index for JSONB metadata search
CREATE INDEX IF NOT EXISTS idx_vault_credentials_metadata
    ON vault_credentials USING GIN (metadata);

-- Enable RLS
ALTER TABLE vault_credentials ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see credentials from their team's projects
CREATE POLICY IF NOT EXISTS "Users see credentials from their team projects"
    ON vault_credentials
    FOR SELECT
    USING (
        completed_project_id IN (
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

-- RLS Policy: Users can insert credentials for their team's projects
CREATE POLICY IF NOT EXISTS "Users can upload credentials for their team projects"
    ON vault_credentials
    FOR INSERT
    WITH CHECK (
        completed_project_id IN (
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
        AND uploaded_by = auth.uid()
    );

-- RLS Policy: Users can update their own uploads
CREATE POLICY IF NOT EXISTS "Users can update their own credential uploads"
    ON vault_credentials
    FOR UPDATE
    USING (uploaded_by = auth.uid())
    WITH CHECK (uploaded_by = auth.uid());

-- RLS Policy: Users can soft-delete their own uploads
CREATE POLICY IF NOT EXISTS "Users can delete their own credential uploads"
    ON vault_credentials
    FOR DELETE
    USING (uploaded_by = auth.uid());

-- Update timestamp trigger
CREATE TRIGGER update_vault_credentials_updated_at
    BEFORE UPDATE ON vault_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE vault_credentials IS '실적증명서 (completion certificates) storage with OCR extraction';
COMMENT ON COLUMN vault_credentials.credential_type IS 'Type of credential: 준공증명서, 실제완료증명서, 실적보증서, etc.';
COMMENT ON COLUMN vault_credentials.file_path IS 'Supabase Storage path to the credential file';
COMMENT ON COLUMN vault_credentials.extracted_text IS 'Full text extracted by OCR pipeline';
COMMENT ON COLUMN vault_credentials.ocr_status IS 'OCR processing status: pending, processing, success, failed';
COMMENT ON COLUMN vault_credentials.metadata IS 'Additional extracted fields and metadata in JSONB format';
COMMENT ON COLUMN vault_credentials.deleted_at IS 'Soft delete timestamp for audit trail';

COMMIT;
