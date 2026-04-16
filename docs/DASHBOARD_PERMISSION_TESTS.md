# Dashboard Permission Validation Tests

## Overview

This document describes the test scenarios for dashboard scope-based permission validation (Task 3.5).

## Backend Permission Validation

### Endpoint: GET /api/dashboard/team
**Required Role:** None (any authenticated user)

**Permission Logic:**
- Returns empty data if user has no `team_id`
- Returns only the user's team data if `team_id` is set
- No explicit role check (accessible to all roles)

**Test Cases:**

1. **TC-DPT-01: Team scope access without team_id**
   - User: member (no team_id)
   - Expected: 200 OK with empty stats/pipeline
   - Request: `GET /api/dashboard/team`
   - Response:
     ```json
     {
       "data": {
         "scope": "team",
         "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []},
         "performance": null,
         "pipeline": {"registered": 0, "inProgress": 0, "completed": 0, "pending": 0, "won": 0, "lost": 0}
       }
     }
     ```

2. **TC-DPT-02: Team scope access with team_id**
   - User: member (team_id = "team-abc")
   - Expected: 200 OK with team data
   - Request: `GET /api/dashboard/team`
   - Response: Team stats and performance data

---

### Endpoint: GET /api/dashboard/division
**Required Role:** director, executive, admin

**Permission Logic:**
- Returns 403 if user lacks required role
- Returns empty data if user has no `division_id`
- Returns division-wide data for all teams in user's division if authorized

**Test Cases:**

1. **TC-DPD-01: Division scope access without permission**
   - User: lead (no director+ role)
   - Expected: 403 Forbidden (AuthInsufficientRoleError)
   - Request: `GET /api/dashboard/division`
   - Response:
     ```json
     {
       "code": "AUTH_002",
       "message": "권한 부족: lead (필요: director, executive, admin)",
       "status": 403,
       "data": {
         "required_roles": ["director", "executive", "admin"],
         "current_role": "lead"
       }
     }
     ```

2. **TC-DPD-02: Division scope access with director role but no division_id**
   - User: director (no division_id)
   - Expected: 200 OK with empty teams
   - Request: `GET /api/dashboard/division`
   - Response:
     ```json
     {
       "data": {
         "scope": "division",
         "teams": [],
         "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []}
       }
     }
     ```

3. **TC-DPD-03: Division scope access with director role and division_id**
   - User: director (division_id = "div-xyz")
   - Expected: 200 OK with division data
   - Request: `GET /api/dashboard/division`
   - Response: Teams and their performance stats

4. **TC-DPD-04: Division scope access with executive role**
   - User: executive (division_id = "div-xyz")
   - Expected: 200 OK (executive has director+ privilege)
   - Request: `GET /api/dashboard/division`
   - Response: Teams and their performance stats

---

### Endpoint: GET /api/dashboard/company
**Required Role:** executive, admin

**Permission Logic:**
- Returns 403 if user lacks required role (executive or admin)
- Returns company-wide data for all proposals

**Test Cases:**

1. **TC-DPC-01: Company scope access without permission**
   - User: director
   - Expected: 403 Forbidden
   - Request: `GET /api/dashboard/company`
   - Response:
     ```json
     {
       "code": "AUTH_002",
       "message": "권한 부족: director (필요: executive, admin)",
       "status": 403,
       "data": {
         "required_roles": ["executive", "admin"],
         "current_role": "director"
       }
     }
     ```

2. **TC-DPC-02: Company scope access with executive role**
   - User: executive
   - Expected: 200 OK with company-wide data
   - Request: `GET /api/dashboard/company`
   - Response: All proposals, by_month aggregation, overall stats

3. **TC-DPC-03: Company scope access with admin role**
   - User: admin
   - Expected: 200 OK (admin has executive privilege)
   - Request: `GET /api/dashboard/company`
   - Response: All proposals, by_month aggregation, overall stats

---

## Frontend Permission Validation

### Component: DashboardPage (`frontend/app/(app)/dashboard/page.tsx`)

**Error Handling:**
- Permission errors (403) are caught in `loadStats()` callback
- Error message is displayed in UI with user-friendly text
- Scope is automatically downgraded to "team" after 3 seconds

**Test Cases:**

1. **TC-FPE-01: Display division permission error**
   - User: member (role=lead)
   - Action: Click "본부" scope button
   - Expected: 
     - Error message: "본부 권한이 없습니다. 본부장 이상이 필요합니다."
     - "팀으로 변경" button appears
     - After 3 seconds: scope automatically switches to "team"

2. **TC-FPE-02: Display company permission error**
   - User: team lead (role=director)
   - Action: Click "전체" scope button
   - Expected:
     - Error message: "전사 권한이 없습니다. 경영진 이상이 필요합니다."
     - "팀으로 변경" button appears
     - After 3 seconds: scope automatically switches to "team"

3. **TC-FPE-03: Manual scope downgrade via error button**
   - User: member
   - Precondition: Permission error is displayed for division scope
   - Action: Click "팀으로 변경" button
   - Expected: Scope immediately switches to "team", error disappears

4. **TC-FPE-04: Successful scope access**
   - User: director with valid division_id
   - Action: Click "본부" scope button
   - Expected: No error, division data loads successfully

---

## Manual Testing Checklist

### Prerequisites
1. Deploy backend changes to staging
2. Ensure Supabase database has:
   - Users with different roles (member, lead, director, executive, admin)
   - Some users assigned to teams and divisions
   - Sample proposal data with win/loss results

### Test Execution

- [ ] **Team Scope**
  - [ ] TC-DPT-01: Member without team_id sees empty data
  - [ ] TC-DPT-02: Member with team_id sees their team data
  - [ ] Frontend: Scope selection works without errors

- [ ] **Division Scope**
  - [ ] TC-DPD-01: Member trying to access division scope gets 403 error
  - [ ] TC-DPD-02: Director without division_id sees empty teams
  - [ ] TC-DPD-03: Director with division_id sees team data
  - [ ] TC-DPD-04: Executive can access division scope
  - [ ] Frontend: Error message appears and auto-downgrade works

- [ ] **Company Scope**
  - [ ] TC-DPC-01: Director trying to access company scope gets 403 error
  - [ ] TC-DPC-02: Executive sees all company data
  - [ ] TC-DPC-03: Admin can access company scope
  - [ ] Frontend: Error message appears and auto-downgrade works

### Browser Console
- [ ] No console errors when switching scopes
- [ ] Permission error caught gracefully
- [ ] Network requests show correct 403 status for unauthorized access

---

## Role Hierarchy

```
admin (highest privilege)
  ├─ executive
  ├─ director
  └─ lead
      └─ member (lowest privilege)
```

**Permission Requirements:**
- `team` scope: Any authenticated user (member+)
- `division` scope: director+
- `company` scope: executive+

---

## Implementation Details

### Backend Changes
- File: `app/api/routes_performance.py`
- Changes:
  - `dashboard_division`: Added `require_role("director", "executive", "admin")`
  - `dashboard_company`: Already uses `require_role("executive", "admin")`
  - `dashboard_team`: No explicit role check (accessible to all)

### Frontend Changes
- File: `frontend/app/(app)/dashboard/page.tsx`
- Changes:
  - Added `scopeError` state to track permission errors
  - Enhanced `loadStats` with 403 error detection
  - Added error display with auto-downgrade functionality
  - User gets 3 seconds to read error before auto-switching to team scope

---

## Troubleshooting

### Issue: 403 error persists after "팀으로 변경" click
- **Cause:** State update may not trigger scope change properly
- **Solution:** Clear browser localStorage (dashboard widget config) and reload

### Issue: Error message not appearing
- **Cause:** Error detection may not work with all API client versions
- **Solution:** Check browser console for actual error response format, update status code detection logic

### Issue: Scope not auto-downgrading after 3 seconds
- **Cause:** Timeout may conflict with other state updates
- **Solution:** Verify no other async operations are interfering with `setScope("team")`

---

## Success Criteria

✅ All TC-DPT tests pass (team scope always accessible)
✅ All TC-DPD tests pass (division scope role validation works)
✅ All TC-DPC tests pass (company scope role validation works)
✅ All TC-FPE tests pass (frontend error handling works)
✅ Role hierarchy is correctly enforced
✅ No console errors during permission validation
