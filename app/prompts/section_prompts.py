"""
섹션 유형별 전문 프롬프트 (v3.5)

10가지 섹션 유형에 대한 전문 프롬프트.
모든 프롬프트 공통 원칙:
  - 평가위원의 채점 관점에서 작성 (배점 최고점 획득 목표)
  - 평가항목·세부항목과 1:1 정합성 확보
  - 추상적 서술 금지, 구체적 근거·사례·수치 필수
"""

# ── 섹션 유형 코드 ──

SECTION_TYPES = {
    "UNDERSTAND": "사업의 이해",
    "STRATEGY": "추진 전략",
    "METHODOLOGY": "수행 방법론",
    "TECHNICAL": "기술적 수행방안",
    "MANAGEMENT": "사업 관리",
    "PERSONNEL": "투입 인력",
    "TRACK_RECORD": "수행 실적",
    "SECURITY": "보안 대책",
    "MAINTENANCE": "유지보수/하자보수",
    "ADDED_VALUE": "부가제안/기대효과",
}

# ── 섹션 유형 자동 분류 키워드 매핑 ──

SECTION_TYPE_KEYWORDS = {
    "UNDERSTAND": [
        "사업의 이해", "과업의 이해", "사업 이해", "배경", "목적", "현황",
        "AS-IS", "TO-BE", "과업 범위", "범위", "필요성", "개요",
    ],
    "STRATEGY": [
        "추진 전략", "추진 방향", "기본 방향", "전략", "프레임워크",
        "핵심 성공", "접근 방법", "추진 방침",
    ],
    "METHODOLOGY": [
        "방법론", "수행 방법", "수행 절차", "추진 절차", "프로세스",
        "수행 체계", "수행 방안", "단계별",
    ],
    "TECHNICAL": [
        "기술", "시스템", "아키텍처", "설계", "구현", "개발",
        "인프라", "플랫폼", "솔루션", "기능", "연계", "이관",
        "데이터", "네트워크", "클라우드", "AI", "분석",
    ],
    "MANAGEMENT": [
        "사업 관리", "프로젝트 관리", "일정", "품질", "위험",
        "리스크", "의사소통", "보고", "추진 체계", "조직",
        "관리 방안", "변경 관리", "이슈 관리",
    ],
    "PERSONNEL": [
        "인력", "투입 인력", "인력 구성", "조직 구성", "역할",
        "약력", "경력", "자격", "PM", "PL",
    ],
    "TRACK_RECORD": [
        "수행 실적", "실적", "유사 사업", "수행 경험", "레퍼런스",
        "회사 소개", "회사 현황", "업체 소개",
    ],
    "SECURITY": [
        "보안", "정보보호", "개인정보", "접근 통제", "암호화",
        "보안 대책", "취약점", "침해", "보안 관리",
    ],
    "MAINTENANCE": [
        "유지보수", "하자보수", "운영", "SLA", "서비스 수준",
        "장애 대응", "모니터링", "전환", "인수인계", "안정화",
    ],
    "ADDED_VALUE": [
        "부가 제안", "부가제안", "기대효과", "기대 효과", "활용 방안",
        "향후 발전", "확장", "추가 제안", "특장점",
    ],
}


def classify_section_type(section_id: str, section_title: str = "") -> str:
    """섹션 ID/제목에서 유형을 자동 분류. 매칭 안 되면 TECHNICAL 기본값."""
    text = f"{section_id} {section_title}".lower()

    priority_order = [
        "PERSONNEL", "TRACK_RECORD", "SECURITY", "MAINTENANCE",
        "ADDED_VALUE", "UNDERSTAND", "MANAGEMENT", "METHODOLOGY",
        "STRATEGY", "TECHNICAL",
    ]

    for stype in priority_order:
        keywords = SECTION_TYPE_KEYWORDS[stype]
        for kw in keywords:
            if kw.lower() in text:
                return stype

    return "TECHNICAL"


# ════════════════════════════════════════════════════════
# 공통 평가위원 관점 프롬프트 블록
# ════════════════════════════════════════════════════════

EVALUATOR_PERSPECTIVE_BLOCK = """
## 평가위원 채점 관점 (최고점 획득 전략)

이 섹션의 평가항목 정보:
{eval_item_detail}

### 채점 원리
평가위원은 다음 기준으로 점수를 부여합니다:
1. **정합성** — 평가항목/세부항목에서 요구하는 내용이 빠짐없이 대응되어 있는가
2. **구체성** — 추상적 서술이 아닌 구체적 방법·수치·사례·근거가 제시되었는가
3. **논리성** — 내용의 흐름이 논리적이고, 주장→근거→결론 구조가 명확한가
4. **차별성** — 다른 제안서와 구별되는 독창적 접근이나 강점이 드러나는가
5. **실현가능성** — 제안한 내용이 실제로 실행 가능하고 현실적인가

### 최고점 획득 방법
- 세부항목 하나하나에 대해 **명시적으로 대응**하세요 (암묵적 대응 X)
- 세부항목이 3개면, 본문에서 3개 각각에 대한 서술이 명확히 구분되어야 합니다
- 각 서술에는 반드시 **구체적 근거**(수치, 사례, 도표, 레퍼런스)를 포함하세요
- 평가위원이 점수를 줄 때 "이 부분은 OO점" 하고 바로 체크할 수 있는 구조로 작성하세요
"""


# ════════════════════════════════════════════════════════
# 유형별 전문 프롬프트
# ════════════════════════════════════════════════════════


SECTION_PROMPT_UNDERSTAND = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(사업의 이해)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"우리가 이 사업을 누구보다 깊이 이해하고 있다"**는 인상을 주는 것입니다.
RFP를 단순히 베끼는 것이 아니라, 발주기관의 관점에서 사업의 본질을 재해석하세요.

평가위원은 이 섹션에서 "이 업체가 우리 기관의 상황과 사업 목적을 제대로 파악하고 있는가"를 봅니다.
RFP 복사본을 제출하는 업체는 낮은 점수를 받습니다. **발주기관이 미처 인식하지 못한 이슈까지
짚어주는 수준**이면 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과 (반드시 활용)
{research_context}

## 필수 포함 요소 (각 요소에 구체적 근거 필수)
1. **발주기관 미션·비전과 사업 연결**
   - 기관의 중장기 계획, 상위 정책과 본 사업의 관계를 명시
   - 예: "OO기관 제3차 정보화전략계획(2024~2028)의 핵심과제 3-2에 해당"
2. **현황 분석 (AS-IS)**
   - 현재 시스템/프로세스의 문제점을 구조적으로 정리
   - 문제 → 원인 → 영향의 인과관계 서술
   - 가능하면 정량 데이터 포함 (처리건수, 장애횟수, 민원건수 등)
3. **개선 방향 (TO-BE)**
   - AS-IS 각 문제에 대응하는 개선 목표
   - 도표: AS-IS vs TO-BE 비교 매트릭스 필수
4. **과업 범위 재구성**
   - RFP 요구사항을 우리의 이해 체계로 재정리 (단순 복사 X)
   - "RFP에서 요구하는 A는 실질적으로 B를 의미하며..." 수준의 해석
5. **핫버튼 반영**: {hot_buttons}
   - 핫버튼 키워드를 자연스럽게 본문에 녹여 넣으세요

## 주의사항
- RFP 문장 그대로 복사 금지. 발주기관 관점에서 재해석
- 추상적 미사여구("최적의", "효율적인") 금지 → 구체적 데이터/정책 근거 인용
- AS-IS/TO-BE 비교표 또는 현황 분석 다이어그램 1개 이상 필수

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown 형식, 표·다이어그램 포함)",
  "self_check": {{
    "client_perspective": true,
    "as_is_to_be_included": true,
    "hot_buttons_reflected": true,
    "no_rfp_copy": true,
    "diagram_included": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_STRATEGY = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(추진 전략)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"우리만의 차별화된 접근법과 Win Theme을 선언"**하는 것입니다.
평가위원은 "이 업체의 접근법이 남다르고, 실제로 성과를 낼 수 있겠다"고 느껴야 합니다.

전략이 구호에 그치는 제안서는 중간 점수, **전략이 구체적 실행 방안과 연결되고
경쟁사 대비 차별점이 명확한 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략
포지셔닝: {positioning}
Win Theme: {win_theme}
핵심 메시지: {key_messages}
Ghost Theme: {ghost_theme}

## 리서치 결과
{research_context}

## 필수 포함 요소 (각 요소에 구체적 근거 필수)
1. **추진 비전/슬로건**
   - Win Theme을 한 문장으로 압축한 슬로건
   - 예: "데이터 기반 선제적 관리로 OO 서비스 혁신"
2. **추진 전략 프레임워크**
   - 3~5개 전략 축을 다이어그램으로 시각화 (필수)
   - 각 전략 축이 RFP의 어떤 요구사항에 대응하는지 매핑
3. **차별화 포인트** (최소 3가지)
   - 각 차별화 포인트에 대해: 무엇이 다른가 → 왜 효과적인가 → 증빙/근거
   - Ghost Theme(경쟁사 약점)을 은연중 부각
4. **핵심 성공 요인 (CSF)**
   - 이 사업의 성패를 가르는 요소 3~5개
   - 각 CSF에 대한 우리의 대응 전략
5. **기대 성과 Preview**
   - 전략 실행 시 달성할 정량적 목표 (KPI 수준)

## 주의사항
- 전략 프레임워크 도표 필수 (텍스트만으로는 감점)
- Ghost Theme은 노골적으로 경쟁사 비판 X → 우리 강점 강조로 간접 부각
- 전략 → 다음 섹션(수행방안)과의 연결고리 명시

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown)",
  "self_check": {{
    "win_theme_declared": true,
    "framework_visualized": true,
    "differentiation_clear": true,
    "ghost_theme_woven": true,
    "csf_identified": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_METHODOLOGY = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(수행 방법론)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"검증된 방법론으로 체계적으로 수행하겠다"**는 신뢰를 주는 것입니다.
평가위원은 "이 업체는 체계적인 절차를 갖추고 있고, 각 단계에서 무엇을 하고
무엇을 만들어내는지 구체적으로 알고 있구나"라고 느껴야 합니다.

교과서적인 방법론 소개는 중간 점수, **사업에 맞게 커스터마이징된 방법론에
단계별 수행활동과 산출물이 구체적으로 명시된 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과
{research_context}

## 필수 포함 요소 (각 요소에 구체적 예시 필수)

### 1. 방법론 개요 및 선택 근거
- 적용할 방법론 명칭과 핵심 특징
- **왜 이 방법론인가**: 사업 특성(규모, 기간, 기술, 도메인)과의 적합성
- 대안 방법론 대비 장점 비교표
- 예: "본 사업은 OO 특성이 있어 Agile보다 단계적 접근이 적합하며, 당사의 OO방법론은..."

### 2. 단계별 프로세스 (Phase/Stage)
**반드시 아래 형식으로 각 단계를 구체적으로 기술하세요:**

| 단계 | 목표 | 주요 수행활동 | 산출물 | 기간 |
|------|------|-------------|--------|------|

**각 단계별 수행활동 예시 (사업 유형에 맞게 조정하세요):**

**[착수/분석 단계]**
- 수행활동: 이해관계자 인터뷰, 현행 시스템 분석, 요구사항 수집·정리, 현황 조사
- 산출물 예시: 착수보고서, 현황분석서, 요구사항정의서, 이해관계자 분석서
- 산출물 상세: "요구사항정의서는 기능/비기능/데이터/인터페이스 요구사항을
  분류하여 총 4개 섹션, 요구사항 추적 매트릭스(RTM) 포함"

**[설계 단계]**
- 수행활동: 아키텍처 설계, 상세 설계, UI/UX 설계, 데이터 모델링, 인터페이스 설계
- 산출물 예시: 아키텍처설계서, 상세설계서, UI설계서, 데이터모델링문서, 인터페이스설계서
- 산출물 상세: "아키텍처설계서는 논리/물리 아키텍처, 기술 스택 선정 근거,
  성능 목표, 보안 설계 포함 (약 30~50페이지)"

**[구현/개발 단계]**
- 수행활동: 코딩/개발, 단위테스트, 코드리뷰, 데이터 이관 개발, 연계 개발
- 산출물 예시: 소스코드, 단위테스트결과서, 코드리뷰보고서, 이관프로그램
- 산출물 상세: "단위테스트결과서는 모듈별 테스트 케이스, 실행 결과,
  커버리지 80% 이상 달성 근거 포함"

**[테스트/검증 단계]**
- 수행활동: 통합테스트, 시스템테스트, 성능테스트, 보안점검, 사용자테스트(UAT)
- 산출물 예시: 테스트계획서, 테스트결과보고서, 성능테스트보고서, 보안점검결과서
- 산출물 상세: "테스트계획서는 테스트 전략, 범위, 일정, 환경, 합격기준,
  결함관리 프로세스 포함"

**[이행/안정화 단계]**
- 수행활동: 시스템 이행, 데이터 이관, 사용자 교육, 안정화 운영, 인수인계
- 산출물 예시: 이행계획서, 교육교재, 운영매뉴얼, 완료보고서, 유지보수계획서
- 산출물 상세: "교육교재는 관리자용/사용자용 분리, 실습 시나리오 포함,
  교육 후 만족도 조사 실시"

### 3. 사업 특화 커스터마이징
- 표준 방법론에서 이 사업에 맞게 **구체적으로 조정한 부분**
- 예: "기존 5단계를 4단계로 축소 (분석-설계 통합) — 사업 기간 6개월 특성 반영"
- 예: "OO 기관의 보안 심사 절차를 감안하여 3차에 걸친 보안 검토 게이트 추가"

### 4. 품질 게이트 (단계 전환 기준)
| 게이트 | 전환 기준 | 검증 방법 | 승인 주체 |
|--------|----------|----------|----------|
| G1: 분석→설계 | 요구사항 확정률 100% | 요구사항 검토회의 | 발주기관 PM |
| G2: 설계→개발 | 설계 검토 완료, 결함 0건 | 설계 워크스루 | 기술검토위원회 |
| ... | ... | ... | ... |

### 5. 산출물 총괄 목록
| 단계 | 산출물명 | 작성 기준/양식 | 페이지(예상) | 검토 주체 |
|------|---------|-------------|------------|----------|

## 주의사항
- 교과서적 방법론 설명 금지 → 이 사업에 왜 이 방법론인지, 어떻게 맞춤화했는지
- **프로세스 흐름도(다이어그램) 필수** — 단계간 흐름과 품질 게이트를 시각화
- 산출물 목록은 표로 정리 (산출물명, 작성 기준, 검토 주체 포함)
- 각 산출물의 내용 구성(목차 수준)을 간략히 서술하면 최고점

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 프로세스도·산출물표·품질게이트표 포함)",
  "self_check": {{
    "methodology_justified": true,
    "customized_for_project": true,
    "process_diagram_included": true,
    "activities_per_phase_concrete": true,
    "deliverables_with_detail": true,
    "quality_gates_defined": true,
    "deliverables_table_complete": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_TECHNICAL = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(기술적 수행방안)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"구체적으로 어떻게 구현/수행할 것인가"**를 입증하는 것입니다.
평가위원(기술 전문가)은 "이 업체가 실제로 이것을 할 수 있는 기술력이 있는가"를 봅니다.

일반론 수준의 기술 서술은 중간 점수, **구체적 기술명·구성도·구현 방법·성능 수치가
포함된 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과
{research_context}

## KB 참조 (보유 역량·기술)
{kb_context}

## 필수 포함 요소 (각 요소에 구체적 근거 필수)
1. **전체 구성도/아키텍처**
   - 시스템 구성을 논리적·물리적으로 시각화 (텍스트 다이어그램 필수)
   - 구성 요소 간 데이터 흐름, 인터페이스 표시
2. **기술 선택 근거**
   - 주요 기술/솔루션별 선택 이유 (대안 비교표 포함)
   - 예: "ORM 선택: TypeORM vs Prisma — 타입 안정성과 마이그레이션 편의성 비교"
3. **세부 구현 방안**
   - RFP 요구사항별 구현 방법을 입력→처리→출력 수준으로 상세 서술
   - 핵심 기능은 처리 로직/알고리즘 수준까지 설명
4. **RFP 요구사항 1:1 대응표**
   - | RFP 요구사항 | 대응 방안 | 구현 기술 | 검증 방법 |
5. **차별화 기술**
   - 경쟁사 대비 기술적 우위 (벤치마크, 성능 수치, 특허/인증 등)

## 주의사항
- "최신 기술을 활용하여" 같은 추상적 서술 금지 → 기술명, 버전, 적용 위치 명시
- 구성도/다이어그램 필수 (없으면 감점)
- 성능 수치, 벤치마크, 적용 사례 등 정량 근거 필수
- RFP 요구사항과의 매핑 표(Compliance Matrix) 포함

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 구성도·요구사항대응표·기술비교표 포함)",
  "self_check": {{
    "architecture_diagram_included": true,
    "tech_choice_justified": true,
    "implementation_concrete": true,
    "rfp_requirements_mapped": true,
    "quantitative_evidence": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_MANAGEMENT = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(사업 관리)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"체계적인 관리로 일정·품질·리스크를 통제하겠다"**는 신뢰를 주는 것입니다.
평가위원은 "이 업체는 문제가 생겨도 체계적으로 대응할 수 있겠다"고 느껴야 합니다.

형식적인 관리 체계 나열은 중간 점수, **이 사업에서 실제로 발생할 이슈를 예측하고
구체적 대응 절차를 제시한 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과
{research_context}

## 필수 포함 요소 (각 요소에 구체적 근거 필수)
1. **추진 체계도**
   - 발주기관-수행사 간 조직도, 보고/의사결정 라인
   - 각 역할의 책임 범위 명확화
2. **일정 관리**
   - WBS 기반 마일스톤 일정표 (간트차트 형태)
   - 주요 마일스톤과 납기 일정, 크리티컬 패스 표시
3. **품질 관리**
   - 품질 기준(정량 지표), 검토 프로세스, 산출물 검증 체계
   - 예: "코드 리뷰 100%, 단위테스트 커버리지 80% 이상, 결함 밀도 0.5건/KLOC 이하"
4. **위험 관리** (이 사업 특유의 리스크)
   - 리스크 매트릭스: | 리스크 | 발생확률 | 영향도 | 대응전략 | 모니터링 |
   - 일반적 리스크가 아닌, 이 사업에서 실제 발생 가능한 리스크 식별
5. **의사소통/보고 체계**
   - 정기 보고 주기·형식, 이슈 에스컬레이션 절차, 회의 체계
   - 예: "주간보고(매주 금), 월간보고(매월 마지막 주), 긴급보고(장애/지연 시 2시간 내)"

## 주의사항
- 교과서적 일반론 금지 → 이 사업의 구체적 상황에 맞는 관리 방안
- 일정표는 주요 마일스톤 중심 (상세 WBS는 별도 첨부 언급)
- 발주기관과의 협업 체계를 구체적으로 제시

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 체계도·일정표·리스크매트릭스 포함)",
  "self_check": {{
    "org_chart_included": true,
    "schedule_with_milestones": true,
    "risk_specific_to_project": true,
    "quality_metrics_quantified": true,
    "communication_plan_clear": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_PERSONNEL = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(투입 인력)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"최적의 인력으로 구성했으며, 각 인력이 이 사업에 적합하다"**를 증명하는 것입니다.
평가위원은 "투입 인력이 이 사업을 수행할 역량이 충분한가"를 봅니다.

단순 인력표 나열은 중간 점수, **인력 구성의 전략적 의도와 핵심 인력의
유사 사업 경험이 구체적으로 서술된 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## KB 참조 (보유 인력·역량)
{kb_context}

## 필수 포함 요소
1. **인력 구성 총괄표**
   - | 구분 | 성명 | 직급 | 자격/학위 | 경력(년) | 투입기간 | M/M |
2. **인력 구성 전략**
   - RFP 요구 인력 vs 제안 인력 비교, 초과 투입 사유
3. **핵심 인력 프로필** (PM/PL/핵심기술인력)
   - 경력 요약, 보유 자격, **유사 사업 수행 경험** (사업명·역할·성과)
4. **역할 분담 매트릭스 (RACI)**
   - | 활동 | PM | PL | 개발자 | 분석가 | QA |
5. **단계별 투입 계획**
   - 시간축 M/M 투입 차트 또는 표

## 주의사항
- RFP 요구 인력 자격 요건 반드시 충족
- 핵심 인력의 유사 사업 경험은 구체적으로 (사업명, 기간, 금액, 역할, 성과)
- M/M이 사업 규모·기간과 합리적으로 일치해야 함

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 인력표·RACI·투입계획 포함)",
  "self_check": {{
    "rfp_personnel_requirements_met": true,
    "composition_strategy_explained": true,
    "key_personnel_experience_detailed": true,
    "raci_matrix_included": true,
    "mm_plan_reasonable": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_TRACK_RECORD = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(수행 실적)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"유사 사업을 성공적으로 수행한 검증된 업체"**임을 증명하는 것입니다.
평가위원은 "이 업체의 실적이 현재 사업과 얼마나 유사하고, 실제 성과가 어떠했는가"를 봅니다.

단순 실적 나열은 중간 점수, **각 실적의 현 사업과의 유사성을 체계적으로 분석하고
정량적 성과를 제시한 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## KB 참조 (수행 실적)
{kb_context}

## 필수 포함 요소
1. **유사성 매트릭스**
   - | 실적명 | 사업규모 | 기술분야 | 도메인 | 기관유형 | 유사도 |
2. **핵심 실적 상세** (사업명, 기간, 금액, 발주기관, 주요 내용)
3. **정량적 성과** — 비용절감률, 처리속도 향상, 사용자만족도 등
4. **현 사업에의 시사점** — 각 실적에서 얻은 교훈의 적용 방안
5. **회사 개요** — 설립, 매출, 인력, 인증 현황 (간략)

## 주의사항
- 유사성이 낮은 실적을 억지로 끼워넣지 마세요
- "성공적으로 수행" 대신 구체적 성과 수치 제시
- 발주기관이 확인 가능한 실적 정보(계약번호 등) 포함

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 유사성매트릭스·실적표 포함)",
  "self_check": {{
    "similarity_matrix_included": true,
    "quantitative_results": true,
    "relevance_to_current_project": true,
    "verifiable_information": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_SECURITY = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(보안 대책)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"법적 준거와 기술적 보안 대책을 빈틈없이 이행하겠다"**를 보여주는 것입니다.
평가위원은 보안 섹션에서 "법령 준수 여부, 기술적 대책의 구체성"을 봅니다.

보안은 가점보다 **감점 방지**가 핵심입니다. 법령 누락이나 대책 부실은 큰 감점,
법령별 대응표와 기술적 대책이 구체적이면 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과
{research_context}

## 필수 포함 요소
1. **보안 준거 법령** — 해당 법령명과 조항, 준수 방안 매핑표
2. **기술적 보안** — 접근통제, 암호화, 네트워크 보안, 취약점 점검 (구체적 기술)
3. **관리적 보안** — 보안 조직, 교육, 감사, 사고 대응 절차
4. **물리적 보안** — 시설 출입 통제, 장비 관리 (해당 시)
5. **개인정보 보호** — 수집·이용·파기 절차, DPIA (해당 시)

## 주의사항
- RFP 보안 요구사항을 빠짐없이 대응
- 법령명·조항을 정확하게 인용
- 보안 체계도 포함 권장

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 법령대응표·보안체계도 포함)",
  "self_check": {{
    "legal_compliance_cited": true,
    "technical_measures_concrete": true,
    "admin_measures_included": true,
    "rfp_security_reqs_covered": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_MAINTENANCE = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(유지보수/하자보수)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"사업 완료 후에도 안정적으로 지원하겠다"**는 신뢰를 주는 것입니다.
평가위원은 "사업 종료 후 문제가 생기면 어떻게 대응하는가"를 봅니다.

추상적 약속은 중간 점수, **구체적 SLA 지표와 장애 대응 절차가
명확한 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 필수 포함 요소
1. **하자보수 범위·기간** — RFP 명시 기간, 무상/유상 구분
2. **SLA 지표** — | 항목 | 목표 | 측정방법 | 미달 시 조치 |
3. **장애 대응 체계** — 장애 등급별 대응 절차 플로우차트
4. **기술 이전/인수인계** — 산출물 목록, 교육 계획, 운영 가이드
5. **안정화 기간 운영** — 사업 완료 후 안정화 지원 방안

## 주의사항
- SLA 수치는 실현 가능한 수준으로 (과도한 약속 지양)
- 장애 대응 절차 플로우차트 시각화
- 기술 이전 산출물 목록 표로 정리

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, SLA표·장애대응플로우 포함)",
  "self_check": {{
    "warranty_scope_clear": true,
    "sla_metrics_quantified": true,
    "incident_process_visualized": true,
    "knowledge_transfer_planned": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


SECTION_PROMPT_ADDED_VALUE = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션(부가제안/기대효과)을 작성하세요.

## 작성 핵심 포인트
이 섹션의 목적은 **"기본 요구사항을 넘어서는 추가 가치를 제공하겠다"**는 것입니다.
평가위원은 "이 업체가 기본 이상의 가치를 줄 수 있는가"를 봅니다.

사업과 무관한 부가 제안은 감점, **사업 목적과 연계된 부가 제안과
산출 근거가 있는 정량 효과를 제시한 제안서**가 최고점을 받습니다.
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략 방향
포지셔닝: {positioning} / Win Theme: {win_theme}

## 리서치 결과
{research_context}

## 필수 포함 요소
1. **부가 제안** — RFP에 없지만 사업 가치를 높이는 추가 제안 (2~3개, 사업 목적 연계)
2. **기대효과 (정량)** — 산출 근거 포함 (예: "연간 OO건 수작업 → 자동화 시 인건비 OO원 절감")
3. **기대효과 (정성)** — 조직 역량 강화, 대국민 서비스 개선 등
4. **향후 확장 로드맵** — 본 사업 완료 후 발전 방향
5. **차별화 특장점 요약** — 제안서 전체의 핵심 차별화를 한 눈에 (Win Theme 재강조)

## 주의사항
- 부가 제안은 사업 목적과 연결 (무관한 제안 금지)
- 기대효과 수치에 산출 근거 필수 (근거 없는 숫자 금지)
- 제안서 마무리 섹션으로, Win Theme을 다시 한번 강조

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
평가 배점: {eval_weight}점 → 권장 분량: {recommended_pages}
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "섹션 제목",
  "content": "본문 (Markdown, 기대효과표·로드맵 포함)",
  "self_check": {{
    "added_proposals_relevant": true,
    "quantitative_effects_with_basis": true,
    "future_roadmap_included": true,
    "win_theme_reinforced": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


# ── 케이스 B 전용 (서식 지정) ──

SECTION_PROMPT_CASE_B = """당신은 20년 경력의 용역 제안서 작성 전문가이자, 정부 제안 평가위원 출신입니다.
'{section_id}' 섹션을 **발주기관 지정 서식**에 맞춰 작성하세요.

## 서식 구조 (원본 보존 필수)
{template_structure}

## 섹션 유형: {section_type_name}
""" + EVALUATOR_PERSPECTIVE_BLOCK + """
## RFP 분석
{rfp_summary}

## 전략
포지셔닝: {positioning} / Win Theme: {win_theme}
핵심 메시지: {key_messages}

## 리서치 결과
{research_context}

## KB 참조
{kb_context}

## 유형별 작성 가이드
{section_type_guide}

## 서식 작성 규칙
1. **서식 구조(제목·번호·항목)를 정확히 보존**하고 내용만 채우세요
2. 서식에 없는 항목을 임의로 추가하지 마세요
3. 표 형식이 지정된 경우 표 구조를 유지하세요
4. 분량 제한이 있으면 정확히 지키세요
5. 유형별 작성 가이드의 필수 포함 요소를 서식 안에 녹여 넣으세요
6. **평가 세부항목에 대한 내용이 서식 안에 모두 대응되도록** 작성하세요

{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}

## 분량 가이드
{volume_spec}

## 출력 형식 (JSON)
{{
  "section_id": "{section_id}",
  "title": "서식 원본 제목",
  "content": "서식 구조 보존 + 내용 채움 (Markdown)",
  "template_preserved": true,
  "self_check": {{
    "template_structure_preserved": true,
    "no_extra_items_added": true,
    "section_type_guide_applied": true,
    "positioning_reflected": true,
    "eval_sub_items_all_addressed": true
  }}
}}
"""


# ── 유형별 간략 가이드 (케이스 B에서 참조) ──

SECTION_TYPE_GUIDES = {
    "UNDERSTAND": "발주기관 관점 재해석, AS-IS/TO-BE 비교표, 핫버튼 반영, 현황 데이터 인용, 과업범위 재구성",
    "STRATEGY": "Win Theme 선언, 전략 프레임워크 도표, 차별화 포인트 3가지, CSF, Ghost Theme 은연중 부각",
    "METHODOLOGY": "방법론 선택 근거, 사업 특화 커스터마이징, 단계별 수행활동·산출물 상세표, 품질 게이트, 프로세스 흐름도",
    "TECHNICAL": "구성도/아키텍처, 기술 선택 근거(비교표), 구체적 구현 방안, RFP 요구사항 1:1 대응표, 성능 수치",
    "MANAGEMENT": "추진 체계도, 마일스톤 일정표, 리스크 매트릭스(사업 특유), 품질 지표(정량), 보고 체계",
    "PERSONNEL": "인력 구성 전략, 핵심 인력 유사사업 경험, RACI 매트릭스, M/M 투입 계획, RFP 요구 자격 충족",
    "TRACK_RECORD": "유사성 매트릭스, 정량 성과, 현 사업 시사점, 검증 가능한 실적 정보",
    "SECURITY": "법령별 대응표(조항 명시), 기술/관리/물리적 보안 구체 방안, 개인정보 보호, 보안 체계도",
    "MAINTENANCE": "하자보수 범위, SLA 지표(정량), 장애 대응 플로우차트, 기술 이전 산출물 목록, 안정화 계획",
    "ADDED_VALUE": "사업목적 연계 부가 제안, 정량 기대효과(산출 근거), 향후 로드맵, Win Theme 재강조",
}


# ── 프롬프트 선택 함수 ──

SECTION_PROMPTS = {
    "UNDERSTAND": SECTION_PROMPT_UNDERSTAND,
    "STRATEGY": SECTION_PROMPT_STRATEGY,
    "METHODOLOGY": SECTION_PROMPT_METHODOLOGY,
    "TECHNICAL": SECTION_PROMPT_TECHNICAL,
    "MANAGEMENT": SECTION_PROMPT_MANAGEMENT,
    "PERSONNEL": SECTION_PROMPT_PERSONNEL,
    "TRACK_RECORD": SECTION_PROMPT_TRACK_RECORD,
    "SECURITY": SECTION_PROMPT_SECURITY,
    "MAINTENANCE": SECTION_PROMPT_MAINTENANCE,
    "ADDED_VALUE": SECTION_PROMPT_ADDED_VALUE,
}


def get_section_prompt(section_type: str) -> str:
    """섹션 유형에 맞는 프롬프트 반환."""
    return SECTION_PROMPTS.get(section_type, SECTION_PROMPT_TECHNICAL)


def get_recommended_pages(eval_weight: int, total_pages: int = 100) -> str:
    """평가 배점 기반 권장 분량 산출."""
    if eval_weight <= 0:
        return "2~3페이지"
    ratio = eval_weight / 100
    pages = max(2, round(total_pages * ratio))
    return f"약 {pages}페이지 (배점 {eval_weight}점 기준)"
