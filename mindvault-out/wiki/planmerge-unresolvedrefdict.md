# plan_merge & __unresolved__::ref::dict
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **plan_merge** (C:\project\tenopa proposer\app\graph\nodes\merge_nodes.py) -- 9 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefmodeldump]]
  - -> calls -> [[unresolvedrefhasattr]]
  - -> calls -> [[unresolvedrefdict]]
  - -> calls -> [[unresolvedrefitems]]
  - -> calls -> [[unresolvedrefproposalplan]]
  - -> calls -> [[unresolvedrefupdate]]
  - -> calls -> [[unresolvedrefsyncdynamicsections]]
  - <- contains <- [[mergenodes]]
- **__unresolved__::ref::dict** () -- 7 connections
  - <- calls <- [[planmerge]]
  - <- calls <- [[getallpipelinestatus]]
  - <- calls <- [[buildprofilefromdb]]
  - <- calls <- [[patchhwpxlibrary]]
  - <- calls <- [[truncatekbresults]]
  - <- calls <- [[checknodemovefeasibility]]
  - <- calls <- [[buildkeywordindex]]
- **check_node_move_feasibility** (C:\project\tenopa proposer\app\services\version_manager.py) -- 5 connections
  - -> calls -> [[unresolvedrefvalidatemoveandresolveversions]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefany]]
  - -> calls -> [[unresolvedrefdict]]
  - <- contains <- [[versionmanager]]
- **get_all_pipeline_status** (C:\project\tenopa proposer\app\services\bid_pipeline.py) -- 2 connections
  - -> calls -> [[unresolvedrefdict]]
  - <- contains <- [[bidpipeline]]
- **__unresolved__::ref::_sync_dynamic_sections** () -- 1 connections
  - <- calls <- [[planmerge]]
- **__unresolved__::ref::proposalplan** () -- 1 connections
  - <- calls <- [[planmerge]]
- **__unresolved__::ref::validate_move_and_resolve_versions** () -- 1 connections
  - <- calls <- [[checknodemovefeasibility]]

## Internal Relationships
- plan_merge -> calls -> __unresolved__::ref::dict [EXTRACTED]
- plan_merge -> calls -> __unresolved__::ref::proposalplan [EXTRACTED]
- plan_merge -> calls -> __unresolved__::ref::_sync_dynamic_sections [EXTRACTED]
- get_all_pipeline_status -> calls -> __unresolved__::ref::dict [EXTRACTED]
- check_node_move_feasibility -> calls -> __unresolved__::ref::validate_move_and_resolve_versions [EXTRACTED]
- check_node_move_feasibility -> calls -> __unresolved__::ref::dict [EXTRACTED]

## Cross-Community Connections
- plan_merge -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_merge -> calls -> __unresolved__::ref::model_dump (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_merge -> calls -> __unresolved__::ref::hasattr (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_merge -> calls -> __unresolved__::ref::items (-> [[unresolvedrefget-unresolvedrefexecute]])
- plan_merge -> calls -> __unresolved__::ref::update (-> [[unresolvedrefget-unresolvedrefexecute]])
- check_node_move_feasibility -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- check_node_move_feasibility -> calls -> __unresolved__::ref::any (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 plan_merge, __unresolved__::ref::dict, check_node_move_feasibility를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 bid_pipeline.py, merge_nodes.py, version_manager.py이다.

### Key Facts
- plan_merge, proposal_merge: 부분 재작업 시 기존 결과 보존 + 새 결과 덮어씌움.
- async def check_node_move_feasibility( proposal_id: UUID, target_node: str, state: ProposalState, ) -> dict: """ 노드 이동 가능 여부 사전 확인 (모달 표시 전).
- def get_all_pipeline_status() -> dict: return dict(_pipeline_status)
