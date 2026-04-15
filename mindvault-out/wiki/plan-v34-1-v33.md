# Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 & 1. 현황 (v3.3 검토 결과)
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 5 connections
  - -> contains -> [[1-v33]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
- **1. 현황 (v3.3 검토 결과)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 3 connections
  - -> contains -> [[11-critical]]
  - -> contains -> [[12]]
  - <- contains <- [[plan-v34]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22]]
  - <- contains <- [[plan-v34]]
- **3. 작업 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 3 connections
  - -> contains -> [[phase-a-critical]]
  - -> contains -> [[phase-b]]
  - <- contains <- [[plan-v34]]
- **1.1 Critical 버그** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[1-v33]]
- **1.2 구조 문제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[1-v33]]
- **2.1 최우선 (버그 수정)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2.2 구조 최적화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **4. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[plan-v34]]
- **5. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[plan-v34]]
- **Phase A — Critical 버그** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **Phase B — 구조 최적화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-agent-v34.plan.md) -- 1 connections
  - <- contains <- [[3]]

## Internal Relationships
- 1. 현황 (v3.3 검토 결과) -> contains -> 1.1 Critical 버그 [EXTRACTED]
- 1. 현황 (v3.3 검토 결과) -> contains -> 1.2 구조 문제 [EXTRACTED]
- 2. 목표 -> contains -> 2.1 최우선 (버그 수정) [EXTRACTED]
- 2. 목표 -> contains -> 2.2 구조 최적화 [EXTRACTED]
- 3. 작업 목록 -> contains -> Phase A — Critical 버그 [EXTRACTED]
- 3. 작업 목록 -> contains -> Phase B — 구조 최적화 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 -> contains -> 1. 현황 (v3.3 검토 결과) [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 -> contains -> 2. 목표 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 -> contains -> 3. 작업 목록 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 -> contains -> 4. 성공 기준 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화 -> contains -> 5. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 용역 제안서 자동 생성 에이전트 v3.4 — 최적화, 1. 현황 (v3.3 검토 결과), 2. 목표를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-agent-v34.plan.md이다.

### Key Facts
- 2.1 최우선 (버그 수정) - /execute → Phase 1~5 완전 실행 가능하게 - 이벤트루프 블로킹 해소
- Phase A — Critical 버그
- | # | 위치 | 문제 | 영향 | |---|------|------|------| | B1 | phase_executor.py:42 | parse_rfp(rfp_content) — 문자열을 Path로 전달 | /execute 호출 즉시 Phase 1 실패 | | B2 | phase_executor.py:49,61,75,93 | anthropic.Anthropic (동기) 사용 | async 함수에서 이벤트루프 블로킹 |
- | # | 위치 | 문제 | 영향 | |---|------|------|------| | S1 | routes_v31.py | /execute가 blocking HTTP | timeout 위험, UX 저하 | | S2 | routes.py | legacy/v3/test 라우터 모두 노출 | Swagger 혼란, 에러 노출 | | S3 | main.py | lifespan이 미존재 모듈 초기화 | 서버 시작 불안정 | | S4 | phase_executor.py | _parse_json_safe 중복 | 코드 중복 | | S5 |…
- 2.2 구조 최적화 - /execute 백그라운드 실행 전환 (202 Accepted 패턴) - 레거시/테스트 라우터 제거 - main.py lifespan 단순화 - JSON 파싱 유틸 통합
