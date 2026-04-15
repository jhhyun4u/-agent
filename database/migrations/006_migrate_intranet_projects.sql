-- Migration Phase 2: Migrate data from intranet_projects to master_projects
-- Date: 2026-04-11
-- Purpose: Copy historical project data with proper field mapping

-- Step 1: Migrate intranet_projects → master_projects (historical type)
INSERT INTO master_projects (
    id,
    org_id,
    project_name,
    project_year,
    start_date,
    end_date,
    client_name,
    summary,
    description,
    budget_krw,
    project_type,
    proposal_status,
    result_status,
    execution_status,
    legacy_idx,
    legacy_code,
    proposal_id,
    actual_teams,
    actual_participants,
    proposal_teams,
    proposal_participants,
    document_count,
    archive_count,
    keywords,
    embedding,
    created_at,
    updated_at
)
SELECT
    id,
    org_id,
    pr_title as project_name,
    EXTRACT(YEAR FROM COALESCE(pr_start_date, CURRENT_DATE))::integer as project_year,
    pr_start_date as start_date,
    pr_end_date as end_date,
    pr_com as client_name,
    pr_summary as summary,
    pr_description as description,
    pr_budget_krw as budget_krw,
    'historical' as project_type,
    'RESULT_ANNOUNCED' as proposal_status,
    NULL::text as result_status,
    NULL::text as execution_status,
    idx_no as legacy_idx,
    pr_code as legacy_code,
    NULL::uuid as proposal_id,
    -- actual_teams: JSON 배열로 구성 (현재 스키마에서 pr_team 필드 사용)
    CASE
        WHEN pr_team IS NOT NULL AND pr_team != '' THEN
            jsonb_build_array(
                jsonb_build_object(
                    'team_id', gen_random_uuid()::text,
                    'team_name', pr_team
                )
            )
        ELSE
            jsonb_build_array()
    END as actual_teams,
    -- actual_participants: JSON 배열로 구성 (현재 스키마의 pr_manager 사용, 추후 상세화 필요)
    CASE
        WHEN pr_manager IS NOT NULL AND pr_manager != '' THEN
            jsonb_build_array(
                jsonb_build_object(
                    'name', pr_manager,
                    'role', 'Manager',
                    'team_id', (CASE WHEN pr_team IS NOT NULL THEN gen_random_uuid()::text ELSE NULL END),
                    'years_involved', 0
                )
            )
        ELSE
            jsonb_build_array()
    END as actual_participants,
    NULL::jsonb as proposal_teams,
    NULL::jsonb as proposal_participants,
    0 as document_count,
    0 as archive_count,
    -- keywords: pr_key 필드를 쉼표로 분리하여 배열로 변환
    CASE
        WHEN pr_key IS NOT NULL AND pr_key != '' THEN
            STRING_TO_ARRAY(
                TRIM(BOTH FROM pr_key),
                ','
            )
        ELSE
            ARRAY[]::text[]
    END as keywords,
    NULL::vector as embedding,
    COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
    COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
FROM intranet_projects
WHERE org_id IS NOT NULL;

-- Step 2: Log migration result
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
SELECT
    org_id,
    NULL,
    'migrate_intranet_to_master',
    'master_projects',
    id,
    NULL,
    jsonb_build_object(
        'project_name', project_name,
        'legacy_idx', legacy_idx,
        'legacy_code', legacy_code
    ),
    CURRENT_TIMESTAMP
FROM master_projects
WHERE project_type = 'historical';

-- Step 3: Verify migration count
SELECT
    COUNT(*) as total_historical,
    COUNT(CASE WHEN actual_teams IS NOT NULL AND jsonb_array_length(actual_teams) > 0 THEN 1 END) as with_teams,
    COUNT(CASE WHEN keywords IS NOT NULL AND array_length(keywords, 1) > 0 THEN 1 END) as with_keywords
FROM master_projects
WHERE project_type = 'historical';
