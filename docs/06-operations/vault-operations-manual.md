# Vault Operations Manual
**Document Status:** Draft v1.0  
**Last Updated:** 2026-04-14  
**Owner:** DevOps / Platform Team  
**Target Phase:** Phase 1 (2026-05-01 ~ 2026-06-12)

---

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Monitoring & Alerting](#monitoring--alerting)
3. [Failure Handling SOP](#failure-handling-sop)
4. [Data Update & Refresh Strategy](#data-update--refresh-strategy)
5. [Performance Baselines](#performance-baselines)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Rollback Procedures](#rollback-procedures)
8. [Security & Access Control](#security--access-control)

---

## System Architecture Overview

### Core Components

**Backend Stack:**
- FastAPI application (Python 3.11+)
- Supabase PostgreSQL with pgvector extension (embeddings)
- OpenAI Embeddings API (text-embedding-3-small)
- Redis (caching layer, optional for Phase 1)

**Frontend Stack:**
- Next.js 14 with TypeScript
- TanStack Query (data fetching)
- Tailwind CSS + shadcn/ui (components)

**8 Vault Sections:**
1. **Completed Projects** — SQL-primary (proposals DB) + Vector search
2. **Company Internal** — SQL-only (internal documents, company profile)
3. **Credentials** — SQL-only (certifications, licenses)
4. **Government Guidelines** — SQL-only (공고, 낙찰률, salary data)
5. **Competitors** — Vector-primary (market research, competitive intel)
6. **Success Cases** — Vector-primary (project outcomes, lessons learned)
7. **Clients DB** — SQL-only (client contact info, project history)
8. **Research Materials** — Vector-primary with TTL (시간 제한 자료, auto-delete 3mo)

### Data Flow

```
Frontend (Next.js)
    ↓
LB (API Gateway, if applicable)
    ↓
Backend (FastAPI) → routes_vault_chat.py
    ├→ vault_query_router.py (route to correct section handler)
    ├→ vault_validation.py (3-Point Gate: source coherence, fact alignment, confidence)
    ├→ 8 section handlers (completed_projects_handler, company_internal_handler, ...)
    ├→ Supabase PostgreSQL (SQL queries)
    └→ OpenAI API (embeddings, LLM synthesis)
    
Supabase:
    ├→ vault_documents (pgvector: embeddings)
    ├→ vault_conversations (chat history)
    ├→ vault_messages (individual messages)
    └→ Existing tables (proposals, clients, certifications, ...)
```

---

## Monitoring & Alerting

### Key Metrics

#### 1. API Performance
- **Metric:** Response time per endpoint
- **Baseline:** <3s for all endpoints (p95)
- **Alert Threshold:** >5s (p95)
- **Frequency:** Real-time

```python
# Backend instrumentation example (FastAPI middleware)
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log to metrics service (Prometheus/CloudWatch)
    metrics.histogram("vault_request_duration_ms", 
                      process_time * 1000, 
                      tags={"endpoint": request.url.path})
    
    if process_time > 5.0:
        logger.warning(f"Slow request: {request.url.path} took {process_time}s")
    
    return response
```

#### 2. Embedding Costs
- **Metric:** Daily OpenAI API spend
- **Baseline:** ~$0.30/day (text-embedding-3-small at current volumes)
- **Alert Threshold:** >$2.00/day (7x increase)
- **Frequency:** Daily summary

```python
# Track embedding costs
async def create_embeddings(texts: List[str], section: str):
    """
    Monitor cost per section
    - completed_projects: ~0.02/month (low volume)
    - research_materials: ~0.15/month (high volume, new uploads)
    """
    try:
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        # Log cost
        cost = len(texts) * 0.00002  # $0.02 per 1M tokens, ~10 tokens per doc
        metrics.gauge("vault_embedding_cost", cost, tags={"section": section})
        
        return response.embeddings
    except Exception as e:
        logger.error(f"Embedding failed for {section}: {e}")
        metrics.increment("vault_embedding_errors", tags={"section": section})
        raise
```

#### 3. Accuracy Metrics
- **Metric:** Hallucination rate (false/unverified statements)
- **Baseline:** <1% (monitored via logging + sampling)
- **Alert Threshold:** >2%
- **Frequency:** Hourly sampling (log every 10th response for review)

```python
# In vault_validation.py
async def validate_response(response: dict, section: str) -> dict:
    """
    3-Point Gate validation:
    1. Source coherence — does source support response?
    2. Fact alignment — do facts match SQL/Vector results?
    3. Confidence threshold — confidence >= 80%
    """
    
    confidence = response.get("confidence", 0)
    sources_match = response.get("sources_valid", False)
    facts_aligned = response.get("facts_verified", False)
    
    # Log for monitoring
    if confidence < 0.8:
        metrics.increment("vault_low_confidence_responses", 
                          tags={"section": section})
        logger.warning(f"Low confidence response in {section}: {confidence}")
    
    if not sources_match or not facts_aligned:
        metrics.increment("vault_validation_failures", 
                          tags={"section": section})
        logger.warning(f"Validation gate failed for {section}")
    
    return {
        **response,
        "validation_passed": confidence >= 0.8 and sources_match and facts_aligned,
        "confidence": confidence
    }
```

#### 4. Database Health
- **Metric:** pgvector embedding count, storage usage
- **Baseline:** ~5000 embeddings initially (Phase 1)
- **Alert Threshold:** >50000 (indicates data growth, plan scaling)
- **Frequency:** Daily

```sql
-- Monitor pgvector table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename IN ('vault_documents', 'vault_conversations')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check embedding vector distribution
SELECT 
    section,
    COUNT(*) as embedding_count,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as vectors_created
FROM vault_documents
GROUP BY section;
```

#### 5. User Activity
- **Metric:** Requests per user, session duration, feature usage
- **Baseline:** Establish during Phase 1 beta
- **Alert Threshold:** 1 user >100 requests/minute (potential abuse/script)
- **Frequency:** Real-time

### Recommended Monitoring Stack

**Option A: Supabase Native (Simplest for Phase 1)**
- Use Supabase Dashboard → Logs → Edge Functions logs
- CloudWatch (if AWS RDS) or Supabase native metrics
- Simple threshold alerts via Supabase Webhooks

**Option B: Prometheus + Grafana (Recommended for Scale)**
- Python Prometheus client in backend
- Grafana dashboards for:
  - Vault API Performance (response times, error rates)
  - Accuracy Dashboard (validation pass %, confidence distribution)
  - Cost Dashboard (embedding spend, token usage)
  - Database Health (pgvector table sizes, query latency)

**Sample Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'vault-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Sample Grafana Dashboard Panels:**
1. Vault API Response Time (p50, p95, p99)
2. Error Rate by Section
3. Hallucination Detection Rate (rolling 24h)
4. OpenAI Embedding Cost (daily)
5. Vector Search Latency
6. Request Distribution by Section

---

## Failure Handling SOP

### Failure Category 1: API Timeout (>5s response)

**Symptoms:**
- Frontend shows "요청 시간 초과" error
- Grafana alerts: `vault_request_duration_ms` > 5000

**Root Cause Analysis Checklist:**
- [ ] Is OpenAI Embeddings API slow? (Check OpenAI status)
- [ ] Is PostgreSQL query slow? (Check `EXPLAIN ANALYZE` on slow query)
- [ ] Is vector search slow? (Check pgvector performance)
- [ ] Is LLM synthesis slow? (Claude Sonnet might be rate-limited)
- [ ] Network latency? (Check Supabase region, backend region)

**Resolution Steps:**

1. **Check Database Query (Completed Projects + Vector Search)**
   ```sql
   -- If query >3s, review index usage
   EXPLAIN ANALYZE
   SELECT d.id, d.title, d.content, d.embedding
   FROM vault_documents d
   WHERE d.section = 'completed_projects'
   AND d.embedding <-> query_embedding < 0.5
   ORDER BY d.embedding <-> query_embedding
   LIMIT 10;
   
   -- If slow, ensure pgvector index exists
   CREATE INDEX IF NOT EXISTS vault_documents_embedding_idx 
   ON vault_documents USING ivfflat (embedding vector_cosine_ops);
   ```

2. **Check OpenAI API Status**
   ```bash
   curl https://status.openai.com/api/v2/status.json
   # If status != "operational", use cached embeddings + retry after 5min
   ```

3. **Check Claude API Rate Limits**
   - Look for `429` errors in logs
   - Implement exponential backoff: 1s → 2s → 4s → 8s (max)
   - Consider adding request queue with max concurrency

4. **Implement Graceful Degradation**
   ```python
   # If embedding creation fails, continue with SQL-only results
   async def completed_projects_handler(query, search_method="hybrid"):
       try:
           # Try vector search first
           vector_results = await vector_search(query)
       except Exception as e:
           logger.error(f"Vector search failed: {e}, falling back to SQL")
           vector_results = []
       
       try:
           # Always try SQL search as fallback
           sql_results = await sql_search(query)
       except Exception as e:
           logger.error(f"SQL search failed: {e}")
           return {"error": "데이터베이스 검색 실패", "results": []}
       
       # Return best available results
       return {
           "results": vector_results or sql_results,
           "warning": "Vector search unavailable" if not vector_results else None
       }
   ```

5. **Escalate if unresolved**
   - Page on-call engineer
   - Check Supabase support status

---

### Failure Category 2: Hallucination Detected (Confidence <80%)

**Symptoms:**
- User reports incorrect information
- Validation gate triggers: `vault_validation_failures` increases
- Low confidence responses: `vault_low_confidence_responses` alert

**Root Cause Analysis:**
- Is the section configured correctly? (Check section_config.py)
- Is the LLM prompt correct? (Check system prompt in vault_context.py)
- Are facts actually in the database? (Run manual SQL verification)
- Is embedding quality poor? (Check embedding distance thresholds)

**Resolution Steps:**

1. **Immediate: Block Low-Confidence Responses**
   ```python
   # In routes_vault_chat.py
   if response["confidence"] < 0.8:
       return {
           "success": False,
           "message": "신뢰도가 낮아 정보를 제공할 수 없습니다. 관리자에게 문의하세요.",
           "debug_info": {
               "confidence": response["confidence"],
               "sources": response.get("sources", [])
           }
       }
   ```

2. **Investigate Source Data**
   ```sql
   -- Check if facts are in vault_documents for the section
   SELECT * FROM vault_documents
   WHERE section = 'success_cases'
   AND (title ILIKE '%keyword%' OR content ILIKE '%keyword%')
   LIMIT 5;
   ```

3. **Review LLM Prompt**
   - Check `system_prompts` in vault_context.py
   - For section, verify:
     - Is the prompt instructing source attribution?
     - Is it restricting answers to data in the context?
     - Does it include confidence threshold checks?

4. **Fine-tune Embedding Thresholds**
   ```python
   # In vault_embedding.py
   EMBEDDING_THRESHOLDS = {
       "completed_projects": 0.3,  # Stricter: only very similar docs
       "success_cases": 0.5,       # Moderate: allow semantic matches
       "research_materials": 0.6   # Relaxed: capture adjacent context
   }
   
   # If hallucinations increase, tighten threshold
   # If accuracy drops but no hallucinations, loosen threshold
   ```

5. **Manual Review & Logging**
   ```python
   # Log exact response for manual review
   if response["confidence"] < 0.8:
       logger.critical({
           "timestamp": datetime.now().isoformat(),
           "section": section,
           "query": query,
           "confidence": response["confidence"],
           "sources": response.get("sources", []),
           "response_text": response.get("text", ""),
           "llm_thinking": response.get("reasoning", "")
       })
       # Alert on-call for investigation
   ```

6. **Escalate & Document**
   - Create incident report in `/docs/incidents/hallucination-YYYY-MM-DD.md`
   - Update LLM prompt if systematic issue found
   - Increase embedding data volume for weak sections if needed

---

### Failure Category 3: Embedding/Vector Search Fails

**Symptoms:**
- "벡터 검색 실패" errors in logs
- Vector search returns empty results for valid queries
- OpenAI API errors in logs

**SOP:**

1. **Check OpenAI API**
   ```python
   # Test embeddings endpoint
   import openai
   
   try:
       response = openai.Embedding.create(
           model="text-embedding-3-small",
           input=["test"]
       )
       print("OpenAI API: OK")
   except Exception as e:
       print(f"OpenAI API Error: {e}")
       # Switch to SQL-only mode
   ```

2. **Check pgvector Extension**
   ```sql
   -- Verify extension is loaded
   SELECT * FROM pg_extension WHERE extname = 'vector';
   -- Output: should show vector extension
   
   -- If missing:
   -- Contact Supabase support to enable pgvector on this database
   ```

3. **Fall Back to SQL Search**
   ```python
   # vault_query_router.py
   async def route_query(query, section, user_id):
       try:
           # Try vector search first
           results = await vector_search(query, section)
       except Exception as e:
           logger.warning(f"Vector search failed for {section}, using SQL: {e}")
           # Fall back to SQL full-text search
           results = await sql_full_text_search(query, section)
       
       return results
   ```

---

### Failure Category 4: Data Staleness (Research Materials Expired)

**Symptoms:**
- Research material >3 months old still appears in results
- `research_materials_retention_check` doesn't trigger

**SOP:**

1. **Manual Cleanup Query**
   ```sql
   -- Check expired research materials
   SELECT id, title, created_at, NOW() - created_at as age
   FROM vault_documents
   WHERE section = 'research_materials'
   AND created_at < NOW() - INTERVAL '3 months'
   ORDER BY created_at DESC;
   
   -- Delete expired
   DELETE FROM vault_documents
   WHERE section = 'research_materials'
   AND created_at < NOW() - INTERVAL '3 months';
   ```

2. **Automate via Scheduled Job**
   ```python
   # app/jobs/cleanup_research_materials.py
   from apscheduler.schedulers.background import BackgroundScheduler
   
   scheduler = BackgroundScheduler()
   
   async def cleanup_expired_research():
       """Delete research materials >3 months old"""
       deleted_count = await client.table("vault_documents").delete().eq(
           "section", "research_materials"
       ).lt("created_at", (datetime.now() - timedelta(days=90)).isoformat()).execute()
       
       logger.info(f"Deleted {deleted_count.count} expired research materials")
   
   # Run daily at 2 AM
   scheduler.add_job(cleanup_expired_research, 'cron', hour=2, minute=0)
   scheduler.start()
   ```

---

## Data Update & Refresh Strategy

### Section-Specific Update Schedules

| Section | Source | Update Frequency | Trigger | Owner |
|---------|--------|------------------|---------|-------|
| **Completed Projects** | proposals DB | Real-time | When proposal status → "closed" | System |
| **Company Internal** | Manual upload | Weekly | HR/Admin uploads | HR Team |
| **Credentials** | Manual upload | Quarterly | After certification renewal | Compliance |
| **Government Guidelines** | 나라장터 + Manual | Monthly | Manual weekly check + parsing | Research |
| **Competitors** | Manual upload | Monthly | Marketing research reports | Marketing |
| **Success Cases** | Proposal closure | Monthly | Extract from closed proposals | PM Team |
| **Clients DB** | proposals DB | Real-time | When client updated in proposals | System |
| **Research Materials** | Manual upload | On-demand | User/researcher uploads | Team |

### Automated Data Refresh: Completed Projects → Success Cases

**Trigger:** When proposal status changes to "closed" (won/lost)

```python
# app/services/vault_data_sync.py
from app.state_machine import StateMachine

async def on_proposal_closed(proposal_id: str, win_result: str):
    """
    Called when proposal is closed (won/lost)
    Automatically creates/updates success case
    """
    
    # 1. Fetch proposal details
    proposal = await client.table("proposals").select("*").eq(
        "id", proposal_id
    ).single().execute()
    
    # 2. Prepare success case document
    success_case = {
        "section": "success_cases",
        "title": f"{'승리' if win_result == 'won' else '낙선'}: {proposal.data['title']}",
        "content": f"""
        **발주처:** {proposal.data.get('client', 'N/A')}
        **예산:** {proposal.data.get('budget', 'N/A')}
        **결과:** {win_result}
        **기간:** {proposal.data.get('duration', 'N/A')}
        **팀:** {proposal.data.get('team', 'N/A')}
        
        {proposal.data.get('summary', '')}
        """,
        "metadata": {
            "proposal_id": proposal_id,
            "win_result": win_result,
            "client": proposal.data.get('client'),
            "budget": proposal.data.get('budget'),
            "team_members": proposal.data.get('team_members', [])
        },
        "created_at": datetime.now().isoformat(),
        "embedding": None  # Will be generated in next step
    }
    
    # 3. Store in vault_documents
    await client.table("vault_documents").insert(success_case).execute()
    
    # 4. Generate embedding (async)
    asyncio.create_task(generate_embedding_for_document(success_case["id"]))
    
    logger.info(f"Success case created for proposal {proposal_id}")
```

### Manual Data Update: Company Internal, Government Guidelines

```python
# app/api/routes_vault_admin.py
@router.post("/vault/documents/upload")
async def upload_vault_document(
    file: UploadFile,
    section: str,
    metadata: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint: Upload document to Vault section
    - Validates file type (PDF, MD, DOCX)
    - Extracts text
    - Generates embedding
    - Stores metadata
    """
    
    # Check authorization
    if not current_user.roles.contains("vault_admin"):
        raise HTTPException(status_code=403)
    
    # 1. Validate file
    if file.content_type not in ["application/pdf", "text/markdown", 
                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식")
    
    # 2. Extract text
    if file.content_type == "application/pdf":
        text = extract_pdf_text(file)
    elif file.content_type == "text/markdown":
        text = (await file.read()).decode()
    else:  # DOCX
        text = extract_docx_text(file)
    
    # 3. Create document record
    doc_id = str(uuid.uuid4())
    document = {
        "id": doc_id,
        "section": section,
        "title": file.filename,
        "content": text,
        "metadata": metadata,
        "created_by": current_user.id,
        "created_at": datetime.now().isoformat(),
        "embedding": None
    }
    
    # 4. Store document
    await client.table("vault_documents").insert(document).execute()
    
    # 5. Generate embedding (async, non-blocking)
    asyncio.create_task(
        generate_and_store_embedding(doc_id, text)
    )
    
    return {
        "message": "문서 업로드 완료",
        "document_id": doc_id,
        "embedding_status": "생성 중"
    }
```

---

## Performance Baselines

### Target Metrics (Phase 1)

| Metric | Target | Measurement | Notes |
|--------|--------|-------------|-------|
| **API Response Time** | <3s (p95) | Per request | Includes OpenAI/Vector search |
| **Hallucination Rate** | <1% | Monthly sampling | Manual review of 10% of responses |
| **Availability** | 99.5% | Monthly uptime | Acceptable downtime: ~3.6 hours/month |
| **Vector Search Latency** | <1.5s | Per search request | pgvector + OpenAI embedding |
| **SQL Query Latency** | <500ms | Per query | Completed projects, clients, etc. |
| **Embedding Generation Cost** | <$0.50/month | Daily tracking | OpenAI text-embedding-3-small |
| **Error Rate** | <0.1% | Real-time | Critical errors only (5xx, timeouts) |

### Load Testing Scenarios

```python
# tests/performance/test_vault_load.py
import locust

class VaultLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def search_completed_projects(self):
        """Simulate 3x searches for completed projects"""
        self.client.post("/vault/chat", json={
            "section": "completed_projects",
            "query": "AI 프로젝트 5년",
            "conversation_id": None
        })
    
    @task(2)
    def search_success_cases(self):
        """Simulate 2x searches for success cases"""
        self.client.post("/vault/chat", json={
            "section": "success_cases",
            "query": "AI 프로젝트 성공 사례",
            "conversation_id": None
        })
    
    @task(1)
    def search_government_guidelines(self):
        """Simulate 1x search for guidelines"""
        self.client.post("/vault/chat", json={
            "section": "government_guidelines",
            "query": "2026년 정부 급여 기준",
            "conversation_id": None
        })

# Run: locust -f test_vault_load.py --host=http://localhost:8000
# Expected: Handle 10 concurrent users, <3s p95 response time
```

---

## Troubleshooting Guide

### Issue: "AI Chat이 응답하지 않음"

1. Check backend logs
   ```bash
   tail -f logs/vault.log | grep ERROR
   ```

2. Test API endpoint directly
   ```bash
   curl -X POST http://localhost:8000/vault/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "section": "completed_projects"}'
   ```

3. Check OpenAI API status
   ```bash
   curl https://status.openai.com/api/v2/status.json
   ```

4. Restart backend service
   ```bash
   # Docker
   docker restart tenopa-backend
   
   # Or systemd
   systemctl restart tenopa-backend
   ```

---

### Issue: "벡터 검색이 느림"

1. Check pgvector index
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'vault_documents' AND indexname LIKE '%embedding%';
   ```

2. Rebuild index if missing
   ```sql
   DROP INDEX IF EXISTS vault_documents_embedding_idx;
   CREATE INDEX vault_documents_embedding_idx 
   ON vault_documents USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

3. Check Supabase query performance
   - Use Supabase Dashboard → SQL Editor
   - Run: `EXPLAIN ANALYZE` on slow queries

---

### Issue: "신뢰도가 낮음" 반복

1. Check LLM prompt in vault_context.py
2. Verify document quality in vault_documents
3. Consider increasing embedding vector density
4. Review confidence threshold logic

---

## Rollback Procedures

### Scenario 1: Critical Bug Introduced in Phase 1

**Rollback Plan:**

1. **Database Rollback** (if data corruption)
   ```sql
   -- Supabase Dashboard → Backups
   -- Restore from latest clean backup (before deployment)
   -- Estimated downtime: 5-15 minutes
   ```

2. **Backend Code Rollback**
   ```bash
   # If deployed via Docker
   docker pull tenopa-backend:stable
   docker stop tenopa-backend
   docker run -d --name tenopa-backend tenopa-backend:stable
   ```

3. **Frontend Rollback**
   ```bash
   # If deployed via Vercel
   # Vercel Dashboard → Deployments → Click previous stable build
   # Auto-rollback takes <1 minute
   ```

### Scenario 2: Embedding Cost Explosion

If OpenAI Embeddings cost >$5/day (16x baseline):

1. **Immediate:** Disable automatic embedding generation
   ```python
   # In vault_embedding.py
   DISABLE_EMBEDDING_GENERATION = True  # Fallback to SQL-only search
   ```

2. **Investigate:** Check vault_documents for anomalies
   ```sql
   SELECT section, COUNT(*) as doc_count, MAX(created_at) as latest
   FROM vault_documents
   GROUP BY section
   ORDER BY doc_count DESC;
   ```

3. **Clean up:** Delete duplicate/corrupted documents
   ```sql
   DELETE FROM vault_documents
   WHERE created_at > NOW() - INTERVAL '1 hour'
   AND content IS NULL;
   ```

4. **Resume:** Re-enable embedding generation once cost normalized

---

## Security & Access Control

### Row-Level Security (RLS) Rules

```sql
-- vault_documents: Teams can only see their section data
CREATE POLICY vault_documents_select_by_team ON vault_documents
FOR SELECT
USING (auth.jwt() ->> 'team_id' = team_id OR section = 'public');

-- vault_conversations: Users can only see their own conversations
CREATE POLICY vault_conversations_select_by_user ON vault_conversations
FOR SELECT
USING (auth.jwt() ->> 'sub' = user_id);

-- vault_admin_operations: Only vault_admin role can insert/update
CREATE POLICY vault_documents_admin_write ON vault_documents
FOR INSERT
WITH CHECK (auth.jwt() ->> 'role' = 'vault_admin');
```

### Rate Limiting

```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Apply per endpoint
@app.post("/vault/chat")
@limiter.limit("100/minute")  # 100 requests per minute per user
async def vault_chat(request: Request, body: VaultChatRequest):
    ...
```

### Audit Logging

```python
# Log all vault_documents access
@app.post("/vault/chat")
async def vault_chat(request: Request, body: VaultChatRequest, current_user: User):
    # Log query + response
    await client.table("vault_audit_logs").insert({
        "user_id": current_user.id,
        "section": body.section,
        "query": body.query,
        "response_length": len(response),
        "confidence": response.get("confidence"),
        "timestamp": datetime.now().isoformat(),
        "ip_address": request.client.host
    }).execute()
    
    return response
```

---

## Emergency Contacts

| Role | Name | Phone | Email | On-Call Schedule |
|------|------|-------|-------|------------------|
| DevOps Lead | — | — | — | 24/7 rotation |
| Backend Lead | — | — | — | Weekdays 9-18 |
| Supabase Support | — | — | support@supabase.io | 24/7 |
| OpenAI Support | — | — | support@openai.com | Business hours |

---

## Change Log

| Date | Change | Impact | Owner |
|------|--------|--------|-------|
| 2026-04-14 | Created v1.0 | Baseline for Phase 1 | DevOps |
| — | — | — | — |

---

**Document Owner:** DevOps / Platform Team  
**Last Review:** 2026-04-14  
**Next Review:** 2026-05-31 (after Phase 1 beta)  
**Version:** 1.0
