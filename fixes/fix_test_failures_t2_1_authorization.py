"""
Fix T2.1: Authorization Validation (5 failing tests)

File: app/api/deps.py
Location: require_role() function around line 180

Current: require_role() only checks if user.role is in the allowed roles list
Issue: Does not validate endpoint-level permission requirements in some cases

Fix: Enhance require_role() to validate against endpoint metadata if available
"""

# CURRENT CODE (app/api/deps.py, lines 175-195):
"""
def require_role(*roles: str):
    '''역할 기반 접근 제어 데코레이터.

    사용법:
        @router.get("/admin")
        async def admin_page(user=Depends(require_role("admin", "executive"))):
            ...
    '''
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise AuthInsufficientRoleError(list(roles), user.role)
        _validate_user_status(user)
        return user
    return _check
"""

# ANALYSIS:
# The require_role() function IS correctly validating roles. The issue is that
# some endpoints don't use require_role() at all, or pass incorrect required roles.
#
# Tests failing:
# 1. test_unauthorized_team_access — Missing role check on GET /api/dashboard/metrics/team
# 2. test_no_auth_header_returns_401 — Missing auth header validation
# 3. test_websocket_unauthorized_access — WebSocket auth not checking role
# 4. test_unauthorized_job_status — Job queue endpoint missing role requirement
# 5. test_forbidden_access_other_team — Cross-team access control missing

# FIXES NEEDED:

# Fix 1: app/api/routes_dashboard.py (around line 200+)
# BEFORE:
"""
@router.get("/metrics/team")
async def get_team_metrics(
    dashboard_type: str = Query(...),
    user: CurrentUser = Depends(get_current_user),
):
    ...
"""

# AFTER:
"""
@router.get("/metrics/team")
async def get_team_metrics(
    dashboard_type: str = Query(...),
    user: CurrentUser = Depends(require_role("lead", "director", "executive", "admin")),
):
    ...
"""

# Fix 2: app/api/routes_jobs.py (around line 50+)
# BEFORE:
"""
@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    ...
"""

# AFTER:
"""
@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    user: CurrentUser = Depends(require_role("member", "lead", "director", "executive", "admin")),
):
    # Enforce team access control (same team or admin)
    job = await job_service.get_job(job_id)
    if job.team_id != user.team_id and user.role != "admin":
        raise AuthProjectAccessError(job_id, user.id)
    return job_status
"""

# Fix 3: WebSocket endpoint (app/api/routes_*.py for WebSocket handlers)
# BEFORE:
"""
@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ...
"""

# AFTER:
"""
@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    # Validate auth token from headers/query
    token = websocket.headers.get("authorization", "").replace("Bearer ", "")
    if not token:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    try:
        client = await get_async_client()
        user_auth = await client.auth.get_user(token)
        if not user_auth:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=1008, reason="Auth failed")
        return

    await websocket.accept()
    ...
"""

# IMPLEMENTATION STEPS:
print("""
Steps to fix authorization (T2.1):

1. Open app/api/routes_dashboard.py
2. Find GET /api/dashboard/metrics/team endpoint (line ~200)
3. Change require_role parameter from "current_user" to:
   Depends(require_role("lead", "director", "executive", "admin"))
4. Repeat for all 4 dashboard endpoints
5. Open app/api/routes_jobs.py
6. Add require_role() to GET /status/{job_id} endpoint
7. Add team access control check
8. Open WebSocket handler (find @router.websocket)
9. Add auth token validation before accepting connection
10. Run tests: pytest -k "test_unauthorized" -v
11. All 5 should pass
""")
