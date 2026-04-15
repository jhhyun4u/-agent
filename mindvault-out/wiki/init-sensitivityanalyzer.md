# __init__ & SensitivityAnalyzer
Cohesion: 0.20 | Nodes: 10

## Key Nodes
- **__init__** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\engine.py) -- 8 connections
  - -> calls -> [[unresolvedrefcoststandardselector]]
  - -> calls -> [[unresolvedrefenhancedcostestimator]]
  - -> calls -> [[unresolvedrefwinprobabilitymodel]]
  - -> calls -> [[unresolvedrefsensitivityanalyzer]]
  - -> calls -> [[unresolvedrefcompetitorpricinganalyzer]]
  - -> calls -> [[unresolvedrefclientpreferenceanalyzer]]
  - -> calls -> [[unresolvedrefpricescorecalculator]]
  - <- contains <- [[pricingengine]]
- **SensitivityAnalyzer** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\sensitivity.py) -- 3 connections
  - -> contains -> [[init]]
  - -> contains -> [[analyze]]
  - <- contains <- [[sensitivity]]
- **__unresolved__::ref::winprobabilitymodel** () -- 2 connections
  - <- calls <- [[init]]
  - <- calls <- [[init]]
- **__init__** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\sensitivity.py) -- 2 connections
  - -> calls -> [[unresolvedrefwinprobabilitymodel]]
  - <- contains <- [[sensitivityanalyzer]]
- **__unresolved__::ref::clientpreferenceanalyzer** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::competitorpricinganalyzer** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::coststandardselector** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::enhancedcostestimator** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::pricescorecalculator** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::sensitivityanalyzer** () -- 1 connections
  - <- calls <- [[init]]

## Internal Relationships
- __init__ -> calls -> __unresolved__::ref::coststandardselector [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::enhancedcostestimator [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::winprobabilitymodel [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::sensitivityanalyzer [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::competitorpricinganalyzer [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::clientpreferenceanalyzer [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::pricescorecalculator [EXTRACTED]
- SensitivityAnalyzer -> contains -> __init__ [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::winprobabilitymodel [EXTRACTED]

## Cross-Community Connections
- SensitivityAnalyzer -> contains -> analyze (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 __init__, SensitivityAnalyzer, __unresolved__::ref::winprobabilitymodel를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 engine.py, sensitivity.py이다.

### Key Facts
- def __init__(self): self._cost_selector = CostStandardSelector() self._cost_estimator = EnhancedCostEstimator() self._win_model = WinProbabilityModel() self._sensitivity = SensitivityAnalyzer() self._competitor = CompetitorPricingAnalyzer() self._client_pref = ClientPreferenceAnalyzer()…
- class SensitivityAnalyzer: """민감도 분석기. 입찰 비율 범위를 스윕하며 최적점을 찾는다."""
- def __init__(self): self._model = WinProbabilityModel()
