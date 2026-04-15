# Design: ppt-enhancement & python
Cohesion: 0.24 | Nodes: 11

## Key Nodes
- **Design: ppt-enhancement** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 5 connections
  - -> contains -> [[fr-01-fr-02-comparisonteam]]
  - -> contains -> [[fr-03-action-title]]
  - -> contains -> [[fr-04]]
  - -> contains -> [[fr-05-os]]
  - -> contains -> [[fr-06-step-2]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 3 connections
  - <- has_code_example <- [[presentationpptxbuilderpy]]
  - <- has_code_example <- [[fr-05-os]]
  - <- has_code_example <- [[fr-06-step-2]]
- **FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 3 connections
  - -> contains -> [[storyboarduser-json]]
  - -> contains -> [[storyboardsystem]]
  - <- contains <- [[design-ppt-enhancement]]
- **FR-03: Action Title 규칙 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 3 connections
  - -> contains -> [[tocsystem]]
  - -> contains -> [[storyboardsystem]]
  - <- contains <- [[design-ppt-enhancement]]
- **FR-04: 슬라이드 번호 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 2 connections
  - -> contains -> [[presentationpptxbuilderpy]]
  - <- contains <- [[design-ppt-enhancement]]
- **FR-05: 파일 경로 OS 독립화** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[design-ppt-enhancement]]
- **FR-06: Step 2 토큰 증가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[design-ppt-enhancement]]
- **설계: `presentation_pptx_builder.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[fr-04]]
- **데이터 출처 지시 추가 (STORYBOARD_SYSTEM)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 2 connections
  - <- contains <- [[fr-01-fr-02-comparisonteam]]
  - <- contains <- [[fr-03-action-title]]
- **설계: `STORYBOARD_USER` 예시 JSON 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 1 connections
  - <- contains <- [[fr-01-fr-02-comparisonteam]]
- **TOC_SYSTEM 마지막에 규칙 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\ppt-enhancement.design.md) -- 1 connections
  - <- contains <- [[fr-03-action-title]]

## Internal Relationships
- Design: ppt-enhancement -> contains -> FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가 [EXTRACTED]
- Design: ppt-enhancement -> contains -> FR-03: Action Title 규칙 추가 [EXTRACTED]
- Design: ppt-enhancement -> contains -> FR-04: 슬라이드 번호 추가 [EXTRACTED]
- Design: ppt-enhancement -> contains -> FR-05: 파일 경로 OS 독립화 [EXTRACTED]
- Design: ppt-enhancement -> contains -> FR-06: Step 2 토큰 증가 [EXTRACTED]
- FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가 -> contains -> 설계: `STORYBOARD_USER` 예시 JSON 추가 [EXTRACTED]
- FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가 -> contains -> 데이터 출처 지시 추가 (STORYBOARD_SYSTEM) [EXTRACTED]
- FR-03: Action Title 규칙 추가 -> contains -> TOC_SYSTEM 마지막에 규칙 추가 [EXTRACTED]
- FR-03: Action Title 규칙 추가 -> contains -> 데이터 출처 지시 추가 (STORYBOARD_SYSTEM) [EXTRACTED]
- FR-04: 슬라이드 번호 추가 -> contains -> 설계: `presentation_pptx_builder.py` [EXTRACTED]
- FR-05: 파일 경로 OS 독립화 -> has_code_example -> python [EXTRACTED]
- FR-06: Step 2 토큰 증가 -> has_code_example -> python [EXTRACTED]
- 설계: `presentation_pptx_builder.py` -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: ppt-enhancement, python, FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 ppt-enhancement.design.md이다.

### Key Facts
- > Plan 참조: `docs/01-plan/features/ppt-enhancement.plan.md`
- ```python def _add_slide_number(slide, num: int): """슬라이드 우측 하단에 페이지 번호 표시 (표지 제외)""" _add_textbox( slide, Inches(12.5), Inches(6.9), Inches(0.6), Inches(0.35), text=str(num), font_size=14, color=COLOR_DARK_TEXT, align=PP_ALIGN.RIGHT, ) ```
- 문제 `STORYBOARD_USER` 프롬프트 예시에 `comparison`과 `team` 레이아웃 JSON 구조가 없어 Claude가 해당 필드(`table`, `team_rows`)를 생성하지 않음 → 항상 bullets fallback
- 문제 슬라이드 제목이 토픽("사업 이해도")으로 생성됨. McKinsey 원칙상 제목은 완결 주장 문장이어야 함.
- 설계: `presentation_pptx_builder.py`
