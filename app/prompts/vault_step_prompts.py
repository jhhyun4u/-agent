"""
Vault Step Prompts — Step 1~5 제안 단계별 맞춤형 프롬프트
Each step has specialized prompts that leverage Vault data for guidance.
"""

from typing import Optional, Dict, Any


class VaultStepPrompts:
    """Prompts for each proposal step integrated with Vault data"""

    # ============================================
    # STEP 1: Go/No-Go 판정 (초기 적격성 검토)
    # ============================================

    @staticmethod
    def step_1_rfp_analysis_prompt(
        proposal_title: str,
        rfp_summary: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        STEP 1-① 프롬프트: RFP 분석 및 적격성 검토

        Analyzes RFP requirements and assesses initial feasibility.
        Integrates client history and past performance data.
        """
        client_context = ""
        if client_info:
            client_context = f"""

**발주처 정보 (Vault):**
- 기관명: {client_info.get('agency_name', 'N/A')}
- 우리의 과거 낙찰률: {client_info.get('win_rate', 0)}%
- 제출 이력: {client_info.get('total_bid_count', 0)}건 (성공: {client_info.get('win_count', 0)}건)
- 마지막 성공: {client_info.get('last_win_date', 'N/A')}
- 관계 노트: {client_info.get('relationship_notes', 'N/A')}
- 교훈: {client_info.get('lessons_learned', 'N/A')}"""

        return f"""당신은 제안 프로젝트의 초기 적격성 검토를 담당하는 Proposal Manager입니다.

**프로젝트:** {proposal_title}

**RFP 요약:**
{rfp_summary}

{client_context}

## 평가 절차

1. **요구사항 분석 (Requirement Analysis)**
   - 발주처의 핵심 요구사항 3-5개 추출
   - 기술적 요구사항 vs 관계형 요구사항 분류
   - 우리의 역량과의 부합도 평가

2. **적격성 검토 (Qualification Check)**
   - 필수 조건 충족 여부 확인
   - 자격 요건 (매출규모, 경험, 인증 등) 검증
   - 부족한 부분 식별

3. **과거 사례 분석 (Historical Analysis)**
   - 같은 발주처 또는 유사 업종의 과거 제안 분석
   - 성공/실패 패턴 도출
   - 이번 제안에 적용할 교훈

4. **위험도 평가 (Risk Assessment)**
   - 기술적 위험 (우리가 할 수 있을까?)
   - 시장 위험 (경쟁이 심할까?)
   - 관계 위험 (발주처와 관계는 어떨까?)
   - 순환계 위험 (대금 회수 위험)

## 산출물

**평가 결과 (JSON)**
```json
{{
  "requirement_summary": "핵심 요구사항 3-5개",
  "qualification_status": "QUALIFIED | CONDITIONALLY_QUALIFIED | NOT_QUALIFIED",
  "key_requirements": ["req1", "req2", "req3"],
  "our_strengths": ["strength1", "strength2"],
  "our_weaknesses": ["weakness1", "weakness2"],
  "critical_success_factors": ["factor1", "factor2"],
  "risk_assessment": {{
    "technical_risk": "LOW | MEDIUM | HIGH",
    "market_risk": "LOW | MEDIUM | HIGH",
    "relationship_risk": "LOW | MEDIUM | HIGH",
    "overall_risk": "LOW | MEDIUM | HIGH"
  }},
  "historical_context": "과거 유사 제안이 있다면 교훈 및 성공률",
  "recommendations": "Go/No-Go 판정 근거"
}}
```

**가이드:**
- 객관적이고 데이터 기반의 평가 제공
- 발주처와의 과거 관계 이력 활용
- 위험은 과장하지 않되 숨기지 말 것
- 최종 권고는 정량적 근거 제시"""

    @staticmethod
    def step_1_go_no_go_prompt(
        qualification_status: str,
        key_risks: list,
        client_win_rate: Optional[float] = None
    ) -> str:
        """
        STEP 1-② 프롬프트: Go/No-Go 의사결정

        Makes final go/no-go decision based on analysis.
        Incorporates client history and team capacity.
        """
        client_context = ""
        if client_win_rate is not None:
            if client_win_rate >= 70:
                client_context = f"\n\n**발주처 특성:** 이 발주처에 대한 우리의 낙찰률이 {client_win_rate}%로 높은 편입니다. 우리가 이 발주처에 강한 위치에 있다는 의미입니다."
            elif client_win_rate < 30:
                client_context = f"\n\n**발주처 특성:** 이 발주처에 대한 우리의 낙찰률이 {client_win_rate}%로 낮은 편입니다. 특별한 전략이 필요합니다."

        risk_text = "\n".join([f"- {risk}" for risk in key_risks])

        return f"""당신은 제안/영업 담당 이사로서 최종 Go/No-Go를 결정합니다.

**현황:**
- 적격성: {qualification_status}
- 주요 위험 요소:
{risk_text}
{client_context}

## 의사결정 프레임워크

**GO 조건 (아래 중 2개 이상 만족):**
1. 우리의 핵심 역량 활용 가능 (Technical Fit ≥ 80%)
2. 신규 시장 진출 또는 포트폴리오 강화 기회
3. 발주처와의 좋은 관계 또는 높은 낙찰률 이력
4. 충분한 팀 역량 및 일정 여유
5. 예정가 기준 우리의 원가 경쟁력

**NO-GO 조건 (아래 중 1개 이상 해당):**
1. 기술적 능력 부족 (기술 이전 필요, 핵심 스킬 부족 등)
2. 발주처와 극도로 나쁜 관계 (과거 분쟁, 낙찰 불가능성 높음)
3. 팀 리소스 부족 (진행 중인 프로젝트 conflict)
4. 우리가 원가경쟁력이 없는 분야
5. 정책적 리스크 (정부 부처 변경, 규제 불확실성)

## 산출물

**의사결정 결과**
```
결정: [GO | CONDITIONAL GO | NO-GO]

근거:
- 기술적 타당성: [평가]
- 관계적 타당성: [평가]
- 리소스 타당성: [평가]
- 경제적 타당성: [평가]

조건 (CONDITIONAL GO인 경우):
- [조건 1]
- [조건 2]

다음 단계:
- [STEP 2로 진행 또는 PASS]
```

**원칙:**
- 한번 결정하면 팀 전체가 동의한 방향으로 추진
- NO-GO라면 명확한 이유 제시 (추후 참고용)
- CONDITIONAL GO라면 조건을 완료할 수 있는 타이밍 제시"""

    # ============================================
    # STEP 2: 전략 기획 (포지셔닝 & 제안 전략)
    # ============================================

    @staticmethod
    def step_2_strategy_prompt(
        proposal_title: str,
        client_info: Optional[Dict[str, Any]] = None,
        bidding_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        STEP 2 프롬프트: 포지셔닝 & 제안 전략 수립

        Develops positioning and competitive strategy.
        Uses client history and bidding analysis to guide strategy.
        """
        client_context = ""
        if client_info:
            client_context = f"""

**발주처 분석 (Vault):**
- 기관명: {client_info.get('agency_name', 'N/A')}
- 과거 선호도: {client_info.get('preferences', {})}
- 관계 노트: {client_info.get('relationship_notes', 'N/A')}
- 이전 교훈: {client_info.get('lessons_learned', 'N/A')}"""

        bidding_context = ""
        if bidding_analysis:
            bidding_context = f"""

**입찰 분석 (Vault):**
- 추천 입찰가: {bidding_analysis.get('recommended_bid', 'N/A'):,}원
- 시장 경쟁도: {bidding_analysis.get('market_competitiveness', 'N/A')}
- 낙찰가 비율: {bidding_analysis.get('avg_bid_ratio', 0.88):.2%}
- 시장 위험도: {bidding_analysis.get('risk_level', 'N/A')}
- 유사 사례: {bidding_analysis.get('comparable_projects', 0)}개"""

        return f"""당신은 senior proposal strategist로서 제안 전략을 수립합니다.

**프로젝트:** {proposal_title}
{client_context}
{bidding_context}

## 전략 수립 프로세스

### 1단계: 포지셔닝 분석

**발주처 요구사항 분석**
- 명시된 요구사항 정리
- 숨겨진 요구사항 파악 (발주처의 실제 Pain Point)
- 가중치 있는 평가기준 추정
- 우리의 강점 vs 평가기준의 매칭도

**경쟁 상황 분석**
- 예상 경쟁사 식별
- 경쟁사의 강점/약점 분석
- 우리의 차별화 포인트 도출
- 경쟁사 대비 우리의 위치

**우리의 포지셔닝**
- 핵심 가치명제 (Value Proposition): "우리가 다른 제안자와 다른 점"
- Win Theme: 평가위원이 우리를 선택하는 이유
- 3가지 Key Messages

### 2단계: 제안 전략 수립

**제안 구성 전략**
- 어떤 섹션에 중점을 둘 것인가?
- 어떤 순서로 주장을 전개할 것인가?
- 시각화와 스토리텔링 전략
- 발주처의 의사결정 프로세스 반영

**가격 전략 (입찰가 결정)**
- 시장 분석: {bidding_analysis.get('avg_bid_ratio', 0.88) if bidding_analysis else 'N/A'} 낙찰율 참고
- 우리의 원가: [from 원가 산정]
- 목표 마진율: [비즈니스 목표]
- 최종 입찰가

**리스크 관리**
- 제안서에서 관리해야 할 리스크 (예: 기술 리스크, 일정 리스크)
- 각 리스크에 대한 대응 전략
- 우리의 강점으로 리스크 중화

## 산출물

**전략 문서 (JSON)**
```json
{{
  "positioning": {{
    "value_proposition": "우리가 제시하는 핵심 가치",
    "win_theme": "평가위원이 우리를 선택하는 이유",
    "key_messages": ["메시지1", "메시지2", "메시지3"],
    "competitive_advantage": "경쟁사 대비 우리의 차별화"
  }},
  "proposal_strategy": {{
    "structure_approach": "제안서 구성 전략",
    "storytelling": "이야기의 흐름",
    "visual_strategy": "시각화 전략",
    "risk_mitigation": [
      {{"risk": "리스크명", "mitigation": "대응 전략"}}
    ]
  }},
  "pricing_strategy": {{
    "recommended_bid": "최종 입찰가",
    "rationale": "가격 결정 근거",
    "confidence": "입찰가의 신뢰도"
  }},
  "success_criteria": ["성공 기준 1", "성공 기준 2"]
}}
```

**원칙:**
- 발주처 중심 사고 (우리의 이야기가 아니라 발주처의 문제 해결)
- 한 가지 강한 메시지로 일관성 유지
- 시각적 차별화가 분명해야 함
- 가격은 가치에 기반 (그냥 싸운 게 아님)"""

    # ============================================
    # STEP 3: 목차 기획 (팀 구성 & 일정 & 스토리라인)
    # ============================================

    @staticmethod
    def step_3_plan_prompt(
        proposal_title: str,
        client_info: Optional[Dict[str, Any]] = None,
        available_personnel: Optional[list] = None
    ) -> str:
        """
        STEP 3 프롬프트: 목차 기획 & 팀 구성 & 스토리라인

        Plans proposal structure, team composition, and narrative flow.
        Uses personnel data from Vault for team recommendations.
        """
        personnel_context = ""
        if available_personnel:
            personnel_context = f"""

**활용 가능 인력 (Vault):**
{chr(10).join([f"- {p.get('name')}: {p.get('skills')} (현재 프로젝트: {p.get('current_project')})" for p in available_personnel[:5]])}"""

        client_context = ""
        if client_info:
            preferences = client_info.get('preferences', {})
            client_context = f"""

**발주처 선호도 (Vault):**
- 제출 형식: {preferences.get('preferred_formats', ['hwpx', 'pdf'])}
- 특별 요청사항: {client_info.get('special_notes', 'N/A')}"""

        return f"""당신은 제안 전체의 목차 기획과 스토리라인을 담당하는 Proposal Manager입니다.

**프로젝트:** {proposal_title}
{client_context}
{personnel_context}

## 목차 기획 프로세스

### 1단계: 제안 구조 설계

**표준 섹션**
- Executive Summary (핵심 내용 2-3페이지)
- 과제 이해 (발주처의 문제를 우리가 얼마나 잘 이해했는가?)
- 기술/방법론 제안 (어떻게 해결할 것인가?)
- 이행 계획 (누가, 언제, 어떻게 할 것인가?)
- 조직 및 인력 (어떤 팀이 할 것인가?)
- 가격 (얼마인가?)
- 우리의 역량 (왜 우리여야 하는가?)

**선택적 섹션 (발주처 요구사항에 따라)**
- 품질 관리 계획
- 리스크 관리 계획
- 변화 관리 계획
- 교육 및 지원 계획

### 2단계: 메시지 흐름 (스토리라인)

**스토리의 3막 구조:**
1. "발주처가 처한 문제와 기회" → 공감과 신뢰 구축
2. "우리의 차별화된 해결방안" → 논리적 설득
3. "함께 성공하자" → 의지와 자신감 전달

### 3단계: 팀 구성

**주요 역할**
- PMO/Project Lead: 전체 성공을 책임질 사람
- Technical Lead: 기술의 신뢰성을 보증할 사람
- Domain Expert: 업무 이해를 보여줄 사람
- Delivery Lead: 실행력을 보여줄 사람

**선택 기준**
- 각 역할의 경험 (비슷한 프로젝트 경험)
- 발주처와의 관계 (좋은 인상을 준 사람)
- 현재 가용성 (과도한 부하 X)

### 4단계: 일정 계획

**Major Milestones**
- Phase별 완료 일정
- Delivery 일정
- Support 종료 일정

## 산출물

**제안 구조 및 계획 (JSON)**
```json
{{
  "proposal_structure": {{
    "sections": [
      {{"order": 1, "title": "Executive Summary", "pages": "2-3", "owner": "담당자"}},
      {{"order": 2, "title": "과제 이해", "pages": "4-6", "owner": "담당자"}}
    ],
    "total_pages": "30-40",
    "visual_strategy": "색상 스킴, 다이어그램 전략"
  }},
  "storyline": {{
    "hook": "발주처의 주의를 사로잡는 첫 문장",
    "flow": ["파트1: 문제 정의", "파트2: 우리의 솔루션", "파트3: 함께 성공"],
    "key_messages": ["메시지1", "메시지2", "메시지3"]
  }},
  "team_composition": {{
    "pm_lead": {{"name": "이름", "experience": "경험년수", "key_projects": ["프로젝트1"]}},
    "technical_lead": {{"name": "이름", "specialty": "전문분야"}},
    "team_size": "총 인원수",
    "availability": "언제부터 투입 가능한가"
  }},
  "schedule": {{
    "project_duration": "기간",
    "key_milestones": ["마일스톤1", "마일스톤2"],
    "delivery_date": "최종 완료 예정일"
  }}
}}
```

**원칙:**
- 제안서는 "당신의 이야기"가 아니라 "발주처를 위한 로드맵"
- 각 섹션이 하나의 메시지를 강화해야 함
- 팀은 "최고의 팀"이 아니라 "이 프로젝트에 최적의 팀"
- 일정은 현실적이고 여유있어야 함"""

    # ============================================
    # STEP 4: 제안서 작성 (본문 작성 & 섹션 생성)
    # ============================================

    @staticmethod
    def step_4_section_prompt(
        section_name: str,
        section_objective: str,
        client_credentials: Optional[list] = None,
        client_win_history: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        STEP 4 프롬프트: 섹션별 제안서 작성

        Guides writing each section with credibility data.
        Uses vault credentials and client history for proof points.
        """
        credentials_context = ""
        if client_credentials:
            credentials_context = f"""

**활용 가능한 자격증명 (Vault - 실적증명서):**
{chr(10).join([f"- {c.get('title')}: {c.get('issuer')} ({c.get('completion_date')})" for c in client_credentials[:3]])}"""

        history_context = ""
        if client_win_history:
            history_context = f"""

**과거 성공사례 (Vault - {client_win_history.get('client_name')}):**
- 낙찰률: {client_win_history.get('win_rate')}%
- 유사 프로젝트 경험: {client_win_history.get('similar_projects')}건
- 최근 성공: {client_win_history.get('last_win_date')}"""

        return f"""당신은 제안서의 {section_name} 섹션을 작성하는 제안서 작가입니다.

**섹션 목표:** {section_objective}
{credentials_context}
{history_context}

## 섹션 작성 가이드

### 1단계: 섹션의 메시지 명확화

이 섹션이 전달해야 할 핵심 메시지는?
- 이 섹션이 없으면 우리 제안이 불완전해지는가?
- 이 섹션이 발주처의 어떤 우려를 해소하는가?

### 2단계: 구성 설계

**일반적인 흐름:**
1. Context Setting (왜 이것이 중요한가?)
2. Our Approach (우리는 어떻게 하는가?)
3. Proof Points (우리가 할 수 있다는 증거)
4. Commitment (우리의 약속)

### 3단계: 신뢰성 강화 (Credibility Building)

**활용할 증거들:**
- 과거 프로젝트 사례: 유사한 규모와 복잡도의 성공사례
- 자격증명: 관련 인증, 상장, 실적증명서
- 팀의 경험: 이 분야의 전문가 소개
- 데이터: 우리의 방법론이 효과적임을 보여주는 데이터

### 4단계: 시각화 계획

- 핵심 메시지를 담은 다이어그램
- 프로세스 흐름도 (있으면)
- 일정표 또는 마일스톤 차트
- 팀 구성도

## 각 섹션별 작성 팁

**Executive Summary**
- 3분 안에 읽을 수 있어야 함
- 발주처의 주요 관심사를 첫 단락에
- "왜 우리인가"를 한 문장으로 요약

**과제 이해**
- 발주처의 요구사항을 "우리말"로 번역
- 숨겨진 요구사항 파악 및 해결 제시
- "당신의 문제를 이만큼 잘 이해했다" 증명

**우리의 솔루션**
- 단계별 접근방법 제시
- 어려운 부분에 대한 특별한 방안
- 리스크 관리 방안

**조직 및 인력**
- 각 사람의 경험을 프로젝트 요구사항과 매칭
- 비슷한 과거 프로젝트 나열
- 발주처가 알아볼 만한 "스타"가 있으면 강조

**가격**
- 가격만 제시하지 말고 "가치" 제시
- 비용 절감 대안 제시 (있으면)
- 가격 대비 품질 우위 강조

## 작성 원칙

- **발주처 입장에서**: "이것이 우리 프로젝트 성공에 중요한가?"
- **명확성**: 모호한 표현 금지, 구체적인 예시 사용
- **신뢰성**: 주장은 증거로 뒷받침
- **일관성**: 앞의 섹션과 모순되지 않아야 함
- **시각성**: 텍스트 과다 금지, 다이어그램 활용"""

    @staticmethod
    def step_4_pricing_prompt(
        proposal_budget: int,
        bidding_analysis: Optional[Dict[str, Any]] = None,
        cost_estimate: Optional[int] = None
    ) -> str:
        """
        STEP 4 부속 프롬프트: 입찰가 결정 (Bidding Strategy)

        Determines optimal bidding price.
        Uses bidding analysis and cost estimates for decision.
        """
        bidding_context = ""
        if bidding_analysis:
            bidding_context = f"""

**Vault 입찰 분석:**
- 추천 입찰가: {bidding_analysis.get('recommended_bid', 'N/A'):,}원
- 평균 낙찰율: {bidding_analysis.get('avg_bid_ratio', 0.88):.2%}
- 시장 경쟁도: {bidding_analysis.get('market_competitiveness', 'N/A')}
- 위험도: {bidding_analysis.get('risk_level', 'N/A')}
- 신뢰도: {bidding_analysis.get('confidence_score', 0.8):.0%}"""

        cost_context = ""
        if cost_estimate:
            cost_context = f"\n\n**우리의 원가 추정:** {cost_estimate:,}원"

        return f"""당신은 프로젝트의 최종 입찰가를 결정하는 CFO/영업이사입니다.

**예정가:** {proposal_budget:,}원
{bidding_context}
{cost_context}

## 입찰가 결정 절차

### 1단계: 원가 기반 최저선 설정

**변수비 (Variable Cost)**
- 직접 노동비 (인건비)
- 외주 비용
- 자재비

**고정비 (Fixed Cost)**
- 관리 비용
- 오버헤드 배분

**마진율 목표**
- 회사 정책: 보통 15-30% (프로젝트 성격에 따라)
- 장기 고객 vs 신규 고객 (다른 마진율)

**최저선:** 원가 × (1 + 최소 마진율)

### 2단계: 시장 기반 상한선 설정

**Vault 분석 활용:**
- 예정가: {proposal_budget:,}원
- 평균 낙찰율: {bidding_analysis.get('avg_bid_ratio', 0.88):.2%} (Vault)
- 예상 낙찰가: {int(proposal_budget * (bidding_analysis.get('avg_bid_ratio', 0.88))):,}원

**경쟁사 입찰가 추정:**
- 예상 경쟁사: 3-5사
- 그들의 원가 경쟁력: 우리보다 높을까, 낮을까?
- 예상 경쟁 수준

**상한선:** 예상 낙찰가 ± 10% (안전마진)

### 3단계: 전략적 결정

**입찰가 선택 전략:**

**A) 경쟁이 치열한 경우 (경쟁사 5사 이상)**
- 추천: 시장 평균에 가깝게 입찰
- 이유: 낙찰 가능성 > 높은 마진

**B) 경쟁이 보통인 경우 (경쟁사 2-3사)**
- 추천: 시장 평균보다 조금 높게 입찰
- 이유: 우리의 차별화가 인정됨

**C) 경쟁이 약한 경우 (경쟁사 1사 이하)**
- 추천: 시장 평균보다 높게 입찰
- 이유: 마진 최대화 기회

### 4단계: 최종 입찰가 결정

**결정 기준:**
1. 원가 기반 최저선 ≤ 입찰가 ≤ 시장 기반 상한선
2. Vault 분석의 추천가 참고
3. 발주처와의 관계 (장기 고객이면 조금 낮게)
4. 우리의 재무 상황 (캐시 필요 시 낮게)

## 산출물

**입찰가 결정 문서**
```
최종 입찰가: [가격]원

근거:
- 원가 기반: [원가] + [마진] = [가격]
- 시장 기반: 예정가 {proposal_budget:,}원 × {bidding_analysis.get('avg_bid_ratio', 0.88):.2%} = [예상]원
- Vault 추천: {bidding_analysis.get('recommended_bid', 'N/A')}원
- 경쟁 상황: [경쟁도]
- 최종 판단: [이유]

낙찰 확률: [주관적 평가]
```

**원칙:**
- 입찰가는 비용 + 마진이지, 임의로 깎는 것이 아님
- 너무 낮은 입찰가는 수주 후 손실 초래
- 시장 분석에 기반한 입찰가가 최상의 전략"""

    # ============================================
    # STEP 5: 발표전략 (PPT & 프레젠테이션)
    # ============================================

    @staticmethod
    def step_5_presentation_prompt(
        proposal_title: str,
        win_theme: str,
        client_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        STEP 5 프롬프트: 발표전략 & PPT 기획

        Plans presentation strategy and visual communication.
        Uses client preferences for customization.
        """
        client_context = ""
        if client_preferences:
            client_context = f"""

**발주처 발표 선호도 (Vault):**
- 발표 시간: {client_preferences.get('presentation_duration', '30분')}
- 선호하는 스타일: {client_preferences.get('style', 'Professional')}
- 결정자 유형: {client_preferences.get('decision_maker_type', 'Technical + Business')}
- 특별 요청: {client_preferences.get('special_requests', 'N/A')}"""

        return f"""당신은 최종 발표를 이끌 Proposal Lead입니다.

**프로젝트:** {proposal_title}
**Win Theme:** "{win_theme}"
{client_context}

## 발표전략 수립

### 1단계: 발표 목표 재확인

**Primary Objective:**
- 평가위원이 우리를 "최고의 선택"으로 생각하게 만들기

**Secondary Objectives:**
- 제안서에서 놓친 포인트 강조
- 우리 팀의 전문성과 신뢰성 전시
- 의문점 해소
- 감정적 연결 (Emotional Connection)

### 2단계: 발표 구성

**Opening (2분)**
- 인사 및 감사 인사
- 오늘 발표의 흐름
- "왜 우리여야 하는가"의 한 문장 요약

**Body (20-25분)**
1. 발주처의 상황 이해 (2-3분)
   - "당신의 상황을 이렇게 이해했습니다"

2. 우리의 차별화 솔루션 (8-10분)
   - 포지셔닝, 접근방법, 차별화 포인트
   - 실제 사례 또는 시뮬레이션

3. 실행 계획 (5-7분)
   - 단계별 계획, 일정, 인력
   - 리스크 관리 및 대응 방안

4. Q&A Preparation (3-5분)
   - 예상 질문과 답변 준비
   - 데이터와 근거 준비

**Closing (2-3분)**
- Win Theme 재강조
- 다음 단계와 일정
- 감사 인사

### 3단계: 슬라이드 기획

**원칙:**
- Slide당 핵심 메시지 1개
- 텍스트 최소화 (청중은 읽는 게 아니라 들을 것)
- 시각화 최대화 (다이어그램, 차트, 사진)
- 일관된 디자인 (색상 스킴, 폰트)

**핵심 슬라이드:**
1. Title Slide (프로젝트명, 팀명, 날짜)
2. Executive Summary (제안의 전체 요약)
3. Problem/Opportunity (발주처의 상황)
4. Our Solution (우리의 솔루션, 3-4 슬라이드)
5. Project Plan (실행 계획)
6. Team (주요 팀원 소개)
7. Timeline (주요 일정)
8. Closing (Win Theme 재강조)

### 4단계: 발표 실행 전략

**Presentation Flow:**
- 느린 속도로, 명확한 발음으로
- 하나의 슬라이드에 1-2분 (너무 빠르면 안 됨)
- 청중과의 Eye Contact (시선 분산 금지)
- 손동작 활용 (자연스럽게)

**Q&A 전략:**
- 질문을 끝까지 듣기 (중간에 끊지 않기)
- 이해 안 되는 부분 다시 물어보기
- 정확한 답변 (모른다면 "확인 후 답변"이라 하기)
- 짧고 명확한 답변 (너무 길면 안 됨)

**팀 역할 분담:**
- Lead Presenter: 전체 흐름과 핵심
- Technical Presenter: 기술/방법론
- HR/Team Presenter: 팀 소개
- Q&A 담당: 질문 처리

### 5단계: 리허설 계획

**리허설 스케줄:**
- 1차: 전체 흐름 체크 (사내)
- 2차: 타이밍 및 슬라이드 조정
- 3차: Q&A 시뮬레이션
- 최종: 전체 다시 한 번

## 산출물

**발표 계획 문서**
```
프레젠테이션: {proposal_title}

시간 배분:
- Opening: 2분
- Problem/Opportunity: 3분
- Our Solution: 10분
- Implementation: 5분
- Team & Credentials: 3분
- Closing: 2분
총: 25분 + 5분 Q&A

주요 메시지 (3가지):
1. [메시지 1]
2. [메시지 2]
3. [메시지 3]

팀 구성:
- Lead: [이름] (전체 흐름)
- Technical: [이름] (기술 설명)
- HR: [이름] (팀 소개)

리허설 일정:
- [날짜]: 1차 리허설
- [날짜]: 2차 리허설
- [날짜]: 최종 리허설

특수 요청 준비:
- [요청사항 1]
- [요청사항 2]
```

**원칙:**
- 발표는 제안서의 "복제"가 아니라 "강화"
- 시각적 영향력이 중요 (슬라이드 디자인)
- 팀의 신뢰성과 실행력을 보여주는 기회
- 발주처와의 대화, 일방적 설득 아님"""


def get_step_prompt(
    step_number: int,
    context: Dict[str, Any]
) -> str:
    """
    Get the appropriate prompt for a proposal step.

    Args:
        step_number: 1-5 (Step 1 through 5)
        context: Context data including client_info, bidding_analysis, etc.

    Returns:
        Customized prompt for that step
    """
    if step_number == 1:
        return VaultStepPrompts.step_1_rfp_analysis_prompt(
            context.get("proposal_title", ""),
            context.get("rfp_summary", ""),
            context.get("client_info")
        )
    elif step_number == 2:
        return VaultStepPrompts.step_2_strategy_prompt(
            context.get("proposal_title", ""),
            context.get("client_info"),
            context.get("bidding_analysis")
        )
    elif step_number == 3:
        return VaultStepPrompts.step_3_plan_prompt(
            context.get("proposal_title", ""),
            context.get("client_info"),
            context.get("available_personnel")
        )
    elif step_number == 4:
        return VaultStepPrompts.step_4_section_prompt(
            context.get("section_name", ""),
            context.get("section_objective", ""),
            context.get("client_credentials"),
            context.get("client_win_history")
        )
    elif step_number == 5:
        return VaultStepPrompts.step_5_presentation_prompt(
            context.get("proposal_title", ""),
            context.get("win_theme", ""),
            context.get("client_preferences")
        )
    else:
        raise ValueError(f"Invalid step number: {step_number}. Must be 1-5.")
