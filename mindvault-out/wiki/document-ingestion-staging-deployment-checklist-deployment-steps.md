# Document Ingestion - Staging Deployment Checklist & Deployment Steps
Cohesion: 0.09 | Nodes: 25

## Key Nodes
- **Document Ingestion - Staging Deployment Checklist** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 11 connections
  - -> contains -> [[pre-deployment-checklist]]
  - -> contains -> [[deployment-steps]]
  - -> contains -> [[current-test-results]]
  - -> contains -> [[deployment-commands]]
  - -> contains -> [[success-criteria-for-staging]]
  - -> contains -> [[rollback-plan]]
  - -> contains -> [[monitoring-in-staging]]
  - -> contains -> [[post-deployment-steps]]
  - -> contains -> [[estimated-timeline]]
  - -> contains -> [[contacts-resources]]
  - -> contains -> [[questions]]
- **Deployment Steps** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 5 connections
  - -> contains -> [[phase-1-verify-local-works-now]]
  - -> contains -> [[phase-2-deploy-to-staging-in-30-min]]
  - -> contains -> [[phase-3-staging-validation-in-1-hour]]
  - -> contains -> [[phase-4-production-deployment-next-day]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **bash** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 4 connections
  - <- has_code_example <- [[step-1-commit-push]]
  - <- has_code_example <- [[step-2-verify-deployment]]
  - <- has_code_example <- [[rollback-plan]]
  - <- has_code_example <- [[logs-to-watch]]
- **Current Test Results** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 3 connections
  - -> contains -> [[smoke-test-file-upload]]
  - -> contains -> [[pending-async-processing-completion]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Deployment Commands** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 3 connections
  - -> contains -> [[step-1-commit-push]]
  - -> contains -> [[step-2-verify-deployment]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Monitoring in Staging** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 3 connections
  - -> contains -> [[logs-to-watch]]
  - -> contains -> [[metrics-to-track]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Post-Deployment Steps** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 3 connections
  - -> contains -> [[if-staging-passes]]
  - -> contains -> [[if-staging-fails]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Logs to Watch** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[monitoring-in-staging]]
- **Rollback Plan** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Step 1: Commit & Push** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[deployment-commands]]
- **Step 2: Verify Deployment** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[deployment-commands]]
- **Contacts & Resources** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Estimated Timeline** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **If Staging ❌ Fails:** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[post-deployment-steps]]
- **If Staging ✅ Passes:** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[post-deployment-steps]]
- **Metrics to Track** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[monitoring-in-staging]]
- **⏳ Pending: Async Processing Completion** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[current-test-results]]
- **Phase 1: Verify Local Works (NOW)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[deployment-steps]]
- **Phase 2: Deploy to Staging (IN 30 MIN)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[deployment-steps]]
- **Phase 3: Staging Validation (IN 1 HOUR)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[deployment-steps]]
- **Phase 4: Production Deployment (NEXT DAY)** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[deployment-steps]]
- **Pre-Deployment Checklist** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **Questions?** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]
- **✅ Smoke Test: File Upload** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[current-test-results]]
- **Success Criteria for Staging** (C:\project\tenopa proposer\-agent-master\STAGING_DEPLOYMENT.md) -- 1 connections
  - <- contains <- [[document-ingestion-staging-deployment-checklist]]

## Internal Relationships
- Current Test Results -> contains -> ✅ Smoke Test: File Upload [EXTRACTED]
- Current Test Results -> contains -> ⏳ Pending: Async Processing Completion [EXTRACTED]
- Deployment Commands -> contains -> Step 1: Commit & Push [EXTRACTED]
- Deployment Commands -> contains -> Step 2: Verify Deployment [EXTRACTED]
- Deployment Steps -> contains -> Phase 1: Verify Local Works (NOW) [EXTRACTED]
- Deployment Steps -> contains -> Phase 2: Deploy to Staging (IN 30 MIN) [EXTRACTED]
- Deployment Steps -> contains -> Phase 3: Staging Validation (IN 1 HOUR) [EXTRACTED]
- Deployment Steps -> contains -> Phase 4: Production Deployment (NEXT DAY) [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Pre-Deployment Checklist [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Deployment Steps [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Current Test Results [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Deployment Commands [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Success Criteria for Staging [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Rollback Plan [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Monitoring in Staging [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Post-Deployment Steps [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Estimated Timeline [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Contacts & Resources [EXTRACTED]
- Document Ingestion - Staging Deployment Checklist -> contains -> Questions? [EXTRACTED]
- Logs to Watch -> has_code_example -> bash [EXTRACTED]
- Monitoring in Staging -> contains -> Logs to Watch [EXTRACTED]
- Monitoring in Staging -> contains -> Metrics to Track [EXTRACTED]
- Post-Deployment Steps -> contains -> If Staging ✅ Passes: [EXTRACTED]
- Post-Deployment Steps -> contains -> If Staging ❌ Fails: [EXTRACTED]
- Rollback Plan -> has_code_example -> bash [EXTRACTED]
- Step 1: Commit & Push -> has_code_example -> bash [EXTRACTED]
- Step 2: Verify Deployment -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Document Ingestion - Staging Deployment Checklist, Deployment Steps, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 STAGING_DEPLOYMENT.md이다.

### Key Facts
- **Date**: 2026-04-07 **Status**: Ready for Staging **Target**: Get feature working in staging environment
- Phase 1: Verify Local Works (NOW) - [x] Migration 018 applied to Supabase - [x] Smoke test: File upload successful - [x] Smoke test: Document record created - [ ] Next: Async processing verification
- Step 1: Commit & Push ```bash cd /c/project/tenopa\ proposer/-agent-master
- ✅ Smoke Test: File Upload ``` Status: 201 Created Document ID: [generated UUID] Processing Status: extracting ```
- Step 1: Commit & Push ```bash cd /c/project/tenopa\ proposer/-agent-master
