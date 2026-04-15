# Design: 제안서 품질 강화 v3 (proposal-quality-v3) & 4. 변경 전후 비교
Cohesion: 0.14 | Nodes: 16

## Key Nodes
- **Design: 제안서 품질 강화 v3 (proposal-quality-v3)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-phaseschemaspy]]
  - -> contains -> [[3-phasepromptspy]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **4. 변경 전후 비교** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 4 connections
  - -> contains -> [[phase3artifact]]
  - -> contains -> [[phase3user]]
  - -> contains -> [[phase4system]]
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 3 connections
  - <- has_code_example <- [[phase3artifact-objectionresponses]]
  - <- has_code_example <- [[3-1-phase3user-objectionresponses]]
  - <- has_code_example <- [[3-2-phase4system-3]]
- **3. phase_prompts.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 3 connections
  - -> contains -> [[3-1-phase3user-objectionresponses]]
  - -> contains -> [[3-2-phase4system-3]]
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **2. phase_schemas.py 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 2 connections
  - -> contains -> [[phase3artifact-objectionresponses]]
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **3-1. PHASE3_USER — `objection_responses` 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phasepromptspy]]
- **3-2. PHASE4_SYSTEM — 원칙 3줄 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-phasepromptspy]]
- **Phase3Artifact — `objection_responses` 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phaseschemaspy]]
- **1. 변경 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **5. 토큰 영향 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **6. 하위 호환성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **7. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[design-v3-proposal-quality-v3]]
- **PHASE3_USER 최상위 필드 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase3Artifact 필드 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[4]]
- **PHASE4_SYSTEM 원칙 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.design.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 2. phase_schemas.py 변경 설계 -> contains -> Phase3Artifact — `objection_responses` 필드 추가 [EXTRACTED]
- 3-1. PHASE3_USER — `objection_responses` 필드 추가 -> has_code_example -> python [EXTRACTED]
- 3-2. PHASE4_SYSTEM — 원칙 3줄 추가 -> has_code_example -> python [EXTRACTED]
- 3. phase_prompts.py 변경 설계 -> contains -> 3-1. PHASE3_USER — `objection_responses` 필드 추가 [EXTRACTED]
- 3. phase_prompts.py 변경 설계 -> contains -> 3-2. PHASE4_SYSTEM — 원칙 3줄 추가 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> Phase3Artifact 필드 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE3_USER 최상위 필드 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE4_SYSTEM 원칙 변화 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 1. 변경 파일 목록 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 2. phase_schemas.py 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 3. phase_prompts.py 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 4. 변경 전후 비교 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 5. 토큰 영향 분석 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 6. 하위 호환성 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 7. 구현 순서 [EXTRACTED]
- Design: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 8. 성공 기준 [EXTRACTED]
- Phase3Artifact — `objection_responses` 필드 추가 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: 제안서 품질 강화 v3 (proposal-quality-v3), 4. 변경 전후 비교, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v3.design.md이다.

### Key Facts
- ```python objection_responses: list[dict] = Field( default_factory=list, description="평가위원 예상 반론 및 선제 대응 (objection/acknowledge/response/evidence)" ) ```
- 3-1. PHASE3_USER — `objection_responses` 필드 추가
- Phase3Artifact — `objection_responses` 필드 추가
- **추가 위치:** `logic_model` 닫는 `}}` 다음, 최종 `}}` 앞
- **추가 위치:** line 206 `Logic Model 표` 원칙 다음
