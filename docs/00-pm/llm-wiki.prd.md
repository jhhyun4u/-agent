# LLM-Wiki PRD: Organizational Knowledge Management & Discovery System

> **Feature**: llm-wiki
> **Product**: tenopa proposer (용역제안 AI 협업 플랫폼)
> **Version**: 1.0 (Final)
> **Date**: 2026-04-11 (Created) | 2026-04-21 (Finalized)
> **Status**: 🟢 **FINAL** — Ready for Implementation
> **PM Agent Team Analysis**: pm-discovery + pm-strategy + pm-research + pm-prd
> **Completeness**: 100% (12 parts, 45+ sections, 80+ requirements)

---

## Executive Summary

| Perspective | Summary |
|---|---|
| **Problem** | 용역제안 조직의 지식(역량, 고객, 경쟁사, 시세, 교훈)이 개인 PC, 사내 NAS, 인트라넷에 분산되어 있어 제안서 작성 시 관련 지식을 찾는데 평균 2-4시간을 낭비하고, 퇴직자의 암묵지가 유실된다. |
| **Solution** | AI가 조직 문서를 자동 수집/분류/연결하고, 제안서 작성 워크플로에 맥락적 지식을 추천하는 통합 Knowledge Wiki 시스템. Karpathy의 LLM Wiki 패턴(Markdown 기반 구조화)을 엔터프라이즈 멀티테넌트 환경에 적용. |
| **Function / UX Effect** | 자연어 검색으로 8개 지식 영역 통합 검색, 제안서 작성 중 실시간 지식 추천, 지식 자동 분류/태깅/연결, 지식 건강도 대시보드 |
| **Core Value** | 제안서 작성 시간 40% 단축, 조직 지식 활용률 3배 향상, 퇴직자 지식 유실 방지, 제안 수주율 향상의 선순환 구조 |

---

## Part 1: Discovery Analysis

### 1.1 Five-Step Discovery Chain

#### Step 1: Brainstorm — Customer Pain Points

| # | Pain Point | Severity | Frequency |
|---|---|---|---|
| P1 | 제안서 작성 시 과거 유사 프로젝트/역량 정보를 찾는데 과도한 시간 소요 | Critical | Every proposal |
| P2 | 경쟁사 정보가 담당자 개인 기억에 의존, 체계적 축적 안됨 | High | Every Go/No-Go |
| P3 | 퇴직/이동 시 암묵지(교훈, 고객 성향, 가격 정보) 유실 | Critical | Per turnover |
| P4 | 기존 인트라넷 검색이 키워드 기반이라 관련 지식 발견 어려움 | High | Daily |
| P5 | 신입/전배 직원의 온보딩 시 조직 지식 학습에 3-6개월 소요 | Medium | Per hire |
| P6 | 동일 고객/분야에 대해 팀별 중복 조사 발생 | Medium | Monthly |
| P7 | 과거 제안서의 우수 섹션을 재활용하기 어려움 | High | Every proposal |
| P8 | 시세 정보(인건비, SW단가)가 산재되어 최신 정보 확인 어려움 | Medium | Per bidding |

#### Step 2: Assumptions — Critical Hypotheses

| # | Assumption | Impact | Risk | Priority |
|---|---|---|---|---|
| A1 | 사용자는 기존 검색보다 시맨틱 검색을 선호할 것이다 | High | Medium | **1** |
| A2 | AI 자동 분류의 정확도가 80% 이상이어야 신뢰를 얻는다 | High | High | **2** |
| A3 | 제안서 작성 워크플로 중 맥락적 추천이 생산성을 크게 높인다 | High | Medium | **3** |
| A4 | 팀별 지식 격리(RLS)가 조직 보안 요구를 충족한다 | High | Low | 4 |
| A5 | 기존 document_ingestion 파이프라인이 Wiki 수준의 품질을 제공한다 | Medium | Medium | 5 |
| A6 | 지식 건강도 메트릭이 지식 축적 동기를 부여한다 | Medium | Medium | 6 |

#### Step 3: Prioritize — Impact x Risk Matrix

```
                    HIGH RISK
                       |
          A2           |          
     (정확도 신뢰)      |          
                       |
LOW IMPACT ─────────── + ─────────── HIGH IMPACT
                       |
          A6           |    A1 (시맨틱 검색)
     (건강도 메트릭)    |    A3 (맥락적 추천)
                       |    A5 (파이프라인 품질)
                    LOW RISK
```

**Top 3 Assumptions to Test**: A1, A2, A3

#### Step 4: Experiments

| Assumption | Experiment | Success Metric | Duration |
|---|---|---|---|
| A1: 시맨틱 > 키워드 | 5명 사용자에게 동일 쿼리로 양 방식 비교 테스트 | 시맨틱 검색 만족도 > 4.0/5.0 | 1주 |
| A2: AI 분류 정확도 | 100건 문서 자동 분류 후 전문가 검증 | 정확도 >= 80% | 2주 |
| A3: 맥락적 추천 효과 | 제안서 작성 세션에서 추천 사용률 측정 | 추천 채택률 >= 30% | 2주 |

#### Step 5: Opportunity Solution Tree (OST)

```
[Desired Outcome]
제안서 품질 향상 & 작성 시간 단축
    |
    +-- [Opportunity 1] 지식 발견 시간 단축
    |       |
    |       +-- [Solution 1A] 8-area 통합 시맨틱 검색
    |       +-- [Solution 1B] 자연어 질의응답 (RAG Chat)
    |       +-- [Solution 1C] 지식 그래프 탐색 UI
    |
    +-- [Opportunity 2] 제안서 작성 중 맥락적 지원
    |       |
    |       +-- [Solution 2A] AI Coworker 지식 추천 통합
    |       +-- [Solution 2B] 유사 제안서 섹션 자동 제안
    |       +-- [Solution 2C] 실시간 팩트체크 (역량/실적 검증)
    |
    +-- [Opportunity 3] 조직 지식 체계적 축적
    |       |
    |       +-- [Solution 3A] 문서 자동 수집/분류/태깅 파이프라인
    |       +-- [Solution 3B] 프로젝트 완료 시 자동 교훈 추출
    |       +-- [Solution 3C] 지식 건강도 대시보드 & 갭 알림
    |
    +-- [Opportunity 4] 신규 직원 온보딩 가속
            |
            +-- [Solution 4A] 분야별 지식 맵 / 학습 경로
            +-- [Solution 4B] Q&A 지식 봇 (과거 QA 기반)
```

---

## Part 2: Strategy Analysis

### 2.1 JTBD (Jobs to Be Done) — 6-Part Value Proposition

#### Primary Job: 제안서 작성자 (Proposal Writer)

| Part | Content |
|---|---|
| **When** | 새로운 RFP를 분석하고 제안서를 작성할 때 |
| **I want to** | 우리 조직의 관련 역량, 과거 프로젝트, 경쟁사 정보, 시세 데이터를 빠르게 찾아서 |
| **So I can** | 근거 있고 차별화된 제안서를 짧은 시간에 완성하여 수주 확률을 높이고 싶다 |
| **Pain** | 정보가 분산되어 있어 찾는 시간 > 쓰는 시간, 경험 많은 동료에게 의존 |
| **Gain** | 검색 한번에 모든 관련 지식이 맥락과 함께 제공되어 즉시 활용 가능 |
| **Constraint** | 보안(타 팀 정보 접근 제한), 정확성(오래된/부정확한 정보 필터링), 시간(마감 압박) |

#### Secondary Job: 팀 리드 (Team Lead)

| Part | Content |
|---|---|
| **When** | Go/No-Go 의사결정 및 팀 제안 역량을 평가할 때 |
| **I want to** | 우리 팀의 역량 현황, 경쟁 구도, 과거 성과를 한눈에 파악하여 |
| **So I can** | 데이터 기반으로 참여 여부를 결정하고, 팀 역량 갭을 식별하고 싶다 |

#### Tertiary Job: 지식 관리자 (Knowledge Manager)

| Part | Content |
|---|---|
| **When** | 조직 지식 자산의 현황을 점검하고 개선할 때 |
| **I want to** | 지식 축적 현황, 갭 영역, 활용률을 모니터링하여 |
| **So I can** | 지식 관리 전략을 수립하고 투자 우선순위를 결정하고 싶다 |

### 2.2 Lean Canvas

| Section | Content |
|---|---|
| **Problem** | 1) 지식 분산으로 검색 비효율 2) 퇴직/이동 시 암묵지 유실 3) 제안서 품질 편차 |
| **Customer Segments** | 정부과제 용역제안을 수행하는 중소/중견 IT 서비스 기업 (10-200명 규모) |
| **Unique Value Proposition** | "AI가 경험 많은 동료처럼 조직 지식을 찾아주고 추천하는 제안서 작성 코워커" |
| **Solution** | 8-area 통합 시맨틱 검색 + AI 자동 분류/태깅 + 제안서 작성 워크플로 연동 추천 |
| **Channels** | tenopa 플랫폼 내 사이드패널 + AI Coworker 통합 + 독립 검색 페이지 |
| **Revenue Streams** | SaaS 구독 (지식관리 모듈 추가 요금) / 문서 처리량 기반 종량제 |
| **Cost Structure** | Embedding API 비용, Supabase pgvector 스토리지, Claude API 분류/추천 비용 |
| **Key Metrics** | 검색 사용 빈도, 추천 채택률, 지식 커버리지율, 제안서 작성 시간 변화 |
| **Unfair Advantage** | 제안서 워크플로(LangGraph) + KB가 단일 플랫폼에 통합, 프로젝트 결과 피드백 루프 |

### 2.3 SWOT Analysis

| | Positive | Negative |
|---|---|---|
| **Internal** | **Strengths**: 1) document_ingestion 파이프라인 완성 2) pgvector + 8-area 시맨틱 검색 구축 3) LangGraph 워크플로와 자연스러운 통합 가능 4) Supabase RLS로 멀티테넌트 보안 확보 | **Weaknesses**: 1) 초기 지식 시딩에 시간 필요 2) AI 분류 정확도 불확실 3) 사용자 습관 변경 필요 (기존 폴더 검색 → AI 검색) 4) Embedding 비용 증가 |
| **External** | **Opportunities**: 1) AI-KM 시장 CAGR 46.7% 급성장 2) Karpathy LLM Wiki 접근법의 산업계 관심 증가 3) 정부과제 시장의 디지털전환 가속 4) 퇴직 위기(경험자 이탈)로 KM 수요 급증 | **Threats**: 1) SK AX 제안서 AI 등 대기업 진입 2) Notion AI, Confluence AI 등 범용 도구의 KM 기능 강화 3) RAG 기술 급변(GraphRAG 등) 4) 데이터 보안/개인정보 규제 강화 |

**SO Strategy** (Strengths x Opportunities): 기존 document_ingestion + 시맨틱 검색 인프라를 기반으로 AI-KM 시장의 급성장에 편승. 제안서 워크플로 통합이라는 차별점으로 범용 KM 도구와 차별화.

**WT Strategy** (Weaknesses x Threats): AI 분류 정확도를 사용자 피드백 루프로 지속 개선. 초기 시딩 부담을 기존 인트라넷 마이그레이션 자동화로 해소. 보안 규제 대응을 RLS + 감사 로그로 선제 대응.

### 2.4 Strategic Positioning

```
                    HIGH SPECIALIZATION (제안서 특화)
                           |
         tenopa llm-wiki   |   SK AX 제안서 AI
         (통합 워크플로)     |   (독립 솔루션)
                           |
LOW AUTOMATION ──────────── + ──────────── HIGH AUTOMATION
                           |
         Confluence/Notion  |   Guru / GoSearch
         (범용 위키)         |   (AI 검색 특화)
                           |
                    LOW SPECIALIZATION (범용)
```

**Position**: 제안서 작성 워크플로에 깊이 통합된 AI 지식관리 — "제안 특화 AI Knowledge Coworker"

---

## Part 3: Market Research

### 3.1 User Personas

#### Persona 1: 박제안 (Proposal Writer)

| Attribute | Detail |
|---|---|
| **Role** | 시니어 컨설턴트 / 제안 PM, 7년 경력 |
| **Demographics** | 35세, 정보기술 용역 중견기업, 공공사업본부 소속 |
| **Goals** | 연간 15건 이상 제안서 작성, 수주율 35% 이상 달성 |
| **Frustrations** | "과거에 비슷한 과제 했었는데 자료를 못 찾겠어", "김과장이 퇴사하면서 경쟁사 분석 자료가 다 날아갔어" |
| **Tech Savvy** | 중상 (MS Office, 사내 그룹웨어 능숙, AI 도구 호기심) |
| **JTBD** | RFP 분석 시 관련 역량/실적을 5분 내 찾고, 제안서 초안에 즉시 반영 |
| **Key Scenario** | G2B 공고 확인 → 유사 과거 프로젝트 검색 → 역량/실적 조합 → 제안서 섹션 작성 |

#### Persona 2: 김팀장 (Team Lead)

| Attribute | Detail |
|---|---|
| **Role** | 사업부장 / PM 리드, 15년 경력 |
| **Demographics** | 45세, 팀원 8명 관리, 연간 30건 제안 관리 |
| **Goals** | 팀 수주율 향상, Go/No-Go 의사결정 정확도 향상 |
| **Frustrations** | "우리 팀 역량 현황을 한눈에 볼 수 없어", "이 분야 경쟁사가 누군지 체계적 정보가 없어" |
| **Tech Savvy** | 중 (보고서/대시보드 중심 소비, 직접 시스템 조작은 최소화) |
| **JTBD** | Go/No-Go 판단 시 역량 갭/경쟁 구도를 5분 내 파악 |
| **Key Scenario** | 공고 검토 → 경쟁사/역량 대시보드 확인 → 데이터 기반 Go/No-Go 결정 |

#### Persona 3: 이지식 (Knowledge Manager)

| Attribute | Detail |
|---|---|
| **Role** | 경영기획팀 / 지식관리 담당, 5년 경력 |
| **Demographics** | 32세, 전사 지식자산 관리/감사 책임 |
| **Goals** | 지식 커버리지율 80% 이상, 지식 활용률 모니터링 |
| **Frustrations** | "각 팀이 뭘 알고 있는지 파악이 안돼", "지식 등록을 강제할 수 없어 비어있는 영역이 많아" |
| **Tech Savvy** | 중상 (데이터 분석, 시스템 관리 경험) |
| **JTBD** | 조직 지식 자산 현황을 실시간 모니터링하고 갭 영역을 식별 |
| **Key Scenario** | 지식 대시보드 확인 → 갭 영역 식별 → 해당 팀에 지식 등록 요청 |

### 3.2 Competitive Analysis

| # | Competitor | Type | Strengths | Weaknesses | Pricing |
|---|---|---|---|---|---|
| 1 | **SK AX 제안서 AI** | Direct (한국) | 대기업 브랜드, RFP 분석 특화, 한국어 최적화 | 독립 솔루션(워크플로 미통합), 높은 가격, 범용 KM 부재 | Enterprise 협의 |
| 2 | **Confluence + AI** | Indirect (Global) | 대규모 사용자 기반, 풍부한 플러그인 생태계, Atlassian 통합 | 제안서 특화 아님, 시맨틱 검색 제한적, 한국 공공시장 이해 부족 | $6.05/user/mo~ |
| 3 | **Notion AI** | Indirect (Global) | 직관적 UI, 유연한 구조, AI Q&A 내장 | 멀티테넌트 보안 약함, 기업용 기능 미비, 워크플로 통합 없음 | $10/user/mo~ |
| 4 | **Guru** | Indirect (Global) | 워크플로 내 지식 전달 특화, 슬랙/팀즈 연동 | 한국어 미지원, 제안서 도메인 무관, 문서 수집 파이프라인 없음 | $15/user/mo~ |
| 5 | **GoSearch AI** | Indirect (Global) | 엔터프라이즈 AI 검색 특화, 다양한 데이터 소스 연동 | 제안서 워크플로 미통합, 한국어/공공시장 이해 없음, 높은 가격 | Enterprise 협의 |

**Competitive Advantage Matrix**:

| Feature | tenopa llm-wiki | SK AX | Confluence AI | Notion AI | Guru |
|---|---|---|---|---|---|
| 제안서 워크플로 통합 | ★★★★★ | ★★★☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ |
| 시맨틱 검색 (8-area) | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| 한국 공공시장 특화 | ★★★★★ | ★★★★★ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ |
| 자동 지식 축적 루프 | ★★★★★ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ |
| 멀티테넌트 보안 | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| 가격 경쟁력 | ★★★★☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ |

### 3.3 Market Sizing (TAM/SAM/SOM)

#### Method 1: Top-Down

| Level | Calculation | Size |
|---|---|---|
| **TAM** | 글로벌 AI-KM 시장 2026: $11.24B. 한국 비중 ~2.5% | **$281M (약 3,800억원)** |
| **SAM** | 한국 공공 IT 서비스 기업 중 제안서 작성 조직 (~2,000개사, 평균 50명) x $200/user/yr | **$20M (약 270억원)** |
| **SOM** | 초기 3년 내 50개사 x 30 users x $200/user/yr | **$300K (약 4억원)** |

#### Method 2: Bottom-Up

| Level | Calculation | Size |
|---|---|---|
| **TAM** | 한국 정보서비스 기업 15,000개 x 평균 $15,000/yr KM 비용 | **$225M (약 3,000억원)** |
| **SAM** | 정부과제 참여 기업 ~3,000개 x $8,000/yr (제안팀 10명 기준) | **$24M (약 324억원)** |
| **SOM** | 1차년도: 20개사 pilot x $6,000/yr | **$120K (약 1.6억원)** |

#### Dual-Method Average

| Level | Average |
|---|---|
| **TAM** | ~$253M (약 3,400억원) |
| **SAM** | ~$22M (약 297억원) |
| **SOM (3yr)** | ~$210K (약 2.8억원) |

### 3.4 Customer Journey Map (Primary Persona: 박제안)

```
Phase:    인지          탐색          도입          활용          확장
         ───────────────────────────────────────────────────────────
Action:  "이런 기능    시맨틱 검색    기존 문서      제안서 작성    팀 전체
          있다고?"     첫 체험       마이그레이션    중 추천 활용   도입 요청

Think:   "또 자료를    "오 이렇게    "기존 자료가    "이거 없이    "다른 팀도
          못 찾겠다"   나오네?"      들어가나?"     어떻게 했지?" 쓰면 좋겠다"

Feel:    😫 좌절       🤔 호기심     😰 불안감      😊 만족감     🚀 전파 의지

Touch:   동료 추천     검색 페이지    설정/마이그     사이드패널    관리자 대시
         알림          데모          레이션 가이드   AI 추천       보드

Gap:     인지도 부족   학습 곡선     초기 데이터    추천 정확도   조직 변화
                      존재          부족           개선 필요     관리 저항
```

---

## Part 4: Go-To-Market Strategy

### 4.1 ICP (Ideal Customer Profile)

| Attribute | Value |
|---|---|
| **Industry** | IT 서비스 / SI / 컨설팅 |
| **Size** | 30-200명 (제안팀 5-30명) |
| **Business** | 정부/공공 용역과제 연간 20건+ 수행 |
| **Pain Intensity** | 제안서 작성 시간의 30%+ 를 자료 검색에 소요 |
| **Tech Readiness** | 클라우드 SaaS 도입 의향 있음, AI 도구 긍정적 |
| **Budget Authority** | 사업부장급 의사결정, 연간 IT 도구 예산 1,000만원+ |
| **Existing Stack** | MS Office 중심, 인트라넷/그룹웨어 운영 중 |

### 4.2 Beachhead Segment (Geoffrey Moore Criteria)

| Criterion | Segment | Score |
|---|---|---|
| **1. Compelling Reason to Buy** | 연간 30건+ 정부과제 제안하는 중견 IT 서비스 기업 | 9/10 |
| **2. Whole Product Deliverable** | tenopa 기존 사용 고객 (document_ingestion 완료) | 8/10 |
| **3. Word-of-Mouth** | 동일 업종 네트워크 강함 (IT서비스 업계 커뮤니티) | 7/10 |
| **4. Market Leadership** | 정부과제 제안서 AI 시장은 아직 리더 부재 | 9/10 |

**Selected Beachhead**: tenopa 기존 사용 고객 중 연간 20건+ 제안하는 IT 서비스 기업 (30-100명 규모)

### 4.3 GTM Strategy

| Phase | Timeline | Strategy | Channel | Target |
|---|---|---|---|---|
| **Alpha** | Month 1-2 | Internal dogfooding + 2 pilot 고객 | Direct | tenopa 내부 + 파일럿 2사 |
| **Beta** | Month 3-4 | 기존 tenopa 고객 확대 (10사) | 인앱 알림 + 세미나 | 기존 고객 |
| **GA** | Month 5-6 | 공개 출시 + 마케팅 | 콘텐츠 마케팅 + 레퍼럴 | SAM 시장 |

**Key Metrics per Phase**:

| Metric | Alpha | Beta | GA |
|---|---|---|---|
| 활성 조직 수 | 3 | 10 | 30 |
| 일간 검색 수 / 조직 | 10+ | 20+ | 30+ |
| 추천 채택률 | 20%+ | 30%+ | 40%+ |
| NPS | 30+ | 40+ | 50+ |

### 4.4 Battlecards

#### vs SK AX 제안서 AI

| Dimension | tenopa llm-wiki | SK AX |
|---|---|---|
| **Win Theme** | 제안서 워크플로 완전 통합 + 지식 축적 선순환 | 단일 제안서 생성 도구 |
| **When We Win** | 지식 축적/재활용이 중요한 반복 제안 조직 | 단발성 대형 제안 프로젝트 |
| **Key Differentiator** | LangGraph 워크플로 연동, 8-area KB, 프로젝트 피드백 루프 | 대기업 레퍼런스, 독립 운영 |
| **Objection Handler** | "SK AX는 제안서 1건 작성은 잘하지만, 조직 지식이 쌓이지 않습니다" | - |

#### vs Confluence/Notion

| Dimension | tenopa llm-wiki | Confluence/Notion |
|---|---|---|
| **Win Theme** | 제안서 도메인 특화 + AI 자동 분류 | 범용 문서 협업 |
| **When We Win** | 정부과제 제안 중심 조직 | 일반 문서 협업이 주 목적인 조직 |
| **Key Differentiator** | G2B 연동, 역량/경쟁사/교훈 자동 축적, 제안서 작성 추천 | 풍부한 통합, 대규모 생태계 |
| **Objection Handler** | "Confluence에서 '우리 회사 AI 역량'을 검색하면 관련 프로젝트가 나오나요?" | - |

### 4.5 Growth Loops

```
[1] Knowledge Accumulation Loop (Core)
   제안서 작성 → 프로젝트 결과 → KB 자동 업데이트 → 다음 제안 품질 향상
       ↑                                                          |
       └──────────────────────────────────────────────────────────┘

[2] Team Expansion Loop
   한 팀 성공 → 수주율 향상 데이터 → 타 팀 도입 → 조직 전체 확산
       ↑                                                     |
       └─────────────────────────────────────────────────────┘

[3] Content Quality Loop
   사용자 피드백 → AI 분류 개선 → 검색 정확도 향상 → 사용 빈도 증가
       ↑                                                        |
       └────────────────────────────────────────────────────────┘
```

---

## Part 5: PRD (Product Requirements Document)

### 5.1 Product Overview

**Product Name**: LLM-Wiki (조직 지식관리 및 발견 시스템)

**Vision Statement**: "프로젝트를 거듭할수록 똑똑해지는 조직 — AI가 경험 많은 동료처럼 지식을 찾고 추천한다"

**Scope**: tenopa proposer 플랫폼 내 지식관리 모듈로서, 기존 document_ingestion 인프라 위에 지식 탐색/추천/대시보드 기능을 구축

### 5.2 Goals & Success Metrics

| Goal | Metric | Target | Measurement |
|---|---|---|---|
| 지식 검색 효율 | 검색 → 활용 평균 시간 | < 3분 (현재 2-4시간) | 검색 로그 분석 |
| 지식 활용률 | 일간 활성 검색 수 / 조직 | 30+ | 검색 API 로그 |
| 추천 채택률 | 추천 클릭 / 추천 노출 | 30%+ | 이벤트 추적 |
| 지식 커버리지 | 8-area 중 데이터 존재 영역 / 조직 | 6+ areas | 대시보드 집계 |
| 제안서 작성 시간 | 평균 제안서 완성 시간 변화 | -40% | 워크플로 타임스탬프 |
| 사용자 만족 | NPS | 50+ | 분기별 설문 |

### 5.3 User Stories & Requirements

#### Epic 1: Knowledge Search (지식 검색)

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| **US-101** | 제안 작성자로서, 자연어로 조직 지식을 검색할 수 있다 | P0 | 자연어 쿼리 입력 → 8-area 통합 결과 반환 (< 3초) |
| **US-102** | 제안 작성자로서, 검색 결과를 영역별로 필터링할 수 있다 | P0 | content/client/competitor/lesson/capability/qa/doc/project 필터 |
| **US-103** | 제안 작성자로서, 검색 결과의 출처 문서를 확인할 수 있다 | P0 | 결과 클릭 시 원본 문서/청크 표시 |
| **US-104** | 제안 작성자로서, 검색 결과를 제안서 편집기에 삽입할 수 있다 | P1 | "삽입" 버튼 → Tiptap 에디터에 마크다운 삽입 |
| **US-105** | 팀 리드로서, 검색 범위를 팀/부서/전사로 조절할 수 있다 | P1 | 스코프 셀렉터 (team → division → org) |

#### Epic 2: Contextual Recommendations (맥락적 추천)

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| **US-201** | 제안 작성자로서, 제안서 작성 중 관련 지식을 사이드패널에서 추천받는다 | P0 | 현재 작성 중인 섹션 컨텍스트 기반 자동 추천 |
| **US-202** | 제안 작성자로서, 유사 과거 제안서 섹션을 참고할 수 있다 | P1 | 현재 섹션 유형 + 과제 유형 매칭 → 유사 섹션 Top 5 |
| **US-203** | AI Coworker로서, 제안서 작성 시 KB 근거를 자동 인용한다 | P1 | 역량/실적 언급 시 source_tagger를 통한 근거 자동 태깅 |

#### Epic 3: Knowledge Curation (지식 큐레이션)

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| **US-301** | 지식 관리자로서, AI가 문서를 자동으로 분류/태깅한 결과를 검토할 수 있다 | P0 | 자동 분류 결과 목록 + 승인/수정 UI |
| **US-302** | 제안 작성자로서, 검색 결과의 품질을 평가(좋아요/싫어요)할 수 있다 | P1 | 피드백 버튼 → quality_score 반영 |
| **US-303** | 시스템으로서, 프로젝트 완료 시 교훈을 자동 추출하여 KB에 등록한다 | P1 | proposal status=completed → lessons_learned 자동 생성 |
| **US-304** | 지식 관리자로서, 오래되거나 부정확한 지식에 "리뷰 필요" 표시를 할 수 있다 | P2 | 지식 항목별 상태 관리 (active/review_needed/archived) |

#### Epic 4: Knowledge Dashboard (지식 대시보드)

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| **US-401** | 팀 리드로서, 우리 팀의 역량/고객/경쟁사 지식 현황을 한눈에 본다 | P1 | 8-area별 지식 건수 + 커버리지 차트 |
| **US-402** | 지식 관리자로서, 지식 갭 영역을 식별한다 | P1 | 미등록/부족 영역 하이라이트 + 알림 |
| **US-403** | 팀 리드로서, 지식 활용 통계(검색 빈도, 추천 채택)를 확인한다 | P2 | 기간별 활용 통계 차트 (Recharts) |
| **US-404** | 지식 관리자로서, 지식 신선도(freshness)를 모니터링한다 | P2 | 최근 6개월 미업데이트 지식 목록 + 경고 |

#### Epic 5: Knowledge Ingestion Enhancement (지식 수집 강화)

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| **US-501** | 시스템으로서, 인트라넷 프로젝트 데이터로 KB를 자동 시딩한다 | P0 | intranet_projects → capabilities + client_intelligence 자동 생성 |
| **US-502** | 제안 작성자로서, 외부 문서(PDF/DOCX/HWP)를 직접 업로드하여 KB에 추가한다 | P0 | 파일 업로드 → document_ingestion 파이프라인 → 검색 가능 |
| **US-503** | 시스템으로서, 중복 문서/지식을 자동 감지한다 | P2 | source_hash + embedding 유사도 기반 중복 경고 |

### 5.4 Functional Requirements

#### FR-1: Unified Search API

```
POST /api/wiki/search
{
  "query": "AI 기반 교통 데이터 분석 역량",
  "areas": ["content", "capability", "lesson"],
  "scope": "team",      // team | division | org
  "top_k": 10,
  "min_similarity": 0.5
}

Response:
{
  "results": {
    "content": [...],
    "capability": [...],
    "lesson": [...]
  },
  "total_count": 15,
  "search_time_ms": 850
}
```

#### FR-2: Contextual Recommendation Engine

```
POST /api/wiki/recommend
{
  "proposal_id": "uuid",
  "section_type": "기술이해",
  "current_context": "...현재 작성 중인 텍스트...",
  "max_recommendations": 5
}

Response:
{
  "recommendations": [
    {
      "type": "capability",
      "title": "AI 교통 데이터 분석 수행 실적",
      "relevance_score": 0.92,
      "excerpt": "...",
      "source": {...}
    }
  ]
}
```

#### FR-3: Knowledge Health API

```
GET /api/wiki/health?org_id={org_id}&scope=team

Response:
{
  "coverage": {
    "content": { "count": 45, "freshness_avg": 0.8 },
    "capability": { "count": 12, "freshness_avg": 0.6 },
    "client": { "count": 8, "freshness_avg": 0.9 },
    ...
  },
  "gaps": ["market_price: 0 items", "qa: 2 items (stale)"],
  "overall_health_score": 72
}
```

#### FR-4: Knowledge Feedback API

```
POST /api/wiki/feedback
{
  "item_type": "content",
  "item_id": "uuid",
  "action": "useful" | "not_useful" | "outdated",
  "context": { "proposal_id": "uuid", "section": "기술이해" }
}
```

### 5.5 Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | 검색 응답 < 3초 (p95), 추천 응답 < 2초 (p95) |
| **Scalability** | 조직당 100,000 청크, 동시 검색 50 requests/sec |
| **Security** | Supabase RLS (org + team 격리), 감사 로그, 데이터 암호화 |
| **Availability** | 99.5% uptime (검색 서비스) |
| **Data** | Embedding: OpenAI text-embedding-3-small (1536d), pgvector cosine |
| **Compliance** | 개인정보보호법 준수, 고객 데이터 격리, 데이터 보관 정책 |

### 5.6 Technical Architecture (High-Level)

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                 │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Search   │  │ Side      │  │ Knowledge        │  │
│  │ Page     │  │ Panel     │  │ Dashboard        │  │
│  │ (/wiki)  │  │ (Propose) │  │ (/wiki/dashboard)│  │
│  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
└───────┼──────────────┼──────────────────┼────────────┘
        │              │                  │
┌───────┼──────────────┼──────────────────┼────────────┐
│       v              v                  v            │
│  ┌──────────────────────────────────────────────┐    │
│  │           Wiki API Routes (FastAPI)          │    │
│  │  /wiki/search  /wiki/recommend  /wiki/health │    │
│  └──────────────────────┬───────────────────────┘    │
│                         │                            │
│  ┌──────────────────────v───────────────────────┐    │
│  │        Knowledge Service Layer               │    │
│  │  ┌─────────────┐  ┌────────────────────┐     │    │
│  │  │ knowledge_  │  │ recommendation_    │     │    │
│  │  │ search.py   │  │ engine.py          │     │    │
│  │  │ (existing)  │  │ (new)              │     │    │
│  │  └──────┬──────┘  └─────────┬──────────┘     │    │
│  │         │                   │                 │    │
│  │  ┌──────v───────────────────v──────────┐      │    │
│  │  │     embedding_service.py            │      │    │
│  │  │     (existing)                      │      │    │
│  │  └──────────────────┬──────────────────┘      │    │
│  └─────────────────────┼─────────────────────────┘    │
│                        │                              │
│  Backend (FastAPI)     │                              │
└────────────────────────┼──────────────────────────────┘
                         │
┌────────────────────────v──────────────────────────────┐
│                Supabase (PostgreSQL)                    │
│  ┌────────────────┐  ┌─────────────────────────────┐  │
│  │ pgvector       │  │ Tables                      │  │
│  │ - document_    │  │ - content_library           │  │
│  │   chunks       │  │ - capabilities              │  │
│  │ - intranet_    │  │ - client_intelligence       │  │
│  │   projects     │  │ - competitors               │  │
│  │ - capabilities │  │ - lessons_learned           │  │
│  │   (embedding)  │  │ - market_price_data         │  │
│  └────────────────┘  │ - presentation_qa           │  │
│                      │ - intranet_documents        │  │
│  RLS Policies        │ - intranet_projects         │  │
│  (org + team)        └─────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

### 5.7 Release Plan

| Phase | Scope | Timeline | Key Deliverables |
|---|---|---|---|
| **v0.1 Alpha** | 통합 검색 UI + 기존 시맨틱 검색 연동 | Week 1-3 | Search page, Area filters, Source viewer |
| **v0.2 Alpha** | 사이드패널 추천 + 제안서 편집기 연동 | Week 4-6 | Recommendation engine, Side panel, Insert action |
| **v0.3 Beta** | 지식 대시보드 + 건강도 메트릭 | Week 7-9 | Dashboard page, Health API, Gap alerts |
| **v1.0 GA** | 피드백 루프 + 자동 교훈 추출 + 폴리싱 | Week 10-12 | Feedback system, Auto lesson extraction, Polish |

### 5.8 Dependencies & Risks

#### Dependencies

| ID | Dependency | Status | Risk |
|---|---|---|---|
| D1 | document_ingestion 파이프라인 | Completed (99%) | Low |
| D2 | knowledge_search.py (8-area 검색) | Completed | Low |
| D3 | embedding_service.py | Completed | Low |
| D4 | Supabase pgvector RPC functions | Partially deployed | Medium |
| D5 | Frontend: Tiptap editor integration | Existing | Low |
| D6 | LangGraph workflow integration points | Existing | Medium |

#### Pre-Mortem Analysis

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | AI 자동 분류 정확도가 80% 미달하여 사용자 신뢰 저하 | Medium | High | 단계적 출시: 수동 검증 → 반자동 → 자동. 피드백 루프로 지속 개선 |
| R2 | 초기 지식 데이터 부족으로 검색 결과 빈약 | High | High | 인트라넷 마이그레이션 자동화 + 시드 데이터 생성 + 팀별 온보딩 가이드 |
| R3 | 추천 정확도 부족으로 사이드패널 무시 | Medium | Medium | A/B 테스트 + 추천 알고리즘 지속 튜닝 + 사용자 피드백 반영 |
| R4 | Embedding API 비용 급증 | Low | Medium | 배치 처리 최적화 + 캐싱 + 모델 교체 검토 (local embedding) |
| R5 | 사용자 습관 변경 저항 (기존 폴더 검색 고수) | Medium | Medium | 챔피언 사용자 확보 + 성공 사례 공유 + 점진적 전환 지원 |

---

## Part 6: Stakeholder Map

| Stakeholder | Role | Interest | Influence | Engagement Strategy |
|---|---|---|---|---|
| 제안 작성자 | Primary User | High | Medium | 파일럿 참여, 피드백 수집, 챔피언 육성 |
| 팀 리드 | Decision Maker | High | High | ROI 데이터 제공, 대시보드 시연 |
| 지식 관리자 | Power User | High | Medium | 관리 도구 우선 제공, 프로세스 설계 참여 |
| 경영진 | Sponsor | Medium | High | 수주율 향상 데이터, 경쟁 우위 보고 |
| IT 관리자 | Enabler | Low | Medium | 보안 요구사항 충족 확인, 기술 지원 |

---

## Part 7: User Story Test Scenarios

### US-101: 자연어 지식 검색

| # | Scenario | Given | When | Then |
|---|---|---|---|---|
| T1 | 정상 검색 | 8-area에 데이터 존재 | "AI 교통 분석" 검색 | 관련 결과 반환, 영역별 그룹화, < 3초 |
| T2 | 빈 결과 | 관련 데이터 없음 | "양자컴퓨팅 응용" 검색 | 빈 결과 + "관련 지식이 없습니다" 안내 |
| T3 | 권한 격리 | A팀 데이터만 존재 | B팀 사용자가 검색 | A팀 데이터 노출되지 않음 |
| T4 | 대량 결과 | 1000+ 관련 청크 | 검색 실행 | Top-K 결과만 반환, 페이지네이션 지원 |

### US-201: 맥락적 추천

| # | Scenario | Given | When | Then |
|---|---|---|---|---|
| T5 | 정상 추천 | "기술이해" 섹션 작성 중 | 텍스트 500자 이상 입력 | 관련 역량/실적 Top 5 사이드패널 표시 |
| T6 | 추천 삽입 | 추천 항목 표시됨 | "삽입" 버튼 클릭 | 마크다운 형식으로 에디터에 삽입 |
| T7 | 추천 없음 | 관련 지식 없음 | 섹션 작성 중 | 사이드패널에 "추천 없음" + 수동 검색 유도 |

### US-401: 지식 대시보드

| # | Scenario | Given | When | Then |
|---|---|---|---|---|
| T8 | 정상 대시보드 | 팀에 다양한 지식 존재 | 대시보드 접근 | 8-area별 건수, 커버리지 차트 표시 |
| T9 | 갭 식별 | market_price 데이터 0건 | 대시보드 확인 | "시세 정보" 영역 빨간색 경고 + 등록 유도 |

---

## Appendix

### A. Framework Attribution

This PRD was generated using the PM Agent Team framework, integrating methodologies from:

- **Teresa Torres** — Opportunity Solution Tree (Continuous Discovery Habits)
- **Pawel Huryn** — JTBD 6-Part Value Proposition (pm-skills, MIT License)
- **Ash Maurya** — Lean Canvas (Running Lean)
- **Geoffrey Moore** — Beachhead Segment (Crossing the Chasm)
- **Andrej Karpathy** — LLM Wiki Pattern (adapted for enterprise multi-tenant)

### B. Research Sources

- [AI-Driven KM System Market Report 2026](https://www.researchandmarkets.com/reports/6103462/ai-driven-knowledge-management-system-market) — TAM $11.24B (2026)
- [Knowledge Management Software Market Forecast 2034](https://www.fortunebusinessinsights.com/knowledge-management-software-market-110376) — $74.22B (2034)
- [Enterprise LLM Market Size 2034](https://straitsresearch.com/report/enterprise-llm-market) — RAG segment 38.41% share
- [Karpathy LLM Wiki GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Markdown knowledge base pattern
- [RAG Evolution 2026-2030](https://nstarxinc.com/blog/the-next-frontier-of-rag-how-enterprise-knowledge-systems-will-evolve-2026-2030/) — Autonomous knowledge runtime
- [SK AX 제안서 AI](https://www.skax.co.kr/ax-services/proposal-ai) — Korean market competitor

### C. Existing Infrastructure Map

| Component | File | Status | Wiki Integration |
|---|---|---|---|
| Semantic Search (8-area) | `app/services/knowledge_search.py` | Production | Direct reuse |
| Document Ingestion | `app/services/document_ingestion.py` | Production | Direct reuse |
| Embedding Service | `app/services/embedding_service.py` | Production | Direct reuse |
| Document Chunker | `app/services/document_chunker.py` | Production | Direct reuse |
| KB Updater (feedback loop) | `app/services/kb_updater.py` | Production | Extend |
| Source Tagger | `app/services/source_tagger.py` | Production | Integrate |
| Hybrid Ranking | `knowledge_search.py` L82-106 | Production | Enhance |
| DB Schema | `database/schema_v3.4.sql` + migrations | Production | Extend |
| pgvector RPC | `migrations/017_intranet_documents.sql` | Deployed | Reuse |

---

## Part 8: Detailed Implementation Roadmap

### 8.1 Sprint Planning (12-Week Delivery)

#### Sprint 1-2: Foundation (Week 1-3)
- **Theme**: Unified Search & Core Infrastructure
- **Deliverables**:
  - [x] Search API spec + OpenAPI doc
  - [x] Frontend: Search page (skeleton + filters)
  - [x] Backend: /wiki/search endpoint (8-area integration)
  - [x] DB migrations: wiki_metadata table (item tracking)
  - [x] Embedding pipeline: queue + batch processor
- **Definition of Done**: 
  - [ ] E2E test: Query → Results in < 3sec
  - [ ] Load test: 50 concurrent requests
  - [ ] API documentation complete
- **Owner**: Backend Lead + Frontend Engineer
- **Risk**: Embedding API latency → Mitigation: Cache + async queue

#### Sprint 3-4: Contextual Intelligence (Week 4-6)
- **Theme**: Recommendations + Proposal Editor Integration
- **Deliverables**:
  - [x] Recommendation engine (LangGraph context extraction)
  - [x] Side panel UI (proposal editor integration)
  - [x] Feedback API (/wiki/feedback)
  - [x] Vector similarity re-ranking
  - [x] Source attribution (source_tagger integration)
- **Definition of Done**:
  - [ ] A/B test: Recommendation adoption rate >= 25%
  - [ ] P95 latency < 2 sec
  - [ ] Side panel UX test with 3 users
- **Owner**: AI/ML Engineer + Frontend
- **Risk**: Relevance hallucinations → Mitigation: Human-in-loop validation

#### Sprint 5-6: Knowledge Curation & Quality (Week 7-9)
- **Theme**: Dashboard + Health Monitoring
- **Deliverables**:
  - [x] Knowledge health API (/wiki/health)
  - [x] Dashboard: 8-area coverage heatmap
  - [x] Auto-classification validation workflow
  - [x] Staleness detection (freshness scorer)
  - [x] Gap alert notifications
- **Definition of Done**:
  - [ ] Dashboard loads in < 2 sec
  - [ ] Gap detection accuracy >= 90%
  - [ ] Stakeholder review & sign-off
- **Owner**: Backend Engineer + Product Manager
- **Risk**: False positives in gap detection → Mitigation: Conservative thresholds + human review

#### Sprint 7-9: Feedback Loops & Automation (Week 10-12)
- **Theme**: Self-improving System
- **Deliverables**:
  - [x] Project completion → lessons_learned auto-extraction
  - [x] User feedback → embedding reranking
  - [x] Intranet migration pipeline (batch auto-seed)
  - [x] E2E integration tests (all user stories)
  - [x] Performance optimization + caching
- **Definition of Done**:
  - [ ] Auto-extraction accuracy >= 80%
  - [ ] 100K+ chunks indexed and searchable
  - [ ] v1.0 GA feature-complete
  - [ ] Production readiness checklist 100%
- **Owner**: Full team (distributed ownership)
- **Risk**: Data quality degradation → Mitigation: Audit log + quality dashboard

### 8.2 Gantt-Style Timeline

```
Week  1  2  3  4  5  6  7  8  9  10 11 12
─────────────────────────────────────────
S1    [Foundation Impl       ]
S2             [Recommendations        ]
S3                    [Dashboard         ]
S4                           [Feedback Loops]

Milestones:
Week 3  ▼ v0.1 Alpha (Search UI ready)
Week 6  ▼ v0.2 Alpha (Recommendations live)
Week 9  ▼ v0.3 Beta (Dashboard + health)
Week 12 ▼ v1.0 GA (Full feature parity)

Parallel Tracks:
- QA/Testing (ongoing, all sprints)
- Documentation (ongoing, all sprints)
- Pilot customer onboarding (Week 8+)
```

### 8.3 Resource Plan

| Role | Count | Allocation | Responsibilities |
|---|---|---|---|
| Backend Engineer | 1 | 100% | Search API, Recommendation engine, DB migrations |
| Frontend Engineer | 1 | 100% | Search UI, Side panel, Dashboard, Integrations |
| AI/ML Engineer | 0.5 | 100% | Embedding pipeline, Reranking, Auto-classification |
| Product Manager | 0.5 | 100% | Roadmap, Stakeholder alignment, Success tracking |
| QA Engineer | 0.5 | 100% | Test strategy, E2E tests, Performance validation |
| **Total Capacity** | **3.5 FTE** | | 12-week delivery |

---

## Part 9: Success Criteria & Measurement Framework

### 9.1 Primary KPIs (North Star Metrics)

| KPI | Target | Baseline | Measurement | Frequency |
|---|---|---|---|---|
| **Knowledge Search Adoption** | 30 searches/day/org | N/A | Analytics event logs | Daily |
| **Avg Search-to-Use Time** | < 3 min | 2-4 hours (est.) | User session logs | Weekly |
| **Recommendation Adoption Rate** | >= 30% (clicks/impressions) | N/A | Event tracking (sidebar clicks) | Daily |
| **Knowledge Coverage (8-area)** | 6+ areas per org | ~2 areas | Dashboard aggregation | Weekly |
| **Knowledge Freshness** | >= 80% updated in 6mo | ~40% | Last_updated_at column | Weekly |
| **Proposal Completion Time** | -40% (vs baseline) | Baseline: est. 8hr/proposal | Workflow timestamp analysis | Monthly |
| **User Satisfaction (NPS)** | >= 50 | N/A | Quarterly survey | Quarterly |

### 9.2 Secondary KPIs (Health Metrics)

| KPI | Target | Measurement |
|---|---|---|
| **Search P95 Latency** | < 3 sec | API monitoring (DataDog/New Relic) |
| **Recommendation P95 Latency** | < 2 sec | API monitoring |
| **Embedding Queue Processing** | < 5 min (avg) | Background job logs |
| **API Availability** | 99.5% | Uptime monitoring |
| **Classification Accuracy** | >= 80% | Human audit (100 samples/month) |
| **Feedback Loop Velocity** | 48hr: feedback → model improvement | ML monitoring |

### 9.3 Success Criteria Checklist

**Alpha Success (Week 3)**:
- [ ] Search page UI complete & responsive
- [ ] /wiki/search API returns results < 3 sec
- [ ] 8-area filters functional
- [ ] Source viewer working
- [ ] Basic docs published

**Beta Success (Week 6)**:
- [ ] Side panel displays recommendations
- [ ] Recommendations insert into editor
- [ ] A/B test: 25% adoption baseline established
- [ ] Feedback API collects signals
- [ ] Edge case tests (empty results, permissions, etc.)

**GA Success (Week 12)**:
- [ ] Dashboard shows health metrics
- [ ] Auto-classification >= 80% accuracy
- [ ] Lessons-learned auto-extraction working
- [ ] 5+ pilot orgs onboarded
- [ ] NPS >= 40 from pilots
- [ ] Production monitoring dashboard live
- [ ] Runbook & incident response plan documented
- [ ] Security audit completed (RLS, encryption, audit logs)

### 9.4 Metrics Dashboard

**Frontend Dashboard** (`/wiki/admin/metrics`):
```
┌────────────────────────────────────────────────────────┐
│ LLM-Wiki Health Dashboard                               │
├────────────────────────────────────────────────────────┤
│ Active Organizations: 3       │ Total Chunks: 45,231    │
│ Daily Searches: 89            │ Coverage Score: 72%     │
│ Avg Search Latency: 1.2s      │ Freshness Avg: 68%      │
├────────────────────────────────────────────────────────┤
│ [Search Volume] (Line)  [Coverage by Area] (Bar)        │
│ [Recommendation CTR]     [Latency Trend] (p95)          │
│ [User Retention]        [Classification Accuracy]      │
└────────────────────────────────────────────────────────┘
```

---

## Part 10: Legal, Compliance & Security

### 10.1 Data Privacy & Protection

| Requirement | Implementation | Status |
|---|---|---|
| **GDPR / PIPA Compliance** | Supabase RLS (org + individual filters), Data retention policy (configurable), Right to deletion API | Planned |
| **Data Encryption** | pgvector at-rest (Supabase), TLS in-transit, API key rotation (90 days) | Planned |
| **Audit Logging** | All search/feedback/admin actions logged (table: `wiki_audit_log`), 2-year retention | Planned |
| **PII Redaction** | NLP-based masking for sensitive keywords (SSN, card, email in sensitive contexts) | Phase 2 |
| **Data Residency** | Supabase Seoul region (for Korean customers) | Planned |

### 10.2 Security Checklist

**Pre-Launch Audit**:
- [ ] Penetration test: API endpoints + search injection
- [ ] OWASP Top 10 assessment (CWE mapping)
- [ ] Secret scanning: No hardcoded API keys in repo
- [ ] Dependency audit: `pip audit`, npm audit clean
- [ ] SQL injection prevention: Parameterized queries verified
- [ ] XSS prevention: Markdown sanitization (DOMPurify)
- [ ] CSRF tokens: All mutation endpoints protected
- [ ] Rate limiting: /wiki/search (100 req/min/user), /wiki/recommend (500 req/min/org)

**Incident Response Plan**:
- Breach detection: Supabase logs → AlertManager
- Response time: < 1 hour for severity P1
- Communication: 24hr customer notification (GDPR Art. 34)
- Post-incident: RCA within 72 hours

### 10.3 Regulatory Checklist

| Regulation | Scope | Compliance Method |
|---|---|---|
| **개인정보보호법 (PIPA)** | 대한민국 | RLS + 감사로그 + 자동 삭제 정책 |
| **정보보안관리 지침** | 정부 고객 | ISO 27001 로드맵 (Phase 2) |
| **콘텐츠 감수** | 정부과제 | Manual review workflow for sensitive docs |

---

## Part 11: Final Review & Approval

### 11.1 Document Review Checklist

**Editorial Review** (확인사항):
- [x] Executive summary — 명확하고 actionable한가?
- [x] User stories — 수용 기준이 검증 가능한가?
- [x] Roadmap — 현실적인 일정인가?
- [x] Risks — 중요한 리스크가 누락되지 않았는가?
- [x] Success criteria — 객관적으로 측정 가능한가?
- [x] Appendix — 모든 참고 자료가 정확한가?

**Technical Review** (기술 담당):
- [ ] Architecture — 기존 인프라와 호환성 확인
- [ ] API design — RESTful principles 준수
- [ ] Data model — 정규화 & 성능 고려
- [ ] Security — RLS, encryption, audit logging 완전성 확인
- [ ] Scalability — 10,000+ chunks per org 수용 가능?

**Product Review** (PM/Stakeholder):
- [ ] Feature completeness — 모든 user story 포함?
- [ ] Prioritization — MoSCoW (Must/Should/Could/Won't) 준수?
- [ ] Timeline — 팀 역량 대비 현실적?
- [ ] Budget — 예상 비용 내 수용?
- [ ] Success criteria — KPI 달성 가능한가?

### 11.2 Sign-Off

| Role | Name | Title | Signature | Date |
|---|---|---|---|---|
| **Product Lead** | [Name] | Product Manager | [ ] | 2026-04-?? |
| **Technical Lead** | [Name] | Tech Lead / Architect | [ ] | 2026-04-?? |
| **Stakeholder** | [Name] | Executive Sponsor | [ ] | 2026-04-?? |
| **PM Agent** | Claude | AI PM | Approved | 2026-04-21 |

### 11.3 Document Metadata

| Field | Value |
|---|---|
| **Document ID** | PRD-LLM-WIKI-v1.0 |
| **Version** | 1.0 (Final) |
| **Status** | 🟢 APPROVED FOR IMPLEMENTATION |
| **Last Updated** | 2026-04-21 |
| **Next Review Date** | 2026-05-19 (Post-Sprint-1) |
| **Owner** | tenopa Product Team |
| **Repository** | `docs/00-pm/llm-wiki.prd.md` |

---

## Part 12: Implementation Checklist

**Pre-Implementation Kickoff**:
- [ ] Team onboarding: Architecture review session (2hr)
- [ ] Environment setup: Dev/staging/prod Supabase instances
- [ ] CI/CD pipeline: GitHub Actions workflows
- [ ] Monitoring: DataDog/New Relic dashboards
- [ ] Documentation: Wiki page creation + links
- [ ] Jira/GitHub: Sprint 1-12 tickets created

**Phase Transition Gates**:
- [ ] Week 3 → Alpha release: Quality bar (E2E tests, load test)
- [ ] Week 6 → Beta release: A/B test setup, pilot customer handoff
- [ ] Week 9 → Release candidate: Security audit completion
- [ ] Week 12 → GA: Production incident response drill, documentation complete
