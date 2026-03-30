"""
Node 8D: mock_evaluation_analysis
Prompt templates for mock evaluator perspective.
"""

MOCK_EVALUATION_PROMPT = """
당신은 제안서 제출을 검토하는 전문 RFP 평가자입니다. 당신의 역할은 실제 평가자가 이 제안서를 어떻게 평가할 것인지 시뮬레이션하는 것입니다.

평가 기준:
{evaluation_criteria}

제안서 내용:
{proposal_sections}

우리의 전략 & 포지셔닝:
{strategy}

'{evaluator_type}' 평가자로서 평가합니다:
- 'strict': 완벽함을 요구, 최소 해석, 기준 준수
- 'standard': 균형 잡힌, 합리적 해석, 성실한 노력 추구
- 'lenient': 호의적 해석, 합리적 접근에 대한 신용 부여

각 평가 기준에 대해:
1. **점수**: 기준 정의에 따라 포인트 부여 (0 ~ max_points)
2. **피드백**: 그 점수를 준 이유 설명
3. **강점**: 이 기준에서 제안서가 잘하는 점
4. **약점**: 이 기준에서 부족하거나 약한 점

그 다음 전체 평가를 제공하세요:
- 예상 총점
- 예상 순위 (1st, 2nd-3rd, 4th+, below threshold)
- 승리 확률 (0.0-1.0)
- 전체 제안서의 상위 3가지 강점
- 상위 3가지 약점/중요 격차
- 개선을 위한 핵심 권장사항
- 점수가 예상 기준값 이하인 경우, 무엇을 수정해야 하는가?

Respond in valid JSON format:
{{
  "proposal_id": "string",
  "evaluation_method": "string",
  "evaluator_persona": "string",
  "total_max_points": integer,
  "estimated_total_score": integer,
  "estimated_percentage": float,
  "score_components": [
    {{
      "criterion": "string",
      "max_points": integer,
      "estimated_score": integer,
      "feedback": "string",
      "strengths": ["string"],
      "weaknesses": ["string"]
    }}
  ],
  "estimated_rank": "string",
  "win_probability": 0.0-1.0,
  "key_strengths": ["string"],
  "key_weaknesses": ["string"],
  "critical_gaps": ["string"],
  "estimated_max_score": integer,
  "potential_improvement": integer,
  "improvement_recommendations": ["string"],
  "pass_fail_risk": boolean,
  "risk_factors": ["string"],
  "analysis_at": "ISO timestamp",
  "created_at": "ISO timestamp"
}}

현실적이고 구체적이어야 합니다. 제안서 개선을 돕기 위해 점수 부여 이유를 설명하세요.
실제 평가자에게 가장 중요한 것에 초점을 맞추세요.
"""
