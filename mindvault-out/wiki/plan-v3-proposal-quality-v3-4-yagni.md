# Plan: 제안서 품질 강화 v3 (proposal-quality-v3) & 4. 변경 계획 (YAGNI 검토 후)
Cohesion: 0.11 | Nodes: 19

## Key Nodes
- **Plan: 제안서 품질 강화 v3 (proposal-quality-v3)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-yagni]]
  - -> contains -> [[5-yagni]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **4. 변경 계획 (YAGNI 검토 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 4 connections
  - -> contains -> [[4-1-assertion-based-section-titles]]
  - -> contains -> [[4-2-narrative-arc]]
  - -> contains -> [[4-3-objection-handling]]
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **3. 현재 구조 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 3 connections
  - -> contains -> [[phase4system-line-197-206]]
  - -> contains -> [[phase3artifact]]
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **4-3. Objection Handling (반론 선제 대응)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 3 connections
  - -> has_code_example -> [[python]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-yagni]]
- **5. YAGNI 검토** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 3 connections
  - -> contains -> [[v3]]
  - -> contains -> [[v4]]
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- has_code_example <- [[4-3-objection-handling]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- has_code_example <- [[4-3-objection-handling]]
- **1. 핵심 문제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **2. 개선 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **4-1. Assertion-based Section Titles** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[4-yagni]]
- **4-2. Narrative Arc (스토리텔링 구조)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[4-yagni]]
- **6. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **7. 토큰 영향 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **8. 변경 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **9. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[plan-v3-proposal-quality-v3]]
- **Phase3Artifact 현재 필드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **PHASE4_SYSTEM 현재 원칙 (line 197-206)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **v3 포함 (필수)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]
- **v4 이후 (보류)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v3\proposal-quality-v3.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]

## Internal Relationships
- 3. 현재 구조 분석 -> contains -> PHASE4_SYSTEM 현재 원칙 (line 197-206) [EXTRACTED]
- 3. 현재 구조 분석 -> contains -> Phase3Artifact 현재 필드 [EXTRACTED]
- 4-3. Objection Handling (반론 선제 대응) -> has_code_example -> python [EXTRACTED]
- 4-3. Objection Handling (반론 선제 대응) -> has_code_example -> json [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> 4-1. Assertion-based Section Titles [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> 4-2. Narrative Arc (스토리텔링 구조) [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> 4-3. Objection Handling (반론 선제 대응) [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v3 포함 (필수) [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v4 이후 (보류) [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 1. 핵심 문제 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 2. 개선 목표 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 3. 현재 구조 분석 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 4. 변경 계획 (YAGNI 검토 후) [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 5. YAGNI 검토 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 6. 성공 기준 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 7. 토큰 영향 분석 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 8. 변경 파일 목록 [EXTRACTED]
- Plan: 제안서 품질 강화 v3 (proposal-quality-v3) -> contains -> 9. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 제안서 품질 강화 v3 (proposal-quality-v3), 4. 변경 계획 (YAGNI 검토 후), 3. 현재 구조 분석를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v3.plan.md이다.

### Key Facts
- 4-1. Assertion-based Section Titles
- PHASE4_SYSTEM 현재 원칙 (line 197-206)
- **Phase3Artifact 추가 필드:** ```python objection_responses: list[dict] = Field( default_factory=list, description="평가위원 예상 반론 및 선제 대응 (objection/acknowledge/response/evidence)" ) ```
- v3 포함 (필수) - PHASE4_SYSTEM: Assertion Title 원칙 1줄 - PHASE4_SYSTEM: Narrative Arc 원칙 1줄 - Phase3Artifact: `objection_responses` 필드 추가 - PHASE3_USER: `objection_responses` JSON 스키마 + 지침 - PHASE4_SYSTEM: Objection Handling 원칙 1줄
- **PHASE3_USER JSON 추가 필드** (`logic_model` 다음): ```json "objection_responses": [ { "objection": "평가위원이 가질 수 있는 예상 반론 (구체적, 예: '경험 부족')", "acknowledge": "이 우려가 타당한 이유를 인정하는 표현 (1문장)", "response": "우리의 대응 논리 (Challenger 방식: 새로운 관점 제시)", "evidence": "정량 근거 1~2개 (수치, 사례, 레퍼런스)" } ] ```
