# Go/No-Go 스크리닝 고도화 Design Document

> **Summary**: 3축 정량 분석(유사실적·자격·경쟁) + AI 전략가산 = 100점 합산, 70점 게이트
>
> **Plan**: `docs/01-plan/features/go-no-go-enhancement.plan.md`
> **Date**: 2026-03-26
> **Status**: Draft

---

## 1. State 모델 변경

### 1.1 GoNoGoResult 확장 (`app/graph/state.py`)

```python
class GoNoGoResult(BaseModel):
    """STEP 1-②: Go/No-Go 의사결정 결과. v4.0: 4축 정량 스코어링."""

    # ── 기존 필드 (하위 호환 유지) ──
    rfp_analysis_ref: str = ""
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int                           # 4축 합산 (0~100)
    score_breakdown: dict                            # v4.0: 4축 구조
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    fatal_flaw: Optional[str] = None
    strategic_focus: Optional[str] = None
    decision: str = "pending"

    # ── v4.0 신규 필드 ──
    score_tag: Literal["priority", "standard", "below_threshold", "disqualified", ""] = ""
    performance_detail: dict = {}                    # §2.1 반환값
    qualification_detail: dict = {}                  # §2.2 반환값
    competition_detail: dict = {}                    # §2.3 반환값
```

**하위 호환 규칙**:
- `score_breakdown`의 키는 4축(`similar_performance`, `qualification`, `competition`, `strategic`)으로 변경하되, 기존 5항목 키(`기술역량`, `수행실적` 등)도 `score_breakdown["legacy"]` 안에 보존
- 신규 필드는 모두 default 값이 있어 기존 데이터 역직렬화에 영향 없음

---

## 2. 정량 스코어링 함수 3개 (`app/graph/context_helpers.py`)

### 2.1 `score_similar_performance` (30점 만점)

```python
async def score_similar_performance(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """RFP 유사실적 요건 ↔ 자사 수주 이력 정량 매칭.

    Returns:
        {
            "score": int,                      # 0~30
            "required_items": [                 # RFP에서 파싱한 요건 목록
                {
                    "raw_text": str,            # 원문: "최근 5년 내 10억 이상 SI 2건"
                    "period_years": int,        # 5
                    "min_amount": int,           # 1_000_000_000
                    "min_count": int,            # 2
                    "domain_keywords": list[str],# ["SI"]
                    "matched_count": int,        # DB 매칭 건수
                    "matched_projects": list[dict],  # [{title, amount, year, client}]
                    "is_met": bool,
                },
            ],
            "coverage_rate": float,            # 충족률 (0.0~1.0)
            "same_client_wins": int,           # 동일 발주기관 수주 건수
            "same_domain_win_rate": float|None, # 동일 사업유형 승률
            "is_fatal": bool,                  # 필수 요건 0건 충족
            "fatal_reason": str|None,
        }
    """
```

**구현 로직**:

```
Step 1 — RFP 유사실적 요건 구조화
  입력: rfp_dict["similar_project_requirements"]: list[str]
  처리: AI 파싱 (claude_generate)
    프롬프트: "다음 유사실적 요건을 JSON 배열로 구조화하세요..."
    출력: [{period_years, min_amount, min_count, domain_keywords}]
  Fallback: 빈 리스트 → 요건 없음으로 간주 (score = 20, is_fatal = False)

Step 2 — DB 정량 매칭 (각 요건별)
  쿼리 대상: proposal_results JOIN proposals
  조건:
    - proposals.org_id = org_id
    - proposal_results.result = 'won'
    - proposals.created_at >= now() - interval '{period_years} years'
    - proposals.bid_amount >= min_amount
    - proposals.title ILIKE any of domain_keywords (OR 조건)
  SELECT: proposals.title, proposals.bid_amount, proposals.created_at, proposals.client_name

Step 3 — 동일 발주기관 보너스
  쿼리: proposal_results JOIN proposals
    WHERE proposals.client_name ILIKE '%{rfp_dict["client"]}%'
    AND proposal_results.result = 'won'
  결과: same_client_wins (건수)

Step 4 — 동일 사업유형 승률 (artifacts.content에서 domain 추출은 비용 큼 → lessons_learned.industry 활용)
  쿼리: lessons_learned
    WHERE org_id AND industry ILIKE '%{rfp_dict["domain"]}%'
  집계: won / (won + lost)

Step 5 — 점수 산정
  base_score:
    - required_items가 없으면: 20점 (요건 자체가 없는 공고)
    - coverage_rate >= 1.0: 25점
    - coverage_rate > 0: round(coverage_rate * 25)
    - coverage_rate == 0 AND min_count > 0: 0점 + is_fatal = True
  bonus:
    - same_client_wins >= 1: +3점
    - same_domain_win_rate >= 0.6: +2점
  score = min(base_score + bonus, 30)
```

**DB 쿼리 (Step 2)**:

```sql
SELECT p.title, p.bid_amount, p.created_at, p.client_name
FROM proposal_results pr
JOIN proposals p ON pr.proposal_id = p.id
WHERE p.org_id = :org_id
  AND pr.result = 'won'
  AND p.created_at >= NOW() - INTERVAL ':period_years years'
  AND p.bid_amount >= :min_amount
  AND (p.title ILIKE '%:kw1%' OR p.title ILIKE '%:kw2%')
ORDER BY p.created_at DESC
LIMIT 20
```

---

### 2.2 `score_qualification` (30점 만점)

```python
async def score_qualification(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """RFP 자격 요건 ↔ 자사 보유 자격(capabilities) 자동 대조.

    Returns:
        {
            "score": int,                        # 0~30
            "mandatory": [                       # 필수 자격 (참가자격)
                {
                    "requirement": str,          # RFP 원문
                    "status": "met"|"unmet"|"partial",
                    "matched_capability": str|None,  # 매칭된 capabilities.title
                    "note": str,                 # 설명
                },
            ],
            "preferred": [                       # 가점 항목
                {
                    "requirement": str,
                    "status": "met"|"unmet",
                    "bonus_points": int,         # 가점 배점 (RFP 기재 시)
                },
            ],
            "is_fatal": bool,                    # 필수 1건이라도 unmet
            "fatal_reason": str|None,
            "summary": str,                      # "필수 3/3 충족, 가점 2/4 보유"
        }
    """
```

**구현 로직**:

```
Step 1 — RFP 자격 요건 분류 (AI 파싱)
  입력: rfp_dict["qualification_requirements"]: list[str]
  프롬프트:
    "다음 자격 요건을 mandatory(필수)와 preferred(가점)로 분류하세요.
     mandatory: '필수', '참가자격', '등록', '면허', '보유업체' 등 포함
     preferred: '가점', '우대', '우선' 등 포함
     출력: {mandatory: [{requirement, keywords}], preferred: [{requirement, keywords, bonus_points}]}"
  Fallback: 전체를 mandatory로 간주

Step 2 — 자사 보유 자격 조회
  쿼리: capabilities WHERE org_id AND type IN ('certification', 'license', 'registration')
  SELECT: title, type, detail, keywords

Step 3 — 매칭 (키워드 기반)
  각 requirement의 keywords ↔ capabilities의 title/keywords 매칭
  매칭 알고리즘:
    1차: title에 keyword 포함 (ILIKE)
    2차: keywords[] && requirement_keywords (배열 교집합)
    3차: unmet (미보유)

Step 4 — 점수 산정
  mandatory 전체 met:
    base = 25점
    preferred met 개수에 따라 +1~5점 (max 30)
  mandatory 1건 unmet:
    is_fatal = True
    score = 0
  mandatory 부분 충족 (일부 partial):
    is_fatal = False (partial은 조건부 참가 가능)
    score = round((met_count / total_mandatory) * 25)
```

**DB 쿼리 (Step 2)**:

```sql
SELECT id, title, type, detail, keywords
FROM capabilities
WHERE org_id = :org_id
  AND type IN ('certification', 'license', 'registration', 'track_record')
ORDER BY type, title
```

**매칭 알고리즘 상세**:

```python
def _match_qualification(req_keywords: list[str], capabilities: list[dict]) -> dict | None:
    """자격 요건 키워드 ↔ capabilities 매칭. 가장 유사한 1건 반환."""
    for cap in capabilities:
        cap_text = f"{cap['title']} {cap.get('detail', '')}".lower()
        cap_kws = [k.lower() for k in (cap.get('keywords') or [])]
        for kw in req_keywords:
            kw_lower = kw.lower()
            if kw_lower in cap_text or kw_lower in cap_kws:
                return cap
    return None
```

---

### 2.3 `score_competition` (20점 만점)

```python
async def score_competition(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """경쟁 강도 분석: 발주기관 낙찰이력 + 자사 대전 기록.

    Returns:
        {
            "score": int,                        # 0~20
            "intensity_level": "low"|"medium"|"high",
            "estimated_competitors": int,        # 예상 참여업체 수
            "avg_competitors_same_client": float|None,  # 동일 기관 평균 참여수
            "top_competitors": [                 # 상위 경쟁사
                {
                    "name": str,
                    "wins_at_client": int,       # 해당 기관에서의 낙찰 횟수
                    "head_to_head": str,         # "3승 1패" (자사 관점)
                },
            ],
            "our_win_rate_at_client": float|None,# 해당 기관에서의 자사 승률
            "our_market_share": float|None,      # 해당 기관 점유율
            "rationale": str,
        }
    """
```

**구현 로직**:

```
Step 1 — 동일 발주기관 과거 경쟁 이력 (client_bid_history)
  쿼리: client_intelligence → client_bid_history
    WHERE client_name ILIKE '%{client}%'
  집계: 총 입찰 건수, 자사 won/lost 건수

Step 2 — 예상 참여업체 수 추정
  방법 A: proposal_results.competitor_count 평균 (동일 기관)
    쿼리: proposal_results JOIN proposals
      WHERE proposals.client_name ILIKE '%{client}%'
    AVG(competitor_count)

  방법 B: 데이터 없으면 기본값 5 (보통)

Step 3 — 경쟁사 대전 기록 (competitor_history)
  쿼리: competitor_history WHERE org_id
  상위 5개 경쟁사 (대전 횟수 기준)
  각 경쟁사별 자사 관점 승/패

Step 4 — 점수 산정
  base_by_intensity:
    estimated_competitors <= 3:  base = 18  (low)
    estimated_competitors 4~7:   base = 12  (medium)
    estimated_competitors >= 8:  base = 8   (high)

  adjustments:
    our_win_rate_at_client >= 0.5: +2 (기관 내 강자)
    our_win_rate_at_client < 0.3:  -2 (기관 내 약자)
    our_market_share >= 0.3: +2 (높은 점유율)

  score = max(0, min(base + adjustments, 20))
```

**DB 쿼리 (Step 1 — 발주기관 입찰 이력)**:

```sql
-- 발주기관 ID 조회
SELECT id FROM client_intelligence
WHERE org_id = :org_id AND client_name ILIKE :client_pattern
LIMIT 1;

-- 해당 기관 입찰 이력
SELECT positioning, result, bid_year
FROM client_bid_history
WHERE client_id = :client_id
ORDER BY bid_year DESC;
```

**DB 쿼리 (Step 2 — 평균 참여수)**:

```sql
SELECT AVG(pr.competitor_count) as avg_competitors
FROM proposal_results pr
JOIN proposals p ON pr.proposal_id = p.id
WHERE p.org_id = :org_id
  AND p.client_name ILIKE :client_pattern
  AND pr.competitor_count IS NOT NULL;
```

**DB 쿼리 (Step 3 — 대전 기록)**:

```sql
SELECT c.company_name,
       COUNT(*) FILTER (WHERE ch.our_result = 'won') as our_wins,
       COUNT(*) FILTER (WHERE ch.our_result = 'lost') as our_losses
FROM competitor_history ch
JOIN competitors c ON ch.competitor_id = c.id
WHERE c.org_id = :org_id
GROUP BY c.company_name
ORDER BY (COUNT(*)) DESC
LIMIT 5;
```

---

## 3. Go/No-Go 노드 개편 (`app/graph/nodes/go_no_go.py`)

### 3.1 전체 흐름

```python
async def go_no_go(state: ProposalState) -> dict:
    """STEP 1-②: Go/No-Go 4축 정량 스코어링.

    v4.0: 3축 정량(유사실적·자격·경쟁) + AI 전략가산 = 100점 합산.
    """

    rfp = state.get("rfp_analysis")
    if not rfp:
        return {error...}

    mode = state.get("mode", "full")
    rfp_dict = rfp_to_dict(rfp)
    org_id = state.get("org_id", "")

    # ── 축 1~3: 정량 스코어링 (DB 기반) ──
    if mode == "full" and org_id:
        perf = await score_similar_performance(rfp_dict, org_id)
        qual = await score_qualification(rfp_dict, org_id)
        comp = await score_competition(rfp_dict, org_id)
    else:
        # Lite 모드: 정량 스코어링 스킵
        perf = {"score": 0, "is_fatal": False, ...}
        qual = {"score": 0, "is_fatal": False, ...}
        comp = {"score": 10, ...}  # 기본 중립

    # ── 축 4: AI 전략 가산 (20점) ──
    strategic = await _ai_strategic_assessment(state, rfp_dict, org_id)
    # strategic = {"score": 15, "tech_fit": 7, "client_relationship": 4,
    #              "price_competitiveness": 4, "positioning": "defensive",
    #              "positioning_rationale": "...", "strategic_focus": "...",
    #              "pros": [...], "risks": [...]}

    # ── 합산 + 게이트 판정 ──
    total = perf["score"] + qual["score"] + comp["score"] + strategic["score"]

    if qual.get("is_fatal") or perf.get("is_fatal"):
        recommendation = "no-go"
        score_tag = "disqualified"
        fatal_flaw = qual.get("fatal_reason") or perf.get("fatal_reason")
    elif total >= 85:
        recommendation = "go"
        score_tag = "priority"
        fatal_flaw = None
    elif total >= 70:
        recommendation = "go"
        score_tag = "standard"
        fatal_flaw = None
    else:
        recommendation = "no-go"
        score_tag = "below_threshold"
        fatal_flaw = f"합산 {total}점 (기준: 70점)"

    gng = GoNoGoResult(
        rfp_analysis_ref=f"rfp_{state.get('project_id', '')}",
        positioning=strategic.get("positioning", "defensive"),
        positioning_rationale=strategic.get("positioning_rationale", ""),
        feasibility_score=total,
        score_breakdown={
            "similar_performance": perf["score"],
            "qualification": qual["score"],
            "competition": comp["score"],
            "strategic": strategic["score"],
        },
        pros=strategic.get("pros", []),
        risks=strategic.get("risks", []),
        recommendation=recommendation,
        fatal_flaw=fatal_flaw,
        strategic_focus=strategic.get("strategic_focus"),
        score_tag=score_tag,
        performance_detail=perf,
        qualification_detail=qual,
        competition_detail=comp,
    )

    return {
        "go_no_go": gng,
        "positioning": gng.positioning,
        "current_step": "go_no_go_complete",
    }
```

### 3.2 AI 전략 가산 함수 (`_ai_strategic_assessment`)

```python
async def _ai_strategic_assessment(
    state: ProposalState,
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """AI 기반 전략 평가 (20점 만점).

    기존 go_no_go 프롬프트를 축소:
    - 기술 적합도 (8점)
    - 발주처 관계 (6점)
    - 가격 경쟁력 (6점)
    + 포지셔닝 추천 + 강점/리스크 + 핵심 승부수
    """
```

**프롬프트 (축소)**:

```
다음 RFP에 대한 전략적 평가를 수행하세요. (20점 만점)

## RFP 요약
{rfp_summary}

## 자사 역량
{capabilities_text}

## 발주기관 인텔리전스
{client_intel_text}

## 가격 분석
{pricing_context}

## 리서치 브리프
{research_text}

## 과거 교훈
{lessons_text}

## 지시사항
1. 기술 적합도 (0~8점): RFP 핫버튼·평가항목 ↔ 자사 역량 부합도
2. 발주처 관계 (0~6점): 기관 인텔리전스 기반 관계 수준 + 접점 이력
3. 가격 경쟁력 (0~6점): 예산 대비 시장 분석 + 낙찰률 추정
4. 포지셔닝: defensive | offensive | adjacent
5. 강점 3개, 리스크 3개
6. 핵심 승부수 (go 시)

## 출력 (JSON)
{
  "score": 15,
  "tech_fit": 7,
  "client_relationship": 4,
  "price_competitiveness": 4,
  "positioning": "defensive",
  "positioning_rationale": "근거",
  "pros": ["강점1", "강점2", "강점3"],
  "risks": ["리스크1", "리스크2", "리스크3"],
  "strategic_focus": "핵심 승부수"
}
```

**기존 프롬프트 대비 제거 항목**:
- `score_breakdown` 5항목 (정량 축으로 대체)
- `recommendation` (합산 게이트로 대체)
- `fatal_flaw` (정량 fatal로 대체)
- 포지셔닝별 과거 성과 데이터 (정량 축 ①에서 처리)
- 포지셔닝 오버라이드 이력 (불필요한 컨텍스트 제거 → 토큰 절약)

---

## 4. 프론트엔드 변경

### 4.1 GoNoGoPanel.tsx 개편

**GngAnalysis 타입 확장**:

```typescript
interface GngAnalysis {
  // 기존
  win_probability?: number;       // feasibility_score로 매핑
  scores?: Array<{ label: string; score: number; max: number }>;  // max 추가
  strengths?: string[];
  risks?: string[];
  recommendation?: string;
  fatal_flaw?: string | null;
  strategic_focus?: string | null;

  // v4.0 신규
  score_tag?: "priority" | "standard" | "below_threshold" | "disqualified" | "";
  performance_detail?: PerformanceDetail;
  qualification_detail?: QualificationDetail;
  competition_detail?: CompetitionDetail;
}

interface PerformanceDetail {
  score: number;
  required_items?: Array<{
    raw_text: string;
    min_count: number;
    matched_count: number;
    is_met: boolean;
    matched_projects?: Array<{ title: string; amount: number; year: number }>;
  }>;
  coverage_rate?: number;
  same_client_wins?: number;
  is_fatal?: boolean;
  fatal_reason?: string;
}

interface QualificationDetail {
  score: number;
  mandatory?: Array<{
    requirement: string;
    status: "met" | "unmet" | "partial";
    matched_capability?: string;
  }>;
  preferred?: Array<{
    requirement: string;
    status: "met" | "unmet";
  }>;
  is_fatal?: boolean;
  fatal_reason?: string;
  summary?: string;
}

interface CompetitionDetail {
  score: number;
  intensity_level?: "low" | "medium" | "high";
  estimated_competitors?: number;
  top_competitors?: Array<{
    name: string;
    wins_at_client: number;
    head_to_head: string;
  }>;
  our_win_rate_at_client?: number;
}
```

**UI 레이아웃 변경**:

```
┌──────────────────────────────────────────────┐
│  Go/No-Go 의사결정                 [승인 대기] │
│  이 입찰에 자원을 투입할 가치가 있는가?         │
├──────────────────────────────────────────────┤
│                                              │
│  ★ 합산 점수        78 / 100   [일반 참여]    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━ ──── (70점 컷라인)  │
│                                              │
│  4축 분석                                     │
│  ┌────────────────────────────────────┐      │
│  │ 유사실적   ████████████░░░  22/30  │      │
│  │ 자격적격   ██████████████░  28/30  │      │
│  │ 경쟁강도   ████████░░░░░░  14/20  │      │
│  │ 전략가산   ██████████░░░░  14/20  │      │
│  └────────────────────────────────────┘      │
│                                              │
│  [▸ 유사실적 상세]  ← 접기/펼치기             │
│    요건: "최근 5년 내 10억 이상 SI 2건"        │
│    매칭: 3건 충족 ✅                           │
│    · 2024 XX사업 (12억)                       │
│    · 2023 YY사업 (15억)                       │
│    · 2025 ZZ사업 (11억)                       │
│    동일 발주기관 수주: 2건                     │
│                                              │
│  [▸ 자격 적격성 상세]                         │
│    필수 3/3 충족, 가점 2/4 보유               │
│    ✅ 소프트웨어사업자                         │
│    ✅ ISO 27001                               │
│    ✅ 정보보호 전문서비스 기업                  │
│    ⬜ GS인증 (가점)                           │
│                                              │
│  [▸ 경쟁 강도 상세]                           │
│    예상 참여: 5~6개사 (보통)                   │
│    주요 경쟁사: A사(3승1패), B사(1승2패)       │
│    해당 기관 자사 승률: 60%                    │
│                                              │
│  ─── 강점 / 리스크 ───                        │
│  + 강점1    - 리스크1                          │
│  + 강점2    - 리스크2                          │
│                                              │
│  AI 추천: go  |  핵심 승부수: "..."           │
│                                              │
│  ⚠️ Fatal: (자격 미충족 시 빨간 배너)          │
│                                              │
│  [포지셔닝 선택] 수성형 | 공격형 | 인접형      │
│  [의사결정 사유 textarea]                     │
│  [No-Go] [빠른 승인] [Go]                    │
└──────────────────────────────────────────────┘
```

**주요 UI 컴포넌트**:

1. **합산 점수 바**: 전체 진행바 + 70점 컷라인 마커 + score_tag 배지
2. **4축 바 차트**: 각 축별 `score/max` 수평 바. 색상: ≥70% 녹색, ≥50% 노란색, <50% 빨간색
3. **상세 접기/펼치기 (Collapsible)**: `useState` + 토글. 기본 접힘
4. **Fatal 배너**: `is_fatal` 시 상단에 빨간 경고 배너. "참가자격 미충족" 등

### 4.2 ArtifactReviewPanel.tsx — GoNoGoContent 수정

```typescript
function GoNoGoContent({ data }: { data: Record<string, unknown> }) {
  const score = data.feasibility_score as number | undefined;
  const scoreTag = data.score_tag as string | undefined;
  const breakdown = data.score_breakdown as Record<string, number> | undefined;
  // ... 기존 필드 유지 ...

  // 4축 바 차트 렌더링
  const axes = breakdown ? [
    { label: "유사실적", score: breakdown.similar_performance ?? 0, max: 30 },
    { label: "자격적격", score: breakdown.qualification ?? 0, max: 30 },
    { label: "경쟁강도", score: breakdown.competition ?? 0, max: 20 },
    { label: "전략가산", score: breakdown.strategic ?? 0, max: 20 },
  ] : [];

  // ... 렌더링 ...
}
```

---

## 5. DB 마이그레이션

### 5.1 `database/migrations/015_go_no_go_enhancement.sql`

```sql
-- Go/No-Go Enhancement v4.0: capabilities 자격 유형 보강

-- 기존 capabilities.type에 certification, license, registration 값이
-- track_record, tech, personnel 외에 추가로 사용될 수 있도록 주석만 갱신.
-- (TEXT 타입이라 CHECK 제약 없음 — 추가 DDL 불필요)

-- proposals 테이블에 domain 컬럼 추가 (유사실적 매칭용)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS domain TEXT;
COMMENT ON COLUMN proposals.domain IS 'SI/SW개발, 컨설팅, 감리, 인프라구축, 운영유지보수 등';

-- go_no_go_score 컬럼 추가 (4축 합산 스코어)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS go_no_go_score INTEGER;
COMMENT ON COLUMN proposals.go_no_go_score IS 'Go/No-Go 4축 합산 점수 (0~100)';

-- go_no_go_tag 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS go_no_go_tag TEXT;
COMMENT ON COLUMN proposals.go_no_go_tag IS 'priority|standard|below_threshold|disqualified';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_proposals_domain ON proposals(domain);
CREATE INDEX IF NOT EXISTS idx_proposals_gng_score ON proposals(go_no_go_score);
```

### 5.2 시드 데이터 확장 (`scripts/seed_data.py`)

```python
SEED_CAPABILITIES_QUALIFICATIONS = [
    # certification
    {"type": "certification", "title": "ISO 27001", "detail": "정보보안 경영시스템 인증", "keywords": ["ISO", "27001", "ISMS"]},
    {"type": "certification", "title": "ISO 9001", "detail": "품질경영시스템 인증", "keywords": ["ISO", "9001", "품질"]},
    {"type": "certification", "title": "ISMS-P", "detail": "정보보호 및 개인정보보호 관리체계 인증", "keywords": ["ISMS", "개인정보"]},
    {"type": "certification", "title": "GS인증", "detail": "Good Software 인증 (1등급)", "keywords": ["GS", "소프트웨어", "품질인증"]},
    {"type": "certification", "title": "SW품질인증", "detail": "소프트웨어 프로세스 품질인증", "keywords": ["SW", "품질", "프로세스"]},
    # license
    {"type": "license", "title": "소프트웨어사업자 신고", "detail": "소프트웨어산업진흥법 기반 신고", "keywords": ["소프트웨어사업자", "SW사업자"]},
    {"type": "license", "title": "정보통신공사업 등록", "detail": "정보통신공사업법 기반 등록", "keywords": ["정보통신공사", "통신공사"]},
    {"type": "license", "title": "정보보호 전문서비스 기업", "detail": "KISA 지정 정보보호 전문서비스 기업", "keywords": ["정보보호", "전문서비스", "KISA"]},
    # registration
    {"type": "registration", "title": "벤처기업 확인", "detail": "중소벤처기업부 벤처기업 확인서", "keywords": ["벤처", "벤처기업"]},
    {"type": "registration", "title": "중소기업 확인", "detail": "중소기업확인서", "keywords": ["중소기업"]},
    {"type": "registration", "title": "여성기업 확인", "detail": "여성기업확인서", "keywords": ["여성기업"]},
]
```

---

## 6. 에러 처리 및 Fallback

| 상황 | Fallback |
|------|----------|
| `qualification_requirements` 빈 배열 | 자격 축 = 25점 (요건 없음은 통과) |
| `similar_project_requirements` 빈 배열 | 유사실적 축 = 20점 (요건 없음) |
| AI 파싱 실패 (유사실적 구조화) | 원문 그대로 → AI 전략가산에 텍스트로 전달, 유사실적 축 = 15점 |
| DB 연결 실패 | 3축 모두 기본점수 (perf=15, qual=15, comp=10), 로그 warning |
| Lite 모드 | 3축 스킵, AI 전략가산만 20점 스케일로 실행 |
| competitor_count 데이터 없음 | 기본 estimated_competitors = 5 |

---

## 7. 수정 파일 요약

| # | 파일 | 변경 | 신규/수정 |
|---|------|------|-----------|
| 1 | `app/graph/state.py` | GoNoGoResult에 v4.0 필드 3개 추가 | 수정 |
| 2 | `app/graph/context_helpers.py` | `score_similar_performance`, `score_qualification`, `score_competition`, `_match_qualification` 추가 | 수정 |
| 3 | `app/graph/nodes/go_no_go.py` | 전면 개편 — 3축 정량 + `_ai_strategic_assessment` + 합산 게이트 | 수정 |
| 4 | `frontend/components/GoNoGoPanel.tsx` | 4축 바 차트 + 70점 컷라인 + 상세 접기/펼치기 + fatal 배너 | 수정 |
| 5 | `frontend/components/ArtifactReviewPanel.tsx` | GoNoGoContent 4축 렌더링 | 수정 |
| 6 | `database/migrations/015_go_no_go_enhancement.sql` | proposals.domain, go_no_go_score, go_no_go_tag | 신규 |
| 7 | `scripts/seed_data.py` | certification/license/registration 시드 추가 | 수정 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-26 | Initial design — 4축 스코어링 함수·노드·프론트 상세 설계 | AI |
