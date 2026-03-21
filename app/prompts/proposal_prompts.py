"""
제안서 섹션 작성 + 자가진단 프롬프트 (§9, §8, STEP 4)

케이스 A(자유양식) / 케이스 B(서식 지정) 분기.
자가진단 4축 평가: 컴플라이언스 + 전략 일관성 + 품질 + 근거 신뢰성.
v3.2: 자가점검 체크리스트 포함.
"""

# ── 케이스 A: 자유 양식 ──
PROPOSAL_CASE_A_PROMPT = """다음 평가 항목에 대한 제안서 섹션을 작성하세요.

## 섹션 정보
섹션 ID: {section_id}
케이스: A (자유 양식)

## RFP 분석
{rfp_summary}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
핵심 메시지: {key_messages}

## 포지셔닝 전략 가이드
{positioning_guide}

## 스토리라인 가이드
{storyline_guide}

## 지시사항
1. 평가위원이 쉽게 점수를 줄 수 있는 구조로 작성
2. 핵심 메시지를 섹션 도입부와 결론에 반복
3. 구체적 근거(수치, 사례, 실적) 포함
4. 포지셔닝에 맞는 톤앤매너 유지
5. 제안서 분량 규격 준수: {volume_spec}

## v3.2: 자가점검 체크리스트
작성 후 아래 항목을 점검하세요:
- [ ] RFP 요구사항과의 정합성 (1:1 대응 확인)
- [ ] Win Theme 핵심 메시지가 본문에 반영되었는가
- [ ] 구체적 수치/근거가 포함되었는가
- [ ] 평가 배점에 비례하는 분량인가
- [ ] 경쟁사 대비 차별화 포인트가 드러나는가

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 내용 (Markdown 형식, 표·그림 포함)",
  "self_check": {{
    "rfp_alignment": true,
    "win_theme_reflected": true,
    "evidence_included": true,
    "volume_appropriate": true,
    "differentiation_clear": true
  }}
}}
"""


# ── 케이스 B: 서식 지정 ──
PROPOSAL_CASE_B_PROMPT = """발주기관 지정 서식에 맞춰 제안서 섹션을 작성하세요.

## 섹션 정보
섹션 ID: {section_id}
케이스: B (지정 서식)

## 서식 구조 (원본 보존 필수)
{template_structure}

## RFP 분석
{rfp_summary}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
핵심 메시지: {key_messages}

## 포지셔닝 전략 가이드
{positioning_guide}

## 지시사항
1. **서식 구조(제목·번호·항목)를 정확히 보존**하고 내용만 채우세요
2. 서식에 없는 항목을 임의로 추가하지 마세요
3. 표 형식이 지정된 경우 표 구조를 유지하세요
4. 분량 제한이 있으면 정확히 지키세요

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "서식 원본 제목",
  "content": "서식 구조 보존 + 내용 채움 (Markdown)",
  "template_preserved": true,
  "self_check": {{
    "template_structure_preserved": true,
    "no_extra_items_added": true,
    "table_format_maintained": true,
    "volume_within_limit": true
  }}
}}
"""


# ── 자가진단 프롬프트 (§8) ──
SELF_REVIEW_PROMPT = """제안서 전체를 4축으로 자가진단하세요.

## 제안서 섹션 목록
{sections_summary}

## RFP 요구사항
{rfp_requirements}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
핵심 메시지: {key_messages}

## Compliance Matrix
{compliance_matrix}

## 4축 평가 기준 (각 25점, 합계 100점)

### 1축: 컴플라이언스 (25점)
- RFP 필수 요건 충족 여부
- 평가 항목별 1:1 대응 확인
- 누락 요건 식별

### 2축: 전략 일관성 (25점)
- Win Theme이 전 섹션에 일관되게 반영되었는가
- 포지셔닝에 맞는 톤앤매너가 유지되었는가
- Ghost Theme이 은연중 전달되는가

### 3축: 작성 품질 (25점)
- 논리 구조의 명확성
- 구체성 (수치·사례·도표) — 섹션당 구체적 근거 3개 미만이면 감점
- 가독성 (소제목·불릿·표)
- 분량 적정성 — 배점 대비 너무 얇은 섹션(최소 분량 미달)이 있으면 감점
- 표/다이어그램 밀도 — 섹션당 최소 1개 포함 여부 확인

### 4축: 근거 신뢰성 (25점, v3.0)
- 인용된 수치·통계의 출처 명시 여부
- 수행실적과 현 과제의 관련성
- 제안 방법론의 학술적·실무적 타당성

## v3.2: 3-페르소나 시뮬레이션
다음 3가지 관점에서 각각 평가하세요:
1. **호의적 평가위원**: 장점 중심, 긍정 평가
2. **비판적 평가위원**: 약점·논리 허점 집중 탐색
3. **실무 전문가**: 실현 가능성·구체성 검증

## 출력 형식 (JSON)
{{
  "total": 0,
  "compliance_score": 0,
  "strategy_score": 0,
  "quality_score": 0,
  "trustworthiness": {{
    "trustworthiness_score": 0,
    "source_citations": 0,
    "relevance_of_track_record": 0,
    "methodology_validity": 0
  }},
  "section_scores": [
    {{
      "section_id": "...",
      "score": 0,
      "strengths": ["..."],
      "weaknesses": ["..."],
      "improvement_suggestions": ["..."],
      "depth_metrics": {{
        "evidence_count": 0,
        "tables_or_diagrams": 0,
        "estimated_pages": 0.0,
        "min_pages_met": true
      }}
    }}
  ],
  "persona_reviews": {{
    "favorable": "호의적 평가 요약",
    "critical": "비판적 평가 요약",
    "practical": "실무 전문가 평가 요약"
  }},
  "overall_assessment": "종합 평가",
  "critical_issues": ["즉시 수정 필요 사항"],
  "compliance_gaps": ["미충족 요건"]
}}
"""


# ── PPT 프롬프트 ──
PPT_SLIDE_PROMPT = """제안서 섹션을 PPT 슬라이드로 변환하세요.

## 섹션 내용
{section_content}

## 전략
Win Theme: {win_theme}
핵심 메시지: {key_messages}

## 발표 전략 (v3.2)
{presentation_strategy}

## 지시사항
1. 한 슬라이드에 핵심 메시지 1개
2. 불릿포인트 5개 이내
3. 시각적 요소(차트, 다이어그램) 제안
4. 발표자 노트 포함

## 출력 형식 (JSON)
{{
  "slide_id": "{slide_id}",
  "title": "슬라이드 제목",
  "content": "본문 (Markdown, 불릿포인트)",
  "visual_suggestion": "시각 요소 제안",
  "notes": "발표자 노트",
  "duration_seconds": 120
}}
"""


# ── 발표전략 프롬프트 (v3.2, §29) ──
PRESENTATION_STRATEGY_PROMPT = """제안서 발표 전략을 수립하세요.

## RFP 분석
{rfp_summary}
평가 방식: {eval_method}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}

## 제안서 섹션 요약
{sections_summary}

## 과거 발표 Q&A 패턴 (유사 사업/발주기관)
{past_qa_context}

## 지시사항
1. 시간 배분 전략 (발표 시간 / 질의응답)
2. 발표 구조 (도입-본론-결론)
3. 핵심 메시지 전달 순서
4. Q&A 예상 질문 + 답변 전략 (과거 Q&A 패턴을 분석하여 빈출 질문 우선 대비)
5. 시각 전략 (강조 슬라이드, 인포그래픽)

## 출력 형식 (JSON)
{{
  "time_allocation": {{
    "presentation": 0,
    "qa": 0,
    "total": 0
  }},
  "structure": [
    {{
      "phase": "도입",
      "duration_min": 3,
      "key_messages": ["..."],
      "slides": ["slide_ids"]
    }}
  ],
  "qa_strategy": [
    {{
      "expected_question": "예상 질문",
      "answer_strategy": "답변 전략",
      "supporting_slide": "참조 슬라이드"
    }}
  ],
  "visual_strategy": {{
    "highlight_slides": ["강조 슬라이드"],
    "infographic_suggestions": ["인포그래픽 제안"]
  }}
}}
"""
