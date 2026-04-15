# 🔌 API 호출 흐름 & 📊 ARTIFACT_VERSION 통합 설계
Cohesion: 0.14 | Nodes: 18

## Key Nodes
- **🔌 API 호출 흐름** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 9 connections
  - -> contains -> [[detailcenterpanel]]
  - -> contains -> [[ui]]
  - -> contains -> [[api]]
  - -> contains -> [[ux]]
  - -> contains -> [[phase-1]]
  - -> contains -> [[phase-2-ux]]
  - -> contains -> [[phase-3]]
  - <- contains <- [[artifactversion-ui]]
  - <- contains <- [[api]]
- **📊 ARTIFACT_VERSION 통합 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 5 connections
  - -> contains -> [[1-versionselectionmodal]]
  - -> contains -> [[2-ui-phasegraph]]
  - -> contains -> [[3-detailrightpanel]]
  - -> contains -> [[4-artifactversionpanel]]
  - <- contains <- [[artifactversion-ui]]
- **ARTIFACT_VERSION UI 통합 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 4 connections
  - -> contains -> [[3-panel]]
  - -> contains -> [[artifactversion]]
  - -> contains -> [[ui]]
  - -> contains -> [[api]]
- **🎨 UI 배치 시뮬레이션** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 4 connections
  - -> contains -> [[1-phasegraph]]
  - -> contains -> [[2-workflowpanel]]
  - <- contains <- [[artifactversion-ui]]
  - <- contains <- [[api]]
- **tsx** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 3 connections
  - <- has_code_example <- [[1-versionselectionmodal]]
  - <- has_code_example <- [[2-ui-phasegraph]]
  - <- has_code_example <- [[3-detailrightpanel]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - <- has_code_example <- [[4-artifactversionpanel]]
  - <- has_code_example <- [[detailcenterpanel]]
- **1️⃣ VersionSelectionModal의 배치** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[artifactversion]]
- **2️⃣ 노드 이동 UI (PhaseGraph 강화)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[artifactversion]]
- **3️⃣ DetailRightPanel의 "버전" 탭 강화** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[artifactversion]]
- **4️⃣ ArtifactVersionPanel (신규 컴포넌트)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[artifactversion]]
- **DetailCenterPanel 에서 노드 이동 시** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[api]]
- **노드 이동 시나리오 1: PhaseGraph에서 이동** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[ui]]
- **노드 이동 시나리오 2: WorkflowPanel에서 이동** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[ui]]
- **현재 3-Panel 구조** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[artifactversion-ui]]
- **Phase 1: 핵심 기능 (필수)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[api]]
- **Phase 2: UX 개선 (권장)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[api]]
- **Phase 3: 고급 기능 (선택)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[api]]
- **UX 검증** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-ui-integration.design.md) -- 1 connections
  - <- contains <- [[api]]

## Internal Relationships
- 1️⃣ VersionSelectionModal의 배치 -> has_code_example -> tsx [EXTRACTED]
- 2️⃣ 노드 이동 UI (PhaseGraph 강화) -> has_code_example -> tsx [EXTRACTED]
- 3️⃣ DetailRightPanel의 "버전" 탭 강화 -> has_code_example -> tsx [EXTRACTED]
- 4️⃣ ArtifactVersionPanel (신규 컴포넌트) -> has_code_example -> typescript [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> DetailCenterPanel 에서 노드 이동 시 [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> 🎨 UI 배치 시뮬레이션 [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> 🔌 API 호출 흐름 [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> UX 검증 [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> Phase 1: 핵심 기능 (필수) [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> Phase 2: UX 개선 (권장) [EXTRACTED]
- 🔌 API 호출 흐름 -> contains -> Phase 3: 고급 기능 (선택) [EXTRACTED]
- 📊 ARTIFACT_VERSION 통합 설계 -> contains -> 1️⃣ VersionSelectionModal의 배치 [EXTRACTED]
- 📊 ARTIFACT_VERSION 통합 설계 -> contains -> 2️⃣ 노드 이동 UI (PhaseGraph 강화) [EXTRACTED]
- 📊 ARTIFACT_VERSION 통합 설계 -> contains -> 3️⃣ DetailRightPanel의 "버전" 탭 강화 [EXTRACTED]
- 📊 ARTIFACT_VERSION 통합 설계 -> contains -> 4️⃣ ArtifactVersionPanel (신규 컴포넌트) [EXTRACTED]
- ARTIFACT_VERSION UI 통합 설계 -> contains -> 현재 3-Panel 구조 [EXTRACTED]
- ARTIFACT_VERSION UI 통합 설계 -> contains -> 📊 ARTIFACT_VERSION 통합 설계 [EXTRACTED]
- ARTIFACT_VERSION UI 통합 설계 -> contains -> 🎨 UI 배치 시뮬레이션 [EXTRACTED]
- ARTIFACT_VERSION UI 통합 설계 -> contains -> 🔌 API 호출 흐름 [EXTRACTED]
- DetailCenterPanel 에서 노드 이동 시 -> has_code_example -> typescript [EXTRACTED]
- 🎨 UI 배치 시뮬레이션 -> contains -> 노드 이동 시나리오 1: PhaseGraph에서 이동 [EXTRACTED]
- 🎨 UI 배치 시뮬레이션 -> contains -> 노드 이동 시나리오 2: WorkflowPanel에서 이동 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 🔌 API 호출 흐름, 📊 ARTIFACT_VERSION 통합 설계, ARTIFACT_VERSION UI 통합 설계를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 artifact-version-ui-integration.design.md이다.

### Key Facts
- DetailCenterPanel 에서 노드 이동 시
- 1️⃣ VersionSelectionModal의 배치
- > **작성일**: 2026-03-30 > **목표**: ARTIFACT_VERSION System을 기존 3-Panel 레이아웃에 통합 > **범위**: VersionSelectionModal 배치 + 노드 이동 UI + 산출물 버전 표시
- 노드 이동 시나리오 1: PhaseGraph에서 이동
- ```tsx // DetailCenterPanel.tsx
