"""
STEP 2 제안 전략 수립 프롬프트 (v2 - 간소화 버전)

핵심: 정확히 2개 이상의 전략 대안 생성 (JSON-ONLY 출력)
토큰 예산: 8,000
"""

# 간소화된 STEP 2 프롬프트
STRATEGY_GENERATE_PROMPT_V2 = """## MANDATORY: JSON-ONLY OUTPUT

당신의 모든 응답은 다음 형식의 VALID JSON으로만 구성되어야 합니다.
다른 텍스트, 설명, 마크다운 코드블록 없음. 순수 JSON만 출력하세요.

## COMPLETE EXAMPLE (2 ALTERNATIVES - YOU MUST FOLLOW THIS STRUCTURE)

{{
  "positioning": "{positioning}",
  "positioning_rationale": "{positioning_rationale}. 기술 혁신과 안정성 모두 겸비.",
  "alternatives": [
    {{
      "alt_id": "A_OFFENSIVE",
      "ghost_theme": "경쟁사는 기존 온프레미스 기반으로 클라우드 전환 경험 부족. 마이크로서비스 설계 역량이 입증되지 않음.",
      "win_theme": "우리는 마이크로서비스 아키텍처 5건 이상의 수행 경험과 Kubernetes 클러스터 운영 경험 3년, AWS/Azure 멀티클라우드 통합 경험으로 클라우드 네이티브 전환을 가장 안정적으로 추진할 수 있다. 초저지연 네트워크 설계 기술로 99.95% SLA 보증 가능하며, DevOps 통합으로 운영 인력 30% 절감 달성.",
      "action_forcing_event": "정부 클라우드 정책(2026년) + 레거시 시스템 EOL(2027년) → 2026년 내 의사결정 필수. 지연 시 레거시 유지비 연 ₩50M 이상 소모.",
      "key_messages": [
        "클라우드 네이티브로 즉시 50% 성능 향상 (경험 기반 보장)",
        "자동 스케일링으로 연간 ₩200M 비용 절감 (TCO 분석 수행)",
        "DevOps 통합으로 운영 인력 30% 절감 (자동화 도입)",
        "24/7 SLA 99.95% 보장 (5년 누적 달성률 기준)",
        "정부기관 3곳 클라우드 도입 사례 (2019년 이후 운영 중)"
      ],
      "price_strategy": {{
        "approach": "innovation_premium",
        "target_ratio": 0.88,
        "rationale": "기술 혁신으로 프리미엄 정당화. 시장 평균 대비 경쟁 가격으로 진입 확보"
      }},
      "risk_assessment": {{
        "key_risks": [
          "마이그레이션 복잡도 (400+ 애플리케이션)",
          "레거시 호환성 이슈 (20% 위험율)",
          "운영팀 학습곡선 (3개월)"
        ],
        "mitigation": [
          "단계적 마이그레이션 (Phase 1-3, 각 4개월)",
          "호환성 계층 구축 (Bridge Layer)",
          "6주 교육 프로그램 (50명 운영팀)"
        ]
      }}
    }},
    {{
      "alt_id": "B_DEFENSIVE",
      "ghost_theme": "새로운 팀의 클라우드 경험 미검증. 초기 구축비용 높음 (ROI 불명확).",
      "win_theme": "우리는 정부기관 40건 이상의 수행실적과 국내 최초 클라우드 도입 3곳을 성공적으로 운영(2019년 이후 운영 중). 5년 누적 SLA 달성률 99.98%로 안정성 입증. 정부 기관의 신뢰와 이해도를 바탕으로 클라우드 전환을 가장 안정적으로 추진할 수 있다.",
      "action_forcing_event": "ISMS 인증 의무화(2026.07) → 지금부터 운영 체계 수립 필수. 준비 기간 부족 시 인증 불가.",
      "key_messages": [
        "정부기관 신뢰도 #1: 40건 이상의 수행실적 (AURI 등록)",
        "안정적 운영: 5년 99.98% SLA 달성 (누적 기록)",
        "검증된 아키텍처: 초기 위험 최소화 (사례 기반)",
        "교육·지원 풀 투입: 안정적 전환 보장 (50명 교육팀)",
        "ISMS/보안: 정부 규정 준수 확인 (인증 기관 파트너)"
      ],
      "price_strategy": {{
        "approach": "stability_premium",
        "target_ratio": 0.92,
        "rationale": "신뢰·안정성으로 높은 낙찰률 기대. 정부기관 선호 포지셔닝"
      }},
      "risk_assessment": {{
        "key_risks": [
          "높은 초기 구축비용 (ROI 3년)",
          "기술 최신성 부족 (관리형 서비스)",
          "향후 확장성 제약"
        ],
        "mitigation": [
          "분할 납부 조건 협상",
          "업그레이드 계약 포함",
          "확장 옵션 사전 설계"
        ]
      }}
    }}
  ],
  "focus_areas": [
    {{"area": "기술 혁신", "weight": 35, "strategy": "클라우드 네이티브 아키텍처"}},
    {{"area": "안정성·신뢰", "weight": 35, "strategy": "99.95% SLA 보증 + 정부기관 경험"}},
    {{"area": "비용 효율", "weight": 20, "strategy": "연간 ₩200M 절감 + 인력 30% 감소"}},
    {{"area": "위험 관리", "weight": 10, "strategy": "단계적 마이그레이션 + 교육"}}
  ],
  "competitor_analysis": {{
    "swot_matrix": [
      {{"competitor": "경쟁사A (기존 온프레미스)", "strength": "낮은 구축비", "weakness": "클라우드 경험 부족", "opportunity": "정부 마이그레이션 정책", "threat": "우리의 기술 우위"}}
    ],
    "scenarios": {{
      "best_case": "우리 기술 차별화 강조 → Offensive 전략 선택 → 경쟁가격 (낙찰률 88%)",
      "base_case": "기술과 신뢰 균형 → 기술과 안정성 혼합 → 적정가격 (낙찰률 90%)",
      "worst_case": "경쟁사 가격 공격 → Defensive 강조 → 신뢰도 우위 (낙찰률 92%)"
    }}
  }},
  "research_framework": {{
    "research_questions": [
      "정부 클라우드 마이그레이션 시 가장 큰 우려사항은? → SLA/안정성",
      "클라우드 아키텍처 선택의 핵심 평가 기준은? → 성능/비용/안정성",
      "운영팀 전환의 주요 장벽은? → 기술 학습곡선"
    ],
    "methodology_rationale": [
      "학술 타당성: 마이크로서비스 아키텍처는 클라우드 전환의 표준 (AWS/Azure 가이드 준수)",
      "실무 실현가능성: 5년 경험 + 50명 교육팀 확보 → 12개월 내 완료 가능",
      "차별성: 경쟁사 대비 클라우드 네이티브 경험 5배 이상"
    ]
  }}
}}

---

## CONTEXT (참고용)

### RFP 분석 요약
{rfp_summary}

### Go/No-Go 결과
포지셔닝: {positioning} ({positioning_label})
판정 근거: {positioning_rationale}
핵심 승부수: {strategic_focus}
강점: {pros}
리스크: {risks}

### 자사 역량
{capabilities_text}

### 발주기관 인텔리전스
{client_intel_text}

### 경쟁 환경
{competitor_text}

### 과거 교훈
{lessons_text}

---

## FINAL REQUIREMENT (반드시 준수)

1. **VALID JSON ONLY** — 다른 텍스트, 코드블록, 설명 금지. 순수 JSON만.
2. **2개 이상 alternatives** — 1개만이면 검증 실패. A와 B 두 가지 완전한 대안 필수.
3. **각 대안의 필수 필드**:
   - alt_id: "A_OFFENSIVE" 또는 "B_DEFENSIVE" 형식
   - ghost_theme: 경쟁사 약점 (최소 50자)
   - win_theme: 우리의 승리 포인트 (최소 150자)
   - action_forcing_event: 의사결정 강제 사건 (최소 30자)
   - key_messages: 3개 이상 (각 50~100자)
   - price_strategy: approach + target_ratio + rationale
   - risk_assessment: key_risks + mitigation
4. **대안 간 명확한 차별화** — positioning_tone 다르게 (offensive vs defensive)

예: 위의 EXAMPLE을 참고하여 정확히 같은 구조의 JSON을 반드시 2개 alternatives로 생성하세요.
"""
