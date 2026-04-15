-- Vault Data Loading Migration
-- Populates vault_documents from existing proposals (initial data seeding)

-- Load completed projects from proposals
INSERT INTO vault_documents (
  document_id,
  document_type,
  section,
  title,
  content,
  metadata,
  created_at
)
SELECT
  p.id,
  'proposal',
  'completed_projects',
  p.title,
  COALESCE(
    p.description || ' | Status: ' || p.status || ' | Phases: ' || p.phases_completed || '/5',
    'No description'
  ) AS content,
  jsonb_build_object(
    'client', p.client,
    'budget', p.budget_usd,
    'deadline', p.deadline,
    'status', p.status,
    'phases_completed', p.phases_completed,
    'bid_number', p.bid_number
  ) AS metadata,
  p.created_at
FROM proposals p
WHERE p.status IN ('completed', 'won', 'lost', 'archived')
  AND p.deleted_at IS NULL
ON CONFLICT DO NOTHING;

-- Notes for manual completion:
-- 1. Government Guidelines should be loaded from your external source
--    INSERT INTO vault_documents (document_id, document_type, section, title, content, metadata)
--    VALUES (...)
--
-- 2. Lessons Learned should be extracted from project notes
--    INSERT INTO vault_documents (document_id, document_type, section, title, content, metadata)
--    VALUES (...)
--
-- 3. Market Prices should be loaded from pricing_history or market_data tables
--    INSERT INTO vault_documents (document_id, document_type, section, title, content, metadata)
--    VALUES (...)
--
-- 4. After loading documents, regenerate embeddings using:
--    UPDATE vault_documents SET embedding = (embeddings generation service)
--    WHERE embedding IS NULL

-- Add verification query (run after data load)
-- SELECT COUNT(*) as total_documents, section, document_type 
-- FROM vault_documents 
-- GROUP BY section, document_type;
