# Plan: 프롬프트 강화 (prompt-enhancement) & 4. 변경 계획 (YAGNI 검토 후)
Cohesion: 0.14 | Nodes: 15

## Key Nodes
- **Plan: 프롬프트 강화 (prompt-enhancement)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-yagni]]
  - -> contains -> [[5-yagni]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **4. 변경 계획 (YAGNI 검토 후)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 4 connections
  - -> contains -> [[phase-3-user-3]]
  - -> contains -> [[phase-4-system-3]]
  - -> contains -> [[phase-5-user-3]]
  - <- contains <- [[plan-prompt-enhancement]]
- **5. YAGNI 검토** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 3 connections
  - -> contains -> [[v1]]
  - -> contains -> [[v2]]
  - <- contains <- [[plan-prompt-enhancement]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 2 connections
  - <- has_code_example <- [[phase-3-user-3]]
  - <- has_code_example <- [[phase-5-user-3]]
- **Phase 3 USER 프롬프트 — 핵심 3개 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-yagni]]
- **Phase 5 USER 프롬프트 — 3요소 검증 항목 추가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-yagni]]
- **1. 핵심 문제** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **2. 개선 목표** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **3. 현재 프롬프트 구조 분석** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **6. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **7. 작업 목록** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[plan-prompt-enhancement]]
- **Phase 4 SYSTEM 프롬프트 — 3개 섹션 작성 원칙 추가** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[4-yagni]]
- **v1 포함 (필수)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]
- **v2 이후 (보류)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\prompt-enhancement.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]

## Internal Relationships
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> Phase 3 USER 프롬프트 — 핵심 3개 필드 추가 [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> Phase 4 SYSTEM 프롬프트 — 3개 섹션 작성 원칙 추가 [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> Phase 5 USER 프롬프트 — 3요소 검증 항목 추가 [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v1 포함 (필수) [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v2 이후 (보류) [EXTRACTED]
- Phase 3 USER 프롬프트 — 핵심 3개 필드 추가 -> has_code_example -> json [EXTRACTED]
- Phase 5 USER 프롬프트 — 3요소 검증 항목 추가 -> has_code_example -> json [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 1. 핵심 문제 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 2. 개선 목표 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 3. 현재 프롬프트 구조 분석 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 4. 변경 계획 (YAGNI 검토 후) [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 5. YAGNI 검토 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 6. 성공 기준 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 7. 작업 목록 [EXTRACTED]
- Plan: 프롬프트 강화 (prompt-enhancement) -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 프롬프트 강화 (prompt-enhancement), 4. 변경 계획 (YAGNI 검토 후), 5. YAGNI 검토를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 prompt-enhancement.plan.md이다.

### Key Facts
- Phase 3 USER 프롬프트 — 핵심 3개 필드 추가
- v1 포함 (필수) - Phase 3 USER: `alternatives_considered`, `risks_mitigations`, `implementation_checklist` 필드 추가 - Phase 4 SYSTEM: 3개 섹션 작성 원칙 추가 (1~2줄) - Phase 5 USER: 3개 검증 항목 추가
- ```json // 기존 { "differentiation_strategy": [...], "bid_price_strategy": {...} }
- ```json // 기존 { "differentiation_strategy": [...], "bid_price_strategy": {...} }
- ```json "alternatives_quality": "Alternatives Considered의 설득력 평가 (1~2문장)", "risks_coverage": "Risks/Mitigations의 완성도 평가 (1~2문장)", "checklist_specificity": "Implementation Checklist의 구체성 평가 (1~2문장)" ```
