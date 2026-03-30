"""STEP 8F Write Next V2 Prompt"""

WRITE_NEXT_V2_PROMPT = """
You are a proposal writer. Rewrite the following proposal section based on feedback and validation findings.

SECTION: {section_name}
CURRENT CONTENT:
{current_content}

IMPROVEMENT ACTIONS:
{improvement_actions}

FEEDBACK:
{feedback}

TASK:
1. Incorporate feedback into the section
2. Improve clarity and evidence
3. Maintain consistent tone
4. Ensure section flows naturally into next section

OUTPUT FORMAT (JSON):
{{
  "content": "Improved section content in Markdown",
  "word_count": 500,
  "quality_improvement": 15.0,
  "changes_summary": "Summary of changes made",
  "feedback_incorporated": ["Feedback item 1", "Feedback item 2"],
  "ready_for_validation": true
}}
"""
