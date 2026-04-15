# 1. 문제 진단: 왜 Phase가 필요한가 & 2. 5-Phase 모델 설계
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **1. 문제 진단: 왜 Phase가 필요한가** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 4 connections
  - -> contains -> [[11-v30]]
  - -> contains -> [[12-phase]]
  - -> contains -> [[13-v30-v31]]
  - <- contains <- [[phase-hitl]]
- **2. 5-Phase 모델 설계** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 3 connections
  - -> contains -> [[21-5-phase]]
  - -> contains -> [[22-phase-sub-agent]]
  - <- contains <- [[phase-hitl]]
- **Phase 기반 컨텍스트 관리 및 적응형 HITL 설계안** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 2 connections
  - -> contains -> [[1-phase]]
  - -> contains -> [[2-5-phase]]
- **1.1 v3.0의 컨텍스트 누적 문제** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 1 connections
  - <- contains <- [[1-phase]]
- **1.2 Phase 도입으로 해결** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 1 connections
  - <- contains <- [[1-phase]]
- **1.3 v3.0과 v3.1의 차이** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 1 connections
  - <- contains <- [[1-phase]]
- **2.1 제안서 작성에 매핑한 5-Phase** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 1 connections
  - <- contains <- [[2-5-phase]]
- **2.2 Phase ↔ Sub-agent 매핑** (C:\project\tenopa proposer\-agent-master\docs\PHASE_CONTEXT_MANAGEMENT_v3.1.1.md) -- 1 connections
  - <- contains <- [[2-5-phase]]

## Internal Relationships
- 1. 문제 진단: 왜 Phase가 필요한가 -> contains -> 1.1 v3.0의 컨텍스트 누적 문제 [EXTRACTED]
- 1. 문제 진단: 왜 Phase가 필요한가 -> contains -> 1.2 Phase 도입으로 해결 [EXTRACTED]
- 1. 문제 진단: 왜 Phase가 필요한가 -> contains -> 1.3 v3.0과 v3.1의 차이 [EXTRACTED]
- 2. 5-Phase 모델 설계 -> contains -> 2.1 제안서 작성에 매핑한 5-Phase [EXTRACTED]
- 2. 5-Phase 모델 설계 -> contains -> 2.2 Phase ↔ Sub-agent 매핑 [EXTRACTED]
- Phase 기반 컨텍스트 관리 및 적응형 HITL 설계안 -> contains -> 1. 문제 진단: 왜 Phase가 필요한가 [EXTRACTED]
- Phase 기반 컨텍스트 관리 및 적응형 HITL 설계안 -> contains -> 2. 5-Phase 모델 설계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 1. 문제 진단: 왜 Phase가 필요한가, 2. 5-Phase 모델 설계, Phase 기반 컨텍스트 관리 및 적응형 HITL 설계안를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PHASE_CONTEXT_MANAGEMENT_v3.1.1.md이다.

### Key Facts
- 2.1 제안서 작성에 매핑한 5-Phase
- > **v3.0 → v3.1 → v3.1.1 아키텍처 확장** > 기존 Supervisor + Sub-agent 구조 위에 **5-Phase 컨텍스트 격리** 계층과 > **적응형 HITL 게이트**를 추가하여, 컨텍스트 폭발 문제를 해결하고 > 사람의 개입을 최적화합니다. > > **v3.1.1 보완**: Design Review 13건 (C-1~C-4, M-1~M-5, m-2~m-4) + > Token Efficiency Review 12건 (#1~#11) 반영. > HITL interrupt() 전면 재설계, Phase 5…
- ``` v3.0 현재 흐름 (컨텍스트가 계속 쌓임):
- ``` Phase 기반 흐름 (Phase 경계에서 컨텍스트 압축):
- ``` ┌─────────────────┬──────────────────────┬──────────────────────────────┐ │ 관점            │ v3.0                 │ v3.1 (Phase 기반)            │ ├─────────────────┼──────────────────────┼──────────────────────────────┤ │ 컨텍스트 관리   │ 누적 (State에 전부)  │ Phase별 격리 + Artifact 전달│ │                 │…
