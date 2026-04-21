# Phase 5 Staging Monitoring Plan

**Feature**: phase5-scheduler-integration  
**Status**: Staging Deployed ✅ (2026-04-21 09:00 UTC)  
**Monitoring Window**: 24 hours (2026-04-21 ~ 2026-04-22)  
**Go/No-Go Decision**: 2026-04-22 09:00 UTC → Production deployment 2026-04-25

---

## Monitoring Objectives

**Primary**: Validate scheduler service stability under staging load  
**Secondary**: Establish baseline metrics for production deployment SLO

---

## Checkpoint Schedule

| Checkpoint | Time UTC | Check Items | Go/No-Go |
|------------|----------|-------------|----------|
| **1 (Baseline)** | 2026-04-21 09:00 | Service startup, DB migration, API endpoints | — |
| **2 (2h)** | 2026-04-21 11:00 | Health, error rate, latency, memory | YELLOW (track) |
| **3 (5h)** | 2026-04-21 14:00 | Extended monitoring | YELLOW (track) |
| **4 (9h)** | 2026-04-21 18:00 | Evening load test | YELLOW (track) |
| **5 (15h)** | 2026-04-22 00:00 | Overnight stability | YELLOW (track) |
| **6 (20h)** | 2026-04-22 05:00 | Pre-morning test | YELLOW (track) |
| **7 (FINAL)** | 2026-04-22 09:00 | 24h summary & decision | **GO/NO-GO** |

---

## Health Check Items (Each Checkpoint)

### 1. Service Health

```bash
# Check scheduler service is running
curl -X GET https://staging.api.tenopa.co.kr/api/scheduler/health \
  -H "Authorization: Bearer {staging_token}"

# Expected response:
# {
#   "status": "healthy",
#   "version": "4.1.0",
#   "uptime_seconds": 7200,
#   "db_connected": true,
#   "memory_mb": 385
# }

# Success: HTTP 200, status = "healthy"
# ALERT: HTTP 503 or status = "unhealthy"
```

### 2. Error Logs (Last 30 min)

```bash
# Check for CRITICAL/ERROR logs
tail -30 /var/log/tenopa/scheduler.log | grep -i "ERROR\|CRITICAL"

# Expected: None (or only < 1% of total logs)
# ALERT: Any CRITICAL, or ERROR rate > 1%
```

### 3. API Latency Sample

```bash
# Test 6 critical endpoints (time the response)
time curl -X GET https://staging.api.tenopa.co.kr/api/migrations/status \
  -H "Authorization: Bearer {token}"

# Expected: < 500ms p95 latency
# ALERT: > 1000ms latency consistently
```

### 4. Memory Usage

```bash
# Check process memory
ps aux | grep "uvicorn.*scheduler" | awk '{print $6}'

# Expected: < 500 MB
# ALERT: > 1000 MB or growing trend
```

### 5. Database Connection Pool

```bash
# Query PostgreSQL connection count
psql -c "SELECT count(*) FROM pg_stat_activity WHERE application_name LIKE '%tenopa%';"

# Expected: 5-10 connections
# ALERT: > 20 connections or connection errors
```

### 6. Migration Status

```bash
# Verify 006_scheduler_integration.sql ran successfully
SELECT count(*) FROM information_schema.tables 
WHERE table_name IN ('scheduler_jobs', 'scheduler_execution_logs', 'batch_migrations');

# Expected: 3 new tables created
# ALERT: Any table missing
```

---

## Go/No-Go Criteria (Final Checkpoint)

### GO Conditions (Proceed to Production)
- ✅ Service uptime: 99.0%+ (0 unplanned restarts)
- ✅ Error rate: <0.5% (avg across 24h)
- ✅ API latency p95: <500ms (consistent)
- ✅ Database: No connection errors
- ✅ Memory: Stable (<400 MB avg)
- ✅ Migration: All 3 tables verified
- ✅ No security alerts

### NO-GO Conditions (Hold for Fixes)
- ❌ Service crash/restart detected
- ❌ Error rate >1% sustained
- ❌ Memory leak trend (continuous growth)
- ❌ Database connection failures
- ❌ Any migration table missing
- ❌ Security incident detected

---

## Automated Checkpoint Collection

**Script**: `scripts/phase5_checkpoint.sh` (run hourly)

```bash
#!/bin/bash
# Automated checkpoint collection every 2 hours

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S")
LOG_FILE="PHASE5_MONITORING_STATUS.jsonl"

health=$(curl -s https://staging.api.tenopa.co.kr/api/scheduler/health)
error_count=$(tail -100 /var/log/tenopa/scheduler.log | grep -c "ERROR")
memory=$(ps aux | grep uvicorn | awk '{print $6}')

echo "{
  \"timestamp\": \"$TIMESTAMP\",
  \"status\": \"$(echo $health | jq -r .status)\",
  \"uptime_seconds\": $(echo $health | jq .uptime_seconds),
  \"error_count_30min\": $error_count,
  \"memory_mb\": $memory,
  \"db_connected\": $(echo $health | jq .db_connected)
}" >> $LOG_FILE
```

**Run via**:
```bash
# Option 1: Cron job (every 2 hours)
0 */2 * * * cd /c/project/tenopa\ proposer && bash scripts/phase5_checkpoint.sh

# Option 2: Manual execution
bash scripts/phase5_checkpoint.sh
```

---

## Escalation Procedure

**If GO→NO-GO transition detected**:

1. **Immediate** (0 min)
   - Pause production deployment scheduling
   - Post #incidents alert: "@devops Scheduler health degradation detected in staging"

2. **Investigation** (5 min)
   - Check error logs for root cause
   - Review memory/connection trends
   - Restart service if needed (test fix)

3. **Communication** (10 min)
   - Update #deployments channel
   - Notify @product-manager of delay
   - Estimate fix time

4. **Resolution** (30-60 min)
   - Apply fix to staging
   - Re-run 2h checkpoint
   - If stable → Resume monitoring
   - If still failing → Extend monitoring window to 48h

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | >99.0% | Service restart count = 0 |
| Error rate | <0.5% | ERROR log lines / total log lines |
| Latency p95 | <500ms | Last 100 requests sample |
| Memory stability | <2% growth/4h | Memory at t=0h vs t=4h |
| DB connections | Stable | No spike/drop events |

---

## Post-Deployment (Production)

**Next Steps After GO**:
1. Tag release: `git tag -a v4.1.0-phase5 -m "Phase 5 Scheduler Integration Production Release"`
2. Schedule production deployment: 2026-04-25 08:00 UTC
3. Notify teams: #deployments + email blast
4. Set up production monitoring (same metrics)

