# bash & Production Smoke Test Checklist
Cohesion: 0.16 | Nodes: 17

## Key Nodes
- **bash** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 7 connections
  - <- has_code_example <- [[1-authentication-users]]
  - <- has_code_example <- [[2-proposal-management]]
  - <- has_code_example <- [[3-workflow-graph]]
  - <- has_code_example <- [[4-bid-recommendation-new-my-fix]]
  - <- has_code_example <- [[artifact-versioning-phase-1]]
  - <- has_code_example <- [[document-ingestion-phase-2]]
  - <- has_code_example <- [[logs-to-check]]
- **Production Smoke Test Checklist** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 7 connections
  - -> contains -> [[pre-test-verification]]
  - -> contains -> [[core-api-tests-phase-1]]
  - -> contains -> [[critical-path-tests-phase-2]]
  - -> contains -> [[success-criteria]]
  - -> contains -> [[monitoring]]
  - -> contains -> [[rollback-plan]]
  - -> contains -> [[sign-off]]
- **Core API Tests (Phase 1)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 5 connections
  - -> contains -> [[1-authentication-users]]
  - -> contains -> [[2-proposal-management]]
  - -> contains -> [[3-workflow-graph]]
  - -> contains -> [[4-bid-recommendation-new-my-fix]]
  - <- contains <- [[production-smoke-test-checklist]]
- **Critical Path Tests (Phase 2)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 3 connections
  - -> contains -> [[artifact-versioning-phase-1]]
  - -> contains -> [[document-ingestion-phase-2]]
  - <- contains <- [[production-smoke-test-checklist]]
- **Monitoring** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 3 connections
  - -> contains -> [[logs-to-check]]
  - -> contains -> [[key-metrics]]
  - <- contains <- [[production-smoke-test-checklist]]
- **1. Authentication & Users** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[core-api-tests-phase-1]]
- **2. Proposal Management** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[core-api-tests-phase-1]]
- **3. Workflow (Graph)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[core-api-tests-phase-1]]
- **4. Bid Recommendation (NEW - My Fix)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[core-api-tests-phase-1]]
- **Artifact Versioning (Phase 1)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[critical-path-tests-phase-2]]
- **Document Ingestion (Phase 2)** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[critical-path-tests-phase-2]]
- **Logs to Check** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[monitoring]]
- **Key Metrics** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 1 connections
  - <- contains <- [[monitoring]]
- **Pre-Test Verification** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 1 connections
  - <- contains <- [[production-smoke-test-checklist]]
- **Rollback Plan** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 1 connections
  - <- contains <- [[production-smoke-test-checklist]]
- **Sign-Off** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 1 connections
  - <- contains <- [[production-smoke-test-checklist]]
- **Success Criteria** (C:\project\tenopa proposer\-agent-master\PRODUCTION_SMOKE_TEST_CHECKLIST.md) -- 1 connections
  - <- contains <- [[production-smoke-test-checklist]]

## Internal Relationships
- 1. Authentication & Users -> has_code_example -> bash [EXTRACTED]
- 2. Proposal Management -> has_code_example -> bash [EXTRACTED]
- 3. Workflow (Graph) -> has_code_example -> bash [EXTRACTED]
- 4. Bid Recommendation (NEW - My Fix) -> has_code_example -> bash [EXTRACTED]
- Artifact Versioning (Phase 1) -> has_code_example -> bash [EXTRACTED]
- Core API Tests (Phase 1) -> contains -> 1. Authentication & Users [EXTRACTED]
- Core API Tests (Phase 1) -> contains -> 2. Proposal Management [EXTRACTED]
- Core API Tests (Phase 1) -> contains -> 3. Workflow (Graph) [EXTRACTED]
- Core API Tests (Phase 1) -> contains -> 4. Bid Recommendation (NEW - My Fix) [EXTRACTED]
- Critical Path Tests (Phase 2) -> contains -> Artifact Versioning (Phase 1) [EXTRACTED]
- Critical Path Tests (Phase 2) -> contains -> Document Ingestion (Phase 2) [EXTRACTED]
- Document Ingestion (Phase 2) -> has_code_example -> bash [EXTRACTED]
- Logs to Check -> has_code_example -> bash [EXTRACTED]
- Monitoring -> contains -> Logs to Check [EXTRACTED]
- Monitoring -> contains -> Key Metrics [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Pre-Test Verification [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Core API Tests (Phase 1) [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Critical Path Tests (Phase 2) [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Success Criteria [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Monitoring [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Rollback Plan [EXTRACTED]
- Production Smoke Test Checklist -> contains -> Sign-Off [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bash, Production Smoke Test Checklist, Core API Tests (Phase 1)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PRODUCTION_SMOKE_TEST_CHECKLIST.md이다.

### Key Facts
- 1. Authentication & Users ```bash Test Azure AD SSO curl -X POST https://api.example.com/api/auth/login \ -H "Authorization: Bearer {token}" \ -H "Content-Type: application/json"
- **Date:** 2026-04-07 (16:25 UTC+9) **Status:** Ready to Execute **Backend:** ✅ All 322 tests passing
- 1. Authentication & Users ```bash Test Azure AD SSO curl -X POST https://api.example.com/api/auth/login \ -H "Authorization: Bearer {token}" \ -H "Content-Type: application/json"
- Artifact Versioning (Phase 1) ```bash Get artifact versions curl https://api.example.com/api/proposals/{id}/artifacts/versions \ -H "Authorization: Bearer {token}" ```
- Logs to Check ```bash Backend logs (Render/Railway) tail -f logs/production.log
