-- Vault Embedding Generation Setup
-- Prepares stored procedures for embedding generation
-- Note: Embeddings are typically generated via FastAPI service

-- Create a function to mark documents needing embedding regeneration
CREATE OR REPLACE FUNCTION vault_mark_for_embedding_refresh()
RETURNS TRIGGER AS $$
BEGIN
  -- If content changed, mark for regeneration by clearing embedding
  IF NEW.content <> OLD.content THEN
    NEW.embedding = NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to refresh embeddings on content update
CREATE TRIGGER vault_documents_content_changed
  BEFORE UPDATE ON vault_documents
  FOR EACH ROW
  EXECUTE FUNCTION vault_mark_for_embedding_refresh();

-- Create a view for documents needing embeddings
CREATE OR REPLACE VIEW vault_documents_needing_embeddings AS
SELECT id, content, section, document_type
FROM vault_documents
WHERE embedding IS NULL
  AND deleted_at IS NULL
ORDER BY created_at DESC;

-- Create a utility function to get similar documents
CREATE OR REPLACE FUNCTION vault_search_similar(
  query_embedding VECTOR(1536),
  similarity_threshold FLOAT DEFAULT 0.7,
  limit_count INT DEFAULT 10
)
RETURNS TABLE(
  document_id UUID,
  section TEXT,
  title TEXT,
  content TEXT,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    vd.id,
    vd.section,
    vd.title,
    vd.content,
    (1 - (vd.embedding <=> query_embedding))::FLOAT AS similarity
  FROM vault_documents vd
  WHERE vd.deleted_at IS NULL
    AND (1 - (vd.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY similarity DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create an audit table for tracking embedding operations
CREATE TABLE IF NOT EXISTS vault_embedding_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES vault_documents(id) ON DELETE CASCADE,
  embedding_service TEXT, -- 'openai', 'local', etc
  embedding_model TEXT, -- 'text-embedding-3-small', etc
  status TEXT CHECK (status IN ('pending', 'success', 'error')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_vault_embedding_audit_status ON vault_embedding_audit(status);
CREATE INDEX idx_vault_embedding_audit_document_id ON vault_embedding_audit(document_id);

COMMENT ON FUNCTION vault_search_similar IS 'Search for similar documents using vector embeddings with cosine similarity';
COMMENT ON VIEW vault_documents_needing_embeddings IS 'View of documents that need embedding generation';
COMMENT ON TABLE vault_embedding_audit IS 'Audit log for embedding generation operations';
