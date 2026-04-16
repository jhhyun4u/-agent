# Unified State System — Production Deployment Checklist

**Feature**: unified-state-system  
**Deployment Date**: 2026-04-15  
**Status**: Ready for Production  
**Rollback Available**: Yes (migration 019 rollback script exists)

---

## Pre-Deployment (1 hour)

### Environment Verification
- [ ] Staging database is replica of production
- [ ] All environment variables configured (DB connection, API keys, etc.)
- [ ] Supabase project verified (correct URL, key)
- [ ] Azure AD app registration confirmed
- [ ] Teams webhook URL configured for notifications

### Code Verification
- [ ] Latest commit: Unified State System report generated
- [ ] Backend build successful: `uv run python -m py_compile app/services/state_validator.py`
- [ ] Frontend build successful: `npm run build` (0 TypeScript errors)
- [ ] All tests passing: `uv run pytest tests/integration/test_unified_state_e2e.py -v` (11/11)
- [ ] No pending changes: `git status` is clean

### Backup & Rollback Preparation
- [ ] Database backup taken (Supabase auto-backup or manual snapshot)
- [ ] Rollback migration script downloaded: `database/rollback_migration_019.sql`
- [ ] Rollback test performed in staging (verify tables drop correctly)
- [ ] Git commit hash noted for rollback: `git rev-parse HEAD`

---

## Deployment Phase (30 minutes)

### Step 1: Database Migration (5 min)
```bash
# Run migration in order
psql -d production_db -f database/migrations/019_unified_state_system.sql

# Verify migration success
SELECT COUNT(*) FROM proposal_timelines;  -- Should be populated
SELECT COUNT(*) FROM proposals WHERE started_at IS NOT NULL;  -- Check timestamps
```

**Success Criteria**:
- ✅ proposal_timelines table exists with data
- ✅ 8 timestamp columns on proposals table
- ✅ CHECK constraints active
- ✅ No errors in migration log

### Step 2: Backend Deployment (10 min)
```bash
# Deploy new backend code
git pull origin main
uv sync  # Install new dependencies if any

# Verify code changes
grep -n "ProposalStatus" app/services/state_validator.py | head -3
grep -n "class StateMachine" app/state_machine.py

# Start backend
uvicorn app.main:app --reload  # Dev
# OR: systemctl restart tenopa-backend  # Production
```

**Success Criteria**:
- ✅ Backend starts without errors
- ✅ StateValidator + StateMachine classes loaded
- ✅ API endpoints responding (GET /health should return 200)

### Step 3: Frontend Deployment (10 min)
```bash
# Deploy new frontend code
cd frontend
npm run build
npm run deploy  # Or: vercel deploy --prod

# Verify types are available
grep "type ProposalStatus" lib/api.ts
grep "type WinResult" lib/api.ts
```

**Success Criteria**:
- ✅ Frontend builds without errors
- ✅ Types correctly defined
- ✅ Components updated (ProjectContextHeader, DetailRightPanel, WorkflowResumeBanner)

### Step 4: Health Checks (5 min)
```bash
# Verify API endpoints
curl -X GET http://localhost:3000/api/health
# Expected: { "status": "healthy", "timestamp": "..." }

# Check state endpoint on a test proposal
curl -X GET http://localhost:3000/api/proposals/{proposal_id}/state
# Expected: 3-layer response with business_status, workflow_phase, ai_status

# Verify database
psql -d production_db -c "SELECT status FROM proposals LIMIT 1;"
# Expected: One of the 10 unified statuses
```

---

## Post-Deployment (30 minutes)

### Validation
- [ ] Existing proposals are queryable (no 500 errors)
- [ ] New proposals can be created (status initializes correctly)
- [ ] Workflow transitions work (status changes logged to proposal_timelines)
- [ ] Notifications sent on status changes (check Teams channel)
- [ ] State history endpoint returns paginated results
- [ ] Frontend UI shows new statuses correctly (no stale values)

### Monitoring
- [ ] Error logs clean (no constraint violation errors)
- [ ] Database query performance normal (proposal_timelines queries < 100ms)
- [ ] API response times normal (3-layer responses < 500ms)
- [ ] No spike in CPU/memory usage
- [ ] Notification queue processing normally

### Team Communication
- [ ] Announce deployment to team Slack channel
- [ ] Update documentation with new 10-status enum
- [ ] Brief support team on new status values
- [ ] Share state diagram (initialized → waiting → in_progress → ...)

---

## Rollback Procedure (If Issues Found)

### Trigger Rollback If:
- ❌ Constraint violations detected (400 errors on status update)
- ❌ Data corruption in proposal_timelines (missing entries)
- ❌ Performance degradation (queries > 1 second)
- ❌ Critical bugs in state transitions

### Rollback Steps (15 minutes)

**Step 1: Stop New Deployments**
```bash
# Prevent new changes from propagating
git revert HEAD  # Revert latest commit
```

**Step 2: Database Rollback**
```bash
# Drop new tables and columns
psql -d production_db -f database/rollback_migration_019.sql

# Verify rollback
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'proposals' AND column_name = 'started_at';
-- Expected: No results (column dropped)
```

**Step 3: Code Rollback**
```bash
# Restore previous code version
git checkout <previous-commit-hash>
uv sync

# Restart backend
systemctl restart tenopa-backend
```

**Step 4: Verification**
```bash
# Verify old API response (2-layer instead of 3-layer)
curl -X GET http://localhost:3000/api/proposals/{id}/state
# Should return: { proposal_id, status, current_phase } (no ai_status, timestamps)
```

**Step 5: Communication**
- Notify team of rollback
- Schedule post-mortem to analyze issue
- Plan re-deployment with fixes

---

## Success Metrics (Track for 48 hours)

| Metric | Target | Monitoring |
|:---|:---:|:---|
| **Deployment Success Rate** | 100% | No rollback needed |
| **API Response Time (p95)** | < 500ms | Datadog / CloudWatch |
| **Constraint Violations** | 0 | Error logs |
| **Proposal State Accuracy** | 100% | Sample data queries |
| **Timeline Entry Creation** | 100% | proposal_timelines row count growth |
| **Notification Delivery** | > 99% | Teams webhook logs |
| **Test Pass Rate** | 100% | CI/CD pipeline |

---

## Documentation Updates

### Code Changes Summary
```
Modified Files:
- app/services/state_validator.py (NEW)
- app/state_machine.py (NEW)
- app/api/routes_workflow.py (enhanced endpoints)
- database/migrations/019_unified_state_system.sql (NEW)
- frontend/lib/api.ts (type exports)
- frontend/components/ProjectContextHeader.tsx (status badge updates)
- frontend/components/DetailRightPanel.tsx (win_result form)
- frontend/components/WorkflowResumeBanner.tsx (terminal status logic)

Database Changes:
- proposals table: +8 timestamp columns, +1 win_result column
- proposal_timelines table: NEW (11 columns, 5 indexes)
- CHECK constraints: +2 (status values, win_result values)
```

### Knowledge Base Updates
- [ ] Update team wiki with new 10-status enum
- [ ] Document valid state transitions (StateValidator.VALID_TRANSITIONS)
- [ ] Add example: "How to query proposal timeline"
- [ ] Update runbook: "What to do if proposal is stuck in a state"

---

## Contacts & Escalation

### On-Call During Deployment
- **Backend**: [Engineer Name] — Contact if API not responding
- **Database**: [DBA Name] — Contact if migration fails
- **Frontend**: [Engineer Name] — Contact if UI broken
- **Infrastructure**: [DevOps Name] — Contact if deployment blocked

### Escalation Path
1. Issue detected → Page on-call engineer
2. No resolution in 5 min → Page team lead
3. Critical issue → Notify engineering director
4. Rollback decision → Engineering director approval

---

## Approval Sign-off

- [ ] **Backend Lead**: Approves code changes _________________ Date: _____
- [ ] **Database Admin**: Approves migration script _________________ Date: _____
- [ ] **Frontend Lead**: Approves component updates _________________ Date: _____
- [ ] **QA Manager**: Confirms test pass rate _________________ Date: _____
- [ ] **Product Owner**: Approves deployment _________________ Date: _____

---

**Deployment Prepared By**: AI Assistant  
**Reviewed By**: [Name]  
**Approved For Production**: [Name, Date]

---

## Quick Reference

**Revert Checklist** (if things go wrong):
```bash
# 1. Stop new requests (take service offline if critical)
# 2. Revert code
git revert HEAD
# 3. Run rollback migration
psql -d production_db -f database/rollback_migration_019.sql
# 4. Restart services
systemctl restart tenopa-backend
systemctl restart tenopa-frontend
# 5. Notify team
```

**Verify Deployment Success**:
```bash
# Check 1: API health
curl -X GET http://localhost:3000/api/health

# Check 2: Database migration
psql -c "SELECT COUNT(*) FROM proposal_timelines;"

# Check 3: Frontend types
npm list | grep api.ts

# Check 4: Tests
npm run test -- unified-state-system

# Check 5: Logs for errors
tail -f /var/log/tenopa-backend.log | grep -i error
```
