# Phase 5 Scheduler Integration — Staging Deployment Guide

**Date:** 2026-04-20  
**Target Deployment Date:** 2026-04-21  
**Target Environment:** Staging  

## Pre-Deployment Checklist

- [ ] All 24 unit tests passing (`pytest tests/test_scheduler_integration.py -v`)
- [ ] Database migration SQL validated
- [ ] API endpoint contracts defined
- [ ] APScheduler configuration ready
- [ ] Environment variables set (Supabase URL, keys, API keys)
- [ ] Backup of current staging database created
- [ ] Deployment rollback plan documented

## Deployment Steps

### 1. Prepare Staging Environment

```bash
# Update dependencies
uv sync

# Verify database connection to staging
python -c "from app.config import settings; print(f'DB: {settings.database_url}')"

# Create backup of staging database (if applicable)
# pg_dump --format custom -f staging_backup_$(date +%Y%m%d_%H%M%S).bak
```

### 2. Run Database Migration

```bash
# Apply Phase 5 scheduler integration migration
# This creates: migration_schedules, migration_batches, migration_logs tables

# Option A: Direct SQL execution (if you have direct DB access)
psql -h [staging_db_host] -U [user] -d [database] \
  -f database/migrations/006_scheduler_integration.sql

# Option B: Via Supabase SQL editor
# 1. Go to Supabase dashboard
# 2. Navigate to SQL Editor
# 3. Create new query
# 4. Copy contents of database/migrations/006_scheduler_integration.sql
# 5. Execute query
```

### 3. Verify Database Schema

```bash
# Check tables created
psql -h [staging_db_host] -U [user] -d [database] -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'migration%';"

# Expected output:
# - migration_schedules
# - migration_batches
# - migration_logs

# Check indices created
psql -h [staging_db_host] -U [user] -d [database] -c \
  "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename LIKE 'migration%';"

# Expected output: 8 indices for performance
```

### 4. Deploy Application

```bash
# Option A: Using Railway/Render deployment platform
# 1. Push changes to main branch: git push origin main
# 2. Deployment will trigger automatically
# 3. Monitor deployment logs

# Option B: Manual deployment to staging server
# Copy files to staging server and restart service
rsync -av --exclude=.git app/ database/ tests/ [staging_server]:/app/

# Restart application
ssh [staging_server] "cd /app && uv sync && supervisorctl restart api"
```

### 5. Verify Scheduler Initialization

```bash
# Check application logs for successful initialization
# Expected log message:
# "Scheduler initialized with X schedules"

# View recent logs
# If using Railway: railway logs
# If using Render: render logs

# Verify no errors in scheduler startup
grep -i "scheduler" [app_logs] | head -20
```

## Post-Deployment Testing

### 1. Run Integration Tests in Staging

```bash
# From staging environment, run integration test suite
pytest tests/test_scheduler_integration.py -v --tb=short

# Expected result: 24/24 tests PASSING
```

### 2. Manual API Endpoint Testing

#### Create Schedule
```bash
curl -X POST http://staging-api.local/api/migration/schedules \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Schedule",
    "cron_expression": "0 8 * * *",
    "source_type": "intranet",
    "enabled": true
  }'

# Expected response: 200 OK with schedule_id
```

#### Get Schedules
```bash
curl -X GET http://staging-api.local/api/migration/schedules \
  -H "Authorization: Bearer [token]"

# Expected response: 200 OK with list of schedules
```

#### Trigger Migration
```bash
curl -X POST http://staging-api.local/api/migration/trigger/[schedule_id] \
  -H "Authorization: Bearer [token]"

# Expected response: 200 OK with batch_id
```

#### Get Batch Status
```bash
curl -X GET http://staging-api.local/api/migration/batches/[batch_id] \
  -H "Authorization: Bearer [token]"

# Expected response: 200 OK with batch details
```

### 3. Database Verification

```bash
# Verify schedule was created
SELECT * FROM migration_schedules WHERE enabled = true;

# Verify batch was created
SELECT * FROM migration_batches ORDER BY created_at DESC LIMIT 5;

# Check migration logs
SELECT COUNT(*) as log_count FROM migration_logs;
```

### 4. Performance Testing

```bash
# Load test with 100 document batch
python scripts/load_test_scheduler.py --documents=100 --workers=5

# Monitor:
# - Processing time (target: < 30 seconds)
# - Worker utilization (should use 5 threads)
# - Error rate (target: < 1%)
# - Database query performance
```

## Success Criteria

### Critical (Must Pass)
- [ ] All 24 unit tests passing
- [ ] Database migration applied successfully
- [ ] Application starts without errors
- [ ] Scheduler initializes on startup
- [ ] API endpoints respond with correct status codes
- [ ] Batch creation works end-to-end

### Important (Should Pass)
- [ ] 100+ documents processed in < 30 seconds
- [ ] Error handling covers edge cases
- [ ] Database records persist correctly
- [ ] Concurrent workers executing properly
- [ ] Retry logic functions correctly

### Nice to Have
- [ ] Performance within SLA (< 20 seconds for 100 docs)
- [ ] Graceful degradation on errors
- [ ] Logging captures all operations

## Monitoring During Staging

### Real-time Monitoring

```bash
# Watch application logs
tail -f [app_logs] | grep -E "Scheduler|Batch|Migration"

# Monitor database queries
# Enable query logging if available

# Track error rates
grep -i "error" [app_logs] | wc -l
```

### Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Scheduler startup time | < 2s | > 5s |
| Batch processing time | < 30s (100 docs) | > 60s |
| API response time | < 200ms | > 500ms |
| Error rate | < 0.1% | > 1% |
| Database query time | < 500ms | > 1s |
| Worker utilization | 80-90% | < 50% |

## Rollback Plan

If critical issues found during staging, follow these steps:

### Immediate Rollback

```bash
# Stop scheduler gracefully
# Application will stop picking up new schedules

# Revert database migration (if needed)
# Drop tables if data is not critical:
DROP TABLE IF EXISTS migration_logs;
DROP TABLE IF EXISTS migration_batches;
DROP TABLE IF EXISTS migration_schedules;

# Revert code to previous commit
git revert [commit_hash]
git push origin main

# Restart application
# Deployment will trigger automatically
```

### Data Preservation Rollback

If you need to preserve data:

```bash
# Backup migration data before rollback
SELECT * FROM migration_schedules INTO OUTFILE 'schedules_backup.csv';
SELECT * FROM migration_batches INTO OUTFILE 'batches_backup.csv';

# Then proceed with database cleanup
```

## Known Issues & Workarounds

### Issue 1: Scheduler Not Initializing
**Symptom:** Scheduler startup log shows 0 schedules  
**Cause:** migration_schedules table empty  
**Fix:** Create test schedule via API endpoint

### Issue 2: Batch Processing Stuck
**Symptom:** Batch status remains "processing" indefinitely  
**Cause:** Worker thread deadlock or exception  
**Fix:** Check application logs, restart workers

### Issue 3: Database Connection Errors
**Symptom:** "Connection refused" in logs  
**Cause:** Staging database credentials incorrect  
**Fix:** Verify environment variables, check DB availability

## Support & Escalation

### Contact Points
- **Staging Database:** [Supabase Dashboard URL]
- **Application Logs:** [Logging Platform URL]
- **Team Slack:** #tenopa-technical

### Escalation Path
1. **First:** Check logs and metrics (30 min troubleshooting)
2. **Second:** Execute rollback plan if needed
3. **Third:** File incident report and proceed to fix in next cycle

## Next Steps

### If Staging Validation Passes ✅
1. Create staging validation report (5 min)
2. Update deployment checklist (5 min)
3. Schedule production deployment (2026-04-25)
4. Begin ACT phase (bug fixes if needed)

### If Issues Found ⚠️
1. Document issues with exact error messages
2. Create bug fixes in new commits
3. Re-run tests to verify fixes
4. Return to step 1 (staging validation)

## Appendix: Useful Commands

```bash
# Deploy from command line
railway deploy

# View real-time logs
railway logs --follow

# Trigger manual database backup
pg_dump --format custom -f backup.bak [database_url]

# Scale workers if needed
# Update ConcurrentBatchProcessor(num_workers=10) in routes_migration.py

# Check scheduler status
curl http://staging-api.local/health
```

---

**Deployment Target:** 2026-04-21  
**Estimated Duration:** 30-60 minutes  
**Risk Level:** LOW (all tests passing, comprehensive validation)
