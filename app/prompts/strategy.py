"""
전략 수립 프롬프트 (§29-5, STEP 2)

포지셔닝 매트릭스 + SWOT + 시나리오 + 연구질문 + Win Theme.
토큰 예산: 25,000
"""

# 포지셔닝별 전략 가이드
POSITIONING_STRATEGY_MATRIX = {
    "defensive": {
        "label": "수성 (Defensive)",
        "core_message": "기존 신뢰와 실적 강조, 연속성과 안정성",
        "tone": "안정적이고 신뢰할 수 있는",
        "price_approach": "적정가격 — 기존 실적 대비 합리적 가격 제시",
        "ghost_strategy": "경쟁사의 경험 부족, 새로운 팀의 리스크 부각",
        "key_focus": ["수행 실적 강조", "기관 이해도", "연속성·안정성", "리스크 최소화"],
    },
    "offensive": {
        "label": "공격 (Offensive)",
        "core_message": "혁신과 차별화, 새로운 관점과 방법론",
        "tone": "혁신적이고 도전적인",
        "price_approach": "경쟁가격 — 진입을 위한 전략적 가격",
        "ghost_strategy": "기존 수행사의 매너리즘, 새로운 시도 부재 부각",
        "key_focus": ["혁신 방법론", "차별화 포인트", "새로운 가치 제안", "공격적 인력 구성"],
    },
    "adjacent": {
        "label": "인접 (Adjacent)",
        "core_message": "관련 분야 전문성의 자연스러운 확장",
        "tone": "전문적이면서 유연한",
        "price_approach": "합리적 가격 — 관련 실적 기반 비용 효율성 강조",
        "ghost_strategy": "핵심 분야 전문성 대비 타 분야 경험 한계 부각",
        "key_focus": ["관련 분야 실적 전이", "융합 역량", "학습 곡선 최소화", "시너지 효과"],
    },
}


# v3.2: 경쟁분석 프레임워크 (ProposalForge #4)
COMPETITIVE_ANALYSIS_FRAMEWORK = """
## 경쟁분석 프레임워크

### 경쟁사별 SWOT 매트릭스
각 경쟁사에 대해 SWOT 분석 + 대응전략:
| 경쟁사 | S(강점) → 대응 | W(약점) → 공략 | O(기회) → 활용 | T(위협) → 방어 |

### 차별화 포인트 구조
각 차별화 포인트:
- **What**: 무엇이 다른가
- **Why**: 왜 발주기관에 중요한가
- **How**: 어떻게 증명할 것인가
- **Evidence**: 구체적 근거 (수행실적, 특허, 인력 자격 등)

### 경쟁 시나리오별 대응전략
- **Best Case**: 경쟁사 약점 부각 → 공격적 차별화
- **Base Case**: 동등 경쟁 → 가격+품질 균형
- **Worst Case**: 경쟁사 강점 부각 → 방어적 대응
"""

# v3.2: 연구수행 전략 프레임워크 (ProposalForge #7)
STRATEGY_RESEARCH_FRAMEWORK = """
## 연구수행 전략 프레임워크

### 핵심 연구질문(Research Questions) 도출
RFP의 핵심 과업에서 3~5개 연구질문 도출:
- RQ1: [연구질문] → [접근법]

### 연구수행 프레임워크
Phase → Task → Output 구조:
- Phase 1: [명칭] — 핵심 활동, 산출물, 기간

### 방법론 선택 근거
1. **학술 타당성**: 이론적 기반, 선행연구 사례
2. **실무 실현가능성**: 투입인력·기간·예산 내 실행 가능 여부
3. **차별성**: 경쟁사 대비 방법론적 우위
"""


# 전략 수립 메인 프롬프트 (v2: 간소화, JSON-ONLY 강제)
STRATEGY_GENERATE_PROMPT = """## MANDATORY: JSON-ONLY OUTPUT

당신의 모든 응답은 다음 형식의 VALID JSON으로만 구성되어야 합니다.
다른 텍스트, 설명, 마크다운 코드블록 없음. 순수 JSON만 출력하세요.

## REQUIRED STRUCTURE: 2+ ALTERNATIVES (A_OFFENSIVE, B_DEFENSIVE)

{{
  "positioning": "{positioning}",
  "positioning_rationale": "상세 근거 (최소 200자)",
  "alternatives": [
    {{
      "alt_id": "A_OFFENSIVE",
      "ghost_theme": "경쟁사 약점 부각 (최소 50자)",
      "win_theme": "우리의 승리 포인트 — 역량 + 성과 (최소 150자)",
      "action_forcing_event": "의사결정 강제 사건 (최소 30자)",
      "key_messages": ["메시지1 (50~100자)", "메시지2", "메시지3", "메시지4"],
      "price_strategy": {{"approach": "innovation_premium", "target_ratio": 0.88, "rationale": "..."}},
      "risk_assessment": {{"key_risks": ["리스크1", "리스크2"], "mitigation": ["대응1", "대응2"]}}
    }},
    {{
      "alt_id": "B_DEFENSIVE",
      "ghost_theme": "경쟁사 약점 부각 (다른 각도)",
      "win_theme": "우리의 안정성·신뢰도 (최소 150자)",
      "action_forcing_event": "다른 의사결정 강제 요인",
      "key_messages": ["메시지1", "메시지2", "메시지3", "메시지4"],
      "price_strategy": {{"approach": "stability_premium", "target_ratio": 0.92, "rationale": "..."}},
      "risk_assessment": {{"key_risks": ["리스크1"], "mitigation": ["대응1"]}}
    }}
  ],
  "focus_areas": [{{"area": "영역", "weight": 30, "strategy": "접근법"}}],
  "competitor_analysis": {{"swot_matrix": [...], "scenarios": {{"best_case": "...", "base_case": "...", "worst_case": "..."}}}},
  "research_framework": {{"research_questions": [...], "methodology_rationale": [...]}}
}}

---

## CONTEXT (Formatting above must be exact)

RFP 분석 요약: {rfp_summary}

Go/No-Go 결과:
- 포지셔닝: {positioning} ({positioning_label})
- 판정 근거: {positioning_rationale}
- 핵심 승부수: {strategic_focus}
- 강점: {pros}
- 리스크: {risks}

포지셔닝 전략 가이드: {positioning_guide}

자사 역량: {capabilities_text}

발주기관 인텔리전스: {client_intel_text}

경쟁 환경: {competitor_text}

과거 교훈: {lessons_text}

{competitive_analysis_framework}

{strategy_research_framework}

## CRITICAL REQUIREMENT

**반드시 2개 이상의 완전한 alternatives 포함. 1개만 제시하면 검증 실패.**

각 대안:
- alt_id: "A_OFFENSIVE" 또는 "B_DEFENSIVE" (명확한 포지셔닝)
- win_theme: 최소 150자 (역량 + 구체적 성과)
- key_messages: 최소 4개 (각 50~100자)
- price_strategy: approach + target_ratio (offensive: 0.88, defensive: 0.92)
- risk_assessment: 리스크 + 대응책
"""
