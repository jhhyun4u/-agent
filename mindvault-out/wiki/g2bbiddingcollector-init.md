# G2BBiddingCollector & __init__
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **G2BBiddingCollector** (C:\project\tenopa proposer\app\services\g2b_bidding_collector.py) -- 5 connections
  - -> contains -> [[init]]
  - -> contains -> [[collectsimilarprojects]]
  - -> contains -> [[savetovault]]
  - -> contains -> [[analyzeandsave]]
  - <- contains <- [[g2bbiddingcollector]]
- **__init__** (C:\project\tenopa proposer\app\services\g2b_bidding_collector.py) -- 2 connections
  - -> calls -> [[unresolvedrefg2bapiclient]]
  - <- contains <- [[g2bbiddingcollector]]
- **__unresolved__::ref::g2bapiclient** () -- 1 connections
  - <- calls <- [[init]]

## Internal Relationships
- G2BBiddingCollector -> contains -> __init__ [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::g2bapiclient [EXTRACTED]

## Cross-Community Connections
- G2BBiddingCollector -> contains -> collect_similar_projects (-> [[unresolvedrefget-unresolvedrefexecute]])
- G2BBiddingCollector -> contains -> save_to_vault (-> [[unresolvedrefget-unresolvedrefexecute]])
- G2BBiddingCollector -> contains -> analyze_and_save (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 G2BBiddingCollector, __init__, __unresolved__::ref::g2bapiclient를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 g2b_bidding_collector.py이다.

### Key Facts
- class G2BBiddingCollector: """나라장터 입찰/낙찰 데이터 수집"""
- def __init__(self): self.g2b_client = G2BAPIClient() self.batch_size = 10  # 유사 과제 수집 개수
