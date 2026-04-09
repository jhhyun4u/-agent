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

## 활용 가능한 검증된 근거 데이터 (리서치 기반)
{evidence_candidates}
위 데이터를 각 섹션의 evidence에 우선 배치하세요. 부족한 경우 [KB 데이터 필요: 설명] 플레이스홀더를 사용하세요.

## 지시사항

### 1단계: 목차 확정
- 현재 목차를 전략 관점에서 검토하세요.
- 평가항목 배점, 전략적 중요도, 발주처 관심사를 종합하여 **섹션 순서를 최적화**하세요.
- 필요하면 섹션을 추가(예: 부가제안/기대효과)하거나 분할(예: 기술방안을 시스템/데이터 분리)하세요.
- 불필요하거나 중복되는 섹션은 병합하세요.

### 2단계: 섹션별 스토리라인
- 각 섹션의 **핵심 메시지**(Assertion Title 수준의 한 문장 주장)를 작성하세요.
- 핵심 메시지를 뒷받침하는 **논거 2~3개**와 **근거 데이터**를 설계하세요.
- 각 섹션의 **기대 성과**를 SMART 기준으로 구체화하세요:
  - **S**pecific(구체적): 무엇을 달성하는가
  - **M**easurable(측정 가능): 어떤 지표로 측정하는가
  - **A**chievable(달성 가능): 현실적 근거가 있는가
  - **R**elevant(관련성): 사업 목적과 직결되는가
  - **T**ime-bound(기한): 언제까지 달성하는가
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
  }},
  "quality_check": {{
    "eval_coverage": {{
      "required": ["{eval_item_ids}의 각 항목"],
      "mapped": ["실제 매핑된 평가항목 목록"],
      "missing": ["누락된 평가항목 (없으면 빈 배열)"]
    }},
    "win_theme_coverage": {{
      "total_sections": 0,
      "sections_with_win_theme": 0,
      "weak_sections": ["Win Theme 연결이 약한 섹션명 (없으면 빈 배열)"]
    }},
    "smart_compliance": {{
      "total_sections": 0,
      "smart_complete": 0,
      "incomplete_sections": [
        {{"section": "섹션명", "missing": ["Measurable 등 미충족 SMART 요소"]}}
      ]
    }},
    "evidence_quality": {{
      "total_evidence": 0,
      "from_research": 0,
      "placeholders": 0
    }}
  }}
}}
"""

# NOTE: DEPRECATED (v4.0)
# plan_price 프롬프트는 STEP 3A에서 제거됨.
# 가격 계획은 STEP 4B (bid_plan)에서 통합 처리됨.
# bid_plan.py의 PRICING_ENGINE 참조.
