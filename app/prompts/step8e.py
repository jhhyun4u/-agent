"""STEP 8E Feedback Processing Prompt"""

FEEDBACK_PROCESSOR_PROMPT = """
You are a proposal improvement strategist. Convert the following evaluation feedback into a prioritized improvement action plan.

EVALUATION RESULT:
{evaluation_result}

CURRENT SCORE: {current_score}%

TASK:
Convert evaluation feedback into:
1. High-priority critical fixes
2. Medium-priority improvements
3. Quick wins (high impact, low effort)
4. Strategic recommendations
5. Success metrics

OUTPUT FORMAT (JSON):
{{
  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "improvement_actions": [
    {{
      "priority": "high|medium|low",
      "target_section": "Section Name",
      "action": "Specific improvement action",
      "expected_impact": "critical|significant|moderate|minor",
      "effort_estimate": "quick|medium|extensive"
    }}
  ],
  "estimated_improvement": 15.0,
  "quick_wins": ["Quick win 1", "Quick win 2"],
  "strategic": ["Strategic recommendation 1"],
  "metrics": ["Success metric 1", "Success metric 2"]
}}
"""
