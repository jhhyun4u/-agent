# 통합 테스트 완료 보고서 — test-integration

- **Feature**: test-integration
- **PDCA 사이클**: Plan → Design → Do → Check → Act-1 → Report
- **작업일**: 2026-03-26
- **Match Rate**: 75% → **90%**

---

## 1. 목표 및 배경

TENOPA 시스템의 3대 핵심 통합 지점에 대한 테스트 부재를 해소:

| 통합 지점 | Before | After |
|----------|:---:|:---:|
| LangGraph 워크플로 흐름 | Happy path 1개만 | **8개 시나리오** |
| PostgreSQL 연결 | 테스트 없음 | **2 mock + 3 live** |
| MCP 도구 호출 | 테스트 없음 | **6 mock + 2 live** |

---

## 2. PDCA 사이클 요약

| 단계 | 산출물 | 핵심 결정 |
|------|--------|---------|
| **Plan** | `test-integration.plan.md` | Level 1 (Mock/CI) + Level 2 (Live/수동) 2단계 전략 |
| **Design** | `test-integration.design.md` | 9개 신규 파일, 20개 테스트 케이스 설계 |
| **Do** | 8개 테스트 파일 + pyproject.toml | 13 pass / 4 fail (state 키 불일치, mock 경로 오류) |
| **Check** | `test-integration.analysis.md` | Match Rate 75% — GAP-3 (MCP), GAP-1 (Fork) |
| **Act-1** | +7 테스트 추가, 기존 수정 | 20 pass / 0 fail → Match Rate **90%** |

---

## 3. 최종 테스트 결과

```
20 passed, 0 failed, 10 warnings in 2.35s
```

### 파일별 상세

| 파일 | 테스트 수 | 커버 영역 |
|------|:---:|------|
| `test_workflow_integration.py` | 8 | WF-01~04 + Fork/Convergence 라우팅 4개 |
| `test_workflow_error_recovery.py` | 4 | self_review 5방향 라우팅 3개 + Claude timeout 1개 |
| `test_mcp_tools.py` | 6 | research_brief 산출 + KB 연동 + G2B mock + graceful degradation |
| `test_db_fallback.py` | 2 | PostgresSaver 폴백 + MemorySaver 체크포인트 |
| **합계** | **20** | |

### Live 테스트 (환경 준비 시 실행)

| 파일 | 테스트 수 | 필요 환경 |
|------|:---:|------|
| `live/test_workflow_live_db.py` | 3 | `TEST_DATABASE_URL` |
| `live/test_mcp_tools_live.py` | 2 | `G2B_API_KEY`, `SEARXNG_URL` |

---

## 4. 신규 파일 목록

| 파일 | 줄 수 | 용도 |
|------|:---:|------|
| `tests/integration/conftest.py` | ~180 | Mock fixture 인프라 (Claude, MCP, 그래프 빌드) |
| `tests/integration/test_workflow_integration.py` | ~170 | 워크플로 통합 8개 |
| `tests/integration/test_workflow_error_recovery.py` | ~120 | 에러 복구 4개 |
| `tests/integration/test_mcp_tools.py` | ~140 | MCP 도구 6개 |
| `tests/integration/test_db_fallback.py` | ~60 | DB 폴백 2개 |
| `tests/integration/live/conftest.py` | ~70 | Live fixture (DB, API) |
| `tests/integration/live/test_workflow_live_db.py` | ~90 | Live DB 3개 |
| `tests/integration/live/test_mcp_tools_live.py` | ~60 | Live API 2개 |
| `tests/integration/live/__init__.py` | 0 | 패키지 |
| **합계** | **~890** | **9 파일** |

### 수정 파일

| 파일 | 변경 내용 |
|------|---------|
| `pyproject.toml` | `addopts` 변경 (`--ignore=tests/integration` → `--ignore=tests/integration/live`), `markers` 추가 |

---

## 5. 테스트 전략 결정사항

### Fork 다중 Interrupt 대응
LangGraph v4.0에서 `fork_to_branches(Send())` 후 Path A/B가 동시에 interrupt를 발생시키면 resume 시 interrupt ID가 필요합니다. 이 제약으로:
- Fork/Convergence E2E 테스트 대신 **라우팅 함수 단위 테스트**로 검증
- `fork_to_branches`, `convergence_gate`, `plan_selective_fan_out` 3개 함수 직접 테스트
- HEAD 구간(fork 전)은 전체 그래프 E2E로 검증

### research_gather MCP 아키텍처
현재 research_gather는 **Claude 프롬프트 기반 리서치** (별도 MCP 도구 직접 호출 없음). 따라서:
- MCP "도구 호출" 테스트는 research_gather **노드 입출력 검증** + **KB 연동 검증**으로 대체
- G2B 서비스는 **서비스 레이어 단위 테스트**로 별도 검증
- 향후 SearXNG/OpenAlex 직접 호출 구현 시 Live 테스트 활용

---

## 6. 잔여 갭 (향후 과제)

| ID | 심각도 | 내용 | 해소 방안 |
|----|:---:|------|---------|
| GAP-4 | LOW | Live DB-02 RLS 정책 검증 | `live/test_workflow_live_db.py`에 RLS 테스트 추가 |
| GAP-5 | LOW | JSON fixture 파일 미생성 | 인라인 mock으로 충분, 필요 시 추출 |

---

## 7. 실행 방법

```bash
# Mock 통합 테스트 (CI 기본, ~2초)
uv run pytest tests/integration/ -v

# Live 테스트 포함 (로컬)
TEST_DATABASE_URL="postgresql://..." G2B_API_KEY="..." \
  uv run pytest tests/integration/ -m live -v

# 기존 단위/API 테스트 + 통합 테스트 전체
uv run pytest -v
```
