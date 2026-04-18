# STEP 4A Staging Deployment Procedure

**Date:** 2026-04-19  
**Target Window:** 2026-04-22 ~ 2026-04-24  
**Environment:** Staging  
**Go-Live Target:** 2026-04-25

---

## Pre-Deployment Checklist (2026-04-21)

### Code Verification
- [ ] All commits pushed to main branch
- [ ] Latest code pulled into staging environment
- [ ] No uncommitted changes
- [ ] Environment variables configured (.env.staging)
- [ ] Database connection string points to staging DB

### Dependencies & Build
- [ ] `uv sync` executed successfully
- [ ] All Python dependencies installed
- [ ] No import errors detected
- [ ] Build passes without warnings
- [ ] Type checking passes (if mypy/pyright configured)

### Configuration Review
- [ ] SUPABASE_URL set to staging instance
- [ ] CLAUDE_API_KEY configured
- [ ] Database migrations staged
- [ ] Logging level set to DEBUG
- [ ] Error tracking enabled (Sentry/similar)

---

## Staging Deployment Steps (2026-04-22)

### 1. Database Preparation (09:00 KST)
```bash
# Create backup of staging database
pg_dump staging_db > backup_2026-04-22.sql

# Apply migrations
alembic upgrade head
# or
uv run python -m scripts.migrate_staging

# Verify feedback_entry table
SELECT * FROM feedback_entries LIMIT 1;
```

**Verification:**
- [ ] Backup file created and tested
- [ ] All migrations applied successfully
- [ ] feedback_entry table exists with correct schema
- [ ] RLS policies configured
- [ ] Indexes created

### 2. Application Deployment (10:00 KST)
```bash
# Stop current application
systemctl stop tenopa-staging
# or
pkill -f "uvicorn app.main"

# Deploy new code
cd /opt/tenopa-staging
git pull origin main
uv sync

# Start application
systemctl start tenopa-staging
# or
nohup uv run uvicorn app.main:app --reload &
```

**Verification:**
- [ ] Application started without errors
- [ ] No startup exceptions in logs
- [ ] Health check endpoint responds (GET /)
- [ ] Database connection established

### 3. API Endpoint Verification (10:30 KST)

Test new STEP 4A endpoints:
```bash
# Latency endpoints
curl http://staging.tenopa.co.kr/api/metrics/harness-latency
curl http://staging.tenopa.co.kr/api/metrics/harness-latency-history?limit=10

# CSV export endpoints
curl http://staging.tenopa.co.kr/api/metrics/export/metrics.csv -o metrics.csv
curl http://staging.tenopa.co.kr/api/metrics/export/latency.csv -o latency.csv
curl http://staging.tenopa.co.kr/api/metrics/export/info

# Existing endpoints (sanity check)
curl http://staging.tenopa.co.kr/api/health
curl http://staging.tenopa.co.kr/api/proposals
```

**Verification Checklist:**
- [ ] All endpoints return HTTP 200
- [ ] CSV files download successfully
- [ ] Export info endpoint returns correct format documentation
- [ ] No 500 errors in application logs
- [ ] Response times within expected ranges (<2s for metrics endpoints)

---

## Performance Testing Phase (2026-04-22 ~ 2026-04-23)

### Generate Test Proposals (2026-04-22 14:00 KST)

Create 50+ test proposals to exercise STEP 4A features:
```bash
python << 'ENDSCRIPT'
import requests
import time

BASE_URL = "http://staging.tenopa.co.kr/api"
HEADERS = {"Authorization": f"Bearer {STAGING_TOKEN}"}

test_proposals = [
    {
        "title": f"Test Proposal {i}",
        "rfp_content": "Sample RFP content for testing",
        "section_count": 5
    }
    for i in range(50)
]

for prop in test_proposals:
    response = requests.post(
        f"{BASE_URL}/proposals",
        json=prop,
        headers=HEADERS
    )
    print(f"Created proposal: {response.json()['id']}")
    time.sleep(1)  # Rate limiting
ENDSCRIPT
```

**Monitoring During Load:**
- [ ] Memory usage stays below 80%
- [ ] CPU usage below 70%
- [ ] Database connections within limit
- [ ] No timeout errors
- [ ] Latency metrics being recorded

### Latency Analysis (2026-04-22 16:00 KST)

```bash
# Export latency metrics
curl http://staging.tenopa.co.kr/api/metrics/export/latency.csv \
  -o /tmp/staging_latency_2026-04-22.csv

# Analyze results
python << 'ANALYSIS'
import pandas as pd
import numpy as np

df = pd.read_csv('/tmp/staging_latency_2026-04-22.csv')

# Calculate percentiles
stats = {
    'count': len(df),
    'avg_total_ms': df['Total Section (ms)'].mean(),
    'p50': df['Total Section (ms)'].quantile(0.50),
    'p95': df['Total Section (ms)'].quantile(0.95),
    'p99': df['Total Section (ms)'].quantile(0.99),
    'max': df['Total Section (ms)'].max(),
    'min': df['Total Section (ms)'].min()
}

print("LATENCY STATISTICS (ms)")
print("-" * 40)
for key, val in stats.items():
    print(f"{key}: {val:.2f}")

# Check against target
target = 21000  # 21 seconds in ms
pct_under_target = (df['Total Section (ms)'] < target).sum() / len(df) * 100
print(f"\nSections under {target}ms: {pct_under_target:.1f}%")
print(f"Target: 100% (P95 < 22s)")
ANALYSIS
```

**Expected Results:**
- Average latency: 15-18 seconds
- P95 latency: <22 seconds (target: <21s)
- P99 latency: <25 seconds
- 100% of sections under 25s timeout

**Acceptance Criteria:**
- [ ] P95 latency < 22 seconds
- [ ] 100% of sections complete (no timeouts)
- [ ] No memory leaks detected
- [ ] No database connection exhaustion

### CSV Export Validation (2026-04-22 17:00 KST)

Test CSV exports:
```bash
# Download both CSVs
curl http://staging.tenopa.co.kr/api/metrics/export/metrics.csv \
  -o /tmp/staging_metrics.csv
curl http://staging.tenopa.co.kr/api/metrics/export/latency.csv \
  -o /tmp/staging_latency.csv

# Verify formatting
python << 'VERIFY'
import csv

# Check metrics.csv
with open('/tmp/staging_metrics.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    expected_headers = [
        'Timestamp', 'Section ID', 'Proposal ID', 'Confidence', 'Score',
        'Ensemble Applied', 'Feedback Triggered', 'Feedback Improved'
    ]
    assert headers == expected_headers, f"Headers mismatch: {headers}"
    row_count = sum(1 for row in reader)
    print(f"Metrics CSV: {row_count} rows, headers OK")

# Check latency.csv
with open('/tmp/staging_latency.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    expected_headers = [
        'Timestamp', 'Section ID', 'Proposal ID',
        'Variant Generation (ms)', 'Ensemble Voting (ms)',
        'Feedback Loop (ms)', 'Total Section (ms)'
    ]
    assert headers == expected_headers, f"Headers mismatch: {headers}"
    row_count = sum(1 for row in reader)
    print(f"Latency CSV: {row_count} rows, headers OK")
VERIFY
```

**Validation Checklist:**
- [ ] Both CSV files downloadable
- [ ] Column headers correct
- [ ] Data properly encoded (UTF-8-sig)
- [ ] Numbers parse as floats without errors
- [ ] Timestamps are valid ISO format
- [ ] Files open in Excel/Google Sheets without issues

---

## Feedback Process Testing (2026-04-23)

### Manual Feedback Collection (09:00 KST)

Create manual feedback entries:
```sql
INSERT INTO feedback_entries (
    proposal_id, section_id, section_type, user_decision,
    reason, rating_hallucination, rating_persuasiveness,
    rating_completeness, rating_clarity, created_at, weight_version
) VALUES (
    'prop-test-001', 'exec_summary', 'executive_summary', 'APPROVE',
    'Well written and persuasive', 5, 5, 5, 5, NOW(), 1
),
(
    'prop-test-002', 'tech_detail', 'technical_details', 'REJECT',
    'Missing technical depth', 3, 3, 2, 4, NOW(), 1
),
(
    'prop-test-003', 'team_sec', 'team', 'APPROVE',
    'Good team structure', 4, 4, 4, 5, NOW(), 1
);
```

### Feedback Analysis Test (10:00 KST)

Test FeedbackAnalyzer:
```bash
python << 'TEST'
from app.services.feedback_analyzer import FeedbackAnalyzer

# Create analyzer
analyzer = FeedbackAnalyzer()

# Load test feedback
test_feedback = [
    {
        "section_type": "executive_summary",
        "decision": "APPROVE",
        "reason": "Well written",
        "ratings": {
            "hallucination": 5,
            "persuasiveness": 5,
            "completeness": 5,
            "clarity": 5
        }
    },
    {
        "section_type": "technical_details",
        "decision": "REJECT",
        "reason": "Too shallow",
        "ratings": {
            "hallucination": 3,
            "persuasiveness": 3,
            "completeness": 2,
            "clarity": 4
        }
    }
]

# Analyze
analysis = analyzer.analyze_weekly_feedback(test_feedback)
print(analysis)

# Generate report
report = analyzer.get_feedback_analysis_report(test_feedback)
print(report)
TEST
```

**Verification:**
- [ ] FeedbackAnalyzer runs without errors
- [ ] Statistics calculated correctly
- [ ] Weight recommendations generated
- [ ] Reports formatted properly

### Google Sheets Integration (11:00 KST)

1. Create test Google Sheet (staging-metrics-test)
2. Import CSV data:
   - File → Import → CSV file upload
   - Metrics CSV data imported
   - Latency CSV data imported

3. Create pivot tables:
   - Section type analysis
   - Confidence distribution
   - Latency percentiles

**Verification:**
- [ ] Google Sheet created
- [ ] CSV imports successful
- [ ] Pivot tables functional
- [ ] Charts display correctly

---

## Smoke Tests (2026-04-23 14:00 KST)

Run final verification suite:

```bash
# API Health
curl -f http://staging.tenopa.co.kr/api/health || echo "FAIL: Health check"

# Proposal Creation
PROP_ID=$(curl -s -X POST http://staging.tenopa.co.kr/api/proposals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Smoke Test","rfp_content":"Test"}' \
  | jq -r '.id')
[ -n "$PROP_ID" ] && echo "PASS: Created proposal $PROP_ID" || echo "FAIL: Create proposal"

# Latency Endpoint
curl -f http://staging.tenopa.co.kr/api/metrics/harness-latency > /dev/null && \
  echo "PASS: Latency metrics endpoint" || echo "FAIL: Latency metrics"

# CSV Export
curl -f http://staging.tenopa.co.kr/api/metrics/export/metrics.csv > /dev/null && \
  echo "PASS: CSV export endpoint" || echo "FAIL: CSV export"

# Feedback Collection (if feedback UI available)
# curl -f -X POST http://staging.tenopa.co.kr/api/proposals/$PROP_ID/feedback \
#   -H "Content-Type: application/json" \
#   -d '{"decision":"APPROVE","ratings":{"hallucination":5}}' && \
#   echo "PASS: Feedback collection" || echo "FAIL: Feedback collection"

echo "Smoke tests complete"
```

---

## Sign-Off & Approval (2026-04-24 EOD)

### Final Review Meeting (14:00 KST)

Attendees:
- [ ] Tech Lead
- [ ] QA Lead  
- [ ] DevOps Engineer
- [ ] Product Manager

Review Items:
- [ ] All 3 gaps implemented and working
- [ ] Performance meets targets (latency <21s)
- [ ] CSV exports functional
- [ ] Feedback process ready
- [ ] Zero critical issues remaining
- [ ] Rollback plan reviewed and approved

### Go/No-Go Decision

**Decision:** ☐ GO / ☐ NO-GO

**Approved By:** _________________ (Tech Lead)

**Conditions (if any):** 

---

## Staging to Production Handoff (2026-04-25)

Once approved:
1. Tag production release: `v4.1-step4a-act-complete`
2. Prepare production deployment script
3. Schedule production deployment window (09:00 KST)
4. Notify stakeholders
5. Execute STEP4A_PRODUCTION_DEPLOYMENT_CHECKLIST.md

---

**Document Version:** 1.0  
**Created:** 2026-04-19  
**Next Update:** 2026-04-22 (Pre-staging deployment review)
