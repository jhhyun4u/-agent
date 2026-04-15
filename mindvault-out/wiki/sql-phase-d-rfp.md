# sql & Phase D: 수주율 대시보드 + RFP 캘린더
Cohesion: 0.13 | Nodes: 20

## Key Nodes
- **sql** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 5 connections
  - <- has_code_example <- [[a-1-db]]
  - <- has_code_example <- [[b-1-db]]
  - <- has_code_example <- [[c-1-db]]
  - <- has_code_example <- [[d-1-db]]
  - <- has_code_example <- [[rls]]
- **Phase D: 수주율 대시보드 + RFP 캘린더** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 5 connections
  - -> contains -> [[d-1-db]]
  - -> contains -> [[d-2-api]]
  - -> contains -> [[d-3]]
  - -> contains -> [[rls]]
  - <- contains <- [[design-proposal-platform-v2]]
- **Design: proposal-platform-v2** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 4 connections
  - -> contains -> [[phase-a]]
  - -> contains -> [[phase-b]]
  - -> contains -> [[phase-c]]
  - -> contains -> [[phase-d-rfp]]
- **Phase A: 섹션 라이브러리 + 아카이브** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 4 connections
  - -> contains -> [[a-1-db]]
  - -> contains -> [[a-2-api]]
  - -> contains -> [[a-3]]
  - <- contains <- [[design-proposal-platform-v2]]
- **Phase B: 작업 단계 + 버전관리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 4 connections
  - -> contains -> [[b-1-db]]
  - -> contains -> [[b-2-api]]
  - -> contains -> [[b-3]]
  - <- contains <- [[design-proposal-platform-v2]]
- **Phase C: 공통서식 라이브러리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 4 connections
  - -> contains -> [[c-1-db]]
  - -> contains -> [[c-2-api]]
  - -> contains -> [[c-3]]
  - <- contains <- [[design-proposal-platform-v2]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - <- has_code_example <- [[a-2-api]]
  - <- has_code_example <- [[c-2-api]]
- **A-1. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[phase-a]]
- **A-2. 백엔드 API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-a]]
- **B-1. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[phase-b]]
- **C-1. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[phase-c]]
- **C-2. 백엔드 API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-c]]
- **D-1. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[phase-d-rfp]]
- **RLS 정책 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[phase-d-rfp]]
- **A-3. 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-a]]
- **B-2. 백엔드 API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-b]]
- **B-3. 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-b]]
- **C-3. 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-c]]
- **D-2. 백엔드 API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-d-rfp]]
- **D-3. 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2\proposal-platform-v2.design.md) -- 1 connections
  - <- contains <- [[phase-d-rfp]]

## Internal Relationships
- A-1. DB 스키마 -> has_code_example -> sql [EXTRACTED]
- A-2. 백엔드 API -> has_code_example -> python [EXTRACTED]
- B-1. DB 스키마 -> has_code_example -> sql [EXTRACTED]
- C-1. DB 스키마 -> has_code_example -> sql [EXTRACTED]
- C-2. 백엔드 API -> has_code_example -> python [EXTRACTED]
- D-1. DB 스키마 -> has_code_example -> sql [EXTRACTED]
- Design: proposal-platform-v2 -> contains -> Phase A: 섹션 라이브러리 + 아카이브 [EXTRACTED]
- Design: proposal-platform-v2 -> contains -> Phase B: 작업 단계 + 버전관리 [EXTRACTED]
- Design: proposal-platform-v2 -> contains -> Phase C: 공통서식 라이브러리 [EXTRACTED]
- Design: proposal-platform-v2 -> contains -> Phase D: 수주율 대시보드 + RFP 캘린더 [EXTRACTED]
- Phase A: 섹션 라이브러리 + 아카이브 -> contains -> A-1. DB 스키마 [EXTRACTED]
- Phase A: 섹션 라이브러리 + 아카이브 -> contains -> A-2. 백엔드 API [EXTRACTED]
- Phase A: 섹션 라이브러리 + 아카이브 -> contains -> A-3. 프론트엔드 [EXTRACTED]
- Phase B: 작업 단계 + 버전관리 -> contains -> B-1. DB 스키마 [EXTRACTED]
- Phase B: 작업 단계 + 버전관리 -> contains -> B-2. 백엔드 API [EXTRACTED]
- Phase B: 작업 단계 + 버전관리 -> contains -> B-3. 프론트엔드 [EXTRACTED]
- Phase C: 공통서식 라이브러리 -> contains -> C-1. DB 스키마 [EXTRACTED]
- Phase C: 공통서식 라이브러리 -> contains -> C-2. 백엔드 API [EXTRACTED]
- Phase C: 공통서식 라이브러리 -> contains -> C-3. 프론트엔드 [EXTRACTED]
- Phase D: 수주율 대시보드 + RFP 캘린더 -> contains -> D-1. DB 스키마 [EXTRACTED]
- Phase D: 수주율 대시보드 + RFP 캘린더 -> contains -> D-2. 백엔드 API [EXTRACTED]
- Phase D: 수주율 대시보드 + RFP 캘린더 -> contains -> D-3. 프론트엔드 [EXTRACTED]
- Phase D: 수주율 대시보드 + RFP 캘린더 -> contains -> RLS 정책 추가 [EXTRACTED]
- RLS 정책 추가 -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 sql, Phase D: 수주율 대시보드 + RFP 캘린더, Design: proposal-platform-v2를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-platform-v2.design.md이다.

### Key Facts
- ```sql -- 섹션 라이브러리 CREATE TABLE sections ( id          UUID PRIMARY KEY DEFAULT gen_random_uuid(), team_id     UUID REFERENCES teams(id) ON DELETE CASCADE, owner_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, title       TEXT NOT NULL, category    TEXT NOT NULL CHECK (category IN…
- 메타 정보 | 항목 | 내용 | |------|------| | Feature | proposal-platform-v2 | | 작성일 | 2026-03-08 | | 기반 Plan | docs/01-plan/features/proposal-platform-v2.plan.md | | 구현 순서 | Phase A → B → C → D |
- **섹션 컨텍스트 주입 (phase_executor 수정):** ```python phase_executor._build_context() 에 추가 if proposal.section_ids: sections = await get_sections(proposal.section_ids) context += "\n\n## 우리 회사 참고 자료\n" for s in sections: context += f"\n### {s.title}\n{s.content}\n" ```
- ```sql -- 섹션 라이브러리 CREATE TABLE sections ( id          UUID PRIMARY KEY DEFAULT gen_random_uuid(), team_id     UUID REFERENCES teams(id) ON DELETE CASCADE, owner_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE, title       TEXT NOT NULL, category    TEXT NOT NULL CHECK (category IN…
- ``` GET    /api/resources/sections    목록 (category, q, scope 필터) POST   /api/resources/sections    생성 PUT    /api/resources/sections/{id}    수정 DELETE /api/resources/sections/{id}   삭제
