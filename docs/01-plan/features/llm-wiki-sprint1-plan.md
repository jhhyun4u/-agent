# LLM-Wiki Sprint 1 상세 계획

> **Feature**: llm-wiki  
> **Sprint**: Sprint 1 (Week 1-3)  
> **Theme**: Unified Search & Core Infrastructure  
> **Date**: 2026-04-21 ~ 2026-05-09 (3주, 15 working days)  
> **Team**: 3.5 FTE (Backend 1, Frontend 1, ML/AI 0.5, PM 0.5)  
> **Goal**: Functional alpha-level search page + backend API

---

## 📋 Sprint Goal

제안서 작성자가 **자연어로 조직 지식 8개 영역을 통합 검색**할 수 있는 기본 인터페이스 및 API를 완성하여, alpha 데모가 가능한 수준으로 끌어올리기.

---

## 📊 Epic Breakdown & Task List

### Epic 1: Search API Backend (Backend Engineer)

#### Task 1.1: Search API Specification & Documentation (2 days)
- **Story Points**: 3
- **Owner**: Backend Lead
- **Description**: 
  - OpenAPI 3.1 spec 작성 (POST /api/wiki/search endpoint)
  - Request/Response schema 정의 (8-area filtering, pagination, scoring)
  - Error handling spec (empty results, invalid queries, rate limiting)
  - API documentation (Swagger UI integration)

- **Acceptance Criteria**:
  - [ ] OpenAPI YAML 파일 생성 및 validate
  - [ ] Swagger UI에서 schema 확인 가능
  - [ ] Request/Response 예시 5개 이상 작성
  - [ ] Error code mapping document 완성

- **Dependencies**: None
- **Blocked By**: None
- **Risks**: API design 변경으로 인한 재작업 → 초기 리뷰 우선화

---

#### Task 1.2: /wiki/search Endpoint Implementation (3 days)
- **Story Points**: 5
- **Owner**: Backend Engineer
- **Description**:
  - FastAPI route 생성
  - knowledge_search.py 기존 함수 통합 (재사용)
  - 8-area 필터링 로직 (content/client/capability/competitor/lesson/qa/doc/project)
  - Request validation & error handling
  - Pagination logic (top_k, offset)

- **Implementation Steps**:
  ```python
  # routes_wiki.py
  @router.post("/wiki/search")
  async def search_knowledge(
      query: str,
      areas: List[str] = [],  # optional filter
      scope: str = "team",    # team | division | org
      top_k: int = 10,
      min_similarity: float = 0.5,
  ) -> Dict[str, Any]:
      # 1. Input validation
      # 2. knowledge_search.py 호출
      # 3. RLS 적용 (user's org/team)
      # 4. Results 포맷 변환
      # 5. Return
  ```

- **Acceptance Criteria**:
  - [ ] Endpoint 구현 완료
  - [ ] 8-area filtering 정상 작동
  - [ ] RLS (Row Level Security) 적용 검증
  - [ ] 50개 동시 요청 처리 가능 (load test)
  - [ ] Response time < 3 sec (p95)

- **Dependencies**: Task 1.1 (API spec)
- **Blocked By**: None
- **Risks**: RLS 오류 → 데이터 격리 테스트 우선화

---

#### Task 1.3: DB Migration: wiki_metadata Table (1 day)
- **Story Points**: 2
- **Owner**: Backend Engineer
- **Description**:
  - knowledge_library 개선 (문서 메타데이터 확장)
  - 테이블 정의:
    - `wiki_items(id, org_id, team_id, item_type, item_id, title, area, freshness, last_updated, ...)`
    - Indices: (org_id, team_id, area), (org_id, last_updated)
  - Migration script 생성 (up/down)

- **SQL Script**:
  ```sql
  -- 008_wiki_metadata.sql
  CREATE TABLE IF NOT EXISTS wiki_items (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(id),
    team_id UUID REFERENCES teams(id),
    item_type VARCHAR(50) NOT NULL,  -- content|capability|client|competitor|lesson|qa|doc|project
    item_id UUID NOT NULL,           -- FK to actual item table
    title VARCHAR(500),
    area VARCHAR(50),                -- 8-area classification
    freshness FLOAT DEFAULT 1.0,     -- 1.0 = fresh, 0.0 = stale
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(org_id, item_type, item_id)
  );
  
  CREATE INDEX idx_wiki_items_search ON wiki_items(org_id, team_id, area);
  CREATE INDEX idx_wiki_items_freshness ON wiki_items(org_id, last_updated DESC);
  ```

- **Acceptance Criteria**:
  - [ ] Migration 파일 생성 및 문법 검증
  - [ ] Staging DB에서 성공적 적용
  - [ ] Rollback 테스트 완료
  - [ ] 문서화: 스키마 다이어그램 포함

- **Dependencies**: None
- **Blocked By**: None

---

#### Task 1.4: Embedding Pipeline Setup (3 days)
- **Story Points**: 5
- **Owner**: ML/AI Engineer (0.5 FTE)
- **Description**:
  - 기존 embedding_service.py 기반 queue 구축
  - Background worker (Celery or async task)
  - Batch processing (100 chunks per batch)
  - pgvector storage 확인 (기존 infrastructure)
  - Cache layer (Redis) 검토

- **Implementation**:
  - Task queue: Redis or Postgres LISTEN/NOTIFY
  - Worker: Background process (uvicorn subprocess or Celery)
  - Batch logic: 100개씩 묶어서 embedding API 호출
  - Fallback: API 실패 시 retry (exponential backoff)

- **Acceptance Criteria**:
  - [ ] 1000 chunks embedding 처리 < 5 min
  - [ ] 실패 시 자동 재시도 동작
  - [ ] pgvector에 저장 확인
  - [ ] Monitor: queue depth, processing latency 기록

- **Dependencies**: Task 1.3 (metadata table)
- **Blocked By**: None
- **Risks**: Embedding API 레이트 제한 → Batch 크기 조정 필요

---

### Epic 2: Frontend Search UI (Frontend Engineer)

#### Task 2.1: Search Page Skeleton & Layout (2 days)
- **Story Points**: 3
- **Owner**: Frontend Engineer
- **Description**:
  - Route: `/wiki` or `/search`
  - Components:
    - Search input (Shadcn SearchInput or input + button)
    - Area filter sidebar (8-area checkboxes)
    - Scope selector (team | division | org)
    - Results container (placeholder)
  - Responsive design (mobile: 1 column, desktop: 2 columns)
  - Skeleton loader (while fetching)

- **Design Specs**:
  - Search bar: Tiptap-style placeholder "역량, 고객, 경쟁사 검색..."
  - Filter section: Collapsible on mobile
  - Results: Card-based layout (title, excerpt, area badge, source link)
  - Empty state: "관련 지식이 없습니다" + suggestions

- **Acceptance Criteria**:
  - [ ] Page responsive on mobile/tablet/desktop
  - [ ] Skeleton loader 500ms 동안 표시
  - [ ] Filter inputs functional (local state)
  - [ ] Accessibility: ARIA labels, keyboard navigation

- **Dependencies**: None
- **Blocked By**: None

---

#### Task 2.2: Search Form & Integration (2 days)
- **Story Points**: 3
- **Owner**: Frontend Engineer
- **Description**:
  - Form state management (React hooks or Redux)
  - API call: POST /api/wiki/search (with error handling)
  - Loading state: isLoading, error message
  - Debounce query input (500ms)
  - Pagination: "Load more" button or infinite scroll

- **Implementation**:
  ```typescript
  // hooks/useWikiSearch.ts
  export function useWikiSearch() {
    const [query, setQuery] = useState('');
    const [areas, setAreas] = useState<string[]>([]);
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const search = useCallback(async () => {
      const response = await fetch('/api/wiki/search', {
        method: 'POST',
        body: JSON.stringify({ query, areas, top_k: 10 })
      });
      // handle response
    }, [query, areas]);
    
    return { query, setQuery, areas, setAreas, results, search, isLoading, error };
  }
  ```

- **Acceptance Criteria**:
  - [ ] Form submission 시 API call 발생
  - [ ] Loading state 표시
  - [ ] Error message 노출
  - [ ] 500ms debounce 동작
  - [ ] Results 페이지에 렌더링

- **Dependencies**: Task 1.2 (Search API)
- **Blocked By**: None

---

#### Task 2.3: Results Display & Source Viewer (2 days)
- **Story Points**: 3
- **Owner**: Frontend Engineer
- **Description**:
  - Results 카드 렌더링 (title, excerpt, area badge, score)
  - Source information (document name, section, author, date)
  - "View source" link → modal or new page
  - Highlight query terms in results (optional)
  - Copy text button

- **UI Components**:
  - ResultCard: compact card with excerpt
  - SourceViewer: modal showing full document context
  - Badge: area type (blue=content, green=capability, etc.)

- **Acceptance Criteria**:
  - [ ] 각 result card 정보 완전
  - [ ] Source viewer modal functional
  - [ ] 화면 반응성 확인
  - [ ] Copy button 동작
  - [ ] 스크린 리더 테스트 (a11y)

- **Dependencies**: Task 2.2 (Search integration)
- **Blocked By**: None

---

### Epic 3: Testing & QA

#### Task 3.1: Unit Tests (Backend API) (2 days)
- **Story Points**: 3
- **Owner**: QA Engineer (0.5 FTE) + Backend
- **Description**:
  - Test suite: pytest
  - Test cases:
    - Valid query → correct results
    - Empty query → error
    - Invalid areas → error
    - RLS enforcement → 다른 조직 데이터 노출 안됨
    - Rate limiting → 100 req/min/user 초과 시 429
  - Fixture: 50 test documents pre-indexed
  - Target coverage: >= 80%

- **Test Examples**:
  ```python
  def test_search_valid_query(client, auth_header):
      response = client.post('/api/wiki/search', 
          json={'query': 'AI 교통', 'top_k': 10},
          headers=auth_header)
      assert response.status_code == 200
      assert len(response.json()['results']) > 0
  
  def test_search_rls_enforcement(client, auth_header_org_a, org_b_data):
      response = client.post('/api/wiki/search', 
          json={'query': 'secret'}, headers=auth_header_org_a)
      # Org B 데이터 없음 확인
      assert 'org_b_secret' not in [r['title'] for r in response.json()['results']]
  ```

- **Acceptance Criteria**:
  - [ ] 12개 이상 test cases 작성
  - [ ] 모든 테스트 통과
  - [ ] Coverage report >= 80%
  - [ ] CI/CD 파이프라인 통합

- **Dependencies**: Task 1.2, 1.4 (API, embedding)
- **Blocked By**: None

---

#### Task 3.2: E2E Tests (Frontend) (2 days)
- **Story Points**: 3
- **Owner**: QA Engineer + Frontend
- **Description**:
  - E2E framework: Playwright
  - Scenarios:
    - User opens search page
    - Enters query → results displayed
    - Clicks filter → filtered results
    - Clicks source → modal opens
  - Performance check: Page load < 2 sec, search response < 3 sec

- **Test Scenarios**:
  ```typescript
  test('User searches and views results', async ({ page }) => {
    await page.goto('/wiki');
    await page.fill('input[placeholder*="검색"]', 'AI 교통');
    await page.click('button[type="submit"]');
    await page.waitForSelector('[data-testid="result-card"]');
    const cards = await page.locator('[data-testid="result-card"]').count();
    expect(cards).toBeGreaterThan(0);
  });
  ```

- **Acceptance Criteria**:
  - [ ] 5+ E2E test scenarios 작성
  - [ ] 모든 시나리오 통과
  - [ ] Performance baseline 기록
  - [ ] Accessibility 스캔 (axe DevTools)

- **Dependencies**: Task 2.3 (Frontend complete)
- **Blocked By**: None

---

#### Task 3.3: Load Testing (1 day)
- **Story Points**: 2
- **Owner**: QA Engineer
- **Description**:
  - Tool: k6 or Apache JMeter
  - Scenario: 50 concurrent users, 5 min duration
  - Load profile:
    - 50% search requests (2 req/min per user)
    - 30% source viewer (1 req/min per user)
    - 20% think time
  - Metrics: throughput, latency (p50/p95/p99), errors
  - Target: < 1% error rate, p95 latency < 3 sec

- **k6 Script Example**:
  ```javascript
  export let options = {
    stages: [
      { duration: '2m', target: 50 },   // ramp-up
      { duration: '3m', target: 50 },   // steady
      { duration: '2m', target: 0 },    // ramp-down
    ]
  };
  
  export default function() {
    http.post(`${BASE_URL}/api/wiki/search`, {
      query: randomQuery(),
      top_k: 10
    });
  }
  ```

- **Acceptance Criteria**:
  - [ ] Load test 완료
  - [ ] Report 생성 (throughput, latency curve)
  - [ ] Bottleneck 식별 및 문서화
  - [ ] Performance baseline 기록

- **Dependencies**: Task 1.2, 3.1 (API 안정)
- **Blocked By**: None

---

### Epic 4: Documentation & Deployment Prep

#### Task 4.1: API Documentation & Developer Guide (1 day)
- **Story Points**: 2
- **Owner**: Backend Engineer
- **Description**:
  - Swagger UI auto-generated docs 확인
  - README.md: API 개요, authentication, error codes
  - Code comments: Docstrings 추가
  - Example requests: cURL, Python, JavaScript

- **Contents**:
  - Quick start guide
  - Authentication & authorization
  - Error code mapping
  - Rate limits & quotas
  - Sample payloads (JSON)

- **Acceptance Criteria**:
  - [ ] Swagger UI 정상 표시
  - [ ] README 완성
  - [ ] Code comments 80% coverage
  - [ ] Examples 3+ languages

- **Dependencies**: Task 1.2
- **Blocked By**: None

---

#### Task 4.2: Deployment to Staging (1 day)
- **Story Points**: 2
- **Owner**: DevOps / Backend Lead
- **Description**:
  - GitHub Actions workflow (이미 있다고 가정)
  - Staging DB에 migration 적용
  - Environment variables 설정
  - Health check: /health endpoint
  - Smoke test 실행

- **Deployment Checklist**:
  - [ ] Code merged to `develop`
  - [ ] CI/CD pipeline 통과 (build, test)
  - [ ] Staging DB migration 완료
  - [ ] Environment secrets 설정
  - [ ] Smoke test 통과 (search API 동작)
  - [ ] Frontend staging build 배포
  - [ ] Rollback plan 준비

- **Acceptance Criteria**:
  - [ ] Staging에서 search page 접근 가능
  - [ ] Search API 응답 정상
  - [ ] Logs 정상 기록
  - [ ] Monitoring alert 구성

- **Dependencies**: Task 1-4 (all features)
- **Blocked By**: None
- **Risk**: Staging DB 데이터 부족 → 테스트용 fixture 10,000 chunks 생성

---

#### Task 4.3: Sprint Review & Alpha Demo Prep (1 day)
- **Story Points**: 2
- **Owner**: Product Manager
- **Description**:
  - Sprint retrospective (team feedback)
  - Demo script 작성
  - Stakeholder 데모 일정 (Week 3 end)
  - Feedback 수집 양식 (구글 폼)
  - Next sprint (2-3) 우선순위 조정

- **Demo Agenda** (15 min):
  - Search page 오픈
  - 3개 sample queries 실행
  - Filter 사용
  - Source viewer 확인
  - Performance metrics 설명
  - Q&A

- **Acceptance Criteria**:
  - [ ] Sprint retro 완료
  - [ ] Demo script 작성
  - [ ] 3+ stakeholders 초대
  - [ ] Feedback form 준비

- **Dependencies**: Task 3 (testing complete)
- **Blocked By**: None

---

## 📅 Weekly Timeline

```
Week 1 (Apr 21-25)
├─ Mon 21: Sprint kickoff, task assignment
├─ Tue 22: 1.1 완료 (API spec), 2.1 진행 (UI skeleton)
├─ Wed 23: 1.2 진행 (endpoint impl), 2.2 진행 (form)
├─ Thu 24: 1.3 완료 (DB migration), 1.4 시작 (embedding)
└─ Fri 25: Daily standup, checkpoint

Week 2 (Apr 28-May 2)
├─ Mon 28: 1.2/1.4 진행 중, 2.2/2.3 진행 중
├─ Tue 29: 3.1 unit tests 시작
├─ Wed 30: 1.2 완료 검증, 2.3 진행
├─ Thu May 1: 3.2 E2E tests 시작, 1.4 embedding 검증
└─ Fri 2: Weekly integration test

Week 3 (May 5-9)
├─ Mon 5: Final polish, 3.3 load test 실행
├─ Tue 6: 4.1/4.2 deployment 준비
├─ Wed 7: Staging 배포, smoke test
├─ Thu 8: Bug fix & refinement
└─ Fri 9: Sprint review & alpha demo
```

---

## 👥 Team Allocation

| Role | Name | Allocation | Tasks |
|------|------|-----------|-------|
| **Backend Lead** | TBD | 100% | 1.1, 1.2, 1.3, API docs |
| **Frontend Engineer** | TBD | 100% | 2.1, 2.2, 2.3, E2E |
| **ML/AI Engineer** | TBD | 50% | 1.4 (embedding pipeline) |
| **QA Engineer** | TBD | 50% | 3.1, 3.2, 3.3 (testing) |
| **PM** | TBD | 50% | Roadmap, stakeholder comms, demo |

---

## 🎯 Definition of Done

Sprint 1이 완료되려면 다음을 만족해야 합니다:

- [ ] **Code**: 모든 기능 구현 완료, code review 통과
- [ ] **Tests**: Unit (80%), E2E (5 scenarios), Load test 완료
- [ ] **Deployment**: Staging 배포 성공, smoke test 통과
- [ ] **Documentation**: API docs, code comments, README 완성
- [ ] **Performance**: Search p95 < 3 sec, zero data leaks (RLS)
- [ ] **Demo Ready**: Alpha demo 스크립트 준비, stakeholder feedback 수집

---

## 📊 Success Metrics (Sprint 1 Objectives)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Code Completion** | 100% | Task closure rate |
| **Test Pass Rate** | 100% | CI/CD pipeline |
| **Code Coverage** | >= 80% | pytest + coverage.py |
| **Search Latency** | < 3 sec (p95) | Load test results |
| **Data Isolation** | 100% | RLS validation audit |
| **Team Velocity** | 35 story points | Burndown chart |
| **Stakeholder Satisfaction** | NPS >= 30 | Alpha demo feedback |

---

## ⚠️ Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Embedding API rate limit exceeded | Medium | High | Batch 크기 조정, queue backpressure 추가 |
| RLS 설정 오류 → 데이터 유출 | Low | Critical | Security audit (penetration test) 우선화 |
| Search performance 저하 | Low | Medium | pgvector index 최적화, Redis caching 추가 |
| Frontend component library 문제 | Low | Low | 기존 Shadcn components 재사용 |
| Staging DB 트래픽 부족 | High | Medium | Test fixture 자동 생성 (10K docs) |

---

## 🔄 Dependencies & Blockers

**Internal Dependencies**:
- Supabase pgvector RLS 설정 완료 (기존 infrastructure 확인)
- document_ingestion pipeline 안정성 (embdding 품질)
- authentication/authorization framework 정상 (기존 tenopa)

**External Dependencies**:
- OpenAI Embedding API 가용성
- GitHub Actions runner 안정성

---

## 📝 Notes for Kickoff

- **Team Kickoff**: Week 1 Mon (Apr 21) 2시간
  - Architecture review
  - Task ownership assignment
  - CI/CD pipeline 확인
  - Staging environment 준비

- **Daily Standups**: 매일 9:00 AM (15 min)
  - 진행 상황
  - 블로커 식별
  - 우선순위 조정

- **Mid-Sprint Checkpoint**: Wed (Apr 30) 1시간
  - Sprint progress 검토
  - Risk escalation
  - Resource rebalancing

- **Sprint Review & Retro**: Fri (May 9) 1.5시간
  - Demo (stakeholders)
  - Retrospective (team)
  - Sprint 2 우선순위 논의
