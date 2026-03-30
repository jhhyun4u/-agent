# 로그/모니터링 개선 (Monitoring Enhancement)

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-03-26 |
| 상태 | 초안 |
| 선행 | Phase 0~6 완료 |

---

## 1. 목적

LangGraph 에이전트(노드) 실행 중 오류 발생 시 **원인 파악에 필요한 시간을 단축**하고, 운영 환경에서 **장애를 사전에 감지**할 수 있도록 모니터링 인프라를 개선한다.

### 핵심 가치
- **빠른 장애 진단**: 에이전트 실패 시 request_id → 노드 → 에러 원인을 3분 이내 역추적
- **사전 감지**: 토큰 예산 초과, 하트비트 무응답, 반복 실패 패턴을 자동 알림
- **운영 가시성**: 노드별 성공률·지연시간·토큰 비용을 대시보드에서 한눈에 확인

---

## 2. 현재 상태 (AS-IS)

### 2-1. 잘 되어 있는 것 (Keep)
| 항목 | 구현 위치 | 비고 |
|------|-----------|------|
| JSON 구조화 로깅 | `main.py` `_JsonFormatter` | `log_format="json"` 시 활성화 |
| Request ID 전파 | `middleware/request_id.py` | ContextVar + X-Request-ID 헤더 |
| 느린 응답 경고 | `request_id.py:97` | 1초 초과 시 warning |
| AI 작업 상태 추적 | `ai_status_manager.py` | 인메모리 + SSE 이벤트 |
| 토큰 비용 DB 기록 | `token_tracking.py` | `ai_task_logs` 테이블 자동 기록 |
| 헬스체크 | `main.py /health` | DB 연결 포함 |
| 하트비트 타임아웃 | `ai_status_manager.py` | `no_response` 자동 전환 |

### 2-2. 부족한 것 (Gap)
| # | 문제 | 영향 | 심각도 |
|---|------|------|--------|
| G1 | **silent except** — `except Exception:` 26건 (그래프 노드)에서 로그 없이 삼키는 패턴 | 실패해도 원인 불명, state에 빈값만 남음 | HIGH |
| G2 | **ai_task_logs에 error 미기록** — `track_tokens`는 성공만 기록, `ai_status_manager.persist_log`는 호출처 미통일 | DB에서 에러 이력 조회 불가 | HIGH |
| G3 | **에러 알림 없음** — 에이전트 실패 시 Teams/인앱 알림 미발송 | 운영자가 실패를 모름 | MEDIUM |
| G4 | **노드별 성공률/지연 집계 없음** — ai_task_logs 데이터는 있으나 집계 API/MV 없음 | 어떤 노드가 병목인지 파악 불가 | MEDIUM |
| G5 | **프론트엔드 에러 로그 미수집** — 클라이언트 측 JS 에러 서버 전송 없음 | 사용자 화면 오류 진단 불가 | LOW |
| G6 | **외부 모니터링 미연동** — Sentry/Datadog 등 APM 도구 없음 | 알림·대시보드·트렌드 분석 수동 | LOW |

---

## 3. 목표 상태 (TO-BE)

```
[에이전트 노드 실행]
  │
  ├── 성공 → ai_task_logs (status=complete, tokens, cost, duration)
  │
  └── 실패 → ai_task_logs (status=error, error_message, traceback_summary)
              │
              ├── logger.error (request_id + proposal_id + node_name + traceback)
              ├── Teams Webhook 알림 (MEDIUM 이상)
              └── 인앱 알림 (담당자에게)

[집계]
  ai_task_logs → mv_node_health (노드별 success_rate, avg_duration, error_count)
                → /api/admin/monitoring (대시보드 API)
```

---

## 4. 요구사항

### 4-1. Silent Exception 제거 (G1) — HIGH
- **MON-01**: `except Exception:` 패턴 26건을 모두 `except Exception as e: logger.error(...)` 또는 적절한 fallback 로깅으로 교체
- **MON-02**: 그래프 노드의 최상위 except에서 `error_message`를 state에 기록하여 프론트엔드에서 확인 가능하게 함

### 4-2. 에러 DB 기록 통합 (G2) — HIGH
- **MON-03**: `track_tokens` 데코레이터가 노드 실행 실패(exception) 시에도 `ai_task_logs`에 `status='error'`, `error_message` 기록
- **MON-04**: `ai_status_manager.fail_task()` 호출 시 자동으로 `persist_log(status='error')` 연동

### 4-3. 에러 알림 (G3) — MEDIUM
- **MON-05**: 에이전트 노드 에러 발생 시 Teams Webhook으로 장애 알림 발송 (노드명, proposal_id, 에러 요약)
- **MON-06**: 인앱 알림으로 해당 제안서 담당자에게 "AI 작업 실패" 알림

### 4-4. 노드 헬스 집계 (G4) — MEDIUM
- **MON-07**: `mv_node_health` Materialized View — 노드별 최근 24h/7d 성공률, 평균 지연, 에러 수
- **MON-08**: `/api/admin/monitoring/node-health` API 엔드포인트
- **MON-09**: `/api/admin/monitoring/recent-errors` — 최근 에러 목록 (proposal_id, node, error, timestamp)

### 4-5. 프론트엔드 에러 수집 (G5) — LOW
- **MON-10**: `POST /api/client-errors` 엔드포인트로 프론트엔드 JS 에러 수집
- **MON-11**: `client_error_logs` 테이블에 저장 (user_id, url, error, stack, timestamp)

### 4-6. 외부 APM 연동 준비 (G6) — LOW (향후)
- **MON-12**: Sentry SDK 연동 가능 구조 준비 (config에 `sentry_dsn` 추가, 초기화 코드)
- 현 단계에서는 **구현하지 않음** — 배포 인프라 확정 후 진행

---

## 5. 구현 범위

### Phase A — Silent Exception 제거 + 에러 DB 기록 (HIGH)
| 파일 | 작업 | 예상 변경량 |
|------|------|------------|
| `app/graph/nodes/*.py` (11파일) | `except Exception:` → 로깅 + state 에러 기록 | ~80줄 |
| `app/graph/token_tracking.py` | exception 시 error 로그 + DB insert | ~20줄 |
| `app/services/ai_status_manager.py` | `fail_task()` → `persist_log()` 자동 호출 | ~10줄 |

### Phase B — 에러 알림 + 노드 헬스 (MEDIUM)
| 파일 | 작업 | 예상 변경량 |
|------|------|------------|
| `app/services/notification_service.py` | `notify_agent_error()` 함수 추가 | ~30줄 |
| `app/graph/token_tracking.py` | 에러 시 알림 호출 연동 | ~10줄 |
| `database/migrations/0XX_node_health.sql` | `mv_node_health` MV 생성 | ~30줄 |
| `app/api/routes_admin.py` | monitoring 엔드포인트 2개 | ~60줄 |

### Phase C — 프론트엔드 에러 수집 (LOW)
| 파일 | 작업 | 예상 변경량 |
|------|------|------------|
| `database/migrations/0XX_client_errors.sql` | `client_error_logs` 테이블 | ~15줄 |
| `app/api/routes_admin.py` | `POST /api/client-errors` | ~20줄 |
| `frontend/src/lib/error-reporter.ts` | 글로벌 에러 핸들러 + 서버 전송 | ~40줄 |

---

## 6. 구현하지 않는 것 (Out of Scope)

| 항목 | 사유 |
|------|------|
| Sentry/Datadog 연동 | 배포 인프라(Railway/Render) 확정 후 진행 |
| 분산 트레이싱 (OpenTelemetry) | 단일 서버 구조에서 불필요 |
| 로그 파일 로테이션 | 컨테이너 환경에서 stdout 기반으로 충분 |
| 별도 모니터링 대시보드 UI | 기존 Admin 페이지에 통합하는 것으로 충분 |

---

## 7. 우선순위 및 의존성

```
Phase A (HIGH) ──→ Phase B (MEDIUM) ──→ Phase C (LOW)
  Silent Exception    에러 알림 + 집계     프론트 에러 수집
  에러 DB 기록
```

- Phase A는 **독립 수행 가능** (외부 의존 없음)
- Phase B는 Phase A 완료 후 (에러가 DB에 쌓여야 집계 가능)
- Phase C는 프론트엔드 작업이므로 독립적이나 우선순위 낮음

---

## 8. 성공 기준

| 기준 | 측정 방법 |
|------|-----------|
| silent except 0건 | `grep -c "except Exception:\s*$"` 결과 = 0 |
| 에이전트 에러 시 ai_task_logs에 error 행 존재 | 의도적 실패 테스트 후 DB 조회 |
| Teams 알림 수신 | 에러 발생 시 Teams 채널에 메시지 도착 확인 |
| 노드 헬스 API 응답 | `/api/admin/monitoring/node-health` 200 OK |
