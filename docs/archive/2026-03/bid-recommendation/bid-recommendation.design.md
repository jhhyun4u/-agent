# Design: bid-recommendation

## 메타 정보
| 항목 | 내용 |
|------|------|
| Feature | bid-recommendation |
| 작성일 | 2026-03-08 |
| Plan 참조 | `docs/01-plan/features/bid-recommendation.plan.md` |
| 목표 | 나라장터 공고 수집 → AI 자격판정+매칭 → 추천 목록 제공 |

> **API 경로 변경 사항 (Plan 대비):** Plan F-04의 `/api/bids/*` 경로를 `/api/teams/{team_id}/bids/*`로 변경. 팀 단위 소유 원칙에 부합하는 설계. **이 문서(Design)의 경로를 구현 정본(source of truth)으로 사용할 것.**

---

## 1. 아키텍처 개요

```
[프론트엔드]
  /bids              → 추천 공고 목록
  /bids/[bidNo]      → 공고 상세 + AI 분석
  /bids/settings     → 팀 프로필 + 검색 프리셋 설정

      ↓ HTTP

[FastAPI — routes_bids.py]
  POST /api/teams/{team_id}/bids/fetch          ← 공고 수집 트리거
  GET  /api/teams/{team_id}/bids/recommendations ← 추천 목록
  GET  /api/teams/{team_id}/bids/announcements  ← 수집 공고 목록
  GET  /api/bids/{bid_no}                       ← 공고 상세
  POST /api/proposals/from-bid/{bid_no}         ← 제안서 생성 연동
  CRUD /api/teams/{team_id}/bid-profile         ← 팀 프로필
  CRUD /api/teams/{team_id}/search-presets      ← 검색 프리셋

      ↓

[서비스 레이어]
  BidFetcher          → G2BService 래퍼 (수집 + 후처리 필터 + DB upsert)
  BidRecommender      → Claude API (1단계 자격판정 → 2단계 매칭 점수)

      ↓

[외부 의존성]
  G2BService (기존)   → 나라장터 Open API (공고 목록/상세)
  Supabase            → bid_announcements, bid_recommendations, team_bid_profiles, search_presets
  Claude API          → claude-sonnet-4-5-20250929 (배치 분석)
```

---

## 2. DB 스키마 (F-06)

### 2.1 bid_announcements — 공고 원문 전역 캐시

```sql
CREATE TABLE bid_announcements (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_no                 TEXT UNIQUE NOT NULL,        -- 입찰공고번호 (bidNtceNo)
  bid_title              TEXT NOT NULL,               -- 공고명 (bidNtceNm)
  agency                 TEXT NOT NULL,               -- 발주기관 (ntcInsttNm)
  bid_type               TEXT,                        -- 공고종류 (bidClsfcNm)
  budget_amount          BIGINT,                      -- 추정가격 원 (presmptPrceAmt)
  announce_date          DATE,                        -- 공고일
  deadline_date          TIMESTAMPTZ,                 -- 입찰마감일시 (bfSpecRgstDt)
  days_remaining         INTEGER,                     -- 수집 시점 잔여일 (계산값)
  content_text           TEXT,                        -- 공고 상세내용 (규격서, 자격요건)
  qualification_available BOOLEAN DEFAULT true,       -- 자격요건 텍스트 확보 여부
  raw_data               JSONB,                       -- API 원본 응답
  fetched_at             TIMESTAMPTZ DEFAULT now(),
  created_at             TIMESTAMPTZ DEFAULT now()
);
```

**만료 공고 정리:** `deadline_date < now() - interval '7 days'` 건 앱 레벨에서 주기적 삭제

### 2.2 team_bid_profiles — 팀 AI 매칭 프로필

```sql
CREATE TABLE team_bid_profiles (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id                  UUID REFERENCES teams(id) ON DELETE CASCADE,
  expertise_areas          TEXT[],           -- 전문분야 배열
  tech_keywords            TEXT[],           -- 보유기술 키워드 배열
  past_projects            TEXT,             -- 수행실적 요약 (자유 텍스트)
  company_size             TEXT,             -- 개인/소기업/중기업/대기업
  certifications           TEXT[],           -- 보유 인증·자격 배열
  business_registration_type TEXT,           -- 개인/법인/중소기업/중견기업
  employee_count           INTEGER,          -- 임직원 수
  founded_year             INTEGER,          -- 설립연도
  created_at               TIMESTAMPTZ DEFAULT now(),
  updated_at               TIMESTAMPTZ DEFAULT now(),
  UNIQUE(team_id)                            -- 팀당 1개
);
```

### 2.3 search_presets — 검색 조건 프리셋

```sql
CREATE TABLE search_presets (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id            UUID REFERENCES teams(id) ON DELETE CASCADE,
  name               TEXT NOT NULL,                    -- 프리셋명
  keywords           TEXT[] NOT NULL,                  -- 검색 키워드 배열 (최대 3개 권장)
  min_budget         BIGINT DEFAULT 100000000,          -- 최소 사업금액 (기본 1억)
  min_days_remaining INTEGER DEFAULT 5,                 -- 최소 잔여일
  bid_types          TEXT[] DEFAULT '{용역}',            -- 공고종류 필터
  preferred_agencies TEXT[],                            -- 선호 발주기관 (빈 배열 = 전체)
  is_active          BOOLEAN DEFAULT false,
  created_at         TIMESTAMPTZ DEFAULT now(),
  updated_at         TIMESTAMPTZ DEFAULT now()
);

-- 팀당 활성 프리셋 1개 보장
CREATE UNIQUE INDEX idx_search_presets_active
  ON search_presets(team_id) WHERE is_active = true;
```

### 2.4 bid_recommendations — AI 분석 결과 캐시

```sql
CREATE TABLE bid_recommendations (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id                 UUID REFERENCES teams(id) ON DELETE CASCADE,
  bid_no                  TEXT REFERENCES bid_announcements(bid_no) ON DELETE CASCADE,
  preset_id               UUID REFERENCES search_presets(id),

  -- 1단계: 자격 판정
  qualification_status    TEXT NOT NULL,    -- 'pass' | 'fail' | 'ambiguous'
  disqualification_reason TEXT,             -- fail 제외 이유
  qualification_notes     TEXT,             -- ambiguous 불명확 사유

  -- 2단계: 매칭 점수 (qualification_status = 'fail'이면 NULL)
  match_score             INTEGER,          -- 0~100
  match_grade             TEXT,             -- S/A/B/C/D
  recommendation_summary  TEXT,             -- 1줄 추천 요약 (필수)
  recommendation_reasons  JSONB,            -- [{category, reason, strength}] 1개 이상 필수
  risk_factors            JSONB,            -- [{risk, level}]
  win_probability_hint    TEXT,             -- 상/중상/중/중하/하
  recommended_action      TEXT,             -- 적극 검토/검토/보류

  analyzed_at  TIMESTAMPTZ DEFAULT now(),
  expires_at   TIMESTAMPTZ,                 -- 24h TTL
  UNIQUE(team_id, bid_no, preset_id)
);
```

---

## 3. Pydantic 스키마 (`app/models/bid_schemas.py`)

```python
class BidAnnouncement(BaseModel):
    bid_no: str
    bid_title: str
    agency: str
    bid_type: Optional[str]
    budget_amount: Optional[int]
    announce_date: Optional[date]
    deadline_date: Optional[datetime]
    days_remaining: Optional[int]
    content_text: Optional[str]
    qualification_available: bool = True

class TeamBidProfile(BaseModel):
    team_id: str
    expertise_areas: list[str] = []
    tech_keywords: list[str] = []
    past_projects: str = ""
    company_size: Optional[str] = None
    certifications: list[str] = []
    business_registration_type: Optional[str] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None

class SearchPreset(BaseModel):
    id: Optional[str] = None
    team_id: str
    name: str
    keywords: list[str]
    min_budget: int = 100_000_000
    min_days_remaining: int = 5
    bid_types: list[str] = ["용역"]
    preferred_agencies: list[str] = []
    is_active: bool = False

# ── Claude 1단계 응답 스키마 ──
class QualificationResult(BaseModel):
    bid_no: str
    qualification_status: Literal["pass", "fail", "ambiguous"]
    disqualification_reason: Optional[str] = None
    qualification_notes: Optional[str] = None

# ── Claude 2단계 응답 스키마 ──
class RecommendationReason(BaseModel):
    category: Literal["전문성", "실적", "규모", "기술", "지역", "기타"]
    reason: str
    strength: Literal["high", "medium", "low"]

class RiskFactor(BaseModel):
    risk: str
    level: Literal["high", "medium", "low"]

class BidRecommendation(BaseModel):
    bid_no: str
    match_score: int                      # 0~100
    match_grade: str                      # S/A/B/C/D
    recommendation_summary: str           # 필수, 1줄
    recommendation_reasons: list[RecommendationReason] = Field(min_length=1)  # 1개 이상 필수
    risk_factors: list[RiskFactor] = []
    win_probability_hint: str
    recommended_action: str
```

---

## 4. 서비스 레이어 설계

### 4.1 BidFetcher (`app/services/bid_fetcher.py`)

**역할:** G2BService 래퍼 + 후처리 필터 + DB upsert

```python
class BidFetcher:
    def __init__(self, g2b_service: G2BService, supabase_client):
        self.g2b = g2b_service
        self.db = supabase_client

    async def fetch_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        1. 키워드별 G2BService.search_bid_announcements(keyword, num_of_rows=100) 호출 후 합산
           - num_of_rows=100 고정 (기본값 20에서 변경 필요)
           - 키워드 최대 3개 권장 (API 쿼터: 3개×100건=300건/수집)
           - 페이징 불필요 (100건/키워드로 충분, 초과 시 키워드 세분화 권장)
        2. 후처리 필터 적용:
           - min_budget: presmptPrceAmt < preset.min_budget 제거
           - min_days_remaining: deadline - today < preset.min_days_remaining 제거
           - bid_types: bidClsfcNm not in preset.bid_types 제거
        3. BidAnnouncement 스키마로 정규화
        4. bid_announcements 테이블에 upsert (bid_no 기준)
        5. 각 공고별 fetch_bid_detail() 호출하여 content_text 확보
        """

    async def fetch_bid_detail(self, bid_no: str) -> Optional[str]:
        """
        G2BService.get_bid_detail(bid_no) 호출 (G2BService에 public 메서드 추가 필요)
        → 내부적으로 BidPublicInfoService04/getBidPblancDetailInfoServc 엔드포인트 호출
        - ntceSpecCn 필드에서 자격요건 포함 상세내용 추출
        - 내용 없음 or "첨부파일 참조" → qualification_available = False

        ⚠️ G2BService 수정 사항:
            async def get_bid_detail(self, bid_no: str) -> dict:
                return await self._call_api(
                    "BidPublicInfoService04/getBidPblancDetailInfoServc",
                    {"bidNtceNo": bid_no}
                )
        """
```

**나라장터 API 필드 매핑:**

| DB 컬럼 | API 필드 | 비고 |
|---------|---------|------|
| `bid_no` | `bidNtceNo` | 입찰공고번호 |
| `bid_title` | `bidNtceNm` | 공고명 |
| `agency` | `ntcInsttNm` | 발주기관 |
| `budget_amount` | `presmptPrceAmt` | 추정가격 (원) |
| `deadline_date` | `bfSpecRgstDt` | 입찰마감일시 |
| `bid_type` | `bidClsfcNm` | 공고종류 |
| `content_text` | 상세API `ntceSpecCn` | 자격요건 포함 |

**후처리 필터 로직:**
```python
# 용역 공고만 (기본값)
if bid.bid_type and bid.bid_type not in preset.bid_types:
    continue

# 최소 금액
if bid.budget_amount and bid.budget_amount < preset.min_budget:
    continue

# 최소 잔여일
days = (bid.deadline_date.date() - date.today()).days
if days < preset.min_days_remaining:
    continue
```

### 4.2 BidRecommender (`app/services/bid_recommender.py`)

**역할:** 2단계 Claude 분석 (자격 판정 → 매칭 점수)

```python
class BidRecommender:
    BATCH_SIZE = 20  # 배치당 공고 수

    async def analyze_bids(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement],
        top_n: int = 20
    ) -> tuple[list[BidRecommendation], list[QualificationResult]]:
        """1단계 → 2단계 통합 실행"""
        # 1단계: 자격 판정 (전체)
        qual_results = await self.check_qualifications(team_profile, bids)

        # 2단계: pass + ambiguous만 매칭
        eligible = [b for b in bids
                    if qual_results_map[b.bid_no].qualification_status != "fail"]
        recommendations = await self.score_bids(team_profile, eligible[:top_n])

        return recommendations, qual_results

    async def check_qualifications(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement]
    ) -> list[QualificationResult]:
        """
        1단계 배치 자격 판정 (20건/호출)
        qualification_available = False → 자동 ambiguous + "원문 확인 필요"
        """

    async def score_bids(
        self,
        team_profile: TeamBidProfile,
        bids: list[BidAnnouncement]
    ) -> list[BidRecommendation]:
        """
        2단계 배치 매칭 점수 산출 (20건/호출)
        match_score 내림차순 정렬하여 반환
        """
```

**Claude 1단계 프롬프트 구조:**
```
SYSTEM: 당신은 입찰 자격 판정 전문가입니다.
        팀 프로필과 공고 자격요건을 비교하여 pass/fail/ambiguous를 판정합니다.
        [팀 프로필 정보]

USER:   다음 {N}개 공고에 대해 자격 판정을 수행하세요.
        각 공고의 bid_no와 qualification_status를 JSON 배열로 반환하세요.
        [공고 목록 — bid_no, bid_title, content_text 요약]

        응답 형식: [{"bid_no":"...", "qualification_status":"pass|fail|ambiguous", ...}]
```

**Claude 2단계 프롬프트 구조:**
```
SYSTEM: 당신은 입찰 매칭 분석 전문가입니다.
        팀 역량과 공고를 비교하여 매칭 점수와 추천 사유를 생성합니다.
        recommendation_reasons는 반드시 1개 이상 포함해야 합니다.
        [팀 프로필 정보]

USER:   다음 {N}개 공고에 대해 매칭 분석을 수행하세요.
        [공고 목록]

        응답 형식: [{...BidRecommendation 스키마...}]
```

**match_grade 기준:**
| 점수 범위 | 등급 |
|-----------|------|
| 90~100 | S |
| 80~89 | A |
| 70~79 | B |
| 60~69 | C |
| 0~59 | D |

---

## 5. API 설계 (`app/api/routes_bids.py`)

### 5.1 팀 프로필 관리

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/teams/{team_id}/bid-profile` | 팀 AI 매칭 프로필 조회 |
| `PUT` | `/api/teams/{team_id}/bid-profile` | 팀 AI 매칭 프로필 생성/수정 (upsert) |

**인증:** Bearer JWT 필수 (`get_current_user`)
**권한:** 팀 멤버 이상 (`_require_team_member`)

### 5.2 검색 프리셋 관리

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/teams/{team_id}/search-presets` | 프리셋 목록 조회 |
| `POST` | `/api/teams/{team_id}/search-presets` | 프리셋 생성 |
| `PUT` | `/api/teams/{team_id}/search-presets/{id}` | 프리셋 수정 |
| `DELETE` | `/api/teams/{team_id}/search-presets/{id}` | 프리셋 삭제 |
| `POST` | `/api/teams/{team_id}/search-presets/{id}/activate` | 활성 프리셋 전환 |

**활성 전환 로직:**
트랜잭션: 1) 팀의 모든 프리셋 `is_active=false` → 2) 지정 ID `is_active=true`

### 5.3 공고 수집 및 추천

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/teams/{team_id}/bids/fetch` | 활성 프리셋으로 공고 수집 트리거 |
| `GET` | `/api/teams/{team_id}/bids/recommendations` | 추천 공고 목록 |
| `GET` | `/api/teams/{team_id}/bids/announcements` | 수집 공고 목록 (필터/페이징) |
| `GET` | `/api/bids/{bid_no}` | 공고 상세 + AI 분석 결과 |

**POST /fetch 동작:**
- 즉시 `{"status": "fetching", "message": "공고 수집을 시작합니다"}` 반환
- `BackgroundTasks`로 BidFetcher.fetch_bids_by_preset() 실행

**GET /recommendations 응답 구조:**
```json
{
  "data": {
    "recommended": [
      {
        "bid_no": "...",
        "bid_title": "...",
        "agency": "...",
        "budget_amount": 300000000,
        "deadline_date": "2026-03-20T18:00:00+09:00",
        "days_remaining": 12,
        "qualification_status": "pass",
        "match_score": 85,
        "match_grade": "A",
        "recommendation_summary": "...",
        "recommendation_reasons": [...],
        "risk_factors": [...],
        "win_probability_hint": "중상",
        "recommended_action": "적극 검토"
      }
    ],
    "excluded": [
      {
        "bid_no": "...",
        "bid_title": "...",
        "qualification_status": "fail",
        "disqualification_reason": "..."
      }
    ]
  },
  "meta": {
    "total_fetched": 45,
    "analyzed_at": "2026-03-08T10:00:00+09:00"
  }
}
```

**GET /announcements 쿼리 파라미터:**
- `keyword`: 공고명 검색
- `min_budget`: 최소 사업금액
- `min_days`: 최소 잔여일
- `bid_type`: 공고종류 필터
- `agency`: 발주기관 검색
- `page`: 페이지 번호 (기본 1)
- `per_page`: 페이지당 건수 (기본 20, 최대 100)

### 5.4 제안서 연동

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/proposals/from-bid/{bid_no}` | 공고 → 제안서 생성 |

**동작:** `bid_announcements.content_text`를 RFP 내용으로 주입 → 기존 `POST /api/proposals/generate` 재사용

---

## 6. 캐시 전략

| 대상 | TTL | 무효화 조건 |
|------|-----|-----------|
| `bid_announcements` | deadline + 7일 | 자동 만료 |
| `bid_recommendations` | 24시간 | 팀 프로필 변경 시 즉시 무효화 |
| 팀 프로필 변경 감지 | - | `team_bid_profiles.updated_at` 비교 |

**캐시 히트 판정 (GET /recommendations):**
```python
# expires_at > now() AND team_profile.updated_at < analyzed_at
# 위 조건 충족 시 캐시 반환, 아니면 재분석
```

---

## 7. 프론트엔드 설계

### 7.1 페이지 구조

```
/bids                    → 추천 공고 목록 페이지 (메인)
/bids/[bidNo]            → 공고 상세 + AI 분석
/bids/settings           → 팀 프로필 + 검색 프리셋 설정
```

### 7.2 /bids 페이지 (추천 공고 목록)

```
┌─────────────────────────────────────────────────────────┐
│ 공고 추천                              [공고 수집] 버튼  │
│ 활성 프리셋: [AI분야 ▼]                                  │
│ 키워드: AI, LLM | 최소금액: 1억 | 잔여 5일 이상         │
├─────────────────────────────────────────────────────────┤
│ [추천 공고 23건] [제외된 공고 15건]                      │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 85점 A │ D-12 │ LLM 기반 AI 교육 시스템 개발      │ │
│ │ 과학기술정보통신부 · 3억원                          │ │
│ │ ⚡ 전문성 일치  📋 실적 보유  💰 규모 적합          │ │
│ │ "핵심 역량과 직접 부합하는 최우선 검토 대상"        │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 72점 B │ D-8 │ ⚠️ 자격 확인 필요  클라우드 전환... │ │
│ │ 행정안전부 · 2억원                                  │ │
│ │ ...                                                 │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**추천 카드 항목:**
- Match Score 배지 (점수 + 등급)
- D-day 마감 배지 (7일 이하 빨간색, 14일 이하 주황색)
- `ambiguous` 경고 배지 (주황색 "자격 확인 필요")
- `recommendation_reasons` 중 `strength="high"` 최대 3개 카테고리 배지
- `recommendation_summary` 1줄 요약
- "이 공고로 제안서 만들기" 버튼

### 7.3 /bids/[bidNo] 페이지 (공고 상세)

```
┌─────────────────────────────────────────────────────────┐
│ LLM 기반 AI 교육 시스템 개발                             │
│ 과학기술정보통신부 | 3억원 | D-12 마감                    │
├─────────────────────────────────────────────────────────┤
│ 🤖 AI 분석 결과                                          │
│                                                          │
│ 매칭 점수 ══════════════════════════ 85/100 (A등급)      │
│                                                          │
│ "LLM 기반 AI 교육 시스템 개발 사업으로, 귀사의 핵심      │
│  역량과 직접 부합하는 최우선 검토 대상입니다."           │
│                                                          │
│ 추천 사유                                                │
│ ⚡ 전문성 · AI/ML 및 LLM 개발 역량과 직접 일치 ████     │
│ 📋 실적   · 유사 AI 교육 플랫폼 구축 실적 보유  ████     │
│ 💰 규모   · 사업금액 3억원, 희망 범위 내        ███      │
│                                                          │
│ 리스크 요인                                              │
│ ⚠️ 중간 · 대형 SI업체 경쟁 가능성                        │
├─────────────────────────────────────────────────────────┤
│ 공고 원문                                                │
│ [공고 규격 내용 전문 표시...]                            │
├─────────────────────────────────────────────────────────┤
│         [이 공고로 제안서 만들기]                         │
└─────────────────────────────────────────────────────────┘
```

### 7.4 /bids/settings 페이지

**온보딩 가드:**
1. 미인증 → `/login` 리다이렉트
2. 팀 미가입 → "팀을 먼저 생성하세요" 안내 + `/teams/new` 버튼
3. 프로필 미설정 → 빈 상태 화면 "팀 프로필을 설정하면 맞춤 공고 추천이 시작됩니다"

**탭 구성:**
- 탭 1 — 팀 프로필 (전문분야 체크박스, 보유기술 태그 입력, 수행실적 텍스트, 자격증 태그, 사업자 정보)
- 탭 2 — 검색 조건 프리셋 (키워드 태그 입력, 최소 금액 슬라이더, 최소 잔여일 스피너, 공고종류 체크박스)

### 7.5 네비게이션 추가

기존 `proposals` 메뉴 옆에 `공고 추천` 메뉴 추가 (`/bids`)

---

## 8. 구현 순서 (Implementation Order)

```
F-06 DB 스키마          → database/schema_bids.sql 작성
  ↓
F-02 팀 프로필 + 프리셋  → bid_schemas.py (TeamBidProfile, SearchPreset)
                          routes_bids.py (프로필·프리셋 CRUD 엔드포인트)
  ↓
F-01 BidFetcher         → bid_fetcher.py (G2BService 래퍼 + 후처리 필터)
  ↓
F-03 BidRecommender     → bid_recommender.py (1단계 자격판정 + 2단계 매칭)
  ↓
F-04 추천 API           → routes_bids.py (수집 트리거, 추천 목록, 상세)
  ↓
F-05 프론트엔드          → /bids, /bids/[bidNo], /bids/settings 페이지
```

---

## 9. 에러 처리

| 상황 | 처리 방식 |
|------|----------|
| 나라장터 API 호출 실패 | G2BService exponential backoff 재사용, 3회 실패 시 부분 결과 반환 |
| 공고 상세 미제공 | `qualification_available=false` 설정, ambiguous 자동 분류 |
| Claude API 타임아웃 | 30초 timeout, 실패 시 해당 배치 건너뜀 후 재시도 엔드포인트 제공 |
| 팀 프로필 미설정 | `GET /recommendations` 시 `422 Unprocessable Entity` + "팀 프로필을 먼저 설정하세요" |
| 활성 프리셋 없음 | `GET /recommendations` 시 `422` + "검색 조건 프리셋을 먼저 생성하세요" |
| recommendation_reasons 빈 배열 | 프롬프트에서 강제, 파서에서 `Field(min_length=1)` 검증 후 재시도 |

### 입력 검증 규칙

| 필드 | 검증 규칙 | 에러 |
|------|----------|------|
| `keywords` | 1개 이상, 최대 5개, 항목당 최대 20자 | `422` |
| `min_budget` | 0 이상, 최대 100,000,000,000 (1천억) | `422` |
| `min_days_remaining` | 1~30 | `422` |
| `bid_types` | 1개 이상, 허용값: `["용역","공사","물품"]` | `422` |
| `bid_no` (경로 파라미터) | 숫자+하이픈 패턴만 허용 (`^[\d\-]+$`) — injection 방지 | `400` |

### Rate Limiting (수집 트리거 남용 방지)

`POST /api/teams/{team_id}/bids/fetch`
- 팀당 최소 수집 간격: **1시간** (Redis 또는 Supabase `last_fetched_at` 컬럼 비교)
- 간격 미달 시: `429 Too Many Requests` + `"마지막 수집: N분 전. 1시간 후 다시 시도하세요."`

---

## 10. 테스트 계획

### 단위 테스트 (BidFetcher)
| 테스트 케이스 | 검증 항목 |
|-------------|----------|
| `test_filter_min_budget` | budget_amount < min_budget인 공고 제거 |
| `test_filter_min_days` | days_remaining < min_days_remaining인 공고 제거 |
| `test_filter_bid_type` | bid_type이 "공사"인 공고가 기본 필터에서 제거됨 |
| `test_qualification_unavailable` | `qualification_available=false`인 공고가 ambiguous로 분류됨 |
| `test_no_duplicate_bids` | 동일 bid_no가 여러 키워드에서 수집돼도 1건만 upsert |

### 단위 테스트 (BidRecommender)
| 테스트 케이스 | 검증 항목 |
|-------------|----------|
| `test_fail_excluded_from_scoring` | qualification_status=fail 공고가 2단계 진입 안 함 |
| `test_recommendation_reasons_not_empty` | BidRecommendation.recommendation_reasons 항상 1개 이상 |
| `test_batch_processing` | 21건 입력 시 2배치(20+1)로 분리하여 Claude 호출 |
| `test_match_grade_mapping` | 점수 범위별 등급(S/A/B/C/D) 정확히 매핑 |

### API 통합 테스트
| 테스트 케이스 | 검증 항목 |
|-------------|----------|
| `test_crud_bid_profile` | 팀 프로필 생성→조회→수정 정상 동작 |
| `test_preset_activate_uniqueness` | 활성 프리셋 전환 시 기존 활성 프리셋 비활성화 |
| `test_fetch_requires_active_preset` | 활성 프리셋 없을 때 422 반환 |
| `test_fetch_rate_limit` | 1시간 내 재수집 시 429 반환 |
| `test_recommendations_cache_hit` | 캐시 유효 시 Claude 재호출 없음 |
| `test_recommendations_cache_invalidate` | 프로필 변경 후 재분석 실행됨 |
| `test_unauthorized_access` | 타 팀 리소스 접근 시 403 반환 |

---

## 11. 환경 변수

```env
DATA_GO_KR_API_KEY=...   # 공공데이터포털 API 인증키 (기존 G2BService 공유)
```

**기존 변수 재사용:** `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`

---

## 11. 성공 기준 (Plan에서 이관)

- [ ] 검색 조건 프리셋 CRUD 및 활성 전환 동작
- [ ] 수집된 공고에 공사·물품 공고 미포함 (용역만)
- [ ] min_budget / min_days_remaining 후처리 필터 동작
- [ ] 자격 fail 공고가 추천 목록에 미포함
- [ ] 자격 ambiguous 공고에 "자격 확인 필요" 배지 표시
- [ ] 제외된 공고 탭에서 fail 공고 + 제외 이유 확인 가능
- [ ] match_score (0~100) + recommendation_reasons (1개 이상) 항상 함께 생성
- [ ] 추천 카드에 high strength 사유가 카테고리 배지로 최대 3개 표시
- [ ] 공고 상세에서 전체 추천 사유 목록 확인 가능
- [ ] "제안서 만들기" 버튼 → 기존 제안서 생성 플로우 연결
- [ ] Gap Analysis >= 90%
