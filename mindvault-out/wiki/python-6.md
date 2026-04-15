# python & 👥 평가위원 6명 프로필
Cohesion: 0.18 | Nodes: 15

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 8 connections
  - <- has_code_example <- [[async-def-mockevaluationstate-proposalstate-dict]]
  - <- has_code_example <- [[createevaluatorprofiles-listdict]]
  - <- has_code_example <- [[routeaftermockevalreviewstate-str]]
  - <- has_code_example <- [[graphpy]]
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[3]]
  - <- has_code_example <- [[ai]]
- **👥 평가위원 6명 프로필** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 6 connections
  - -> contains -> [[createevaluatorprofiles-listdict]]
  - -> contains -> [[async-def-scoreevaluationitemitem-evaluator-sections-strategy-dict]]
  - -> contains -> [[calculatedistributionscores-dict]]
  - -> contains -> [[assessconsensusscores-dict]]
  - -> contains -> [[assesswinprobabilityfinalscore-str]]
  - -> contains -> [[routeaftermockevalreviewstate-str]]
- **🔗 그래프 통합 (graph.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 5 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[ai]]
- **3. 라우팅 로직 테스트** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 3 connections
  - -> has_code_example -> [[python]]
  - -> has_code_example -> [[bash]]
  - <- contains <- [[graphpy]]
- **1. 평가위원 프로필 확인** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[graphpy]]
- **2. 분포 분석 테스트** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[graphpy]]
- **AI 응답 검증** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[graphpy]]
- **`_create_evaluator_profiles() -> list[dict]`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6]]
- **`route_after_mock_eval_review(state) -> str`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - <- has_code_example <- [[3]]
- **`_assess_consensus(scores) -> dict`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - <- contains <- [[6]]
- **`_assess_win_probability(final_score) -> str`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - <- contains <- [[6]]
- **`async def _score_evaluation_item(item, evaluator, sections, strategy) -> dict`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - <- contains <- [[6]]
- **`async def mock_evaluation(state: ProposalState) -> dict`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **`_calculate_distribution(scores) -> dict`** (C:\project\tenopa proposer\-agent-master\docs\02-design\MOCK_EVALUATION_QUICK_REFERENCE.md) -- 1 connections
  - <- contains <- [[6]]

## Internal Relationships
- 1. 평가위원 프로필 확인 -> has_code_example -> python [EXTRACTED]
- 2. 분포 분석 테스트 -> has_code_example -> python [EXTRACTED]
- 3. 라우팅 로직 테스트 -> has_code_example -> python [EXTRACTED]
- 3. 라우팅 로직 테스트 -> has_code_example -> bash [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `_create_evaluator_profiles() -> list[dict]` [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `async def _score_evaluation_item(item, evaluator, sections, strategy) -> dict` [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `_calculate_distribution(scores) -> dict` [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `_assess_consensus(scores) -> dict` [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `_assess_win_probability(final_score) -> str` [EXTRACTED]
- 👥 평가위원 6명 프로필 -> contains -> `route_after_mock_eval_review(state) -> str` [EXTRACTED]
- AI 응답 검증 -> has_code_example -> python [EXTRACTED]
- `async def mock_evaluation(state: ProposalState) -> dict` -> has_code_example -> python [EXTRACTED]
- `_create_evaluator_profiles() -> list[dict]` -> has_code_example -> python [EXTRACTED]
- 🔗 그래프 통합 (graph.py) -> has_code_example -> python [EXTRACTED]
- 🔗 그래프 통합 (graph.py) -> contains -> 1. 평가위원 프로필 확인 [EXTRACTED]
- 🔗 그래프 통합 (graph.py) -> contains -> 2. 분포 분석 테스트 [EXTRACTED]
- 🔗 그래프 통합 (graph.py) -> contains -> 3. 라우팅 로직 테스트 [EXTRACTED]
- 🔗 그래프 통합 (graph.py) -> contains -> AI 응답 검증 [EXTRACTED]
- `route_after_mock_eval_review(state) -> str` -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 👥 평가위원 6명 프로필, 🔗 그래프 통합 (graph.py)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 MOCK_EVALUATION_QUICK_REFERENCE.md이다.

### Key Facts
- **입력** ```python state: { "rfp_analysis": RFPAnalysis,  # eval_items 포함 "strategy": Strategy,          # win_theme, positioning "proposal_sections": [ProposalSection, ...],  # 제안서 콘텐츠 } ```
- `_create_evaluator_profiles() -> list[dict]`
- ```python STEP 10A: 모의평가 AI 실행 g.add_edge("mock_evaluation", "review_mock_eval")
- 테스트 state 구성 state = { "approval": { "mock_evaluation": { "status": "approved"  # or "rejected" } }, "feedback_history": [ { "rework_targets": ["strategy_generate"]  # or ["section_1"] } ] }
- evaluators = _create_evaluator_profiles() for e in evaluators: print(f"{e['name']} ({e['type']}): {e['perspective']}") ```
