# Design: 프롬프트 강화 (prompt-enhancement) & python
Cohesion: 0.15 | Nodes: 17

## Key Nodes
- **Design: 프롬프트 강화 (prompt-enhancement)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-phasepromptspy]]
  - -> contains -> [[3-phaseschemaspy]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 5 connections
  - <- has_code_example <- [[2-1-phase3user-json-3]]
  - <- has_code_example <- [[2-2-phase4system-3]]
  - <- has_code_example <- [[2-3-phase5user-json-3]]
  - <- has_code_example <- [[3-1-phase3artifact-3]]
  - <- has_code_example <- [[3-2-phase5artifact-3]]
- **2. phase_prompts.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 4 connections
  - -> contains -> [[2-1-phase3user-json-3]]
  - -> contains -> [[2-2-phase4system-3]]
  - -> contains -> [[2-3-phase5user-json-3]]
  - <- contains <- [[design-prompt-enhancement]]
- **3. phase_schemas.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 3 connections
  - -> contains -> [[3-1-phase3artifact-3]]
  - -> contains -> [[3-2-phase5artifact-3]]
  - <- contains <- [[design-prompt-enhancement]]
- **4. 변경 전후 비교** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 3 connections
  - -> contains -> [[phase3-json]]
  - -> contains -> [[phase5-json]]
  - <- contains <- [[design-prompt-enhancement]]
- **2-1. PHASE3_USER — JSON 스키마 끝에 3개 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phasepromptspy]]
- **2-2. PHASE4_SYSTEM — 작성 원칙 3개 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phasepromptspy]]
- **2-3. PHASE5_USER — JSON 스키마에 3개 검증 항목 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phasepromptspy]]
- **3-1. Phase3Artifact — 3개 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phaseschemaspy]]
- **3-2. Phase5Artifact — 3개 검증 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phaseschemaspy]]
- **1. 변경 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[design-prompt-enhancement]]
- **5. 토큰 영향 분석** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[design-prompt-enhancement]]
- **6. 하위 호환성** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[design-prompt-enhancement]]
- **7. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[design-prompt-enhancement]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[design-prompt-enhancement]]
- **Phase3 JSON 스키마 변경** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase5 JSON 스키마 변경** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\prompt-enhancement.design.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 2-1. PHASE3_USER — JSON 스키마 끝에 3개 필드 추가 -> has_code_example -> python [EXTRACTED]
- 2-2. PHASE4_SYSTEM — 작성 원칙 3개 추가 -> has_code_example -> python [EXTRACTED]
- 2-3. PHASE5_USER — JSON 스키마에 3개 검증 항목 추가 -> has_code_example -> python [EXTRACTED]
- 2. phase_prompts.py 변경 설계 -> contains -> 2-1. PHASE3_USER — JSON 스키마 끝에 3개 필드 추가 [EXTRACTED]
- 2. phase_prompts.py 변경 설계 -> contains -> 2-2. PHASE4_SYSTEM — 작성 원칙 3개 추가 [EXTRACTED]
- 2. phase_prompts.py 변경 설계 -> contains -> 2-3. PHASE5_USER — JSON 스키마에 3개 검증 항목 추가 [EXTRACTED]
- 3-1. Phase3Artifact — 3개 필드 추가 -> has_code_example -> python [EXTRACTED]
- 3-2. Phase5Artifact — 3개 검증 필드 추가 -> has_code_example -> python [EXTRACTED]
- 3. phase_schemas.py 변경 설계 -> contains -> 3-1. Phase3Artifact — 3개 필드 추가 [EXTRACTED]
- 3. phase_schemas.py 변경 설계 -> contains -> 3-2. Phase5Artifact — 3개 검증 필드 추가 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> Phase3 JSON 스키마 변경 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> Phase5 JSON 스키마 변경 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 1. 변경 파일 목록 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 2. phase_prompts.py 변경 설계 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 3. phase_schemas.py 변경 설계 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 4. 변경 전후 비교 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 5. 토큰 영향 분석 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 6. 하위 호환성 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 7. 구현 순서 [EXTRACTED]
- Design: 프롬프트 강화 (prompt-enhancement) -> contains -> 8. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: 프롬프트 강화 (prompt-enhancement), python, 2. phase_prompts.py 변경 설계를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 prompt-enhancement.design.md이다.

### Key Facts
- ```python "alternatives_considered": [ {{ "approach": "일반적 접근법 또는 경쟁사가 취할 방식 (구체적으로)", "our_approach": "우리가 선택한 접근법", "why_better": "우리 접근법이 우월한 이유 (정량 근거 또는 사례 포함)" }} ], "risks_mitigations": [ {{ "risk": "리스크 설명 (구체적)", "probability": "high/medium/low", "impact": "high/medium/low", "mitigation":…
- 2-1. PHASE3_USER — JSON 스키마 끝에 3개 필드 추가
- 3-1. Phase3Artifact — 3개 필드 추가
- **추가 위치:** 기존 `"bid_price_strategy"` 필드 바로 다음
- **추가 위치:** 기존 마지막 원칙("경쟁사를 직접 언급하지 않되...") 다음 줄
