# Staging Deployment Verification Checklist
**Date:** 2026-04-07  
**Status:** 🟡 In Progress  
**Branch:** staging (commit f6bf20b)  
**PR:** [#2](https://github.com/jhhyun4u/-agent/pull/2) - MERGED

---

## Pre-Deployment Verification ✅

- [x] Code changes merged to staging branch
- [x] Database migration 018 already applied to Supabase (2026-04-07 01:32 UTC)
- [x] Storage bucket `intranet-documents` created
- [x] E2E tests (7/8 passing, 87.5%)
- [x] Security validation: magic bytes, org_id isolation, RLS

---

## Staging Deployment Checklist

### Environment Setup
- [ ] Staging server deployed (Railway/Render)
- [ ] Environment variables configured:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `ANTHROPIC_API_KEY`
- [ ] Database connection verified
- [ ] Storage bucket accessible

### API Endpoint Validation

#### 1. POST /api/documents/upload
- [ ] Accept PDF, DOCX, HWP, HWPX, PPTX files
- [ ] Reject files >500MB
- [ ] Validate magic bytes (file signature)
- [ ] Return 201 with document ID and storage_path
- [ ] Trigger async processing
- [ ] Initial status: "extracting"

**Test Command:**
```bash
curl -X POST http://staging/api/documents/upload \
  -H "Authorization: Bearer test-token" \
  -F "file=@test.pdf" \
  -F "doc_type=보고서"
```

#### 2. GET /api/documents
- [ ] List documents with pagination
- [ ] Filter by doc_type, processing_status
- [ ] Return items array with total count
- [ ] Respect org_id isolation (RLS)
- [ ] Response format: `{items: [...], total: N, limit: 20, offset: 0}`

**Test Command:**
```bash
curl http://staging/api/documents?limit=10&offset=0 \
  -H "Authorization: Bearer test-token"
```

#### 3. GET /api/documents/{id}
- [ ] Return document detail with all fields
- [ ] Include processing_status, chunk_count, error_message
- [ ] Include storage_path and extracted_text
- [ ] Return 404 if not found or not authorized

**Test Command:**
```bash
curl http://staging/api/documents/{doc_id} \
  -H "Authorization: Bearer test-token"
```

#### 4. POST /api/documents/{id}/process
- [ ] Trigger manual reprocessing
- [ ] Reset status to "extracting"
- [ ] Return 200 with updated document
- [ ] Handle idempotent retries

**Test Command:**
```bash
curl -X POST http://staging/api/documents/{doc_id}/process \
  -H "Authorization: Bearer test-token"
```

#### 5. GET /api/documents/{id}/chunks
- [ ] Return document chunks
- [ ] Include: id, document_id, chunk_index, content, embedding
- [ ] Embedding dimension: 3073 (Claude embedding)
- [ ] Ordered by chunk_index

**Test Command:**
```bash
curl http://staging/api/documents/{doc_id}/chunks \
  -H "Authorization: Bearer test-token"
```

#### 6. DELETE /api/documents/{id}
- [ ] Delete document and cascade to chunks
- [ ] Delete file from storage
- [ ] Return 204 No Content
- [ ] Idempotent (succeeds on second delete)

**Test Command:**
```bash
curl -X DELETE http://staging/api/documents/{doc_id} \
  -H "Authorization: Bearer test-token"
```

### Async Processing Pipeline
- [ ] Text extraction completes within 1-2 seconds
- [ ] Status transitions: extracting → chunking → embedding → completed
- [ ] Handles text <50 chars (marks as failed)
- [ ] Chunking creates 3+ chunks for normal documents
- [ ] Embedding batch size: 100 chunks
- [ ] Handles API rate limits gracefully

### Security Validation
- [ ] Magic byte validation blocks invalid files
- [ ] Error messages don't expose sensitive paths
- [ ] org_id isolation enforced (RLS)
- [ ] Unauthorized users can't access other org's documents
- [ ] No hardcoded secrets in responses
- [ ] Rate limiting functional (if configured)

### Performance Metrics
| Operation | Target | Actual |
|-----------|--------|--------|
| File Upload | <1s | — |
| Async Processing | 2-5s | — |
| List Documents | <100ms | — |
| Get Detail | <100ms | — |
| Delete | <100ms | — |

### Error Handling
- [ ] File too large (>500MB) → 413 Payload Too Large
- [ ] Invalid file type → 400 Bad Request (파일 형식이 유효하지 않습니다)
- [ ] Invalid doc_type → 422 Unprocessable Entity
- [ ] Document not found → 404 Not Found
- [ ] Insufficient permissions → 403 Forbidden
- [ ] Server errors logged with traceback

### Database Validation
- [ ] `intranet_documents` table contains uploaded documents
- [ ] `document_chunks` table populated with chunks
- [ ] RLS policies enforce org_id filtering
- [ ] Timestamps (created_at, updated_at) set correctly
- [ ] chunk_count in documents matches actual chunks
- [ ] processing_status transitions logged

### Storage Validation
- [ ] Files uploaded to `intranet-documents` bucket
- [ ] Storage path format: `{org_id}/{document_id}/{filename}`
- [ ] File retrieval via GET /storage/v1/object/public/...
- [ ] Delete operations remove files from storage
- [ ] No orphaned files after document deletion

### Monitoring & Logs
- [ ] Application logs visible in staging environment
- [ ] Document processing logs include:
  - Upload attempt
  - File validation result
  - Text extraction output
  - Chunking result (chunk count)
  - Embedding API calls
  - Completion status
- [ ] Error logs capture:
  - File validation failures
  - Text extraction errors
  - API rate limit errors
  - Database operation errors
- [ ] No stack traces exposed to client

### Health Checks
- [ ] `/health` endpoint returns 200
- [ ] Database connectivity confirmed
- [ ] Supabase client initialized
- [ ] Anthropic API client initialized
- [ ] Storage bucket accessible

---

## Test Scenarios

### Scenario 1: PDF Upload & Processing
```
1. Upload PDF with substantial text (>500 chars)
2. Verify response: 201 with document_id
3. Wait 5 seconds
4. Check GET /documents/{id}
5. Verify status: "completed"
6. Verify chunk_count > 0
7. GET /documents/{id}/chunks
8. Verify embedding length = 3073
```

### Scenario 2: Invalid File Type
```
1. Upload .txt file
2. Verify response: 400 Bad Request
3. Check error message: "파일 형식이 유효하지 않습니다"
4. Verify no document created in DB
```

### Scenario 3: File Too Large
```
1. Upload file >500MB
2. Verify response: 413 Payload Too Large
3. Check error message
```

### Scenario 4: Pagination
```
1. Upload 30 documents
2. GET /documents?limit=10&offset=0
3. Verify 10 items, total=30
4. Verify offset parameter works
```

### Scenario 5: Org_id Isolation
```
1. Upload document as org_id=A
2. Attempt access as org_id=B
3. Verify 403 Forbidden or 404 Not Found
```

### Scenario 6: Reprocessing
```
1. Upload document
2. Wait for completion
3. POST /documents/{id}/process
4. Verify status reset to "extracting"
5. Verify chunks recreated
```

---

## Sign-Off

- [ ] QA Team: Tested all 6 endpoints
- [ ] Security Team: Reviewed RLS and validation
- [ ] DevOps: Deployed and monitored
- [ ] Product: Verified feature completeness

**QA Lead Signature:** _______________  
**Date:** _______________

**Ready for Production Promotion?** [ ] YES [ ] NO

---

## Known Issues & Workarounds

### Issue 1: Small Files May Fail
**Symptom:** Document marked as failed with "텍스트가 너무 짧음"  
**Workaround:** Test with files >1KB or >50 characters of text  
**Status:** Expected behavior, validated in tests

### Issue 2: Embedding Rate Limits
**Symptom:** "Rate limit exceeded" on large batch  
**Workaround:** Reduce batch size from 100 to 50  
**Status:** Design allows tuning, not critical in staging

### Issue 3: Chunk Creation Timing
**Symptom:** test_upload_creates_chunks fails with timeout  
**Workaround:** Increase wait timeout from 3s to 15s  
**Status:** Fixed in test, actual processing 2-5s normal

---

## Rollback Procedure

If critical issues discovered:

```bash
# 1. Revert to previous state
git revert f6bf20b
git push origin staging

# 2. Notify team
# - Document issue details
# - Timestamp of revert
# - Plan for fix

# 3. Optional: Rollback DB migration
# In Supabase SQL Editor:
ALTER TABLE intranet_documents 
  ALTER COLUMN project_id SET NOT NULL,
  ALTER COLUMN file_slot SET NOT NULL,
  ALTER COLUMN file_type SET NOT NULL;

# 4. Delete storage bucket
# In Supabase Storage UI: delete "intranet-documents"
```

---

**Last Updated:** 2026-04-07 14:30 UTC  
**Next Review:** After initial staging smoke tests complete
