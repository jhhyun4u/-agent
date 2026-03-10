# Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-agent-v34 |
| 작성일 | 2026-03-05 |
| 기반 버전 | v3.3 (Phase Pipeline 완성) |
| 목표 | 런타임 버그 수정 + 구조 최적화 |
| 우선순위 | High |

---

## 1. 현황 (v3.3 검토 결과)

### 1.1 Critical 버그

| # | 위치 | 문제 | 영향 |
|---|------|------|------|
| B1 | phase_executor.py:42 | parse_rfp(rfp_content) — 문자열을 Path로 전달 | /execute 호출 즉시 Phase 1 실패 |
| B2 | phase_executor.py:49,61,75,93 | anthropic.Anthropic (동기) 사용 | async 함수에서 이벤트루프 블로킹 |

### 1.2 구조 문제

| # | 위치 | 문제 | 영향 |
|---|------|------|------|
| S1 | routes_v31.py | /execute가 blocking HTTP | timeout 위험, UX 저하 |
| S2 | routes.py | legacy/v3/test 라우터 모두 노출 | Swagger 혼란, 에러 노출 |
| S3 | main.py | lifespan이 미존재 모듈 초기화 | 서버 시작 불안정 |
| S4 | phase_executor.py | _parse_json_safe 중복 | 코드 중복 |
| S5 | phase_executor.py:92 | Phase 5 content v[:300] | 품질점수 신뢰성 낮음 |

---

## 2. 목표

### 2.1 최우선 (버그 수정)
- /execute → Phase 1~5 완전 실행 가능하게
- 이벤트루프 블로킹 해소

### 2.2 구조 최적화
- /execute 백그라운드 실행 전환 (202 Accepted 패턴)
- 레거시/테스트 라우터 제거
- main.py lifespan 단순화
- JSON 파싱 유틸 통합

---

## 3. 작업 목록

### Phase A — Critical 버그

| 순서 | 파일 | 작업 |
|------|------|------|
| A1 | rfp_parser.py | parse_rfp_text(content: str) 함수 추가 |
| A2 | phase_executor.py | phase1_research에서 parse_rfp_text 사용 |
| A3 | phase_executor.py | anthropic.Anthropic → AsyncAnthropic + await |

### Phase B — 구조 최적화

| 순서 | 파일 | 작업 |
|------|------|------|
| B1 | routes_v31.py | /execute → BackgroundTasks 비동기 실행 |
| B2 | routes.py | legacy, test 라우터 제거 |
| B3 | main.py | lifespan 단순화 |
| B4 | phase_executor.py | _parse_json_safe 통합 |
| B5 | phase_executor.py | Phase 5 preview 300자 → 1000자 |

---

## 4. 성공 기준

| 기준 | 검증 |
|------|------|
| /execute Phase 1~5 완전 실행 | RFP 텍스트 테스트 |
| AsyncAnthropic 사용 | import 확인 |
| /execute 즉시 202 반환 | 응답시간 < 1초 |
| Swagger에 v3.1만 노출 | /docs 확인 |
| 서버 기동 오류 0건 | import 테스트 |

---

## 5. 다음 단계

다음: /pdca design proposal-agent-v34
