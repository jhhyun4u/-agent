# 2. 항목별 Gap 분석 & Gap Analysis: prompt-enhancement
Cohesion: 0.20 | Nodes: 10

## Key Nodes
- **2. 항목별 Gap 분석** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 6 connections
  - -> contains -> [[g1-phaseschemaspy-phase3artifact-3]]
  - -> contains -> [[g2-phaseschemaspy-phase5artifact-3]]
  - -> contains -> [[g3-phase3user-json-3]]
  - -> contains -> [[g4-phase4system-3]]
  - -> contains -> [[g5-phase5user-3-minor-gap]]
  - <- contains <- [[gap-analysis-prompt-enhancement]]
- **Gap Analysis: prompt-enhancement** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-gap]]
  - -> contains -> [[3-match-rate]]
  - -> contains -> [[4]]
- **1. 분석 요약** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-prompt-enhancement]]
- **3. Match Rate 계산** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-prompt-enhancement]]
- **4. 결론** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-prompt-enhancement]]
- **G1: phase_schemas.py — Phase3Artifact 3개 필드** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G2: phase_schemas.py — Phase5Artifact 3개 필드** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G3: PHASE3_USER — JSON 스키마 3개 필드** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G4: PHASE4_SYSTEM — 작성 원칙 3개** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]
- **G5: PHASE5_USER — 검증 필드 3개 순서 (Minor Gap)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\prompt-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[2-gap]]

## Internal Relationships
- 2. 항목별 Gap 분석 -> contains -> G1: phase_schemas.py — Phase3Artifact 3개 필드 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G2: phase_schemas.py — Phase5Artifact 3개 필드 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G3: PHASE3_USER — JSON 스키마 3개 필드 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G4: PHASE4_SYSTEM — 작성 원칙 3개 [EXTRACTED]
- 2. 항목별 Gap 분석 -> contains -> G5: PHASE5_USER — 검증 필드 3개 순서 (Minor Gap) [EXTRACTED]
- Gap Analysis: prompt-enhancement -> contains -> 1. 분석 요약 [EXTRACTED]
- Gap Analysis: prompt-enhancement -> contains -> 2. 항목별 Gap 분석 [EXTRACTED]
- Gap Analysis: prompt-enhancement -> contains -> 3. Match Rate 계산 [EXTRACTED]
- Gap Analysis: prompt-enhancement -> contains -> 4. 결론 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 항목별 Gap 분석, Gap Analysis: prompt-enhancement, 1. 분석 요약를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 prompt-enhancement.analysis.md이다.

### Key Facts
- G1: phase_schemas.py — Phase3Artifact 3개 필드
- Design 문서의 7개 변경 항목 중 6개 완전 일치, 1개 미세 순서 차이. 기능적 영향 없음 — Match Rate **97%**.
- | 카테고리 | 항목 수 | 완전 일치 | 미세 차이 | |---------|---------|----------|----------| | phase_schemas.py | 6 | 6 | 0 | | PHASE3_USER JSON | 3 | 3 | 0 | | PHASE3_USER 지침 | 3 | 3 | 0 | | PHASE4_SYSTEM 원칙 | 3 | 3 | 0 | | PHASE5_USER 필드 | 3 | 2 | 1 (순서) | | **합계** | **18** | **17** | **1** |
- - 모든 핵심 기능 요구사항 충족 - G5 순서 차이는 기능적 영향 없음 (프롬프트 내 JSON 예시 순서는 Claude 출력 순서에 영향 미미) - `/pdca report prompt-enhancement` 진행 가능
- | 설계 | 구현 | 상태 | |------|------|------| | `alternatives_considered: list[dict]`, `default_factory=list` | 구현됨 (line 74) | ✅ Match | | `risks_mitigations: list[dict]`, `default_factory=list` | 구현됨 (line 78) | ✅ Match | | `implementation_checklist: list[dict]`, `default_factory=list` | 구현됨 (line 82)…
