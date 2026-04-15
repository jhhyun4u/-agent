# Vault AI Chat - Database Setup Guide

## Overview

This document describes the database setup for the Vault AI Chat feature in Phase 1 Week 1.

## Migration Scripts

### 020_vault_conversations.sql
**Purpose**: Core tables and infrastructure for Vault AI Chat

**Tables Created**:
1. `vault_conversations` - Stores AI chat conversations
   - Columns: id, user_id, title, created_at, updated_at, deleted_at
   - Indexes: user_id, created_at, deleted_at filtering
   - RLS: User isolation (users can only see their own conversations)

2. `vault_messages` - Individual messages within conversations
   - Columns: id, conversation_id, user_id, role (user/assistant), content, sources, created_at, updated_at
   - Indexes: conversation_id, user_id, created_at
   - RLS: User isolation

3. `vault_documents` - Knowledge base documents with vector embeddings
   - Columns: id, document_id, document_type, section, title, content, metadata, embedding (VECTOR(1536)), created_at, updated_at, deleted_at
   - Vectors: OpenAI text-embedding-3-small 1536-dimensional
   - Indexes: document_id, section, document_type, created_at, IVFFLAT for vector similarity search
   - RLS: Read-only for all authenticated users

**Features**:
- pgvector extension for similarity search
- Row-level security (RLS) for multi-tenant isolation
- Soft delete support via deleted_at column
- Vector indexing with IVFFLAT for efficient cosine similarity search

### 021_vault_data_load.sql
**Purpose**: Initial data seeding from existing proposals

**Operations**:
1. Loads completed projects from `proposals` table into `vault_documents`
   - Filters: status IN ('completed', 'won', 'lost', 'archived')
   - Section: 'completed_projects'
   - Metadata: client, budget, deadline, status, phases_completed, bid_number

**Manual Steps Required**:
1. Load Government Guidelines from external source
2. Extract Lessons Learned from project notes
3. Load Market Prices from pricing_history or market_data tables
4. Generate embeddings for all documents (see 022 migration)

### 022_vault_embedding_generation.sql
**Purpose**: Setup for vector embedding generation and similarity search

**Components**:
1. Trigger: `vault_documents_content_changed`
   - Automatically marks documents for re-embedding when content changes
   - Clears embedding when content is updated

2. View: `vault_documents_needing_embeddings`
   - Lists all documents that need embedding generation
   - Used by embedding service to batch-process documents

3. Function: `vault_search_similar()`
   - Performs vector similarity search with configurable threshold
   - Returns top K similar documents ordered by similarity score
   - Used by the Vault Query Router for source retrieval

4. Audit Table: `vault_embedding_audit`
   - Tracks embedding generation operations
   - Records: document_id, service, model, status, error_message, timestamps
   - Helps debug embedding generation issues

## Deployment Steps

### 1. Pre-Deployment Checks

```bash
# Verify pgvector extension is available in Supabase
# Dashboard → Database → Extensions → Search for "vector"
# If not enabled, enable it from the Dashboard
```

### 2. Apply Migrations in Order

```sql
-- Migration 020: Core tables and infrastructure
-- Dashboard → SQL Editor → Run query from 020_vault_conversations.sql

-- Migration 021: Load initial data
-- Dashboard → SQL Editor → Run query from 021_vault_data_load.sql

-- Migration 022: Embedding infrastructure
-- Dashboard → SQL Editor → Run query from 022_vault_embedding_generation.sql
```

### 3. Verify Tables Created

```sql
-- Check tables exist
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE 'vault_%'
ORDER BY tablename;

-- Check counts
SELECT 'vault_conversations' as table_name, COUNT(*) as count FROM vault_conversations
UNION ALL
SELECT 'vault_messages', COUNT(*) FROM vault_messages
UNION ALL
SELECT 'vault_documents', COUNT(*) FROM vault_documents;
```

### 4. Enable RLS Policies

RLS is automatically enabled in the migration scripts. Verify:

```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename LIKE 'vault_%';

-- Should show: rowsecurity = true for conversations and messages
```

### 5. Generate Embeddings

After data is loaded, generate embeddings using the FastAPI embedding service:

```python
# Backend service (routes_vault_embeddings.py or similar)
from app.services.vault_embedding_service import EmbeddingService

service = EmbeddingService(
    model="text-embedding-3-small",
    provider="openai"
)

# Process documents needing embeddings
await service.embed_documents_batch()
```

## Vector Similarity Search

Once embeddings are generated, use the `vault_search_similar()` function:

```sql
-- Example: Search for similar documents
SELECT * FROM vault_search_similar(
  query_embedding => YOUR_EMBEDDING::vector,
  similarity_threshold => 0.7,
  limit_count => 10
);
```

## Data Model

### Conversation Flow

```
User
  ↓
vault_conversations (conversation metadata)
  ↓
vault_messages (user/assistant message pairs)
  ↓
vault_documents (referenced sources via metadata)
```

### Document Sections

Supported document sections in `vault_documents`:
- `completed_projects` - Finished projects with metadata
- `government_guidelines` - Government requirements and regulations
- `market_prices` - Market pricing and cost information
- `lessons_learned` - Lessons from past projects (future)
- `labor_rates` - Labor cost information (future)
- `competitors` - Competitor analysis (future)

### Document Types

Currently supported:
- `proposal` - From existing proposals table
- `guideline` - Government/regulatory guidelines
- `lesson` - Project lessons learned
- `market_data` - Market pricing data

## Monitoring

### Track Embedding Generation

```sql
-- View embedding generation status
SELECT 
  document_id,
  status,
  COUNT(*) as count
FROM vault_embedding_audit
GROUP BY status;

-- Check for errors
SELECT * FROM vault_embedding_audit 
WHERE status = 'error' 
ORDER BY created_at DESC;
```

### Monitor Document Coverage

```sql
-- Coverage by section
SELECT 
  section,
  COUNT(*) as total_documents,
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedded
FROM vault_documents
WHERE deleted_at IS NULL
GROUP BY section;
```

## Troubleshooting

### pgvector Not Available

```
Error: extension "vector" does not exist
```

**Solution**: Enable pgvector in Supabase Dashboard:
1. Go to Database → Extensions
2. Search for "vector"
3. Click "Enable"

### RLS Blocking Access

If users can't see conversations:
1. Verify `user_id` is correct in vault_conversations
2. Check RLS policies are applied
3. Ensure `auth.uid()` returns the correct user ID

### Embedding Generation Stuck

If `vault_documents_needing_embeddings` view shows many pending documents:
1. Check `vault_embedding_audit` for errors
2. Verify OpenAI API key is valid
3. Check rate limits on embedding service
4. Review error messages in logs

## API Endpoints

### Conversation Management
- `GET /api/vault/conversations` - List user's conversations
- `GET /api/vault/conversations/{id}` - Get conversation details
- `GET /api/vault/conversations/{id}/messages` - Get messages
- `POST /api/vault/conversations` - Create new conversation
- `DELETE /api/vault/conversations/{id}` - Delete conversation

### Chat
- `POST /api/vault/chat` - Send message to Vault AI

### Health
- `GET /api/vault/health` - Health check

## Next Steps

1. **Embedding Generation Service**: Implement batch embedding generation
2. **Enhanced Search**: Add full-text search + semantic search combination
3. **Document Management**: Add UI for manual document management
4. **Analytics**: Track which documents are referenced most often
5. **Fine-tuning**: Optimize embedding models based on usage patterns
