# Workflow UX 개선 계획서 & 2. 구현 범위 (5개 영역)
Cohesion: 0.15 | Nodes: 14

## Key Nodes
- **Workflow UX 개선 계획서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-5]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **2. 구현 범위 (5개 영역)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 6 connections
  - -> contains -> [[2-1]]
  - -> contains -> [[2-2]]
  - -> contains -> [[2-3-step]]
  - -> contains -> [[2-4-ui]]
  - -> contains -> [[2-5]]
  - <- contains <- [[workflow-ux]]
- **4. 신규/수정 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 4 connections
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - <- contains <- [[workflow-ux]]
  - <- contains <- [[4]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 2 connections
  - -> contains -> [[api]]
  - <- contains <- [[workflow-ux]]
- **3. 구현 우선순위 및 의존성** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 2 connections
  - <- contains <- [[workflow-ux]]
  - <- contains <- [[4]]
- **2-1. 세부 진행 표시 (실시간 노드 로그)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[2-5]]
- **2-2. 중단/재개 버튼** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[2-5]]
- **2-3. STEP별 산출물 뷰어** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[2-5]]
- **2-4. 타임트래블 UI** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[2-5]]
- **2-5. 실시간 로그 패널** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[2-5]]
- **5. 기존 재사용 자산** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[workflow-ux]]
- **6. 검증 방법** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[workflow-ux]]
- **7. 비기능 요구사항** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[workflow-ux]]
- **핵심 사실: 백엔드 API는 이미 전부 구현되어 있음** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\workflow-ux.plan.md) -- 1 connections
  - <- contains <- [[1]]

## Internal Relationships
- 1. 배경 및 목적 -> contains -> 핵심 사실: 백엔드 API는 이미 전부 구현되어 있음 [EXTRACTED]
- 2. 구현 범위 (5개 영역) -> contains -> 2-1. 세부 진행 표시 (실시간 노드 로그) [EXTRACTED]
- 2. 구현 범위 (5개 영역) -> contains -> 2-2. 중단/재개 버튼 [EXTRACTED]
- 2. 구현 범위 (5개 영역) -> contains -> 2-3. STEP별 산출물 뷰어 [EXTRACTED]
- 2. 구현 범위 (5개 영역) -> contains -> 2-4. 타임트래블 UI [EXTRACTED]
- 2. 구현 범위 (5개 영역) -> contains -> 2-5. 실시간 로그 패널 [EXTRACTED]
- 4. 신규/수정 파일 목록 -> contains -> 3. 구현 우선순위 및 의존성 [EXTRACTED]
- 4. 신규/수정 파일 목록 -> contains -> 4. 신규/수정 파일 목록 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 2. 구현 범위 (5개 영역) [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 3. 구현 우선순위 및 의존성 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 4. 신규/수정 파일 목록 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 5. 기존 재사용 자산 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 6. 검증 방법 [EXTRACTED]
- Workflow UX 개선 계획서 -> contains -> 7. 비기능 요구사항 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Workflow UX 개선 계획서, 2. 구현 범위 (5개 영역), 4. 신규/수정 파일 목록를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 workflow-ux.plan.md이다.

### Key Facts
- > STEP 0~5 워크플로 진행 과정의 실시간 가시성, 중간 개입, 산출물 검토 기능 구현
- 2-1. 세부 진행 표시 (실시간 노드 로그)
- 신규 파일 (3개) | 파일 | 용도 | |------|------| | `frontend/lib/hooks/useWorkflowStream.ts` | SSE 실시간 스트림 훅 | | `frontend/components/StepArtifactViewer.tsx` | STEP별 산출물 렌더러 | | `frontend/components/WorkflowLogPanel.tsx` | 하단 실시간 로그 패널 |
- 현재 문제점 - **"처리 중" 화면이 텅 빔**: 스피너 + "Phase N/5" + 경과 시간만 표시, 어떤 노드가 실행 중인지 알 수 없음 - **중단/재개 불가**: `ai-abort`, `ai-retry` API는 있으나 UI 버튼 없음 - **STEP별 산출물 미노출**: `artifacts/{step}` API는 있으나 뷰어 UI 없음 - **타임트래블 접근 불가**: `goto/{step}` API는 있으나 UI 없음 - **SSE 미활용**: `stream` API로 실시간 이벤트를 받을 수 있으나, 5초 HTTP…
- ``` Phase A (핵심): 2-1 세부 진행 + 2-2 중단/재개 → SSE 훅 기반, 즉시 체감 가능한 UX 개선 → 의존성 없음
