# 통합 테스트 계획서 — test-integration

- **Feature**: test-integration
- **작성일**: 2026-03-26
- **우선순위**: HIGH
- **예상 범위**: 테스트 파일 5~8개, fixture 2개, 설정 1개

---

## 1. 배경 및 목적

TENOPA 시스템의 3대 핵심 통합 지점에 대한 테스트가 부족하다:

| 통합 지점 | 현재 상태 | 위험도 |
|----------|---------|:---:|
| LangGraph 워크플로 흐름 | `tests/workflow/` 존재 (mock 기반 happy path) | MEDIUM |
| PostgreSQL 연결 | 체크포인터 테스트 없음 (MemorySaver만 사용) | **HIGH** |
| MCP 도구 호출 (SearXNG, OpenAlex 등) | 테스트 전무 | **HIGH** |

### 목표
1. **실제 DB 연결 테스트** — AsyncPostgresSaver 체크포인터 생존 검증
2. **MCP 도구 호출 테스트** — 외부 검색 도구 연동 검증 (mock + 선택적 live)
3. **워크플로 E2E 강화** — interrupt/resume 사이클 + 에러 복구 시나리오

---

## 2. 현재 테스트 구조 분석

```
tests/
├── conftest.py            — MockQueryBuilder, make_supabase_mock, httpx client
├── workflow/
│   ├── conftest.py        — Claude mock (키워드 디스패치), workflow_patches
│   ├── test_graph_happy_path.py   — 전체 흐름 1개 시나리오 ✅
│   ├── test_graph_branching.py    — 분기 시나리오 ✅
│   ├── test_edges_unit.py         — 라우팅 함수 단위 ✅
│   └── test_nodes_unit.py         — 노드 단위 ✅
├── integration/
│   ├── conftest.py        — "레거시 — 임포트 불가" (사실상 빈 파일)
│   └── test_*.py          — 레거시 3개 (비활성)
├── unit/                  — rfp_parser, bid 관련 ✅
└── test_phase*.py         — API 엔드포인트별 ✅
```

### 갭
- `integration/conftest.py`가 비어 있어 실제 통합 테스트 인프라 없음
- 모든 DB 호출이 `MockQueryBuilder`로 대체 → RLS/트랜잭션/체크포인터 미검증
- MCP 도구(`research_gather` 노드의 SearXNG/OpenAlex) 호출 테스트 없음
- 에러 시나리오 테스트 없음 (Claude 타임아웃, DB 연결 끊김 등)

---

## 3. 테스트 전략

### 3.1 테스트 레벨 분류

```
Level 1: Mock Integration (CI에서 항상 실행)
  - 외부 서비스 mock, 내부 모듈 간 연동 검증
  - pytest -m "not live" (기본)

Level 2: Live Integration (로컬/스테이징에서 수동 실행)
  - 실제 DB, 실제 API 연결 (API 키 필요)
  - pytest -m "live" --live
```

### 3.2 환경 요구사항

| Level | DB | Claude API | MCP 도구 | G2B API |
|-------|:--:|:----------:|:--------:|:-------:|
| Mock | `MemorySaver` | mock | mock | mock |
| Live | `AsyncPostgresSaver` (로컬 PostgreSQL) | 실제 호출 | SearXNG (Docker) | 실제 호출 |

---

## 4. 테스트 항목

### 4.1 LangGraph 워크플로 흐름 (강화)

| ID | 테스트 | 레벨 | 파일 |
|----|--------|:---:|------|
| WF-01 | Happy path: 전체 흐름 (RFP→전략→계획→제안서→PPT→END) | Mock | 기존 `test_graph_happy_path.py` 보강 |
| WF-02 | interrupt→resume 사이클 정합성 (상태 보존 검증) | Mock | `test_workflow_integration.py` |
| WF-03 | No-Go 분기 → 조기 종료 | Mock | 기존 `test_graph_branching.py` 보강 |
| WF-04 | 서류심사(document_only) → PPT 스킵 | Mock | 기존 보강 |
| WF-05 | self_review 실패 → retry 분기 (5방향 라우팅) | Mock | `test_workflow_error_recovery.py` |
| WF-06 | Claude API 타임아웃 중 워크플로 에러 전파 | Mock | `test_workflow_error_recovery.py` |
| WF-07 | 체크포인트 저장/복원 (AsyncPostgresSaver) | **Live** | `test_workflow_live_db.py` |
| WF-08 | 워크플로 중단 후 서버 재시작 → 상태 복원 | **Live** | `test_workflow_live_db.py` |

### 4.2 PostgreSQL 연결

| ID | 테스트 | 레벨 | 파일 |
|----|--------|:---:|------|
| DB-01 | AsyncPostgresSaver setup + checkpoint write/read | **Live** | `test_db_integration.py` |
| DB-02 | Supabase RLS 정책 검증 (user A가 user B 데이터 접근 불가) | **Live** | `test_db_integration.py` |
| DB-03 | DB 연결 끊김 시 MemorySaver 폴백 | Mock | `test_db_fallback.py` |
| DB-04 | 마이그레이션 스크립트 정합성 (schema_v3.4.sql) | **Live** | `test_db_integration.py` |
| DB-05 | concurrent proposals (동시 실행) 체크포인터 격리 | **Live** | `test_db_integration.py` |

### 4.3 MCP 도구 호출

| ID | 테스트 | 레벨 | 파일 |
|----|--------|:---:|------|
| MCP-01 | research_gather 노드: mock 도구 호출 + 결과 파싱 | Mock | `test_mcp_tools.py` |
| MCP-02 | SearXNG 검색 결과 → research_brief 통합 | Mock | `test_mcp_tools.py` |
| MCP-03 | OpenAlex 학술 검색 → 근거 데이터 추출 | Mock | `test_mcp_tools.py` |
| MCP-04 | G2B API → 유사 공고/경쟁사 데이터 | Mock | `test_mcp_tools.py` |
| MCP-05 | 도구 호출 실패 시 graceful degradation | Mock | `test_mcp_tools.py` |
| MCP-06 | SearXNG 실제 호출 (Docker 필요) | **Live** | `test_mcp_tools_live.py` |
| MCP-07 | G2B API 실제 호출 (API 키 필요) | **Live** | `test_mcp_tools_live.py` |

---

## 5. 구현 계획

### 파일 구조

```
tests/
├── conftest.py                      — 기존 유지
├── integration/
│   ├── conftest.py                  — 신규: live DB fixture, MCP mock
│   ├── test_workflow_integration.py — WF-01~06 (Mock)
│   ├── test_workflow_error_recovery.py — WF-05~06 (Mock)
│   ├── test_mcp_tools.py           — MCP-01~05 (Mock)
│   ├── test_db_fallback.py         — DB-03 (Mock)
│   └── live/
│       ├── conftest.py             — Live DB 연결, pytest.mark.live
│       ├── test_workflow_live_db.py — WF-07~08, DB-01~05
│       └── test_mcp_tools_live.py  — MCP-06~07
└── workflow/                        — 기존 유지 (단위 테스트)
```

### 구현 순서

| 단계 | 작업 | 의존성 |
|:---:|------|--------|
| 1 | `integration/conftest.py` 재작성 (fixture 인프라) | — |
| 2 | `test_workflow_integration.py` (WF-01~04, Mock) | 단계 1 |
| 3 | `test_workflow_error_recovery.py` (WF-05~06, Mock) | 단계 1 |
| 4 | `test_mcp_tools.py` (MCP-01~05, Mock) | 단계 1 |
| 5 | `test_db_fallback.py` (DB-03, Mock) | 단계 1 |
| 6 | `live/conftest.py` + `test_workflow_live_db.py` (Live) | 로컬 PostgreSQL |
| 7 | `live/test_mcp_tools_live.py` (Live) | SearXNG Docker |

### pytest 설정 추가 (pyproject.toml)

```toml
[tool.pytest.ini_options]
markers = [
    "live: 실제 외부 서비스 연결 필요 (로컬/스테이징 전용)",
]
```

---

## 6. Mock 전략

### 6.1 MCP 도구 Mock 설계

```python
# research_gather 노드가 호출하는 도구별 mock
mock_searxng = AsyncMock(return_value={
    "results": [
        {"title": "클라우드 ERP 트렌드", "url": "...", "snippet": "..."},
    ]
})
mock_openalex = AsyncMock(return_value={
    "results": [
        {"title": "ERP Cloud Migration Study", "doi": "...", "abstract": "..."},
    ]
})
mock_g2b_research = AsyncMock(return_value={
    "similar_bids": [...],
    "competitor_history": [...],
})
```

### 6.2 에러 시나리오 Mock

```python
# Claude 타임아웃 시뮬레이션
mock_claude_timeout = AsyncMock(side_effect=AITimeoutError(step="strategy_generate"))

# DB 연결 실패 시뮬레이션
mock_db_fail = AsyncMock(side_effect=ConnectionError("PostgreSQL connection refused"))

# MCP 도구 실패 시뮬레이션
mock_searxng_fail = AsyncMock(side_effect=RuntimeError("SearXNG unavailable"))
```

---

## 7. 성공 기준

| 지표 | 목표 |
|------|------|
| Mock 통합 테스트 통과율 | 100% (CI 필수) |
| Live 통합 테스트 통과율 | 100% (수동 실행) |
| 워크플로 시나리오 커버리지 | Happy + 3 분기 + 2 에러 = **6 시나리오** |
| MCP 도구 커버리지 | 3 도구 x (성공 + 실패) = **6 케이스** |
| DB 통합 커버리지 | 체크포인터 + RLS + 폴백 + 동시성 = **5 케이스** |
| **총 테스트 케이스** | **17+ 케이스** |

---

## 8. 리스크 및 의존성

| 리스크 | 영향 | 완화 방안 |
|--------|------|---------|
| Live 테스트용 로컬 PostgreSQL 필요 | DB-01~05, WF-07~08 실행 불가 | Docker Compose로 제공 |
| SearXNG Docker 필요 | MCP-06 실행 불가 | docker-compose.test.yml에 포함 |
| Claude API 비용 | Live 테스트 시 토큰 소모 | `pytest.mark.live` 분리, CI에서 제외 |
| G2B API Rate Limit | MCP-07 반복 실행 시 차단 | 캐시 활용 + 1일 1회 제한 |

---

## 9. 비범위 (Out of Scope)

- 프론트엔드 E2E 테스트 (Playwright 등)
- 성능/부하 테스트
- 보안 침투 테스트
- 기존 `tests/test_phase*.py` API 테스트 리팩토링
