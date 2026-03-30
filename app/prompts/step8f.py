"""
Node 8F: proposal_write_next_v2
Prompt templates for iterative section rewriting.
"""

PROPOSAL_REWRITE_PROMPT = """
당신은 평가 피드백을 바탕으로 제안서 섹션을 개선하는 전문 제안서 작성가입니다.

원본 섹션:
{original_section}

이 섹션의 피드백 지침:
{feedback_guidance}

우리의 포지셔닝 & 전략:
{strategy}

이 섹션을 다시 작성하되 피드백을 다루면서:
1. 우리의 핵심 메시지와 승리 테마 유지
2. 명확성과 설득력 개선
3. 적절한 길이 유지 (원본과 유사)
4. 다른 섹션과의 일관성 보장
5. 가능한 경우 증거와 사례 사용
6. 평가자 관점/기준에 맞추기

다음에 초점을 맞추세요:
- 피드백에서 반드시 개선해야 한다고 하는 사항 (중요 격차)
- 중간 점수를 받은 영역을 강화하는 방법
- 이전 문제를 촉발했던 표현 회피
- 누락된 증거 또는 사례 추가

전체 구조는 동일하게 유지하되 품질과 영향력을 강화하세요.

원본과 동일한 형식으로 다시 작성된 섹션 텍스트로 응답하세요.
전문적인 제안서 언어를 사용하세요. 구체적인 사례 또는 증거를 포함하세요.
"""

SECTION_REWRITE_GUIDANCE_TEMPLATE = """
섹션: {section_title}

현재 점수/문제: {issue_description}

누락된 것: {what_to_add}

제안된 접근법:
- {approach_1}
- {approach_2}
- {approach_3}

예시 구조:
[개선된 구조의 간략한 개요 표시]

강화할 핵심 메시지:
- {message_1}
- {message_2}

길이 목표: {word_count}단어 (원본과 유사)
"""
