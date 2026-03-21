# Data Security Audit Report

**Project**: 용역제안 Coworker (Proposal Architect v3.4)
**Date**: 2026-03-20
**Auditor**: Security Architect Agent
**Scope**: Full application security review (Backend, DB, Frontend config, LangGraph)

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| **CRITICAL** | 2 | Requires immediate action |
| **HIGH** | 5 | Fix before next deployment |
| **MEDIUM** | 8 | Fix in current sprint |
| **LOW** | 6 | Track in backlog |
| **Total** | 21 | |

The most severe finding is **live production secrets committed to version control** (`.env` file). Two CRITICAL issues and five HIGH issues require immediate attention before any deployment.

---

## CRITICAL Findings

### C-1. Production Secrets Committed to Version Control

**OWASP**: A02 (Cryptographic Failures)
**File**: `C:\project\tenopa proposer\-agent-master\.env` (lines 1-8)
**Also**: `C:\project\tenopa proposer\-agent-master\frontend\.env.local` (lines 1-3)

The `.env` file contains live production credentials in plaintext:

- `ANTHROPIC_API_KEY=sk-ant-api03-hvPYPY...` (line 2)
- `G2B_API_KEY=0c72ec113c...` (line 1)
- `SUPABASE_KEY=eyJhbGci...` (line 6)
- `SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...` (line 8) -- **This key bypasses all RLS policies**

While `.env` is listed in `.gitignore` (line 16), the file exists on disk. If this repository has ever been pushed with these files, the secrets are permanently exposed in git history.

**Risk**: Complete database compromise. The `SUPABASE_SERVICE_ROLE_KEY` bypasses Row Level Security, giving unrestricted read/write access to all tables.

**Remediation**:
1. **Immediately rotate ALL keys** (Anthropic, G2B, Supabase anon + service_role).
2. Audit git history for any commits containing these secrets (`git log --all -p -- .env`).
3. If found in history, use `git filter-branch` or BFG Repo Cleaner.
4. Implement a secrets manager (Azure Key Vault, Doppler, or Railway/Render native env vars).
5. Add `.env` to a pre-commit hook that blocks commits containing secret patterns.

---

### C-2. Supabase Service Role Key Used for ALL Server Operations (RLS Bypass)

**OWASP**: A01 (Broken Access Control)
**File**: `app/utils/supabase_client.py` (lines 20-30)

```python
async def get_async_client() -> AsyncClient:
    api_key = settings.supabase_service_role_key or settings.supabase_key
    _server_client = await acreate_client(settings.supabase_url, api_key)
```

Every server-side database operation uses the service_role key, which **bypasses all 28+ RLS policies** defined in `database/schema_v3.4.sql`. The carefully designed RLS policies (lines 530-639) for organization isolation, team access, and role-based visibility are completely ineffective.

**Risk**: Any authenticated user can potentially read/modify data from other organizations, teams, and users via API endpoints that construct queries without proper filtering. The `require_project_access()` function in `deps.py` provides application-level access control, but not all endpoints use it (see H-2).

**Remediation**:
1. Use `get_user_client(user_jwt)` (line 33-40, already implemented but unused) for user-facing operations.
2. Reserve `get_async_client()` (service_role) for system/background tasks only.
3. Audit every route handler to ensure either RLS-enforced client or explicit authorization is used.

---

## HIGH Findings

### H-1. Missing Authorization on Multiple API Endpoints

**OWASP**: A01 (Broken Access Control)
**Files**: Multiple route files

Several endpoints use `get_current_user_or_none` (which returns `None` for unauthenticated requests) instead of `get_current_user`, allowing anonymous access:

| File | Line | Endpoint | Issue |
|------|------|----------|-------|
| `routes_proposal.py` | 66 | `POST /api/proposals/from-rfp` | `get_current_user_or_none` -- unauthenticated users create proposals with hardcoded fallback admin ID |
| `routes_proposal.py` | 93 | Same endpoint | Fallback `user_id = "113a90c4-da41-4d60-8ca3-3f62c09325f3"` -- hardcoded admin UUID |
| `routes_proposal.py` | 190-191 | `GET /api/proposals` | `get_current_user_or_none` -- unauthenticated listing |
| `routes_proposal.py` | 229 | `GET /api/proposals/{id}` | `get_current_user_or_none` -- unauthenticated detail access |

**Risk**: Unauthenticated users can create proposals (impersonating the hardcoded admin), list all proposals, and view proposal details.

**Remediation**: Change all endpoints to use `get_current_user` (strict). Remove the hardcoded fallback admin UUID entirely. If background/system operations need no-auth access, use a dedicated internal service token.

---

### H-2. Missing Project-Level Access Control on Most Endpoints

**OWASP**: A01 (Broken Access Control)
**Files**: `routes_workflow.py`, `routes_files.py`, `routes_artifacts.py`, `routes_notification.py`

The `require_project_access()` dependency performs hierarchical authorization (admin/executive/director/lead/member/participant), but most proposal-scoped endpoints do not use it:

- `routes_workflow.py`: start, resume, stream, history, goto, lock/unlock -- only `get_current_user`
- `routes_files.py`: upload, list, delete, download -- only `get_current_user`
- All workflow control endpoints allow any authenticated user to manipulate any proposal's workflow

**Risk**: Any authenticated user can start/resume/time-travel any proposal's workflow, upload/delete files on any proposal, and read any proposal's state.

**Remediation**: Add `require_project_access` as a dependency to all proposal-scoped endpoints:
```python
@router.post("/{proposal_id}/start")
async def start_workflow(
    proposal_id: str,
    proposal=Depends(require_project_access),  # Add this
    user=Depends(get_current_user),
):
```

---

### H-3. Server-Side Request Forgery (SSRF) in RFP Parser

**OWASP**: A10 (Server-Side Request Forgery)
**File**: `app/services/rfp_parser.py` (lines 106-139)

```python
async def parse_rfp_from_url(url: str, file_type: str = "pdf") -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ...) as resp:
```

The `parse_rfp_from_url` function fetches arbitrary URLs without validation. An attacker could supply URLs targeting internal services (e.g., `http://169.254.169.254/latest/meta-data/` for cloud metadata, `http://localhost:5432` for database probing).

**Risk**: Access to cloud instance metadata (credentials), internal service probing, port scanning.

**Remediation**:
1. Implement URL allowlist (e.g., only `*.g2b.go.kr` domains).
2. Block private/internal IP ranges (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16).
3. Add DNS resolution validation before making the request.

---

### H-4. No File Size Enforcement on Upload

**OWASP**: A04 (Insecure Design)
**Files**: `routes_files.py` (line 46), `routes_proposal.py` (line 73)

While `config.py` defines `max_file_size_mb: int = 50`, the actual upload endpoints read the entire file into memory without checking size:

```python
content = await file.read()  # No size check before reading
```

An attacker can upload multi-gigabyte files causing memory exhaustion (DoS).

**Remediation**:
```python
content = await file.read()
if len(content) > settings.max_file_size_mb * 1024 * 1024:
    raise FileSizeExceededError(settings.max_file_size_mb, len(content) / (1024*1024))
```
Better: use streaming reads with size limit enforcement.

---

### H-5. Missing CSRF Protection

**OWASP**: A01 (Broken Access Control)
**File**: `app/main.py` (lines 126-132)

The application uses `allow_credentials=True` with Bearer token auth but has no CSRF protection. With `allow_credentials=True`, a malicious site could potentially perform cross-origin requests with the user's cookies/credentials.

Current CORS configuration:
```python
allow_credentials=True,
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
```

**Risk**: While Bearer token authentication provides some CSRF resistance (tokens must be explicitly sent), if any authentication method uses cookies (Supabase Auth session cookies), CSRF attacks become possible.

**Remediation**:
1. If using only Bearer tokens (no cookies), set `allow_credentials=False`.
2. If cookies are needed, implement CSRF token validation middleware.
3. Restrict `cors_origins` to exact production domain (currently defaults to `http://localhost:3000`).

---

## MEDIUM Findings

### M-1. Missing Security Headers

**OWASP**: A05 (Security Misconfiguration)
**File**: `app/main.py`

No security headers are configured:
- No `Strict-Transport-Security` (HSTS)
- No `X-Content-Type-Options: nosniff`
- No `X-Frame-Options: DENY`
- No `Content-Security-Policy`
- No `X-XSS-Protection`

**Remediation**: Add a security headers middleware:
```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

---

### M-2. Prompt Injection Risk in LangGraph Workflow

**OWASP**: A03 (Injection)
**Files**: `routes_workflow.py` (line 59), `app/graph/nodes/rfp_analyze.py`, `app/services/claude_client.py`

User-supplied RFP text flows directly into LLM prompts:
- `rfp_raw` text from uploaded documents
- `feedback` from resume endpoint
- `rfp_file_text` from resume

While the state whitelist (`_ALLOWED_INITIAL_STATE_KEYS`, line 33) prevents injecting arbitrary state keys, the allowed values themselves (e.g., `search_query`, `rfp_raw`) are passed to Claude prompts without sanitization.

**Risk**: Crafted RFP documents could contain prompt injection payloads that manipulate AI behavior, exfiltrate system prompts, or produce misleading outputs.

**Remediation**:
1. Add input sanitization layer before LLM calls (strip known injection patterns).
2. Implement output validation on Claude responses.
3. Use structured outputs (tool_use) where possible to constrain response format.
4. Log and flag anomalous AI responses.

---

### M-3. Sensitive Data in Error Responses

**OWASP**: A04 (Insecure Design)
**Files**: `routes_workflow.py` (lines 178, 211, 330, 498-499)

Error messages expose internal system details:

```python
# Line 178 - Exposes truncated error string
"current_phase": f"error: {str(e)[:100]}",

# Line 211 - Returns raw exception message
return {"proposal_id": proposal_id, "error": str(e)}

# Line 330 - Streams error to client via SSE
yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
```

**Risk**: Stack traces and internal error messages can reveal database schema, file paths, library versions, and other implementation details useful for targeted attacks.

**Remediation**: Return generic error messages to clients. Log detailed errors server-side only.

---

### M-4. No Password Complexity Enforcement

**OWASP**: A07 (Identification and Authentication Failures)
**File**: `app/models/user_schemas.py` (PasswordChangeRequest)

The `PasswordChangeRequest` schema (referenced in `routes_auth.py` line 15) likely lacks password complexity validation. The new password is sent directly to Supabase without server-side strength checks.

**Remediation**: Add Pydantic validators for minimum length (12+), complexity (upper, lower, digit, special), and common password checks.

---

### M-5. Client-Provided Request ID Accepted Without Validation

**OWASP**: A09 (Security Logging and Monitoring Failures)
**File**: `app/middleware/request_id.py` (line 37)

```python
request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
```

Client-provided `X-Request-ID` is accepted verbatim. An attacker could inject log-forging payloads or excessively long strings.

**Remediation**: Validate client-provided request IDs (alphanumeric, max 64 chars). Reject or replace invalid values.

---

### M-6. Unbounded Query Results in List Endpoints

**OWASP**: A04 (Insecure Design)
**Files**: `routes_proposal.py` (line 189), `routes_kb.py`, `routes_admin.py`

While most list endpoints accept `limit` parameters, there is no server-side maximum enforcement:

```python
limit: int = 20  # default 20, but no max constraint
```

An attacker can request `limit=999999` to dump large datasets.

**Remediation**: Add `Query(20, ge=1, le=100)` validation to all limit parameters.

---

### M-7. SSE Stream Does Not Require Project Access

**OWASP**: A01 (Broken Access Control)
**File**: `routes_workflow.py` (lines 296-336)

The SSE streaming endpoint requires `get_current_user` but not project membership. Any authenticated user can subscribe to real-time workflow events of any proposal, potentially leaking sensitive strategy and proposal content.

**Remediation**: Add `require_project_access` dependency.

---

### M-8. Temp File Cleanup Race Condition

**OWASP**: A04 (Insecure Design)
**File**: `app/services/rfp_parser.py` (lines 93-103)

```python
with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
    tmp.write(content)
    tmp_path = Path(tmp.name)
try:
    return extract_text_from_file(tmp_path)
finally:
    tmp_path.unlink(missing_ok=True)
```

Using `delete=False` creates a window where temp files exist on disk. On Windows, `NamedTemporaryFile` paths are predictable. If the process crashes between write and unlink, sensitive RFP data persists.

**Remediation**: Use a dedicated temp directory with restricted permissions. Implement periodic cleanup of stale temp files.

---

## LOW Findings

### L-1. Health Check Exposes Database Error Types

**File**: `app/main.py` (line 212)

```python
health["database"] = f"error: {type(e).__name__}"
```

Reveals exception class names (e.g., `ConnectionRefusedError`, `OperationalError`) which can help attackers fingerprint the database technology.

**Remediation**: Return only `"error"` without the class name.

---

### L-2. Status Endpoint Leaks Active Session Count

**File**: `app/main.py` (lines 216-224)

The `/status` endpoint is unauthenticated and reveals `active_sessions` count, which can be used for reconnaissance.

**Remediation**: Require admin authentication for the `/status` endpoint.

---

### L-3. RLS Policies Missing on Several Tables

**File**: `database/schema_v3.4.sql`

Tables without RLS enabled:
- `project_participants`
- `search_results`
- `g2b_cache`
- `audit_logs`
- `ai_task_logs`
- `section_locks`
- `company_templates`
- `presentation_qa`
- `approval_delegations`
- `consortium_members`
- `project_teams`

While the service_role key bypasses RLS anyway (C-2), these tables would remain unprotected even after fixing C-2 if accessed via anon key or user JWT.

**Remediation**: Enable RLS and define policies for all tables, especially `audit_logs` (should be read-only for users), `section_locks`, and `approval_delegations`.

---

### L-4. No Rate Limiting on Most Endpoints

**File**: `app/middleware/rate_limit.py`, `routes_workflow.py`

Only 2 endpoints have explicit rate limits:
- `POST /{id}/start`: 10/minute
- `POST /change-password`: 5/minute

All other endpoints (KB CRUD, file upload, AI operations, admin) have no rate limits.

**Remediation**: Apply default global rate limit (e.g., 60/minute per user) and stricter limits on AI-calling endpoints.

---

### L-5. Inconsistent Error Handling Pattern

**Files**: Multiple route files

Mix of `HTTPException` (legacy) and `TenopAPIError` (standardized). The `HTTPException` responses return different JSON structure than `TenopAPIError`, potentially confusing client error handling and making security monitoring harder.

**Remediation**: Complete migration from `HTTPException` to `TenopAPIError` across all route files (at least 15+ occurrences in `routes_bids.py` alone).

---

### L-6. Email Logged in Warning Message

**File**: `app/services/auth_service.py` (line 47)

```python
logger.warning(f"사전 등록되지 않은 사용자 로그인 시도: {email}")
```

User email addresses are PII and should not appear in logs at WARNING level (which is typically more broadly distributed).

**Remediation**: Log only a hash or partial email at WARNING. Log full email at DEBUG level only.

---

## Positive Security Observations

The following security practices are well-implemented:

1. **State injection whitelist** (`routes_workflow.py` line 33): `_ALLOWED_INITIAL_STATE_KEYS` prevents arbitrary LangGraph state manipulation.
2. **Structured error codes** (`exceptions.py`): Consistent error taxonomy prevents ad-hoc information leakage.
3. **Role-based access control** (`deps.py`): Hierarchical RBAC (member/lead/director/executive/admin) with inactive user blocking.
4. **Comprehensive RLS design** (`schema_v3.4.sql`): 28+ policies for multi-tenant isolation (though ineffective due to C-2).
5. **Request ID tracing** (`request_id.py`): Full request lifecycle logging with correlation IDs.
6. **Rate limiting infrastructure** (`rate_limit.py`): SlowAPI with per-user key function.
7. **File extension allowlist** (`routes_files.py` line 21, `config.py` line 67).
8. **Audit logging** (`audit_service.py`): Key admin actions are recorded.
9. **Private Storage bucket** (`main.py` line 72): `"public": False`.
10. **Signed URLs for downloads** (`routes_files.py` line 157): 1-hour expiry.
11. **Self-signup blocking** (`auth_service.py` line 46): Only pre-registered users can access.

---

## Remediation Priority

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 1 (NOW) | C-1 Rotate secrets | 1h | Prevents credential abuse |
| 2 (NOW) | C-2 RLS-enforced client | 4h | Enables multi-tenant isolation |
| 3 (24h) | H-1 Fix auth on proposals | 1h | Blocks anonymous access |
| 4 (24h) | H-2 Add project access checks | 2h | Prevents cross-project access |
| 5 (48h) | H-3 SSRF URL validation | 2h | Blocks internal network probing |
| 6 (48h) | H-4 File size enforcement | 30m | Prevents DoS |
| 7 (48h) | H-5 CSRF protection | 1h | Prevents cross-origin attacks |
| 8 (sprint) | M-1 Security headers | 30m | Defense in depth |
| 9 (sprint) | M-2 Prompt injection defense | 4h | AI safety |
| 10 (sprint) | M-3 Sanitize error responses | 2h | Reduce info leakage |

---

## Appendix: Files Audited

| Category | Files |
|----------|-------|
| Auth/Authz | `app/api/deps.py`, `app/services/auth_service.py`, `app/api/routes_auth.py` |
| API Routes | `routes_proposal.py`, `routes_workflow.py`, `routes_files.py`, `routes_admin.py`, `routes_kb.py` |
| Config/Secrets | `app/config.py`, `.env`, `frontend/.env.local`, `.gitignore` |
| Database | `database/schema_v3.4.sql` |
| LangGraph | `app/graph/state.py`, `app/api/routes_workflow.py` |
| Services | `claude_client.py`, `rfp_parser.py`, `session_manager.py`, `notification_service.py` |
| Middleware | `app/middleware/rate_limit.py`, `app/middleware/request_id.py`, `app/main.py` |
| Models | `app/models/schemas.py` |
| Infrastructure | `app/utils/supabase_client.py`, `app/exceptions.py` |
