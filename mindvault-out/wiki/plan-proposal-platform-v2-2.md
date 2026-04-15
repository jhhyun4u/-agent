# Plan: proposal-platform-v2 & 2. 구현 범위 (순차 구현)
Cohesion: 0.14 | Nodes: 14

## Key Nodes
- **Plan: proposal-platform-v2** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5-yagni]]
  - -> contains -> [[6]]
- **2. 구현 범위 (순차 구현)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 5 connections
  - -> contains -> [[phase-a]]
  - -> contains -> [[phase-b-ux]]
  - -> contains -> [[phase-c]]
  - -> contains -> [[phase-d-rfp]]
  - <- contains <- [[plan-proposal-platform-v2]]
- **4. 기술 영향 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 4 connections
  - -> contains -> [[db-supabase]]
  - -> contains -> [[fastapi]]
  - -> contains -> [[nextjs]]
  - <- contains <- [[plan-proposal-platform-v2]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v2]]
- **3. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v2]]
- **5. YAGNI 검토** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v2]]
- **6. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-proposal-platform-v2]]
- **DB (Supabase)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **백엔드 (FastAPI)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **프론트엔드 (Next.js)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase A — 섹션 라이브러리 + 아카이브 (임팩트 최대)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **Phase B — 작업 단계 + 버전관리 (UX 핵심)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **Phase C — 공통서식 라이브러리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **Phase D — 수주율 대시보드 + RFP 캘린더** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.plan.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 2. 구현 범위 (순차 구현) -> contains -> Phase A — 섹션 라이브러리 + 아카이브 (임팩트 최대) [EXTRACTED]
- 2. 구현 범위 (순차 구현) -> contains -> Phase B — 작업 단계 + 버전관리 (UX 핵심) [EXTRACTED]
- 2. 구현 범위 (순차 구현) -> contains -> Phase C — 공통서식 라이브러리 [EXTRACTED]
- 2. 구현 범위 (순차 구현) -> contains -> Phase D — 수주율 대시보드 + RFP 캘린더 [EXTRACTED]
- 4. 기술 영향 범위 -> contains -> DB (Supabase) [EXTRACTED]
- 4. 기술 영향 범위 -> contains -> 백엔드 (FastAPI) [EXTRACTED]
- 4. 기술 영향 범위 -> contains -> 프론트엔드 (Next.js) [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 2. 구현 범위 (순차 구현) [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 3. 성공 기준 [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 4. 기술 영향 범위 [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 5. YAGNI 검토 [EXTRACTED]
- Plan: proposal-platform-v2 -> contains -> 6. 구현 순서 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: proposal-platform-v2, 2. 구현 범위 (순차 구현), 4. 기술 영향 범위를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-platform-v2.plan.md이다.

### Key Facts
- 메타 정보 | 항목 | 내용 | |------|------| | Feature | proposal-platform-v2 | | 작성일 | 2026-03-08 | | 우선순위 | P0 | | 예상 Phase | 4단계 순차 구현 |
- Phase A — 섹션 라이브러리 + 아카이브 (임팩트 최대) 회사 자산을 AI에게 먹이면 제안서 품질이 즉시 향상됨.
- DB (Supabase) - `sections` 테이블 신규 (섹션 라이브러리) - `company_assets` 테이블 신규 (회사 자료) - `form_templates` 테이블 신규 (공통서식) - `proposals` 테이블: `version`, `parent_id`, `form_template_id` 컬럼 추가 - `rfp_calendar` 테이블 신규
- v1은 단일 RFP → 제안서 생성 도구였다면, **v2는 팀 단위 제안서 관리 플랫폼**으로 확장. 반복 작업을 줄이고, 팀 지식을 축적하며, 수주율을 높이는 것이 목표.
- | Phase | 기준 | |-------|------| | A | 섹션 라이브러리에서 선택한 내용이 AI 생성 제안서에 반영됨 | | A | 아카이브에서 회사/팀/개인 필터가 동작함 | | B | Phase 진행 대시보드가 실시간으로 업데이트됨 | | B | 동일 RFP의 v1/v2 결과물을 나란히 비교 가능 | | C | 서식 선택 후 생성된 제안서에 서식이 반영됨 | | D | 수주율 차트가 실제 win_result 데이터 기반으로 표시됨 |
