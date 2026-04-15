# python & 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged)
Cohesion: 0.47 | Nodes: 6

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 4 connections
  - <- has_code_example <- [[5-d-2-d-8-u-2]]
  - <- has_code_example <- [[5-1-1-reviewsectionnode]]
  - <- has_code_example <- [[5-1-2-plan-buildplanreviewcontext]]
  - <- has_code_example <- [[5-1-3-plan-handleplanreview]]
- **5-1. 리뷰 노드 v3.5 변경 (§32-7 merged)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 3 connections
  - -> contains -> [[5-1-1-reviewsectionnode]]
  - -> contains -> [[5-1-2-plan-buildplanreviewcontext]]
  - -> contains -> [[5-1-3-plan-handleplanreview]]
- **5-1-1. review_section_node (신규)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5-1-v35-32-7-merged]]
- **5-1-2. plan 리뷰 강화 (_build_plan_review_context)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5-1-v35-32-7-merged]]
- **5-1-3. plan 리뷰 핸들러 (_handle_plan_review)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5-1-v35-32-7-merged]]
- **5. 리뷰 노드 (단계별 관점 차별화) — D-2, D-8, U-2 해결** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\04-review-nodes.md) -- 1 connections
  - -> has_code_example -> [[python]]

## Internal Relationships
- 5-1-1. review_section_node (신규) -> has_code_example -> python [EXTRACTED]
- 5-1-2. plan 리뷰 강화 (_build_plan_review_context) -> has_code_example -> python [EXTRACTED]
- 5-1-3. plan 리뷰 핸들러 (_handle_plan_review) -> has_code_example -> python [EXTRACTED]
- 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged) -> contains -> 5-1-1. review_section_node (신규) [EXTRACTED]
- 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged) -> contains -> 5-1-2. plan 리뷰 강화 (_build_plan_review_context) [EXTRACTED]
- 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged) -> contains -> 5-1-3. plan 리뷰 핸들러 (_handle_plan_review) [EXTRACTED]
- 5. 리뷰 노드 (단계별 관점 차별화) — D-2, D-8, U-2 해결 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged), 5-1-1. review_section_node (신규)를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 04-review-nodes.md이다.

### Key Facts
- ```python app/graph/nodes/review_node.py from langgraph.types import interrupt from app.graph.state import ProposalState, ApprovalStatus
- 5-1-1. review_section_node (신규)
- ```python def review_section_node(state: ProposalState) -> dict: """섹션별 human 리뷰 게이트.
- plan 리뷰 시 기존 plan 데이터에 추가로 스토리라인 컨텍스트를 제공:
- ```python def _handle_plan_review(state: ProposalState, human_input: dict) -> dict: """plan 리뷰 human 응답 처리.
