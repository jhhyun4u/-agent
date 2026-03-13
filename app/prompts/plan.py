"""
실행 계획 프롬프트 (§4, §29-6, STEP 3)

5개 병렬 노드: team, assign, schedule, story, price.
"""

# ── plan_team ──
PLAN_TEAM_PROMPT = """다음 RFP와 전략에 적합한 제안 팀을 구성하세요.

## RFP 분석
{rfp_summary}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
핵심 메시지: {key_messages}

## 자사 역량
{capabilities_text}

## 지시사항
1. 프로젝트 성격에 맞는 역할별 인력 구성
2. 각 인력의 자격 요건 (학력, 경력, 자격증)
3. 포지셔닝에 따른 인력 전략 (수성: 기존 인력 강조 / 공격: 전문가 영입)

## 출력 형식 (JSON)
{{
  "team": [
    {{
      "role": "프로젝트 관리자",
      "grade": "기술사",
      "mm": 3.0,
      "requirements": ["자격 요건"],
      "responsibilities": ["역할"]
    }}
  ]
}}
"""


# ── plan_assign ──
PLAN_ASSIGN_PROMPT = """제안서에 포함될 주요 산출물과 역할 배분을 계획하세요.

## RFP 분석
{rfp_summary}

## 팀 구성
{team_summary}

## 지시사항
1. RFP 요구 산출물 목록
2. 각 산출물별 담당 역할과 일정
3. 품질 관리 체크포인트

## 출력 형식 (JSON)
{{
  "deliverables": [
    {{
      "name": "산출물명",
      "responsible_role": "담당 역할",
      "due_phase": "해당 단계",
      "quality_criteria": "품질 기준"
    }}
  ]
}}
"""


# ── plan_schedule ──
PLAN_SCHEDULE_PROMPT = """프로젝트 추진 일정을 수립하세요.

## RFP 분석
{rfp_summary}
마감일: {deadline}

## 산출물 목록
{deliverables_summary}

## 지시사항
1. 전체 기간을 3~5개 Phase로 구분
2. 각 Phase별 주요 활동과 마일스톤
3. 핵심 경로(Critical Path) 식별
4. 리스크 대비 버퍼 일정

## 출력 형식 (JSON)
{{
  "schedule": {{
    "total_duration": "전체 기간",
    "phases": [
      {{
        "name": "1단계: 분석",
        "duration": "4주",
        "activities": ["활동1", "활동2"],
        "milestones": ["마일스톤"],
        "deliverables": ["산출물"]
      }}
    ],
    "critical_path": ["핵심 경로 항목"],
    "buffer": "리스크 버퍼 기간"
  }}
}}
"""


# ── plan_story ──
PLAN_STORY_PROMPT = """제안서의 **목차 구성**과 **섹션별 스토리라인**을 설계하세요.

## RFP 분석
{rfp_summary}

## 현재 목차 (RFP 분석 기반 초안)
{current_sections}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
Ghost Theme: {ghost_theme}
핵심 메시지: {key_messages}
Action Forcing Event: {action_forcing_event}

## 평가 항목
{eval_items}

## 지시사항

### 1단계: 목차 확정
- 현재 목차를 전략 관점에서 검토하세요.
- 평가항목 배점, 전략적 중요도, 발주처 관심사를 종합하여 **섹션 순서를 최적화**하세요.
- 필요하면 섹션을 추가(예: 부가제안/기대효과)하거나 분할(예: 기술방안을 시스템/데이터 분리)하세요.
- 불필요하거나 중복되는 섹션은 병합하세요.

### 2단계: 섹션별 스토리라인
- 각 섹션의 **핵심 메시지**(Assertion Title 수준의 한 문장 주장)를 작성하세요.
- 핵심 메시지를 뒷받침하는 **논거 2~3개**와 **근거 데이터**를 설계하세요.
- 평가위원이 해당 섹션에서 점수를 주기 쉬운 구조로 배치하세요.
- 섹션 간 **연결고리**(앞 섹션의 결론이 다음 섹션의 전제가 되는 내러티브 흐름)를 명시하세요.
- Win Theme이 각 섹션에서 어떻게 강화되는지 서술하세요.

### 3단계: 톤앤매너
- 포지셔닝에 맞는 전체 톤과 섹션별 뉘앙스 차이를 가이드하세요.

## 출력 형식 (JSON)
{{
  "storylines": {{
    "overall_narrative": "전체 스토리 한줄 요약 (Win Theme 연계)",
    "opening_hook": "도입부 핵심 메시지 (평가위원의 첫인상을 결정)",
    "sections": [
      {{
        "eval_item": "평가 항목명 (= 섹션 ID, 순서대로)",
        "weight": 30,
        "key_message": "이 섹션의 핵심 주장 (Assertion Title, 한 문장)",
        "narrative_arc": "문제 제기 → 긴장감 → 해결책 구조 요약",
        "supporting_points": ["논거1 (구체적 방법/접근)", "논거2 (차별화 포인트)"],
        "evidence": ["근거 데이터 (수치/실적/사례)"],
        "win_theme_connection": "Win Theme과 이 섹션의 연결 방식",
        "transition_to_next": "다음 섹션으로의 연결고리",
        "tone": "이 섹션의 톤 가이드"
      }}
    ],
    "closing_impact": "마무리 임팩트 메시지 (Win Theme 재강조)"
  }}
}}
"""


# ── plan_price ──
# v3.2: 원가기준·노임단가·입찰시뮬레이션 (ProposalForge #8)
BUDGET_DETAIL_FRAMEWORK = """
## 예산산정 상세 프레임워크

### 1. 원가 기준: {cost_standard}

### 2. 노임단가 (실제 데이터)
{labor_rates_table}

### 3. 직접경비 항목
여비, 회의비, 설문조사비, 데이터 구매비, 인쇄비, 기타

### 4. 간접경비(제경비)
영리법인: 인건비 대비 110~120% / 비영리법인: 40~60%

### 5. 기술료(이윤)
영리법인: (인건비+직접경비+간접경비) × 20% 이내

### 6. 시장 벤치마크
{benchmark_summary}
"""

PLAN_PRICE_PROMPT = """프로젝트 예산과 입찰 가격 전략을 수립하세요.

## RFP 분석
{rfp_summary}
예산: {budget}

## 전략
포지셔닝: {positioning}
가격 전략: {price_strategy}

## 팀 구성
{team_summary}

## 예산산정 프레임워크
{budget_framework}

## 지시사항
1. 적용 원가 기준 판별
2. 등급별 노임단가 × 투입 M/M으로 인건비 산출
3. 직접경비, 간접경비, 기술료 산출
4. 입찰가격 결정 시뮬레이션 (계약 방식별 최적가)

## 출력 형식 (JSON)
{{
  "bid_price": {{
    "cost_standard": "적용 원가 기준",
    "labor_cost": {{
      "breakdown": [
        {{"grade": "등급", "monthly_rate": 0, "mm": 0, "subtotal": 0}}
      ],
      "total": 0
    }},
    "direct_expenses": {{
      "items": [{{"name": "항목", "amount": 0, "basis": "산출 근거"}}],
      "total": 0
    }},
    "overhead": {{"rate": 0.0, "total": 0}},
    "profit": {{"rate": 0.0, "total": 0}},
    "total_cost": 0,
    "bid_simulation": {{
      "method": "계약 방식",
      "optimal_price": 0,
      "price_range": {{"min": 0, "max": 0}},
      "rationale": "가격 결정 근거"
    }}
  }}
}}
"""
