-- KB Enhancement: capabilities 임베딩 + 시맨틱 검색 RPC
-- Phase B-1: capabilities 테이블에 임베딩 컬럼 추가

ALTER TABLE capabilities
  ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_capabilities_embedding
  ON capabilities USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 50);

-- 시맨틱 검색 RPC
CREATE OR REPLACE FUNCTION search_capabilities_by_embedding(
  query_embedding vector(1536),
  match_org_id UUID,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  type TEXT,
  title TEXT,
  detail TEXT,
  keywords TEXT[],
  similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id, c.type, c.title, c.detail, c.keywords,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM capabilities c
  WHERE c.org_id = match_org_id
    AND c.embedding IS NOT NULL
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Phase D-3: 중복 콘텐츠 탐지 RPC
CREATE OR REPLACE FUNCTION find_content_duplicates(
  match_org_id UUID,
  threshold FLOAT DEFAULT 0.9,
  match_limit INT DEFAULT 20
)
RETURNS TABLE (
  id_a UUID,
  title_a TEXT,
  id_b UUID,
  title_b TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    a.id AS id_a, a.title AS title_a,
    b.id AS id_b, b.title AS title_b,
    1 - (a.embedding <=> b.embedding) AS similarity
  FROM content_library a
  JOIN content_library b ON a.id < b.id AND a.org_id = b.org_id
  WHERE a.org_id = match_org_id
    AND a.embedding IS NOT NULL
    AND b.embedding IS NOT NULL
    AND 1 - (a.embedding <=> b.embedding) > threshold
  ORDER BY similarity DESC
  LIMIT match_limit;
END;
$$;
