# STEP 8 Post-Deployment Monitoring Checklist

**Deployment Date**: 2026-05-01  
**Monitoring Period**: 2026-05-01 11:30 UTC - 2026-05-02 11:30 UTC  
**Production Decision**: 2026-05-02 11:30 UTC

---

## Daily Monitoring (Hourly Checks)

### Endpoint Health (Every Hour)
```bash
# Health check
curl -s https://staging.tenopa.app/api/health | jq .

# Response should be:
{
  "status": "healthy",
  "uptime_seconds": XXXX,
  "version": "1.0.0"
}
```

**Check Every Hour**:
- [ ] 09:30 UTC (1h post-deployment)
- [ ] 10:30 UTC (2h post-deployment)
- [ ] 11:30 UTC (3h post-deployment)
- [ ] 12:30 UTC (4h post-deployment)
- [ ] 13:30 UTC (5h post-deployment)
- [ ] 14:30 UTC (6h post-deployment)
- [ ] 15:30 UTC (7h post-deployment)
- [ ] 16:30 UTC (8h post-deployment)
- [ ] 17:30 UTC (9h post-deployment)
- [ ] 18:30 UTC (10h post-deployment)
- [ ] 19:30 UTC (11h post-deployment)
- [ ] 20:30 UTC (12h post-deployment)
- [ ] 21:30 UTC (13h post-deployment)
- [ ] 22:30 UTC (14h post-deployment)
- [ ] 23:30 UTC (15h post-deployment)
- [ ] 00:30 UTC (16h post-deployment)
- [ ] 01:30 UTC (17h post-deployment)
- [ ] 02:30 UTC (18h post-deployment)
- [ ] 03:30 UTC (19h post-deployment)
- [ ] 04:30 UTC (20h post-deployment)
- [ ] 05:30 UTC (21h post-deployment)
- [ ] 06:30 UTC (22h post-deployment)
- [ ] 07:30 UTC (23h post-deployment)
- [ ] 08:30 UTC (24h post-deployment) ← Final validation
- [ ] 09:30 UTC (25h post-deployment)

---

### Key Metrics to Monitor

#### 1. API Response Times
```
Target: P95 < 500ms, P99 < 1000ms

✅ PASS if:
  - POST /api/jobs: p95 < 500ms
  - GET /api/jobs/{id}: p95 < 100ms
  - GET /api/jobs: p95 < 100ms
  - WebSocket upgrade: < 200ms
  
⚠️ WARN if:
  - Any endpoint p95 between 500-1000ms
  - Degradation trend visible
  
❌ FAIL if:
  - Any endpoint p95 > 1000ms
  - Consistent degradation over 1 hour
```

#### 2. Error Rates
```
Target: < 0.5%

✅ PASS if:
  - Error rate < 0.5% overall
  - No 5xx errors
  - Max 1% 4xx errors (expected validation failures)
  
⚠️ WARN if:
  - Error rate between 0.5-1%
  - Isolated 5xx spikes (< 1 minute)
  
❌ FAIL if:
  - Error rate > 1%
  - Sustained 5xx errors (> 5 minutes)
  - Pattern of cascading failures
```

#### 3. Job Success Rate
```
Target: > 99.5%

Track from job creation to completion:
  - Total jobs submitted: XXXX
  - Jobs completed: XXXX
  - Jobs succeeded: XXXX
  - Jobs failed: XXXX
  - Success rate: XX.X%

✅ PASS if: > 99.5%
⚠️ WARN if: 99.0-99.5%
❌ FAIL if: < 99.0%
```

#### 4. Resource Utilization
```
✅ CPU: < 40%
✅ Memory: < 60% (1.5GB limit on Railway)
✅ Redis Memory: < 500MB
✅ DB Connection Pool: < 80% (8/10 active)
✅ Disk I/O: < 20%

⚠️ WARN if: Approaching limits
❌ FAIL if: Exceeding limits
```

#### 5. Worker Pool Health
```
Target: All 5 workers healthy

Track:
  - Worker-0: Status (UP/DOWN)
  - Worker-1: Status (UP/DOWN)
  - Worker-2: Status (UP/DOWN)
  - Worker-3: Status (UP/DOWN)
  - Worker-4: Status (UP/DOWN)
  
✅ PASS if: All 5 UP
⚠️ WARN if: 1 DOWN (recovers within 5 min)
❌ FAIL if: >1 DOWN or persistent DOWN
```

#### 6. Queue Depth
```
Target: < 100 pending jobs at any time

✅ PASS if: Avg pending < 100, Peak < 500
⚠️ WARN if: Avg pending > 100 OR Peak > 500
❌ FAIL if: Sustained > 1000 pending (queue overwhelmed)
```

---

### Hourly Report Template

**Time: [HH:MM UTC] (Post-Deployment: [Xh])**

```
API Response Times:
  - POST /api/jobs (p95): XXXms ✅/⚠️/❌
  - GET /api/jobs/{id} (p95): XXms ✅/⚠️/❌
  - WebSocket (p95): XXms ✅/⚠️/❌

Error Rates:
  - Overall: X.XX% ✅/⚠️/❌
  - 4xx: X.XX% ✅/⚠️/❌
  - 5xx: X.XX% ✅/⚠️/❌

Job Success:
  - Total Submitted: XXX
  - Success Rate: XX.X% ✅/⚠️/❌

Resources:
  - CPU: XX% ✅/⚠️/❌
  - Memory: XX% (XXXmb/1500mb) ✅/⚠️/❌
  - Redis: XX% (XXXmb) ✅/⚠️/❌

Worker Pool:
  - Healthy Workers: X/5 ✅/⚠️/❌
  - Queue Depth: XXX pending ✅/⚠️/❌

Status: ✅ NOMINAL / ⚠️ DEGRADED / ❌ CRITICAL

Notes: [Any observations, anomalies, or actions taken]
```

---

## Critical Alerts (Should NOT Occur)

If ANY of these conditions occur, escalate immediately:

### 🚨 CRITICAL: Service Down
```
Condition: /api/health returns 5xx or timeout
Action:
  1. Check Railway deployment status
  2. Review application logs
  3. Check database connectivity
  4. Initiate rollback if unrecoverable
```

### 🚨 CRITICAL: Error Rate > 5%
```
Condition: Error rate sustained > 5% for > 5 minutes
Action:
  1. Check error logs for pattern
  2. Review recent code changes
  3. Check database for issues
  4. Consider rollback
```

### 🚨 CRITICAL: Job Success Rate < 90%
```
Condition: < 90% of jobs successfully complete
Action:
  1. Check worker logs
  2. Review job payloads
  3. Check database constraints
  4. Consider rollback
```

### 🚨 CRITICAL: Memory Leak
```
Condition: Memory usage increasing > 10% per hour consistently
Action:
  1. Check for connection leaks
  2. Review Redis usage
  3. Check job result cleanup
  4. Restart service if needed
```

### 🚨 CRITICAL: Database Connection Exhaustion
```
Condition: Connection pool > 90% for > 5 minutes
Action:
  1. Check for connection leaks
  2. Kill idle connections if safe
  3. Check database query performance
  4. Consider scaling
```

### 🚨 CRITICAL: Worker Crashes
```
Condition: > 1 worker down simultaneously
Action:
  1. Check worker logs
  2. Review job payloads
  3. Check system resources
  4. Consider rollback
```

---

## Production Go/No-Go Criteria

**After 24-hour monitoring period (2026-05-02 11:30 UTC), validate:**

### Must-Have Criteria (ALL required for GO)
- [ ] Error rate < 0.5% throughout period
- [ ] P95 latency consistently < 500ms
- [ ] Job success rate > 99.5%
- [ ] No sustained 5xx errors
- [ ] No worker crashes
- [ ] No memory/connection leaks detected
- [ ] All RLS policies enforced
- [ ] No data consistency issues

### Should-Have Criteria (Most required)
- [ ] Peak response time < 2000ms
- [ ] Resource usage < 80% of limits
- [ ] Queue depth always < 1000 pending
- [ ] No cascading failures observed
- [ ] Monitoring dashboards working

### Nice-to-Have Criteria
- [ ] Performance improved over baseline
- [ ] Cache hit rate > 85%
- [ ] No unexpected behavior patterns
- [ ] User feedback positive (if available)

---

## Decision Logic

```
IF (all Must-Have criteria passed):
  DECISION = GO FOR PRODUCTION ✅
  NEXT_ACTION = Deploy to production on 2026-05-02
  
ELIF (all critical alerts < 3 AND Must-Have mostly passed):
  DECISION = GO WITH CAUTION 🟡
  NEXT_ACTION = Extended monitoring (48 hours) + fix known issues
  
ELSE:
  DECISION = NO-GO FOR PRODUCTION ❌
  NEXT_ACTION = Rollback + root cause analysis
```

---

## Contact & Escalation

**Monitoring Owner**: AI Coworker  
**Review Schedule**: Hourly during monitoring period  
**Escalation**: If any CRITICAL alert triggered

**Production Decision Meeting**: 2026-05-02 11:30 UTC  
**Participants**: Product Team, Engineering Lead, DevOps

---

## Sign-Off

**Monitoring Started**: 2026-05-01 11:30 UTC  
**Monitoring Ends**: 2026-05-02 11:30 UTC  
**Production Go/No-Go Decision**: 2026-05-02 11:30 UTC

This checklist will be filled out continuously over the 24-hour period.

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-01
