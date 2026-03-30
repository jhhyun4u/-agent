"""
Node 8E: mock_evaluation_feedback_processor
Prompt templates for feedback prioritization.
"""

FEEDBACK_PROCESSING_PROMPT = """
당신은 제안서 개선 전략가입니다. 당신의 업무는 원본 평가 결과를 가져와 제안서 개선을 위한 실행 가능하고 우선순위가 정해진 피드백으로 전환하는 것입니다.

모의 평가 결과:
{mock_eval_result}

현재 제안서 섹션:
{proposal_sections}

RFP 요구사항:
{rfp_analysis}

평가 피드백을 전략적으로 처리하세요:

1. **중요 격차 식별** (반드시 수정해야 할 사항):
   - 점수를 잃거나 실패를 유발하는 문제
   - 누락된 필수 요구사항
   - 포지셔닝의 치명적 결함

2. **개선 기회 식별** (강화할 사항):
   - 개선 가능한 중간 점수 기준
   - 약한 강점 표현
   - 누락된 증거 또는 사례

3. **문제가 있는 각 섹션에 대해**:
   - 구체적 재작성 지침 (변경/추가할 사항)
   - 개선을 위한 예시 또는 접근법
   - 노력 추정 (quick/medium/complex)
   - 점수에 미치는 예상 영향

4. **영향도별 우선순위 지정**:
   - 점수 영향 (수정 시 얻을 수 있는 포인트 수)
   - 필요한 노력 (구현 시간)
   - 우선순위 = 영향도 / 노력 비율

5. **개선 추정**:
   - 모든 문제가 해결되면 새로운 예상 점수는?
   - 새로운 순위는 어떻게 될 것인가?

6. **일정 계획**:
   - 중요 격차를 해결하는 데 얼마나 걸릴 것인가? (시간 또는 일)
   - 모든 개선사항을 구현하는 데 얼마나 걸릴 것인가?
   - 중요 경로: 만족할 수 있는 점수로 가는 가장 빠른 경로

Respond in valid JSON format:
{{
  "proposal_id": "string",
  "critical_gaps": [
    {{
      "section_id": "string",
      "section_title": "string",
      "issue_category": "string",
      "priority": 1-10,
      "issue_description": "string",
      "rewrite_guidance": "string",
      "example_improvement": "string or null",
      "estimated_effort": "string"
    }}
  ],
  "improvement_opportunities": [...],
  "section_feedback": {{"section_id": ["feedback items"]}},
  "highest_impact_issues": ["string"],
  "rewrite_strategy": "string",
  "affected_sections": ["string"],
  "estimated_total_effort": "string",
  "critical_path_effort": "string",
  "estimated_score_improvement": integer,
  "estimated_new_score": integer,
  "estimated_new_rank": "string",
  "recommended_timeline": "string",
  "processed_at": "ISO timestamp",
  "created_at": "ISO timestamp"
}}

실용적이고 정직해야 합니다. 실제로 평가 점수를 개선할 변화에 초점을 맞추세요.
"""
