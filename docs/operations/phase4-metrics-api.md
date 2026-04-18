# Phase 4 Metrics API Documentation

**Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: 2026-04-18  

---

## Overview

The Phase 4 Metrics API provides real-time monitoring and analytics for the Harness Accuracy Improvement system. It enables tracking of:

- Section-level metrics (confidence, scores, ensemble application)
- Proposal-level aggregation and trends
- Latency tracking and performance analysis
- Feedback loop effectiveness measurement
- CSV export for external analysis

**Base URL**: `https://api.tenopa.co.kr/api/metrics` (Production)

---

## Authentication

All endpoints require:
- **Header**: `Authorization: Bearer <JWT_TOKEN>`
- **User Role**: Minimum `proposal_viewer` or higher
- **Project Access**: Must have access to the project associated with metrics

---

## Endpoints

### 1. Get Current Accuracy Metrics

```http
GET /api/metrics/harness-accuracy
```

**Description**: Returns current accuracy metrics for all proposals in the last 7 days.

**Response** (200 OK):
```json
{
  "status": "success",
  "current_metrics": {
    "total_sections": 45,
    "avg_score": 0.865,
    "avg_confidence": 0.78,
    "high_confidence_pct": 65.4,
    "medium_confidence_pct": 28.9,
    "low_confidence_pct": 5.7,
    "ensemble_application_rate": 93.3,
    "feedback_trigger_rate": 8.9,
    "feedback_effectiveness_rate": 72.5
  },
  "metrics_summary": {
    "precision": 0.96,
    "recall": 0.97,
    "f1_score": 0.965,
    "false_negative_pct": 3.0,
    "false_positive_pct": 4.0
  },
  "timestamp": "2026-04-18T12:34:56Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid org_id
- `401 Unauthorized`: Missing or invalid token
- `500 Internal Server Error`: Database error

---

### 2. Get Accuracy Trend Analysis

```http
GET /api/metrics/harness-accuracy-trend?days=7
```

**Parameters**:
- `days` (optional): Number of days to analyze (7 or 30, default: 7)

**Description**: Returns trend data for accuracy metrics over specified period.

**Response** (200 OK):
```json
{
  "status": "success",
  "period_days": 7,
  "trend_data": [
    {
      "date": "2026-04-11",
      "avg_score": 0.850,
      "avg_confidence": 0.76,
      "sections_count": 5,
      "f1_score": 0.960
    },
    {
      "date": "2026-04-12",
      "avg_score": 0.865,
      "avg_confidence": 0.78,
      "sections_count": 7,
      "f1_score": 0.965
    }
  ],
  "trend_summary": {
    "score_trend": "up",
    "confidence_trend": "up",
    "overall_trajectory": "improving"
  }
}
```

---

### 3. Get Deployment Readiness Status

```http
GET /api/metrics/deployment-readiness
```

**Description**: Returns deployment readiness checklist and current status.

**Response** (200 OK):
```json
{
  "status": "success",
  "deployment_ready": true,
  "checklist": {
    "all_tests_passing": {
      "status": true,
      "details": "39/39 tests passing"
    },
    "accuracy_threshold_met": {
      "status": true,
      "details": "F1-score: 0.96 (target: >= 0.92)"
    },
    "confidence_distribution": {
      "status": true,
      "details": "94.3% HIGH+MEDIUM (target: >= 70%)"
    },
    "latency_acceptable": {
      "status": true,
      "details": "P95: 18.2s (target: < 21s)"
    },
    "monitoring_configured": {
      "status": true,
      "details": "Prometheus + Grafana active"
    },
    "database_migrated": {
      "status": true,
      "details": "3 new tables created"
    }
  },
  "overall_readiness": 100,
  "timestamp": "2026-04-18T12:34:56Z"
}
```

---

### 4. Get Latency Metrics

```http
GET /api/metrics/harness-latency
```

**Description**: Returns current latency statistics for section evaluations.

**Response** (200 OK):
```json
{
  "status": "success",
  "latency_metrics": {
    "evaluation": {
      "p50_ms": 8234,
      "p95_ms": 18420,
      "p99_ms": 21890,
      "avg_ms": 9210,
      "min_ms": 2100,
      "max_ms": 25600
    },
    "variant_generation": {
      "p50_ms": 2450,
      "p95_ms": 3180,
      "p99_ms": 3890
    },
    "ensemble_voting": {
      "p50_ms": 180,
      "p95_ms": 250,
      "p99_ms": 340
    },
    "feedback_loop": {
      "p50_ms": 0,
      "p95_ms": 0,
      "p99_ms": 2100,
      "triggered_rate": 8.9
    }
  },
  "breakdown": {
    "variant_generation_pct": 41.2,
    "ensemble_voting_pct": 3.8,
    "feedback_loop_pct": 18.6,
    "other_pct": 36.4
  },
  "alerts": [],
  "timestamp": "2026-04-18T12:34:56Z"
}
```

**Alert Conditions**:
- P95 latency > 25000ms: ⚠️ WARNING
- P99 latency > 30000ms: 🚨 CRITICAL

---

### 5. Get Latency History

```http
GET /api/metrics/harness-latency-history?limit=100
```

**Parameters**:
- `limit` (optional): Number of recent records (default: 50, max: 500)
- `section_id` (optional): Filter by section ID

**Description**: Returns detailed latency records for analysis.

**Response** (200 OK):
```json
{
  "status": "success",
  "records": [
    {
      "timestamp": "2026-04-18T12:34:00Z",
      "proposal_id": "prop_001",
      "section_id": "introduction",
      "variant_generation_ms": 2450,
      "ensemble_voting_ms": 145,
      "feedback_loop_ms": 0,
      "total_ms": 2595,
      "feedback_triggered": false
    },
    {
      "timestamp": "2026-04-18T12:35:00Z",
      "proposal_id": "prop_002",
      "section_id": "approach",
      "variant_generation_ms": 2680,
      "ensemble_voting_ms": 201,
      "feedback_loop_ms": 1890,
      "total_ms": 4771,
      "feedback_triggered": true
    }
  ],
  "total_records": 2450,
  "timestamp": "2026-04-18T12:34:56Z"
}
```

---

### 6. Post Feedback Evaluation

```http
POST /api/metrics/evaluate-feedback
Content-Type: application/json
```

**Description**: Records manual feedback evaluation on a section.

**Request Body**:
```json
{
  "evaluation_id": "eval_12345",
  "section_id": "introduction",
  "section_type": "introduction",
  "user_decision": "approved",
  "reason": "Good quality, clear messaging",
  "corrected_scores": {
    "hallucination": 0.95,
    "persuasiveness": 0.92,
    "completeness": 0.94,
    "clarity": 0.96
  }
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "feedback_id": "fb_12345",
  "evaluation_id": "eval_12345",
  "timestamp": "2026-04-18T12:34:56Z",
  "message": "Feedback recorded successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input format
- `422 Unprocessable Entity`: Invalid section_type or decision value

---

### 7. Export Metrics as CSV

```http
GET /api/metrics/export/metrics.csv
```

**Description**: Downloads section metrics in CSV format for Google Sheets import.

**Response** (200 OK):
```
Content-Type: text/csv; charset=utf-8-sig
Content-Disposition: attachment; filename="metrics_2026-04-18.csv"

proposal_id,section_id,confidence,score,ensemble_applied,feedback_triggered,date
prop_001,introduction,0.85,0.88,true,false,2026-04-18
prop_001,approach,0.72,0.75,true,true,2026-04-18
prop_002,introduction,0.90,0.92,true,false,2026-04-18
```

**Features**:
- UTF-8-sig encoding (Excel compatible)
- Auto-import ready for Google Sheets
- Last 7 days of data

---

### 8. Export Latency as CSV

```http
GET /api/metrics/export/latency.csv
```

**Description**: Downloads latency records in CSV format for performance analysis.

**Response** (200 OK):
```
Content-Type: text/csv; charset=utf-8-sig
Content-Disposition: attachment; filename="latency_2026-04-18.csv"

timestamp,proposal_id,section_id,variant_generation_ms,ensemble_voting_ms,feedback_loop_ms,total_ms,feedback_triggered
2026-04-18T12:34:00Z,prop_001,introduction,2450,145,0,2595,false
2026-04-18T12:35:00Z,prop_002,approach,2680,201,1890,4771,true
```

---

### 9. Get Export Format Information

```http
GET /api/metrics/export/info
```

**Description**: Returns documentation for CSV export formats and integration guides.

**Response** (200 OK):
```json
{
  "status": "success",
  "formats": {
    "metrics.csv": {
      "fields": ["proposal_id", "section_id", "confidence", "score", "ensemble_applied", "feedback_triggered", "date"],
      "encoding": "utf-8-sig",
      "purpose": "Section-level metrics analysis",
      "google_sheets_guide": "1. Click File > Import > CSV > Select export file > Create new spreadsheet"
    },
    "latency.csv": {
      "fields": ["timestamp", "proposal_id", "section_id", "variant_generation_ms", "ensemble_voting_ms", "feedback_loop_ms", "total_ms", "feedback_triggered"],
      "encoding": "utf-8-sig",
      "purpose": "Performance and latency analysis",
      "google_sheets_guide": "1. Click File > Import > CSV > Select export file > Create new spreadsheet"
    }
  },
  "update_frequency": "real-time",
  "retention_period": "30 days"
}
```

---

## Response Format Standard

All endpoints follow this standard response format:

```json
{
  "status": "success|error",
  "data": {...},
  "error": "optional error message",
  "timestamp": "ISO-8601 timestamp"
}
```

**Status Values**:
- `success`: 200 OK
- `error`: 4xx or 5xx error codes

---

## Error Handling

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify JWT token |
| 403 | Forbidden | Check project access |
| 404 | Not Found | Verify resource ID exists |
| 429 | Too Many Requests | Wait and retry (rate limited) |
| 500 | Server Error | Contact support if persistent |

### Example Error Response

```json
{
  "status": "error",
  "error": "Invalid org_id: not_found",
  "details": {
    "code": "ORG_NOT_FOUND",
    "field": "org_id"
  },
  "timestamp": "2026-04-18T12:34:56Z"
}
```

---

## Rate Limiting

- **Per IP**: 60 requests/minute
- **Per API Key**: 1000 requests/hour
- **Retry-After**: Provided in response headers

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1713443696
```

---

## Examples

### Example 1: Get Current Metrics and Check Readiness

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co.kr/api/metrics/harness-accuracy

# Check deployment readiness
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co.kr/api/metrics/deployment-readiness
```

### Example 2: Export Data for Analysis

```bash
# Export metrics
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co.kr/api/metrics/export/metrics.csv \
  -o metrics.csv

# Import to Google Sheets:
# 1. Open Google Sheets
# 2. File > Import > Upload > Select metrics.csv
# 3. Create new spreadsheet
```

### Example 3: Monitor Latency Performance

```bash
# Get latency statistics
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.co.kr/api/metrics/harness-latency

# Get recent latency records
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.tenopa.co.kr/api/metrics/harness-latency-history?limit=100"
```

### Example 4: Record Feedback Evaluation

```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.tenopa.co.kr/api/metrics/evaluate-feedback \
  -d '{
    "evaluation_id": "eval_001",
    "section_id": "introduction",
    "section_type": "introduction",
    "user_decision": "approved",
    "reason": "Excellent quality",
    "corrected_scores": {
      "hallucination": 0.95,
      "persuasiveness": 0.92,
      "completeness": 0.94,
      "clarity": 0.96
    }
  }'
```

---

## Monitoring and Alerts

### Recommended Monitoring Metrics

1. **Accuracy Metrics**:
   - F1-score (target: >= 0.92)
   - False negative rate (target: < 5%)
   - False positive rate (target: < 8%)

2. **Confidence Distribution**:
   - HIGH + MEDIUM combined (target: >= 70%)
   - LOW percentage (alert if > 20%)

3. **Latency Performance**:
   - P95 latency (target: < 21s, alert if > 25s)
   - P99 latency (alert if > 30s)

4. **Feedback Loop**:
   - Trigger rate (target: 10-20%)
   - Effectiveness rate (target: >= 70%)

### Alert Configuration

Set up alerts for:
- Accuracy drop > 5% from baseline
- P95 latency > 25 seconds
- Low confidence rate > 20%
- Database connectivity issues

---

## Best Practices

1. **Polling Frequency**:
   - Real-time monitoring: Every 60 seconds
   - Trend analysis: Every 1 hour
   - Report generation: Daily or weekly

2. **Data Retention**:
   - Keep production metrics for 30+ days
   - Archive historical data quarterly
   - Export to long-term storage monthly

3. **Performance**:
   - Use pagination for large result sets
   - Cache trend data if polling frequently
   - Implement exponential backoff for retries

4. **Security**:
   - Store JWT tokens securely
   - Rotate API credentials monthly
   - Audit access logs regularly
   - Use HTTPS for all requests

---

## Integration Examples

### Python Client

```python
import requests
from datetime import datetime

class MetricsClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def get_accuracy_metrics(self):
        response = requests.get(
            f"{self.base_url}/harness-accuracy",
            headers=self.headers
        )
        return response.json()
    
    def get_latency_metrics(self):
        response = requests.get(
            f"{self.base_url}/harness-latency",
            headers=self.headers
        )
        return response.json()
    
    def export_metrics_csv(self, output_file):
        response = requests.get(
            f"{self.base_url}/export/metrics.csv",
            headers=self.headers
        )
        with open(output_file, 'wb') as f:
            f.write(response.content)

# Usage
client = MetricsClient("https://api.tenopa.co.kr/api/metrics", TOKEN)
metrics = client.get_accuracy_metrics()
print(f"Current F1-Score: {metrics['metrics_summary']['f1_score']}")
```

### JavaScript/Node.js Client

```javascript
class MetricsAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = { Authorization: `Bearer ${token}` };
  }

  async getAccuracyMetrics() {
    const response = await fetch(
      `${this.baseUrl}/harness-accuracy`,
      { headers: this.headers }
    );
    return response.json();
  }

  async getLatencyMetrics() {
    const response = await fetch(
      `${this.baseUrl}/harness-latency`,
      { headers: this.headers }
    );
    return response.json();
  }
}

// Usage
const api = new MetricsAPI(
  "https://api.tenopa.co.kr/api/metrics",
  TOKEN
);
const metrics = await api.getAccuracyMetrics();
console.log(`F1-Score: ${metrics.metrics_summary.f1_score}`);
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Invalid or expired JWT token  
**Solution**:
1. Verify token is valid
2. Check token hasn't expired
3. Re-authenticate and get new token

### Issue: 403 Forbidden

**Cause**: User doesn't have access to requested resource  
**Solution**:
1. Check user has correct role
2. Verify user has project access
3. Contact admin for permission grant

### Issue: Metrics Not Updating

**Cause**: Monitoring service not collecting data  
**Solution**:
1. Check harness_proposal_write.py has record_section() calls
2. Verify ensemble_metrics_monitor is operational
3. Check database connectivity
4. Review error logs

### Issue: High Latency (> 25s)

**Cause**: Slow variant generation or feedback loop  
**Solution**:
1. Check variant count (reduce if needed)
2. Monitor feedback loop frequency
3. Optimize database queries
4. Increase compute resources if necessary

---

## Support & Contact

- **Documentation**: https://docs.tenopa.co.kr/metrics-api
- **Issues**: Create issue in GitHub repository
- **Support**: support@tenopa.co.kr
- **Slack**: #metrics-api-support channel

---

**Version**: 1.0  
**Last Updated**: 2026-04-18  
**Status**: Production Ready  
**Next Review**: 2026-05-18  
