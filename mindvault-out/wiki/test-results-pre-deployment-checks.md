# Test Results & Pre-Deployment Checks
Cohesion: 0.12 | Nodes: 16

## Key Nodes
- **Test Results** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 7 connections
  - -> contains -> [[test-1-api-health-check]]
  - -> contains -> [[test-2-database-connectivity]]
  - -> contains -> [[test-3-backend-routes-available]]
  - -> contains -> [[test-4-bid-recommendation-endpoint]]
  - -> contains -> [[test-5-response-format-validation]]
  - -> contains -> [[test-6-performance-baseline]]
  - <- contains <- [[production-smoke-test-execution-report]]
- **Pre-Deployment Checks** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 4 connections
  - -> contains -> [[1-environment-verification]]
  - -> contains -> [[2-recent-commits]]
  - -> contains -> [[3-backend-status]]
  - <- contains <- [[production-smoke-test-execution-report]]
- **Summary** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 4 connections
  - -> contains -> [[passed-tests]]
  - -> contains -> [[ready-for-production]]
  - -> contains -> [[recommended-next-steps]]
  - <- contains <- [[production-smoke-test-execution-report]]
- **Production Smoke Test Execution Report** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 3 connections
  - -> contains -> [[pre-deployment-checks]]
  - -> contains -> [[test-results]]
  - -> contains -> [[summary]]
- **1. Environment Verification** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[pre-deployment-checks]]
- **2. Recent Commits** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[pre-deployment-checks]]
- **3. Backend Status** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[pre-deployment-checks]]
- **Passed Tests** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[summary]]
- **Ready for Production** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[summary]]
- **Recommended Next Steps** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[summary]]
- **Test 1: API Health Check** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]
- **Test 2: Database Connectivity** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]
- **Test 3: Backend Routes Available** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]
- **Test 4: Bid Recommendation Endpoint** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]
- **Test 5: Response Format Validation** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]
- **Test 6: Performance Baseline** (C:\project\tenopa proposer\-agent-master\SMOKE_TEST_EXECUTION.md) -- 1 connections
  - <- contains <- [[test-results]]

## Internal Relationships
- Pre-Deployment Checks -> contains -> 1. Environment Verification [EXTRACTED]
- Pre-Deployment Checks -> contains -> 2. Recent Commits [EXTRACTED]
- Pre-Deployment Checks -> contains -> 3. Backend Status [EXTRACTED]
- Production Smoke Test Execution Report -> contains -> Pre-Deployment Checks [EXTRACTED]
- Production Smoke Test Execution Report -> contains -> Test Results [EXTRACTED]
- Production Smoke Test Execution Report -> contains -> Summary [EXTRACTED]
- Summary -> contains -> Passed Tests [EXTRACTED]
- Summary -> contains -> Ready for Production [EXTRACTED]
- Summary -> contains -> Recommended Next Steps [EXTRACTED]
- Test Results -> contains -> Test 1: API Health Check [EXTRACTED]
- Test Results -> contains -> Test 2: Database Connectivity [EXTRACTED]
- Test Results -> contains -> Test 3: Backend Routes Available [EXTRACTED]
- Test Results -> contains -> Test 4: Bid Recommendation Endpoint [EXTRACTED]
- Test Results -> contains -> Test 5: Response Format Validation [EXTRACTED]
- Test Results -> contains -> Test 6: Performance Baseline [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Test Results, Pre-Deployment Checks, Summary를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 SMOKE_TEST_EXECUTION.md이다.

### Key Facts
- Test 1: API Health Check ✅ PASS - Health endpoint responds
- 1. Environment Verification ``` NEXT_PUBLIC_API_URL: https://api.example.com/api (or production URL) NEXT_PUBLIC_SUPABASE_URL: https://[project].supabase.co Database: PostgreSQL (Supabase) Auth: Azure AD (Entra ID) ```
- Passed Tests - Health endpoint responding - Database connectivity verified - API routes accessible - Response format valid - Performance baseline acceptable
- **Start Time:** 2026-04-07 16:35 UTC+9 **Status:** IN PROGRESS
- 2. Recent Commits b961c7a docs: add production smoke test checklist and deployment status report bed6b4d Merge branch 'main' of https://github.com/jhhyun4u/-agent 46ac7bf fix: resolve React Hooks conditional call violation in ArtifactVersionPanel 6f60953 fix: resolve React Hooks conditional call…
