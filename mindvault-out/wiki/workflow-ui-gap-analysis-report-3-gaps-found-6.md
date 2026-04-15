# Workflow UI Gap Analysis Report & 3. Gaps Found (6건)
Cohesion: 0.18 | Nodes: 11

## Key Nodes
- **Workflow UI Gap Analysis Report** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 6 connections
  - -> contains -> [[1-scope]]
  - -> contains -> [[2-scores]]
  - -> contains -> [[3-gaps-found-6]]
  - -> contains -> [[4-added-features-8]]
  - -> contains -> [[5-intentional-changes-3]]
  - -> contains -> [[6-iteration-act-phase-2026-03-25]]
- **3. Gaps Found (6건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 3 connections
  - -> contains -> [[medium-2]]
  - -> contains -> [[low-4]]
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **6. Iteration 결과 (Act Phase, 2026-03-25)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 3 connections
  - -> contains -> [[66]]
  - -> contains -> [[match-rate-97]]
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **1. Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **2. Scores** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **4. Added Features (설계에 없으나 구현됨, 8건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **5. Intentional Changes (3건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[workflow-ui-gap-analysis-report]]
- **해소된 갭 (6/6건 — 전부 수정)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[6-iteration-act-phase-2026-03-25]]
- **LOW (4건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[3-gaps-found-6]]
- **수정 후 Match Rate: **97%**** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[6-iteration-act-phase-2026-03-25]]
- **MEDIUM (2건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\workflow-ui\analysis.md) -- 1 connections
  - <- contains <- [[3-gaps-found-6]]

## Internal Relationships
- 3. Gaps Found (6건) -> contains -> MEDIUM (2건) [EXTRACTED]
- 3. Gaps Found (6건) -> contains -> LOW (4건) [EXTRACTED]
- 6. Iteration 결과 (Act Phase, 2026-03-25) -> contains -> 해소된 갭 (6/6건 — 전부 수정) [EXTRACTED]
- 6. Iteration 결과 (Act Phase, 2026-03-25) -> contains -> 수정 후 Match Rate: **97%** [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 1. Scope [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 2. Scores [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 3. Gaps Found (6건) [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 4. Added Features (설계에 없으나 구현됨, 8건) [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 5. Intentional Changes (3건) [EXTRACTED]
- Workflow UI Gap Analysis Report -> contains -> 6. Iteration 결과 (Act Phase, 2026-03-25) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Workflow UI Gap Analysis Report, 3. Gaps Found (6건), 6. Iteration 결과 (Act Phase, 2026-03-25)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 analysis.md이다.

### Key Facts
- > **Analysis Type**: Gap Analysis (Design vs Implementation) > **Project**: 용역제안 Coworker > **Date**: 2026-03-25 > **Overall Match Rate**: **92%**
- | Component | Design Ref | File | |-----------|-----------|------| | PhaseGraph v4 | §13-1-1 | `frontend/components/PhaseGraph.tsx` | | ArtifactReviewPanel | §13-5 | `frontend/components/ArtifactReviewPanel.tsx` | | DetailRightPanel | §13-5 | `frontend/components/DetailRightPanel.tsx` | |…
- | Category | Score | |----------|:-----:| | PhaseGraph (§13-1-1) | 92% | | ArtifactReviewPanel (§13-5) | 88% | | DetailRightPanel | 95% | | DetailCenterPanel | 90% | | Page Layout + Resizable | 95% | | Convention Compliance | 93% | | **Overall** | **92%** |
- | ID | Feature | Location | |----|---------|----------| | ADD-01 | SVG 원주 진행률 아크 (예상 시간 대비 경과) | PhaseGraph.tsx:99-124 | | ADD-02 | Start 버튼 (다음 대기 단계) | PhaseGraph.tsx:357-364 | | ADD-03 | Finish 배지 (완료 단계) | PhaseGraph.tsx:366-369 | | ADD-04 | Token cost 표시 ($USD) | PhaseGraph.tsx:206-209 | |…
- | ID | 항목 | 설계 | 구현 | 영향 | |----|------|------|------|------| | CHG-01 | Gate 승인 | Gate에서 직접 승인 | WorkflowPanel로 스크롤 | LOW — 승인을 한 곳에서 처리 | | CHG-02 | 리뷰 패널 | 탭 기반 multi-artifact | 단일 artifact 전체 패널 | LOW — Claude Desktop 패턴 | | CHG-03 | 병렬 표시 | 시각적 fan-out 라인 | 플랫 원 + SubNodeList 아코디언 | LOW — 동일…
