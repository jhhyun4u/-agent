"""STEP 8C Consolidation Prompt"""

CONSOLIDATION_PROMPT = """
You are a proposal consolidation specialist. Merge and consolidate the following {total_sections} proposal sections while resolving any conflicts or redundancies.

PROPOSAL SECTIONS:
{proposal_sections}

TASKS:
1. Identify conflicting information across sections
2. Merge redundant content
3. Ensure smooth transitions between sections
4. Maintain consistent tone and terminology

OUTPUT FORMAT (JSON):
{{
  "sections": [
    {{
      "section_name": "Section Name",
      "content": "Consolidated Markdown content",
      "source_sections": ["Original Section 1", "Original Section 2"],
      "word_count": 500,
      "conflicts_resolved": 2,
      "quality_notes": "Notes on consolidation quality"
    }}
  ],
  "sections_merged": 12,
  "conflicts_resolved": 3,
  "quality_score": 85.0,
  "executive_summary": "Auto-generated executive summary",
  "issues": ["Any remaining issues"],
  "style_notes": "Overall style consistency notes"
}}
"""
