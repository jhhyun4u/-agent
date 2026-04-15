# python & 1. 평가위원 프로필 정의 (`_create_evaluator_profiles`)
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 6 connections
  - <- has_code_example <- [[1-createevaluatorprofiles]]
  - <- has_code_example <- [[2-scoreevaluationitem]]
  - <- has_code_example <- [[3-calculatedistribution]]
  - <- has_code_example <- [[5]]
  - <- has_code_example <- [[edgespy]]
  - <- has_code_example <- [[graphpy]]
- **1. 평가위원 프로필 정의 (`_create_evaluator_profiles`)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **2. 평가항목별 점수 산출 (`_score_evaluation_item`)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **3. 분포 분석 (`_calculate_distribution`)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **5. 최종 평가 보고서 구조** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **라우팅 함수 (edges.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]
- **그래프 엣지 (graph.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[python]]

## Internal Relationships
- 1. 평가위원 프로필 정의 (`_create_evaluator_profiles`) -> has_code_example -> python [EXTRACTED]
- 2. 평가항목별 점수 산출 (`_score_evaluation_item`) -> has_code_example -> python [EXTRACTED]
- 3. 분포 분석 (`_calculate_distribution`) -> has_code_example -> python [EXTRACTED]
- 5. 최종 평가 보고서 구조 -> has_code_example -> python [EXTRACTED]
- 라우팅 함수 (edges.py) -> has_code_example -> python [EXTRACTED]
- 그래프 엣지 (graph.py) -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 1. 평가위원 프로필 정의 (`_create_evaluator_profiles`), 2. 평가항목별 점수 산출 (`_score_evaluation_item`)를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 mock-evaluation-implementation-summary.md이다.

### Key Facts
- **프로필 구조** ```python { "id": "evaluator_1", "name": "이산업", "title": "OOO 회사 개발이사", "type": "산업계", "experience_years": 15, "perspective": ["사업 실현가능성", "비용 효율성", ...], "evaluation_bias": { "tendency": "보수적", "scoring_range": (0, 90),  # 점수 범위 제한 "weight": 1.0 } } ```
- **6명 평가위원 (산학연 2명씩)**
- **프로세스** 1. RFP의 eval_items에서 평가항목 추출 2. 각 평가위원이 독립적으로 해당 항목 평가 3. AI(Claude)가 평가위원 관점 시뮬레이션 4. 점수 범위 제한 (evaluator bias 반영) 5. 배점 기준으로 정규화
- **6명 평가위원의 점수 분포** ```python { "mean": 72.5,          # 평균 "median": 75.0,        # 중앙값 "stdev": 8.3,          # 표준편차 (합의도 지표) "variance": 68.9,      # 분산 "min": 62.0, "max": 85.0, "range": (62.0, 85.0), "scores": [68, 75, 78, 62, 80, 85] } ```
- ```python mock_evaluation_report = { "evaluation_metadata": { "total_evaluators": 6, "evaluators_by_type": {"산업계": 2, "학계": 2, "연구계/공공": 2}, "total_evaluation_items": N, "final_score": 72.5, "percentage": 72.5, }, "evaluators": [ { "id": "evaluator_1", "name": "이산업", "title": "OOO 회사 개발이사", "type":…
