# 📊 수정 지시 구조 (Human이 받는 정보) & python
Cohesion: 0.14 | Nodes: 18

## Key Nodes
- **📊 수정 지시 구조 (Human이 받는 정보)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 11 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[case-1-approved]]
  - -> contains -> [[case-2-rework]]
  - -> contains -> [[case-3-re-evaluate]]
  - -> contains -> [[v60]]
  - -> contains -> [[v61]]
  - -> contains -> [[phase-a-analysis-1]]
  - -> contains -> [[phase-b-human-review-ui-1]]
  - -> contains -> [[phase-c-feedback-processing-1]]
  - -> contains -> [[phase-d-integration-testing-1]]
  - <- contains <- [[mock-evaluation-human-review-feedback]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 5 connections
  - <- has_code_example <- [[step-10a-mockevaluationanalysis]]
  - <- has_code_example <- [[ai]]
  - <- has_code_example <- [[state]]
  - <- has_code_example <- [[step-11a-processmockevalfeedback]]
  - <- has_code_example <- [[human]]
- **Mock Evaluation → Human Review → Feedback 루프 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 4 connections
  - -> contains -> [[step-10a-mockevaluationanalysis]]
  - -> contains -> [[step-11a-reviewmockeval-human-review]]
  - -> contains -> [[step-11a-processmockevalfeedback]]
  - -> contains -> [[human]]
- **🔍 STEP 10A-분석: mock_evaluation_analysis (신규 노드)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 3 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[ai]]
  - <- contains <- [[mock-evaluation-human-review-feedback]]
- **👤 STEP 11A (강화): review_mock_eval Human Review** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 3 connections
  - -> contains -> [[human-review-panel]]
  - -> contains -> [[state]]
  - <- contains <- [[mock-evaluation-human-review-feedback]]
- **AI 분석 프롬프트** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-10a-mockevaluationanalysis]]
- **State 필드 추가** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-11a-reviewmockeval-human-review]]
- **🔄 STEP 11A-피드백: process_mock_eval_feedback (신규 노드)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[mock-evaluation-human-review-feedback]]
- **Case 1: 점수 만족 → Approved** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Case 2: 특정 항목만 개선 → Rework** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Case 3: 의견이 너무 갈려서 → Re-evaluate** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Human Review Panel 구조** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[step-11a-reviewmockeval-human-review]]
- **Phase A: Analysis 노드 (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Phase B: Human Review UI (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Phase C: Feedback Processing 노드 (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **Phase D: Integration & Testing (1일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **기존 (v6.0)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]
- **신규 (v6.1)** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-human-review-feedback.md) -- 1 connections
  - <- contains <- [[human]]

## Internal Relationships
- AI 분석 프롬프트 -> has_code_example -> python [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> has_code_example -> python [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Case 1: 점수 만족 → Approved [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Case 2: 특정 항목만 개선 → Rework [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Case 3: 의견이 너무 갈려서 → Re-evaluate [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> 기존 (v6.0) [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> 신규 (v6.1) [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Phase A: Analysis 노드 (1일) [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Phase B: Human Review UI (1일) [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Phase C: Feedback Processing 노드 (1일) [EXTRACTED]
- 📊 수정 지시 구조 (Human이 받는 정보) -> contains -> Phase D: Integration & Testing (1일) [EXTRACTED]
- Mock Evaluation → Human Review → Feedback 루프 설계 -> contains -> 🔍 STEP 10A-분석: mock_evaluation_analysis (신규 노드) [EXTRACTED]
- Mock Evaluation → Human Review → Feedback 루프 설계 -> contains -> 👤 STEP 11A (강화): review_mock_eval Human Review [EXTRACTED]
- Mock Evaluation → Human Review → Feedback 루프 설계 -> contains -> 🔄 STEP 11A-피드백: process_mock_eval_feedback (신규 노드) [EXTRACTED]
- Mock Evaluation → Human Review → Feedback 루프 설계 -> contains -> 📊 수정 지시 구조 (Human이 받는 정보) [EXTRACTED]
- State 필드 추가 -> has_code_example -> python [EXTRACTED]
- 🔍 STEP 10A-분석: mock_evaluation_analysis (신규 노드) -> has_code_example -> python [EXTRACTED]
- 🔍 STEP 10A-분석: mock_evaluation_analysis (신규 노드) -> contains -> AI 분석 프롬프트 [EXTRACTED]
- 👤 STEP 11A (강화): review_mock_eval Human Review -> contains -> Human Review Panel 구조 [EXTRACTED]
- 👤 STEP 11A (강화): review_mock_eval Human Review -> contains -> State 필드 추가 [EXTRACTED]
- 🔄 STEP 11A-피드백: process_mock_eval_feedback (신규 노드) -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 📊 수정 지시 구조 (Human이 받는 정보), python, Mock Evaluation → Human Review → Feedback 루프 설계를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 mock-evaluation-human-review-feedback.md이다.

### Key Facts
- ```python rework_instructions = { "T1": { "eval_item_id": "T1", "eval_item_title": "기술혁신성", "current_score": 17.5, "target_score": "19", "key_concern": [ "파일럿 경험 부족", "적용성 검증 미흡" ], "suggested_actions": [ "파일럿 프로젝트 사례 2-3개 추가", "각 사례마다: 프로젝트명, 기간, 규모, 성과 지표", "리스크 관리 계획 강화" ], "evaluator_feedback":…
- ```python mock_evaluation_result = { "evaluation_items": { "T1": { "item_title": "기술혁신성", "max_score": 20, "scores_by_evaluator": { "evaluator_1": { "evaluator_id": "evaluator_1", "evaluator_name": "이산업", "score": 16, "reasoning": "신기술 적용도 우수하나 실현가능성 검증 부족", "strengths": ["AI 기술 수준 높음"],…
- > **설계일**: 2026-03-29 > **목표**: 평가위원 평가의견 정리 → Human 피드백 → 수정 지시 > **핵심**: "평가위원이 왜 낮은 점수를 줬는가?" 를 Human이 명확히 이해
- ```python async def mock_evaluation_analysis(state: ProposalState) -> dict: """평가위원 평가의견 정렬 & 분석"""
- ```python class ProposalState(TypedDict): # ... 기존 필드들 ...
