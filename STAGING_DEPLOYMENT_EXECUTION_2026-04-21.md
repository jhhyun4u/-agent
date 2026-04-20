# Phase 5 Staging Deployment Execution Guide
**Date:** 2026-04-21  
**Status:** READY FOR EXECUTION  
**Target:** Staging Environment  

---

## Pre-Deployment (NOW)

### 1. Code Quality Verification ✓
```
CRITICAL issues: 3/3 RESOLVED
MEDIUM issues: 6/6 RESOLVED
Code Review: PASSED
```

### 2. Git Status Check
```bash
git status                    # Verify all changes committed
git log --oneline -5         # Confirm recent commits
git branch -v                # On main branch
```

Expected output:
```
commit 0cf956b fix: resolve 6 MEDIUM code quality issues
commit 138dcf3 fix: resolve 3 critical code quality issues
On branch main
```

### 3. Test Verification
```bash
pytest tests/test_scheduler_integration.py -v    # 24 tests PASS
pytest tests/unit/test_accuracy_enhancement.py -v # All tests PASS
```

---

## Staging Deployment Timeline

### PHASE 1: Database Migration (2026-04-21 09:00-09:30 UTC)

#### Option A: Supabase SQL Editor (Recommended)
1. Open Supabase Dashboard: https://app.supabase.com
2. Go to Project > SQL Editor
3. Click "New Query"
4. Copy entire contents of: `database/migrations/006_scheduler_integration.sql`
5. Paste into SQL editor
6. Click "RUN"
7. Verify output: "command completed successfully" (no errors)

#### Option B: Command Line
```bash
psql -h [SUPABASE_HOST] -U [USER] -d [DATABASE] \
  -f database/migrations/006_scheduler_integration.sql
```

#### Verification Query (Execute after migration)
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'migration%'
ORDER BY table_name;
```

Expected result:
```
migration_batches
migration_schedule
migration_status_logs
```

### PHASE 2: Code Deployment (2026-04-21 09:30-10:00 UTC)

#### Railway Auto-Deploy (Triggered on git push)
```bash
# Verify code is on main branch
git branch

# Show recent commits
git log --oneline -3

# Code will auto-deploy via Railway webhook
# Watch deployment progress in Railway Dashboard:
# https://railway.app/project/[PROJECT_ID]
```

#### Deployment Steps (Automatic)
1. Git push triggers Railway webhook
2. Build starts (dependencies install: `uv sync`)
3. Environment variables loaded from Railway
4. Health check: GET /api/health -> 200 OK
5. Deployment status: SUCCESS or ROLLBACK on failure

**Expected Duration:** 15-20 minutes

### PHASE 3: Smoke Tests (2026-04-21 10:00-10:15 UTC)

#### Health Check
```bash
curl -X GET https://staging-api.railway.app/api/health \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Expected: 200 OK
# Body: {"status": "healthy", ...}
```

#### Scheduler Endpoints Check
```bash
# Get schedules
curl -X GET https://staging-api.railway.app/api/scheduler/schedules \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Expected: 200 OK
# Body: {"data": [{"id": "...", "schedule_name": "...", ...}]}

# Create schedule
curl -X POST https://staging-api.railway.app/api/scheduler/schedules \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Schedule",
    "cron_expression": "0 0 * * *",
    "source_type": "intranet",
    "enabled": true
  }'

# Expected: 201 Created
```

#### Permission Check
```bash
# Non-admin access should return 403
curl -X GET https://staging-api.railway.app/api/scheduler/schedules \
  -H "Authorization: Bearer $STAGING_USER_TOKEN"

# Expected: 403 Forbidden
```

### PHASE 4: Integration Tests (2026-04-21 10:15-10:45 UTC)

#### Test Manual Batch Trigger
```bash
# Replace SCHEDULE_ID with actual value from Phase 3
SCHEDULE_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST https://staging-api.railway.app/api/scheduler/schedules/$SCHEDULE_ID/trigger \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Expected: 200 OK
# Body: {"batch_id": "...", "message": "Migration triggered"}
```

#### Check Batch Status
```bash
# Replace BATCH_ID with response from trigger
BATCH_ID="770a0502-f41d-53f6-c938-668877662222"

curl -X GET https://staging-api.railway.app/api/scheduler/batches/$BATCH_ID \
  -H "Authorization: Bearer $STAGING_ADMIN_TOKEN"

# Expected: 200 OK
# Body: {"id": "...", "status": "completed", ...}
```

### PHASE 5: Performance Baseline (2026-04-21 10:45-11:00 UTC)

#### Response Time Measurement
```bash
# Test each endpoint 10 times and measure response time

# GET /schedules
for i in {1..10}; do
  time curl -s https://staging-api.railway.app/api/scheduler/schedules \
    -H "Authorization: Bearer $STAGING_ADMIN_TOKEN" > /dev/null
done

# POST /schedules (if you want to create another schedule)
# GET /batches/{id}
# All p95 should be: <200ms, <500ms, <1000ms respectively
```

---

## 24-Hour Monitoring Period (2026-04-21 11:00 ~ 2026-04-22 11:00)

### Hourly Checks
- API response times (p95, p99)
- Error rate (5xx, 4xx)
- Database connection health
- Scheduler job completion status

### Daily Summary (Next morning)
- Batch success/failure count
- Average response times
- Any anomalies or warnings
- Resource utilization (CPU, memory)

### Alert Thresholds
- p95 response > 1000ms → WARNING
- Error rate > 1% → CRITICAL
- Memory > 400MB → WARNING
- Scheduler job failure → CRITICAL

---

## Rollback Procedure (If Issues Found)

### Immediate Rollback
```bash
# 1. Revert to previous commit
git revert HEAD

# 2. Push to trigger new deployment
git push origin main

# 3. Drop migration (Supabase SQL Editor)
DROP TABLE IF EXISTS migration_status_logs CASCADE;
DROP TABLE IF EXISTS migration_batches CASCADE;
DROP TABLE IF EXISTS migration_schedule CASCADE;

# 4. Remove scheduler from app (edit main.py line 262-271)
# Comment out Phase 5 scheduler initialization
```

---

## Success Criteria

- [ ] Database migration applied successfully
- [ ] 3 tables created (migration_schedule, migration_batches, migration_status_logs)
- [ ] 5 indices created
- [ ] All smoke tests pass (200 OK on health check + scheduler endpoints)
- [ ] Integration test (manual trigger) succeeds
- [ ] Performance baselines established (p95 < targets)
- [ ] 24-hour monitoring period completes without critical errors
- [ ] No significant warnings in logs

---

## Timeline Summary

| Phase | Time Window | Duration | Owner |
|-------|-------------|----------|-------|
| Pre-Deployment | 2026-04-21 08:00 | 1 hour | Engineer |
| Database Migration | 2026-04-21 09:00-09:30 | 30 min | DBA/Engineer |
| Code Deployment | 2026-04-21 09:30-10:00 | 30 min | CI/CD Pipeline |
| Smoke Tests | 2026-04-21 10:00-10:15 | 15 min | QA/Engineer |
| Integration Tests | 2026-04-21 10:15-10:45 | 30 min | QA/Engineer |
| Performance Baseline | 2026-04-21 10:45-11:00 | 15 min | Performance Team |
| **24-Hour Monitoring** | **2026-04-21 11:00 ~ 2026-04-22 11:00** | **24 hours** | **On-Call** |
| Final Validation | 2026-04-23 ~ 2026-04-24 | 2 days | Tech Lead |
| **Production Deploy Decision** | **2026-04-25** | - | **Go/No-Go Meeting** |

---

## Success Scenario (Expected)

```
2026-04-21 09:00 UTC: Pre-deployment checks pass
2026-04-21 09:15 UTC: Database migration succeeds (3 tables, 5 indices)
2026-04-21 09:45 UTC: Code deployed to staging (Railway auto-deploy)
2026-04-21 10:05 UTC: Smoke tests pass (all endpoints 200 OK)
2026-04-21 10:30 UTC: Integration tests pass (batch trigger succeeds)
2026-04-21 10:55 UTC: Performance baselines established
2026-04-21 11:00 UTC: 24-hour monitoring period begins
2026-04-22 11:00 UTC: Monitoring complete, NO CRITICAL ISSUES
2026-04-23 UTC: Analysis of metrics + final validation
2026-04-24 UTC: GO/NO-GO decision for production
2026-04-25 UTC: Production deployment (if GO approved)
```

---

## Rollback Scenario (If Needed)

```
Scenario: Critical issue detected during integration tests

2026-04-21 10:35 UTC: Integration test fails (batch doesn't complete)
2026-04-21 10:40 UTC: Issue triage begins
2026-04-21 10:50 UTC: Rollback decision made
2026-04-21 11:00 UTC: Code reverted + deployed
2026-04-21 11:15 UTC: Database migration rolled back
2026-04-21 11:30 UTC: Staging restored to previous state
2026-04-21 12:00 UTC: Root cause analysis begins
2026-04-22 UTC: Fix implemented + tested locally
2026-04-22 UTC: Second deployment attempt scheduled
```

---

**Status:** READY FOR EXECUTION  
**Approver:** [DevOps Lead / Tech Lead]  
**Execution Date:** 2026-04-21 08:00 UTC
