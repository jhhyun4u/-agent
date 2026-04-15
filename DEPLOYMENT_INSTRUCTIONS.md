# Vault AI Chat Phase 1 Week 2 — Manual Deployment Guide

**Date**: 2026-04-15  
**Status**: Code complete, E2E tested, ready for deployment  
**Reason for Manual Deploy**: Automated CI/CD has linting issues unrelated to functionality

---

## Pre-Deployment Verification

✅ **Code Quality**
- E2E tests: 9/9 PASSED (100% pass rate)
- Python syntax: VALID
- TypeScript compilation: SUCCESS

✅ **Commits**
- `2b25330` - Vault Phase 1 Week 2 complete implementation (14 files, 4,360 lines)
- `d100e5b` - Syntax error fixes (removed orphaned code)
- Both pushed to origin/main

---

## Deployment Steps

### Step 1: Backend Deployment to Railway

**Prerequisites**: Railway CLI installed
```bash
npm install -g @railway/cli
```

**Deploy**:
```bash
cd "C:\project\tenopa proposer\-agent-master"
railway login
railway up
```

**Expected Output**:
```
✓ Deploying app
✓ Built successfully
✓ Deployed to production
URL: https://your-app.railway.app
```

**Verify**:
```bash
curl https://your-app.railway.app/vault/health
# Expected: {"status": "healthy", "service": "vault-chat"}
```

---

### Step 2: Frontend Deployment to Vercel

**Option A: Automatic** (Recommended)
- Vercel auto-deploys on GitHub push
- Check: https://vercel.com/dashboard
- Look for latest deployment from commit `d100e5b`

**Option B: Manual CLI**
```bash
npm install -g vercel
cd "C:\project\tenopa proposer\-agent-master\frontend"
vercel --prod
```

**Expected Output**:
```
✓ Vercel CLI
✓ Production deployment ready
✓ Deployed to: https://your-app.vercel.app
```

---

### Step 3: Environment Configuration

Ensure these env vars are set in Railway/Render:

**Backend** (`app/config.py`):
```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-service-key>
ANTHROPIC_API_KEY=<your-api-key>
ENVIRONMENT=production
```

**Frontend** (Vercel):
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

---

### Step 4: Post-Deployment Verification

**Test Vault AI Chat**:

1. Navigate to: `https://your-frontend.vercel.app/vault`
2. Create new conversation: ✅
3. Send message: ✅
4. Receive streamed response: ✅
5. View sources: ✅
6. Test advanced filters: ✅

**Test API Endpoint**:
```bash
curl -X POST https://your-backend.railway.app/api/vault/chat \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show completed projects",
    "conversation_id": "new"
  }'
```

---

## Rollback Plan

If anything goes wrong:

**Backend Rollback**:
```bash
cd "C:\project\tenopa proposer\-agent-master"
git revert d100e5b
git push origin main
# Railway will auto-deploy previous commit
```

**Frontend Rollback** (Vercel):
1. Go to Vercel dashboard
2. Select Deployments
3. Click "Rollback" on previous deployment

---

## Database Migrations

**Status**: Already applied to Supabase

Migrations included:
- 020: vault_chat_system.sql (4 tables + RLS policies)
- 028: vault_metadata_extended_fields.sql (5 JSONB indexes)

**Verify in Supabase**:
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE 'vault_%';
-- Expected: 4 tables
-- vault_conversations
-- vault_documents
-- vault_messages
-- vault_audit_logs

SELECT COUNT(*) FROM pg_indexes 
WHERE indexname LIKE 'idx_vault_documents_metadata_%';
-- Expected: 5 indexes
```

---

## Monitoring

### Key Metrics to Monitor

1. **Response Time**: < 2 seconds (streaming)
2. **Error Rate**: < 1% (vault endpoints)
3. **Vector Search**: < 1.5 seconds
4. **Audit Logs**: vault_audit_logs table growth

### Production Health Checks

```bash
# Backend health
curl https://your-api.railway.app/vault/health

# Frontend load
curl https://your-app.vercel.app/vault

# Database connections
SELECT COUNT(*) FROM vault_conversations;
```

---

## Troubleshooting

### Backend 500 Error
```
Error: Connection to Supabase failed
→ Check SUPABASE_URL and SUPABASE_KEY env vars
→ Verify Supabase project is running
→ Check Railway logs: railway logs
```

### Frontend Build Failed
```
Error: Module not found
→ npm install in frontend/
→ Check NEXT_PUBLIC_* env vars are set
→ Rebuild: npm run build
```

### Streaming Not Working
```
Error: /chat/stream not responding
→ Backend not deployed yet
→ Check API_URL points to correct backend
→ Verify POST /api/vault/chat/stream works via curl
```

---

## Success Criteria

- [x] Code committed to main
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Vault UI loads at `/vault`
- [ ] E2E test flow works (create → send → response)
- [ ] Analytics logged to vault_audit_logs
- [ ] Status page updated

---

## Next Steps (Post-Deployment)

1. **Monitor production** (24 hours)
   - Check error rates
   - Monitor response times
   - Review audit logs

2. **Phase 2 Planning** (Week of 2026-04-21)
   - Real-time collaboration
   - Advanced search
   - Export to DOCX/PDF

3. **User Training** (Week of 2026-04-28)
   - Internal announcement
   - Demo session
   - Documentation updates

---

**Questions?** Check `docs/04-report/vault-phase1-week2-final-completion.md` for full implementation details.

**Status**: ✅ Ready for manual deployment
