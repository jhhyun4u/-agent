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


# v3.3: 포지셔닝별 전술적 대안 프레임워크
# STEP 2가 생성할 대안들은 포지셔닝 내에서의 전술적 변형입니다.
POSITIONING_TACTICAL_ALTERNATIVES = {
    "defensive": {
        "description": "수성 포지셔닝 내 2가지 전술적 변형",
        "alternative_a": {
            "name": "Trusted Legacy",
            "concept": "과거 성공과 신뢰도를 최대로 강조",
            "key_focus": ["과거 수행실적 강조", "기관과의 관계 깊이", "연속성 및 안정성", "리스크 최소화"],
            "ghost_theme_angle": "새로운 팀의 미검증 경험 vs 우리의 증명된 노하우",
            "win_theme_focus": "정부기관/대형기관 40+건 수행실적, 누적 SLA 달성률 99.98%, 평가 신뢰도 #1",
            "price_approach": "신뢰프리미엄 (높은 낙찰률)",
        },
        "alternative_b": {
            "name": "Proven Excellence",
            "concept": "운영 우수성과 품질 우수 메트릭을 강조",
            "key_focus": ["품질 메트릭 (99.95%+ SLA)", "자격증 및 인증", "운영 효율성", "프로세스 성숙도"],
            "ghost_theme_angle": "경쟁사의 높은 초기 구축비용 vs 우리의 TCO 최적화",
            "win_theme_focus": "5년 운영 우수성 증명, 자동화로 인력 30% 절감, ISO 인증 및 정부기관 선호도",
            "price_approach": "효율성프리미엄 (적정 낙찰률)",
        },
    },
    "offensive": {
        "description": "공격 포지셔닝 내 2가지 전술적 변형",
        "alternative_a": {
            "name": "Aggressive Innovation",
            "concept": "기술 혁신을 공격적으로 리드",
            "key_focus": ["최신 기술 도입", "차별화된 방법론", "혁신적 인력 구성", "성능 향상 극대화"],
            "ghost_theme_angle": "경쟁사의 매너리즘과 보수성 vs 우리의 혁신과 도전 정신",
            "win_theme_focus": "마이크로서비스 아키텍처 5건+, 클라우드 네이티브 전환 3년 경험, 성능 50% 향상 증명",
            "price_approach": "혁신프리미엄 (경쟁가격으로 진입)",
        },
        "alternative_b": {
            "name": "Smart Innovation",
            "concept": "신중한 혁신 (검증된 부분 + 차별화 부분 조화)",
            "key_focus": ["검증된 기술 + 신규 기술 균형", "계산된 리스크 취하기", "학습 곡선 최소화", "단계적 전환"],
            "ghost_theme_angle": "경쟁사의 보수적 접근 vs 우리의 균형잡힌 혁신",
            "win_theme_focus": "3년 클라우드 경험 + 단계적 마이그레이션 방법론, 위험 30% 감소, 초기 비용 효율성",
            "price_approach": "경쟁력프리미엄 (합리적 낙찰률)",
        },
    },
    "adjacent": {
        "description": "인접 포지셔닝 내 2가지 전술적 변형",
        "alternative_a": {
            "name": "Experience Transfer",
            "concept": "인접 분야 전문성의 자연스러운 확장을 강조",
            "key_focus": ["관련 분야 실적 전이", "도메인 지식의 신속한 습득", "팀의 학습 곡선 최소화", "기존 성공 사례"],
            "ghost_theme_angle": "이 분야의 미경험 팀 vs 관련 분야 깊은 전문성을 가진 우리",
            "win_theme_focus": "비슷한 기술 스택 5건, 도메인 이해도 3년, 업계 트렌드 선도 경험",
            "price_approach": "확장프리미엄 (기존 실적 대비 합리적 가격)",
        },
        "alternative_b": {
            "name": "Synergy Play",
            "concept": "두 분야의 시너지로 독특한 가치 창출",
            "key_focus": ["두 분야의 융합 역량", "타 분야의 best practice 도입", "경쟁사 대비 독특한 가치", "혁신적 통합 설계"],
            "ghost_theme_angle": "한 분야 전문가 vs 두 분야 경험으로 만든 독특한 해법을 제시하는 우리",
            "win_theme_focus": "2개 분야 경험 5+년, 통합 설계로 비용 20% 절감, 업계 사례 3건 성공 증명",
            "price_approach": "가치프리미엄 (차별화 기반 가격)",
        },
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


# 전략 수립 메인 프롬프트 (v3: 포지셔닝별 전술적 대안 생성)
# STEP 2는 Go/No-Go에서 결정된 포지셔닝을 입력받아, 그 포지셔닝 내에서 2+ 전술적 변형을 제시합니다.
STRATEGY_GENERATE_PROMPT = """## MANDATORY: PURE JSON OUTPUT — NO MARKDOWN

응답은 {를 시작으로 } 로 끝나는 VALID JSON만 출력하세요.
- 마크다운 코드블록 NO
- 다른 설명 NO
- 순수 JSON ONLY

마지막 줄에 반드시 }} 를 출력하세요 (이중 중괄호).
```json``` 로 시작하지 말 것. { 로 시작할 것.

## POSITIONING 고정: {positioning}

Go/No-Go 단계에서 이미 포지셔닝이 결정되었습니다.
당신의 역할: {positioning} 전략 내에서 2+ 전술적 변형(alternatives)을 제시하는 것입니다.
(예: 공격형이면 "적극공격" vs "신중공격", 수성형이면 "신뢰강화" vs "안정성강조" 등)

주의: alternatives 배열에 반드시 2개 이상의 완전한 객체를 포함하세요. 1개만 있으면 검증 실패합니다.

## REQUIRED STRUCTURE: {positioning} 포지셔닝 내 2+ ALTERNATIVES

{{
  "positioning": "{positioning}",
  "positioning_rationale": "근거 (200자)",
  "alternatives": [
    {{
      "alt_id": "A_Approach1",
      "alt_name": "첫번째전술",
      "ghost_theme": "경쟁사약점 (50자)",
      "win_theme": "우리승점 (150자)",
      "action_forcing_event": "강제사건 (30자)",
      "key_messages": ["메시지1", "메시지2", "메시지3", "메시지4"],
      "price_strategy": {{"approach": "premium", "target_ratio": 0.88, "rationale": "가격근거"}},
      "risk_assessment": {{"key_risks": ["위험1"], "mitigation": ["대응1"]}}
    }},
    {{
      "alt_id": "B_Approach2",
      "alt_name": "두번째전술",
      "ghost_theme": "경쟁사약점2 (50자)",
      "win_theme": "우리승점2 (150자)",
      "action_forcing_event": "강제사건2 (30자)",
      "key_messages": ["메시지1", "메시지2", "메시지3", "메시지4"],
      "price_strategy": {{"approach": "stability", "target_ratio": 0.92, "rationale": "가격근거"}},
      "risk_assessment": {{"key_risks": ["위험1"], "mitigation": ["대응1"]}}
    }}
  ],
  "focus_areas": [{{"area": "핵심", "weight": 50, "strategy": "전략"}}],
  "competitor_analysis": {{"swot_matrix": [], "scenarios": {{"best_case": "우리우위", "base_case": "균형", "worst_case": "경쟁강화"}}}},
  "research_framework": {{"research_questions": ["Q1"], "methodology_rationale": ["근거"]}}
}}

---

## CONTEXT

RFP 분석 요약: {rfp_summary}

Go/No-Go 결과 (포지셔닝 이미 결정됨):
- 포지셔닝: {positioning} ({positioning_label})
- 판정 근거: {positioning_rationale}
- 핵심 승부수: {strategic_focus}
- 강점: {pros}
- 리스크: {risks}

포지셔닝 가이드: {positioning_guide}

자사 역량: {capabilities_text}

발주기관 인텔리전스: {client_intel_text}

경쟁 환경: {competitor_text}

과거 교훈: {lessons_text}

{competitive_analysis_framework}

{strategy_research_framework}

## FINAL CRITICAL REQUIREMENT

[최고 우선순위] alternatives 배열에 2+ 대안 포함:

1. alt_id: "A_[전술1이름]" 형식
2. alt_id: "B_[전술2이름]" 형식

1개만 있으면 자동 검증 실패. 반드시 2개 이상 완전한 객체를 배열에 포함하세요.

각 대안 필수 필드:
- alt_id: A_ 또는 B_로 시작 (e.g., "A_Aggressive_Innovation")
- alt_name: 전술 이름 (e.g., "Aggressive Innovation (공격적 혁신)")
- ghost_theme: 경쟁사 약점 (최소 50자)
- win_theme: 우리 승리 포인트 (최소 150자)
- action_forcing_event: 의사결정 강제 (최소 30자)
- key_messages: 배열, 4개 메시지 (각 50~100자)
- price_strategy: {{approach: "...", target_ratio: 0.XX, rationale: "..."}}
- risk_assessment: {{key_risks: [...], mitigation: [...]}}
"""
