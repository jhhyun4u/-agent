-- Migration Phase 3: Update foreign keys to link with master_projects
-- Date: 2026-04-11
-- Purpose: Connect intranet_documents and project_archive to master_projects

-- Step 1: Add master_project_id column to intranet_documents
ALTER TABLE intranet_documents
ADD COLUMN master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;

-- Create index for performance
CREATE INDEX idx_intranet_documents_master_project ON intranet_documents(master_project_id);

-- Step 2: Populate master_project_id in intranet_documents
UPDATE intranet_documents
SET master_project_id = mp.id
FROM master_projects mp
WHERE intranet_documents.project_id = mp.legacy_idx
  AND intranet_documents.org_id = mp.org_id
  AND mp.project_type = 'historical';

-- Step 3: Update storage_path to new format: projects/{master_project_id}/intranet-documents/{filename}
UPDATE intranet_documents
SET storage_path = 'projects/' || master_project_id || '/intranet-documents/' || filename
WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';

-- Step 4: Add master_project_id column to project_archive
ALTER TABLE project_archive
ADD COLUMN master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;

-- Create index for performance
CREATE INDEX idx_project_archive_master_project ON project_archive(master_project_id);

-- Step 5: Populate master_project_id in project_archive
UPDATE project_archive
SET master_project_id = mp.id
FROM master_projects mp
WHERE project_archive.proposal_id = mp.proposal_id
  AND project_archive.org_id = mp.org_id
  AND mp.project_type IN ('active_proposal', 'completed_proposal');

-- Step 6: Update storage_path in project_archive to new format: projects/{master_project_id}/proposal-archive/{category}/{filename}
UPDATE project_archive
SET storage_path = 'projects/' || master_project_id || '/proposal-archive/' || COALESCE(category, 'other') || '/' || filename
WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';

-- Step 7: Update document_count in master_projects
UPDATE master_projects
SET document_count = (
    SELECT COUNT(*) FROM intranet_documents
    WHERE intranet_documents.master_project_id = master_projects.id
)
WHERE project_type = 'historical';

-- Step 8: Update archive_count in master_projects
UPDATE master_projects
SET archive_count = (
    SELECT COUNT(*) FROM project_archive
    WHERE project_archive.master_project_id = master_projects.id
)
WHERE project_type IN ('active_proposal', 'completed_proposal');

-- Step 9: Verify foreign key relationships
SELECT
    'intranet_documents' as table_name,
    COUNT(*) as total_rows,
    COUNT(master_project_id) as with_master_project,
    COUNT(storage_path) as with_new_storage_path
FROM intranet_documents
UNION ALL
SELECT
    'project_archive' as table_name,
    COUNT(*) as total_rows,
    COUNT(master_project_id) as with_master_project,
    COUNT(storage_path) as with_new_storage_path
FROM project_archive;

-- Step 10: Log migration completion
INSERT INTO audit_log (
    org_id,
    user_id,
    action,
    table_name,
    record_id,
    old_value,
    new_value,
    created_at
)
VALUES (
    NULL,
    NULL,
    'foreign_key_update_complete',
    'intranet_documents, project_archive',
    NULL,
    NULL,
    jsonb_build_object(
        'intranet_documents_linked', (SELECT COUNT(*) FROM intranet_documents WHERE master_project_id IS NOT NULL),
        'project_archive_linked', (SELECT COUNT(*) FROM project_archive WHERE master_project_id IS NOT NULL)
    ),
    CURRENT_TIMESTAMP
);
