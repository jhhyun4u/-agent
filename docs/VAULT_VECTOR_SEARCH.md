# Vault Vector Search Implementation

## Overview

This document describes the vector search implementation for the Vault AI Chat system, enabling semantic search across completed projects and government guidelines using OpenAI embeddings.

## Architecture

### Three-Layer Search Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌────────┐  ┌──────────┐  ┌────────────┐
   │ SQL    │  │ Vector   │  │ Metadata   │
   │ Search │  │ Search   │  │ Filters    │
   └────────┘  └──────────┘  └────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Deduplication & Merging      │
        │ - Average scores             │
        │ - Prefer exact matches       │
        │ - Remove duplicates          │
        └──────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Sort by Relevance Score      │
        │ - SQL exact: 0.95            │
        │ - Vector semantic: 0-1.0     │
        │ - Merged: averaged           │
        └──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Return Results │
              │ (max limit)    │
              └────────────────┘
```

### Search Modes by Handler

#### CompletedProjectsHandler

**SQL Search (Primary)**
- Exact matching on client name, budget, dates
- Confidence: 0.95 (verified against actual data)
- Returns: Closed proposals with financial details

**Vector Search (Secondary)**
- Semantic similarity on project descriptions
- Similarity threshold: 0.7 (configurable)
- Returns: Semantically related projects even if budget/timeline differs
- Finds: "Build mobile app" matches "iOS development" and "Android project"

**Metadata Filters**
- Client name filtering
- Budget range filtering (min/max)
- Date range filtering
- Team member filtering (from JSONB arrays)

#### GovernmentGuidelinesHandler

**SQL Search (Keyword-based)**
- Exact keyword matching for salary, bidding, regulations
- Confidence: 1.0 (government source of truth)
- Returns: Verified government standards

**Vector Search (Semantic)**
- Broader semantic matching for guidelines
- Similarity threshold: 0.6 (lower for more inclusive results)
- Returns: Related guidelines even with different phrasing
- Finds: "정부 급여" matches "공무원 일급" and "기술자 수당"

**No metadata filters** (government data is exact by nature)

## Implementation Details

### CompletedProjectsHandler

```python
# Hybrid search: SQL + Vector
results = []
results.extend(sql_search(...))      # Exact matches
results.extend(vector_search(...))   # Semantic matches

# Deduplication: merge same-document results
merged = deduplicate_results(results)

# Sort by relevance
return sorted(merged, key=relevance_score)[:limit]
```

### Vector Search Flow

1. **Query Embedding Generation**
   ```python
   embedding_service = EmbeddingService()
   results = await embedding_service.search_similar(
       query="describe your need",
       section="completed_projects",
       limit=10,
       threshold=0.7
   )
   ```

2. **RPC Call to PostgreSQL**
   - Uses `vault_search_similar()` function (1536-dimensional vectors)
   - Cosine similarity: `1 - (vector_a <=> vector_b)`
   - Filters by threshold and section
   - Returns: document_id, section, title, content, similarity

3. **Result Enhancement**
   - Fetch full metadata from vault_documents
   - Apply additional metadata filters
   - Convert to SearchResult format
   - Return with similarity scores

### Deduplication Logic

When a document appears in both SQL and vector results:

```python
# Before
[
  SearchResult(id="proj-1", score=0.95, type="exact"),
  SearchResult(id="proj-1", score=0.80, type="semantic"),
  SearchResult(id="proj-2", score=0.75, type="semantic")
]

# After deduplication
[
  SearchResult(id="proj-1", score=0.875, type="exact+semantic"),  # averaged
  SearchResult(id="proj-2", score=0.75, type="semantic")
]
```

## Configuration

### Similarity Thresholds

| Handler | Section | Threshold | Rationale |
|---------|---------|-----------|-----------|
| CompletedProjects | completed_projects | 0.7 | Strict matching for project relevance |
| GovernmentGuidelines | government_guidelines | 0.6 | Broader matching for general guidance |

### Adjust thresholds based on:
- **Higher (0.8-0.9)**: Strict relevance, fewer false positives
- **Lower (0.5-0.6)**: Broader coverage, more exploration

### Tuning Example

```python
# Start with 0.7
results = await embedding_service.search_similar(
    query="mobile development",
    section="completed_projects",
    threshold=0.7
)

# If too few results: lower to 0.65
# If too many irrelevant: raise to 0.75
```

## Performance Characteristics

### Query Performance

- **SQL search**: O(N log N) with indexed columns (client_name, status, dates)
- **Vector search**: O(M log M) with IVFFLAT index on embeddings
  - M ≤ total documents in section
  - Typically <100ms for 10K documents
- **Deduplication**: O(R) where R = total results

### Storage

- **Embeddings**: 1536 dimensions × 4 bytes = ~6.1 KB per document
- **For 10K documents**: ~61 MB total
- **Index overhead**: ~20% additional storage

## Error Handling

### Graceful Degradation

If embedding service is unavailable:
```python
try:
    vector_results = await embedding_service.search_similar(...)
except ImportError:
    logger.warning("Embedding service not available")
    vector_results = []  # Fall back to SQL only
```

### Error Recovery

Database/RPC errors trigger fallback:
- Primary: `vault_search_similar()` RPC function
- Fallback: Direct SQL query (less efficient)

```python
try:
    result = await client.rpc("vault_search_similar", {...})
except Exception:
    # Fallback: direct query without RPC
    result = await client.table("vault_documents").select(...).execute()
```

## Testing

### Unit Tests

```python
# Test vector search returns semantic results
await test_vector_search_returns_semantic_results()

# Test SQL + Vector hybrid search
await test_hybrid_search_combines_sql_and_vector()

# Test deduplication merges scores
await test_deduplication_merges_duplicate_results()

# Test metadata filters on vector results
await test_metadata_filters_on_vector_results()
```

### Integration Tests

```bash
# Run all vector search tests
pytest tests/services/test_vault_vector_search.py -v

# Test with embedding service
pytest tests/integration/test_vault_embedding_integration.py -v

# End-to-end chat flow
pytest tests/integration/test_vault_e2e.py::test_semantic_search_in_chat -v
```

## Usage Examples

### Search Completed Projects

```python
# Natural language semantic search
results = await CompletedProjectsHandler.search(
    query="We need a team that's built mobile apps",
    filters={"budget_min": 30000, "budget_max": 100000},
    limit=5
)

for result in results:
    print(f"Project: {result.document.title}")
    print(f"Match: {result.match_type} (score: {result.relevance_score})")
    print(f"Preview: {result.preview}\n")
```

### Search Government Guidelines

```python
# Semantic search for government salary standards
results = await GovernmentGuidelinesHandler.search(
    query="정부 기술자 급여 기준이 뭐야?",
    limit=10
)

for result in results:
    print(f"Guideline: {result.document.title}")
    print(f"Content: {result.preview}")
```

## Monitoring

### Key Metrics

Track in monitoring system:
- Average search response time
- Embedding service error rate
- RPC vs fallback query ratio
- Search result relevance (user feedback)

### Query

```sql
-- Check embedding coverage
SELECT
  section,
  COUNT(*) as total,
  COUNT(embedding) as embedded,
  ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as coverage_pct
FROM vault_documents
WHERE deleted_at IS NULL
GROUP BY section;

-- Check recent searches
SELECT
  query,
  COUNT(*) as count,
  AVG(response_time_ms) as avg_time,
  COUNT(CASE WHEN error THEN 1 END) as errors
FROM vault_search_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY query
ORDER BY count DESC;
```

## Next Steps

1. **Embedding Coverage**: Generate embeddings for all documents
   - Run: `POST /api/vault/embeddings/generate`
   - Monitor: `/api/vault/embeddings/status`

2. **Threshold Tuning**: Based on user feedback and search quality metrics
   - A/B test different thresholds
   - Monitor user satisfaction with results

3. **Enhanced Metadata Filtering**: Add more filter combinations
   - Industry vertical filters
   - Project size filters
   - Technology stack filters

4. **Search Analytics**: Track search patterns and results
   - User feedback on result relevance
   - Query reformulation patterns
   - Zero-result queries for improvement

## References

- [Vault Embedding Service](../app/services/vault_embedding_service.py)
- [Database Migrations](../database/migrations/022_vault_embedding_generation.sql)
- [Vector Search Tests](../tests/services/test_vault_vector_search.py)
- [API Endpoints](../app/api/routes_vault_embeddings.py)
