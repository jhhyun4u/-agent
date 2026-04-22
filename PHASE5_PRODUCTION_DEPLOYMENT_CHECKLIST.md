# Phase 5 Scheduler Integration — Production Deployment Checklist

**Deployment Date:** 2026-04-25 10:00 UTC  
**Expected Duration:** 2 hours  
**Risk Level:** MEDIUM (staging health endpoint 404 issue pending resolution)

---

## 📋 Pre-Deployment (2026-04-22 ~ 2026-04-24)

### 1. Staging Issue Resolution ⚠️
- [ ] Investigate scheduler health endpoint 404 error on staging
  - Last failure: 2026-04-21 22:23:14 UTC
  - Error count: 373
  - Root cause: Potential version mismatch or router registration issue
- [ ] Verify scheduler_router registration in latest main.py
- [ ] Test `/api/scheduler/health` endpoint manually
- [ ] Confirm all 24 scheduler tests passing locally
- [ ] Re-deploy staging and verify health endpoint
- [ ] Capture 1 hour clean monitoring data from staging

### 2. Production Environment Validation
- [ ] Database connection to production (Railway/Render)
- [ ] Supabase service status check
- [ ] Azure AD/Entra ID service availability
- [ ] API endpoint reachability from prod network
- [ ] TLS certificate validity (>30 days)
- [ ] DNS resolution for app domain

### 3. Code Quality Gate
- [ ] All 24 unit tests passing: `pytest tests/test_scheduler_integration.py -v`
- [ ] Integration tests passing: `pytest tests/integration/ -k scheduler`
- [ ] Code review completed (0 critical/high issues)
- [ ] Security scan with bandit: `bandit -r app/services/scheduler*`
- [ ] No hardcoded secrets/credentials in code
- [ ] Git log clean (no merge conflicts)

### 4. Database Preparation
- [ ] Production database backup created
  ```bash
  # Backup command (example)
  pg_dump -h [prod_host] -U [user] --format custom -f backup_2026-04-25.bak
  ```
- [ ] Migration script tested on staging first
  - Script: `database/migrations/006_scheduler_integration.sql`
  - Tables: migration_schedules, migration_batches, migration_logs
  - Indices: 8 performance indices
- [ ] Rollback plan documented
- [ ] Data validation queries prepared

### 5. Documentation & Communication
- [ ] Deployment runbook prepared (step-by-step checklist)
- [ ] Rollback procedure documented
- [ ] Monitoring dashboard URL shared with team
- [ ] Slack notification template prepared (#tenopa-deployment)
- [ ] On-call engineer assigned

---

## 🚀 Deployment Execution (2026-04-25)

### Phase 1: Pre-Deployment Checks (09:30 - 10:00 UTC)
```
Start: 09:30 UTC
[ ] 1. Final health check
      - Database: SELECT 1; → OK
      - API: GET /health → 200 OK
      - Auth: Azure AD token generation → OK
      - Supabase: SELECT * FROM public.proposals LIMIT 1 → OK
      
[ ] 2. Alert stakeholders
      - Post to #tenopa-deployment: "Deployment starting in 30 minutes"
      - Notify on-call: deployment window 10:00-12:00 UTC
      
[ ] 3. Prepare rollback
      - Tag current version: git tag production-$(date +%Y%m%d-%H%M%S)
      - Note: rollback branch = previous successful deploy commit
      
Completion: 10:00 UTC
```

### Phase 2: Migration & Code Deployment (10:00 - 11:00 UTC)
```
Start: 10:00 UTC

[ ] 1. Execute database migration
      - Run: database/migrations/006_scheduler_integration.sql
      - Verify: SELECT COUNT(*) FROM migration_schedules;
      - Expected: 0 rows (fresh tables)
      - Check indices: 8 created successfully
      
[ ] 2. Deploy application code
      - Option A: Railway/Render auto-deploy (if using CD)
        - Push to main: git push origin main
        - Monitor deployment logs in provider dashboard
        
      - Option B: Manual deployment
        - SSH to prod server
        - Pull latest code: git pull origin main
        - Install deps: uv sync
        - Restart service: systemctl restart tenopa-api
        
[ ] 3. Verify deployment
      - Check app version: GET /api/version
      - Check scheduler routes: GET /api/scheduler/health
      - Check health: GET /health
      - All should return 200 OK
      
[ ] 4. Run smoke tests
      - pytest tests/test_scheduler_integration.py -v
      - pytest tests/integration/test_jobs_api.py -v
      
Completion: 11:00 UTC
```

### Phase 3: Post-Deployment Monitoring (11:00 - 14:00 UTC)
```
Start: 11:00 UTC - 3 hour continuous monitoring

[ ] 1. Real-time monitoring (every 5 minutes)
      Metrics to track:
      - Error rate: < 1% (target: < 0.5%)
      - API latency: p95 < 1000ms (target: < 500ms)
      - Scheduler health: status = "ok"
      - Database connections: < 10 active
      - Memory usage: < 500MB
      - CPU usage: < 60%
      
      Tools:
      - Prometheus: http://[prod_monitoring]/prometheus
      - Grafana: http://[prod_monitoring]/grafana
      - Log aggregation: check error logs in CloudWatch/ELK
      
[ ] 2. Functional testing
      - Create schedule via API: POST /api/scheduler/schedules
      - Trigger migration: POST /api/scheduler/schedules/{id}/trigger
      - Check batch status: GET /api/scheduler/batches/{batch_id}
      - Verify documents migrated to DB
      
[ ] 3. Database validation
      - Check migration_schedules table: rows match config
      - Check migration_batches table: status updates working
      - Check migration_logs table: logging operational
      - Verify no RLS policy violations
      
[ ] 4. Error log analysis
      - Grep prod logs for ERROR, CRITICAL
      - Check for any authentication failures
      - Verify no database timeout errors
      
[ ] 5. Gradual traffic ramp (if applicable)
      - If using feature flags: incrementally enable scheduler
      - Monitor metrics at 25%, 50%, 75%, 100% traffic
      
Completion: 14:00 UTC
```

### Phase 4: Sign-Off (14:00+ UTC)
```
[ ] 1. Post-deployment report
      - Deployment duration: [actual time]
      - Errors encountered: 0
      - Rollbacks: 0
      - P95 latency: [value]ms
      - Error rate: [value]%
      
[ ] 2. Team notification
      - Slack: ✅ Phase 5 Scheduler successfully deployed to production
      - Update status page: Production - Operational
      
[ ] 3. Archive logs
      - Save deployment logs: logs/deployment-2026-04-25.log
      - Save monitoring data: monitoring/phase5-prod-2026-04-25.jsonl
```

---

## 🔄 Rollback Plan (If Deployment Fails)

**Automatic Rollback Trigger:**
- Error rate > 5% for > 5 minutes
- API latency p95 > 3000ms for > 5 minutes
- Scheduler health endpoint returns 404 for > 2 minutes
- Database connection errors > 10 in 1 minute

**Manual Rollback Procedure:**
```bash
# 1. Immediately notify #tenopa-deployment
# 2. Stop new traffic (feature flag or load balancer)
# 3. Revert code to previous stable version
git checkout [previous-stable-commit]
git push -f origin main

# 4. If DB schema rollback needed
# Restore from backup:
pg_restore -h [prod_host] -U [user] -d [database] backup_2026-04-25.bak

# 5. Restart service
systemctl restart tenopa-api

# 6. Verify health
# GET /api/scheduler/health should return {"status": "ok", ...}

# 7. Document incident
# Create incident report in docs/incidents/rollback-2026-04-25.md
```

---

## 📊 Success Criteria

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Deployment time | < 2 hours | | |
| Error rate (post-deploy) | < 0.5% | | |
| API latency p95 | < 500ms | | |
| Scheduler health | OK | | |
| All tests passing | 24/24 | | |
| Zero critical logs | 0 | | |
| Data integrity | 100% | | |

---

## 📝 Notes & References

- **Monitoring Dashboard:** [Link to Grafana]
- **Runbook:** [Link to runbook]
- **Incident Response:** [Link to IR guide]
- **Rollback History:** [Link to previous rollbacks]
- **Phase 5 Docs:** docs/operations/phase5-*

---

**Last Updated:** 2026-04-22 (Pre-deployment preparation)  
**Next Review:** 2026-04-25 09:00 UTC (2 hours before deployment)
