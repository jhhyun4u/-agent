# Document Ingestion — Production Deployment Plan (2026-04-25)

**Target Date**: 2026-04-25 (Wednesday)  
**Environment**: Production  
**Duration**: ~45 minutes  
**Risk Level**: LOW  
**Approval Required**: Yes

---

## Pre-Deployment Requirements (2026-04-24)

### 1. Staging Validation Complete
- [ ] Staging deployment on 2026-04-20 completed successfully
- [ ] All staging smoke tests passed
- [ ] No critical issues found in staging for 24+ hours
- [ ] Performance metrics within acceptable range

### 2. Team Approvals
- [ ] QA Lead approval: Staging validated ✅
- [ ] DevOps Lead approval: Deployment plan reviewed ✅
- [ ] Product Manager approval: Ready for production ✅
- [ ] Tech Lead approval: Code quality OK ✅

### 3. Backup & Rollback Plan
- [ ] Full database backup scheduled pre-deployment
- [ ] Previous version git hash documented: `git log --oneline -1`
- [ ] Rollback procedure tested (on non-prod database)
- [ ] Team briefed on rollback trigger criteria

### 4. Production Communication Plan
- [ ] Maintenance window announced to stakeholders
- [ ] Deployment status page prepared
- [ ] On-call team briefed and available
- [ ] Customer support aware of changes

---

## Pre-Production Deployment (2026-04-25, 08:00-08:30)

### Step 1: Final Validation
```bash
# Verify code in main branch
git log --oneline -5

# Final test run
pytest tests/test_document_ingestion.py -v --tb=short

# Check for uncommitted changes
git status
```

### Step 2: Database Backup
```bash
# Create production backup
pg_dump $PROD_DB_URL > /backups/document_ingestion_backup_2026-04-25.sql

# Verify backup
ls -lh /backups/document_ingestion_backup_2026-04-25.sql

# Test restore (on test database)
psql $TEST_DB_URL < /backups/document_ingestion_backup_2026-04-25.sql
```

### Step 3: Create Deployment Tag
```bash
# Create annotated tag for this deployment
git tag -a v-document-ingestion-2026-04-25 \
  -m "Production deployment of document_ingestion feature - 99% design alignment, 51/51 tests"

# Push tag
git push origin v-document-ingestion-2026-04-25
```

---

## Production Deployment (2026-04-25, 09:00-09:45)

### Phase A: Code Deployment (10 mins)

**Option A: Blue-Green Deployment (Recommended)**
```bash
# 1. Pull latest code
git pull origin main

# 2. Build new docker image
docker build -t tenopa-api:v-document-ingestion-2026-04-25 .

# 3. Start green environment with new image
docker-compose -f docker-compose.prod.yml up -d api-green

# 4. Run health checks on green
curl http://api-green:8000/health

# 5. Switch load balancer (zero-downtime)
# - Update nginx/LB config to route to green
# - Verify blue still running as fallback

# 6. Monitor traffic on green (5 mins)
# - Check response times
# - Check error rate
# - Check resource usage

# 7. Stop blue environment
docker-compose -f docker-compose.prod.yml down api-blue
```

**Option B: Standard Rolling Deployment**
```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
uv sync

# 3. Deploy using your deployment tool
./scripts/deploy-production.sh

# 4. Verify services restarted
systemctl status tenopa-api
docker ps | grep tenopa-api
```

### Phase B: Health Checks (10 mins)

```bash
# 1. API Health
curl -X GET https://api.tenopa.co.kr/health
# Expected: 200 OK + {"status": "healthy"}

# 2. Database Connection
curl -X GET https://api.tenopa.co.kr/api/documents \
  -H "Authorization: Bearer $PROD_AUTH_TOKEN"
# Expected: 200 OK + document list (empty or populated)

# 3. Document Upload Test
curl -X POST https://api.tenopa.co.kr/api/documents/upload \
  -F "file=@test.pdf" \
  -F "doc_type=보고서" \
  -H "Authorization: Bearer $PROD_AUTH_TOKEN"
# Expected: 201 Created + document_id

# 4. Check Logs
# - No ERROR level logs in last 5 minutes
# - No exceptions or stack traces
# - Normal processing pipeline activity
```

### Phase C: Performance Validation (10 mins)

- [ ] Response time <500ms (p95)
- [ ] Error rate <1%
- [ ] Database queries <100ms (p95)
- [ ] CPU usage <70%
- [ ] Memory usage <80%
- [ ] Disk usage <85%

### Phase D: Monitoring & Alerts (5 mins)

```bash
# Verify monitoring is active
curl https://prometheus.tenopa.co.kr/api/v1/targets

# Check Grafana dashboards
# - API Response Times
# - Error Rates
# - Database Performance
# - Resource Usage

# Verify AlertManager is configured
curl https://alertmanager.tenopa.co.kr/api/v1/alerts

# Verify log aggregation working
# - Check ELK stack for application logs
# - Verify Supabase logs accessible
```

---

## Post-Production Deployment (2026-04-25, 09:45+)

### Hour 1: Intensive Monitoring

**Frequency**: Every 1-2 minutes

Metrics:
- ✅ API response time (target: <500ms)
- ✅ Error rate (target: <1%)
- ✅ Request throughput
- ✅ Database connection pool
- ✅ Supabase Storage operations
- ✅ Authentication success rate

Actions:
- Monitor real-time dashboards
- Watch application logs
- Watch infrastructure metrics
- Team on standby for immediate rollback

### Hours 2-4: Enhanced Monitoring

**Frequency**: Every 5 minutes

Focus:
- Document processing pipeline
- Embedding generation (if applicable)
- Chunk creation and storage
- User action patterns
- Any anomalies or warnings

### Hours 4+: Standard Monitoring

**Frequency**: Every 15 minutes

Daily validation:
- Total documents processed
- Average processing time
- Success rate ≥99%
- No critical errors
- All components healthy

---

## Rollback Decision Criteria

### 🔴 CRITICAL — Rollback Immediately
- API response time >5s consistently
- Error rate >10%
- Database inaccessible
- Authentication broken
- File upload failing completely

### 🟡 WARNING — Evaluate Rollback
- API response time >2s (sustained)
- Error rate 5-10%
- Specific endpoints slow
- Minor features broken
- Intermittent database issues

### 🟢 OK — Continue Monitoring
- API response time <500ms
- Error rate <1%
- All endpoints responding
- No user reports
- Metrics stable

---

## Rollback Procedure (If Needed)

### Immediate Actions
```bash
# 1. Switch load balancer back to blue (if using blue-green)
# OR stop current deployment

# 2. Restore previous version
git checkout $(git rev-list --tags --max-count=1 --before="2026-04-25" --sort=-version:refname)

# 3. Rebuild and redeploy
./scripts/deploy-production.sh

# 4. Verify health
curl https://api.tenopa.co.kr/health
```

### Post-Rollback
```bash
# Check database integrity
psql $PROD_DB_URL -c "SELECT COUNT(*) FROM intranet_documents;"

# Verify no data loss
psql $PROD_DB_URL -c "SELECT MAX(updated_at) FROM intranet_documents;"

# Send rollback notification
# Email team and stakeholders
```

---

## Communication Timeline

### 2026-04-25 08:45
```
Slack #production: STARTING Document Ingestion production deployment.
Window: ~45 minutes. May have brief latency spikes.
Monitoring active. Team on standby.
```

### 2026-04-25 09:30
```
Slack #production: Deployment code changes complete.
Health checks in progress. Monitoring metrics...
```

### 2026-04-25 09:45
```
Slack #production: ✅ Document Ingestion successfully deployed to production.
All health checks passed. Normal monitoring continues.
Full report to follow.
```

### 2026-04-25 17:00
```
Slack #product: Document Ingestion feature now live in production.
Improved document processing pipeline deployed.
24-hour monitoring shows stable performance.
```

---

## Post-Deployment Report

### Generate 24-Hour Report (2026-04-26 09:00)

Metrics to include:
- Uptime percentage
- Average response times
- Error rates
- Documents processed
- Peak load handled
- Any issues encountered
- User feedback

Report location: `/reports/document_ingestion_prod_deployment_2026-04-25.md`

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Deployment Time | <1 hour | ☐ |
| Health Checks | 100% pass | ☐ |
| API Availability | ≥99.9% | ☐ |
| Response Time p95 | <500ms | ☐ |
| Error Rate | <1% | ☐ |
| Document Processing | ≥99% success | ☐ |
| No critical issues | 0 | ☐ |
| Team feedback | Positive | ☐ |

---

## Sign-Off

**Pre-Deployment Approvals**

| Role | Name | Date | Sign-Off |
|------|------|------|----------|
| QA Lead | - | 2026-04-24 | ☐ |
| DevOps Lead | - | 2026-04-24 | ☐ |
| Product Manager | - | 2026-04-24 | ☐ |
| Tech Lead | - | 2026-04-24 | ☐ |

**Deployment Status:** 🟢 SCHEDULED FOR 2026-04-25

---

**Prepared**: 2026-04-18  
**Scheduled**: 2026-04-25 09:00 UTC  
**Environment**: Production  
**Expected Duration**: ~45 minutes  
**Rollback Available**: Yes (git tag: v-document-ingestion-2026-04-25)
