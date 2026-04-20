# Vault Chat Phase 2 - Operations & Deployment Guide

**Version**: 1.0  
**Date**: 2026-04-20  
**Status**: Ready for Staging Deployment  
**Target Go-Live**: 2026-05-08 (Production)

---

## Table of Contents

1. [Deployment Checklist](#deployment-checklist)
2. [Configuration & Setup](#configuration--setup)
3. [Operational Procedures](#operational-procedures)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedures](#rollback-procedures)
7. [FAQ](#faq)

---

## Deployment Checklist

### Pre-Staging Deployment (2026-04-25, T-3 days)

- [ ] **Code Review Complete**
  - [ ] All 7 components reviewed
  - [ ] No security vulnerabilities found
  - [ ] Code quality score > 90%

- [ ] **Testing Validation**
  - [ ] Unit tests: 39/39 passing
  - [ ] Integration tests: 40+ passing
  - [ ] Performance benchmarks: All targets met
  - [ ] E2E tests: 14 tests updated and passing

- [ ] **Environment Setup**
  - [ ] Staging Supabase instance provisioned
  - [ ] Redis cache cluster configured
  - [ ] SSL certificates validated
  - [ ] Staging domain configured

- [ ] **Configuration Ready**
  - [ ] Environment variables set for staging
  - [ ] API secrets rotated and secured
  - [ ] Database migrations tested
  - [ ] Webhook URLs configured

- [ ] **Documentation Complete**
  - [ ] Operations guide finalized
  - [ ] Runbook for common issues created
  - [ ] Deployment procedure documented
  - [ ] Team trained on Vault features

### Staging Deployment (2026-05-01, Go Date)

**Timing**: 09:00 UTC (18:00 KST)  
**Duration**: 2-3 hours  
**Teams**: 3 engineers, 1 product manager, 1 on-call

**Steps**:
1. [ ] Database backup created
2. [ ] Migrations applied to staging
3. [ ] Service instances started
4. [ ] Smoke tests passed
5. [ ] User scenario tests passed
6. [ ] Monitoring confirmed active
7. [ ] Team notified of go-live
8. [ ] 24-hour monitoring begins

### Production Deployment (2026-05-08, Canary Release)

**Week 1: Canary (10%)**
- [ ] 10% of teams on Vault Chat Phase 2
- [ ] Baseline metrics collected
- [ ] Error rate monitored < 0.1%
- [ ] Daily health check

**Week 2: Increase to 50%**
- [ ] Add 40% more teams
- [ ] Monitor for latency issues
- [ ] Check cache hit rates
- [ ] Verify webhook delivery

**Week 3: Full Rollout (100%)**
- [ ] Enable for all teams
- [ ] Final monitoring period
- [ ] Document lessons learned
- [ ] Plan Phase 3 features

---

## Configuration & Setup

### Environment Variables

**Required for Staging**:
```bash
# Database
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_KEY=[anon-key]
SUPABASE_SERVICE_ROLE_KEY=[service-role-key]

# Cache
REDIS_URL=redis://[host]:[port]
REDIS_TTL_SECONDS=3600

# Claude API
ANTHROPIC_API_KEY=[api-key]
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Teams Bot
TEAMS_BOT_ID=[bot-id]
TEAMS_TEAMS_ENDPOINT=https://outlook.webhook.office.com

# G2B API
G2B_API_KEY=[api-key]
G2B_API_URL=https://api.g2b.go.kr

# Monitoring
DATADOG_API_KEY=[api-key]
LOG_LEVEL=INFO
```

### Database Configuration

**Required Tables**:
```sql
-- Teams Bot Configuration
CREATE TABLE IF NOT EXISTS teams_bot_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id TEXT NOT NULL UNIQUE,
    bot_enabled BOOLEAN DEFAULT true,
    bot_modes TEXT[] DEFAULT ARRAY['adaptive', 'digest', 'matching'],
    webhook_url TEXT NOT NULL,
    webhook_validated_at TIMESTAMP,
    digest_time TEXT,
    digest_keywords TEXT[],
    digest_enabled BOOLEAN DEFAULT false,
    matching_enabled BOOLEAN DEFAULT false,
    matching_threshold FLOAT DEFAULT 0.75,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Chat Messages
CREATE TABLE IF NOT EXISTS vault_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- RFP Alerts
CREATE TABLE IF NOT EXISTS g2b_rfp_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    g2b_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    client TEXT,
    deadline TEXT,
    budget INTEGER,
    category TEXT,
    similarity_score FLOAT,
    priority TEXT,
    status TEXT DEFAULT 'new',
    detected_at TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now()
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS vault_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    user_role TEXT,
    component TEXT NOT NULL,
    action TEXT NOT NULL,
    duration_ms INTEGER,
    status TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT now()
);
```

### Redis Cache Configuration

**Key Prefixes**:
```
vault:search:query_hash -> Cached search results (TTL: 1h)
vault:context:user_id -> User conversation context (TTL: 8h)
vault:permission:role -> Role permissions (TTL: 24h)
vault:lang:user_id -> User language preference (TTL: 30d)
vault:performance:metric -> Performance metrics (TTL: 1h)
```

### Webhook Configuration

**Teams Webhook Setup**:

1. **Create Incoming Webhook in Teams**:
   - Navigate to channel settings
   - Click "Connectors"
   - Search for "Incoming Webhook"
   - Configure name: "Vault Chat Bot"
   - Click "Create"

2. **Register Webhook in Vault**:
   ```bash
   curl -X POST http://localhost:8000/api/vault/webhook/register \
     -H "Content-Type: application/json" \
     -d '{
       "team_id": "team_123",
       "webhook_url": "https://outlook.webhook.office.com/webhookb2/xxx/xxx",
       "webhook_modes": ["adaptive", "digest", "matching"]
     }'
   ```

3. **Test Webhook**:
   ```bash
   curl -X POST http://localhost:8000/api/vault/webhook/test \
     -H "Content-Type: application/json" \
     -d '{
       "team_id": "team_123"
     }'
   ```

---

## Operational Procedures

### Daily Operations

**Morning Checklist (08:00 KST)**:
1. [ ] Check application health
   ```bash
   curl http://localhost:8000/health
   ```

2. [ ] Verify cache hit rate
   ```bash
   curl http://localhost:8000/api/vault/metrics/cache-stats
   ```

3. [ ] Check error rates
   ```bash
   curl http://localhost:8000/api/vault/metrics/error-rate
   ```

4. [ ] Review overnight logs
   ```bash
   # Check for any warnings/errors
   tail -f logs/vault_chat.log
   ```

**Afternoon Check (14:00 KST)**:
1. [ ] Monitor G2B hourly checks (should see 08:00-18:00)
2. [ ] Check competitor tracking results
3. [ ] Verify tech trends were captured
4. [ ] Check Teams webhook delivery success rate

**End of Day (17:00 KST)**:
1. [ ] Archive daily metrics
2. [ ] Verify backups completed
3. [ ] Check for any alerts/issues
4. [ ] Prepare incident log for on-call handoff

### KB Update Procedures

**Adding Documents to Vault**:

```bash
# Manual upload via API
curl -X POST http://localhost:8000/api/vault/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@proposal.docx" \
  -F "category=completed_projects" \
  -F "section=success_cases"
```

**Batch KB Update**:
```bash
# From completed projects
curl -X POST http://localhost:8000/api/vault/kb/update-from-projects \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "project_ids": ["proj_001", "proj_002"],
    "update_type": "auto"
  }'
```

### Monitoring G2B Integration

**Manual RFP Monitoring Check**:
```bash
# Trigger G2B monitoring
curl -X POST http://localhost:8000/api/vault/g2b/monitor \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Check results
curl -X GET http://localhost:8000/api/vault/g2b/alerts?limit=10
```

**Competitor Tracking Check**:
```bash
# Trigger competitor analysis
curl -X POST http://localhost:8000/api/vault/competitors/track \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# View results
curl -X GET http://localhost:8000/api/vault/competitors/analysis
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

**Performance Metrics**:
- **Response Time (p95)**: Target < 2s, Alert if > 3s
- **Cache Hit Rate**: Target > 75%, Alert if < 60%
- **Error Rate**: Target < 0.1%, Alert if > 0.5%
- **Webhook Success Rate**: Target > 99%, Alert if < 95%

**Business Metrics**:
- **Daily Active Teams**: Should grow post-launch
- **Queries per Hour**: Baseline during office hours
- **RFP Matches**: Should find 1-3 per day
- **Competitor Wins Tracked**: Weekly summary

### Alert Conditions

```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.5%"
    severity: "critical"
    action: "Page on-call engineer"

  - name: "Cache Hit Rate Low"
    condition: "cache_hit_rate < 60%"
    severity: "warning"
    action: "Review cache configuration"

  - name: "Webhook Failures"
    condition: "webhook_success_rate < 95%"
    severity: "warning"
    action: "Check Teams webhook URLs"

  - name: "Response Time High"
    condition: "p95_latency > 3000ms"
    severity: "warning"
    action: "Check database load"

  - name: "Database Connection Failed"
    condition: "db_available = false"
    severity: "critical"
    action: "Immediate incident response"
```

### Dashboards

**Main Dashboard** (Grafana/Datadog):
- Request rate (requests/minute)
- Response time distribution (p50, p95, p99)
- Error rate
- Cache hit rate
- Webhook success rate
- Active users
- Component health

**Security Dashboard**:
- Permission violations attempted
- Sensitive data access logs
- Role-based access patterns
- Audit trail completeness

---

## Troubleshooting

### Common Issues

#### Issue 1: High Response Latency (> 3 seconds)

**Diagnosis**:
```bash
# Check database performance
SELECT query, calls, total_time FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 5;

# Check Redis connectivity
redis-cli ping

# Check Claude API latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.anthropic.com/
```

**Solutions**:
1. Increase Redis TTL if hit rate is low
2. Add database indexes on frequently queried columns
3. Check Claude API status
4. Scale up application instances if under high load

#### Issue 2: Low Cache Hit Rate (< 60%)

**Diagnosis**:
```bash
# Check cache statistics
curl http://localhost:8000/api/vault/metrics/cache-stats

# Analyze query patterns
SELECT query, COUNT(*) FROM vault_chat_messages 
GROUP BY query ORDER BY COUNT(*) DESC LIMIT 20;
```

**Solutions**:
1. Increase cache TTL for popular queries
2. Implement smarter query normalization
3. Pre-warm cache with common queries
4. Add more Redis instances if memory-bound

#### Issue 3: Webhook Delivery Failures

**Diagnosis**:
```bash
# Check webhook logs
SELECT * FROM vault_audit_logs 
WHERE component = 'teams_webhook' 
AND status = 'failed' 
ORDER BY created_at DESC LIMIT 10;

# Verify webhook URLs
curl -X GET http://localhost:8000/api/vault/teams/webhooks
```

**Solutions**:
1. Verify webhook URLs are still valid (Teams may regenerate)
2. Check Teams webhook rate limits (not exceeded)
3. Implement longer retry backoff
4. Switch to Teams Bot Framework API if webhook unstable

#### Issue 4: Permission Filter False Positives

**Diagnosis**:
```bash
# Check sensitive content detection logs
SELECT * FROM vault_audit_logs 
WHERE component = 'permission_filter' 
AND status = 'filtered'
ORDER BY created_at DESC LIMIT 20;
```

**Solutions**:
1. Review sensitive keyword list
2. Adjust keyword detection patterns
3. Add context-aware detection (not just keywords)
4. Implement manual review process for borderline cases

---

## Rollback Procedures

### Pre-Rollback Validation

Before initiating rollback:
1. Confirm error rate > 1% and persisting
2. Confirm p95 latency > 5s and persisting
3. Confirm not a temporary spike
4. Get approval from engineering lead

### Rollback Steps (Staging)

**If issues detected in staging (09:00-11:00 UTC)**:

```bash
# 1. Stop new service
kubectl scale deployment vault-chat-phase2 --replicas=0

# 2. Revert database migrations
psql -f database/migrations/rollback_latest.sql

# 3. Restore previous service
kubectl apply -f kubernetes/vault-chat-phase1.yaml

# 4. Verify health
curl http://localhost:8000/health

# 5. Notify team in Slack
# "Vault Phase 2 staging deployment rolled back - investigating issues"
```

### Rollback Steps (Production)

**If issues detected in production (Canary Phase)**:

```bash
# 1. Reduce traffic to new version
# Old: 90%, New: 10% (reverse to pre-deployment)
kubectl patch service vault-chat \
  -p '{"spec":{"selector":{"version":"phase1"}}}'

# 2. Terminate new instances
kubectl delete deployment vault-chat-phase2-prod

# 3. Monitor for stability
# Wait 5 minutes
curl http://prod-vault:8000/metrics

# 4. Post-mortem
# Schedule investigation of root cause
```

### Post-Rollback Recovery

```bash
# 1. Run diagnostics
./scripts/diagnose_rollback.sh

# 2. Fix identified issues
# Update code and redeploy with fixes

# 3. Additional testing
# - Extra unit tests for edge case
# - Longer staging period (48 hours)
# - Additional performance tests

# 4. Plan re-deployment
# Schedule for next business day with full team present
```

---

## FAQ

### Q: How often should I check the monitoring dashboard?
**A**: During business hours (08:00-18:00 KST), check every 2 hours. After hours, rely on automated alerts. First week post-launch, daily 30-min check recommended.

### Q: What should I do if I see "Webhook validation failed"?
**A**: The Teams webhook URL has likely expired or been regenerated. Re-configure the webhook URL through Teams channel settings.

### Q: How do I add a new language to MultiLang Handler?
**A**: Add the language code to VaultSection enum, update language detection regex, add translations to templates. See `app/services/vault_multilang_handler.py` for examples.

### Q: Can I manually trigger G2B monitoring?
**A**: Yes, use the API: `POST /api/vault/g2b/monitor`. Useful for testing or urgent RFP checking.

### Q: What's the process for adding a new team to Vault?
**A**: 
1. Create Teams webhook in channel
2. Call `/api/vault/teams/register` with webhook URL
3. Test with `/api/vault/teams/test-message`
4. Enable desired modes (adaptive, digest, matching)

### Q: How do I export conversation history?
**A**: 
```bash
curl -X POST http://localhost:8000/api/vault/export/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "format": "csv|json",
    "date_from": "2026-05-01",
    "date_to": "2026-05-31"
  }'
```

### Q: What happens if Claude API is down?
**A**: Graceful degradation: System returns cached responses or falls back to context-only mode. User sees message: "일시적 오류가 발생했습니다. 지난 대화를 기반으로 응답합니다."

### Q: How do I update KB with new projects?
**A**: Automatic: Projects marked as "completed" are automatically added to KB within 24 hours. Manual: `POST /api/vault/kb/add-document` with project details.

### Q: Can I test Vault features in production without affecting other teams?
**A**: Yes, use "test mode" when creating test team config. Test teams don't trigger real webhooks. Disable with: `VAULT_TEST_MODE=false` in production.

---

## Support & Escalation

**Vault Phase 2 Support Structure**:
- **Tier 1 (Immediate)**: On-call engineer (rotation-based)
- **Tier 2 (Escalation)**: Engineering lead
- **Tier 3 (Critical)**: Engineering manager + product manager

**Incident Severity**:
- **P0 (Critical)**: Service unavailable, data loss risk
- **P1 (High)**: Significant feature impact, error rate > 1%
- **P2 (Medium)**: Minor feature issues, user confusion
- **P3 (Low)**: Edge cases, cosmetic issues

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-20 | Initial release for Phase 2 |

---

## Document Control

**Document Owner**: Engineering Lead (Vault Team)  
**Last Updated**: 2026-04-20  
**Next Review**: 2026-06-01  
**Approval**: [Engineering Lead Signature]
