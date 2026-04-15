# Plan: 제안서 품질 강화 v2 (proposal-quality-v2) & json
Cohesion: 0.13 | Nodes: 17

## Key Nodes
- **Plan: 제안서 품질 강화 v2 (proposal-quality-v2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-yagni]]
  - -> contains -> [[5-yagni]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 3 connections
  - <- has_code_example <- [[sectionplan-phase3user-line-115-128]]
  - <- has_code_example <- [[4-1-sectionplan]]
  - <- has_code_example <- [[4-2-logic-model]]
- **3. 현재 구조 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 3 connections
  - -> contains -> [[sectionplan-phase3user-line-115-128]]
  - -> contains -> [[phase-2-evaluationweights]]
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **4. 변경 계획 (YAGNI 검토 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 3 connections
  - -> contains -> [[4-1-sectionplan]]
  - -> contains -> [[4-2-logic-model]]
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **5. YAGNI 검토** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 3 connections
  - -> contains -> [[v2]]
  - -> contains -> [[v3]]
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **4-1. 평가항목-섹션 매핑 — section_plan 구조 확장** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-yagni]]
- **4-2. Logic Model — 새 최상위 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-yagni]]
- **section_plan 현재 필드 (PHASE3_USER line 115-128)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[3]]
- **1. 핵심 문제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **2. 개선 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **6. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **7. 토큰 영향 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **8. 변경 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **9. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[plan-v2-proposal-quality-v2]]
- **Phase 2 evaluation_weights (이미 생성되는 데이터)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **v2 포함 (필수)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]
- **v3 이후 (보류)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.plan.md) -- 1 connections
  - <- contains <- [[5-yagni]]

## Internal Relationships
- 3. 현재 구조 분석 -> contains -> section_plan 현재 필드 (PHASE3_USER line 115-128) [EXTRACTED]
- 3. 현재 구조 분석 -> contains -> Phase 2 evaluation_weights (이미 생성되는 데이터) [EXTRACTED]
- 4-1. 평가항목-섹션 매핑 — section_plan 구조 확장 -> has_code_example -> json [EXTRACTED]
- 4-2. Logic Model — 새 최상위 필드 추가 -> has_code_example -> json [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> 4-1. 평가항목-섹션 매핑 — section_plan 구조 확장 [EXTRACTED]
- 4. 변경 계획 (YAGNI 검토 후) -> contains -> 4-2. Logic Model — 새 최상위 필드 추가 [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v2 포함 (필수) [EXTRACTED]
- 5. YAGNI 검토 -> contains -> v3 이후 (보류) [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 1. 핵심 문제 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 2. 개선 목표 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 3. 현재 구조 분석 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 4. 변경 계획 (YAGNI 검토 후) [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 5. YAGNI 검토 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 6. 성공 기준 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 7. 토큰 영향 분석 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 8. 변경 파일 목록 [EXTRACTED]
- Plan: 제안서 품질 강화 v2 (proposal-quality-v2) -> contains -> 9. 다음 단계 [EXTRACTED]
- section_plan 현재 필드 (PHASE3_USER line 115-128) -> has_code_example -> json [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 제안서 품질 강화 v2 (proposal-quality-v2), json, 3. 현재 구조 분석를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v2.plan.md이다.

### Key Facts
- ```json { "section": "사업 이해도", "approach": "작성 접근 방법", "page_limit": 5, "priority": "high", "evaluator_check_points": ["확인 항목 1", "확인 항목 2"], "win_theme_alignment": "Win Theme 연결 방식" } ```
- section_plan 현재 필드 (PHASE3_USER line 115-128)
- 4-1. 평가항목-섹션 매핑 — section_plan 구조 확장
- v2 포함 (필수) - section_plan에 `target_criteria`, `score_weight` 추가 - Phase 3에 `logic_model` 최상위 필드 추가 - PHASE4_SYSTEM에 Logic Model 표 원칙 1줄 추가 - Phase3Artifact에 `logic_model: dict` 필드 추가
- **변경 대상:** PHASE3_USER JSON 스키마의 section_plan 항목
