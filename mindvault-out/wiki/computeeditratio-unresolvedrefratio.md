# compute_edit_ratio & __unresolved__::ref::ratio
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **compute_edit_ratio** (C:\project\tenopa proposer\app\services\human_edit_tracker.py) -- 4 connections
  - -> calls -> [[unresolvedrefsequencematcher]]
  - -> calls -> [[unresolvedrefratio]]
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[humanedittracker]]
- **__unresolved__::ref::ratio** () -- 1 connections
  - <- calls <- [[computeeditratio]]
- **__unresolved__::ref::sequencematcher** () -- 1 connections
  - <- calls <- [[computeeditratio]]

## Internal Relationships
- compute_edit_ratio -> calls -> __unresolved__::ref::sequencematcher [EXTRACTED]
- compute_edit_ratio -> calls -> __unresolved__::ref::ratio [EXTRACTED]

## Cross-Community Connections
- compute_edit_ratio -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 compute_edit_ratio, __unresolved__::ref::ratio, __unresolved__::ref::sequencematcher를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 human_edit_tracker.py이다.

### Key Facts
- def compute_edit_ratio(original: str, edited: str) -> float: """두 텍스트의 수정 비율 계산 (0.0~1.0).""" if not original and not edited: return 0.0 if not original: return 1.0 if original == edited: return 0.0
