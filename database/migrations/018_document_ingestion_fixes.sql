-- ==========================================
-- 018: Document Ingestion Schema Fixes
-- Aligns intranet_documents with API requirements
-- ==========================================

-- 1) Fix intranet_documents table
-- Make project_id and file_slot nullable for standalone documents
-- Update doc_type enum to match API (Korean names)

ALTER TABLE intranet_documents
    ALTER COLUMN project_id DROP NOT NULL,
    ALTER COLUMN file_slot DROP NOT NULL,
    ALTER COLUMN file_type DROP NOT NULL;

-- Drop and recreate CHECK constraint to include Korean doc_type values
ALTER TABLE intranet_documents
    DROP CONSTRAINT IF EXISTS intranet_documents_doc_type_check;

ALTER TABLE intranet_documents
    ADD CONSTRAINT intranet_documents_doc_type_check
    CHECK (doc_type IN ('보고서', '제안서', '실적', '기타', 'proposal', 'report', 'presentation', 'contract', 'reference', 'other'));

-- Update UNIQUE constraint to allow NULL project_id
ALTER TABLE intranet_documents
    DROP CONSTRAINT IF EXISTS intranet_documents_project_id_file_slot_key;

-- Recreate with handling for NULL project_id (documents can exist without project)
CREATE UNIQUE INDEX IF NOT EXISTS idx_intranet_documents_project_file_slot
    ON intranet_documents(project_id, file_slot)
    WHERE project_id IS NOT NULL AND file_slot IS NOT NULL;

-- 2) Add default processing_status values
ALTER TABLE intranet_documents
    ALTER COLUMN processing_status SET DEFAULT 'extracting';

-- 3) Ensure RLS policies still work with nullable project_id
-- (existing policies check org_id, which is still NOT NULL)

COMMENT ON TABLE intranet_documents IS 'Intranet documents - can be project-based (with project_id/file_slot) or standalone (project_id=NULL)';
