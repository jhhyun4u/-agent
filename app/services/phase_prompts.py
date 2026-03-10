"""Phase별 Claude API 프롬프트 (v3.5) — 이기는 제안서 가이드라인 반영"""

# ── Phase 2: Analysis ──────────────────────────────────────────────

PHASE2_SYSTEM = """당신은 정부/공공기관 용역 RFP 전략 분석 전문가입니다.
RFP 문서에서 배점 구조, 발주처의 숨은 의도, 필수 충족 요건을 정밀하게 파악합니다.
또한 잠재 경쟁자 구도와 가격 입찰 포지셔닝 전략을 분석합니다.
평가위원의 의사결정 심리와 고득점 판단 기준을 반드시 함께 분석합니다.
응답은 반드시 JSON 형식으로만 제공합니다."""

PHASE2_USER = """다음 RFP 정보를 분석하여 핵심 인사이트를 추출해주세요.

## RFP 요약
{rfp_summary}

## 추가 데이터
{structured_data}

## 나라장터 유사 낙찰 사례 (실데이터 기반 경쟁자 분석)
{g2b_data}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "summary": "분석 결과 3줄 요약",
    "key_requirements": ["핵심 요구사항1", "핵심 요구사항2"],
    "evaluation_weights": {{"기술능력": 40, "수행계획": 30, "가격": 30}},
    "hidden_intent": "발주처가 진짜 원하는 것 (2~3문장)",
    "risk_factors": ["리스크1", "리스크2"],
    "competitor_landscape": {{
        "likely_competitors": ["예상 경쟁자 유형1 (예: 대형 SI 업체)", "유형2 (예: 전문 컨설팅 펌)"],
        "competitor_strengths": ["경쟁자 공통 강점1", "강점2"],
        "competitor_weaknesses": ["경쟁자 공통 약점1", "약점2"],
        "market_positioning": "이 사업의 경쟁 강도 및 시장 특성 설명 (3문장)"
    }},
    "evaluator_perspective": {{
        "decision_criteria": [
            "평가위원이 최우선으로 확인하는 항목1 (배점 고점 요소)",
            "확인 항목2",
            "확인 항목3",
            "확인 항목4",
            "확인 항목5"
        ],
        "preferred_contractor_profile": "발주처/평가위원이 선호하는 도급사 유형과 특성 (2문장)",
        "risk_perception": ["평가위원이 인식할 주요 리스크1", "리스크2", "리스크3"]
    }},
    "our_advantage_opportunities": [
        "우리 강점 × 이 사업 특성 = 활용 기회1 (구체적으로)",
        "활용 기회2",
        "활용 기회3"
    ],
    "price_analysis": {{
        "budget_range": "명시 예산 또는 추정 예산 범위",
        "recommended_bid_range": "추천 입찰 범위 (예: 예산의 85~92%)",
        "price_sensitivity": "high/medium/low - 이 사업에서 가격이 당락에 미치는 영향",
        "price_strategy_rationale": "가격 전략 근거 (배점 구조, 발주처 성향 기반 설명 3문장)"
    }}
}}"""


# ── Phase 3: Plan ──────────────────────────────────────────────────

PHASE3_SYSTEM = """당신은 제안서 전략 수립 전문가입니다.
분석 결과를 바탕으로 경쟁 우위를 가질 수 있는 핵심 전략을 수립합니다.
섹션별 작성 전략과 분량 배분을 구체적으로 제시하고,
경쟁자 대비 차별화 포인트와 최적 입찰가 전략을 확정합니다.
제안서 전체를 관통하는 단일 Win Theme을 도출하고, 각 섹션이 그 테마를 강화하도록 설계합니다.
평가위원이 각 섹션에서 무엇을 확인하는지 명확히 파악하여 설득 포인트를 섹션마다 정의합니다.
응답은 반드시 JSON 형식으로만 제공합니다."""

PHASE3_USER = """다음 분석 결과를 바탕으로 제안서 작성 전략을 수립해주세요.

## 분석 결과
{analysis_summary}

## 핵심 요구사항
{key_requirements}

## 배점 구조
{evaluation_weights}

## 경쟁자 분석
{competitor_landscape}

## 평가위원 관점
{evaluator_perspective}

## 우리의 강점 활용 기회
{our_advantage_opportunities}

## 가격 분석
{price_analysis}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "summary": "전략 요약 3줄",
    "win_strategy": "핵심 차별화 전략 메시지 (3문장 이내)",
    "win_theme": {{
        "primary_message": "제안서 전체를 관통하는 단일 핵심 메시지 (1문장, 예: 'AI 기반 운영 자동화로 귀 기관 디지털 전환을 3개월 앞당깁니다')",
        "rationale": "이 테마가 평가위원/발주처에게 설득력 있는 이유 (2문장)",
        "evidence_pillars": [
            "이 테마를 뒷받침하는 실적/기술/경험 1",
            "근거 2",
            "근거 3"
        ]
    }},
    "business_understanding_strategy": {{
        "explicit_issues": ["RFP에 명시된 발주처 핵심 이슈 1", "이슈 2", "이슈 3"],
        "hidden_issues": [
            "발주처가 언급하지 않은 숨은 문제 1 (산업/정책/기술 트렌드 기반)",
            "숨은 문제 2",
            "숨은 문제 3"
        ],
        "our_unique_perspective": "다른 제안사와 다른 우리만의 관점 (2문장)"
    }},
    "section_plan": [
        {{
            "section": "사업 이해도",
            "approach": "작성 접근 방법",
            "page_limit": 5,
            "priority": "high",
            "evaluator_check_points": [
                "평가위원이 이 섹션에서 확인하는 항목 1",
                "확인 항목 2",
                "확인 항목 3"
            ],
            "win_theme_alignment": "이 섹션이 Win Theme과 연결되는 방식",
            "target_criteria": "이 섹션이 공략하는 평가항목명 (Phase 2 evaluation_weights와 매핑, 예: 기술 이해도)",
            "score_weight": 40
        }}
    ],
    "page_allocation": {{"사업 이해도": 5, "수행 방법론": 10}},
    "team_plan": "투입 인력 구성 계획 (자유 형식 요약)",
    "team_composition": [
        {{"role": "PM", "grade": "특급", "person_months": 6, "labor_type": "SW"}},
        {{"role": "개발자", "grade": "고급", "person_months": 12, "labor_type": "SW"}}
    ],
    "procurement_method": "적격심사",
    "estimated_competitor_count": 5,
    "differentiation_strategy": [
        "경쟁자 대비 차별화 포인트1 (Ghost the Competition — 경쟁사 약점 덮는 방식으로)",
        "차별화 포인트2",
        "차별화 포인트3"
    ],
    "bid_price_strategy": {{
        "value_basis": "발주처가 이 사업에서 인지하는 핵심 가치 (정량적 효과 추정, 예: 업무 효율 30% 향상 = 연 X억 절감)",
        "scenarios": {{
            "bear": {{"price_ratio": "85%", "condition": "경쟁사 3개 이상, 가격 경쟁 심화 시"}},
            "base": {{"price_ratio": "88%", "condition": "일반적 경쟁 환경 (기본 추천)"}},
            "bull": {{"price_ratio": "92%", "condition": "경쟁사 1~2개, 기술 차별성 확보 시"}}
        }},
        "recommended_scenario": "base",
        "rationale": "추천 시나리오 선택 이유 (경쟁 분석 기반, 3문장)",
        "price_competitiveness_message": "가격 경쟁력 어필 방식 (가치 대비 합리적 투자로 포지셔닝)"
    }},
    "alternatives_considered": [
        {{
            "approach": "발주처가 고려했거나 경쟁사가 취할 일반적 접근법 (구체적으로)",
            "our_approach": "우리가 선택한 접근법",
            "why_better": "우리 접근법이 우월한 이유 (정량 근거 또는 유사 사례 포함)"
        }}
    ],
    "risks_mitigations": [
        {{
            "risk": "사업 수행 중 발생 가능한 리스크 (구체적)",
            "probability": 3,
            "impact": 4,
            "risk_score": 12,
            "priority": "high",
            "mitigation": "구체적 선제 대응 방안"
        }}
    ],
    "implementation_checklist": [
        {{
            "phase": "단계명 (예: 1단계: 착수 및 환경 구성)",
            "duration": "소요 기간 (예: 1~2개월)",
            "deliverables": ["산출물1", "산출물2"],
            "milestones": ["마일스톤1"]
        }}
    ],
    "logic_model": {{
        "inputs": ["투입 자원1 (전문 인력, 기술 스택, 인프라 등)", "투입 자원2"],
        "activities": ["핵심 수행 활동1 (구체적 작업 내용)", "활동2"],
        "outputs": ["직접 산출물1 (시스템, 보고서, 교육 결과물 등)", "산출물2"],
        "short_term_outcomes": ["6개월~1년 내 측정 가능한 기대 성과 (수치 포함)", "성과2"],
        "long_term_outcomes": ["2~3년 장기 효과 (사회·행정적 임팩트)", "효과2"]
    }},
    "objection_responses": [
        {{
            "objection": "평가위원이 가질 수 있는 예상 반론 (구체적, 예: '경험 부족' '가격 고가' '일정 촉박')",
            "acknowledge": "이 우려가 타당한 이유를 인정하는 표현 (1문장, 신뢰 구축용)",
            "response": "우리의 대응 논리 (새로운 관점 제시, 기존 전제를 뒤집는 방식)",
            "evidence": "정량 근거 1~2개 (수치, 유사 사례, 인증·레퍼런스)"
        }}
    ]
}}

작성 지침:
- alternatives_considered: 발주처가 고려할 수 있는 다른 접근법과 우리 방안을 비교하여 우월성을 논증하세요 (2~3개).
- risks_mitigations: 사업 수행 중 발생 가능한 주요 리스크 3~5개와 각각의 대응 방안을 명시하세요.
- implementation_checklist: 사업 전체를 3~5단계로 나눠 단계별 산출물과 마일스톤을 구체적으로 제시하세요.
- target_criteria / score_weight: Phase 2 evaluation_weights의 항목명을 각 섹션에 정확히 매핑하고 배점을 기입하세요.
- logic_model: 투입→활동→산출→단기성과→장기성과 인과 체계를 명확히 제시하세요. 단기/장기성과에는 측정 가능한 수치를 포함하세요.
- objection_responses: 평가위원이 가질 수 있는 주요 반론 3~5개를 Acknowledge→Response→Evidence 구조로 선제 대응하세요.
- bid_price_strategy: value_basis에 발주처 인지 가치를 정량화하고, 경쟁 시나리오별 bear/base/bull 3개 입찰가를 제시하세요.
- risks_mitigations: probability(1-5) × impact(1-5) = risk_score를 계산하고, 20-25:critical / 12-19:high / 6-11:medium / 1-5:low로 priority를 기입하세요."""


# ── Phase 4: Implement ─────────────────────────────────────────────

PHASE4_SYSTEM = """당신은 전문 용역 제안서 작성자입니다.
전략 계획을 바탕으로 설득력 있고 구체적인 제안서 본문을 작성합니다.
발주처의 요구사항을 정확히 반영하며 한국어 공공기관 문체를 사용합니다.
경쟁자 대비 차별화 포인트와 가격 경쟁력을 본문 곳곳에 자연스럽게 녹여냅니다.
응답은 반드시 JSON 형식으로만 제공합니다.

## 평가위원 심리 원칙 (반드시 준수)
- 평가위원은 20~30분 안에 제안서를 판단합니다. 첫 섹션(사업 이해도)이 당락을 좌우합니다.
- 발주처가 언급하지 않은 숨은 문제까지 파악한 것을 사업 이해도 섹션에 반드시 포함하세요.
- 정량 지표(수치, 퍼센트, 기간 단축, 비용 절감 등)를 각 섹션에 최소 2개 이상 포함하세요.
- Win Theme이 처음 섹션부터 마지막 섹션까지 일관되게 흐르도록 작성하세요.
- 경쟁사를 직접 언급하지 않되, 우리의 강점이 자연스럽게 경쟁사 약점을 압도하도록 서술하세요.
- 대안 비교(Alternatives Considered): 발주처가 고려했을 다른 접근법 대비 우리 방안의 우월성을 자연스럽게 서술하세요.
- 리스크 대응(Risks/Mitigations): 예상 리스크와 선제 대응 방안을 표 또는 항목 형식으로 포함하세요.
- 추진 체계(Implementation Plan): 단계별 산출물과 마일스톤을 체크리스트 형식으로 제시하세요.
- Logic Model 표: inputs→activities→outputs→단기성과→장기성과 구조의 표를 사업 이해도 섹션에 포함하여 투자 효과의 인과관계를 시각화하세요.
- 섹션 제목(Assertion Title): 토픽 레이블("사업 이해도") 대신 핵심 주장 문장("X 현황의 Y 문제를 Z 방법으로 W% 개선")으로 작성하세요. 평가위원이 제목만으로 핵심 가치를 인식하게 합니다.
- 내러티브 구조(Narrative Arc): 각 섹션을 ①문제 제기(발주처가 처한 현실) → ②긴장감 고조(미해결 시 결과) → ③해결책 제시(우리 방안의 효과) 3단계로 서술하세요.
- 반론 선제 대응(Objection Handling): Phase 3의 objection_responses를 활용하여 평가위원이 가질 우려를 본문 곳곳에서 자연스럽게 해소하세요.
- 가격 앵커링(Price Anchoring): 가격을 언급하기 전에 먼저 사업의 기대 ROI와 가치를 제시하여, 발주처가 비용이 아닌 투자 효과의 관점에서 가격을 인식하게 하세요."""

PHASE4_USER = """다음 정보를 바탕으로 제안서 본문을 작성해주세요.

## 프로젝트 기본 정보
- 프로젝트명: {project_name}
- 발주처: {client_name}
- 사업 범위: {project_scope}
- 사업 기간: {duration}
- 예산: {budget}
- 요구사항: {requirements}

## Win Theme (전체 제안서를 관통하는 핵심 메시지)
{win_theme}

## 작성 전략
{win_strategy}

## 섹션 계획 (각 섹션의 평가위원 설득 포인트 포함)
{section_plan}

## 사업 이해도 전략 (명시된 이슈 + 숨은 이슈 + 우리만의 관점)
{business_understanding_strategy}

## 경쟁 차별화 포인트 (본문에 자연스럽게 반영할 것)
{differentiation_strategy}

## 가격 경쟁력 메시지 (예산/비용 관련 섹션에 반영할 것)
{price_competitiveness_message}

## 제안서 목차 (RFP 지정 목차 또는 템플릿 기반)
{table_of_contents}

## 작성 지침
- 목차에 따라 섹션을 구성하세요.
- 각 섹션명을 정확히 키로 사용하여 JSON을 구성하세요.

## 사업 이해도 섹션 고득점 작성 지침 (배점 최고 항목)
1. 발주처 현황·이슈 → 명시된 요구사항 + 숨은 문제 모두 포함
2. 우리만의 차별화 관점 제시 (다른 제안사가 쉽게 따라올 수 없는 시각)
3. 유사 실적 기반 신뢰도: "OO 프로젝트에서 XX% 성과" 형식으로 수치화
4. 해결 방안 → 이번 사업에 직접 적용하는 방식으로 연결
5. 평가위원이 읽으며 "이 팀은 우리 사업을 정말 이해하고 있다"고 느끼도록 작성

반드시 아래 JSON 형식으로 응답하세요 (섹션명은 실제 목차에 맞게 동적으로 구성):
{{
    "summary": "작성 완료 요약",
    "sections": {{
        "섹션명1": "해당 섹션 본문 내용 (충분히 상세하게, 정량 지표 2개 이상 포함)",
        "섹션명2": "해당 섹션 본문 내용",
        "...": "목차의 모든 항목을 빠짐없이 작성"
    }}
}}"""


# ── Phase 5: Test ──────────────────────────────────────────────────

PHASE5_SYSTEM = """당신은 제안서 품질 심사관입니다.
제안서 초안의 품질을 평가하고 개선 사항을 제시합니다.
조달청 협상에 의한 계약 평가 기준에 따라 항목별로 점수를 예측하고 개선점을 제시합니다.
Win Theme이 전체 제안서에 일관되게 흐르는지, 사업 이해도 섹션이 고득점 요건을 충족하는지,
정량 지표가 충분히 포함되어 있는지를 집중 점검합니다.
특히 경쟁자 대비 차별성이 명확히 드러나는지, 가격 경쟁력 메시지가 적절한지 점검합니다.
응답은 반드시 JSON 형식으로만 제공합니다."""

PHASE5_USER = """다음 제안서 초안을 검토하고 품질을 평가해주세요.

## 핵심 요구사항
{key_requirements}

## 배점 구조 (항목별 배점 기준)
{evaluation_weights}

## 제안서 초안
{sections_preview}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "summary": "검토 결과 요약",
    "quality_score": 85,
    "detailed_scores": {{
        "business_understanding": {{"score": 0, "max": 40, "feedback": "사업 이해도 섹션 평가 및 개선 방향"}},
        "methodology": {{"score": 0, "max": 30, "feedback": "수행 방법론 섹션 평가 및 개선 방향"}},
        "team_credibility": {{"score": 0, "max": 20, "feedback": "인력/실적 신뢰도 평가 및 개선 방향"}},
        "price_rationale": {{"score": 0, "max": 10, "feedback": "가격 합리성 평가 및 개선 방향"}}
    }},
    "win_theme_consistency": "Win Theme이 전체 섹션에 일관되게 반영되었는지 평가 (2~3문장)",
    "quantitative_metrics_count": 0,
    "issues": [
        {{"section": "섹션명", "severity": "high/medium/low", "description": "문제 설명 및 개선 방향"}}
    ],
    "win_probability": "HIGH/MEDIUM/LOW",
    "executive_summary": "제안서 전체 요약 (경영진용, 300자 이내)",
    "alternatives_quality": "Alternatives Considered의 설득력 평가 (1~2문장, 비교 근거의 구체성·정량성 기준)",
    "risks_coverage": "Risks/Mitigations의 완성도 평가 (1~2문장, 리스크 식별 범위와 대응 방안 실현 가능성 기준)",
    "checklist_specificity": "Implementation Checklist의 구체성 평가 (1~2문장, 단계별 산출물 명확성 기준)"
}}"""
