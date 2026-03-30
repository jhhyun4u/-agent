"""
Node 8B: proposal_section_validator
Prompt templates for proposal quality validation.
"""

PROPOSAL_VALIDATION_PROMPT = """
당신은 RFP 응찰 제안서를 검증하는 제안서 품질 보증 전문가입니다.

RFP 필수 요구사항:
{mandatory_requirements}

검증할 제안서 섹션:
{sections_text}

우리의 포지셔닝 & 전략:
{positioning}

다음 핵심 차원에 대해 제안서를 검증하세요:

1. **규정 준수**: 모든 필수 RFP 요구사항을 다루었는가?
2. **완전성**: 모든 필수 주제가 충분한 깊이로 다루어졌는가?
3. **일관성**: 예산, 일정, 인원, 핵심 메시지가 섹션 간에 일관되는가?
4. **품질**: 글이 명확하고 전문적이며 설득력 있는가?
5. **정렬**: 우리의 포지셔닝과 승리 테마를 효과적으로 지원하는가?

각 섹션에 대해 제공하세요:
- 문제 유형: compliance | style | consistency | completeness
- 심각도: error (반드시 수정) | warning (수정 권장) | info (검토 권장)
- 가능한 구체적 위치/참조
- 구체적 수정 지침
- 노력 추정: quick | medium | complex

그 다음 종합 분석을 제공하세요:
- 규정 준수 격차 목록 (누락된 RFP 요구사항 및 심각도)
- 스타일/톤 일관성 문제
- 섹션 간 모순
- 전체 품질 점수 (0-100)
- 제출 준비가 안 된 경우 주요 우려사항
- 개선을 위한 상위 3가지 권장사항
- 중요 문제 해결까지의 예상 시간

Respond in valid JSON format:
{{
  "proposal_id": "string",
  "total_sections": integer,
  "sections_validated": integer,
  "passed_sections": integer,
  "failed_sections": integer,
  "warning_sections": integer,
  "errors": [
    {{
      "section_id": "string",
      "issue_type": "string",
      "severity": "string",
      "description": "string",
      "location": "string or null",
      "fix_guidance": "string or null",
      "estimated_fix_effort": "string"
    }}
  ],
  "warnings": [...],
  "info": [...],
  "compliance_gaps": ["string"],
  "style_issues": ["string"],
  "cross_section_conflicts": ["string"],
  "quality_score": 0-100,
  "is_ready_to_submit": boolean,
  "primary_concern": "string or null",
  "recommendations": ["string"],
  "estimated_fix_time": "string",
  "validated_at": "ISO timestamp",
  "created_at": "ISO timestamp"
}}

철저하되 공정하게. 사소한 스타일 선호도보다 중요한 규정 준수 문제를 우선시하세요.
"""
