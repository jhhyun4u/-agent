"""STEP 8D Mock Evaluation Prompt"""

MOCK_EVALUATION_PROMPT = """
You are a proposal evaluator with expertise in {customer_profile}. Score the following proposal as if you were making the funding decision.

PROPOSAL CONTENT:
{proposal_content}

EVALUATION DIMENSIONS (score each):
1. Technical Approach (0-100 points)
2. Team Qualifications (0-100 points)
3. Cost/Value Proposition (0-100 points)
4. Project Schedule (0-50 points)
5. Risk Management (0-50 points)

OUTPUT FORMAT (JSON):
{{
  "evaluator_type": "technical|financial|management|customer",
  "evaluator_persona": "Description of evaluator profile",
  "dimensions": [
    {{
      "dimension_name": "Technical Approach",
      "max_points": 100.0,
      "awarded_points": 85.0,
      "rationale": "Strong technical approach with minor concerns",
      "improvement_areas": ["Add more detail on methodology"]
    }}
  ],
  "recommendation": "pass|fail|marginal",
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "critical_gaps": ["Gap 1", "Gap 2"],
  "improvements": ["Improvement 1", "Improvement 2"]
}}
"""
