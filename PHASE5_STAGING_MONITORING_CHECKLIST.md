# Phase 5 Staging Deployment - 24h Monitoring Checklist

**Monitoring Window:** 2026-04-21 11:00 UTC — 2026-04-22 11:00 UTC  
**Status:** 🔄 IN PROGRESS  
**Next Decision:** 2026-04-22 11:30 UTC (Go/No-Go)

---

## Success Criteria

All of these must be satisfied for **GO TO PRODUCTION** decision:

| Criteria | Target | Status | Notes |
|----------|--------|--------|-------|
| Scheduler Uptime | ≥ 99.9% | ⏳ | Must not stop during 24h |
| Error Rate | < 0.5% | ⏳ | 4xx + 5xx combined |
| Batch Processing Time | < 30s per 100 docs | ⏳ | Measure actual performance |
| API p95 Response Time | < 500ms | ⏳ | All 6 endpoints combined |
| Memory Stable | No leaks detected | ⏳ | Watch for growth trend |
| Critical Logs | None | ⏳ | CRITICAL or ERROR not allowed |
| RLS Enforcement | 100% | ⏳ | Non-admin access denied |
| Database Integrity | All constraints valid | ⏳ | No orphaned records |

---

## Monitoring Timeline

### Phase 1: Real-Time Intensive (0-4h) — 11:00 - 15:00 UTC

**11:00 UTC - Start Monitoring**
- [ ] Confirm scheduler running (check logs: "스케줄러 초기화 완료")
- [ ] Health endpoint responding: `/api/scheduler/health` → 200 OK
- [ ] All 6 API endpoints accessible
- [ ] No ERROR/CRITICAL in initial logs
- [ ] Baseline metrics recorded

**12:00 UTC - 1h Checkpoint**
- [ ] Scheduler still running (no restarts)
- [ ] Error rate < 0.5%
- [ ] API response times normal
- [ ] Memory usage stable
- [ ] Review logs for warnings
- **Action if anomaly**: Log issue, continue monitoring (no escalation yet)

**13:00 UTC - 2h Checkpoint**
- [ ] Scheduler uptime on track
- [ ] Manual trigger test: Create test schedule + trigger batch
- [ ] Verify batch completed successfully
- [ ] Check database consistency (3 tables, 8 indices intact)
- [ ] Network/connectivity normal

**14:00 UTC - 3h Checkpoint**
- [ ] Second manual trigger test
- [ ] Performance metrics collection
- [ ] Error trend analysis (should be ≈ 0)
- [ ] Resource usage review
- [ ] Prepare summary for next phase

**15:00 UTC - 4h Checkpoint (Phase 1 Complete)**
- [ ] All metrics nominal
- [ ] No critical issues detected
- [ ] Performance baseline established
- **Status**: ✅ PHASE 1 CLEAR — Proceed to Phase 2 continuous monitoring

---

### Phase 2: Continuous Monitoring (4-24h) — 15:00 UTC Day 1 to 11:00 UTC Day 2

**Every 4 hours (15:00, 19:00, 23:00 UTC on Day 1; 03:00, 07:00, 11:00 UTC on Day 2):**

- [ ] Scheduler health check
- [ ] Error rate < 0.5% (rolling 4h window)
- [ ] p95 response time < 500ms
- [ ] Memory usage trend (no exponential growth)
- [ ] Database connection count normal (<5/10)
- [ ] Batch processing working (create test schedule)
- [ ] RLS policies still enforced
- [ ] Log for anomalies or warnings

**Checkpoints:**

| Time | Scheduler | Error Rate | p95 Latency | Memory | Status |
|------|-----------|-----------|-------------|--------|--------|
| 15:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| 19:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| 23:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| 03:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| 07:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| 11:00 | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

---

## Alert Triggers During Monitoring

If ANY of these occur, **immediately escalate**:

| Trigger | Action | Severity |
|---------|--------|----------|
| Scheduler stops | STOP monitoring, restart service, escalate to DevOps | **CRITICAL** |
| Error rate > 1% | Investigate, check logs, continue monitoring | HIGH |
| p95 latency > 1000ms | Review database queries, check CPU load | HIGH |
| Memory growth > 100MB/hour | Check for memory leak, may need restart | HIGH |
| 5xx error spike (>5 in hour) | Database issue? API issue? Escalate | CRITICAL |
| Database connection errors | Connection pool exhausted? Escalate | CRITICAL |
| RLS policy violation detected | Security issue! Immediate escalate | **CRITICAL** |

---

## Manual Testing Checkpoints

**During 24h window, execute these tests at 12:00, 16:00, 20:00, 04:00, 08:00 UTC:**

### Test 1: Create Schedule (Always check)
```bash
curl -X POST https://api.tenopa.co.kr/api/scheduler/schedules \
  -H "Authorization: Bearer ${PROD_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test-'$(date +%H%M)'","cron_expression":"0 * * * *","source_type":"intranet","enabled":true}'
```
- Expected: HTTP 201, valid schedule_id
- [ ] 12:00 ✓ | [ ] 16:00 ✓ | [ ] 20:00 ✓ | [ ] 04:00 ✓ | [ ] 08:00 ✓

### Test 2: Manual Trigger
```bash
# Use schedule_id from Test 1
curl -X POST https://api.tenopa.co.kr/api/scheduler/schedules/${SCHEDULE_ID}/trigger \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```
- Expected: HTTP 200, batch_id returned, batch completes within 30s
- [ ] 12:00 ✓ | [ ] 16:00 ✓ | [ ] 20:00 ✓ | [ ] 04:00 ✓ | [ ] 08:00 ✓

### Test 3: Query Batch Status
```bash
curl -X GET https://api.tenopa.co.kr/api/scheduler/batches/${BATCH_ID} \
  -H "Authorization: Bearer ${PROD_TOKEN}"
```
- Expected: HTTP 200, status = COMPLETED or RUNNING
- [ ] 12:00 ✓ | [ ] 16:00 ✓ | [ ] 20:00 ✓ | [ ] 04:00 ✓ | [ ] 08:00 ✓

---

## Metrics Collection

**Collect and record at 11:00, 15:00, 19:00, 23:00 UTC:**

```json
{
  "timestamp": "2026-04-21T11:00:00Z",
  "scheduler": {
    "uptime": "100%",
    "restarts": 0,
    "last_restart": null
  },
  "api": {
    "requests_total": 0,
    "error_4xx": 0,
    "error_5xx": 0,
    "error_rate": "0%",
    "p50_latency_ms": 0,
    "p95_latency_ms": 0,
    "p99_latency_ms": 0
  },
  "batch_processing": {
    "batches_completed": 0,
    "avg_duration_seconds": 0,
    "max_duration_seconds": 0,
    "failure_count": 0
  },
  "resource": {
    "cpu_percent": 0,
    "memory_mb": 0,
    "memory_growth_percent": 0,
    "db_connections": 0
  },
  "security": {
    "unauthorized_attempts": 0,
    "rls_violations": 0
  }
}
```

---

## Go/No-Go Decision Matrix (2026-04-22 11:30 UTC)

### ✅ GO TO PRODUCTION if:
- [ ] Scheduler uptime ≥ 99.9%
- [ ] Error rate < 0.5% throughout
- [ ] p95 latency < 500ms sustained
- [ ] No memory leaks detected
- [ ] No CRITICAL/ERROR logs
- [ ] All 6 API endpoints working
- [ ] RLS policies enforced
- [ ] Database integrity verified
- [ ] All manual tests passed

**→ Proceed with 2026-04-25 Production Deployment**

### ⚠️ ESCALATE if:
- [ ] Any ONE metric out of spec
- [ ] Intermittent errors detected
- [ ] Performance degradation over time
- [ ] Warnings in critical areas

**→ Investigate root cause, extend monitoring, reassess**

### ❌ NO-GO if:
- [ ] Scheduler stopped during window
- [ ] Error rate > 1%
- [ ] p95 latency > 1000ms
- [ ] Memory leak confirmed
- [ ] Any CRITICAL logs found
- [ ] RLS policy violation
- [ ] Database corruption

**→ Rollback staging, root cause analysis, reschedule production**

---

## Escalation Contacts

| Role | Name | Contact | When |
|------|------|---------|------|
| On-Call | [Name] | [Slack/Phone] | Any CRITICAL trigger |
| DevOps Lead | [Name] | [Slack/Phone] | Deployment decision required |
| Backend Lead | [Name] | [Slack/Phone] | Technical investigation |
| CTO | [Name] | [Slack/Phone] | Final Go/No-Go approval |

---

## Notes & Issues Log

| Time | Issue | Impact | Action | Resolution |
|------|-------|--------|--------|------------|
| — | — | — | — | — |

---

**Status**: 🔄 MONITORING IN PROGRESS  
**Last Updated**: 2026-04-21 11:00 UTC  
**Next Review**: Every 4 hours  
**Final Decision**: 2026-04-22 11:30 UTC
