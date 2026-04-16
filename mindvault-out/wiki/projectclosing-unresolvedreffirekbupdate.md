# project_closing & __unresolved__::ref::_fire_kb_update
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **project_closing** (C:\project\tenopa proposer\app\graph\nodes\evaluation_nodes.py) -- 5 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedreffirekbupdate]]
  - -> calls -> [[unresolvedreffirestatusupdate]]
  - -> calls -> [[unresolvedreflen]]
  - <- contains <- [[evaluationnodes]]
- **__unresolved__::ref::_fire_kb_update** () -- 1 connections
  - <- calls <- [[projectclosing]]
- **__unresolved__::ref::_fire_status_update** () -- 1 connections
  - <- calls <- [[projectclosing]]

## Internal Relationships
- project_closing -> calls -> __unresolved__::ref::_fire_kb_update [EXTRACTED]
- project_closing -> calls -> __unresolved__::ref::_fire_status_update [EXTRACTED]

## Cross-Community Connections
- project_closing -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- project_closing -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 project_closing, __unresolved__::ref::_fire_kb_update, __unresolved__::ref::_fire_status_update를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 evaluation_nodes.py이다.

### Key Facts
- 6A — mock_evaluation: 제안서 + PPT 완성 후 모의 평가 시뮬레이션 (RFP 기반, 6명 평가위원) 7  — eval_result: 실제 평가 결과 기록 (입력 대기) 8  — project_closing: 프로젝트 종료 처리 (KB 업데이트, 아카이브)
