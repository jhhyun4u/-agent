# 2. 항목별 Gap 분석 & Gap Analysis: proposal-quality-v2
Cohesion: 0.20 | Nodes: 10

## Key Nodes
- **2. 항목별 Gap 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 6 connections
  - -> contains -> [[g1-phaseschemaspy-phase3artifact-logicmodel]]
  - -> contains -> [[g2-phase3user-sectionplan-2]]
  - -> contains -> [[g3-phase3user-logicmodel-5]]
  - -> contains -> [[g4-phase3user-2]]
  - -> contains -> [[g5-phase4system-logic-model]]
  - <- contains <- [[gap-analysis-proposal-quality-v2]]
- **Gap Analysis: proposal-quality-v2** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-gap]]
  - -> contains -> [[3-match-rate]]
  - -> contains -> [[4]]
- **1. 분석 요약** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-quality-v2]]
- **3. Match Rate 계산** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-quality-v2]]
- **4. 결론** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-quality-v2]]
- **G1: phase_schemas.py — Phase3Artifact `logic_model` 필드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G2: PHASE3_USER — section_plan 2개 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G3: PHASE3_USER — `logic_model` 최상위 필드 + 5개 서브키** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G4: PHASE3_USER — 작성 지침 2줄 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G5: PHASE4_SYSTEM — Logic Model 표 원칙 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v2\proposal-quality-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]

## Internal Relationships
- 2. 항목별 Gap 분석 -> contains -> G1: phase_schemas.py — Phase3Artifact `logic_model` 필드 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G2: PHASE3_USER — section_plan 2개 필드 추가 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G3: PHASE3_USER — `logic_model` 최상위 필드 + 5개 서브키 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G4: PHASE3_USER — 작성 지침 2줄 추가 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G5: PHASE4_SYSTEM — Logic Model 표 원칙 추가 [EXTRACTED]
- Gap Analysis: proposal-quality-v2 -> contains -> 1. 분석 요약 [EXTRACTED]
- Gap Analysis: proposal-quality-v2 -> contains -> 2. 항목별 Gap 분석 [EXTRACTED]
- Gap Analysis: proposal-quality-v2 -> contains -> 3. Match Rate 계산 [EXTRACTED]
- Gap Analysis: proposal-quality-v2 -> contains -> 4. 결론 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 항목별 Gap 분석, Gap Analysis: proposal-quality-v2, 1. 분석 요약를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v2.analysis.md이다.

### Key Facts
- G1: phase_schemas.py — Phase3Artifact `logic_model` 필드
- Design 문서의 모든 변경 항목 완전 일치. Gap 없음. Match Rate **100%**.
- | 카테고리 | 항목 수 | 완전 일치 | 미세 차이 | |---------|---------|----------|----------| | phase_schemas.py | 1 | 1 | 0 | | PHASE3_USER section_plan | 2 | 2 | 0 | | PHASE3_USER logic_model 필드+서브키 | 6 | 6 | 0 | | PHASE3_USER 지침 | 2 | 2 | 0 | | PHASE4_SYSTEM 원칙 | 1 | 1 | 0 | | **합계** | **12** | **12** | **0** |
- 모든 설계 항목 완전 구현. `/pdca report proposal-quality-v2` 진행 가능.
- | 설계 | 구현 | 상태 | |------|------|------| | `logic_model: dict = Field(default_factory=dict, description="사업 논리 모델 ...")` | 구현됨 (`Phase3Artifact.model_fields`에 존재 확인) | ✅ Match |
