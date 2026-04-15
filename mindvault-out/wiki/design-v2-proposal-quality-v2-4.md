# Design: 제안서 품질 강화 v2 (proposal-quality-v2) & 4. 변경 전후 비교
Cohesion: 0.13 | Nodes: 18

## Key Nodes
- **Design: 제안서 품질 강화 v2 (proposal-quality-v2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-phaseschemaspy]]
  - -> contains -> [[3-phasepromptspy]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **4. 변경 전후 비교** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 5 connections
  - -> contains -> [[phase3artifact]]
  - -> contains -> [[phase3user-sectionplan]]
  - -> contains -> [[phase3user]]
  - -> contains -> [[phase4system]]
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 4 connections
  - <- has_code_example <- [[phase3artifact-logicmodel]]
  - <- has_code_example <- [[3-1-phase3user-sectionplan-2]]
  - <- has_code_example <- [[3-2-phase3user-logicmodel]]
  - <- has_code_example <- [[3-3-phase4system-logic-model]]
- **3. phase_prompts.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 4 connections
  - -> contains -> [[3-1-phase3user-sectionplan-2]]
  - -> contains -> [[3-2-phase3user-logicmodel]]
  - -> contains -> [[3-3-phase4system-logic-model]]
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **2. phase_schemas.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 2 connections
  - -> contains -> [[phase3artifact-logicmodel]]
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **3-1. PHASE3_USER — section_plan 항목에 2개 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phasepromptspy]]
- **3-2. PHASE3_USER — `logic_model` 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phasepromptspy]]
- **3-3. PHASE4_SYSTEM — Logic Model 표 원칙 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phasepromptspy]]
- **Phase3Artifact — `logic_model` 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phaseschemaspy]]
- **1. 변경 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **5. 토큰 영향 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **6. 하위 호환성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **7. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[design-v2-proposal-quality-v2]]
- **PHASE3_USER 최상위 필드 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[4]]
- **PHASE3_USER section_plan 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase3Artifact 필드 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[4]]
- **PHASE4_SYSTEM 원칙 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.design.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 2. phase_schemas.py 변경 설계 -> contains -> Phase3Artifact — `logic_model` 필드 추가 [EXTRACTED]
- 3-1. PHASE3_USER — section_plan 항목에 2개 필드 추가 -> has_code_example -> python [EXTRACTED]
- 3-2. PHASE3_USER — `logic_model` 필드 추가 -> has_code_example -> python [EXTRACTED]
- 3-3. PHASE4_SYSTEM — Logic Model 표 원칙 추가 -> has_code_example -> python [EXTRACTED]
- 3. phase_prompts.py 변경 설계 -> contains -> 3-1. PHASE3_USER — section_plan 항목에 2개 필드 추가 [EXTRACTED]
- 3. phase_prompts.py 변경 설계 -> contains -> 3-2. PHASE3_USER — `logic_model` 필드 추가 [EXTRACTED]
- 3. phase_prompts.py 변경 설계 -> contains -> 3-3. PHASE4_SYSTEM — Logic Model 표 원칙 추가 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> Phase3Artifact 필드 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE3_USER section_plan 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE3_USER 최상위 필드 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE4_SYSTEM 원칙 변화 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 1. 변경 파일 목록 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 2. phase_schemas.py 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 3. phase_prompts.py 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 4. 변경 전후 비교 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 5. 토큰 영향 분석 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 6. 하위 호환성 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 7. 구현 순서 [EXTRACTED]
- Design: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 8. 성공 기준 [EXTRACTED]
- Phase3Artifact — `logic_model` 필드 추가 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: 제안서 품질 강화 v2 (proposal-quality-v2), 4. 변경 전후 비교, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v2.design.md이다.

### Key Facts
- ```python logic_model: dict = Field( default_factory=dict, description="사업 논리 모델 (inputs→activities→outputs→단기성과→장기성과)" ) ```
- 3-1. PHASE3_USER — section_plan 항목에 2개 필드 추가
- Phase3Artifact — `logic_model` 필드 추가
- **추가 위치:** line 126 `"win_theme_alignment"` 값 바로 다음 줄 (line 127 `}}` 앞)
- **추가 위치:** line 169 `implementation_checklist` 배열 닫는 `}}` 다음 줄, 최종 `}}` 바로 앞
