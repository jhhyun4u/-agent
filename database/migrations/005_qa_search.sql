-- PSM-16: Q&A 기록 검색 가능 저장
-- presentation_qa 테이블에 임베딩·콘텐츠 연결·카테고리·작성자 추가

ALTER TABLE presentation_qa
  ADD COLUMN IF NOT EXISTS embedding vector(1536),
  ADD COLUMN IF NOT EXISTS content_library_id UUID REFERENCES content_library(id),
  ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general',
  ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);

-- 시맨틱 검색용 IVFFlat 인덱스
CREATE INDEX IF NOT EXISTS idx_presentation_qa_embedding
  ON presentation_qa USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- 조회 성능용 B-tree 인덱스
CREATE INDEX IF NOT EXISTS idx_presentation_qa_proposal_id
  ON presentation_qa (proposal_id);

CREATE INDEX IF NOT EXISTS idx_presentation_qa_category
  ON presentation_qa (category);

-- 시맨틱 검색 RPC 함수
CREATE OR REPLACE FUNCTION search_qa_by_embedding(
  query_embedding vector(1536),
  match_org_id UUID,
  match_count INT DEFAULT 10,
  filter_category TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  proposal_id UUID,
  question TEXT,
  answer TEXT,
  category TEXT,
  evaluator_reaction TEXT,
  memo TEXT,
  created_at TIMESTAMPTZ,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    pq.id,
    pq.proposal_id,
    pq.question,
    pq.answer,
    pq.category,
    pq.evaluator_reaction,
    pq.memo,
    pq.created_at,
    1 - (pq.embedding <=> query_embedding) AS similarity
  FROM presentation_qa pq
  JOIN proposals p ON p.id = pq.proposal_id
  WHERE p.org_id = match_org_id
    AND pq.embedding IS NOT NULL
    AND (filter_category IS NULL OR pq.category = filter_category)
  ORDER BY pq.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;
