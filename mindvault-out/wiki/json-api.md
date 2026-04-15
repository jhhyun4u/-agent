# json & API 응답 예시
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **json** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - <- has_code_example <- [[api]]
- **API 응답 예시** (C:\project\tenopa proposer\-agent-master\docs\02-design\mock-evaluation-implementation-summary.md) -- 1 connections
  - -> has_code_example -> [[json]]

## Internal Relationships
- API 응답 예시 -> has_code_example -> json [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 json, API 응답 예시를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 mock-evaluation-implementation-summary.md이다.

### Key Facts
- **효율성 최적화** - 섹션은 상위 12개만 요약 (토큰 절약) - 평가항목당 1회 AI 호출 (평가위원 성향 시뮬레이션) - JSON 응답 포맷 지정 (파싱 안정성) - 온도 낮음 (0.3) → 일관성 확보
- ```json { "mock_evaluation_result": { "evaluation_metadata": { "total_evaluators": 6, "final_score": 72.5, "win_probability": "보통 (70-84점)" }, "evaluation_items": { "T1": { "item_title": "기술혁신성", "average_score": 18.3, "consensus": { "consensus_level": "높음", "stdev": 2.1 } } }, "strengths": ["강점1",…
