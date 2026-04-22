# STEP 2: 포지셔닝/전략 - 차별화 포인트 식별 프로세스

> **목적**: 실제 나라장터 공고를 가지고 STEP 2 워크플로가 제대로 작동하는지 **단계별 검증**  
> **Document**: strategy_generate.py + strategy.py 분석  
> **작성일**: 2026-04-21

---

## 1️⃣ STEP 2 입출력 구조

### 📥 Input (STEP 1에서 받은 데이터)

```
STEP 1 Go/No-Go 결과
├─ rfp_analysis (RFP 상세 분석)
│  ├─ client: 발주기관명
│  ├─ domain: 사업 분야
│  ├─ budget: 예산
│  ├─ requirements: 핵심 요구사항
│  └─ eval_method: 평가 방식
│
├─ go_no_go (판정 결과)
│  ├─ positioning: "defensive" | "offensive" | "adjacent"
│  ├─ positioning_rationale: 포지셔닝 근거
│  ├─ strategic_focus: 핵심 승부수 (예: "클라우드 마이그레이션 경험")
│  ├─ pros: 자사 강점
│  └─ risks: 주요 리스크
│
└─ research_brief (사전 조사 결과)
   ├─ client_history: 발주기관 과거 공고 이력
   ├─ market_data: 시장 동향
   └─ competitor_info: 경쟁사 정보
```

### 📤 Output (STEP 2 생성 결과)

```json
{
  "positioning": "offensive",
  "positioning_rationale": "클라우드 네이티브 기술 기반 혁신",
  
  "alternatives": [
    {
      "alt_id": "A",
      "ghost_theme": "경쟁사는 기존 인프라 기반 → 레거시 리스크",
      "win_theme": "우리는 클라우드 네이티브 경험이 풍부하기 때문에 확장성·비용효율 극대화 가능",
      "action_forcing_event": "발주기관의 DX 로드맵 실현 → 파트너 역량 증명",
      "key_messages": [
        "마이크로서비스 아키텍처 3건 경험",
        "클라우드 비용 최적화 평균 35% 절감",
        "국내 공공 클라우드 전환 5건 주도"
      ],
      "price_strategy": {
        "approach": "경쟁가격 (진입 가격: 낙찰률 90%)",
        "target_ratio": 0.90,
        "rationale": "시장 진입을 위한 전략적 가격, 프로젝트 수익성 강함"
      },
      "risk_assessment": {
        "key_risks": [
          "발주기관의 기술 수용도 불확실",
          "경쟁사의 기존 관계"
        ],
        "mitigation": [
          "기술이전 트레이닝 강화",
          "초기 1개월 협력팀 배치"
        ]
      }
    },
    {
      "alt_id": "B",
      "ghost_theme": "...",
      "win_theme": "...",
      "..."
    }
  ],
  
  "focus_areas": [
    {
      "area": "클라우드 아키텍처",
      "weight": 40,
      "strategy": "마이크로서비스 기반 설계 강조"
    },
    {
      "area": "비용 효율성",
      "weight": 35,
      "strategy": "TCO 분석 + 절감액 추정"
    },
    {
      "area": "리스크 관리",
      "weight": 25,
      "strategy": "phased migration 접근"
    }
  ],
  
  "competitor_analysis": {
    "swot_matrix": [
      {
        "competitor": "경쟁사 A",
        "strengths": ["기존 고객 관계", "정부 납기 경험"],
        "weaknesses": ["레거시 기술", "낮은 기술 혁신"],
        "response": "우리의 신기술 강점 부각"
      }
    ],
    "scenarios": {
      "best_case": "경쟁사가 가격으로만 공략 → 기술력 차별화",
      "base_case": "기술+가격 균형 경쟁 → 증명 자료(참고사례) 강화",
      "worst_case": "경쟁사가 저가+기술 공략 → 리스크 관리/품질 강조"
    }
  },
  
  "research_framework": {
    "research_questions": [
      "RQ1: 발주기관의 현재 IT 인프라 수준 → 클라우드 전환의 해결 과제?",
      "RQ2: 예산 범위 내 클라우드 마이그레이션 옵션?",
      "RQ3: 기술 팀의 클라우드 역량 수준?"
    ],
    "methodology_rationale": [
      "학술 타당성: SAP 클라우드 마이그레이션 프레임워크 사용",
      "실무 실현가능성: 6개월 timeline, 15명 팀",
      "차별성: 국내 공공 사례 기반 커스터마이제이션"
    ]
  }
}
```

---

## 2️⃣ 차별화 포인트 식별 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: 포지셔닝/전략 - 차별화 포인트 식별                          │
└─────────────────────────────────────────────────────────────────┘

① INPUT 데이터 수집
   ├─ RFP 분석 (STEP 1)
   ├─ Go/No-Go 결과 + 포지셋 팀
   ├─ KB 조회 (역량, 고객정보, 경쟁사, 교훈)
   └─ 리서치 브리프 + 가격 데이터
        │
        ▼

② 포지셔닝 전략 가이드 선택
   ├─ Defensive: "안정성·신뢰 → 기존 실적 강조"
   ├─ Offensive: "혁신·차별화 → 새로운 방법론"
   └─ Adjacent: "관련분야 확장 → 경험 이전"
        │
        ▼

③ Claude API 호출 (STRATEGY_GENERATE_PROMPT)
   ├─ 15개 Context 입력 (RFP, Go/No-Go, KB, 프레임워크)
   ├─ 토큰 예산: 25,000
   └─ Model: claude-sonnet-4-6
        │
        ▼

④ 전략 생성 (JSON 출력)
   ├─ Win Theme: "우리는 [X역량]이기 때문에 [Y성과]"
   ├─ Ghost Theme: "경쟁사는 [약점]"
   ├─ Action Forcing Event: "발주기관이 선택해야 하는 이유"
   ├─ Key Messages: 3~5개 핵심 메시지
   ├─ Price Strategy: 포지셔닝별 가격 접근법
   ├─ 2가지 이상 대안 (Alternative A, B)
   └─ Competitor Analysis: SWOT + 시나리오
        │
        ▼

⑤ 출력 검증 & 저장
   ├─ JSON 포맷 검증
   ├─ State에 저장
   └─ Next STEP (STEP 3: Plan 수립)
```

---

## 3️⃣ 핵심 프로세스 상세 설명

### 3.1 포지셔닝 선택 (Defensive / Offensive / Adjacent)

**코드** (`strategy_generate.py` L51):
```python
pos_guide = POSITIONING_STRATEGY_MATRIX.get(positioning, POSITIONING_STRATEGY_MATRIX["defensive"])
```

**3가지 포지셔닝 가이드**:

#### Defensive (수성)
```
label: "수성 (Defensive)"
core_message: "기존 신뢰와 실적 강조, 연속성과 안정성"
tone: "안정적이고 신뢰할 수 있는"
price_approach: "적정가격 — 기존 실적 대비 합리적 가격"
ghost_strategy: "경쟁사의 경험 부족, 새로운 팀의 리스크 부각"
key_focus: ["수행 실적 강조", "기관 이해도", "연속성·안정성", "리스크 최소화"]
```

**사용 시나리오**:
- 우리가 기존 고객사와 관계 있을 때
- 경쟁사가 신규 업체일 때
- 발주기관이 안정성을 중시할 때 (정부 기관)

---

#### Offensive (공격)
```
label: "공격 (Offensive)"
core_message: "혁신과 차별화, 새로운 관점과 방법론"
tone: "혁신적이고 도전적인"
price_approach: "경쟁가격 — 진입을 위한 전략적 가격"
ghost_strategy: "기존 수행사의 매너리즘, 새로운 시도 부재 부각"
key_focus: ["혁신 방법론", "차별화 포인트", "새로운 가치 제안", "공격적 인력 구성"]
```

**사용 시나리오**:
- 우리가 신기술/신방법론 경험 풍부할 때
- 기존 발주처가 낡은 솔루션일 때
- 발주기관이 DX/혁신을 추구할 때

---

#### Adjacent (인접)
```
label: "인접 (Adjacent)"
core_message: "관련 분야 전문성의 자연스러운 확장"
tone: "전문적이면서 유연한"
price_approach: "합리적 가격 — 관련 실적 기반 비용 효율성"
ghost_strategy: "핵심 분야 전문성 대비 타 분야 경험 한계 부각"
key_focus: ["관련분야 실적 전이", "융합 역량", "학습 곡선 최소화", "시너지 효과"]
```

**사용 시나리오**:
- 우리가 인접 분야 실적 있을 때
- 발주기관의 니즈가 기존+신규 혼합일 때

---

### 3.2 Context 입력 (15개 변수)

**코드** (`strategy_generate.py` L135-163):

```python
prompt = (reg_text or STRATEGY_GENERATE_PROMPT).format(
    rfp_summary=rfp_summary,                    # ① RFP 요약
    positioning=positioning,                    # ② 포지셔닝 (defensive/offensive/adjacent)
    positioning_label=pos_guide["label"],       # ③ 포지셔닝 라벨
    positioning_rationale=gng_dict.get(...),   # ④ Go/No-Go에서 도출한 근거
    pros=gng_dict.get("pros", []),             # ⑤ 자사 강점
    risks=gng_dict.get("risks", []),           # ⑥ 주요 리스크
    strategic_focus=strategic_focus,            # ⑦ 핵심 승부수
    positioning_guide=_format_positioning_guide(...), # ⑧ 포지셔닝 가이드
    capabilities_text=kb.get("capabilities"), # ⑨ 자사 역량
    research_brief=research_text,               # ⑩ 사전 조사 리서치
    client_intel_text=kb.get("client_intel"), # ⑪ 발주기관 정보
    competitor_text=kb.get("competitors"),     # ⑫ 경쟁사 정보
    lessons_text=kb.get("lessons"),             # ⑬ 과거 교훈
    competitor_history_text=kb.get(...),       # ⑭ 경쟁사 대전 기록
    competitive_analysis_framework=...,        # ⑮ 경쟁분석 프레임워크
    strategy_research_framework=...             # ⑯ 연구수행 프레임워크
)
```

---

### 3.3 Claude API 호출 & 차별화 포인트 생성

**프롬프트의 핵심 지시사항** (`strategy.py` L116-123):

```
## 지시사항
1. Win Theme 구조: "우리는 [X역량/경험]이기 때문에 [Y성과]를 가장 잘 할 수 있다"
   - 핵심 승부수를 Win Theme의 중심축으로 구체화하세요
   - 각 Win Theme에 supporting evidence 최소 2개 (리서치 근거 데이터 우선 활용)

2. Ghost Theme: 경쟁사 약점을 간접적으로 부각하는 메시지

3. Action Forcing Event: 발주기관이 "반드시 우리를 선택해야 하는" 결정적 이유

4. 핵심 메시지 3~5개 (평가위원 머릿속에 남길 키워드)

5. 가격 전략: 포지셔닝에 맞는 가격 접근법

6. 반드시 2가지 이상의 전략 대안(Alternative)을 제시하세요
```

**Claude가 생성하는 차별화 포인트 예시**:

| 요소 | 예시 |
|------|------|
| **Win Theme** | "우리는 클라우드 마이그레이션 5건 경험이 있기 때문에 발주기관의 비용 최적화 목표를 30% 단축으로 달성 가능" |
| **Ghost Theme** | "기존 수행사는 온프레미스 중심 경험만 있어 클라우드 네이티브 아키텍처 구축에 학습곡선 존재" |
| **Action Forcing Event** | "발주기관의 2026년 클라우드 전환 로드맵 → 우리의 기술 리더십이 성공 핵심" |
| **Key Messages** | ["마이크로서비스 아키텍처", "비용 35% 절감 사례", "국내 공공 클라우드 전환 5건 주도"] |
| **Price Strategy** | "경쟁가격 90% (낙찰률 기반 진입가)" |

---

## 4️⃣ 실제 검증 체크리스트

### 🔍 나라장터 공고로 STEP 2 검증하기

**사전 준비**:
1. 나라장터에서 실제 공고 1개 선정 (예: IT 서비스, 예산 5-10억원)
2. STEP 1 완료 (RFP 분석 + Go/No-Go 결과 생성)
3. Staging 환경에 KB 데이터 준비

**검증 체크리스트**:

```
STEP 2 실행 후 다음을 확인하세요:

① 출력 형식 (JSON)
  ☐ "positioning" 필드 존재 (defensive/offensive/adjacent 중 1개)
  ☐ "alternatives" 배열 존재 (최소 2개)
  ☐ 각 alternative에 alt_id, ghost_theme, win_theme, action_forcing_event 포함
  ☐ key_messages 배열 (3~5개 항목)
  ☐ price_strategy 객체 (approach, target_ratio, rationale)

② Win Theme 품질
  ☐ "우리는 [역량]이기 때문에 [성과]" 구조 명확한가?
  ☐ Strategic focus (Go/No-Go에서의 승부수)가 중심축인가?
  ☐ Supporting evidence 2개 이상 있는가?
  ☐ 발주기관의 평가기준과 연결되는가?

③ Ghost Theme 품질
  ☐ 경쟁사 약점이 간접적(슬쩍)으로 표현되는가?
  ☐ 우리의 강점과 대조되는가?
  ☐ 증명 불가능한 명백한 거짓이 아닌가?

④ Action Forcing Event 설득력
  ☐ 발주기관이 "반드시 우리를 선택해야 하는" 이유인가?
  ☐ RFP의 핵심 요구사항과 연결되는가?
  ☐ 독점적이거나 배타적인 역량인가?

⑤ Key Messages 임팩트
  ☐ 3~5개 메시지가 평가위원 머릿속에 남을 만큼 명확한가?
  ☐ 각 메시지가 구체적 근거를 가지는가?
  ☐ 메시지들이 일관된 스토리를 만드는가?

⑥ Price Strategy 타당성
  ☐ 포지셔닝과 가격 접근법이 일치하는가?
  ☐ Target ratio가 합리적인가? (defensive: 95-100%, offensive: 85-95%, adjacent: 90-100%)
  ☐ 가격 근거 (rationale)가 설득력 있는가?

⑦ Competitor Analysis 깊이
  ☐ 경쟁사 SWOT가 구체적인가?
  ☐ Best/Base/Worst case 시나리오가 현실적인가?
  ☐ 각 시나리오에 대한 우리의 대응책이 있는가?

⑧ Research Framework 적실성
  ☐ Research questions이 RFP의 핵심 과업과 관련있는가?
  ☐ 제시된 방법론이 이 문제를 해결할 수 있는가?
  ☐ 인력/기간/예산으로 실행 가능한가?

⑨ 대안(Alternative) 다양성
  ☐ Alternative A와 B의 차이가 명확한가? (예: 기술 수준, 가격, 일정)
  ☐ 각 대안이 다른 리스크/기회를 타겟하는가?
  ☐ 발주기관의 선택에 따라 맞춤 가능한 형태인가?

⑩ 생성 시간 & 토큰 사용량
  ☐ 생성 시간이 2분 이내인가? (목표: < 120초)
  ☐ 토큰 사용량이 예산(25,000) 내인가?
  ☐ 에러 메시지 없는가?
```

---

## 5️⃣ 실제 사례 예상 결과

### 공고 예시: "정부 클라우드 기반 데이터 통합 플랫폼 구축"

**Input**:
```
Client: OOO부 정보기술실
Domain: 클라우드 데이터 통합
Budget: 8억원
Timeline: 12개월
Requirements: 마이크로서비스 아키텍처, 데이터 보안, 스케일러빌리티
Evaluation: 기술점(50%) + 가격(30%) + 제안수행능력(20%)
```

**STEP 1 Output** (Go/No-Go):
```
positioning: "offensive"
positioning_rationale: "클라우드 네이티브 기술력이 차별화"
strategic_focus: "마이크로서비스 아키텍처 & 데이터 메싱"
pros: ["클라우드 마이그레이션 5건", "K8s 운영 경험 2년"]
risks: ["정부 납기 경험 부족", "보안 심사 미경험"]
```

**예상 STEP 2 Output** (포지셔닝/전략):

```json
{
  "positioning": "offensive",
  "alternatives": [
    {
      "alt_id": "A",
      "ghost_theme": "기존 수행사는 온프레미스 중심 → 클라우드 아키텍처 경험 제한",
      "win_theme": "우리는 마이크로서비스 기반 5건 경험이 있기 때문에 발주기관의 확장성·비용효율 동시 달성",
      "action_forcing_event": "2026년 정부 클라우드 정책 전환 → 이에 맞춘 차세대 아키텍처가 필수",
      "key_messages": [
        "마이크로서비스 5건 운영 경험",
        "클라우드 비용 최적화 35% 절감 사례",
        "국내 정부 클라우드 전환 프로젝트 주도"
      ],
      "price_strategy": {
        "approach": "경쟁가격 (낙찰률 90%)",
        "target_ratio": 0.90,
        "rationale": "혁신기술 진입가격, 프로젝트 수익성 강함"
      }
    },
    {
      "alt_id": "B",
      "ghost_theme": "경쟁사는 기술력만 강조 → 운영 안정성 검증 부족",
      "win_theme": "우리는 K8s 운영 경험 2년이 있기 때문에 발주기관의 안정적 운영 보장",
      "action_forcing_event": "정부 시스템은 운영 안정성이 최우선 → 우리의 경험이 핵심",
      "key_messages": [
        "K8s 프로덕션 운영 2년 경험",
        "정부 시스템 무중단 운영 기록",
        "클라우드 운영 자동화 도구 자체개발"
      ],
      "price_strategy": {
        "approach": "적정가격 (낙찰률 95%)",
        "target_ratio": 0.95,
        "rationale": "안정성 강조, 장기 운영 계약으로 수익성"
      }
    }
  ],
  "focus_areas": [
    {
      "area": "마이크로서비스 아키텍처",
      "weight": 40,
      "strategy": "K8s 기반 설계 + 자동 스케일링"
    },
    {
      "area": "데이터 보안",
      "weight": 35,
      "strategy": "정부 보안기준 준수 (ISMS, CC) + 암호화 전략"
    },
    {
      "area": "운영 안정성",
      "weight": 25,
      "strategy": "자동화 모니터링 + 24/7 SLA"
    }
  ],
  "competitor_analysis": {
    "swot_matrix": [
      {
        "competitor": "경쟁사 A (기존 구축사)",
        "strengths": ["정부 납기 경험", "기존 고객 관계"],
        "weaknesses": ["레거시 기술", "클라우드 경험 부족"],
        "response": "혁신 기술력으로 차별화"
      },
      {
        "competitor": "경쟁사 B (신기술 회사)",
        "strengths": ["최신 기술", "혁신 인력"],
        "weaknesses": ["운영 경험 부족", "정부 경험 없음"],
        "response": "운영 안정성·정부 경험 강조"
      }
    ],
    "scenarios": {
      "best_case": "경쟁사 A가 저가로만 공략 → 기술력 차별화로 우위",
      "base_case": "기술+가격 균형 경쟁 → 우리의 경험+혁신 조합 강점",
      "worst_case": "경쟁사 B가 신기술+저가 공략 → 운영 안정성·정부 경험으로 방어"
    }
  },
  "research_framework": {
    "research_questions": [
      "RQ1: 발주기관의 현재 데이터 통합 수준 → 클라우드 전환 시 해결과제?",
      "RQ2: 데이터 보안/정부 컴플라이언스 요구사항 상세 분석?",
      "RQ3: 예산 범위 내 마이크로서비스 도입 로드맵?"
    ],
    "methodology_rationale": [
      "학술 타당성: Netflix/Uber 마이크로서비스 패턴 적용",
      "실무 실현가능성: 6개월 구축, 12명 팀 (예산 내)",
      "차별성: 국내 정부 클라우드 정책 기반 커스터마이제이션"
    ]
  }
}
```

---

## 6️⃣ 실제 워크플로 검증 가이드

### 나라장터 공고 선택 & STEP 2 실행

**Step by Step**:

```
1️⃣ 나라장터 공고 선택 (2시간)
   └─ 분야: IT/클라우드
   └─ 예산: 5-10억원
   └─ 분야별 경쟁사 3-5개 있을 것
   
2️⃣ STEP 0 & 1 완료 (2-3시간)
   └─ RFP 수집 및 분석
   └─ Go/No-Go 판정
   └─ Positioning 결정
   
3️⃣ STEP 2 실행 (5분)
   └─ strategy_generate.py 호출
   └─ Claude API 응답 수신
   
4️⃣ 출력 검증 (30분)
   └─ 위 체크리스트 ① ~ ⑩ 확인
   └─ 각 항목별 Pass/Fail 기록
   
5️⃣ 결과 분석 (1시간)
   └─ Win Theme이 설득력 있는가?
   └─ Ghost Theme이 경쟁사 약점을 정확히 칭했는가?
   └─ 2가지 대안의 차별화가 명확한가?
   └─ 가격 전략이 포지셔닝과 일치하는가?
```

---

## 7️⃣ 발견된 이슈 대응

### 만약 다음 문제가 생기면:

| 문제 | 원인 | 해결책 |
|------|------|--------|
| **Win Theme이 너무 일반적** | KB 데이터 부족 또는 Strategic focus 모호 | KB에 구체적 프로젝트 사례 추가, Go/No-Go 재검토 |
| **경쟁사 정보 부족으로 Ghost Theme 약함** | KB의 competitor 데이터 부족 | 나라장터 낙찰 정보 크롤링, 시장조사 추가 |
| **Alternative A와 B 차이 불명확** | 프롬프트가 대안 생성 충분히 강제하지 못함 | 프롬프트 L123 강화 (대안별 시나리오 명시) |
| **Price Strategy 타당성 낮음** | PricingEngine 데이터 부족 또는 포지셔닝 불일치 | Bid calculator 확인, 포지셔닝 재검토 |
| **Research Framework이 RFP와 관련 없음** | 프롬프트의 research_questions 생성이 약함 | RFP requirements 더 구체적으로 입력 |
| **JSON 파싱 오류** | Claude 응답이 완전한 JSON 아님 | 프롬프트 output format 강화, 재시도 |

---

## 📋 최종 검증 체크리스트 (실행 전)

```
STEP 2 차별화 포인트 식별 워크플로 검증

필수 확인 사항:
☐ 나라장터 공고 선택됨 (URL/공고번호 기록)
☐ STEP 1 완료 (RFP 분석 + Go/No-Go)
☐ KB 데이터 충분 (경쟁사 정보 최소 3개)
☐ Staging 환경 접근 가능
☐ Claude API 토큰 충분 (25,000 이상)

실행 후 검증:
☐ 출력 JSON 형식 정상
☐ Win Theme 품질 (← 가장 중요!)
☐ 2가지 Alternative 명확한 차이
☐ Ghost Theme 설득력
☐ Action Forcing Event 독특성
☐ Key Messages 3~5개 명확함
☐ Price Strategy 타당성
☐ Competitor Analysis 깊이
☐ Research Framework 실행 가능성
☐ 생성 시간 < 2분

이슈 기록:
☐ 발견된 이슈 (있으면 기록)
☐ 개선 사항 (다음 반복에 적용할 것)
```

---

**다음 STEP**: 이 출력을 바탕으로 STEP 3 (Plan/Team/Schedule 수립)로 진행
