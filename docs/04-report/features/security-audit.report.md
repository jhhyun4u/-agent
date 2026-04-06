# Security Audit Report — 용역제안 Coworker

**Date**: 2026-03-26
**Auditor**: Security Architect Agent
**Scope**: Full backend (`app/`) + frontend (`frontend/`) security review
**Framework**: OWASP Top 10 (2021) + project-specific controls

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | Immediate action required |
| HIGH | 5 | Fix before production release |
| MEDIUM | 6 | Fix in next sprint |
| LOW | 4 | Track in backlog |
| INFO | 3 | Best practice notes |

**Overall Risk**: HIGH — One critical secret exposure and several high-severity issues that must be resolved before any production deployment.

---

## CRITICAL Findings

### C-1. Live API Keys and Secrets Committed to Repository

**Severity**: CRITICAL
**OWASP**: A02 Cryptographic Failures
**File**: `.env` (repository root)

The `.env` file contains live, real credentials:

- `ANTHROPIC_API_KEY=sk-ant-api03-hvPYPYZw1o...` (line 2)
- `G2B_API_KEY=0c72ec113c29...` (line 1)
- `SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...` (line 8) — **full admin access, bypasses RLS**
- `SUPABASE_KEY=eyJhbGci...` (line 6)
- `SUPABASE_URL=https://inuuyaxddgbxexljfykg.supabase.co` (line 5)

Additionally, `frontend/.env.local` contains:

- `E2E_USER_PASSWORD=e2e-test-password-2026!` (line 8)
- Supabase URL and anon key (lines 2-3)

**Impact**: Although `.env` is in `.gitignore`, the file exists locally and the `.env.local` in `frontend/` is NOT excluded by `.gitignore` (only `.env*.local` at root level is excluded). If this repository is shared or pushed, all keys are exposed. The `SUPABASE_SERVICE_ROLE_KEY` grants full database access including bypassing all RLS policies.

**Remediation**:
1. **Immediately rotate all keys**: Anthropic API key, G2B API key, Supabase service_role_key
2. Add `frontend/.env.local` explicitly to `.gitignore` (current pattern `frontend/.env*.local` may not match)
3. Use a secrets manager (Azure Key Vault, Doppler, or Vercel/Railway environment variables)
4. Run `git log` to verify these keys were never committed to git history
5. Verify `.gitignore` patterns: `frontend/.env.local` should be tested

---

## HIGH Findings

### H-1. Dev Mode Authentication Bypass Has No Environment Guard

**Severity**: HIGH
**OWASP**: A07 Identification and Authentication Failures
**File**: `app/api/deps.py:67-68, 79-80, 84-85`

```python
if settings.dev_mode and (not credentials or not credentials.credentials):
    return await _get_dev_user()
```

When `DEV_MODE=true` (currently set in `.env`), ALL authentication is bypassed. Any request without a token returns a hardcoded user with `role="lead"`. The dev mode fallback also triggers on ANY auth exception (lines 79-80), meaning a malformed token still gets full access.

**Impact**: If deployed with `DEV_MODE=true` (which is the current default in `.env`), the entire application is unauthenticated.

**Remediation**:
1. Add startup validation: if `DEV_MODE=true` and environment appears to be production (e.g., `log_format=json` or explicit `ENVIRONMENT=production`), refuse to start
2. Remove dev_mode fallback on auth exceptions (lines 79-80) — only apply on missing token
3. Log a prominent WARNING on startup when dev_mode is enabled

### H-2. RLS Bypass in Dev Mode via get_rls_client

**Severity**: HIGH
**OWASP**: A01 Broken Access Control
**File**: `app/api/deps.py:138-140`

```python
if settings.dev_mode and (not credentials or not credentials.credentials):
    return await get_async_client()  # Returns service_role client — bypasses ALL RLS
```

In dev mode, `get_rls_client` returns the `service_role` client instead of a user-scoped client. This completely disables Row Level Security.

**Impact**: Combined with H-1, any unauthenticated request in dev mode gets service_role-level database access.

**Remediation**: Even in dev mode, `get_rls_client` should return a client scoped to the dev user's JWT, not service_role. At minimum, log a warning.

### H-3. Admin Role Change Has No Cross-Organization Guard

**Severity**: HIGH
**OWASP**: A01 Broken Access Control
**File**: `app/api/routes_admin.py:77-91`

The `update_user_role` endpoint allows an admin to change ANY user's role by user_id, without verifying the target user belongs to the same organization:

```python
await client.table("users").update({"role": body.role}).eq("id", user_id).execute()
```

Similarly, `update_user_status` (line 98-112) has no org_id check.

**Impact**: An admin of Organization A could escalate privileges for or disable users in Organization B.

**Remediation**: Add `.eq("org_id", user.org_id)` to both update queries, and verify the response updated exactly 1 row.

### H-4. require_project_access Uses service_role Client

**Severity**: HIGH
**OWASP**: A01 Broken Access Control
**File**: `app/api/deps.py:185`

```python
client = await get_async_client()  # service_role — bypasses RLS
```

The `require_project_access` function uses the service_role client to query proposals. While the function implements application-level access checks, it bypasses database-level RLS. If there is a logic error in the role hierarchy check, there is no database-level safety net.

**Remediation**: Consider using the RLS client where possible, or add defense-in-depth logging when service_role access is used for authorization decisions.

### H-5. No Password Complexity Enforcement

**Severity**: HIGH
**OWASP**: A07 Identification and Authentication Failures
**File**: `app/models/user_schemas.py:97`

```python
new_password: str = Field(min_length=8)
```

Only minimum length (8) is enforced. No requirements for uppercase, lowercase, digits, or special characters. No check against common password lists.

**Remediation**: Add Pydantic validators for password complexity: at least one uppercase, one lowercase, one digit, min 10 characters. Consider using `zxcvbn` for password strength estimation.

---

## MEDIUM Findings

### M-1. Missing Content Security Policy (CSP) Header

**Severity**: MEDIUM
**OWASP**: A05 Security Misconfiguration
**File**: `app/middleware/security_headers.py`

The security headers middleware sets HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, and Permissions-Policy — but does NOT set a Content Security Policy header.

**Impact**: Without CSP, XSS attacks that bypass React's escaping (see M-2) can load arbitrary external scripts.

**Remediation**: Add a CSP header. Start with report-only mode:
```python
response.headers["Content-Security-Policy-Report-Only"] = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; connect-src 'self' https://*.supabase.co"
)
```

### M-2. Unsafe innerHTML Usage in Frontend Components

**Severity**: MEDIUM
**OWASP**: A03 Injection (XSS)
**Files**:
- `frontend/components/AiSuggestionDiff.tsx:43` — `div.innerHTML = html`
- `frontend/components/VersionCompareModal.tsx:22` — `div.innerHTML = html`
- `frontend/components/prompt/PromptEditor.tsx:61` — `dangerouslySetInnerHTML`

The `stripHtml` functions in `AiSuggestionDiff.tsx` and `VersionCompareModal.tsx` use `div.innerHTML = html` to parse HTML. While they immediately extract `.textContent`, this still triggers browser HTML parsing and could execute side effects in edge cases.

The `PromptEditor.tsx` uses `dangerouslySetInnerHTML` for syntax highlighting, which could be vulnerable if the highlighted content includes unsanitized user input.

The `layout.tsx` usage (line 18) is safe — it's a static inline script for theme detection.

**Remediation**: Replace `innerHTML` usage with `DOMParser` API or a sanitization library like DOMPurify. For PromptEditor, verify the highlighting library escapes user input.

### M-3. No CSRF Protection on State-Changing Endpoints

**Severity**: MEDIUM
**OWASP**: A05 Security Misconfiguration

The application uses Bearer token authentication (not cookies), which inherently mitigates CSRF for most scenarios. However, if the frontend stores the token in a cookie (httpOnly or not), CSRF becomes relevant.

Currently there is no explicit CSRF token mechanism. The `CORSMiddleware` in `main.py` restricts origins, which provides some protection.

**Remediation**: If auth tokens are stored in cookies, implement CSRF tokens. If tokens are stored in memory/localStorage only, document this as a design decision. Add `SameSite=Strict` to any cookies.

### M-4. Health/Status Endpoints Expose Internal Details

**Severity**: MEDIUM
**OWASP**: A05 Security Misconfiguration
**File**: `app/main.py:275-298`

The `/health` endpoint exposes database error type names:
```python
health["database"] = f"error: {type(e).__name__}"
```

The `/status` endpoint exposes active session count publicly (no auth required).

**Remediation**: Return generic "error" for database issues in production. Require admin role for detailed health info. Remove session count from unauthenticated `/status`.

### M-5. Missing org_id Scoping on KB Write Operations

**Severity**: MEDIUM
**OWASP**: A01 Broken Access Control
**File**: `app/api/routes_kb.py`

KB write operations (create content, client, competitor, lesson) use `get_current_user` for authentication but do not enforce org_id scoping. A user from Organization A could create or modify KB records that are visible to Organization B.

**Remediation**: Add `org_id` to all KB insert/update operations and filter reads by the user's org_id.

### M-6. Supabase Client Caching — Stale Auth Token

**Severity**: MEDIUM
**OWASP**: A07 Identification and Authentication Failures
**File**: `app/utils/supabase_client.py:39`

```python
await client.auth.set_session(user_jwt, "")
```

The `get_user_client` passes an empty string as the refresh token. If the JWT has expired, Supabase cannot refresh it. This could cause silent auth failures or unexpected behavior.

**Remediation**: Handle token refresh properly or validate JWT expiration before creating the client.

---

## LOW Findings

### L-1. Rate Limiting Not Applied Uniformly

**Severity**: LOW
**File**: `app/api/routes_workflow.py`, various route files

Rate limiting is applied selectively (start: 10/min, resume: 20/min, some file operations: 10/min) but many endpoints have no rate limits. Notably, `/api/proposals/{id}/state` (GET), AI status, and KB search have no rate limits.

**Remediation**: Apply default rate limits to all endpoints via middleware, with per-endpoint overrides as needed.

### L-2. Error Messages Include Internal State Details

**Severity**: LOW
**OWASP**: A09 Security Logging and Monitoring Failures
**File**: `app/api/routes_admin.py:421`

```python
raise TenopAPIError("WF_012", f"상태 조회 실패: {str(e)}", 500)
```

Exception messages are passed directly to API responses in several places. In production, these could reveal internal stack traces or database error details.

**Remediation**: Log the full error server-side; return generic messages to the client in production.

### L-3. Audit Logging Gaps

**Severity**: LOW
**OWASP**: A09 Security Logging and Monitoring Failures

Audit logging is applied to admin actions (role change, status change, reopen) and user management but is missing for:
- Workflow start/resume (logged to app logs but not audit_logs table)
- File uploads and deletions
- KB modifications (create/update/delete)
- Password changes

**Remediation**: Add audit_logs entries for all security-relevant actions.

### L-4. OpenAPI Docs Production Toggle Is Weak

**Severity**: LOW
**File**: `app/main.py:128`

```python
_is_production = settings.log_format == "json"
```

Production detection relies on `log_format` setting. If someone sets `json` logging in dev, or forgets to set it in prod, the docs endpoint state will be wrong.

**Remediation**: Use an explicit `ENVIRONMENT` setting (development/staging/production) instead of inferring from log format.

---

## INFO Findings

### I-1. SSRF Protection Implemented

**File**: `app/services/rfp_parser.py:12-46`

The `_validate_url` function properly blocks private/internal IP ranges and validates URL schemes. This is good defense against SSRF (OWASP A10).

### I-2. File Upload Validation Implemented

**File**: `app/utils/file_utils.py:209-247`

The `validate_upload` function includes filename sanitization (`os.path.basename`), extension whitelisting by category, and file size limits. This properly mitigates path traversal and dangerous file upload attacks.

### I-3. SQL Injection Risk is Low

The project uses the Supabase client library's query builder (`.eq()`, `.in_()`, `.ilike()`) throughout, which parameterizes values. No raw SQL queries were found in the API layer. The `.rpc()` calls in `main.py` use server-side functions without user-controlled parameters. SQL injection risk is minimal.

---

## Security Architecture Assessment

### Positive Controls Already in Place

| Control | Implementation | Status |
|---------|---------------|--------|
| JWT Authentication | Supabase Auth + deps.py | Implemented |
| Role-Based Access Control | require_role decorator | Implemented |
| Project-Level Access Control | require_project_access | Implemented |
| Security Headers | SecurityHeadersMiddleware (HSTS, X-Frame-Options, etc.) | Implemented |
| Rate Limiting | SlowAPI per-user/IP | Partially implemented |
| CORS | Configurable origins | Implemented |
| SSRF Protection | URL validation in rfp_parser | Implemented |
| File Upload Validation | Extension whitelist + size limits + filename sanitization | Implemented |
| Audit Logging | audit_service for admin actions | Partially implemented |
| Error Code System | TenopAPIError standardized errors | Implemented |
| Initial State Whitelist | C-4 _ALLOWED_INITIAL_STATE_KEYS | Implemented |
| Inactive User Blocking | require_role checks status | Implemented |
| OpenAPI Docs Production Toggle | Conditional /docs /redoc | Implemented |

### Priority Remediation Roadmap

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 1 (now) | C-1: Rotate all exposed keys | 1h | Eliminates credential theft risk |
| 2 (now) | H-1: Add production guard for DEV_MODE | 30m | Prevents unauthenticated production |
| 3 (this week) | H-3: Add org_id guard to admin operations | 1h | Prevents cross-org privilege escalation |
| 4 (this week) | H-5: Password complexity validation | 30m | Reduces brute-force risk |
| 5 (this sprint) | M-1: Add CSP header | 2h | Mitigates XSS |
| 6 (this sprint) | M-2: Fix innerHTML usage | 1h | Eliminates client-side XSS vectors |
| 7 (this sprint) | M-5: Add org_id to KB operations | 2h | Prevents cross-org data leakage |
| 8 (backlog) | H-2, H-4: Minimize service_role usage | 4h | Defense-in-depth |
| 9 (backlog) | L-1 through L-4 | 4h | Hardening |

---

## Appendix: Files Reviewed

- `app/api/deps.py` — Authentication and authorization dependencies
- `app/config.py` — Application configuration
- `app/main.py` — FastAPI application entry point
- `app/exceptions.py` — Error code system
- `app/services/auth_service.py` — Azure AD auth service
- `app/services/rfp_parser.py` — RFP parsing with SSRF protection
- `app/utils/supabase_client.py` — Database client utilities
- `app/utils/file_utils.py` — File upload validation
- `app/middleware/security_headers.py` — Security headers
- `app/middleware/rate_limit.py` — Rate limiting
- `app/api/routes_auth.py` — Authentication routes
- `app/api/routes_admin.py` — Admin routes
- `app/api/routes_workflow.py` — Workflow control
- `app/api/routes_files.py` — File management
- `app/api/routes_proposal.py` — Proposal CRUD
- `app/api/routes_users.py` — User management
- `app/api/routes_kb.py` — Knowledge base
- `app/api/routes_g2b.py` — G2B proxy
- `app/models/auth_schemas.py` — Auth models
- `app/models/user_schemas.py` — User models
- `frontend/app/layout.tsx` — Root layout
- `frontend/components/AiSuggestionDiff.tsx` — Diff component
- `frontend/components/VersionCompareModal.tsx` — Version compare
- `frontend/.env.local` — Frontend environment
- `.env` — Backend environment
- `.gitignore` — Git ignore patterns
