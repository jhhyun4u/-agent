# build_context & check_budget
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **build_context** (C:\project\tenopa proposer\app\services\token_manager.py) -- 10 connections
  - -> calls -> [[unresolvedrefgetbudget]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedreftruncatecontext]]
  - -> calls -> [[unresolvedreftrimfeedbackhistory]]
  - -> calls -> [[unresolvedrefjoin]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedreftruncatekbresults]]
  - -> calls -> [[unresolvedrefitems]]
  - <- contains <- [[tokenmanager]]
- **check_budget** (C:\project\tenopa proposer\app\services\token_manager.py) -- 3 connections
  - -> calls -> [[unresolvedrefgetbudget]]
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[tokenmanager]]
- **__unresolved__::ref::get_budget** () -- 2 connections
  - <- calls <- [[checkbudget]]
  - <- calls <- [[buildcontext]]
- **__unresolved__::ref::trim_feedback_history** () -- 1 connections
  - <- calls <- [[buildcontext]]
- **__unresolved__::ref::truncate_context** () -- 1 connections
  - <- calls <- [[buildcontext]]
- **__unresolved__::ref::truncate_kb_results** () -- 1 connections
  - <- calls <- [[buildcontext]]

## Internal Relationships
- build_context -> calls -> __unresolved__::ref::get_budget [EXTRACTED]
- build_context -> calls -> __unresolved__::ref::truncate_context [EXTRACTED]
- build_context -> calls -> __unresolved__::ref::trim_feedback_history [EXTRACTED]
- build_context -> calls -> __unresolved__::ref::truncate_kb_results [EXTRACTED]
- check_budget -> calls -> __unresolved__::ref::get_budget [EXTRACTED]

## Cross-Community Connections
- build_context -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])
- build_context -> calls -> __unresolved__::ref::join (-> [[unresolvedrefget-unresolvedrefexecute]])
- build_context -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- build_context -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- build_context -> calls -> __unresolved__::ref::items (-> [[unresolvedrefget-unresolvedrefexecute]])
- check_budget -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 build_context, check_budget, __unresolved__::ref::get_budget를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 token_manager.py이다.

### Key Facts
- def build_context( step: str, rfp_summary: str = "", strategy: str = "", plan: str = "", feedback_history: list[dict] | None = None, kb_results: dict[str, list[dict]] | None = None, section_specific: str = "", ) -> tuple[list[dict], dict]: """STEP별 최적화된 컨텍스트 메시지 + Prompt Caching 설정 반환.
- def check_budget(step: str, estimated_tokens: int) -> dict[str, Any]: """토큰 예산 초과 여부 확인.
