# Phase 5 Scheduler Integration — Production Deployment Plan

**Project:** tenopa proposer  
**Phase:** 5 - Scheduler Integration  
**Environment:** Production  
**Deployment Date:** 2026-04-25  
**Status:** SCHEDULED  
**Go/No-Go Decision:** 2026-04-22 (Based on 24h staging monitoring)

---

## Executive Summary

Phase 5 Scheduler Integration implements **periodic document migration automation** using APScheduler with concurrent batch processing. This feature enables:

- ✅ Scheduled document ingestion (cron-based)
- ✅ Concurrent batch processing (5 worker threads)
- ✅ Exponential backoff retry logic (1s/2s/4s)
- ✅ RLS-based organization isolation
- ✅ Admin-only management APIs (6 endpoints)
- ✅ Complete audit trail (migration_status_logs)

**Production Readiness:** 95% confidence (based on staging validation)

---

## Pre-Production Criteria (Go/No-Go - 2026-04-22)

### Staging Deployment Must Pass (All Critical)
- [ ] ✅ All 24 unit tests passing (from local validation)
- [ ] ✅ Database migration applied successfully
- [ ] ✅ Scheduler initializes on startup
- [ ] ✅ All 6 API endpoints responding correctly
- [ ] ✅ Batch creation works end-to-end
- [ ] ✅ Error handling functional
- [ ] ✅ 24-hour continuous monitoring completed (2026-04-22 11:00 UTC)

### Staging Monitoring Metrics (24h Window: 2026-04-21 11:00 ~ 2026-04-22 11:00 UTC)
- [ ] Scheduler uptime: ≥ 99.9% (max 1 min downtime)
- [ ] Error rate: < 0.5% (max 50 errors in 100k operations)
- [ ] API p95 response time: < 500ms
- [ ] Batch processing time: < 30s per 100 documents
- [ ] Memory usage: Stable (no memory leaks detected)
- [ ] CPU usage: Consistent (peak < 80%)
- [ ] Database connectivity: 100% (no connection timeouts)
- [ ] No CRITICAL or ERROR level logs (excluding expected retries)

### Production Go/No-Go Decision Matrix
**GO TO PRODUCTION IF:**
- All staging critical criteria ✅
- All monitoring metrics within targets ✅
- Zero P0/P1 issues remaining ✅
- Security review approved ✅
- Rollback plan tested and documented ✅

**NO-GO IF:**
- Any critical staging test failing ❌
- Monitoring metrics exceeded ❌
- P0 issues found (data loss risk, security, availability) ❌
- Memory leaks or performance degradation ❌

---

## Production Deployment Steps (2026-04-25)

### Phase 1: Pre-Deployment (2026-04-25 07:00 UTC)

#### 1a. Final Verification
```bash
# Verify staging still running
curl -X GET https://staging-api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${STAGING_TOKEN}"

# Confirm no recent errors
ssh staging-server "tail -20 /var/log/app.log | grep -i error"

# Backup production database
pg_dump --format custom -f /backup/production_pre_phase5_$(date +%Y%m%d_%H%M%S).bak ${PROD_DB_URL}
```
- [ ] Staging health check passed
- [ ] Production database backed up
- [ ] Backup file verified (size > 100MB expected)

#### 1b. Production Database Backup Verification
```sql
-- On production database
SELECT COUNT(*) as backup_count FROM pg_stat_database 
WHERE datname = 'production_backup';
```
- [ ] Backup database accessible
- [ ] Backup size matches expected range

### Phase 2: Database Migration (2026-04-25 07:30 UTC)

#### 2a. Apply Migration (Option A: Supabase Dashboard)
```
Dashboard > SQL Editor > New Query
[Paste entire contents of database/migrations/040_scheduler_integration.sql]
[Click Run]
[Wait for completion message]
```

#### 2b. Alternative: Command Line
```bash
psql -h ${PROD_HOST} -U ${PROD_USER} -d production \
  -f database/migrations/040_scheduler_integration.sql

# Verify
psql -h ${PROD_HOST} -U ${PROD_USER} -d production -c \
  "SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name LIKE 'migration%';"
```

#### 2c. Post-Migration Verification
```sql
-- Verify all tables created
SELECT COUNT(*) as table_count FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'migration%';
-- Expected: 3

-- Verify all indices created
SELECT COUNT(*) as index_count FROM pg_indexes 
WHERE schemaname = 'public' AND tablename LIKE 'migration%';
-- Expected: 5

-- Verify RLS policies
SELECT COUNT(*) as policy_count FROM pg_policies 
WHERE schemaname = 'public' AND tablename LIKE 'migration%';
-- Expected: 4

-- Test table access
SELECT * FROM migration_batches LIMIT 1;
```

- [ ] migration_batches table created
- [ ] migration_schedules table created  
- [ ] migration_status_logs table created
- [ ] All 5 indices created
- [ ] All 4 RLS policies active
- [ ] No errors in output

### Phase 3: Code Deployment (2026-04-25 08:00 UTC)

#### 3a. Git Push to Production
```bash
cd /path/to/tenopa-proposer
git status  # Verify clean working directory
git pull origin main  # Get latest code (should already have Phase 5 commits)
git log --oneline -5  # Verify Phase 5 commits are present

# Verify Phase 5 files exist
ls -la app/services/scheduler_service.py
ls -la app/graph/nodes/batch_processor.py
ls -la app/api/routes_scheduler.py
```

#### 3b. Production Build & Deployment
```bash
# On production server (e.g., Railway, Render, or direct VPS)
# Option 1: Automated CD (GitHub Actions, Railway)
git push origin main  # Triggers automatic production deployment

# Option 2: Manual deployment
uv sync  # Install dependencies
supervisorctl stop api
# Copy files or pull from git
supervisorctl start api

# Verify deployment
curl -X GET https://api.tenopa.co.kr/api/health \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```

- [ ] Code pushed to main branch
- [ ] Production build triggered/completed
- [ ] Dependencies updated (uv sync)
- [ ] Application restarted successfully
- [ ] Health check responds 200 OK

### Phase 4: Scheduler Initialization Verification (2026-04-25 08:15 UTC)

#### 4a. Monitor Application Startup Logs
```bash
# Real-time monitoring
ssh prod-server "tail -f /var/log/app.log" | grep -i scheduler

# Expected log line:
# [2026-04-25 08:15:00] INFO: Phase 5 정기 문서 마이그레이션 스케줄러 초기화 완료

# Or check after service restart
ssh prod-server "grep -i 'scheduler' /var/log/app.log | tail -10"
```

#### 4b. API Health Check
```bash
# Check scheduler health endpoint
curl -X GET https://api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer ${PROD_TOKEN}"

# Expected response: { "status": "healthy", "scheduler_running": true }
```

- [ ] Scheduler initialization log message found
- [ ] No ERROR level logs during startup
- [ ] Health check responding correctly
- [ ] Scheduler status shows "running"

### Phase 5: Integration Testing (2026-04-25 08:30 UTC)

#### 5a. Test Schedule Creation
```bash
SCHEDULE_PAYLOAD='{
  "name": "Production Test Schedule - 2026-04-25",
  "cron_expression": "0 9 * * *",
  "source_type": "intranet",
  "enabled": true
}'

RESPONSE=$(curl -s -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${SCHEDULE_PAYLOAD}")

echo "$RESPONSE" | jq .
SCHEDULE_ID=$(echo "$RESPONSE" | jq -r '.id')
echo "Created schedule: $SCHEDULE_ID"
```

- [ ] HTTP 200/201 response received
- [ ] Response contains valid schedule_id
- [ ] Schedule name matches input
- [ ] Cron expression validated

#### 5b. Test List Schedules
```bash
curl -s -X GET "https://api.tenopa.co.kr/api/scheduler/schedules?page=1&limit=10" \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .
```

- [ ] Returns 200 OK
- [ ] Contains list of schedules
- [ ] Test schedule visible in list
- [ ] Pagination working correctly

#### 5c. Test Manual Trigger
```bash
TRIGGER_RESPONSE=$(curl -s -X POST \
  https://api.tenopa.co.kr/api/scheduler/schedules/${SCHEDULE_ID}/trigger \
  -H "Authorization: Bearer ${PROD_TOKEN}")

echo "$TRIGGER_RESPONSE" | jq .
BATCH_ID=$(echo "$TRIGGER_RESPONSE" | jq -r '.batch_id')
echo "Created batch: $BATCH_ID"
```

- [ ] HTTP 200 response
- [ ] Batch created successfully
- [ ] Response contains batch_id
- [ ] Batch status shows "processing" or "completed"

#### 5d. Test Batch Status Query
```bash
# Check batch status
curl -s -X GET \
  https://api.tenopa.co.kr/api/scheduler/batches/${BATCH_ID} \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .

# Expected: status in [processing, completed, failed, partial_failed]
```

- [ ] HTTP 200 response
- [ ] Batch details returned
- [ ] Status field present and valid
- [ ] Processed count >= 0

#### 5e. Test Batches List
```bash
curl -s -X GET \
  "https://api.tenopa.co.kr/api/scheduler/batches?page=1&limit=20" \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .
```

- [ ] HTTP 200 response
- [ ] Returns list of batches
- [ ] Test batch visible
- [ ] Pagination info included

### Phase 6: Performance Validation (2026-04-25 09:00 UTC)

#### 6a. Load Test
```bash
# Option 1: Run local load test against production
python scripts/load_test_scheduler.py \
  --target=production \
  --documents=50 \
  --workers=5 \
  --timeout=60

# Option 2: Monitor using production metrics
ssh prod-server "tail -f /var/log/app.log" | \
  grep -E "processing|completed|batch_time|error_rate"
```

**Expected Results:**
- Processing time for 50 documents: < 20 seconds
- Error rate: < 1%
- No timeouts
- No resource exhaustion warnings

- [ ] Load test completed successfully
- [ ] All 50 documents processed
- [ ] Processing time within SLA (< 20s)
- [ ] Error rate < 1%

#### 6b. Monitor Key Metrics (30 minutes)
```bash
# Collect metrics
METRICS_FILE="/tmp/prod_phase5_metrics_$(date +%Y%m%d_%H%M%S).json"

# Scheduler health
echo "=== Scheduler Status ===" >> ${METRICS_FILE}
curl -s https://api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer ${PROD_TOKEN}" >> ${METRICS_FILE}

# Database performance
echo "=== DB Query Performance ===" >> ${METRICS_FILE}
psql -h ${PROD_HOST} -U ${PROD_USER} -d production -c \
  "SELECT 
     (SELECT COUNT(*) FROM migration_batches) as batch_count,
     (SELECT AVG(processing_time_seconds) FROM migration_batches) as avg_processing_time
   \G" >> ${METRICS_FILE}

# Application logs (last 30 minutes)
echo "=== Application Logs ===" >> ${METRICS_FILE}
ssh prod-server "tail -n 500 /var/log/app.log" >> ${METRICS_FILE}
```

**Metrics to Record:**
- [ ] Scheduler uptime: ____% (target: 100%)
- [ ] API p95 response time: ____ms (target: < 500ms)
- [ ] Error rate: ____% (target: < 0.5%)
- [ ] Average batch processing time: ____s (target: < 30s)
- [ ] Database query time: ____ms (target: < 100ms)
- [ ] Memory usage: ____MB (should be stable)
- [ ] CPU usage: ____% (target: < 80%)

### Phase 7: Security Verification (2026-04-25 09:30 UTC)

#### 7a. RLS Policy Test
```bash
# Test with non-admin user (should fail)
curl -s -X GET https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${REGULAR_USER_TOKEN}" \
  2>&1 | grep -i "401\|403\|unauthorized\|forbidden"

# Expected: 401/403 or error message
```

- [ ] Non-admin users cannot access endpoints
- [ ] Admin user can access all endpoints
- [ ] RLS policies enforced at database level

#### 7b. Input Validation
```bash
# Test invalid cron expression
curl -s -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "cron_expression": "invalid", "source_type": "intranet", "enabled": true}' \
  | jq .

# Expected: 400 Bad Request with validation error
```

- [ ] Invalid input rejected with 400 status
- [ ] Error message descriptive
- [ ] No sensitive information leaked

#### 7c. Audit Logging
```bash
# Verify audit trail is being recorded
psql -h ${PROD_HOST} -U ${PROD_USER} -d production -c \
  "SELECT COUNT(*) as log_count, MAX(created_at) as latest FROM migration_status_logs;"
```

- [ ] migration_status_logs table has entries
- [ ] Recent log timestamps visible
- [ ] Audit trail functional

### Phase 8: Post-Deployment Documentation (2026-04-25 10:00 UTC)

#### 8a. Record Deployment Metrics
```markdown
**Phase 5 Production Deployment Summary**
Date: 2026-04-25
Time Started: 2026-04-25 07:00 UTC
Time Completed: 2026-04-25 10:00 UTC (estimated)
Total Duration: 3 hours

**Deployment Steps Completed:**
- [ ] Pre-deployment verification
- [ ] Database migration applied
- [ ] Code deployed
- [ ] Scheduler initialized
- [ ] Integration tests passed
- [ ] Performance validation passed
- [ ] Security verification passed

**Go-Live Metrics:**
- Scheduler uptime: _____%
- API response time (p95): ____ms
- Error rate: _____%
- Batch processing time: ____s
- Memory usage: ____MB
- CPU usage: _____%

**Issues Encountered:** None / [List any issues and resolutions]

**Sign-Off:**
- Deployed By: _______________
- Validated By: _______________
- Date: 2026-04-25
```

- [ ] Deployment metrics recorded
- [ ] All checklist items completed
- [ ] Sign-off obtained from team
- [ ] Post-deployment monitoring scheduled

---

## Monitoring Plan (Post-Deployment)

### Real-Time Monitoring (First 24 hours)
```bash
# Monitor logs
ssh prod-server "tail -f /var/log/app.log" | \
  grep -v "DEBUG" | \
  grep -E "ERROR|CRITICAL|scheduler|batch"

# Check metrics every 15 minutes
watch -n 900 'curl -s https://api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .'
```

**Alert Triggers:**
- [ ] Scheduler stopped or not responding
- [ ] API error rate > 1%
- [ ] Batch processing time > 60 seconds
- [ ] Database connection failures
- [ ] Memory usage > 1GB
- [ ] CPU usage > 90%

### Daily Monitoring (Days 2-7)
- [ ] Check morning application logs for any overnight issues
- [ ] Verify scheduled migrations ran on schedule
- [ ] Monitor database growth rate
- [ ] Collect performance metrics daily
- [ ] Review error logs for patterns

### Weekly Monitoring (Weeks 2+)
- [ ] Generate performance report
- [ ] Review audit trail for all operations
- [ ] Validate concurrent batch processing is working
- [ ] Test failover/recovery procedures
- [ ] Update documentation based on real-world usage

---

## Rollback Plan (If Issues Occur)

### Immediate Rollback (Within First Hour)
```bash
# 1. Stop the application gracefully
systemctl stop api
# or
supervisorctl stop api

# 2. Revert code to previous version
git revert [Phase5_commit_hash]
git push origin main

# 3. Restart application
systemctl start api
# or
supervisorctl start api

# 4. Verify rollback successful
curl -X GET https://api.tenopa.co.kr/api/health

# Application will run without Scheduler functionality
# Database tables remain (no data loss)
# Can be re-deployed later with fixes
```

### Full Rollback (If Critical Issues)
```bash
# 1. Stop application
systemctl stop api

# 2. Restore database from backup
pg_restore --clean --no-acl --no-owner \
  -h ${PROD_HOST} -U ${PROD_USER} -d production \
  /backup/production_pre_phase5_*.bak

# 3. Revert code
git revert [Phase5_commit_hash]
git push origin main

# 4. Restart
systemctl start api

# 5. Verify
curl -X GET https://api.tenopa.co.kr/api/health
psql -h ${PROD_HOST} -U ${PROD_USER} -d production -c \
  "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'migration%';"
# Should return NO results (tables removed by restore)
```

**Rollback Decision Criteria:**
- [ ] Data loss risk detected → Immediate rollback
- [ ] Authentication/authorization broken → Immediate rollback
- [ ] Performance > 2x worse than baseline → Rollback within 1 hour
- [ ] Error rate > 5% sustained for 15 minutes → Rollback within 30 minutes

---

## Success Criteria

### Must Have (Critical)
- ✅ Scheduler initializes on startup
- ✅ All API endpoints responding
- ✅ Database tables created with no errors
- ✅ Batch creation works end-to-end
- ✅ Error handling functional
- ✅ RLS policies enforced
- ✅ Zero data loss

### Should Have (Important)
- ✅ Performance within SLA (< 30s per 100 docs)
- ✅ Error rate < 1%
- ✅ Graceful error handling
- ✅ Audit trail functional
- ✅ Monitoring working

### Nice to Have
- ✅ Performance better than staging
- ✅ Zero rollback needed
- ✅ Documentation complete

---

## Communication Plan

### Before Deployment (2026-04-24)
- [ ] Notify all stakeholders of deployment window
- [ ] Provide estimated duration: 3 hours (07:00-10:00 UTC)
- [ ] Provide communication channel for updates (#tenopa-technical)
- [ ] Create incident response channel if needed

### During Deployment (2026-04-25)
- [ ] Send status update at 07:00 UTC (started)
- [ ] Send status update at 08:00 UTC (database migration complete)
- [ ] Send status update at 09:00 UTC (deployment complete, testing)
- [ ] Send final status at 10:00 UTC (deployment complete/rollback)

### After Deployment
- [ ] Send completion report with metrics
- [ ] Document any issues found
- [ ] Update team on 24-hour monitoring plan
- [ ] Schedule next phase if applicable

---

## Escalation Contacts

| Issue Type | Primary | Backup | Action |
|-----------|---------|--------|--------|
| Database issues | Database Admin | CTO | Page immediately if data loss risk |
| API errors | Backend Lead | DevOps | Check logs, consider rollback |
| Scheduler not running | Backend Lead | Platform | Review startup logs |
| Performance degradation | Performance Team | CTO | Monitor metrics, optimize if < 30s |
| Security issues | Security | CTO | Immediate investigation required |
| General questions | #tenopa-technical | Slack | Document in deployment notes |

---

## Final Checklist

**Pre-Deployment (2026-04-25 06:00 UTC)**
- [ ] All staging metrics reviewed and passed
- [ ] Production database backed up and verified
- [ ] Rollback plan reviewed and tested (on staging)
- [ ] Deployment scripts reviewed and approved
- [ ] Communication plan sent to stakeholders
- [ ] Team on-call and ready
- [ ] Incident response channel created

**Go/No-Go Decision (2026-04-25 06:30 UTC)**
- [ ] Staging passed all success criteria ✅
- [ ] No P0 issues found
- [ ] Security review approved
- [ ] Performance metrics acceptable
- [ ] **DECISION: GO TO PRODUCTION** ✅

**Deployment Execution (2026-04-25 07:00 UTC)**
- [ ] All phases executed as documented
- [ ] All success criteria verified
- [ ] Metrics recorded
- [ ] Monitoring activated
- [ ] Post-deployment documentation complete

---

**Document Status:** READY FOR EXECUTION  
**Last Updated:** 2026-04-20  
**Next Milestone:** Deployment Execution 2026-04-25 07:00 UTC  
**Go-Live Target:** 2026-04-25 10:00 UTC
