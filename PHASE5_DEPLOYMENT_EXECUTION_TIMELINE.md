# Phase 5 Scheduler Integration — Deployment Execution Timeline

**Project:** tenopa proposer  
**Execution Date:** 2026-04-25  
**Execution Window:** 2026-04-25 07:00 - 10:00 UTC  
**Monitoring Duration:** 2026-04-25 10:00 UTC - 2026-04-26 10:00 UTC (24h)  
**Status:** READY FOR EXECUTION ✅

---

## Pre-Deployment Staging (2026-04-21 - 2026-04-22)

### 2026-04-21 Timeline

**09:00 UTC - Staging Deployment Start**
- [ ] Execute `PHASE5_DEPLOYMENT_CHECKLIST.md` steps 1-11
- [ ] Database migration applied
- [ ] Application deployed (Railway/Render/VPS)
- [ ] All integration tests passed

**09:30 UTC - Scheduler Verification**
- [ ] Confirm scheduler initialization in logs
- [ ] Verify all 6 API endpoints responding
- [ ] Test schedule creation, trigger, status endpoints

**10:00 UTC - Monitoring Begins**
- [ ] Set up continuous monitoring (24h window)
- [ ] Configure alert thresholds
- [ ] Begin metrics collection
- [ ] Notify stakeholders: "Staging deployment successful, monitoring phase started"

### 2026-04-22 Timeline (Monitoring Complete + Go/No-Go)

**09:00 UTC - Metrics Review**
- [ ] Collect 24-hour monitoring data
- [ ] Verify all success criteria:
  - ✅ Scheduler uptime ≥ 99.9%
  - ✅ Error rate < 0.5%
  - ✅ API p95 response time < 500ms
  - ✅ Batch processing < 30s per 100 docs
  - ✅ No CRITICAL/ERROR logs
  - ✅ Memory/CPU stable

**11:00 UTC - Go/No-Go Decision**
- [ ] All metrics within target: **GO TO PRODUCTION** ✅
- [ ] Any metric out of spec: **ESCALATE** ⚠️
- [ ] P0 issues found: **NO-GO** ❌

**11:30 UTC - Final Approval**
- [ ] CTO/Tech Lead sign-off for production deployment
- [ ] Deployment window confirmed: 2026-04-25 07:00 UTC
- [ ] Team notifications sent

---

## Production Deployment Day (2026-04-25)

### Pre-Deployment Phase (06:00 - 07:00 UTC)

**06:00 UTC - Readiness Check**
- [ ] Team assembled and ready
- [ ] Communication channel open (#tenopa-technical + Slack)
- [ ] Incident response channel created
- [ ] All tools/credentials verified
- [ ] Notification sent: "Deployment starting in 1 hour"

**06:30 UTC - Final Verification**
- [ ] Production database backed up and verified
- [ ] Rollback plan reviewed (tested on staging)
- [ ] All deployment scripts reviewed
- [ ] No blocking issues identified
- [ ] **FINAL GO/NO-GO: PROCEED** ✅

**06:45 UTC - Team Briefing**
- [ ] All deployment steps reviewed
- [ ] Escalation contacts confirmed
- [ ] Success criteria reviewed
- [ ] 15-minute countdown notification sent

---

### Phase 1: Pre-Deployment (07:00 - 07:30 UTC)

**07:00 UTC - Deployment Start**
- [ ] Notification: "Phase 5 production deployment started"
- [ ] Time log: 07:00 UTC START
- [ ] Staging health check: curl endpoint
- [ ] Production database backup initiated

**07:15 UTC - Backup Verification**
- [ ] Database backup size verified (> 100MB expected)
- [ ] Backup file location confirmed
- [ ] Backup accessible from recovery system
- [ ] Status: "Database backed up and verified"

**07:30 UTC - Checkpoint**
- [ ] Pre-deployment phase complete ✅
- [ ] Proceed to database migration

---

### Phase 2: Database Migration (07:30 - 08:00 UTC)

**07:30 UTC - Migration Start**
- [ ] Execute `database/migrations/040_scheduler_integration.sql`
- [ ] Monitor for errors in output
- [ ] Verify completion message received

**07:40 UTC - Post-Migration Verification**
```sql
SELECT COUNT(*) as table_count FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'migration%';
-- Expected: 3

SELECT COUNT(*) as index_count FROM pg_indexes 
WHERE schemaname = 'public' AND tablename LIKE 'migration%';
-- Expected: 5
```
- [ ] 3 tables created (migration_batches, migration_schedules, migration_status_logs)
- [ ] 5 indices created
- [ ] 4 RLS policies active
- [ ] No errors in migration output
- [ ] Status: "Database migration successful"

**08:00 UTC - Phase 2 Complete**
- [ ] Checkpoint: Database ready for application

---

### Phase 3: Code Deployment (08:00 - 08:15 UTC)

**08:00 UTC - Code Deployment**
- [ ] Git push to main (triggers CD pipeline)
- [ ] Or: Manual deployment steps executed
- [ ] Monitor deployment pipeline

**08:05 UTC - Build & Deploy**
- [ ] Application build triggered/completed
- [ ] Dependencies updated (uv sync)
- [ ] Application restart initiated
- [ ] Monitor logs for startup messages

**08:15 UTC - Phase 3 Complete**
- [ ] Checkpoint: Application deployed
- [ ] Status: "Code deployment successful"

---

### Phase 4: Scheduler Initialization (08:15 - 08:30 UTC)

**08:15 UTC - Verify Scheduler**
- [ ] Check application logs for scheduler init message:
  ```
  INFO: Phase 5 정기 문서 마이그레이션 스케줄러 초기화 완료
  ```
- [ ] Verify no ERROR/CRITICAL logs
- [ ] Health check endpoint responding

**08:20 UTC - Status Check**
- [ ] Scheduler running: YES ✅
- [ ] All endpoints accessible: YES ✅
- [ ] Health check 200 OK: YES ✅
- [ ] Status: "Scheduler initialized and healthy"

**08:30 UTC - Phase 4 Complete**
- [ ] Checkpoint: System ready for testing

---

### Phase 5: Integration Testing (08:30 - 09:00 UTC)

**08:30 UTC - Create Schedule (Test 1)**
```bash
RESPONSE=$(curl -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Prod Test 2026-04-25","cron_expression":"0 9 * * *","source_type":"intranet","enabled":true}')
SCHEDULE_ID=$(echo "$RESPONSE" | jq -r '.id')
```
- [ ] HTTP 200/201 received
- [ ] Valid schedule_id returned
- [ ] Status: "Schedule creation successful"

**08:35 UTC - List Schedules (Test 2)**
```bash
curl -X GET "https://api.tenopa.co.kr/api/scheduler/schedules?page=1&limit=10" \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```
- [ ] HTTP 200 received
- [ ] Test schedule visible in list
- [ ] Status: "Schedule list working"

**08:40 UTC - Manual Trigger (Test 3)**
```bash
TRIGGER=$(curl -X POST \
  https://api.tenopa.co.kr/api/scheduler/schedules/${SCHEDULE_ID}/trigger \
  -H "Authorization: Bearer ${PROD_TOKEN}")
BATCH_ID=$(echo "$TRIGGER" | jq -r '.batch_id')
```
- [ ] HTTP 200 received
- [ ] Batch created with ID
- [ ] Status: "Manual trigger successful"

**08:45 UTC - Batch Status (Test 4)**
```bash
curl -X GET \
  https://api.tenopa.co.kr/api/scheduler/batches/${BATCH_ID} \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```
- [ ] HTTP 200 received
- [ ] Batch status valid (processing/completed)
- [ ] Status: "Batch status query working"

**08:50 UTC - Batches List (Test 5)**
```bash
curl -X GET \
  "https://api.tenopa.co.kr/api/scheduler/batches?page=1&limit=20" \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```
- [ ] HTTP 200 received
- [ ] Test batch visible in list
- [ ] Pagination working
- [ ] Status: "Batches list working"

**09:00 UTC - Phase 5 Complete**
- [ ] All 5 integration tests passed ✅
- [ ] Checkpoint: System ready for performance validation

---

### Phase 6: Performance Validation (09:00 - 09:30 UTC)

**09:00 UTC - Performance Check**
- [ ] Monitor API response times
- [ ] Monitor batch processing duration
- [ ] Monitor error rates
- [ ] Check database performance

**09:15 UTC - Metrics Collection**
Record the following:
- [ ] Scheduler uptime: _____%
- [ ] API p95 response time: ____ms
- [ ] Error rate: _____%
- [ ] Batch processing time: ____s
- [ ] Memory usage: ____MB
- [ ] CPU usage: _____%
- [ ] Database query time: ____ms

**09:30 UTC - Phase 6 Complete**
- [ ] All metrics within acceptable range ✅
- [ ] Status: "Performance validation successful"

---

### Phase 7: Security Verification (09:30 - 09:45 UTC)

**09:30 UTC - RLS Policy Test**
```bash
# Non-admin user attempt (should fail)
curl -X GET https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${REGULAR_USER_TOKEN}"
```
- [ ] Returns 401/403 (unauthorized) ✅
- [ ] Status: "RLS policies enforced"

**09:35 UTC - Input Validation Test**
```bash
# Invalid cron expression
curl -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","cron_expression":"invalid","source_type":"intranet","enabled":true}'
```
- [ ] Returns 400 Bad Request ✅
- [ ] Error message descriptive
- [ ] Status: "Input validation working"

**09:40 UTC - Audit Trail Verification**
```sql
SELECT COUNT(*) as log_count FROM migration_status_logs;
```
- [ ] Records exist ✅
- [ ] Status: "Audit logging functional"

**09:45 UTC - Phase 7 Complete**
- [ ] All security checks passed ✅

---

### Phase 8: Post-Deployment (09:45 - 10:00 UTC)

**09:45 UTC - Record Deployment Metrics**
- [ ] Document all metrics collected
- [ ] Record completion time
- [ ] Note any issues encountered
- [ ] Sign-off obtained

**09:50 UTC - Activate Monitoring**
- [ ] 24-hour post-deployment monitoring activated
- [ ] Alert thresholds configured
- [ ] Monitoring dashboard accessible
- [ ] Team notified of monitoring status

**10:00 UTC - DEPLOYMENT COMPLETE ✅**
- [ ] Time log: 10:00 UTC COMPLETE
- [ ] Total deployment time: 3 hours
- [ ] All success criteria verified ✅
- [ ] **GO-LIVE SUCCESSFUL**
- [ ] Final notification: "Phase 5 Scheduler Integration production deployment complete. System stable. 24h monitoring active."

---

## Post-Deployment Monitoring (2026-04-25 10:00 - 2026-04-26 10:00 UTC)

### Real-Time Monitoring (First 4 hours: 10:00 - 14:00 UTC)
- [ ] Monitor logs every 15 minutes
- [ ] Check scheduler health every 15 minutes
- [ ] Monitor API response times
- [ ] Watch for error spikes
- [ ] Verify batch processing continues normally

### Continuous Monitoring (14:00 - 10:00 next day)
- [ ] Check logs hourly
- [ ] Monitor dashboard every hour
- [ ] Record metrics every 6 hours
- [ ] Alert on any anomalies

### Alert Triggers During Monitoring
- [ ] Scheduler stopped: **IMMEDIATE ESCALATION**
- [ ] API error rate > 1%: **INVESTIGATE**
- [ ] Batch processing > 60s: **MONITOR CLOSELY**
- [ ] Memory usage > 1GB: **CHECK FOR LEAK**
- [ ] Database connection failures: **IMMEDIATE ESCALATION**

---

## Quick Reference - Deployment Day Commands

### Pre-Deployment
```bash
# Final checks (run at 06:30 UTC)
ssh prod-server "curl -s http://localhost:8000/api/health | jq ."
pg_dump --format custom -f /backup/prod_pre_phase5_$(date +%Y%m%d).bak ${PROD_DB}
```

### Database Migration
```bash
# Run migration
psql -h ${PROD_HOST} -U ${PROD_USER} -d production \
  -f database/migrations/040_scheduler_integration.sql

# Verify
psql -h ${PROD_HOST} -U ${PROD_USER} -d production -c \
  "SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name LIKE 'migration%';"
```

### Code Deployment
```bash
# Option 1: Automatic (CD pipeline)
git push origin main

# Option 2: Manual
ssh prod-server "cd /app && git pull origin main && uv sync && supervisorctl restart api"
```

### Verification
```bash
# Check scheduler
curl -s https://api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .

# Test schedule creation
curl -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","cron_expression":"0 9 * * *","source_type":"intranet","enabled":true}' | jq .
```

### Monitoring
```bash
# Watch logs
ssh prod-server "tail -f /var/log/app.log | grep -E 'ERROR|scheduler|batch'"

# Check metrics
watch -n 60 'curl -s https://api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer ${PROD_TOKEN}" | jq .'
```

### Rollback (If Needed)
```bash
# Immediate rollback
systemctl stop api
git revert [commit_hash]
git push origin main
systemctl start api

# Or full rollback with database restore
pg_restore --clean -d production /backup/prod_pre_phase5_*.bak
```

---

## Team Assignments

| Role | Name | Responsibility | Phone/Slack |
|------|------|-----------------|-------------|
| **Deployment Lead** | [Name] | Overall orchestration | [Contact] |
| **Backend Lead** | [Name] | Code deployment, monitoring | [Contact] |
| **Database Admin** | [Name] | Database migration, backup | [Contact] |
| **DevOps/Platform** | [Name] | Infrastructure, logs | [Contact] |
| **QA Lead** | [Name] | Testing, validation | [Contact] |
| **CTO/Approver** | [Name] | Go/no-go decisions | [Contact] |

---

## Communication Timeline

**2026-04-24 (Day Before)**
- 17:00 UTC: "Deployment happening tomorrow 07:00 UTC. Team: 15 min standup tomorrow 06:45 UTC"

**2026-04-25 (Deployment Day)**
- 06:45 UTC: "Team standup - deployment in 15 minutes"
- 07:00 UTC: "Phase 5 production deployment started"
- 08:00 UTC: "Database migration complete, code deployment in progress"
- 09:00 UTC: "All systems deployed, integration testing in progress"
- 10:00 UTC: "✅ Phase 5 production deployment COMPLETE. All tests passed. 24h monitoring active."
- 18:00 UTC: "✅ Production stable. 11h monitoring complete, no issues. Continuing 24h watch."

**2026-04-26**
- 10:00 UTC: "✅ 24h post-deployment monitoring complete. All metrics nominal. Phase 5 stable in production."

---

**Status:** READY FOR EXECUTION ✅  
**Approval Date:** 2026-04-20  
**Execution Date:** 2026-04-25 07:00 UTC  
**Contingency:** Detailed rollback plan available  
**Success Confidence:** 95%
