# Dashboard Permission Validation Tests & Backend Permission Validation
Cohesion: 0.10 | Nodes: 22

## Key Nodes
- **Dashboard Permission Validation Tests** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 8 connections
  - -> contains -> [[overview]]
  - -> contains -> [[backend-permission-validation]]
  - -> contains -> [[frontend-permission-validation]]
  - -> contains -> [[manual-testing-checklist]]
  - -> contains -> [[role-hierarchy]]
  - -> contains -> [[implementation-details]]
  - -> contains -> [[troubleshooting]]
  - -> contains -> [[success-criteria]]
- **Backend Permission Validation** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 4 connections
  - -> contains -> [[endpoint-get-apidashboardteam]]
  - -> contains -> [[endpoint-get-apidashboarddivision]]
  - -> contains -> [[endpoint-get-apidashboardcompany]]
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Manual Testing Checklist** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 4 connections
  - -> contains -> [[prerequisites]]
  - -> contains -> [[test-execution]]
  - -> contains -> [[browser-console]]
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Troubleshooting** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 4 connections
  - -> contains -> [[issue-403-error-persists-after-click]]
  - -> contains -> [[issue-error-message-not-appearing]]
  - -> contains -> [[issue-scope-not-auto-downgrading-after-3-seconds]]
  - <- contains <- [[dashboard-permission-validation-tests]]
- **json** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 3 connections
  - <- has_code_example <- [[endpoint-get-apidashboardteam]]
  - <- has_code_example <- [[endpoint-get-apidashboarddivision]]
  - <- has_code_example <- [[endpoint-get-apidashboardcompany]]
- **Implementation Details** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 3 connections
  - -> contains -> [[backend-changes]]
  - -> contains -> [[frontend-changes]]
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Endpoint: GET /api/dashboard/company** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[backend-permission-validation]]
- **Endpoint: GET /api/dashboard/division** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[backend-permission-validation]]
- **Endpoint: GET /api/dashboard/team** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[backend-permission-validation]]
- **Frontend Permission Validation** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 2 connections
  - -> contains -> [[component-dashboardpage-frontendappappdashboardpagetsx]]
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Backend Changes** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[implementation-details]]
- **Browser Console** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[manual-testing-checklist]]
- **Component: DashboardPage (`frontend/app/(app)/dashboard/page.tsx`)** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[frontend-permission-validation]]
- **Frontend Changes** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[implementation-details]]
- **Issue: 403 error persists after "팀으로 변경" click** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[troubleshooting]]
- **Issue: Error message not appearing** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[troubleshooting]]
- **Issue: Scope not auto-downgrading after 3 seconds** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[troubleshooting]]
- **Overview** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Prerequisites** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[manual-testing-checklist]]
- **Role Hierarchy** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Success Criteria** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[dashboard-permission-validation-tests]]
- **Test Execution** (C:\project\tenopa proposer\docs\DASHBOARD_PERMISSION_TESTS.md) -- 1 connections
  - <- contains <- [[manual-testing-checklist]]

## Internal Relationships
- Backend Permission Validation -> contains -> Endpoint: GET /api/dashboard/team [EXTRACTED]
- Backend Permission Validation -> contains -> Endpoint: GET /api/dashboard/division [EXTRACTED]
- Backend Permission Validation -> contains -> Endpoint: GET /api/dashboard/company [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Overview [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Backend Permission Validation [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Frontend Permission Validation [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Manual Testing Checklist [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Role Hierarchy [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Implementation Details [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Troubleshooting [EXTRACTED]
- Dashboard Permission Validation Tests -> contains -> Success Criteria [EXTRACTED]
- Endpoint: GET /api/dashboard/company -> has_code_example -> json [EXTRACTED]
- Endpoint: GET /api/dashboard/division -> has_code_example -> json [EXTRACTED]
- Endpoint: GET /api/dashboard/team -> has_code_example -> json [EXTRACTED]
- Frontend Permission Validation -> contains -> Component: DashboardPage (`frontend/app/(app)/dashboard/page.tsx`) [EXTRACTED]
- Implementation Details -> contains -> Backend Changes [EXTRACTED]
- Implementation Details -> contains -> Frontend Changes [EXTRACTED]
- Manual Testing Checklist -> contains -> Prerequisites [EXTRACTED]
- Manual Testing Checklist -> contains -> Test Execution [EXTRACTED]
- Manual Testing Checklist -> contains -> Browser Console [EXTRACTED]
- Troubleshooting -> contains -> Issue: 403 error persists after "팀으로 변경" click [EXTRACTED]
- Troubleshooting -> contains -> Issue: Error message not appearing [EXTRACTED]
- Troubleshooting -> contains -> Issue: Scope not auto-downgrading after 3 seconds [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Dashboard Permission Validation Tests, Backend Permission Validation, Manual Testing Checklist를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 DASHBOARD_PERMISSION_TESTS.md이다.

### Key Facts
- Endpoint: GET /api/dashboard/team **Required Role:** None (any authenticated user)
- Prerequisites 1. Deploy backend changes to staging 2. Ensure Supabase database has: - Users with different roles (member, lead, director, executive, admin) - Some users assigned to teams and divisions - Sample proposal data with win/loss results
- Issue: 403 error persists after "팀으로 변경" click - **Cause:** State update may not trigger scope change properly - **Solution:** Clear browser localStorage (dashboard widget config) and reload
- 1. **TC-DPT-01: Team scope access without team_id** - User: member (no team_id) - Expected: 200 OK with empty stats/pipeline - Request: `GET /api/dashboard/team` - Response: ```json { "data": { "scope": "team", "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [],…
- Backend Changes - File: `app/api/routes_performance.py` - Changes: - `dashboard_division`: Added `require_role("director", "executive", "admin")` - `dashboard_company`: Already uses `require_role("executive", "admin")` - `dashboard_team`: No explicit role check (accessible to all)
