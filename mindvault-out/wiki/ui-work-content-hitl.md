# 제안 작업 워크플로우 UI 설계 사양 & 중앙: Work Content (HITL 작업 영역)
Cohesion: 0.10 | Nodes: 21

## Key Nodes
- **제안 작업 워크플로우 UI 설계 사양** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5-ui]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **중앙: Work Content (HITL 작업 영역)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 5 connections
  - -> contains -> [[step-0-rfp]]
  - -> contains -> [[step-1-gono-go]]
  - -> contains -> [[step-2]]
  - -> contains -> [[step-3-4]]
  - <- contains <- [[2]]
- **2. 제안 작업 진행 (워크플로우)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 4 connections
  - -> contains -> [[step-nodes]]
  - -> contains -> [[work-content-hitl]]
  - -> contains -> [[ai-suggestions-ai]]
  - <- contains <- [[ui]]
- **6. 반응형 디자인** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 4 connections
  - -> contains -> [[1280px]]
  - -> contains -> [[640px1280px]]
  - -> contains -> [[640px]]
  - <- contains <- [[ui]]
- **4. 기술 구현 방안** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 3 connections
  - -> contains -> [[hitl]]
  - -> contains -> [[step-node]]
  - <- contains <- [[ui]]
- **5. UI 컴포넌트** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 2 connections
  - -> contains -> [[reusable-components]]
  - <- contains <- [[ui]]
- **1. 제안 프로젝트 목록 (테이블 형식)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[ui]]
- **데스크톱 (≥1280px)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[6]]
- **3. 상태 전환 플로우** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[ui]]
- **모바일 (<640px)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[6]]
- **태블릿 (640px~1280px)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[6]]
- **7. 다음 단계** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[ui]]
- **우측: AI Suggestions (AI 제안 패널)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[2]]
- **HITL 상호작용** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[4]]
- **Reusable Components** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[5-ui]]
- **Step 0: RFP 분석** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[work-content-hitl]]
- **Step 1: Go/No-Go** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[work-content-hitl]]
- **Step 2: 전략 수립** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[work-content-hitl]]
- **Step 3-4: 계획/작성** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[work-content-hitl]]
- **Step Node 상태 관리** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[4]]
- **좌측: Step Nodes (단계 노드)** (C:\project\tenopa proposer\-agent-master\frontend\WORKFLOW_DESIGN_SPEC.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 2. 제안 작업 진행 (워크플로우) -> contains -> 좌측: Step Nodes (단계 노드) [EXTRACTED]
- 2. 제안 작업 진행 (워크플로우) -> contains -> 중앙: Work Content (HITL 작업 영역) [EXTRACTED]
- 2. 제안 작업 진행 (워크플로우) -> contains -> 우측: AI Suggestions (AI 제안 패널) [EXTRACTED]
- 4. 기술 구현 방안 -> contains -> HITL 상호작용 [EXTRACTED]
- 4. 기술 구현 방안 -> contains -> Step Node 상태 관리 [EXTRACTED]
- 5. UI 컴포넌트 -> contains -> Reusable Components [EXTRACTED]
- 6. 반응형 디자인 -> contains -> 데스크톱 (≥1280px) [EXTRACTED]
- 6. 반응형 디자인 -> contains -> 태블릿 (640px~1280px) [EXTRACTED]
- 6. 반응형 디자인 -> contains -> 모바일 (<640px) [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 1. 제안 프로젝트 목록 (테이블 형식) [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 2. 제안 작업 진행 (워크플로우) [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 3. 상태 전환 플로우 [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 4. 기술 구현 방안 [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 5. UI 컴포넌트 [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 6. 반응형 디자인 [EXTRACTED]
- 제안 작업 워크플로우 UI 설계 사양 -> contains -> 7. 다음 단계 [EXTRACTED]
- 중앙: Work Content (HITL 작업 영역) -> contains -> Step 0: RFP 분석 [EXTRACTED]
- 중앙: Work Content (HITL 작업 영역) -> contains -> Step 1: Go/No-Go [EXTRACTED]
- 중앙: Work Content (HITL 작업 영역) -> contains -> Step 2: 전략 수립 [EXTRACTED]
- 중앙: Work Content (HITL 작업 영역) -> contains -> Step 3-4: 계획/작성 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 제안 작업 워크플로우 UI 설계 사양, 중앙: Work Content (HITL 작업 영역), 2. 제안 작업 진행 (워크플로우)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 WORKFLOW_DESIGN_SPEC.md이다.

### Key Facts
- 1. 제안 프로젝트 목록 (테이블 형식)
- - 3열 레이아웃 (노드 + 콘텐츠 + AI)
- ``` [대기] → [진행] → [완료] → [제출] → [결과] → [종료] ↓ [중단] ↓ [진행] ```
- - 1열 레이아웃 (노드 탭 + 콘텐츠)
- - 2열 레이아웃 (노드 + 콘텐츠, AI는 스크롤)
