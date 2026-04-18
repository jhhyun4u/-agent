# Document Ingestion — Staging Deployment Plan (2026-04-20)

**Target Date**: 2026-04-20 (Friday)  
**Environment**: Staging  
**Duration**: ~30 minutes  
**Risk Level**: LOW

---

## Pre-Deployment Checklist (2026-04-19)

- [ ] Verify all changes committed to main branch
- [ ] Run final test suite: `pytest tests/test_document_ingestion.py -v`
- [ ] Verify no uncommitted changes: `git status`
- [ ] Confirm staging database backups are current
- [ ] Notify team of deployment window
- [ ] Prepare rollback plan (git commit hash: current main)

---

## Deployment Steps (2026-04-20, 09:00-09:30)

### Step 1: Pre-Deployment Verification (5 mins)
```bash
# Verify deployment readiness
git log --oneline -1  # Should show latest commit
python -c "from app.models.document_schemas import *; print('Schemas OK')"
pytest tests/test_document_ingestion.py::test_upload_document -v  # Quick smoke test
```

### Step 2: Deploy Code to Staging (5 mins)
```bash
# Pull latest code
git pull origin main

# Install dependencies
uv sync

# Deploy to staging environment
./scripts/deploy-staging.sh
# OR manually:
# - Build Docker image: docker build -t tenopa-api:latest .
# - Push to staging registry
# - Update staging deployment (K8s/VM)
```

### Step 3: Database Verification (5 mins)
```bash
# Verify database connection
curl https://staging-api.tenopa.co.kr/health

# Verify tables exist
psql $STAGING_DB_URL -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'intranet_%' OR tablename = 'document_chunks';"

# Verify RLS policies are in place
psql $STAGING_DB_URL -c "SELECT policyname FROM pg_policies WHERE tablename = 'intranet_documents';"
```

### Step 4: API Smoke Tests (10 mins)
```bash
# Test document upload endpoint
curl -X POST https://staging-api.tenopa.co.kr/api/documents/upload \
  -F "file=@test-document.pdf" \
  -F "doc_type=보고서" \
  -H "Authorization: Bearer $STAGING_AUTH_TOKEN"

# Test document list endpoint
curl https://staging-api.tenopa.co.kr/api/documents \
  -H "Authorization: Bearer $STAGING_AUTH_TOKEN"

# Test chunks endpoint
curl "https://staging-api.tenopa.co.kr/api/documents/{document_id}/chunks?limit=5" \
  -H "Authorization: Bearer $STAGING_AUTH_TOKEN"
```

### Step 5: Validation (5 mins)
- [ ] API responding with 200/201 status codes
- [ ] No 5xx errors in logs
- [ ] Document processing starting (check intranet_documents.processing_status)
- [ ] No database connectivity issues
- [ ] Authentication/authorization working

---

## Post-Deployment Monitoring (30-60 mins)

### Real-Time Checks
- Monitor API response times: target <500ms
- Monitor error rate: target <1%
- Check database query performance
- Monitor Supabase Storage integration

### Logs to Watch
- `app/api/routes_documents.py` — No ERROR/CRITICAL logs
- `app/services/document_ingestion.py` — Processing jobs completing
- Supabase logs — No authentication failures

### Expected Behavior
✅ Document upload returns 201 with document ID  
✅ Documents transition from "extracting" → "chunking" → "embedding" → "completed"  
✅ Chunks stored in `document_chunks` table with embeddings  
✅ All requests properly org-isolated (RLS working)  

---

## Rollback Plan (If Issues Found)

### Immediate Rollback
```bash
# Revert to previous version
git revert HEAD
git push origin main

# Redeploy staging with previous code
./scripts/deploy-staging.sh
```

### Database Rollback (If needed)
```bash
# No database schema changes, so no migration rollback needed
# Just verify old data is intact
psql $STAGING_DB_URL -c "SELECT COUNT(*) FROM intranet_documents;"
```

---

## Success Criteria

| Criterion | Target | Method |
|-----------|--------|--------|
| API Health | 200 OK | `curl /health` |
| Document Upload | <5s | POST /api/documents/upload |
| Document List | <2s | GET /api/documents |
| Chunks Retrieval | <2s | GET /api/documents/{id}/chunks |
| Error Rate | <1% | Monitor logs |
| RLS Isolation | 100% | Test cross-org access (should fail) |

---

## Team Communication

**Pre-Deployment (2026-04-19 EOD)**
```
Slack: @team Document Ingestion staging deployment scheduled for 2026-04-20 09:00-09:30.
Window: ~30 minutes. No user impact (staging only).
```

**During Deployment (2026-04-20 09:00-09:30)**
```
Slack #deployment: [STAGING] Deploying document_ingestion... ETA 09:30
```

**Post-Deployment (2026-04-20 09:30)**
```
Slack #deployment: [STAGING] Document Ingestion deployed successfully. All checks passed.
Ready for production deployment on 2026-04-25.
```

---

## Sign-Off

| Role | Name | Sign-Off |
|------|------|----------|
| DevOps Lead | - | ☐ |
| QA Lead | - | ☐ |
| Tech Lead | - | ☐ |

**Deployment Status:** ✅ READY FOR STAGING

---

**Prepared**: 2026-04-18  
**Scheduled**: 2026-04-20 09:00-09:30 UTC  
**Environment**: Staging
