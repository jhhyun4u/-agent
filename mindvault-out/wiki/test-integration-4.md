# 통합 테스트 계획서 — test-integration & 4. 테스트 항목
Cohesion: 0.11 | Nodes: 20

## Key Nodes
- **통합 테스트 계획서 — test-integration** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-mock]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9-out-of-scope]]
- **4. 테스트 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 4 connections
  - -> contains -> [[41-langgraph]]
  - -> contains -> [[42-postgresql]]
  - -> contains -> [[43-mcp]]
  - <- contains <- [[test-integration]]
- **3. 테스트 전략** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 3 connections
  - -> contains -> [[31]]
  - -> contains -> [[32]]
  - <- contains <- [[test-integration]]
- **6. Mock 전략** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 3 connections
  - -> contains -> [[61-mcp-mock]]
  - -> contains -> [[62-mock]]
  - <- contains <- [[test-integration]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 2 connections
  - <- has_code_example <- [[61-mcp-mock]]
  - <- has_code_example <- [[62-mock]]
- **5. 구현 계획** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 2 connections
  - -> contains -> [[pytest-pyprojecttoml]]
  - <- contains <- [[test-integration]]
- **6.1 MCP 도구 Mock 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6-mock]]
- **6.2 에러 시나리오 Mock** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6-mock]]
- **pytest 설정 추가 (pyproject.toml)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 2 connections
  - -> has_code_example -> [[toml]]
  - <- contains <- [[5]]
- **toml** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- has_code_example <- [[pytest-pyprojecttoml]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **2. 현재 테스트 구조 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **3.1 테스트 레벨 분류** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3.2 환경 요구사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **4.1 LangGraph 워크플로 흐름 (강화)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4.2 PostgreSQL 연결** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4.3 MCP 도구 호출** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **8. 리스크 및 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[test-integration]]
- **9. 비범위 (Out of Scope)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\test-integration\test-integration.plan.md) -- 1 connections
  - <- contains <- [[test-integration]]

## Internal Relationships
- 3. 테스트 전략 -> contains -> 3.1 테스트 레벨 분류 [EXTRACTED]
- 3. 테스트 전략 -> contains -> 3.2 환경 요구사항 [EXTRACTED]
- 4. 테스트 항목 -> contains -> 4.1 LangGraph 워크플로 흐름 (강화) [EXTRACTED]
- 4. 테스트 항목 -> contains -> 4.2 PostgreSQL 연결 [EXTRACTED]
- 4. 테스트 항목 -> contains -> 4.3 MCP 도구 호출 [EXTRACTED]
- 5. 구현 계획 -> contains -> pytest 설정 추가 (pyproject.toml) [EXTRACTED]
- 6.1 MCP 도구 Mock 설계 -> has_code_example -> python [EXTRACTED]
- 6.2 에러 시나리오 Mock -> has_code_example -> python [EXTRACTED]
- 6. Mock 전략 -> contains -> 6.1 MCP 도구 Mock 설계 [EXTRACTED]
- 6. Mock 전략 -> contains -> 6.2 에러 시나리오 Mock [EXTRACTED]
- pytest 설정 추가 (pyproject.toml) -> has_code_example -> toml [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 1. 배경 및 목적 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 2. 현재 테스트 구조 분석 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 3. 테스트 전략 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 4. 테스트 항목 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 5. 구현 계획 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 6. Mock 전략 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 7. 성공 기준 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 8. 리스크 및 의존성 [EXTRACTED]
- 통합 테스트 계획서 — test-integration -> contains -> 9. 비범위 (Out of Scope) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 통합 테스트 계획서 — test-integration, 4. 테스트 항목, 3. 테스트 전략를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test-integration.plan.md이다.

### Key Facts
- - **Feature**: test-integration - **작성일**: 2026-03-26 - **우선순위**: HIGH - **예상 범위**: 테스트 파일 5~8개, fixture 2개, 설정 1개
- 4.1 LangGraph 워크플로 흐름 (강화)
- ```python research_gather 노드가 호출하는 도구별 mock mock_searxng = AsyncMock(return_value={ "results": [ {"title": "클라우드 ERP 트렌드", "url": "...", "snippet": "..."}, ] }) mock_openalex = AsyncMock(return_value={ "results": [ {"title": "ERP Cloud Migration Study", "doi": "...", "abstract": "..."}, ] })…
- ```python research_gather 노드가 호출하는 도구별 mock mock_searxng = AsyncMock(return_value={ "results": [ {"title": "클라우드 ERP 트렌드", "url": "...", "snippet": "..."}, ] }) mock_openalex = AsyncMock(return_value={ "results": [ {"title": "ERP Cloud Migration Study", "doi": "...", "abstract": "..."}, ] })…
- ```python Claude 타임아웃 시뮬레이션 mock_claude_timeout = AsyncMock(side_effect=AITimeoutError(step="strategy_generate"))
