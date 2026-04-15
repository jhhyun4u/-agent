# Plan: ppt-enhancement & FR-01: comparison 레이아웃 프롬프트 수정
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **Plan: ppt-enhancement** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 6 connections
  - -> contains -> [[fr-01-comparison]]
  - -> contains -> [[fr-02-team]]
  - -> contains -> [[fr-03-action-title]]
  - -> contains -> [[fr-04]]
  - -> contains -> [[fr-05-os]]
  - -> contains -> [[fr-06-step-2]]
- **FR-01: comparison 레이아웃 프롬프트 수정** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]
- **FR-02: team 레이아웃 프롬프트 수정** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]
- **FR-03: Action Title 규칙 추가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]
- **FR-04: 슬라이드 번호 추가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]
- **FR-05: 파일 경로 OS 독립화** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]
- **FR-06: Step 2 토큰 증가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\ppt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-ppt-enhancement]]

## Internal Relationships
- Plan: ppt-enhancement -> contains -> FR-01: comparison 레이아웃 프롬프트 수정 [EXTRACTED]
- Plan: ppt-enhancement -> contains -> FR-02: team 레이아웃 프롬프트 수정 [EXTRACTED]
- Plan: ppt-enhancement -> contains -> FR-03: Action Title 규칙 추가 [EXTRACTED]
- Plan: ppt-enhancement -> contains -> FR-04: 슬라이드 번호 추가 [EXTRACTED]
- Plan: ppt-enhancement -> contains -> FR-05: 파일 경로 OS 독립화 [EXTRACTED]
- Plan: ppt-enhancement -> contains -> FR-06: Step 2 토큰 증가 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: ppt-enhancement, FR-01: comparison 레이아웃 프롬프트 수정, FR-02: team 레이아웃 프롬프트 수정를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 ppt-enhancement.plan.md이다.

### Key Facts
- FR-02: team 레이아웃 프롬프트 수정 - STORYBOARD_USER 예시에 `team` 슬라이드 JSON 구조 추가 - 필드: `team_rows: [{role, grade, duration, task}]` 형식 - Claude가 `team_plan`에서 인력 데이터를 추출하도록 지시
- FR-03: Action Title 규칙 추가 - TOC_SYSTEM에 "슬라이드 제목은 완결된 주장 문장(assertion)으로 작성"하는 규칙 추가 - STORYBOARD_SYSTEM에 "title은 TOC의 assertion title 그대로" 규칙 유지 - 예: "사업 이해도" → "당사는 현장 5년 경험으로 발주처 핵심 요구사항을 정확히 이해함"
- FR-04: 슬라이드 번호 추가 - `presentation_pptx_builder.py`에 `_add_slide_number(slide, num)` 헬퍼 추가 - 위치: 슬라이드 우측 하단 (Inches 12.5, 6.9) - 스타일: 14pt, COLOR_DARK_TEXT, 표지(cover)는 제외
- FR-05: 파일 경로 OS 독립화 - `routes_presentation.py`의 `/tmp/{id}/presentation.pptx`를 `tempfile.gettempdir()` 또는 `settings`의 `output_dir` 설정값으로 교체
- FR-06: Step 2 토큰 증가 - `generate_presentation_slides()`의 Step 2 `max_tokens` 6,000 → 8,192
