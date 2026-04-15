# 로그/모니터링 개선 (Monitoring Enhancement) & 4. 요구사항
Cohesion: 0.10 | Nodes: 20

## Key Nodes
- **로그/모니터링 개선 (Monitoring Enhancement)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-as-is]]
  - -> contains -> [[3-to-be]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-out-of-scope]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **4. 요구사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 7 connections
  - -> contains -> [[4-1-silent-exception-g1-high]]
  - -> contains -> [[4-2-db-g2-high]]
  - -> contains -> [[4-3-g3-medium]]
  - -> contains -> [[4-4-g4-medium]]
  - -> contains -> [[4-5-g5-low]]
  - -> contains -> [[4-6-apm-g6-low]]
  - <- contains <- [[monitoring-enhancement]]
- **5. 구현 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 4 connections
  - -> contains -> [[phase-a-silent-exception-db-high]]
  - -> contains -> [[phase-b-medium]]
  - -> contains -> [[phase-c-low]]
  - <- contains <- [[monitoring-enhancement]]
- **2. 현재 상태 (AS-IS)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 3 connections
  - -> contains -> [[2-1-keep]]
  - -> contains -> [[2-2-gap]]
  - <- contains <- [[monitoring-enhancement]]
- **1. 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **2-1. 잘 되어 있는 것 (Keep)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[2-as-is]]
- **2-2. 부족한 것 (Gap)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[2-as-is]]
- **3. 목표 상태 (TO-BE)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **4-1. Silent Exception 제거 (G1) — HIGH** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4-2. 에러 DB 기록 통합 (G2) — HIGH** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4-3. 에러 알림 (G3) — MEDIUM** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4-4. 노드 헬스 집계 (G4) — MEDIUM** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4-5. 프론트엔드 에러 수집 (G5) — LOW** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4-6. 외부 APM 연동 준비 (G6) — LOW (향후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **6. 구현하지 않는 것 (Out of Scope)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **7. 우선순위 및 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[monitoring-enhancement]]
- **Phase A — Silent Exception 제거 + 에러 DB 기록 (HIGH)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase B — 에러 알림 + 노드 헬스 (MEDIUM)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase C — 프론트엔드 에러 수집 (LOW)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\monitoring-enhancement\monitoring-enhancement.plan.md) -- 1 connections
  - <- contains <- [[5]]

## Internal Relationships
- 2. 현재 상태 (AS-IS) -> contains -> 2-1. 잘 되어 있는 것 (Keep) [EXTRACTED]
- 2. 현재 상태 (AS-IS) -> contains -> 2-2. 부족한 것 (Gap) [EXTRACTED]
- 4. 요구사항 -> contains -> 4-1. Silent Exception 제거 (G1) — HIGH [EXTRACTED]
- 4. 요구사항 -> contains -> 4-2. 에러 DB 기록 통합 (G2) — HIGH [EXTRACTED]
- 4. 요구사항 -> contains -> 4-3. 에러 알림 (G3) — MEDIUM [EXTRACTED]
- 4. 요구사항 -> contains -> 4-4. 노드 헬스 집계 (G4) — MEDIUM [EXTRACTED]
- 4. 요구사항 -> contains -> 4-5. 프론트엔드 에러 수집 (G5) — LOW [EXTRACTED]
- 4. 요구사항 -> contains -> 4-6. 외부 APM 연동 준비 (G6) — LOW (향후) [EXTRACTED]
- 5. 구현 범위 -> contains -> Phase A — Silent Exception 제거 + 에러 DB 기록 (HIGH) [EXTRACTED]
- 5. 구현 범위 -> contains -> Phase B — 에러 알림 + 노드 헬스 (MEDIUM) [EXTRACTED]
- 5. 구현 범위 -> contains -> Phase C — 프론트엔드 에러 수집 (LOW) [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 1. 목적 [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 2. 현재 상태 (AS-IS) [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 3. 목표 상태 (TO-BE) [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 4. 요구사항 [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 5. 구현 범위 [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 6. 구현하지 않는 것 (Out of Scope) [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 7. 우선순위 및 의존성 [EXTRACTED]
- 로그/모니터링 개선 (Monitoring Enhancement) -> contains -> 8. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 로그/모니터링 개선 (Monitoring Enhancement), 4. 요구사항, 5. 구현 범위를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 monitoring-enhancement.plan.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 문서 버전 | v1.0 | | 작성일 | 2026-03-26 | | 상태 | 초안 | | 선행 | Phase 0~6 완료 |
- 4-1. Silent Exception 제거 (G1) — HIGH - **MON-01**: `except Exception:` 패턴 26건을 모두 `except Exception as e: logger.error(...)` 또는 적절한 fallback 로깅으로 교체 - **MON-02**: 그래프 노드의 최상위 except에서 `error_message`를 state에 기록하여 프론트엔드에서 확인 가능하게 함
- Phase A — Silent Exception 제거 + 에러 DB 기록 (HIGH) | 파일 | 작업 | 예상 변경량 | |------|------|------------| | `app/graph/nodes/*.py` (11파일) | `except Exception:` → 로깅 + state 에러 기록 | ~80줄 | | `app/graph/token_tracking.py` | exception 시 error 로그 + DB insert | ~20줄 | | `app/services/ai_status_manager.py` |…
- 2-1. 잘 되어 있는 것 (Keep) | 항목 | 구현 위치 | 비고 | |------|-----------|------| | JSON 구조화 로깅 | `main.py` `_JsonFormatter` | `log_format="json"` 시 활성화 | | Request ID 전파 | `middleware/request_id.py` | ContextVar + X-Request-ID 헤더 | | 느린 응답 경고 | `request_id.py:97` | 1초 초과 시 warning | | AI 작업 상태 추적 |…
- LangGraph 에이전트(노드) 실행 중 오류 발생 시 **원인 파악에 필요한 시간을 단축**하고, 운영 환경에서 **장애를 사전에 감지**할 수 있도록 모니터링 인프라를 개선한다.
