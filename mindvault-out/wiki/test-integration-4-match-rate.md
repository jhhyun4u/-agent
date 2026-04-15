# 통합 테스트 갭 분석 — test-integration & 4. Match Rate 계산
Cohesion: 0.18 | Nodes: 11

## Key Nodes
- **통합 테스트 갭 분석 — test-integration** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 5 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-design-vs-implementation]]
  - -> contains -> [[3]]
  - -> contains -> [[4-match-rate]]
  - -> contains -> [[5]]
- **4. Match Rate 계산** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 4 connections
  - -> contains -> [[v10]]
  - -> contains -> [[v20-act-1]]
  - -> contains -> [[act-1]]
  - <- contains <- [[test-integration]]
- **1. 구현 현황** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 3 connections
  - -> contains -> [[mock-level-1]]
  - -> contains -> [[live-level-2]]
  - <- contains <- [[test-integration]]
- **2. Design vs Implementation 비교** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **3. 갭 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **5. 최종 테스트 결과** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **Act-1에서 해소된 갭** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[4-match-rate]]
- **Live 통합 테스트 (Level 2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[1]]
- **Mock 통합 테스트 (Level 1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[1]]
- **v1.0 (초기)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[4-match-rate]]
- **v2.0 (Act-1 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.analysis.md) -- 1 connections
  - <- contains <- [[4-match-rate]]

## Internal Relationships
- 1. 구현 현황 -> contains -> Mock 통합 테스트 (Level 1) [EXTRACTED]
- 1. 구현 현황 -> contains -> Live 통합 테스트 (Level 2) [EXTRACTED]
- 4. Match Rate 계산 -> contains -> v1.0 (초기) [EXTRACTED]
- 4. Match Rate 계산 -> contains -> v2.0 (Act-1 후) [EXTRACTED]
- 4. Match Rate 계산 -> contains -> Act-1에서 해소된 갭 [EXTRACTED]
- 통합 테스트 갭 분석 — test-integration -> contains -> 1. 구현 현황 [EXTRACTED]
- 통합 테스트 갭 분석 — test-integration -> contains -> 2. Design vs Implementation 비교 [EXTRACTED]
- 통합 테스트 갭 분석 — test-integration -> contains -> 3. 갭 목록 [EXTRACTED]
- 통합 테스트 갭 분석 — test-integration -> contains -> 4. Match Rate 계산 [EXTRACTED]
- 통합 테스트 갭 분석 — test-integration -> contains -> 5. 최종 테스트 결과 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 통합 테스트 갭 분석 — test-integration, 4. Match Rate 계산, 1. 구현 현황를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test-integration.analysis.md이다.

### Key Facts
- - **Feature**: test-integration - **분석일**: 2026-03-26 - **Design 참조**: `docs/02-design/features/test-integration.design.md`
- v1.0 (초기) | 항목 | Design 케이스 | 구현 | 일치 | |------|:---:|:---:|:---:| | 워크플로 | 8 | 7.5 | 7.5 | | DB | 5 | 3.5 | 3.5 | | MCP | 7 | 4 | 4 | | **합계** | **20** | **15** | **15** |
- Mock 통합 테스트 (Level 1)
- | Design 항목 | 구현 | 일치율 | 비고 | |------------|:---:|:---:|------| | WF-01 Happy Path HEAD | 구현 | 100% | | | WF-02 상태 보존 | 구현 | 100% | | | WF-03 No-Go 종료 | 구현 | 100% | | | WF-04 거부 루프 | 구현 | 100% | Design에서 WF-04는 fork/convergence였으나, 다중 interrupt 문제로 rejection loop로 변경 | | WF-05 self_review retry |…
- | ID | 심각도 | 항목 | 설명 | |----|:---:|------|------| | GAP-1 | LOW | WF-04 Fork/Convergence E2E | Design에서 A/B 병렬 분기 + convergence 검증 계획이었으나, LangGraph 다중 interrupt 제약으로 rejection loop로 대체. 향후 `interrupt_before` 옵션 활용 시 구현 가능. | | GAP-2 | LOW | WF-05 그래프 E2E | self_review retry를 그래프 전체 대신 라우팅 함수 단위로…
