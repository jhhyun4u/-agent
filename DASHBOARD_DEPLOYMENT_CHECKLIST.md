# Dashboard KPI Deployment Checklist

**Status**: ✅ READY FOR DEPLOYMENT  
**Date**: 2026-04-21  
**Tests**: 14/14 PASSING  
**Blockers**: NONE

---

## Pre-Deployment Verification

- [x] All 14 unit + integration tests passing
- [x] No CRITICAL/HIGH security issues
- [x] Code review approved (PDCA)
- [x] Cache performance baseline recorded
- [x] API documentation complete
- [x] Database schema migrated
- [x] Environment variables configured

---

## Deployment Steps (Staging → Production)

### Step 1: Staging Deployment (NOW)

```bash
# 1. Verify staging environment
curl -X GET https://staging.api.tenopa.co.kr/health

# 2. Deploy dashboard service
cd /c/project/tenopa\ proposer
git checkout main
git pull origin main

# 3. Apply database migrations
uv run alembic upgrade head

# 4. Start dashboard API
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Smoke test endpoints
curl -X GET http://localhost:8000/api/dashboard/metrics/individual \
  -H "Authorization: Bearer {staging_token}"

# 6. Validate caching (request twice, measure latency)
time curl -X GET http://localhost:8000/api/dashboard/metrics/individual
# Should be <200ms on 2nd call
```

### Step 2: Staging Validation (30 min)

**Check endpoints** (6 critical paths):

1. `GET /api/dashboard/metrics/individual` — Personal KPI
2. `GET /api/dashboard/metrics/team` — Team + positioning
3. `GET /api/dashboard/metrics/department` — Dept comparison
4. `GET /api/dashboard/metrics/executive` — Timeline analysis
5. `GET /api/dashboard/metrics/refresh` — Force cache refresh
6. `GET /api/dashboard/health` — Health check

**Validation script**:
```bash
#!/bin/bash
endpoints=(
  "/api/dashboard/metrics/individual"
  "/api/dashboard/metrics/team"
  "/api/dashboard/metrics/department"
  "/api/dashboard/metrics/executive"
  "/api/dashboard/metrics/refresh"
  "/api/dashboard/health"
)

for ep in "${endpoints[@]}"; do
  echo "Testing $ep..."
  curl -s -w "Status: %{http_code}\n" \
    -H "Authorization: Bearer {token}" \
    https://staging.api.tenopa.co.kr$ep
done
```

### Step 3: Production Deployment (2026-04-22)

**Prerequisites**:
- [ ] Staging validation passed
- [ ] Monitoring alerts configured
- [ ] Rollback procedure tested
- [ ] Team notified (Slack channel #deployments)

**Procedure**:
```bash
# 1. Tag release
git tag -a v4.2.0-dashboard-kpi -m "Dashboard KPI production release"
git push origin v4.2.0-dashboard-kpi

# 2. Deploy to production (via CI/CD)
# GitHub Actions: Dashboard KPI Deploy workflow triggered

# 3. Health check (wait 60s for warm-up)
sleep 60
curl https://api.tenopa.co.kr/health

# 4. Smoke tests against production
pytest tests/smoke/test_dashboard_production.py -v

# 5. Monitor metrics for 1 hour
# Check: error rate (<0.1%), latency (p95 <500ms), cache hit rate (>80%)
```

### Step 4: Monitoring & Rollback

**During first hour**:
- Monitor error logs: `tail -f /var/log/tenopa/dashboard.log`
- Check Grafana dashboard: `https://grafana.tenopa.internal/d/dashboard-kpi`
- Alert rules active:
  - Error rate >1%
  - Response time p95 >1000ms
  - Cache hit rate <50%

**If issues occur**:
```bash
# Immediate rollback (fast)
git revert {commit-hash}
git push origin main
# CI/CD auto-deploys previous version within 2 min
```

---

## Rollback Plan

**Trigger**: Any of these conditions
- Error rate >2%
- Response latency p95 >1500ms for >5 min
- Data corruption detected in metrics

**Steps**:
1. Post alert to #incidents channel
2. Run: `git revert HEAD --no-edit && git push origin main`
3. Wait for CD pipeline (2-3 min deployment)
4. Verify health: `curl https://api.tenopa.co.kr/health`
5. Notify stakeholders: "@team Dashboard rolled back to v4.1.0"

---

## Post-Deployment (First 24 Hours)

**Observability**:
- [ ] Error rate stable (<0.1%)
- [ ] Cache hit rate >80%
- [ ] API latency p95 <500ms
- [ ] No critical logs detected

**Success Criteria**:
- ✅ All 14 tests passing in production
- ✅ Dashboard loads <1s for all user types
- ✅ Zero security incidents
- ✅ Data consistency verified

**Sign-off**: @product-manager + @devops

---

## Contacts

- **On-call**: @devops-team (Slack)
- **Product**: @pm-dashboard
- **Security**: @security-team

**Deployment window**: 2026-04-22 10:00-11:00 UTC

