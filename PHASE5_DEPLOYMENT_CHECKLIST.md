# Phase 5 Scheduler Integration — Production Deployment Checklist

**Project:** tenopa proposer
**Phase:** 5 — Scheduler Integration (정기 문서 마이그레이션 자동화)
**Environment:** Production
**Deployment Date:** 2026-04-25 (Saturday)
**Deployment Lead:** @jhhyun4u (hyunjaeho@tenopa.co.kr)
**Risk Level:** LOW (staging validated for 17h with zero P1/P2 incidents)
**Rollback Window:** ≤ 10 minutes

---

## Deployment Timeline (UTC)

| Window          | Phase                                  | Duration | Owner           |
|-----------------|----------------------------------------|----------|-----------------|
| 05:45 – 06:00   | Deployment bridge opens, roll-call     | 15 min   | Deploy Lead     |
| 06:00 – 07:00   | Pre-flight checklist (Section A)       | 60 min   | Deploy Lead     |
| 07:00 – 07:30   | DB migration (Section B)               | 30 min   | DBA             |
| 07:30 – 08:00   | Migration verification (Section C)     | 30 min   | Deploy Lead     |
| 08:00 – 08:40   | Code deploy — Blue/Green (Section D)   | 40 min   | SRE             |
| 08:40 – 09:00   | Smoke tests + traffic cutover (Sec. E) | 20 min   | QA + SRE        |
| 09:00 – 09:00+72h | Monitoring (see PHASE5_DEPLOYMENT_MONITORING.md) | 72 h | Rotation      |

**Freeze window:** 2026-04-25 05:00 – 2026-04-26 00:00 UTC. No unrelated merges to `master`.

---

## Section A — Pre-Flight Checklist (2026-04-25 06:00 UTC)

Complete every item before 07:00 UTC. ANY `NO-GO` answer aborts the deployment and triggers reschedule.

### A.1 Team & Communication
- [ ] **06:00** — Deployment bridge (Teams channel `#tenopa-deploy`) active
- [ ] **06:00** — Deploy Lead, DBA, SRE, QA, On-call acknowledged in roll-call
- [ ] **06:05** — PagerDuty on-call rotation confirmed for next 72h
- [ ] **06:05** — Rollback decision-maker designated (Deploy Lead)
- [ ] **06:10** — Stakeholder announcement posted (#tenopa-general)

### A.2 Source of Truth Verification
- [ ] **06:10** — `master` branch HEAD commit recorded: `___________________`
- [ ] **06:10** — Staging deployed commit matches `master` HEAD (see `.bkit/runtime/deployment-status.json`)
- [ ] **06:15** — No merge conflicts between `master` and `release/phase5-prod`
- [ ] **06:15** — Release tag created: `v-phase5-prod-2026-04-25`

### A.3 Artifact Verification
- [ ] **06:15** — Migration SQL exists: `database/migrations/006_scheduler_integration.sql`
- [ ] **06:15** — `app/services/scheduler_service.py` (236 lines) present on release branch
- [ ] **06:15** — `app/services/concurrent_batch_processor.py` (222 lines) present
- [ ] **06:15** — `app/api/routes_scheduler.py` with 5 endpoints present
- [ ] **06:20** — Docker image built and pushed: `ecr://tenopa-proposer:phase5-2026-04-25`
- [ ] **06:20** — Image digest recorded: `sha256:___________________`

### A.4 Test Gate (Local/CI)
- [ ] **06:20** — CI pipeline green on release commit (GitHub Actions all green)
- [ ] **06:25** — `uv run pytest tests/test_scheduler_integration.py -v` → 24/24 PASS
- [ ] **06:25** — `uv run pytest tests/integration/ -k scheduler -v` → all PASS
- [ ] **06:30** — Static analysis (ruff, mypy) clean on release branch
- [ ] **06:30** — Security scan (Semgrep + Trivy) — 0 CRITICAL, 0 HIGH

### A.5 Infrastructure Readiness
- [ ] **06:30** — Production DB healthy (Supabase dashboard → Health: green)
- [ ] **06:35** — Production API healthy (last 24h error rate < 0.5%)
- [ ] **06:35** — Redis reachable from production VPC
- [ ] **06:35** — Azure AD (Entra ID) status page — operational
- [ ] **06:40** — Railway/Render deploy pipeline idle (no queued deploys)
- [ ] **06:40** — DNS TTL for `api.tenopa.co.kr` ≤ 300s (for fast cutover)

### A.6 Backup & Rollback Prep
- [ ] **06:40** — Fresh Supabase backup triggered; backup ID: `___________________`
- [ ] **06:45** — Backup verified (file size > 100 MB, no errors)
- [ ] **06:45** — Rollback SQL file reviewed: `database/migrations/006_scheduler_integration_rollback.sql`
- [ ] **06:50** — Previous stable image digest archived: `sha256:___________________`
- [ ] **06:50** — Rollback runbook reviewed by Deploy Lead (Section G below)

### A.7 Final GO/NO-GO
- [ ] **06:55** — All Section A items checked
- [ ] **06:55** — Go/No-Go poll executed (see `PHASE5_DEPLOYMENT_DECISION_MATRIX.md`)
- [ ] **07:00** — **GO** recorded in deployment log; proceed to Section B
- [ ] **07:00** — **NO-GO** → halt, reschedule, postmortem entry in `docs/04-report/`

---

## Section B — Database Migration (07:00 – 07:30 UTC)

### B.1 Pre-Migration Snapshot
- [ ] **07:00** — Connect to production DB via Supabase SQL Editor (via SSO)
- [ ] **07:00** — Confirm connection target: `production` (NOT staging)
- [ ] **07:02** — Capture current schema snapshot:
      `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;`
- [ ] **07:02** — Row counts recorded for pre-existing scheduler-adjacent tables (if any)

### B.2 Apply Migration 006_scheduler_integration.sql
- [ ] **07:05** — Open `database/migrations/006_scheduler_integration.sql`
- [ ] **07:05** — Wrap in transaction block (`BEGIN; ... COMMIT;`) — already done in file
- [ ] **07:10** — Execute migration
- [ ] **07:12** — Verify success message: `migration completed`
- [ ] **07:12** — No ERROR-level output in SQL result pane

### B.3 Tables Created Verification
- [ ] **07:15** — `migration_schedules` exists with 11 columns
- [ ] **07:15** — `migration_batches` exists with 9 columns
- [ ] **07:15** — `migration_logs` exists with 7 columns

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('migration_schedules','migration_batches','migration_logs')
ORDER BY table_name, ordinal_position;
```

### B.4 RLS & Indexes
- [ ] **07:20** — RLS enabled on all 3 new tables
- [ ] **07:20** — Service-role policy attached (application access)
- [ ] **07:22** — Indexes created: `idx_migration_schedules_active`, `idx_migration_batches_schedule_id`, `idx_migration_logs_batch_id`

### B.5 Rollback Dry-Run (Disaster Readiness)
- [ ] **07:25** — Rollback SQL file opened in separate window (NOT executed)
- [ ] **07:27** — DBA confirms rollback procedure visually
- [ ] **07:28** — `COMMIT` is final; migration locked in

---

## Section C — Migration Verification (07:30 – 08:00 UTC)

- [ ] **07:30** — Smoke query: `INSERT INTO migration_schedules (...) VALUES (...) RETURNING id;` → succeeds under service role
- [ ] **07:32** — Immediately `DELETE FROM migration_schedules WHERE id = <just_inserted>;` → clean test row
- [ ] **07:35** — Verify no existing API calls are breaking (grep last 10 min of logs for 5xx)
- [ ] **07:40** — Capture baseline metrics (pre-code-deploy):
  - Error rate (1m avg): `____%`
  - p95 latency: `____ ms`
  - Active DB connections: `____`
  - Redis hit rate: `____%`
- [ ] **07:50** — Baseline recorded in `PHASE5_DEPLOYMENT_MONITORING.md`
- [ ] **08:00** — DB checkpoint — GO/NO-GO for code deploy

---

## Section D — Blue/Green Code Deploy (08:00 – 08:40 UTC)

### D.1 Deploy GREEN Environment
- [ ] **08:00** — Trigger deploy to GREEN slot with image `ecr://tenopa-proposer:phase5-2026-04-25`
- [ ] **08:05** — GREEN container healthy (`GET /health` → 200)
- [ ] **08:05** — Scheduler lifecycle hooks booted (look for log: `SchedulerService started` / `APScheduler initialized`)
- [ ] **08:10** — GREEN connects to production DB successfully
- [ ] **08:10** — GREEN reads `migration_schedules` — returns 0 rows (expected, empty table)

### D.2 Scheduler Endpoint Verification (GREEN, pre-traffic)
Call each endpoint against GREEN directly (internal URL, bypass LB):

- [ ] **08:15** — `GET /api/scheduler/health` → 200 OK, `{"status":"healthy"}`
- [ ] **08:17** — `GET /api/scheduler/schedules` → 200 OK, `[]`
- [ ] **08:20** — `POST /api/scheduler/schedules` with valid payload → 201 Created
- [ ] **08:22** — `POST /api/scheduler/schedules/{id}/trigger` → 202 Accepted, batch_id returned
- [ ] **08:25** — `GET /api/scheduler/batches/{batch_id}` → 200 OK, status field present
- [ ] **08:27** — Cleanup: delete the test schedule created in step 3

### D.3 Traffic Cutover (Blue → Green)
- [ ] **08:30** — Load balancer weight: BLUE 100% / GREEN 0%
- [ ] **08:32** — Shift to BLUE 50% / GREEN 50%
- [ ] **08:34** — Monitor error rate for 2 min — must stay < 1.0%
- [ ] **08:36** — Shift to BLUE 0% / GREEN 100%
- [ ] **08:38** — Monitor error rate for 2 min — must stay < 1.0%
- [ ] **08:40** — Cutover complete; BLUE kept warm for 72h as rollback target

---

## Section E — Production Smoke Tests (08:40 – 09:00 UTC)

Execute against public URL `https://api.tenopa.co.kr`:

- [ ] **08:40** — `GET /api/scheduler/health` → 200 OK within 500ms
- [ ] **08:42** — `GET /api/scheduler/schedules` → 200 OK, JSON array
- [ ] **08:44** — Create + trigger + read batch full lifecycle → all PASS
- [ ] **08:48** — Unrelated critical endpoints still healthy:
  - `GET /api/proposal/list` → 200
  - `GET /api/users/me` → 200
  - `POST /api/workflow/start` (dry-run) → 200
- [ ] **08:52** — Sentry dashboard — no new issues since 08:00 UTC
- [ ] **08:55** — Log stream clean — no ERROR bursts
- [ ] **09:00** — Deploy Lead announces "Phase 5 production deploy COMPLETE"
- [ ] **09:00** — Handoff to 72h monitoring rotation (see `PHASE5_DEPLOYMENT_MONITORING.md`)

---

## Section F — Post-Deploy Handoff

- [ ] **09:05** — Deploy log archived at `docs/04-report/phase5-production-deploy-log.md`
- [ ] **09:10** — Memory entry updated: `MEMORY.md` — Phase 5 production deployment complete
- [ ] **09:15** — Staging environment aligned with prod (optional re-deploy)
- [ ] **09:30** — Stakeholder announcement: deployment success + monitoring link
- [ ] **10:00** — First hourly checkpoint posted (see monitoring doc)

---

## Section G — Rollback Procedure (emergency only)

**Trigger criteria:** See `PHASE5_DEPLOYMENT_DECISION_MATRIX.md` Section "Rollback Triggers".

### G.1 Code Rollback (BLUE still warm)
1. Switch LB weight: GREEN 0% / BLUE 100% (single API call, < 30s)
2. Verify `GET /api/scheduler/health` now returns 404 (endpoint removed in BLUE) — expected
3. Confirm overall error rate returns to pre-deploy baseline within 5 min
4. **Total time: ≤ 5 minutes**

### G.2 DB Rollback (only if migration caused issue)
1. Execute `database/migrations/006_scheduler_integration_rollback.sql`
2. Verify tables dropped: `migration_schedules`, `migration_batches`, `migration_logs`
3. **Total time: ≤ 5 minutes**
4. If rollback SQL fails → restore from Supabase backup ID captured in A.6

### G.3 Post-Rollback
- [ ] Incident log opened in `docs/04-report/incidents/`
- [ ] Sentry issues triaged
- [ ] Reschedule decision within 24h
- [ ] Stakeholder announcement: deployment rolled back + next steps

---

## Owners

| Role            | Primary            | Backup            |
|-----------------|--------------------|-------------------|
| Deploy Lead     | @jhhyun4u          | TBD               |
| DBA             | TBD                | TBD               |
| SRE             | TBD                | TBD               |
| QA              | TBD                | TBD               |
| On-call (72h)   | PagerDuty rotation | Escalation policy |

---

## Related Documents

- `PHASE5_PREDEPLOYMENT_VALIDATION.md` — Detailed validation evidence
- `PHASE5_DEPLOYMENT_MONITORING.md` — 72h monitoring plan
- `PHASE5_DEPLOYMENT_DECISION_MATRIX.md` — GO/NO-GO criteria
- `docs/02-design/features/phase5-scheduler-integration.design.md` — Design spec
- `docs/01-plan/features/phase5-scheduler-integration.plan.md` — Implementation plan
- `database/migrations/006_scheduler_integration.sql` — Applied migration
