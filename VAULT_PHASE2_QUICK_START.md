# Vault Chat Phase 2 — Quick Start Guide

**Last Updated**: 2026-04-20  
**For**: Development Team  
**Duration**: 2 weeks (2026-04-20 to 2026-05-04)

---

## 📋 What's Being Built?

Vault Chat Phase 1 (semantic search + multi-turn chat) is being extended with:

| Feature | Benefit | Complexity |
|---------|---------|-----------|
| 💬 **Context Injection** | Natural multi-turn conversations | Medium |
| 🔒 **Permission Filtering** | Secure org-wide access | High |
| 🌍 **Multi-language** | Global team support | Medium |
| 🤖 **Teams Bot** | AI in your workflow | High |

---

## 🎯 Key Numbers

| Item | Value |
|------|-------|
| New Code | ~700 lines |
| New Tests | ~50 tests |
| New Tables | 2 tables |
| Modified Tables | 4 tables |
| API Endpoints | 5 new endpoints |
| Timeline | 2 weeks |
| Team Size | 3 engineers + 1 QA |

---

## 📦 Deliverables (Documentation Complete ✅)

### Planning Documents
1. **vault-chat-phase2.plan.md** (529 lines, 21KB)
   - Requirements specification
   - Feature breakdown (FR1-FR4)
   - Implementation roadmap
   - Success criteria
   - Risk management

2. **vault-chat-phase2.design.md** (1,299 lines, 46KB)
   - System architecture
   - Data flow diagrams
   - Database schema (exact SQL)
   - Service layer design (with code examples)
   - API specifications
   - Testing strategy (50 tests)
   - Performance targets
   - Security measures

3. **VAULT_CHAT_PHASE2_SUMMARY.md** (386 lines, 13KB)
   - Executive summary
   - Current state (Phase 1)
   - Timeline breakdown
   - Success metrics
   - Next actions checklist

---

## 🚀 Quick Implementation Checklist

### Week 1: PLAN & DO (50%)

**Day 1-2 (04/21-22): Context Management**
- [ ] Read: `vault-chat-phase2.design.md` Section 3.1 (VaultContextManager)
- [ ] Extend `vault_context_manager.py`:
  - Add `extract_context_with_embeddings()` method
  - Add `context_embedding` VECTOR field to vault_messages
  - Create index on (conversation_id, created_at DESC)
- [ ] Write tests:
  - `test_context_extraction.py` (5 unit tests)
  - `test_context_injection.py` (3 integration tests)
- [ ] Expected: 80 lines of code, 8 passing tests

**Day 3-4 (04/22-23): Permission Filtering**
- [ ] Read: `vault-chat-phase2.design.md` Section 3.2 (VaultPermissionFilter)
- [ ] Create new file: `app/services/vault_permission_filter.py` (100 lines)
  - Implement `filter_response()` method
  - Implement `_log_denied_access()` helper
  - Add role hierarchy constants
- [ ] Extend database:
  - Add `min_required_role` to vault_documents
  - Add `action_denied`, `denied_reason` to vault_audit_logs
- [ ] Write tests:
  - `test_permission_filter.py` (6 unit tests)
  - `test_permission_integration.py` (4 integration tests)
- [ ] Expected: 100 lines of code, 10 passing tests

**Day 5-6 (04/24-26): Multi-language Support**
- [ ] Read: `vault-chat-phase2.design.md` Section 3.3 (VaultMultiLangHandler)
- [ ] Create new file: `app/services/vault_multilang_handler.py` (200 lines)
  - Implement `detect_language()` using langdetect
  - Implement `search_multilang()` for multi-language search
  - Implement preference save/load methods
- [ ] Update requirements: add `langdetect>=1.0.9`
- [ ] Extend database:
  - Add `language` field to vault_messages and vault_documents
  - Add `preferred_language` to users
- [ ] Write tests:
  - `test_language_detection.py` (4 unit tests: ko, en, zh, ja)
  - `test_multilang_integration.py` (4 integration tests)
- [ ] Expected: 200 lines of code, 8 passing tests

**End of Week 1 Verification**
- [ ] 330 lines of new code
- [ ] 23 tests passing (15 unit + 8 integration)
- [ ] DB migration file created: `023_vault_phase2_tables.sql`
- [ ] Performance check: < 2s response time maintained

---

### Week 2: DO (50%) + CHECK + ACT

**Day 7-8 (04/27-28): Teams Bot Service**
- [ ] Read: `vault-chat-phase2.design.md` Section 3.4 (TeamsBotService)
- [ ] Create new file: `app/services/teams_bot_service.py` (300 lines)
  - Implement Mode 1: Adaptive Bot (send_response_to_teams)
  - Implement Mode 2: Daily Digest (schedule + generate)
  - Implement Mode 3: RFP Matching (recommend_similar_projects)
  - Implement Teams message formatting
- [ ] Create new file: `app/api/routes_teams_bot.py` (70 lines)
  - POST /api/teams/bot/query (adaptive)
  - GET/PUT /api/teams/bot/config/{team_id} (settings)
  - POST /api/teams/bot/digest (manual trigger)
- [ ] Write tests:
  - `test_teams_bot_adaptive.py` (4 unit tests)
  - `test_teams_bot_digest.py` (4 unit tests)
  - `test_teams_bot_integration.py` (8 integration tests)
- [ ] Expected: 370 lines of code, 16 passing tests

**Day 9 (04/29): E2E Testing & Performance**
- [ ] Create: `test_vault_phase2_e2e.py` (15 E2E tests)
  - test_e2e_multi_turn_context
  - test_e2e_permission_enforcement
  - test_e2e_multilang_workflow
  - test_e2e_teams_bot_interaction
  - 11 more...
- [ ] Performance validation:
  - P50 < 1.5s, P95 < 3s
  - Memory per conversation < 150KB
  - 50+ concurrent users supported
- [ ] Expected: 15 E2E tests, 100% passing, performance metrics logged

**Day 10 (05/01): CHECK Phase Validation**
- [ ] Run full test suite: `pytest tests/ -v`
  - Target: 50/50 tests passing
  - Coverage: ≥ 85%
- [ ] Gap analysis:
  - Compare design vs implementation
  - Identify missing pieces
  - Estimate effort to close gaps
- [ ] Bug triage & prioritization
- [ ] Create: `CHECK_PHASE_REPORT.md`

**Day 11-14 (05/02-04): Staging Deploy & Monitoring**
- [ ] Execute DB migration (023_vault_phase2_tables.sql)
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Monitor for 24 hours
  - Response time metrics
  - Error rates
  - Teams API success rate
- [ ] Create: `DEPLOYMENT_READINESS.md`
- [ ] Plan production deployment (05/05 target)

---

## 📁 Files to Create/Modify

### New Files (6 files)
```
app/services/
  ├─ vault_permission_filter.py (100 lines)
  ├─ vault_multilang_handler.py (200 lines)
  └─ teams_bot_service.py (300 lines)

app/api/
  └─ routes_teams_bot.py (70 lines)

database/migrations/
  └─ 023_vault_phase2_tables.sql (150 lines)

tests/
  └─ (50 new test files, ~2,000 lines)
```

### Modified Files (6 files)
```
app/services/
  └─ vault_context_manager.py (extend existing, +80 lines)

app/api/
  └─ routes_vault_chat.py (integrate context, +20 lines)

app/
  └─ main.py (register new routes, +10 lines)

database/
  └─ schema_v3.4.sql (reference for new tables)
```

### Documentation (3 files)
```
docs/01-plan/features/
  └─ vault-chat-phase2.plan.md ✅ (DONE)

docs/02-design/features/
  └─ vault-chat-phase2.design.md ✅ (DONE)

(root)
  └─ VAULT_CHAT_PHASE2_SUMMARY.md ✅ (DONE)
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
cd /c/project/tenopa\ proposer
uv add langdetect>=1.0.9
uv add python-dateutil>=2.8
uv add pytz>=2024.1
uv sync
```

### 2. Review Documentation
```bash
# Read in order:
1. VAULT_CHAT_PHASE2_SUMMARY.md (overview)
2. docs/01-plan/features/vault-chat-phase2.plan.md (requirements)
3. docs/02-design/features/vault-chat-phase2.design.md (detailed design)
```

### 3. Run Existing Tests (Baseline)
```bash
uv run pytest tests/integration/test_vault_chat_complete_e2e.py -v
# Expected: 23/23 passing (Phase 1 baseline)
```

### 4. Start Development
```bash
# Week 1: Context + Permission + L10n
git checkout -b feature/vault-phase2-context
# ... implement

git checkout -b feature/vault-phase2-permission
# ... implement

git checkout -b feature/vault-phase2-multilang
# ... implement

# Week 2: Teams Bot + Tests
git checkout -b feature/vault-phase2-teams-bot
# ... implement

git checkout -b feature/vault-phase2-e2e-tests
# ... test
```

---

## 📊 Progress Tracking Template

### Week 1 Checklist
```
Day 1-2 (04/21-22): Context
  ✅ Implement extract_context_with_embeddings()
  ✅ Add context_embedding field
  ✅ Write 8 tests
  ✅ Pass: 8/8 tests

Day 3-4 (04/23-24): Permission
  ✅ Create VaultPermissionFilter service
  ✅ Add min_required_role field
  ✅ Write 10 tests
  ✅ Pass: 10/10 tests

Day 5-6 (04/25-26): L10n
  ✅ Create VaultMultiLangHandler
  ✅ Integrate langdetect
  ✅ Write 8 tests
  ✅ Pass: 8/8 tests

Week 1 Summary
  ✅ 330 lines of code
  ✅ 23/23 tests passing
  ✅ Ready for Week 2
```

### Week 2 Checklist
```
Day 7-8 (04/27-28): Teams Bot
  ✅ Create TeamsBotService (3 modes)
  ✅ Create routes_teams_bot.py
  ✅ Write 16 tests
  ✅ Pass: 16/16 tests

Day 9 (04/29): E2E Tests
  ✅ Write 15 E2E tests
  ✅ Performance validation
  ✅ Pass: 15/15 tests

Day 10 (05/01): CHECK Phase
  ✅ All tests: 50/50 passing
  ✅ Coverage: 85%+
  ✅ Gap analysis complete

Day 11-14 (05/02-04): Deployment
  ✅ Staging deploy successful
  ✅ 24-hour monitoring complete
  ✅ Production ready
```

---

## 🧪 Test Running Guide

### Run All Phase 2 Tests
```bash
# Unit tests (fast)
uv run pytest tests/services/test_vault_permission_filter.py -v
uv run pytest tests/services/test_vault_context_manager.py -v
uv run pytest tests/services/test_vault_multilang_handler.py -v
uv run pytest tests/api/test_teams_bot_routes.py -v

# Integration tests (medium)
uv run pytest tests/integration/test_vault_phase2_integration.py -v

# E2E tests (slow)
uv run pytest tests/integration/test_vault_phase2_e2e.py -v

# All together with coverage
uv run pytest tests/ -v --cov=app --cov-report=html
```

### Performance Testing
```bash
# Response time benchmark
uv run python scripts/bench_vault_phase2_performance.py

# Load testing (50 concurrent users)
uv run locust -f tests/load/locustfile.py --host=http://localhost:8000

# Memory profiling
uv run python -m memory_profiler app/services/vault_context_manager.py
```

---

## 🔍 Review Checkpoints

### Week 1 Review (04/26)
- [ ] All 23 tests passing
- [ ] Code coverage ≥ 85%
- [ ] Performance: P95 < 3s
- [ ] No security issues (bandit)
- [ ] Style check (black, ruff)

### Week 2 Review (05/01)
- [ ] All 50 tests passing
- [ ] Coverage maintained ≥ 85%
- [ ] E2E tests all green
- [ ] Performance benchmarks met
- [ ] Documentation complete

### Pre-Production (05/04)
- [ ] Staging deploy successful
- [ ] 24-hour monitoring complete
- [ ] All alerts configured
- [ ] Rollback plan documented
- [ ] Team trained on new features

---

## 📚 Reference Links

| Document | Purpose | Lines |
|----------|---------|-------|
| [vault-chat-phase2.plan.md](docs/01-plan/features/vault-chat-phase2.plan.md) | Requirements | 529 |
| [vault-chat-phase2.design.md](docs/02-design/features/vault-chat-phase2.design.md) | Architecture & APIs | 1,299 |
| [VAULT_CHAT_PHASE2_SUMMARY.md](VAULT_CHAT_PHASE2_SUMMARY.md) | Overview | 386 |
| [vault_phase1_complete_final.md](MEMORY.md) | Phase 1 baseline | 550 |

---

## ⚠️ Common Pitfalls

### 1. Context Window Too Large
- **Problem**: Including too many message turns causes token bloat
- **Solution**: Limit to 8 turns, use CONTEXT_WINDOW constant
- **Test**: `test_context_window_limit()`

### 2. Permission Filter Not Triggered
- **Problem**: Responses include restricted info
- **Solution**: Always call `VaultPermissionFilter.filter_response()` after Claude
- **Test**: `test_permission_enforcement()`

### 3. Language Detection Fails
- **Problem**: Mixed languages or technical terms cause wrong detection
- **Solution**: Use fallback language (ko), test with 20+ examples per language
- **Test**: `test_language_detection_edge_cases()`

### 4. Teams API Rate Limit
- **Problem**: Too many messages sent at once → API rejects
- **Solution**: Queue messages, respect rate limits, implement retry logic
- **Test**: `test_teams_rate_limiting()`

---

## 🎓 Learning Resources

### For Context Injection
- OpenAI: [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- Claude: [Context Windows & Prompt Caching](https://anthropic.com/news/100k-context-window)

### For Permission Systems
- OWASP: [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- PostgreSQL: [Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

### For Multi-language NLP
- Hugging Face: [Multi-lingual Models](https://huggingface.co/models?filter=language)
- OpenAI: [text-embedding-3-large Docs](https://platform.openai.com/docs/guides/embeddings)

### For Teams Integration
- Microsoft: [Teams Webhooks API](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/incoming-webhooks)
- Python: [aiohttp Docs](https://docs.aiohttp.org/)

---

## ✅ Completion Criteria

**Phase 2 is complete when:**

1. ✅ All 50 tests passing (15 unit + 20 integration + 15 E2E)
2. ✅ Code coverage ≥ 85%
3. ✅ Response time P95 < 3 seconds
4. ✅ Permission filtering 100% accurate
5. ✅ All 4 languages supported (ko, en, zh, ja)
6. ✅ Teams bot 3 modes operational
7. ✅ Documentation complete (API + ops guides)
8. ✅ Security review passed
9. ✅ Staging deployment successful
10. ✅ Team trained and ready for production

---

## 🚦 Status Dashboard

| Item | Status | Date |
|------|--------|------|
| PLAN Document | ✅ Complete | 2026-04-20 |
| DESIGN Document | ✅ Complete | 2026-04-20 |
| Summary Document | ✅ Complete | 2026-04-20 |
| **Team Review** | ⏳ Pending | 2026-04-21 |
| **Week 1 Implementation** | 🔲 Not Started | 2026-04-21 |
| **Week 2 Implementation** | 🔲 Not Started | 2026-04-27 |
| **CHECK Phase** | 🔲 Not Started | 2026-05-01 |
| **Staging Deploy** | 🔲 Not Started | 2026-05-01 |
| **Production Ready** | 🔲 Not Started | 2026-05-05 |

---

**Start Date**: 2026-04-20  
**Target Completion**: 2026-05-04  
**Duration**: 2 weeks  

Good luck! 🚀
