# Production Smoke Test Checklist

**Date:** 2026-04-07 (16:25 UTC+9)  
**Status:** Ready to Execute  
**Backend:** ✅ All 322 tests passing

---

## Pre-Test Verification

- [ ] Backend deployed to production
- [ ] All environment variables set correctly
- [ ] Database migrations applied
- [ ] API health check: `GET /health`
- [ ] Recent commits on main: `deaa8e9`, `6f60953`, `46ac7bf`

---

## Core API Tests (Phase 1)

### 1. Authentication & Users
```bash
# Test Azure AD SSO
curl -X POST https://api.example.com/api/auth/login \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"

# Get current user
curl https://api.example.com/api/users/me \
  -H "Authorization: Bearer {token}"
```

### 2. Proposal Management
```bash
# List proposals
curl https://api.example.com/api/proposals \
  -H "Authorization: Bearer {token}"

# Create proposal
curl -X POST https://api.example.com/api/proposals \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","agency":"TEST","budget":1000000}'
```

### 3. Workflow (Graph)
```bash
# Start workflow
curl -X POST https://api.example.com/api/proposals/{id}/workflow/start \
  -H "Authorization: Bearer {token}"

# Get workflow state
curl https://api.example.com/api/proposals/{id}/workflow/state \
  -H "Authorization: Bearer {token}"
```

### 4. Bid Recommendation (NEW - My Fix)
```bash
# Test bid analysis
curl -X POST https://api.example.com/api/bids/analyze \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "bids": [{
      "bid_no": "2026-TEST-001",
      "bid_title": "Test Bid",
      "content_text": "Test content"
    }],
    "team_profile": {"specialties": ["AI"]}
  }'
```

---

## Critical Path Tests (Phase 2)

### Artifact Versioning (Phase 1)
```bash
# Get artifact versions
curl https://api.example.com/api/proposals/{id}/artifacts/versions \
  -H "Authorization: Bearer {token}"
```

### Document Ingestion (Phase 2)
```bash
# Upload RFP document
curl -X POST https://api.example.com/api/proposals/{id}/documents \
  -H "Authorization: Bearer {token}" \
  -F "file=@proposal.pdf"
```

---

## Success Criteria

✅ All endpoints return 2xx responses  
✅ Auth tokens validate correctly  
✅ Database queries execute without errors  
✅ No 5xx server errors in logs  
✅ Response times < 2 seconds (median)  
✅ Bid recommendation analysis completes  

---

## Monitoring

### Logs to Check
```bash
# Backend logs (Render/Railway)
tail -f logs/production.log

# Database connections
SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;

# Error rates (Sentry)
https://sentry.io/organizations/{org}/issues/
```

### Key Metrics
- Request latency (p95 < 1s)
- Error rate (< 0.1%)
- Database connection pool (< 80% usage)
- Cache hit rate (> 90%)

---

## Rollback Plan

If smoke tests fail:
1. Check recent deployments
2. Review error logs (Sentry/Application logs)
3. Rollback to previous stable version if critical
4. Fix and re-deploy

---

## Sign-Off

- [ ] Smoke tests completed
- [ ] All critical paths verified
- [ ] Logs reviewed, no errors
- [ ] Performance acceptable
- [ ] Ready for broader testing

**Approved by:** _______________  
**Date:** _______________

