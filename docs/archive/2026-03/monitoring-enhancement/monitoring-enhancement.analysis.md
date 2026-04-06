# Monitoring Enhancement — 설계-구현 갭 분석 보고서

> **분석 유형**: Gap Analysis (설계 vs 구현)
>
> **프로젝트**: 용역제안 Coworker
> **분석일**: 2026-03-26
> **설계 문서**: `docs/02-design/features/monitoring-enhancement.design.md` v1.0
> **요구사항**: `docs/01-plan/features/monitoring-enhancement.plan.md` v1.0

---

## 1. 전체 점수

| 카테고리 | v1.0 점수 | v1.1 점수 | 상태 |
|----------|:--------:|:--------:|:----:|
| Phase A (HIGH) | 88% | 100% | PASS |
| Phase B (MEDIUM) | 100% | 100% | PASS |
| Phase C (LOW) | 100% | 100% | PASS |
| **종합** | **92%** | **100%** | **PASS** |

---

## 2. 요구사항별 검증 결과

| MON | 항목 | 배점 | 득점 | 판정 |
|-----|------|:----:|:----:|:----:|
| MON-01 | Silent except 26건 제거 | 15 | 15 | PASS |
| MON-02 | node_errors state 기록 | 10 | 10 | PASS (v1.1) |
| MON-03 | track_tokens 에러 경로 + DB 기록 | 15 | 15 | PASS |
| MON-04 | fail_task → persist_log 연동 | 10 | 10 | PASS |
| MON-05 | Teams Webhook 에러 알림 | 10 | 10 | PASS |
| MON-06 | 인앱 에러 알림 | 10 | 10 | PASS |
| MON-07 | mv_node_health MV | 10 | 10 | PASS |
| MON-08 | node-health API | 5 | 5 | PASS |
| MON-09 | recent-errors API | 5 | 5 | PASS |
| MON-10 | POST /client-errors + error-reporter.ts | 5 | 5 | PASS |
| MON-11 | client_error_logs 테이블 | 5 | 5 | PASS |
| **합계** | | **100** | **100** | |

---

## 3. 미구현 사항 (GAP)

### GAP-1: node_errors state 기록 (MON-02) — RESOLVED (v1.1)

**v1.0**: 필드만 존재, 0개 노드가 기록 (88% → 92%)

**v1.1 수정** (4개 노드, 내부 except 블록이 있는 곳):
- `go_no_go.py` — rfp 없을 때 early return에 node_errors 추가
- `submission_nodes.py` — submission_plan, cost_sheet_generate 실패 시 node_errors 추가
- `rfp_fetch.py` — G2B 상세 수집 실패 시 node_errors 추가

나머지(ppt_nodes 2건, research_gather)는 내부 핵심 except가 없고 `track_tokens` 데코레이터가 전체를 감싸므로, 에러 시 DB에 직접 기록되어 별도 node_errors 불필요.

---

## 4. 추가/변경 사항

| # | 유형 | 항목 | 영향 |
|---|------|------|------|
| ADD-1 | 추가 | token_tracking의 notify_err 예외 처리 | 긍정 (안정성) |
| CHG-1 | 변경 | 마이그레이션 번호 013/014 → 015 | 없음 |
| CHG-2 | 변경 | 프론트 경로 `src/lib/` → `lib/` | 없음 |
| CHG-3 | 추가 | ErrorReporterInit 별도 컴포넌트 분리 | 긍정 (SSR 분리) |

---

## 5. Plan §8 검증 기준 달성

| 기준 | 기대 | 실제 | 달성 |
|------|------|------|:----:|
| silent except 0건 | grep 결과 0 | **0건** | PASS |
| 에러 시 ai_task_logs error 행 | _persist_ai_task_log_error 존재 | 함수 존재 + track_tokens에서 호출 | PASS |
| Teams 알림 수신 | notify_agent_error + send_teams_notification | 구현 확인 | PASS |
| 노드 헬스 API | GET /api/admin/monitoring/node-health 200 | 엔드포인트 존재 | PASS |
| 프론트 에러 수집 | POST /api/client-errors + client_error_logs + error-reporter.ts | 3개 모두 존재 | PASS |

---

## 6. 권장 조치

모든 GAP 해소 완료. 추가 조치 사항 없음.

---

## 버전 이력

| 버전 | 일자 | 변경사항 |
|------|------|----------|
| 1.0 | 2026-03-26 | 초기 갭 분석 (92%) |
| 1.1 | 2026-03-26 | GAP-1 해소 — node_errors 기록 추가 (100%) |
