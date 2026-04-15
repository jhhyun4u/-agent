/**
 * Migration 028: Vault Metadata Extended Fields & Indexes
 * Adds GIN indexes for advanced metadata filtering on vault_documents
 *
 * Supports filtering by:
 * - industry (string)
 * - tech_stack (array of strings)
 * - team_size (integer range)
 * - duration_months (integer range)
 */

-- GIN index on industry field (string matching)
CREATE INDEX IF NOT EXISTS idx_vault_documents_metadata_industry
ON vault_documents
USING GIN ((metadata->'industry'));

-- GIN index on tech_stack array (contains checking)
CREATE INDEX IF NOT EXISTS idx_vault_documents_metadata_tech_stack
ON vault_documents
USING GIN ((metadata->'tech_stack'));

-- B-tree index on team_size integer (range queries)
CREATE INDEX IF NOT EXISTS idx_vault_documents_metadata_team_size
ON vault_documents
(((metadata->>'team_size')::int));

-- B-tree index on duration_months integer (range queries)
CREATE INDEX IF NOT EXISTS idx_vault_documents_metadata_duration_months
ON vault_documents
(((metadata->>'duration_months')::int));

-- JSONB contains operator index (for general metadata queries)
CREATE INDEX IF NOT EXISTS idx_vault_documents_metadata_general
ON vault_documents
USING GIN (metadata);
