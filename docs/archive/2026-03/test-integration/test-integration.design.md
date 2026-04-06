# 통합 테스트 설계서 — test-integration

- **Feature**: test-integration
- **Plan 참조**: `docs/01-plan/features/test-integration.plan.md`
- **작성일**: 2026-03-26

---

## 1. 테스트 대상 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│ routes_workflow.py (start/resume/stream)                        │
│   ├─ graph.ainvoke(initial_state)                               │
│   │   └─ build_graph(checkpointer)                              │
│   │       ├─ HEAD: rfp_analyze → review_rfp → research_gather   │
│   │       │        → go_no_go → review_gng → strategy_generate  │
│   │       ├─ FORK: fork_gate → Path A + Path B 병렬             │
│   │       │   ├─ A: plan → proposal → PPT → mock_eval           │
│   │       │   └─ B: submission → bid_plan → cost_sheet → check  │
│   │       ├─ TAIL: convergence → eval_result → project_closing  │
│   │       └─ checkpointer: AsyncPostgresSaver | MemorySaver     │
│   └─ Supabase: proposals.status 업데이트                        │
│                                                                 │
│ research_gather (MCP 도구 호출 지점)                             │
│   ├─ claude_generate() — 리서치 주제 도출 + 조사                │
│   ├─ (향후) SearXNG → 웹 검색                                   │
│   ├─ (향후) OpenAlex → 학술 검색                                │
│   └─ G2B API → 유사 공고/낙찰정보                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Fixture 설계

### 2.1 `tests/integration/conftest.py` (신규)

```python
"""통합 테스트 공통 fixture.

Mock 기반 (Level 1) — CI에서 항상 실행.
"""

# ── 의존성 ──
# 기존 tests/conftest.py: make_supabase_mock, MockQueryBuilder
# 기존 tests/workflow/conftest.py: _make_claude_mock, _make_pricing_mock

# ── 신규 fixture ──

@pytest.fixture
def mcp_tools_mock():
    """MCP 도구 mock 세트 반환.

    Returns:
        dict with keys: searxng, openalex, g2b
        각 value는 AsyncMock (호출 가능, 결과 커스터마이즈 가능)
    """

@pytest.fixture
def claude_error_mock(error_type: str):
    """Claude API 에러 시뮬레이션 mock.

    Args:
        error_type: "timeout" | "rate_limit" | "connection" | "auth"
    """

@pytest.fixture
def db_connection_mock(mode: str):
    """DB 연결 mock.

    Args:
        mode: "healthy" | "disconnected" | "slow"
    """

@pytest.fixture
async def graph_with_mocks(workflow_patches):
    """모든 외부 의존성이 mock된 컴파일된 그래프."""

@pytest.fixture
def standard_rfp_state():
    """표준 RFP 테스트 상태 (Case A + PPT)."""

@pytest.fixture
def doc_only_rfp_state():
    """서류심사 전용 RFP 테스트 상태 (PPT 스킵)."""
```

### 2.2 `tests/integration/live/conftest.py` (신규)

```python
"""Live 통합 테스트 fixture.

Level 2 — 로컬/스테이징에서 수동 실행.
pytest -m live 로 실행.
"""

@pytest.fixture(scope="session")
async def pg_checkpointer():
    """실제 PostgreSQL AsyncPostgresSaver.

    환경변수: TEST_DATABASE_URL 필요.
    테스트 완료 후 checkpoint 테이블 정리.
    """

@pytest.fixture(scope="session")
async def live_supabase():
    """실제 Supabase 클라이언트.

    환경변수: TEST_SUPABASE_URL, TEST_SUPABASE_KEY 필요.
    테스트 전용 데이터 생성 → 완료 후 정리.
    """

@pytest.fixture
async def live_graph(pg_checkpointer):
    """실제 PostgreSQL 체크포인터를 사용하는 그래프."""
```

---

## 3. 테스트 케이스 상세 설계

### 3.1 LangGraph 워크플로 (Mock)

**파일**: `tests/integration/test_workflow_integration.py`

#### WF-01: Happy Path 전체 흐름

```python
async def test_full_workflow_happy_path(graph_with_mocks, standard_rfp_state):
    """HEAD → FORK → Path A 완주 → convergence → END.

    검증:
    - 각 interrupt 지점에서 올바른 노드에 멈춤
    - resume 후 다음 노드로 진행
    - 최종 state에 모든 산출물 존재
    - current_step이 올바르게 전이
    """
    # 1. invoke → review_rfp에서 interrupt
    # 2. resume(approved) → research_gather → go_no_go → review_gng
    # 3. resume(go) → strategy_generate → review_strategy
    # 4. resume(approved) → fork → Path A (plan → proposal → PPT → mock_eval)
    #    각 review에서 resume(approved)
    # 5. convergence → eval_result → project_closing → END

    assert result.get("current_step") == "completed"
    assert "proposal_sections" in result
    assert "ppt_storyboard" in result
```

#### WF-02: Interrupt/Resume 상태 보존

```python
async def test_interrupt_resume_state_preservation(graph_with_mocks, standard_rfp_state):
    """interrupt 후 resume 시 이전 노드의 출력이 보존되는지 검증.

    검증:
    - rfp_analysis는 review_rfp resume 후에도 유지
    - strategy는 review_strategy resume 후에도 유지
    - plan 노드 출력들은 review_plan resume 후에도 유지
    """
    # invoke → review_rfp interrupt
    # aget_state → rfp_analysis 존재 확인
    # resume → ... → review_strategy interrupt
    # aget_state → rfp_analysis + strategy 모두 존재 확인
```

#### WF-03: No-Go 분기

```python
async def test_no_go_early_termination(graph_with_mocks, standard_rfp_state):
    """Go/No-Go에서 no_go → 워크플로 즉시 종료.

    검증:
    - review_gng에서 decision="no_go" resume
    - 그래프가 END에 도달
    - strategy_generate 이후 노드 미실행
    """
```

#### WF-04: Path A + B 분기 병합 (convergence_gate)

```python
async def test_fork_convergence(graph_with_mocks, standard_rfp_state):
    """전략 승인 후 A/B 병렬 분기 → convergence_gate 합류.

    검증:
    - fork_gate에서 Path A와 Path B 모두 시작
    - 양쪽 모두 convergence_gate에 도달
    - 통합 후 eval_result 실행
    """
```

**파일**: `tests/integration/test_workflow_error_recovery.py`

#### WF-05: self_review 실패 → retry 분기

```python
async def test_self_review_retry_sections(graph_with_mocks, standard_rfp_state):
    """자가진단 점수 미달 → retry_sections → proposal_start_gate 복귀.

    검증:
    - self_review에서 score < 임계값 → route가 retry_sections 반환
    - proposal_start_gate로 복귀 후 재작성 시작
    - 2회차에서 pass → review_proposal로 진행
    """
```

#### WF-06: Claude API 에러 전파

```python
async def test_claude_timeout_propagation(graph_with_mocks, standard_rfp_state, claude_error_mock):
    """Claude API 타임아웃 시 워크플로가 AITimeoutError 전파.

    검증:
    - strategy_generate에서 AITimeoutError 발생
    - 워크플로가 TenopAPIError로 중단 (raw 500 아님)
    - error_code가 AI_003
    """
```

### 3.2 PostgreSQL 연결

**파일**: `tests/integration/test_db_fallback.py` (Mock)

#### DB-03: MemorySaver 폴백

```python
async def test_postgres_failure_falls_back_to_memory(monkeypatch):
    """AsyncPostgresSaver 연결 실패 시 MemorySaver로 폴백.

    검증:
    - database_url이 잘못된 값일 때
    - _get_graph()가 MemorySaver로 그래프 빌드
    - 워크플로 실행 가능
    - 경고 로그 출력

    참조: routes_workflow.py _get_graph() 함수의 폴백 로직
    """
```

**파일**: `tests/integration/live/test_workflow_live_db.py` (Live)

#### DB-01: AsyncPostgresSaver 기본 동작

```python
@pytest.mark.live
async def test_checkpointer_write_read(pg_checkpointer):
    """체크포인트 저장 → 읽기 왕복 검증.

    검증:
    - graph.ainvoke()로 상태 저장
    - aget_state()로 상태 복원
    - 값이 정확히 일치
    """
```

#### DB-02: RLS 정책 검증

```python
@pytest.mark.live
async def test_rls_cross_user_isolation(live_supabase):
    """User A가 User B의 proposals에 접근 불가.

    검증:
    - User A JWT로 생성한 proposal
    - User B JWT로 같은 proposal 조회 시도
    - 결과 empty (RLS 차단)
    """
```

#### DB-05: 동시 체크포인터 격리

```python
@pytest.mark.live
async def test_concurrent_proposals_isolation(pg_checkpointer):
    """2개 proposal 동시 실행 시 체크포인트 격리.

    검증:
    - thread_id=proposal-A 와 thread_id=proposal-B 동시 invoke
    - 각각의 state가 독립적
    - A의 resume가 B에 영향 없음
    """
```

### 3.3 MCP 도구 호출

**파일**: `tests/integration/test_mcp_tools.py` (Mock)

#### MCP-01: research_gather 정상 흐름

```python
async def test_research_gather_produces_brief(graph_with_mocks, standard_rfp_state):
    """research_gather 노드가 research_brief 산출물 생성.

    검증:
    - invoke 후 research_gather 실행
    - state["research_brief"]에 topics, findings 존재
    - 각 topic에 data_points 배열 존재
    """
```

#### MCP-02~04: 개별 도구 결과 통합

```python
async def test_searxng_results_integrated(mcp_tools_mock):
    """SearXNG 검색 결과가 research_brief에 반영.

    검증:
    - mock SearXNG가 3개 결과 반환
    - research_brief.topics 중 해당 결과 참조 존재
    """

async def test_openalex_results_integrated(mcp_tools_mock):
    """OpenAlex 학술 검색 결과가 research_brief에 반영."""

async def test_g2b_research_integrated(mcp_tools_mock):
    """G2B 유사 공고/경쟁사 데이터가 research_brief에 반영."""
```

#### MCP-05: 도구 실패 시 graceful degradation

```python
async def test_mcp_tool_failure_graceful(mcp_tools_mock):
    """SearXNG 실패 시에도 research_gather가 완료.

    검증:
    - SearXNG mock이 RuntimeError 발생
    - research_gather가 에러 없이 완료
    - research_brief에 다른 도구 결과는 정상 포함
    - 경고 로그 출력
    """
```

**파일**: `tests/integration/live/test_mcp_tools_live.py` (Live)

#### MCP-06: SearXNG 실제 호출

```python
@pytest.mark.live
async def test_searxng_live_search():
    """SearXNG Docker 인스턴스에 실제 검색 요청.

    환경: SEARXNG_URL 환경변수 필요 (예: http://localhost:8080)
    검증:
    - "클라우드 ERP" 검색 시 결과 1개 이상
    - 결과에 title, url 필드 존재
    """
```

#### MCP-07: G2B API 실제 호출

```python
@pytest.mark.live
async def test_g2b_api_live_search():
    """나라장터 API 실제 호출.

    환경: G2B_API_KEY 환경변수 필요
    검증:
    - "시스템 구축" 키워드 검색 시 결과 반환
    - 결과에 bidNtceNm, bidNtceNo 필드 존재
    """
```

---

## 4. 파일 구조 최종

```
tests/
├── conftest.py                              — 기존 유지
├── workflow/
│   ├── conftest.py                          — 기존 유지 (Claude mock, fixtures)
│   └── test_*.py                            — 기존 유지 (단위)
├── integration/
│   ├── conftest.py                          — [신규] Mock fixture 인프라
│   ├── test_workflow_integration.py         — [신규] WF-01~04
│   ├── test_workflow_error_recovery.py      — [신규] WF-05~06
│   ├── test_mcp_tools.py                    — [신규] MCP-01~05
│   ├── test_db_fallback.py                  — [신규] DB-03
│   └── live/
│       ├── __init__.py                      — [신규]
│       ├── conftest.py                      — [신규] Live DB/API fixture
│       ├── test_workflow_live_db.py         — [신규] WF-07~08, DB-01~02, DB-04~05
│       └── test_mcp_tools_live.py           — [신규] MCP-06~07
└── workflow/fixtures/                       — 기존 JSON fixtures 유지
```

**신규 파일**: 9개
**수정 파일**: 1개 (`pyproject.toml` — markers 추가)

---

## 5. pytest 설정

### pyproject.toml 추가

```toml
[tool.pytest.ini_options]
markers = [
    "live: 실제 외부 서비스 연결 필요 (로컬/스테이징 전용)",
]
filterwarnings = [
    "ignore::DeprecationWarning:langgraph.*",
]
```

### 실행 명령

```bash
# Mock 테스트만 (CI 기본)
uv run pytest tests/integration/ -m "not live" -v

# Live 테스트 포함 (로컬)
TEST_DATABASE_URL="postgresql://..." uv run pytest tests/integration/ -v

# 특정 카테고리
uv run pytest tests/integration/test_workflow_integration.py -v
uv run pytest tests/integration/test_mcp_tools.py -v
uv run pytest tests/integration/live/ -m live -v
```

---

## 6. Mock 데이터 설계

### 신규 fixture JSON 파일

| 파일 | 위치 | 내용 |
|------|------|------|
| `research_gather.json` | `tests/workflow/fixtures/` | 이미 존재 ✅ |
| `mcp_searxng_results.json` | `tests/integration/fixtures/` | SearXNG 검색 결과 mock |
| `mcp_openalex_results.json` | `tests/integration/fixtures/` | OpenAlex 검색 결과 mock |
| `mcp_g2b_research.json` | `tests/integration/fixtures/` | G2B 유사 공고 mock |

### JSON 구조 예시

```json
// mcp_searxng_results.json
{
  "results": [
    {
      "title": "클라우드 ERP 도입 사례 — 한국정보화진흥원",
      "url": "https://example.com/cloud-erp",
      "snippet": "2025년 공공기관 클라우드 ERP 전환율 42% 달성...",
      "source": "searxng"
    }
  ]
}
```

---

## 7. 구현 순서 (Plan §5 기준)

| 단계 | 파일 | 테스트 ID | 예상 LOC |
|:---:|------|---------|:---:|
| 1 | `integration/conftest.py` | — | ~120 |
| 2 | `test_workflow_integration.py` | WF-01~04 | ~200 |
| 3 | `test_workflow_error_recovery.py` | WF-05~06 | ~100 |
| 4 | `test_mcp_tools.py` + fixtures | MCP-01~05 | ~150 |
| 5 | `test_db_fallback.py` | DB-03 | ~60 |
| 6 | `live/conftest.py` + `test_workflow_live_db.py` | WF-07~08, DB-01~05 | ~180 |
| 7 | `live/test_mcp_tools_live.py` | MCP-06~07 | ~80 |
| — | `pyproject.toml` markers | — | ~5 |
| **합계** | **9 파일** | **20 케이스** | **~895** |

---

## 8. 의존성

### 기존 활용 (변경 없음)
- `tests/workflow/conftest.py` — `_make_claude_mock`, `_make_pricing_mock`, `workflow_patches`
- `tests/conftest.py` — `make_supabase_mock`, `MockQueryBuilder`
- `tests/workflow/fixtures/*.json` — 기존 14개 JSON fixture

### 신규 패키지 (필요 시)
- `pytest-timeout` — Live 테스트 타임아웃 보호 (선택)
- Docker Compose — SearXNG 컨테이너 (Live MCP 테스트 시)
