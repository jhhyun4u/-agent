# edges & route_after_bid_plan_review
Cohesion: 0.14 | Nodes: 14

## Key Nodes
- **edges** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 15 connections
  - -> contains -> [[approvalrouter]]
  - -> contains -> [[routeaftermockevalreview]]
  - -> contains -> [[routeaftergngreview]]
  - -> contains -> [[routeafterstrategyreview]]
  - -> contains -> [[routeafterbidplanreview]]
  - -> contains -> [[routeafterplanreview]]
  - -> contains -> [[routeafterselfreview]]
  - -> contains -> [[routeaftersectionreview]]
  - -> contains -> [[routeafterpresentationstrategy]]
  - -> contains -> [[routeaftersectionvalidatorreview]]
  - -> contains -> [[routeafterfeedbackprocessorreview]]
  - -> contains -> [[routeafterrewritereview]]
  - -> contains -> [[routeaftergapanalysisreview]]
  - -> imports -> [[unresolvedreftyping]]
  - -> imports -> [[unresolvedrefstate]]
- **route_after_bid_plan_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 3 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefreversed]]
  - <- contains <- [[edges]]
- **route_after_feedback_processor_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 3 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefgetattr]]
  - <- contains <- [[edges]]
- **_approval_router** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_gap_analysis_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_gng_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_mock_eval_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_plan_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_rewrite_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_section_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_section_validator_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_self_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **route_after_strategy_review** (C:\project\tenopa proposer\-agent-master\app\graph\edges.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[edges]]
- **__unresolved__::ref::reversed** () -- 1 connections
  - <- calls <- [[routeafterbidplanreview]]

## Internal Relationships
- route_after_bid_plan_review -> calls -> __unresolved__::ref::reversed [EXTRACTED]
- edges -> contains -> _approval_router [EXTRACTED]
- edges -> contains -> route_after_mock_eval_review [EXTRACTED]
- edges -> contains -> route_after_gng_review [EXTRACTED]
- edges -> contains -> route_after_strategy_review [EXTRACTED]
- edges -> contains -> route_after_bid_plan_review [EXTRACTED]
- edges -> contains -> route_after_plan_review [EXTRACTED]
- edges -> contains -> route_after_self_review [EXTRACTED]
- edges -> contains -> route_after_section_review [EXTRACTED]
- edges -> contains -> route_after_section_validator_review [EXTRACTED]
- edges -> contains -> route_after_feedback_processor_review [EXTRACTED]
- edges -> contains -> route_after_rewrite_review [EXTRACTED]
- edges -> contains -> route_after_gap_analysis_review [EXTRACTED]

## Cross-Community Connections
- _approval_router -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_bid_plan_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_feedback_processor_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_feedback_processor_review -> calls -> __unresolved__::ref::getattr (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_gap_analysis_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_gng_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_mock_eval_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_plan_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_rewrite_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_section_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_section_validator_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_self_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- route_after_strategy_review -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- edges -> contains -> route_after_presentation_strategy (-> [[unresolvedrefget-unresolvedreflen]])
- edges -> imports -> __unresolved__::ref::typing (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- edges -> imports -> __unresolved__::ref::state (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 edges, route_after_bid_plan_review, route_after_feedback_processor_review를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 edges.py이다.

### Key Facts
- def route_after_bid_plan_review(state: ProposalState) -> str: """STEP 2.5: 입찰가격계획 리뷰 라우팅.""" approval = state.get("approval", {}).get("bid_plan") if approval and approval.status == "approved": return "approved" # bid_plan 스텝의 가장 최신 피드백만 검사 (stale 방지) feedback = state.get("feedback_history", [])…
- def route_after_feedback_processor_review(state: ProposalState) -> str: """STEP 8E 피드백 처리 후 라우팅.
- 단순 approved/rejected 패턴은 _approval_router 팩토리로 생성. 복잡한 다방향 라우팅은 개별 함수로 유지. """
- def route_after_gap_analysis_review(state: ProposalState) -> str: """STEP 4A-⑥: 스토리라인 갭 분석 후 라우팅. - approved: 갭 분석 결과 승인, 추가 수정 불필요 → PPT 진행(presentation_strategy) - rework_section: 특정 섹션 갭 수정 필요 → proposal_start_gate (섹션 재작성) - rework_strategy: 스토리라인 자체 재설계 필요 → strategy_generate """ approval =…
- def route_after_gng_review(state: ProposalState) -> str: """STEP 1-②: Go/No-Go 라우팅 (current_step 기반).""" step = state.get("current_step", "") if step == "go_no_go_go": return "go" elif step == "go_no_go_no_go": return "no_go" return "rejected"
