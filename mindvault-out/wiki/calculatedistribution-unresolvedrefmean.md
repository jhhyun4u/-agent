# _calculate_distribution & __unresolved__::ref::mean
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **_calculate_distribution** (C:\project\tenopa proposer\-agent-master\app\graph\nodes\evaluation_nodes.py) -- 8 connections
  - -> calls -> [[unresolvedrefmean]]
  - -> calls -> [[unresolvedrefmedian]]
  - -> calls -> [[unresolvedrefstdev]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefvariance]]
  - -> calls -> [[unresolvedrefmin]]
  - -> calls -> [[unresolvedrefmax]]
  - <- contains <- [[evaluationnodes]]
- **__unresolved__::ref::mean** () -- 1 connections
  - <- calls <- [[calculatedistribution]]
- **__unresolved__::ref::median** () -- 1 connections
  - <- calls <- [[calculatedistribution]]
- **__unresolved__::ref::stdev** () -- 1 connections
  - <- calls <- [[calculatedistribution]]
- **__unresolved__::ref::variance** () -- 1 connections
  - <- calls <- [[calculatedistribution]]

## Internal Relationships
- _calculate_distribution -> calls -> __unresolved__::ref::mean [EXTRACTED]
- _calculate_distribution -> calls -> __unresolved__::ref::median [EXTRACTED]
- _calculate_distribution -> calls -> __unresolved__::ref::stdev [EXTRACTED]
- _calculate_distribution -> calls -> __unresolved__::ref::variance [EXTRACTED]

## Cross-Community Connections
- _calculate_distribution -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_distribution -> calls -> __unresolved__::ref::min (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_distribution -> calls -> __unresolved__::ref::max (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _calculate_distribution, __unresolved__::ref::mean, __unresolved__::ref::median를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 evaluation_nodes.py이다.

### Key Facts
- 항목별 분포 계산 scores_list = [s["score"] for s in item_scores_by_evaluator.values()] distribution = _calculate_distribution(scores_list)
