# LLM-Wiki Team Kickoff Guide

> **Date**: 2026-04-21 (Monday)  
> **Duration**: 2 hours  
> **Attendees**: Backend (1), Frontend (1), ML/AI (0.5), PM (0.5), QA (0.5) + Tech Lead, Product Lead  
> **Objective**: Sprint 1 준비 완료 및 팀 정렬

---

## 📋 Agenda (120 min)

| Time | Topic | Owner | Duration |
|------|-------|-------|----------|
| 00:00-05 | Welcome & Overview | PM | 5 min |
| 05-25 | Product Vision & Market Context | PM | 20 min |
| 25-45 | Architecture & Technical Design | Tech Lead | 20 min |
| 45-70 | Sprint 1 Roadmap & Task Breakdown | Backend Lead | 25 min |
| 70-100 | Team Allocation & Logistics | PM | 30 min |
| 100-115 | Q&A & Risk Discussion | All | 15 min |
| 115-120 | Next Steps & Closing | PM | 5 min |

---

## 🎯 Part 1: Welcome & Overview (5 min)

### Key Message
> "우리는 제안서 작성 시간 40%를 단축하고, 조직 지식 활용률을 3배 높이는 **AI 지식 코워커**를 12주 안에 만든다."

### Quick Facts
- **Product**: LLM-Wiki (조직 지식관리 + AI 추천 시스템)
- **Timeline**: 12주 (4 sprints × 3주)
- **Team**: 3.5 FTE
- **Success Metric**: Alpha 데모 (Week 3), 검색 성능 < 3sec, 사용자 만족도 NPS >= 40

---

## 📊 Part 2: Product Vision & Market Context (20 min)

### Problem Statement (2 min)

**현재 상황**:
- 제안서 작성자: 과거 유사 프로젝트/역량 정보를 찾는데 **평균 2-4시간 소요**
- 경쟁사/시세 정보: 담당자 개인 기억에 의존, 체계적 축적 없음
- 퇴직자 암묵지: 조직이 떠나가는 교훈과 고객 인텔리전스 유실
- 신입/전배: 온보딩에 3-6개월, 팀별 중복 조사 발생

**Vision**:
> "프로젝트를 거듭할수록 똑똑해지는 조직 — AI가 경험 많은 동료처럼 지식을 찾고 추천한다"

---

### Market Opportunity (3 min)

**Market Size**:
- **TAM**: ~$253M (글로벌 AI-KM 시장 2026)
- **SAM**: ~$22M (한국 정부과제 조직)
- **SOM**: ~$210K (3년 내 목표, 50 organizations)

**Competitive Positioning**:
```
                    제안서 특화
                         |
         tenopa llm-wiki |   SK AX 제안서 AI
         (워크플로 통합)  |   (독립 솔루션)
                         |
자동화 수준 ────────────┼──────────
                         |
  Confluence/Notion      |   Guru / GoSearch
  (범용 위키)            |   (AI 검색 특화)
                    범용
```

**Our Advantage**:
- ✅ 제안서 워크플로 완전 통합 (LangGraph)
- ✅ 8-area 시맨틱 검색 (기존 infrastructure 활용)
- ✅ 자동 지식 축적 피드백 루프 (project completion → lessons_learned)
- ✅ 한국 공공 시장 특화 (G2B 데이터 + 제안 도메인)

---

### Beachhead & Go-To-Market (3 min)

**Target Customer**:
- IT 서비스 / SI 기업 (30-200명)
- 연간 정부 용역과제 20건+
- 제안서 작성 시간의 30% 이상을 자료 검색에 소요

**Initial Launch** (Alpha → Beta → GA):
- **Alpha** (Week 3): Internal dogfooding + 2 pilot customers
- **Beta** (Week 6): Existing tenopa customers (10 orgs)
- **GA** (Week 12): Public launch + 30 target organizations

---

### Success Definition (2 min)

| Level | Criteria | Target |
|-------|----------|--------|
| **Feature** | Search works, < 3 sec latency, zero data leaks | Week 3 end |
| **Adoption** | 30 searches/day/org, 30% recommendation CTR | Month 1 |
| **Business** | -40% proposal time, 3x knowledge reuse | Month 3 |
| **Growth** | 50 organizations, NPS >= 50 | Year 1 |

---

## 🏗️ Part 3: Architecture & Technical Design (20 min)

### System Overview (5 min)

**High-Level Architecture**:
```
┌─────────────────────────────────────────────────┐
│           Frontend (Next.js)                     │
│  [Search Page] [Side Panel] [Dashboard]          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────v──────────────────────────────┐
│         Wiki API (FastAPI)                       │
│  /wiki/search  /wiki/recommend  /wiki/health     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────v──────────────────────────────┐
│    Knowledge Services                            │
│  [Search] [Recommend] [Embedding] [Curator]      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────v──────────────────────────────┐
│    Supabase (PostgreSQL + pgvector + RLS)        │
│  8-area tables + embedding vectors + RLS         │
└──────────────────────────────────────────────────┘
```

---

### Core Features (Sprint 1) (5 min)

| Feature | Description | Tech Stack |
|---------|-------------|-----------|
| **Unified Search** | 8-area 통합 검색 (content, capability, client, competitor, lesson, qa, doc, project) | pgvector + FastAPI |
| **Semantic Search** | 자연어 쿼리 → embedding → cosine similarity | OpenAI embedding-3-small + pgvector |
| **Search UI** | Filter + pagination + results card | Next.js + Shadcn/ui |
| **Source Viewer** | 검색 결과 원본 문서 표시 | Modal + markdown render |
| **RLS Security** | org + team 데이터 격리 | Supabase RLS policies |
| **Embedding Pipeline** | 문서 → 청크 → embedding 자동화 | Async queue + batch processing |

---

### Data Flow (3 min)

**Search Scenario**:
1. User inputs query: "AI 교통 분석"
2. Frontend POSTs to `/api/wiki/search` with areas filter
3. Backend:
   - Generates embedding for query
   - Performs pgvector cosine similarity search
   - Applies RLS filters (user's org/team)
   - Ranks results by relevance + freshness
4. Returns top-10 results in < 3 sec
5. Frontend renders card-based UI with source links

**Embedding Pipeline**:
1. Document uploaded / ingested
2. Split into 500-token chunks
3. Queue → Background worker
4. Batch embed (100 chunks at a time)
5. Store in pgvector
6. Index created for fast search

---

### Existing Infrastructure Reuse (2 min)

✅ **Leverage Existing**:
- `app/services/knowledge_search.py` (8-area semantic search) → Direct reuse
- `app/services/embedding_service.py` (OpenAI API client) → Reuse
- `app/services/document_chunker.py` (document splitting) → Reuse
- Supabase pgvector + RLS → Existing
- FastAPI + authentication framework → Existing
- Next.js + Shadcn/ui → Existing

🆕 **New Components**:
- Wiki search page (`/wiki`)
- Side panel integration (proposal editor)
- `/wiki/search` API endpoint
- `wiki_metadata` table
- Embedding pipeline (queue + worker)
- Recommendation engine (Phase 2)
- Knowledge dashboard (Phase 2)

---

## 🎯 Part 4: Sprint 1 Roadmap & Task Breakdown (25 min)

### Sprint Goal (2 min)

> **"Unified search API + frontend UI를 완성하여 alpha 데모 가능 수준으로 만들기"**

**Deliverables**:
- ✅ Search API endpoint (POST /api/wiki/search)
- ✅ Search page UI (filter + results)
- ✅ Source viewer
- ✅ Embedding pipeline
- ✅ Unit & E2E tests
- ✅ Staging deployment

---

### Epic Breakdown (18 min)

#### Epic 1: Search API Backend (5 min)
- **Owner**: Backend Engineer (5 story points)
- **Tasks**:
  - 1.1: API spec + OpenAPI doc (3 pts, 2 days)
  - 1.2: /wiki/search endpoint impl (5 pts, 3 days)
  - 1.3: DB migration wiki_metadata (2 pts, 1 day)
  - 1.4: Embedding pipeline queue (5 pts, 3 days)

**Highlights**:
- Reuse existing knowledge_search.py
- Apply RLS for data isolation
- Support 8-area filtering
- Handle 50 concurrent requests

**Risks**: 
- Embedding API rate limits → Mitigation: Batch optimization

---

#### Epic 2: Frontend Search UI (5 min)
- **Owner**: Frontend Engineer (3 story points)
- **Tasks**:
  - 2.1: UI skeleton + layout (3 pts, 2 days)
  - 2.2: Search form + API integration (3 pts, 2 days)
  - 2.3: Results display + source viewer (3 pts, 2 days)

**Highlights**:
- Responsive design (mobile → desktop)
- Accessibility (ARIA labels, keyboard nav)
- Skeleton loader for UX
- Debounced search input

**Risks**:
- Component library mismatch → Mitigation: Use existing Shadcn/ui

---

#### Epic 3: Testing & QA (5 min)
- **Owner**: QA Engineer + Backend/Frontend (2 story points)
- **Tasks**:
  - 3.1: Unit tests (3 pts, 2 days)
  - 3.2: E2E tests (3 pts, 2 days)
  - 3.3: Load testing (2 pts, 1 day)

**Target Coverage**:
- Unit test: >= 80%
- E2E: 5+ scenarios
- Load: 50 concurrent users, p95 latency < 3 sec

**Risks**:
- Test data insufficient → Mitigation: Generate 10K test documents

---

#### Epic 4: Docs & Deployment (3 min)
- **Owner**: Backend Lead + PM (2 story points)
- **Tasks**:
  - 4.1: API documentation (2 pts, 1 day)
  - 4.2: Staging deployment (2 pts, 1 day)
  - 4.3: Sprint review + alpha demo prep (2 pts, 1 day)

**Deliverables**:
- Swagger UI + README
- Staging deployment checklist
- Demo script
- Stakeholder feedback form

---

### Timeline Visualization (5 min)

```
Week 1: Foundation (Kickoff + API spec + UI skeleton)
├─ Mon 21: Sprint kickoff
├─ Tue 22: API spec done, UI skeleton started
├─ Wed 23: API endpoint started
├─ Thu 24: DB migration, embedding pipeline started
└─ Fri 25: Checkpoint

Week 2: Implementation (Core features)
├─ Mon 28-Fri 2: API + Frontend + Testing in parallel
└─ Checkpoint: Mid-sprint review (Wed 30)

Week 3: Polish & Demo (Finalization)
├─ Mon 5: Load testing + bug fixes
├─ Tue 6: Deployment prep
├─ Wed 7: Staging deployment
├─ Thu 8: Final polish
└─ Fri 9: Alpha demo + sprint review
```

**Story Points**: 35 points (Velocity = 35/3 weeks = 11.7 pts/week)

---

## 👥 Part 5: Team Allocation & Logistics (30 min)

### Role & Responsibilities (10 min)

| Role | Person | Allocation | Primary Tasks | Secondary Tasks |
|------|--------|-----------|----------------|------------------|
| **Backend Lead** | [Name] | 100% | 1.1-1.4 (API, DB, embedding) | Code review, deployment |
| **Frontend Engineer** | [Name] | 100% | 2.1-2.3 (UI, form, results) | E2E tests, accessibility |
| **ML/AI Engineer** | [Name] | 50% | 1.4 (embedding pipeline) | Performance tuning, documentation |
| **QA Engineer** | [Name] | 50% | 3.1-3.3 (tests, load) | Coverage reporting, risk tracking |
| **PM** | [Name] | 50% | Roadmap, stakeholder comms, demo | Metrics tracking, risk mitigation |
| **Tech Lead** | [Name] | 20% (support) | Architecture decisions, blockers | Code review escalation |

---

### Key Responsibilities Breakdown (8 min)

**Backend Engineer Owns**:
- API endpoint implementation (correctness, performance, security)
- DB schema & migrations
- Embedding pipeline (queue, batch processing)
- RLS configuration & validation
- API documentation

**Frontend Engineer Owns**:
- UI component development (responsiveness, a11y)
- API integration (error handling, loading states)
- E2E test scripts
- Performance optimization (bundle, rendering)

**QA Engineer Owns**:
- Unit test coverage (80%+)
- E2E test scenarios (5+)
- Load testing (50 concurrent users)
- Performance baseline & monitoring setup

**PM Owns**:
- Sprint roadmap & priorities
- Stakeholder communication
- Demo preparation & customer feedback
- Risk tracking & escalation

---

### Team Logistics (12 min)

#### Communication Plan
- **Daily Standups**: 9:00 AM (15 min)
  - What did you do yesterday?
  - What will you do today?
  - Blockers?
  
- **Mid-Sprint Checkpoint**: Wed (Apr 30) 1 hour
  - Progress review (tasks, story points)
  - Identify risks early
  - Resource rebalancing if needed

- **Sprint Review & Retro**: Fri (May 9) 1.5 hours
  - Demo (for stakeholders + team)
  - Retrospective (what went well, what to improve)
  - Sprint 2 planning

#### Tools & Access

- **Version Control**: GitHub (backend: `app/`, frontend: Next.js repo)
- **Issue Tracking**: Jira (Sprint 1 board, task assignments)
- **CI/CD**: GitHub Actions (auto-test on push, staging deploy)
- **Documentation**: Confluence / GitHub Wiki
- **Communication**: Slack #llm-wiki channel
- **Monitoring**: DataDog / New Relic (setup Week 1)

#### Environment Setup

**Pre-Kickoff Checklist**:
- [ ] GitHub repos cloned locally
- [ ] Python 3.11+ installed (backend)
- [ ] Node.js 18+ installed (frontend)
- [ ] Supabase staging environment confirmed
- [ ] API keys (OpenAI, Supabase) in `.env`
- [ ] IDE extensions installed (Python, TypeScript linters)
- [ ] CI/CD pipeline tested locally

**Everyone should be ready to**:
- [ ] Run `uv sync && uv run pytest` (backend)
- [ ] Run `npm install && npm run dev` (frontend)
- [ ] Submit first commit by end of Week 1

---

## ⚠️ Part 6: Q&A & Risk Discussion (15 min)

### Likely Questions & Answers (10 min)

**Q1: 왜 12주인가? 더 빨리 못 하나?**

A: 
- Phase 1: Foundation (Week 1-3) — Search API + UI + testing
- Phase 2: Intelligence (Week 4-6) — Recommendations + dashboard
- Phase 3: Automation (Week 7-9) — Auto-classification + lessons extraction
- Phase 4: Polish (Week 10-12) — Optimization + GA release

각 phase는 이전 phase에 의존하므로 순차적으로 진행. 병렬화 여지 제한적 (team size = 3.5 FTE).

---

**Q2: 기존 document_ingestion과의 차이가 뭐지?**

A:
- **document_ingestion**: PDF/DOCX/HWP 자동 분석 → 제안서 섹션 생성 (STEP 4)
- **llm-wiki**: 조직의 모든 지식(역량, 고객, 경쟁사, 시세, 교훈) 통합 검색 → 제안 작성 시 참고 (Cross-STEP)

LLM-Wiki는 document_ingestion 위에 구축. document_ingestion의 결과물도 wiki에 인덱싱됨.

---

**Q3: RLS 설정이 안 되면 어떻게 하나?**

A: Critical risk. Week 1 내에 Supabase RLS 철저히 테스트.
- Penetration test 우선화
- 보안 감사 (다른 org 데이터 노출 확인)
- RLS 설정 오류 발견 시 즉시 roll-back

---

**Q4: Alpha 데모에서 보여줄 게 충분한가?**

A: 충분함. Search page + 3개 sample queries + filter + source viewer로 충분히 가치 증명.
- Fake data 10K documents로 테스트
- Real data는 Beta (Week 6) 때 추가

---

**Q5: Embedding API 비용이 얼마나 되나?**

A: 
- 1000 chunks embedding = ~$0.02 (OpenAI text-embedding-3-small)
- 10K chunks (test) = ~$0.20
- Batch optimization + caching으로 비용 최소화
- Week 1-3: ~$10 (테스트 + pilot data)
- Month 1 (scale-up): ~$100-200 (가정: 100K chunks/org)

---

### Top Risks & Mitigation (5 min)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Embedding API rate limits | Medium | Batch size optimization (100→50), queue backpressure |
| RLS data leak | Critical | Security audit Week 1, penetration test |
| Search perf degradation | Low | pgvector index tuning, Redis cache layer |
| Staging data insufficient | High | Fixture auto-generation (10K test docs) |
| Team knowledge gap | Medium | Daily standup + documentation + pair programming |

---

## 🚀 Part 7: Next Steps & Closing (5 min)

### Immediate Action Items (By End of Week 1)

**All Team**:
- [ ] GitHub repos cloned, environments set up
- [ ] Jira Sprint 1 board created, tasks assigned
- [ ] First commit submitted to `develop` branch

**Backend**:
- [ ] API spec (OpenAPI YAML) completed
- [ ] /wiki/search endpoint skeleton ready

**Frontend**:
- [ ] Search page UI skeleton in Storybook
- [ ] Component structure defined

**QA**:
- [ ] Test plan document written
- [ ] Test fixture generation script started

**PM**:
- [ ] Stakeholder list finalized
- [ ] Demo script outline ready
- [ ] Metrics dashboard setup started

---

### Success Criteria for Kickoff

- [ ] All team members understand the vision & roadmap
- [ ] Task assignments are clear & non-overlapping
- [ ] Technical risks are identified & mitigation plans in place
- [ ] Environment setup complete
- [ ] First sprint tasks can be started immediately

---

### Closing Message

> "We're building something impactful — an AI that learns from every proposal and makes the next one better. 12 weeks. 3.5 FTE. Let's go."

**Questions?** [Discussion]

---

## 📎 Appendix: Reference Materials

### Documents to Share

1. **PRD**: `docs/00-pm/llm-wiki.prd.md` (Full product spec)
2. **Sprint 1 Plan**: `docs/01-plan/features/llm-wiki-sprint1-plan.md` (Detailed tasks)
3. **Architecture Diagram**: [Link to Figma/draw.io]
4. **API Spec**: OpenAPI YAML (generate from code)
5. **Risk Register**: [Jira epic + risk tracking board]

### Helpful Links

- **Supabase RLS Docs**: https://supabase.com/docs/guides/auth/row-level-security
- **pgvector Docs**: https://github.com/pgvector/pgvector
- **OpenAI Embeddings API**: https://platform.openai.com/docs/guides/embeddings
- **tenopa CLAUDE.md**: Project coding standards

### Contact & Escalation

- **Tech Blocker**: Tech Lead (slack: @tech-lead)
- **Timeline/Scope**: PM (slack: @pm)
- **Security**: CISO / Security Lead
- **Infrastructure**: DevOps / Platform team

---

**Last Updated**: 2026-04-21  
**Next Review**: 2026-05-09 (Sprint 1 end)
