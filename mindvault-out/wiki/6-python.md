# 👥 평가위원 6명 상세 정의 & python
Cohesion: 0.21 | Nodes: 12

## Key Nodes
- **👥 평가위원 6명 상세 정의** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 7 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[scoreevaluationitem]]
  - -> contains -> [[consensus]]
  - -> contains -> [[1-rfp]]
  - -> contains -> [[2-6]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 6 connections
  - <- has_code_example <- [[rfpanalysis]]
  - <- has_code_example <- [[step-10a-evalitems]]
  - <- has_code_example <- [[6]]
  - <- has_code_example <- [[scoreevaluationitem]]
  - <- has_code_example <- [[consensus]]
  - <- has_code_example <- [[step-10a]]
- **평가위원 의견 일치도 (Consensus)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6]]
- **🎯 RFP 평가항목 추출** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 2 connections
  - -> contains -> [[rfpanalysis]]
  - -> contains -> [[step-10a-evalitems]]
- **RFPAnalysis 구조 (기존)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[rfp]]
- **_score_evaluation_item 함수** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6]]
- **STEP 10A 수정: eval_items 기반 평가** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[rfp]]
- **1️⃣ RFP 평가항목 기반** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 1 connections
  - <- contains <- [[6]]
- **2️⃣ 6명 평가위원 시뮬레이션** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 1 connections
  - <- contains <- [[6]]
- **3️⃣ 다각도 평가** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 1 connections
  - <- contains <- [[6]]
- **4️⃣ 신뢰성** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 1 connections
  - <- contains <- [[6]]
- **📝 STEP 10A 최종 함수 구조** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-detailed-design.md) -- 1 connections
  - -> has_code_example -> [[python]]

## Internal Relationships
- 👥 평가위원 6명 상세 정의 -> has_code_example -> python [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> _score_evaluation_item 함수 [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> 평가위원 의견 일치도 (Consensus) [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> 1️⃣ RFP 평가항목 기반 [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> 2️⃣ 6명 평가위원 시뮬레이션 [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> 3️⃣ 다각도 평가 [EXTRACTED]
- 👥 평가위원 6명 상세 정의 -> contains -> 4️⃣ 신뢰성 [EXTRACTED]
- 평가위원 의견 일치도 (Consensus) -> has_code_example -> python [EXTRACTED]
- 🎯 RFP 평가항목 추출 -> contains -> RFPAnalysis 구조 (기존) [EXTRACTED]
- 🎯 RFP 평가항목 추출 -> contains -> STEP 10A 수정: eval_items 기반 평가 [EXTRACTED]
- RFPAnalysis 구조 (기존) -> has_code_example -> python [EXTRACTED]
- _score_evaluation_item 함수 -> has_code_example -> python [EXTRACTED]
- 📝 STEP 10A 최종 함수 구조 -> has_code_example -> python [EXTRACTED]
- STEP 10A 수정: eval_items 기반 평가 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 👥 평가위원 6명 상세 정의, python, 평가위원 의견 일치도 (Consensus)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 mock-evaluation-detailed-design.md이다.

### Key Facts
- RFPAnalysis 구조 (기존) ```python class RFPAnalysis(BaseModel): eval_method: str  # 예: "기술 40점 + 가격 30점 + 관리 20점 + 기타 10점" eval_items: list[dict]  # 평가항목 목록 # [ #   { #     "item_id": "T1", #     "category": "기술", #     "title": "기술혁신성", #     "score": 20,  # 배점 #     "criteria": [ #       "신규 기술 적용도",…
- ```python def _assess_consensus(item_scores: dict) -> dict: """ 평가위원들의 의견 일치도 평가
- RFPAnalysis 구조 (기존) ```python class RFPAnalysis(BaseModel): eval_method: str  # 예: "기술 40점 + 가격 30점 + 관리 20점 + 기타 10점" eval_items: list[dict]  # 평가항목 목록 # [ #   { #     "item_id": "T1", #     "category": "기술", #     "title": "기술혁신성", #     "score": 20,  # 배점 #     "criteria": [ #       "신규 기술 적용도",…
- STEP 10A 수정: eval_items 기반 평가
- ```python async def _score_evaluation_item( item: dict, evaluator: dict, proposal_sections: list, strategy: dict ) -> dict: """ 특정 평가항목에 대해 평가위원이 점수를 산출
