# python & 🔗 라우팅 강화 (edges.py)
Cohesion: 0.16 | Nodes: 18

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 8 connections
  - <- has_code_example <- [[appgraphnodesproposalcustomeranalysispy]]
  - <- has_code_example <- [[graphpy]]
  - <- has_code_example <- [[2-1-analyzesectionrequirement]]
  - <- has_code_example <- [[2-2]]
  - <- has_code_example <- [[phase-3]]
  - <- has_code_example <- [[phase-4]]
  - <- has_code_example <- [[statepy]]
  - <- has_code_example <- [[edgespy]]
- **🔗 라우팅 강화 (edges.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 7 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[phase-1-customer-analysis-1]]
  - -> contains -> [[phase-2-section-writing-1]]
  - -> contains -> [[phase-3-section-validation-1]]
  - -> contains -> [[phase-4-consolidation-1]]
  - -> contains -> [[phase-5-integration-testing-1]]
  - <- contains <- [[step-8a]]
- **STEP 8A: 고객 관점 섹션 검토 구현 가이드** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 7 connections
  - -> contains -> [[3]]
  - -> contains -> [[phase-1-proposalcustomeranalysis]]
  - -> contains -> [[phase-2-proposalwritenext]]
  - -> contains -> [[phase-3]]
  - -> contains -> [[phase-4]]
  - -> contains -> [[statepy]]
  - -> contains -> [[edgespy]]
- **📝 Phase 1: proposal_customer_analysis (새 노드)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 3 connections
  - -> contains -> [[appgraphnodesproposalcustomeranalysispy]]
  - -> contains -> [[graphpy]]
  - <- contains <- [[step-8a]]
- **📝 Phase 2: proposal_write_next 강화** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 3 connections
  - -> contains -> [[2-1-analyzesectionrequirement]]
  - -> contains -> [[2-2]]
  - <- contains <- [[step-8a]]
- **2-1) _analyze_section_requirement 함수 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-2-proposalwritenext]]
- **2-2) 고객 관점 프롬프트 강화** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-2-proposalwritenext]]
- **파일: `app/graph/nodes/proposal_customer_analysis.py` (새로 생성)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-1-proposalcustomeranalysis]]
- **그래프 연결 (graph.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[phase-1-proposalcustomeranalysis]]
- **🔍 Phase 3: 섹션 검증 노드 (새 노드)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-8a]]
- **🔄 Phase 4: 통합 검증 노드 (새 노드)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-8a]]
- **📊 상태 필드 추가 (state.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-8a]]
- **3가지 주요 작업** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[step-8a]]
- **Phase 1: Customer Analysis (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[edgespy]]
- **Phase 2: Section Writing 강화 (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[edgespy]]
- **Phase 3: Section Validation (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[edgespy]]
- **Phase 4: Consolidation (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[edgespy]]
- **Phase 5: Integration & Testing (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-implementation-guide.md) -- 1 connections
  - <- contains <- [[edgespy]]

## Internal Relationships
- 2-1) _analyze_section_requirement 함수 추가 -> has_code_example -> python [EXTRACTED]
- 2-2) 고객 관점 프롬프트 강화 -> has_code_example -> python [EXTRACTED]
- 파일: `app/graph/nodes/proposal_customer_analysis.py` (새로 생성) -> has_code_example -> python [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> has_code_example -> python [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> contains -> Phase 1: Customer Analysis (1일) [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> contains -> Phase 2: Section Writing 강화 (1일) [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> contains -> Phase 3: Section Validation (1일) [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> contains -> Phase 4: Consolidation (1일) [EXTRACTED]
- 🔗 라우팅 강화 (edges.py) -> contains -> Phase 5: Integration & Testing (1일) [EXTRACTED]
- 그래프 연결 (graph.py) -> has_code_example -> python [EXTRACTED]
- 📝 Phase 1: proposal_customer_analysis (새 노드) -> contains -> 파일: `app/graph/nodes/proposal_customer_analysis.py` (새로 생성) [EXTRACTED]
- 📝 Phase 1: proposal_customer_analysis (새 노드) -> contains -> 그래프 연결 (graph.py) [EXTRACTED]
- 📝 Phase 2: proposal_write_next 강화 -> contains -> 2-1) _analyze_section_requirement 함수 추가 [EXTRACTED]
- 📝 Phase 2: proposal_write_next 강화 -> contains -> 2-2) 고객 관점 프롬프트 강화 [EXTRACTED]
- 🔍 Phase 3: 섹션 검증 노드 (새 노드) -> has_code_example -> python [EXTRACTED]
- 🔄 Phase 4: 통합 검증 노드 (새 노드) -> has_code_example -> python [EXTRACTED]
- 📊 상태 필드 추가 (state.py) -> has_code_example -> python [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 3가지 주요 작업 [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 📝 Phase 1: proposal_customer_analysis (새 노드) [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 📝 Phase 2: proposal_write_next 강화 [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 🔍 Phase 3: 섹션 검증 노드 (새 노드) [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 🔄 Phase 4: 통합 검증 노드 (새 노드) [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 📊 상태 필드 추가 (state.py) [EXTRACTED]
- STEP 8A: 고객 관점 섹션 검토 구현 가이드 -> contains -> 🔗 라우팅 강화 (edges.py) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 🔗 라우팅 강화 (edges.py), STEP 8A: 고객 관점 섹션 검토 구현 가이드를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 STEP-8A-implementation-guide.md이다.

### Key Facts
- ```python """ STEP 8A-0: 고객 요구사항 분석 (proposal_customer_analysis)
- ```python def route_after_section_review(state: ProposalState) -> str: """섹션 리뷰 후 라우팅 (강화)"""
- > **작성일**: 2026-03-29 > **목표**: 고객(발주기관) 관점에서 섹션별 검토 루프 구현 > **예상 구현 기간**: 3-4일 (Phase, Node 개발)
- 파일: `app/graph/nodes/proposal_customer_analysis.py` (새로 생성)
- ```python async def _analyze_section_requirement( section_id: str, section_title: str, customer_context: dict, eval_items: list ) -> dict: """이 섹션이 충족해야 할 고객 니즈를 정리"""
