# Monitoring Enhancement — PDCA 완료 보고서

| 항목 | 내용 |
|------|------|
| 기능명 | 로그/모니터링 개선 (monitoring-enhancement) |
| 완료일 | 2026-03-26 |
| PDCA 사이클 | 단일 세션 완료 (Plan → Design → Do → Check → Act → Report) |
| Match Rate | 92% (v1.0) → **100%** (v1.1, Act-1 후) |
| Iteration | 1회 |

---

## 1. 목적 및 배경

LangGraph 에이전트(노드) 실행 중 오류 발생 시 원인 파악에 필요한 시간을 단축하고, 운영 환경에서 장애를 사전 감지할 수 있도록 모니터링 인프라를 개선.

**핵심 동기**: 그래프 노드 11개 파일에서 `except Exception:` (로깅 없이 삼키는) 패턴이 26건 발견되어, 에이전트 실패 시 원인 추적이 불가능했음.

---

## 2. 구현 요약

### Phase A — Silent Exception 제거 + 에러 DB 기록 (HIGH)

| 요구사항 | 구현 내용 | 파일 |
|----------|-----------|------|
| MON-01 | `except Exception:` 26건 → `logger.debug/error` 로깅 추가 | 11개 노드 파일 |
| MON-02 | `node_errors` state 필드 + 4개 노드에서 실패 시 기록 | `state.py`, `go_no_go.py`, `submission_nodes.py`, `rfp_fetch.py` |
| MON-03 | `track_tokens` 데코레이터 에러 경로 — DB 기록 + 알림 | `token_tracking.py` |
| MON-04 | `fail_task()` async 전환 + `persist_log()` 자동 호출 | `ai_status_manager.py` |

### Phase B — 에러 알림 + 노드 헬스 집계 (MEDIUM)

| 요구사항 | 구현 내용 | 파일 |
|----------|-----------|------|
| MON-05/06 | `notify_agent_error()` — Teams Webhook + 인앱 알림 | `notification_service.py` |
| MON-07 | `mv_node_health` MV (노드별 성공률/지연/비용, 24h/7d) | `015_node_health.sql` |
| MON-08 | `GET /api/admin/monitoring/node-health` | `routes_admin.py` |
| MON-09 | `GET /api/admin/monitoring/recent-errors` | `routes_admin.py` |

### Phase C — 프론트엔드 에러 수집 (LOW)

| 요구사항 | 구현 내용 | 파일 |
|----------|-----------|------|
| MON-10 | `POST /api/client-errors` + 브라우저 글로벌 에러 캡처 | `routes_admin.py`, `error-reporter.ts`, `ErrorReporterInit.tsx` |
| MON-11 | `client_error_logs` 테이블 | `015_client_errors.sql` |

---

## 3. 변경 파일 목록

### 수정 (16파일)

| 파일 | 변경 요약 |
|------|-----------|
| `app/graph/token_tracking.py` | 에러 경로 try/except + `_persist_ai_task_log_error` 함수 |
| `app/graph/state.py` | `node_errors: Annotated[dict, ...]` 필드 |
| `app/graph/nodes/proposal_nodes.py` | 6건 silent except → debug 로깅 |
| `app/graph/nodes/strategy_generate.py` | 3건 |
| `app/graph/nodes/plan_nodes.py` | 3건 |
| `app/graph/nodes/ppt_nodes.py` | 5건 |
| `app/graph/nodes/bid_plan.py` | 1건 |
| `app/graph/nodes/go_no_go.py` | 2건 + node_errors 추가 |
| `app/graph/nodes/research_gather.py` | 1건 |
| `app/graph/nodes/review_node.py` | 2건 |
| `app/graph/nodes/rfp_analyze.py` | 1건 |
| `app/graph/nodes/rfp_fetch.py` | 1건 + node_errors 추가 |
| `app/graph/nodes/rfp_search.py` | 1건 |
| `app/graph/nodes/submission_nodes.py` | 2건 node_errors 추가 |
| `app/services/ai_status_manager.py` | `fail_task()` async + persist_log 연동 |
| `app/services/notification_service.py` | `notify_agent_error()` 추가 |
| `app/api/routes_admin.py` | 모니터링 EP 2개 + POST /client-errors |
| `frontend/app/layout.tsx` | ErrorReporterInit 통합 |

### 신규 (4파일)

| 파일 | 내용 |
|------|------|
| `database/migrations/015_node_health.sql` | mv_node_health MV + RPC |
| `database/migrations/015_client_errors.sql` | client_error_logs 테이블 |
| `frontend/lib/error-reporter.ts` | 브라우저 글로벌 에러 캡처 |
| `frontend/components/ErrorReporterInit.tsx` | React 초기화 컴포넌트 |

---

## 4. Gap Analysis 결과

| 분석 버전 | Match Rate | GAP 수 | 비고 |
|-----------|:----------:|:------:|------|
| v1.0 | 92% | 1건 (MON-02 node_errors 미기록) | Check 단계 |
| v1.1 | **100%** | 0건 | Act-1 후 |

---

## 5. 검증 결과

| 검증 항목 | 결과 |
|-----------|------|
| `grep "except Exception:\s*$"` 0건 | PASS — 26건 모두 로깅 추가 |
| ruff check 에러 0건 | PASS |
| `_persist_ai_task_log_error` 함수 존재 | PASS |
| `notify_agent_error` 함수 존재 | PASS |
| `GET /api/admin/monitoring/node-health` | PASS |
| `GET /api/admin/monitoring/recent-errors` | PASS |
| `POST /api/client-errors` | PASS |
| `node_errors` state 필드 + 4개 노드 기록 | PASS |

---

## 6. 장애 진단 플로우 (Before → After)

### Before
```
에이전트 실패 → except Exception: pass → 로그 없음 → DB 기록 없음
→ 운영자: "왜 결과가 비어있지?" → 원인 불명
```

### After
```
에이전트 실패 → track_tokens catch → logger.error (request_id 포함)
              → ai_task_logs INSERT (status=error, error_message)
              → Teams Webhook 알림 + 인앱 알림
              → node_errors state 기록 (프론트엔드 표시)
              → 운영자: /api/admin/monitoring/recent-errors 조회
              → 노드별 성공률: /api/admin/monitoring/node-health
```

---

## 7. 향후 과제

| 항목 | 시점 | 비고 |
|------|------|------|
| Sentry SDK 연동 | 배포 인프라 확정 후 | config에 `sentry_dsn` 추가 |
| 모니터링 대시보드 UI | 프론트엔드 어드민 페이지 확장 시 | 현재는 API만 제공 |
| mv_node_health 자동 리프레시 | cron 또는 lifespan | 현재 API 호출 시 수동 리프레시 |

---

## 8. PDCA 문서

| 단계 | 문서 |
|------|------|
| Plan | `docs/01-plan/features/monitoring-enhancement.plan.md` |
| Design | `docs/02-design/features/monitoring-enhancement.design.md` |
| Analysis | `docs/03-analysis/features/monitoring-enhancement.analysis.md` |
| Report | `docs/04-report/features/monitoring-enhancement.report.md` (본 문서) |
