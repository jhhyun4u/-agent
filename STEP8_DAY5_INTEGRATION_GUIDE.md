# STEP 8 Day 5 Integration Guide

## ⚡ Quick Start

### 1. Verify Files Exist

```bash
# Check all files are in place
ls -la app/api/routes_jobs.py
ls -la app/api/websocket_jobs.py
ls -la tests/integration/test_jobs_api.py

# Syntax validation
python -m py_compile app/api/routes_jobs.py app/api/websocket_jobs.py
```

### 2. Start Dev Server

```bash
cd /c/project/tenopa\ proposer
uv sync                              # Install dependencies
uv run uvicorn app.main:app --reload  # Start server
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 3. Test REST API

```bash
# Get your bearer token from Auth endpoint
# Then test Job creation:

curl -X POST http://localhost:8000/api/jobs \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "type": "step4a_diagnosis",
    "payload": {"section": "s1"}
  }'
```

### 4. Test WebSocket

**Browser DevTools Console:**
```javascript
const token = '<your-bearer-token>';
const jobId = '<job-id-from-create-response>';

const ws = new WebSocket(
  `ws://localhost:8000/ws/jobs/${jobId}?token=${token}`
);

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');
```

---

## 🧪 Run Integration Tests

```bash
# Run all tests
cd /c/project/tenopa\ proposer
uv run pytest tests/integration/test_jobs_api.py -v

# Run specific test
uv run pytest tests/integration/test_jobs_api.py::TestJobsAPI::test_create_job_success -v

# Run with coverage
uv run pytest tests/integration/test_jobs_api.py --cov=app.api --cov-report=term-missing
```

**Expected Output:**
```
tests/integration/test_jobs_api.py::TestJobsAPI::test_create_job_success PASSED
tests/integration/test_jobs_api.py::TestJobsAPI::test_create_job_invalid_type PASSED
...
======================= 16 passed in 1.23s =======================
```

---

## 📡 API Endpoint Reference

### REST Endpoints

```
POST   /api/jobs                         Create job
GET    /api/jobs/{job_id}                Get job status
GET    /api/jobs                         List jobs
PUT    /api/jobs/{job_id}/cancel         Cancel job
PUT    /api/jobs/{job_id}/retry          Retry failed job
DELETE /api/jobs/{job_id}                Delete job
GET    /api/jobs/stats                   Queue statistics (admin)
```

### WebSocket Endpoint

```
WS     /ws/jobs/{job_id}?token=<token>   Real-time job updates
```

---

## 🔑 Authentication

All endpoints require Bearer token in header or query parameter:

```bash
# REST (Header)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/jobs

# WebSocket (Query parameter)
ws://localhost:8000/ws/jobs/{job_id}?token=<token>
```

---

## 💡 Common Usage Patterns

### Pattern 1: Create Job and Poll via REST

```python
import httpx
import time

async with httpx.AsyncClient() as client:
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create job
    resp = await client.post(
        "http://localhost:8000/api/jobs",
        json={
            "proposal_id": proposal_id,
            "type": "step4a_diagnosis",
            "payload": {"section": "s1"}
        },
        headers=headers
    )
    job = resp.json()
    job_id = job["id"]
    
    # Poll status every 2 seconds
    while True:
        resp = await client.get(
            f"http://localhost:8000/api/jobs/{job_id}",
            headers=headers
        )
        status = resp.json()
        print(f"Status: {status['status']}, Progress: {status['progress']}%")
        
        if status["status"] in ["success", "failed", "cancelled"]:
            break
        
        time.sleep(2)
```

### Pattern 2: Real-time WebSocket Streaming

```python
import websockets
import json

async def monitor_job(job_id: str, token: str):
    uri = f"ws://localhost:8000/ws/jobs/{job_id}?token={token}"
    
    async with websockets.connect(uri) as ws:
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            if data["type"] == "status":
                print(f"Job status: {data['status']}")
            
            elif data["type"] == "progress":
                print(f"Progress: {data['progress']}%")
            
            elif data["type"] == "completed":
                print(f"Job completed with result: {data['result']}")
                break
            
            elif data["type"] == "error":
                print(f"Error: {data['error']}")
                break
```

### Pattern 3: List Jobs with Filtering

```bash
# List pending jobs of type step4a_diagnosis
curl -X GET "http://localhost:8000/api/jobs?status=pending&type=step4a_diagnosis&limit=20" \
  -H "Authorization: Bearer <token>"

# Paginate through results (page 2, 20 items per page)
curl -X GET "http://localhost:8000/api/jobs?limit=20&offset=20" \
  -H "Authorization: Bearer <token>"
```

---

## 🐛 Troubleshooting

### Issue: "Authorization header missing"

**Solution:** Add Bearer token to all requests
```bash
curl -H "Authorization: Bearer <your-token>" http://localhost:8000/api/jobs
```

### Issue: "WebSocket connection rejected"

**Solution:** Verify token in query parameter
```bash
# Check token is URL-encoded if needed
ws://localhost:8000/ws/jobs/{job_id}?token=<token>
```

### Issue: "Job not found" (404)

**Solution:** Verify job_id exists
```bash
# List all jobs to find valid IDs
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/jobs
```

### Issue: "Cannot cancel job in state..."

**Solution:** Only PENDING or RUNNING jobs can be cancelled
```bash
# Check current status first
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/jobs/{job_id}
```

### Issue: Rate limit exceeded (429)

**Solution:** Wait and retry
```
POST /api/jobs: 30 requests/minute
PUT /api/jobs/{id}/retry: 20 requests/minute
GET /api/jobs/stats: 10 requests/minute
```

---

## 📊 Monitoring

### Check Queue Health

```bash
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:8000/api/jobs/stats
```

**Response:**
```json
{
  "pending": 5,
  "running": 2,
  "success": 157,
  "failed": 3,
  "cancelled": 1,
  "total": 168,
  "avg_duration_seconds": 23.7,
  "success_rate": 0.9345
}
```

---

## 🔗 Related Documentation

- **Design**: `docs/02-design/features/step8-job-queue.design.md`
- **Services**: `app/services/job_queue_service.py` (Days 1-4)
- **Schemas**: `app/models/job_queue_schemas.py`
- **Tests**: `tests/integration/test_jobs_api.py`

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] All 16 tests pass: `pytest tests/integration/test_jobs_api.py -v`
- [ ] No syntax errors: `python -m py_compile app/api/routes_jobs.py app/api/websocket_jobs.py`
- [ ] main.py includes both routers (verified)
- [ ] Rate limits configured appropriately
- [ ] Logging configured for API requests
- [ ] Database migrations applied
- [ ] Bearer token authentication verified
- [ ] WebSocket timeouts configured (30s heartbeat)
- [ ] Error monitoring set up
- [ ] Load test completed (simulate 100+ concurrent jobs)

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test cases in `test_jobs_api.py`
3. Check logs: `tail -f logs/app.log`
4. Review error response codes in implementation report
