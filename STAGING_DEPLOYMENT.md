# Document Ingestion - Staging Deployment Checklist

**Date**: 2026-04-07  
**Status**: Ready for Staging  
**Target**: Get feature working in staging environment

---

## Pre-Deployment Checklist

- [x] Code implemented (6 endpoints)
- [x] Schema migration created (018)
- [x] Security validations added (magic bytes)
- [x] Type hints improved (Pydantic Literal types)
- [x] Documentation created
- [ ] Migration 018 applied to production DB ← **MUST BE DONE**
- [ ] File upload smoke test passes ← **WILL DO NOW**
- [ ] Deployment plan prepared ← **THIS FILE**

---

## Deployment Steps

### Phase 1: Verify Local Works (NOW)
- [x] Migration 018 applied to Supabase
- [x] Smoke test: File upload successful
- [x] Smoke test: Document record created
- [ ] Next: Async processing verification

### Phase 2: Deploy to Staging (IN 30 MIN)
- [ ] Push changes to Git (main branch or staging branch)
- [ ] Verify CI/CD passes
- [ ] Staging environment updates automatically (if using Vercel/Railway)
- [ ] Test endpoints in staging

### Phase 3: Staging Validation (IN 1 HOUR)
- [ ] Test all 6 endpoints
- [ ] Upload various file types (PDF, DOCX, HWP)
- [ ] Verify storage in Supabase
- [ ] Verify chunks created
- [ ] Check processing status transitions

### Phase 4: Production Deployment (NEXT DAY)
- [ ] Create PR from staging → main (if needed)
- [ ] Final QA sign-off
- [ ] Deploy to production
- [ ] Monitor for errors

---

## Current Test Results

### ✅ Smoke Test: File Upload
```
Status: 201 Created
Document ID: [generated UUID]
Processing Status: extracting
```

**What this means**:
- ✅ API endpoint works
- ✅ File stored in Supabase Storage
- ✅ Database record created
- ✅ Async processing triggered

### ⏳ Pending: Async Processing Completion
- Status: "extracting" → should become "chunking" → "embedding" → "completed"
- Timeline: Depends on file size (small PDF: <30 sec)
- Check: `curl http://localhost:8000/api/documents/{id}`

---

## Deployment Commands

### Step 1: Commit & Push
```bash
cd /c/project/tenopa\ proposer/-agent-master

# Stage changes
git add app/api/routes_documents.py app/models/document_schemas.py

# Commit
git commit -m "feat: Add document ingestion API endpoints

- POST /api/documents/upload: File upload + async processing
- GET /api/documents: List with filters
- GET /api/documents/{id}: Detail view
- POST /api/documents/{id}/process: Manual retry
- GET /api/documents/{id}/chunks: Chunk listing
- DELETE /api/documents/{id}: Delete document

Security:
- Magic byte validation (file signature checking)
- org_id isolation (RLS enforced)
- File size limits (500MB max)

Type Safety:
- Literal types for doc_type and processing_status
- Pydantic validation on all inputs
- Comprehensive error handling"

# Push to staging branch
git push origin staging

# OR push to main if CI/CD handles it
git push origin main
```

### Step 2: Verify Deployment
```bash
# Check staging API
curl https://staging.tenopa.ai/api/documents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return: 200 OK with document list
```

---

## Success Criteria for Staging

✅ **API Endpoints Work**
- POST /upload returns 201
- GET /documents returns 200
- GET /documents/{id} returns 200
- POST /documents/{id}/process returns 200
- GET /documents/{id}/chunks returns 200
- DELETE /documents/{id} returns 204

✅ **File Processing Works**
- Upload PDF → File stored in Supabase
- Processing status transitions correctly
- Chunks created in database
- Embeddings generated

✅ **Security Works**
- Magic bytes reject invalid files
- RLS prevents cross-org access
- File size limits enforced

---

## Rollback Plan

If staging has issues:

```bash
# Option 1: Revert last commit
git revert HEAD
git push origin staging

# Option 2: Rollback database migration
# (Run in Supabase SQL Editor)
-- Undo migration 018 (restore NOT NULL constraints)
-- See database/migrations/018_document_ingestion_fixes.sql for reverse

# Option 3: Disable feature flag (if using)
# Set DOCUMENT_INGESTION_ENABLED=false in .env
```

---

## Monitoring in Staging

### Logs to Watch
```bash
# FastAPI logs
tail -f app.log | grep document

# Supabase activity
# Dashboard → Logs → Edge Functions → document_ingestion

# Embedding API usage
# Dashboard → Usage → Claude API credits
```

### Metrics to Track
- Document upload success rate
- Average processing time (target: <30 sec for small PDFs)
- Chunk count per document
- Embedding generation success rate

---

## Post-Deployment Steps

### If Staging ✅ Passes:
1. Schedule production deployment
2. Notify stakeholders
3. Prepare frontend team (API is ready to consume)
4. Monitor production for first 24 hours

### If Staging ❌ Fails:
1. Check logs in Supabase
2. Check async task logs
3. Identify issue (file parsing? embedding API? storage?)
4. Fix in code or configuration
5. Redeploy to staging
6. Re-test

---

## Estimated Timeline

| Phase | Time | Status |
|-------|------|--------|
| Migration 018 | 5 min | ✅ DONE |
| Smoke test | 5 min | ✅ DONE |
| Git commit + push | 5 min | ⏳ TODO |
| CI/CD build | 5-10 min | ⏳ TODO |
| Staging tests | 10 min | ⏳ TODO |
| Production deployment | 5 min | ⏳ LATER |
| **TOTAL** | **30-40 min** | |

---

## Contacts & Resources

**Supabase**:
- Dashboard: https://app.supabase.com/project/inuuyaxddgbxexljfykg
- Status: https://status.supabase.com

**Claude API**:
- Status: https://status.anthropic.com
- Docs: https://docs.anthropic.com

**Deployment**:
- GitHub: https://github.com/your-org/tenopa-proposer
- CI/CD: (Check your pipeline configuration)

---

## Questions?

See `IMPLEMENTATION_CHECKLIST.md` for more details on each step.
