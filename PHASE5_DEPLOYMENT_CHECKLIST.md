# Phase 5 Scheduler Integration — Deployment Checklist

**Project:** tenopa proposer  
**Phase:** 5 - Scheduler Integration  
**Environment:** Staging  
**Deployment Date:** 2026-04-21  
**Status:** READY FOR DEPLOYMENT ✅

---

## Pre-Deployment (Local Environment)

- [x] All 24 unit tests passing
- [x] Database migration SQL created (006_scheduler_integration.sql)
- [x] SchedulerService implemented (236 lines)
- [x] ConcurrentBatchProcessor implemented (222 lines)
- [x] API routes defined (6 endpoints)
- [x] App integration complete (main.py updated)
- [x] Scheduler initialization in lifespan
- [x] Scheduler shutdown in lifespan
- [x] Error handling comprehensive
- [x] Logging in place
- [x] Validation script created and passing

## Staging Deployment Steps

### Step 1: Backup Staging Database
- [ ] Log into Supabase Dashboard
- [ ] Navigate to Database > Backups
- [ ] Click "Create backup"
- [ ] Wait for backup to complete (typically 2-5 minutes)
- [ ] Note backup filename for reference

**Alternative (Command Line):**
```bash
pg_dump --format custom -f staging_backup_$(date +%Y%m%d_%H%M%S).bak [DATABASE_URL]
```

### Step 2: Apply Database Migration
Execute SQL from: `database/migrations/006_scheduler_integration.sql`

**Option A: Supabase SQL Editor**
- [ ] Go to Supabase Dashboard > SQL Editor
- [ ] Click "New Query"
- [ ] Copy entire contents of 006_scheduler_integration.sql
- [ ] Paste into SQL editor
- [ ] Click "Run"
- [ ] Verify: "migration completed" appears at bottom
- [ ] Check that no errors are shown

**Option B: Command Line**
```bash
psql -h [HOST] -U [USER] -d [DATABASE] \
  -f database/migrations/006_scheduler_integration.sql
```

### Step 3: Verify Database Schema Created
Execute verification query:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'migration%';
```

Expected output:
```
migration_schedules
migration_batches
migration_logs
```

- [ ] migration_schedules table exists
- [ ] migration_batches table exists
- [ ] migration_logs table exists

### Step 4: Verify Indices Created
Execute index verification query:
```sql
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE 'migration%';
```

Expected indices (8 total):
- idx_migration_schedules_enabled ✓
- idx_migration_schedules_created ✓
- idx_migration_batches_schedule ✓
- idx_migration_batches_status ✓
- idx_migration_batches_created ✓
- idx_migration_logs_batch ✓
- idx_migration_logs_status ✓
- idx_migration_logs_document ✓

- [ ] All 8 indices created

### Step 5: Deploy Application Code

**Option A: Git Push (Recommended)**
```bash
cd /path/to/project
git add .
git commit -m "feat: Phase 5 Scheduler Integration staging deployment"
git push origin main
```
- [ ] Code pushed to main
- [ ] Staging deployment triggered automatically
- [ ] Monitor deployment logs

**Option B: Manual Deployment**
```bash
# Copy files to staging server
rsync -av app/ database/ tests/ [staging_server]:/app/

# On staging server
ssh [staging_server]
cd /app
uv sync
supervisorctl restart api
```

- [ ] Code copied to staging
- [ ] Dependencies installed (uv sync)
- [ ] Application restarted
- [ ] Service running without errors

### Step 6: Verify Scheduler Initialization
Check application logs for initialization message:

```
[Phase 5] 정기 문서 마이그레이션 스케줄러 초기화 완료
```

**View Logs:**
- [ ] Railway: `railway logs --follow`
- [ ] Render: `render logs`
- [ ] SSH: `ssh [server] "tail -f /var/log/app.log | grep -i scheduler"`

**Success:** Scheduler started without errors

### Step 7: Run Local Unit Tests
```bash
cd /path/to/project
pytest tests/test_scheduler_integration.py -v --tb=short
```

- [ ] 24/24 tests PASSING
- [ ] No failures or critical errors
- [ ] Duration: ~6-10 seconds

### Step 8: Run Staging Integration Tests
From staging environment or via remote:

```bash
pytest tests/test_scheduler_integration_check.py -v
```

- [ ] All integration tests passing
- [ ] No database connection errors
- [ ] All endpoints responding

### Step 9: Manual API Endpoint Testing

**9a. Create Schedule**
```bash
curl -X POST https://staging-api.yourdomain.com/api/migration/schedules \
  -H "Authorization: Bearer [YOUR_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Staging Test Schedule",
    "cron_expression": "0 8 * * *",
    "source_type": "intranet",
    "enabled": true
  }'
```
- [ ] Response: 200 OK
- [ ] Response contains schedule_id
- [ ] Note the schedule_id for next tests

**9b. Get Schedules**
```bash
curl -X GET https://staging-api.yourdomain.com/api/migration/schedules \
  -H "Authorization: Bearer [YOUR_TOKEN]"
```
- [ ] Response: 200 OK
- [ ] Response contains list of schedules
- [ ] Test schedule appears in list

**9c. Trigger Migration**
```bash
curl -X POST https://staging-api.yourdomain.com/api/migration/trigger/[SCHEDULE_ID] \
  -H "Authorization: Bearer [YOUR_TOKEN]"
```
- [ ] Response: 200 OK
- [ ] Response contains batch_id

**9d. Get Batch Status**
```bash
curl -X GET https://staging-api.yourdomain.com/api/migration/batches/[BATCH_ID] \
  -H "Authorization: Bearer [YOUR_TOKEN]"
```
- [ ] Response: 200 OK
- [ ] Response shows batch details
- [ ] Status is "completed" or "processing"

**9e. Get Batches List**
```bash
curl -X GET https://staging-api.yourdomain.com/api/migration/batches \
  -H "Authorization: Bearer [YOUR_TOKEN]"
```
- [ ] Response: 200 OK
- [ ] Response contains batch list

### Step 10: Performance Testing

**Load Test (100 documents):**
```bash
python scripts/load_test_scheduler.py --documents=100 --workers=5
```

- [ ] Processing completes in < 30 seconds
- [ ] All 100 documents processed
- [ ] Error rate < 1%
- [ ] No timeouts or hangs

### Step 11: Monitoring & Alerts Setup

**Metrics to Monitor (30 minutes continuous):**
- [ ] Scheduler startup time: _____ seconds (target: < 2s)
- [ ] API response time: _____ ms (target: < 200ms)
- [ ] Error rate: ______ % (target: < 0.1%)
- [ ] Batch processing time: _____ seconds (target: < 30s)
- [ ] Worker utilization: ______ % (target: 80-90%)

**Log Monitoring:**
```bash
tail -f [app_logs] | grep -E "Scheduler|Batch|Migration|error"
```

- [ ] No ERROR level logs
- [ ] No CRITICAL level logs
- [ ] INFO logs showing operations

**Alert Thresholds:**
- [ ] Set alert if Scheduler fails to initialize
- [ ] Set alert if API response time > 500ms
- [ ] Set alert if batch processing > 60s
- [ ] Set alert if error rate > 1%

---

## Success Criteria Verification

### Critical (Must Pass)
- [x] All 24 unit tests passing
- [ ] Database migration applied successfully
- [ ] Scheduler initializes on startup
- [ ] All 6 API endpoints responding correctly
- [ ] Batch creation works end-to-end
- [ ] Error handling functional

### Important (Should Pass)
- [ ] 100+ documents processed in < 30 seconds
- [ ] Concurrent workers executing (5 threads)
- [ ] Retry logic functioning correctly
- [ ] Database records persisting
- [ ] Logging capturing operations

### Nice to Have
- [ ] Performance < 20 seconds for 100 docs
- [ ] Graceful error degradation
- [ ] Full SLA compliance

---

## Post-Deployment

### Documentation
- [ ] Update deployment report
- [ ] Document any issues found
- [ ] Record actual metrics achieved
- [ ] Note any anomalies

### If All Checks Pass ✅
- [ ] Close staging deployment task
- [ ] Update project status to "staging validated"
- [ ] Schedule production deployment for 2026-04-25
- [ ] Plan ACT phase (minimal, already tested)

### If Issues Found ⚠️
- [ ] Document issue in detail
- [ ] Create bug fix commits
- [ ] Re-run tests to verify fixes
- [ ] Return to Step 7 (re-test)
- [ ] Do NOT proceed to production until resolved

---

## Rollback Plan (If Needed)

### Stop Application Gracefully
```bash
# Application will stop picking up new schedules
systemctl stop api
# or: supervisorctl stop api
```

### Backup Data (If Needed)
```sql
SELECT * FROM migration_schedules INTO OUTFILE 'schedules_backup.csv';
SELECT * FROM migration_batches INTO OUTFILE 'batches_backup.csv';
SELECT * FROM migration_logs INTO OUTFILE 'logs_backup.csv';
```

### Remove Tables
```sql
DROP TABLE IF EXISTS migration_logs;
DROP TABLE IF EXISTS migration_batches;
DROP TABLE IF EXISTS migration_schedules;
```

### Revert Code
```bash
git revert [commit_hash]
git push origin main
# Or manually restore previous version
```

### Restart Application
```bash
systemctl start api
# or: supervisorctl start api
```

### Verify Rollback
```bash
tail -f /var/log/app.log
# Look for initialization without scheduler
```

---

## Contact & Escalation

| Issue | Contact | Action |
|-------|---------|--------|
| Database problems | Database admin | Restore from backup if needed |
| API not responding | Backend team | Check logs, restart service |
| Scheduler not initializing | Backend team | Check logs for errors |
| Performance issues | Performance team | Review load, check indices |
| General questions | #tenopa-technical | Slack channel |

---

## Sign-Off

**Deployment Executed By:** _________________  
**Date:** _________________  
**Time Started:** _________________  
**Time Completed:** _________________  

**All Success Criteria Met:** ☐ YES ☐ NO  
**Ready for Production:** ☐ YES ☐ NO  

**Notes:**
```
[Space for deployment notes]
```

---

**Reference Documents:**
- Staging Deployment Guide: `docs/operations/phase5-staging-deployment-guide.md`
- Deployment Ready Report: `docs/operations/phase5-staging-deployment-ready.md`
- Deployment Script (Unix): `scripts/deploy_phase5_staging.sh`
- Deployment Script (Windows): `scripts/deploy_phase5_staging.bat`
- Validation Script: `scripts/validate_phase5_staging.py`
- Test Suite: `tests/test_scheduler_integration.py`

---

**Status:** STAGING DEPLOYMENT READY ✅  
**Date Prepared:** 2026-04-20  
**Next Milestone:** Production Deployment (2026-04-25)
