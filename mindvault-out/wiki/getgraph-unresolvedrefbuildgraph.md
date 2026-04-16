# _get_graph & __unresolved__::ref::build_graph
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **_get_graph** (C:\project\tenopa proposer\app\api\routes_workflow.py) -- 7 connections
  - -> calls -> [[unresolvedreffromconnstring]]
  - -> calls -> [[unresolvedrefsetup]]
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefwarning]]
  - -> calls -> [[unresolvedrefmemorysaver]]
  - -> calls -> [[unresolvedrefbuildgraph]]
  - <- contains <- [[routesworkflow]]
- **__unresolved__::ref::build_graph** () -- 1 connections
  - <- calls <- [[getgraph]]
- **__unresolved__::ref::from_conn_string** () -- 1 connections
  - <- calls <- [[getgraph]]
- **__unresolved__::ref::memorysaver** () -- 1 connections
  - <- calls <- [[getgraph]]
- **__unresolved__::ref::setup** () -- 1 connections
  - <- calls <- [[getgraph]]

## Internal Relationships
- _get_graph -> calls -> __unresolved__::ref::from_conn_string [EXTRACTED]
- _get_graph -> calls -> __unresolved__::ref::setup [EXTRACTED]
- _get_graph -> calls -> __unresolved__::ref::memorysaver [EXTRACTED]
- _get_graph -> calls -> __unresolved__::ref::build_graph [EXTRACTED]

## Cross-Community Connections
- _get_graph -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- _get_graph -> calls -> __unresolved__::ref::warning (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _get_graph, __unresolved__::ref::build_graph, __unresolved__::ref::from_conn_string를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 routes_workflow.py이다.

### Key Facts
- async def _get_graph(): """LangGraph 그래프 인스턴스 (싱글톤). checkpointer 연결.""" global _graph_instance if _graph_instance is not None: return _graph_instance
