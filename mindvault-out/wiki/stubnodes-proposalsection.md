# stub_nodes & proposal_section
Cohesion: 0.18 | Nodes: 11

## Key Nodes
- **stub_nodes** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 12 connections
  - -> contains -> [[strategygenerate]]
  - -> contains -> [[planteam]]
  - -> contains -> [[planassign]]
  - -> contains -> [[planschedule]]
  - -> contains -> [[planstory]]
  - -> contains -> [[planprice]]
  - -> contains -> [[proposalsection]]
  - -> contains -> [[selfreviewwithautoimprove]]
  - -> contains -> [[presentationstrategy]]
  - -> contains -> [[pptslide]]
  - -> imports -> [[unresolvedreflogging]]
  - -> imports -> [[unresolvedrefstate]]
- **proposal_section** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 3 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **plan_assign** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **plan_price** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **plan_schedule** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **plan_story** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **plan_team** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **ppt_slide** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **presentation_strategy** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **self_review_with_auto_improve** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]
- **strategy_generate** (C:\project\tenopa proposer\scripts\archive\stub_nodes.py) -- 2 connections
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[stubnodes]]

## Internal Relationships
- stub_nodes -> contains -> strategy_generate [EXTRACTED]
- stub_nodes -> contains -> plan_team [EXTRACTED]
- stub_nodes -> contains -> plan_assign [EXTRACTED]
- stub_nodes -> contains -> plan_schedule [EXTRACTED]
- stub_nodes -> contains -> plan_story [EXTRACTED]
- stub_nodes -> contains -> plan_price [EXTRACTED]
- stub_nodes -> contains -> proposal_section [EXTRACTED]
- stub_nodes -> contains -> self_review_with_auto_improve [EXTRACTED]
- stub_nodes -> contains -> presentation_strategy [EXTRACTED]
- stub_nodes -> contains -> ppt_slide [EXTRACTED]

## Cross-Community Connections
- plan_assign -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_price -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_schedule -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_story -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_team -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- ppt_slide -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- presentation_strategy -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- proposal_section -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- proposal_section -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- self_review_with_auto_improve -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- strategy_generate -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- stub_nodes -> imports -> __unresolved__::ref::logging (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- stub_nodes -> imports -> __unresolved__::ref::state (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 stub_nodes, proposal_section, plan_assign를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 stub_nodes.py이다.

### Key Facts
- async def proposal_section(state: ProposalState) -> dict: """STEP 4: 섹션별 제안서 작성.""" section_id = state.get("_current_section_id", "unknown") logger.info(f"[STUB] proposal_section — {section_id}") return {"parallel_results": {"sections": []}}
- async def plan_assign(state: ProposalState) -> dict: """STEP 3: 역할 배분.""" logger.info("[STUB] plan_assign") return {"parallel_results": {"deliverables": []}}
- async def plan_price(state: ProposalState) -> dict: """STEP 3: 가격 산정.""" logger.info("[STUB] plan_price") return {"parallel_results": {"bid_price": {}}}
- async def plan_schedule(state: ProposalState) -> dict: """STEP 3: 일정 계획.""" logger.info("[STUB] plan_schedule") return {"parallel_results": {"schedule": {}}}
- async def plan_story(state: ProposalState) -> dict: """STEP 3: 스토리라인.""" logger.info("[STUB] plan_story") return {"parallel_results": {"storylines": {}}}
