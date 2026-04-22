# Phase 5 Scheduler Integration — Production Monitoring Plan

**Deployment Date:** 2026-04-25 10:00 UTC  
**Monitoring Duration:** 72 hours (3 days)  
**Critical Window:** First 3 hours (continuous monitoring)  
**Alert Contacts:** [On-call Engineer] / [Deployment Lead]

---

## 📊 Monitoring Phases

### Phase 1: Intensive Monitoring (0-3 hours, 10:00 - 13:00 UTC)

**Interval:** Every 5 minutes  
**Responsible:** Deployment Lead (manual/automated checks)

#### Critical Metrics
| Metric | Target | Alert Threshold | Action |
|--------|--------|-----------------|--------|
| Error Rate | < 0.5% | > 2% for 5 min | Page on-call |
| API Latency (p95) | < 500ms | > 2000ms for 5 min | Page on-call |
| Scheduler Health | OK | 404 for 2 min | Page on-call |
| Database Connections | < 10 | > 20 | Investigate |
| Memory Usage | < 400MB | > 600MB | Investigate |
| CPU Usage | < 60% | > 85% | Investigate |

#### Monitoring Commands (Automated)
```bash
#!/bin/bash
# run every 5 minutes

# 1. Health check
curl -s https://api.tenopa.co/health | jq .

# 2. Scheduler health
curl -s https://api.tenopa.co/api/scheduler/health | jq .

# 3. Database connectivity
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co/api/scheduler/schedules | jq '.[] | .id' | wc -l

# 4. Error log count
grep -c ERROR /var/log/tenopa-api.log 2>/dev/null || echo 0

# 5. Latency percentiles (if Prometheus available)
# curl -s 'http://prometheus:9090/api/v1/query?query=http_request_duration_seconds{quantile="0.95"}' | jq
```

#### Post-Deployment Smoke Tests
```bash
#!/bin/bash
# Run once immediately after deployment

echo "=== Smoke Test Suite ==="

# 1. API Health
echo "1. Testing API health..."
curl -f https://api.tenopa.co/health || exit 1

# 2. Scheduler Health
echo "2. Testing scheduler health..."
curl -f https://api.tenopa.co/api/scheduler/health || exit 1

# 3. Database Schema
echo "3. Testing database tables..."
curl -f -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co/api/scheduler/schedules || exit 1

# 4. Unit Tests (quick subset)
echo "4. Running integration tests..."
pytest tests/integration/test_scheduler_*.py -v || exit 1

echo "✓ All smoke tests passed"
```

---

### Phase 2: Standard Monitoring (3-24 hours, 13:00 - 10:00+1 UTC)

**Interval:** Every 30 minutes  
**Responsible:** Automated monitoring system

#### Metrics
- Error rate: < 1%
- API latency: p95 < 1000ms
- Database health: responsive
- Scheduler: no 404 errors
- Memory: stable (<500MB)

#### Functional Tests
```bash
# Run every 2 hours

echo "=== Functional Test Suite ==="

# 1. Create schedule
SCHEDULE_ID=$(curl -s -X POST https://api.tenopa.co/api/scheduler/schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-schedule",
    "cron_expression": "0 12 * * *",
    "source_type": "intranet",
    "enabled": true
  }' | jq -r '.id')

echo "Created schedule: $SCHEDULE_ID"

# 2. Trigger migration
BATCH_ID=$(curl -s -X POST https://api.tenopa.co/api/scheduler/schedules/$SCHEDULE_ID/trigger \
  -H "Authorization: Bearer $TOKEN" | jq -r '.batch_id')

echo "Triggered batch: $BATCH_ID"

# 3. Check batch status
curl -s https://api.tenopa.co/api/scheduler/batches/$BATCH_ID \
  -H "Authorization: Bearer $TOKEN" | jq .

# 4. Verify database entries
# Check migration_schedules table has new entry
# Check migration_batches table has batch record
# Check migration_logs table has activity

echo "✓ Functional tests completed"
```

---

### Phase 3: Extended Monitoring (24-72 hours)

**Interval:** Every 4 hours  
**Responsible:** Automated monitoring

#### Metrics to Track
- Daily error rate trend
- API latency trend
- Scheduler job execution rate
- Database growth rate
- Resource utilization patterns

#### Weekly Validation
After 1 week:
- [ ] Zero critical errors
- [ ] Consistent performance metrics
- [ ] Scheduler executing on schedule
- [ ] No memory leaks detected
- [ ] Database schema stable
- [ ] No authentication issues

---

## 🚨 Alert Rules & Escalation

### Alert Severity Levels

#### 🔴 Critical (Page On-Call Immediately)
```
IF error_rate > 5% for 5 minutes THEN alert("Critical Error Rate")
IF api_latency_p95 > 3000ms for 5 minutes THEN alert("Critical Latency")
IF scheduler_health returns 404 for 2 minutes THEN alert("Scheduler Down")
IF database_connections > 30 THEN alert("DB Connection Pool Exhausted")
IF memory_usage > 700MB THEN alert("Memory Threshold Exceeded")
```

**Action:** Immediately start troubleshooting, consider rollback if unresolved within 10 minutes

#### 🟠 Warning (Alert Team, Check in 15 min)
```
IF error_rate > 2% for 10 minutes THEN alert("Elevated Error Rate")
IF api_latency_p95 > 1000ms for 10 minutes THEN alert("Latency Degradation")
IF cpu_usage > 80% for 10 minutes THEN alert("High CPU Usage")
```

**Action:** Investigate root cause, may require optimization

#### 🟡 Info (Log for Review)
```
IF any metric shows unusual pattern THEN log("Investigation Required")
IF migration_batches queue grows unbounded THEN log("Queue Check")
```

**Action:** Review logs daily, plan optimization if trend continues

### Escalation Chain
```
1. Initial Alert → Deployment Lead (5 min response time)
   ├─ If unresolved → Page On-Call Engineer (2 min response)
   │  ├─ If still unresolved → Initiate Rollback Procedure
   │  └─ If rollback needed → Notify stakeholders
   └─ If resolved → Document incident
```

---

## 📈 Key Performance Indicators (KPIs)

Track these metrics for success validation:

| KPI | Target | Actual (Update) | Status |
|-----|--------|---------|--------|
| Deployment Success | 100% | | |
| Time to Production Ready | < 2 hours | | |
| Error Rate (post-deploy) | < 0.5% | | |
| API Latency p95 | < 500ms | | |
| Scheduler Health Uptime | 100% | | |
| Database Integrity | 100% | | |
| Zero Rollbacks | Required | | |

---

## 📋 Monitoring Checklist

### Immediate Post-Deployment (T+0 to T+30 min)
- [ ] All health endpoints returning 200
- [ ] Scheduler service accepting requests
- [ ] Database tables created and accessible
- [ ] API authentication working
- [ ] WebSocket connections stable
- [ ] Error logs clean (< 10 errors)

### First 3 Hours (T+0 to T+3 hours)
- [ ] Smoke tests all passing
- [ ] Functional tests creating schedules successfully
- [ ] Migration batches executing
- [ ] Error rate staying < 1%
- [ ] Latency stable (p95 < 500ms)
- [ ] Memory usage stable
- [ ] No database connection issues
- [ ] No authentication failures

### 24-Hour Post-Deployment
- [ ] All 3 hours continuous monitoring successful
- [ ] Extended monitoring (24-hour) showing stable metrics
- [ ] No critical incidents
- [ ] Database growth within expected range
- [ ] Scheduler jobs completed as scheduled
- [ ] Performance SLAs met

### 72-Hour Post-Deployment
- [ ] Extended monitoring (72-hour) complete
- [ ] All metrics stable over 3-day period
- [ ] Zero trending issues identified
- [ ] Deployment sign-off completed
- [ ] Monitoring transition to standard ops
- [ ] Incident report finalized

---

## 🔧 Monitoring Tools & Access

### Prometheus (Metrics)
- URL: `http://prometheus.[prod-domain]:9090`
- Queries: `up{job="tenopa-api"}`, `rate(http_requests_total[5m])`

### Grafana (Dashboards)
- URL: `http://grafana.[prod-domain]:3000`
- Dashboards: Phase5-Scheduler-Monitoring, API-Health

### CloudWatch / ELK (Logs)
- Service: CloudWatch Logs / ELK Stack
- Log Groups: `/aws/ecs/tenopa-api-prod` (AWS) or ELK indices
- Filter: `ERROR`, `CRITICAL`, `scheduler`

### Application APM
- Tool: New Relic / DataDog (if available)
- Service: tenopa-api-production
- Key transactions: scheduler.create_schedule, scheduler.trigger_migration

### Database Monitoring
- Tool: Supabase Dashboard or pgAdmin
- Metrics: Connection count, query latency, table sizes
- Queries: `SELECT COUNT(*) FROM migration_schedules`

---

## 📞 Contact Information

Fill in before deployment:

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| Deployment Lead | [Name] | [Slack/Phone] | [Backup] |
| On-Call Engineer | [Name] | [Slack/Phone] | [Backup] |
| Database Admin | [Name] | [Slack/Phone] | [Backup] |
| Incident Commander | [Name] | [Slack/Phone] | [Backup] |

### Notification Channels
- **Slack:** #tenopa-deployment, #tenopa-incidents
- **Email:** ops-team@tenopa.co
- **PagerDuty:** (if configured)

---

## 📝 Incident Response

If critical issue detected:

1. **Assess Severity**
   - Is it data-loss risk? → Critical
   - Is scheduler broken? → Critical
   - Is API degraded? → High
   - Is it minor issue? → Medium

2. **Alert Team**
   - Post to #tenopa-incidents
   - Page on-call if critical
   - Assemble incident team

3. **Investigate**
   - Check recent logs
   - Review metrics at incident time
   - Identify root cause
   - Check recent changes

4. **Decide: Fix vs Rollback**
   - If fix < 10 minutes → Apply fix
   - If fix > 10 minutes → Initiate rollback
   - If data-loss risk → Always rollback

5. **Remediate**
   - Apply fix or rollback
   - Verify health
   - Document incident

6. **Post-Incident**
   - Write incident report
   - Root cause analysis
   - Preventive actions

---

## 📅 Monitoring Timeline

```
2026-04-25 10:00 UTC ───────────────────────────────────────── 2026-04-28 10:00 UTC
    │
    ├─ Phase 1: Intensive (0-3h)  [Every 5 min]
    │   │
    │   ├─ T+0:    Deployment complete
    │   ├─ T+5:    First health check
    │   ├─ T+30:   Smoke tests
    │   ├─ T+1h:   Functional tests begin
    │   └─ T+3h:   Phase 1 complete
    │
    ├─ Phase 2: Standard (3-24h)  [Every 30 min]
    │   │
    │   ├─ T+6h:   Functional tests (repeat)
    │   ├─ T+12h:  Performance review
    │   ├─ T+18h:  Database check
    │   └─ T+24h:  24-hour sign-off
    │
    └─ Phase 3: Extended (24-72h) [Every 4 hours]
        │
        ├─ T+48h:  48-hour review
        ├─ T+60h:  Database growth analysis
        └─ T+72h:  Final sign-off & transition to ops
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-22  
**Next Review:** 2026-04-25 (Pre-deployment final check)
