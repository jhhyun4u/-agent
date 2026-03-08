# Plan: bid-recommendation

## 메타 정보
| 항목 | 내용 |
|------|------|
| Feature | bid-recommendation |
| 작성일 | 2026-03-08 |
| 목표 | 조달청 나라장터 공고를 수집하고, 팀/개인 역량과 매칭하여 최적 사업 공고를 추천 |

---

## 배경

tenopa-proposer는 RFP를 받아 제안서를 생성하는 도구다.
그러나 현재는 "이미 RFP를 가진 상태"를 전제로 한다.
실제 사용자에게는 **어떤 공고에 참여할지 발굴**하는 과정이 먼저 필요하다.

조달청 나라장터는 공공 Open API를 제공하며, 매일 수백 건의 용역 공고가 등록된다.
이 공고들을 자동 수집하고, 팀의 역량·전문분야·수행 실적과 비교하여
**최적 공고를 추천 + 이유 설명**하는 기능을 구현한다.

---

## 사용자 시나리오

```
1. 사용자가 팀 프로필(전문분야, 보유기술, 수행실적, 자격/인증 보유 현황)과 검색 조건을 등록한다.
   - 검색 조건 예시: 키워드=["AI","LLM","교육"], 최소금액=1억, 최소잔여일=5
2. 시스템이 검색 조건을 나라장터 API 파라미터로 변환하여 용역 공고만 수집한다.
   (공사·물품 공고는 수집 단계에서 제외)
3. Claude API가 공고별 자격요건을 팀 프로필과 비교하여 3단계로 판정한다.
   - 충족(pass): 매칭 분석 진행
   - 불충족(fail): 추천 목록에서 제외 + 제외 이유 기록
   - 불명확(ambiguous): 주의 표시와 함께 추천 목록에 포함
4. 사용자는 추천 공고 목록을 보고 관심 공고를 선택한다.
5. 선택한 공고로 바로 "제안서 생성" 플로우로 진입할 수 있다.
```

---

## 구현 범위

### F-01: 나라장터 공고 수집 (bid_fetcher)

**목표:** 검색 조건 프리셋을 기반으로 나라장터 공고를 수집하고, 공고 상세내용(자격요건 포함)을 확보

> **⚠️ 기존 코드 재사용 원칙**: `app/services/g2b_service.py`에 `G2BService.search_bid_announcements()`가 이미 구현되어 있다. `bid_fetcher.py`는 새로 API 연동 코드를 작성하지 않고 `G2BService`를 내부적으로 사용한다.

**구현 내용:**
- `app/services/bid_fetcher.py` (신규) — G2BService 래퍼 + 필터·정규화 레이어
  - `BidFetcher` 클래스
  - `fetch_bids_by_preset(search_preset)` — 프리셋 기반 수집 통합 실행
    1. `G2BService.search_bid_announcements(keyword)` 키워드별 반복 호출 후 합산
    2. **후처리 필터링** (API가 미지원하는 조건들):
       - `min_budget` 필터: `presmptPrceAmt < min_budget` 건 제거
       - `min_days_remaining` 필터: `bfSpecRgstDt(마감일) - today < min_days` 건 제거
       - `bid_types` 필터: `bidClsfcNm`이 "용역" 아닌 건 제거
    3. 통과한 공고 → `BidAnnouncement` Pydantic 스키마로 정규화
    4. Supabase `bid_announcements` 테이블에 upsert
  - `fetch_bid_detail(bid_no)` — 공고 상세내용 수집 (**자격요건 확보를 위해 필수**)
    - `G2BService._call_api("BidPublicInfoService04/getBidPblancDetailInfoServc", {"bidNtceNo": bid_no})`
    - 반환된 상세내용(`ntcInsttNm`, `rsrvtnPrceRng`, `qualificationsText` 등)을 `bid_announcements.content_text`에 저장
    - **자격요건 텍스트가 없거나 "첨부파일 참조"인 경우** → `qualification_available = false` 플래그 설정
  - 중복 수집 방지: `bid_no` 기준 upsert

**나라장터 API 필드 매핑:**
| `bid_announcements` 컬럼 | 나라장터 API 필드 | 비고 |
|--------------------------|------------------|------|
| `bid_no` | `bidNtceNo` | 입찰공고번호 |
| `bid_title` | `bidNtceNm` | 공고명 |
| `agency` | `ntcInsttNm` | 공고기관 |
| `budget_amount` | `presmptPrceAmt` | 추정가격 (원) |
| `deadline_date` | `bfSpecRgstDt` | 입찰마감일시 |
| `bid_type` | `bidClsfcNm` | 입찰분류명 |
| `content_text` | 상세API `ntceSpecCn` | 공고 규격내용 (자격요건 포함) |

**예상 공수:** ~5h

---

### F-02: 팀 프로필 + 검색 조건 관리

**목표:** AI 매칭 기준이 되는 팀 역량(프로필)과, 나라장터 API 필터링 기준이 되는 검색 조건 프리셋을 분리하여 관리

**세 개념의 역할 구분:**
- **팀 프로필 (team_bid_profiles):** Claude AI 분석의 컨텍스트. "우리 팀이 어떤 팀이고, 어떤 자격을 보유했는가"
- **검색 조건 프리셋 (search_presets):** 나라장터 API 호출 파라미터. "어떤 공고를 가져올 것인가"
- **자격 판정 (qualification check):** AI 분석 1단계. "이 공고에 참여 자격이 있는가" (pass/fail/ambiguous)

> **⚠️ 소유 단위 설계 원칙**: 이 기능은 "팀이 관심있는 공고"를 찾는 것이다. 기존 `teams` 테이블 (`routes_team.py`)에 팀이 이미 관리된다. `team_bid_profiles`와 `search_presets`는 **`team_id`를 소유 단위**로 한다 (`user_id` 아님). 팀원 누구나 팀의 프로필과 검색 조건을 공유한다. 개인 사용자(팀 미가입)는 팀을 먼저 생성 후 사용한다.

**구현 내용:**
- DB: `team_bid_profiles` 테이블 (AI 매칭·자격 판정용) ← `team_profiles` 이름 충돌 방지
  - `id`, **`team_id` UUID REFERENCES teams(id)** (팀 단위 소유)
  - `expertise_areas` (전문분야 배열: IT/SW개발, AI/ML, 컨설팅, 교육, 연구 등)
  - `tech_keywords` (보유기술 키워드 배열)
  - `past_projects` (수행실적 요약 텍스트)
  - `company_size` (개인/소기업/중기업/대기업)
  - `certifications` (보유 인증·자격 배열, 예: `["ISO27001", "GS인증", "SW기업확인서"]`)
  - `business_registration_type` (사업자 유형: 개인/법인/중소기업/중견기업)
  - `employee_count` (임직원 수, 자격요건 판단용)
  - `founded_year` (설립연도, 업력 요건 판단용)
  - `created_at`, `updated_at`
  - `UNIQUE(team_id)` — 팀당 프로필 1개

- DB: `search_presets` 테이블 (공고 수집 필터용)
  - `id`, **`team_id` UUID REFERENCES teams(id)** (팀 단위 소유)
  - `name` (프리셋명: "기본", "AI분야", "교육사업" 등)
  - `keywords` (검색 키워드 배열, 예: `["AI","LLM","지능형"]`) ← **핵심**
  - `min_budget` (최소 사업금액, 원, 기본값: `100000000` = 1억)
  - `min_days_remaining` (최소 잔여일, 기본값: `5`)
  - `bid_types` (공고종류 배열: **`["용역"]` 고정 기본값, 공사·물품 선택 시 UI 경고**)
  - `preferred_agencies` (선호 발주기관 배열, 비어있으면 전체)
  - `is_active` (현재 적용 중인 프리셋 여부)
  - `created_at`, `updated_at`

- `app/api/routes_bids.py` — 엔드포인트 (팀 컨텍스트 기반)
  - `GET /api/teams/{team_id}/bid-profile` / `PUT /api/teams/{team_id}/bid-profile`
  - `GET /api/teams/{team_id}/search-presets` — 프리셋 목록
  - `POST /api/teams/{team_id}/search-presets` — 프리셋 생성
  - `PUT /api/teams/{team_id}/search-presets/{id}` — 프리셋 수정
  - `DELETE /api/teams/{team_id}/search-presets/{id}` — 프리셋 삭제
  - `POST /api/teams/{team_id}/search-presets/{id}/activate` — 활성 프리셋 전환

- 프론트엔드: `frontend/app/bids/settings/page.tsx` — 통합 설정 페이지
  - **온보딩 가드**: 팀 미가입 상태면 "먼저 팀을 생성하세요" 안내 → `/teams/new` 리다이렉트
  - **프로필 미설정 상태**: "팀 프로필을 설정하면 맞춤 공고 추천이 시작됩니다" 빈 상태 화면
  - 탭 1: 팀 프로필 (AI 매칭 컨텍스트)
  - 탭 2: 검색 조건 프리셋 목록 + 생성/수정
    - 키워드 태그 입력 (태그 추가/삭제 UI)
    - 최소 금액 슬라이더/입력 (1천만 ~ 100억)
    - 최소 잔여일 스피너 (1~30일)
    - 공고종류 체크박스 (용역/공사/물품)
    - 선호 발주기관 태그 입력 (선택사항)

**예상 공수:** ~4h

---

### F-03: AI 분석 엔진 (bid_recommender) — 2단계 구조

**목표:** Claude API로 ① 자격 판정 → ② 매칭 점수 순서로 분석. 자격 불충족 공고는 추천에서 제외

**2단계 분석 구조:**

```
수집된 공고
    │
    ▼
[1단계] 자격 판정 (Qualification Check) — 배치 처리
    │  Claude가 공고의 자격요건 vs 팀 프로필을 비교
    │
    ├─ pass      → [2단계] 매칭 점수 분석 진행
    ├─ ambiguous → [2단계] 매칭 점수 분석 진행 + "자격 불명확" 경고 표시
    └─ fail      → 제외 (제외 이유 기록, 별도 "제외된 공고" 탭에서 확인 가능)
    │
    ▼
[2단계] 매칭 점수 분석 (Match Scoring) — 배치 처리
    │  pass/ambiguous 공고만 대상
    │
    ▼
추천 목록 (match_score 내림차순)
```

**구현 내용:**
- `app/services/bid_recommender.py` (신규)
  - `BidRecommender` 클래스
  - `check_qualifications(team_profile, bids)` — 1단계: 배치 자격 판정
  - `score_bids(team_profile, bids)` — 2단계: 배치 매칭 점수 산출
  - `analyze_bids(team_profile, bids, top_n=20)` — 1+2단계 통합 실행

  - **1단계 Claude 응답 스키마 (배치, 20건):**
    ```json
    [
      {
        "bid_no": "20260308-001",
        "qualification_status": "pass",
        "qualification_notes": null
      },
      {
        "bid_no": "20260308-002",
        "qualification_status": "fail",
        "disqualification_reason": "중소기업자간 경쟁제품 지정 품목 - 물품 납품 자격 불충족"
      },
      {
        "bid_no": "20260308-003",
        "qualification_status": "ambiguous",
        "qualification_notes": "실적 요건(유사 용역 2건 이상) 충족 여부가 수행실적 기술 방식에 따라 달라질 수 있음"
      }
    ]
    ```

  - **2단계 Claude 응답 스키마 (배치, 20건):**
    ```json
    [
      {
        "bid_no": "20260308-001",
        "match_score": 85,
        "match_grade": "A",
        "recommendation_summary": "LLM 기반 AI 교육 시스템 개발 사업으로, 귀사의 핵심 역량과 직접 부합하는 최우선 검토 대상입니다.",
        "recommendation_reasons": [
          {
            "category": "전문성",
            "reason": "AI/ML 및 LLM 개발 역량이 사업 핵심 요구사항과 직접 일치",
            "strength": "high"
          },
          {
            "category": "실적",
            "reason": "유사 AI 교육 플랫폼 구축 수행실적 보유",
            "strength": "high"
          },
          {
            "category": "규모",
            "reason": "사업금액 3억원으로 희망 사업 규모 범위 내",
            "strength": "medium"
          }
        ],
        "risk_factors": [
          {
            "risk": "대형 SI업체 경쟁 가능성",
            "level": "medium"
          }
        ],
        "win_probability_hint": "중상",
        "recommended_action": "적극 검토"
      }
    ]
    ```
  - `recommendation_reasons[].category`: `"전문성"` | `"실적"` | `"규모"` | `"기술"` | `"지역"` | `"기타"`
  - `recommendation_reasons[].strength`: `"high"` | `"medium"` | `"low"` — 사유 강도 (UI 강조 표시용)
  - `recommendation_reasons`는 **1개 이상 필수** — 빈 배열 불허 (프롬프트 지침으로 강제)

  - 배치 처리: 1단계 20건/호출, 2단계 20건/호출 → 비용 최적화
  - 자격 판정 근거: 팀 프로필의 `certifications`, `business_registration_type`, `employee_count`, `founded_year`, `past_projects` 활용
  - **자격요건 텍스트 미확보 처리**: `qualification_available = false`인 공고 (첨부파일 전용, 내용 없음) → 자격 판정을 `ambiguous`로 자동 분류하고 "공고 원문 직접 확인 필요" 사유 기록

- `app/models/bid_schemas.py` (신규)
  - `BidAnnouncement`, `TeamProfile`, `SearchPreset` Pydantic 스키마
  - `QualificationResult` — `status: Literal["pass","fail","ambiguous"]`
  - `RecommendationReason` — `category`, `reason`, `strength`
  - `RiskFactor` — `risk`, `level`
  - `BidRecommendation` — 최종 추천 결과 (`recommendation_reasons: list[RecommendationReason]`, min_length=1)

**예상 공수:** ~6h

---

### F-04: 추천 공고 API (routes_bids)

**목표:** 프론트엔드에 추천 공고 목록 제공

**구현 내용:**
- `app/api/routes_bids.py` (신규)
  - `POST /api/bids/fetch` — 활성 검색 조건 프리셋으로 공고 수집 트리거
    - 활성 프리셋의 키워드·금액·잔여일 조건 적용
    - 백그라운드로 실행 (즉시 `{"status":"fetching"}` 반환)
  - `GET /api/bids/recommendations` — 추천 공고 목록 (match_score 내림차순)
    - 쿼리 파라미터: `preset_id` (특정 프리셋 기준), `refresh=true` (재분석)
    - 캐시: Supabase `bid_recommendations` 테이블 (24h TTL)
  - `GET /api/bids/announcements` — 수집된 공고 목록 (필터/페이징)
    - 쿼리 파라미터: `keyword`, `min_budget`, `min_days`, `bid_type`, `agency`
  - `GET /api/bids/{bid_no}` — 공고 상세 (AI 분석 포함)
  - `POST /api/proposals/from-bid/{bid_no}` — 공고 → 제안서 생성 연동

**예상 공수:** ~3h

---

### F-05: 추천 공고 UI (frontend)

**목표:** 추천 공고 목록을 카드 형태로 표시하고 제안서 생성으로 연결

**구현 내용:**
- `frontend/app/bids/page.tsx` — 추천 공고 목록 페이지
  - 상단 배너: 활성 검색 조건 요약 표시 ("키워드: AI, LLM | 최소금액: 1억 | 잔여 5일 이상")
  - 활성 프리셋 전환 드롭다운 (빠른 전환)
  - **탭:** "추천 공고" (pass+ambiguous) / "제외된 공고" (fail, 이유 확인용)
  - 추천 공고 탭 카드 항목:
    - 공고명, 발주기관, 사업금액, 마감일 D-day 배지, Match Score 배지
    - **추천 사유 칩 (category 배지):** `high` strength 사유를 카테고리 태그로 최대 3개 표시
      - 예: `⚡ 전문성 일치` `📋 실적 보유` `💰 규모 적합`
    - `recommendation_summary` 1줄 요약 텍스트
    - `ambiguous`인 경우: 주황색 "자격 확인 필요" 배지 + 불명확 사유 툴팁
  - 제외된 공고 탭: 제외 이유와 함께 목록 표시 (재검토 여지 제공)
  - "공고 수집" 버튼 → 활성 프리셋 조건으로 나라장터 수집 트리거
- `frontend/app/bids/[bidNo]/page.tsx` — 공고 상세
  - 공고 원문 내용
  - **AI 분석 결과 섹션:**
    - Match Score 게이지 + 등급 (A/B/C...)
    - `recommendation_summary` 요약문 (굵게 표시)
    - **추천 사유 목록:** `recommendation_reasons` 전체 표시
      - 카테고리 아이콘 + 사유 텍스트 + strength 강도 바
    - 리스크 요인: `risk_factors` 목록 (level별 색상)
    - 자격 판정 결과 (ambiguous일 경우 경고 박스)
  - "이 공고로 제안서 만들기" CTA 버튼
- `frontend/app/bids/settings/page.tsx` — 팀 프로필 + 검색 조건 설정 (F-02 참조)
- 네비게이션: 기존 proposals 메뉴 옆에 "공고 추천" 메뉴 추가

**예상 공수:** ~6h

---

### F-06: DB 스키마 추가

**목표:** 공고 수집·추천 결과 영구 저장

```sql
-- 입찰 공고 원문 (전역 캐시 — 팀 구분 없음)
CREATE TABLE bid_announcements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  bid_no TEXT UNIQUE NOT NULL,          -- 입찰공고번호
  bid_title TEXT NOT NULL,              -- 공고명
  agency TEXT NOT NULL,                 -- 발주기관
  bid_type TEXT,                        -- 공고종류 (용역/공사/물품)
  budget_amount BIGINT,                 -- 추정가격 (원)
  announce_date DATE,                   -- 공고일
  deadline_date TIMESTAMPTZ,            -- 입찰마감일시
  days_remaining INTEGER,               -- 수집 시점 잔여일 (계산값)
  content_text TEXT,                    -- 공고 상세내용 (규격서 등, 자격요건 포함)
  qualification_available BOOLEAN DEFAULT true, -- 자격요건 텍스트 확보 여부
  raw_data JSONB,                       -- API 원본 응답
  fetched_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);
-- 만료 공고 정리: deadline_date < now() - interval '7 days' 건 주기적 삭제 (pg_cron 또는 앱 레벨)

-- 팀 입찰 프로필 (AI 매칭·자격 판정용, 팀 단위 소유)
CREATE TABLE team_bid_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  expertise_areas TEXT[],               -- 전문분야
  tech_keywords TEXT[],                 -- 보유기술 키워드
  past_projects TEXT,                   -- 수행실적 요약
  company_size TEXT,                    -- 개인/소기업/중기업/대기업
  certifications TEXT[],                -- 보유 인증·자격
  business_registration_type TEXT,      -- 개인/법인/중소기업/중견기업
  employee_count INTEGER,               -- 임직원 수
  founded_year INTEGER,                 -- 설립연도
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(team_id)                       -- 팀당 프로필 1개
);

-- 검색 조건 프리셋 (나라장터 필터용, 팀 단위 소유)
CREATE TABLE search_presets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  name TEXT NOT NULL,                   -- 프리셋명
  keywords TEXT[] NOT NULL,             -- 관심 키워드 배열
  min_budget BIGINT DEFAULT 100000000,  -- 최소 사업금액 (기본: 1억)
  min_days_remaining INTEGER DEFAULT 5, -- 최소 잔여일 (기본: 5일)
  bid_types TEXT[] DEFAULT '{용역}',    -- 공고종류 필터
  preferred_agencies TEXT[],            -- 선호 발주기관 (비어있으면 전체)
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
-- 팀당 활성 프리셋 1개 제약
CREATE UNIQUE INDEX idx_search_presets_active
  ON search_presets(team_id) WHERE is_active = true;

-- AI 분석 결과 캐시 (팀 + 공고 + 프리셋 단위)
CREATE TABLE bid_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  bid_no TEXT REFERENCES bid_announcements(bid_no),
  preset_id UUID REFERENCES search_presets(id),

  -- 1단계: 자격 판정
  qualification_status TEXT NOT NULL,   -- 'pass' | 'fail' | 'ambiguous'
  disqualification_reason TEXT,         -- fail일 때 제외 이유
  qualification_notes TEXT,             -- ambiguous일 때 불명확 사유

  -- 2단계: 매칭 점수 (qualification_status = 'fail'이면 NULL)
  match_score INTEGER,                  -- 0~100
  match_grade TEXT,                     -- S/A/B/C/D
  recommendation_summary TEXT,          -- 1줄 추천 요약 (필수)
  recommendation_reasons JSONB,         -- [{category, reason, strength}] (1개 이상 필수)
  risk_factors JSONB,                   -- [{risk, level}]
  win_probability_hint TEXT,
  recommended_action TEXT,

  analyzed_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ,               -- 24h TTL
  UNIQUE(team_id, bid_no, preset_id)
);
```

**예상 공수:** ~1h

---

## 기술 결정

### 기존 G2BService 재사용 전략
- `g2b_service.py`의 `G2BService`가 이미 구현되어 있음 → **새 코드 중복 금지**
- `BidFetcher`는 `G2BService`의 래퍼로만 동작:
  - 공고 목록 수집: `G2BService.search_bid_announcements(keyword)` 재사용
  - 공고 상세 수집: `G2BService._call_api("BidPublicInfoService04/getBidPblancDetailInfoServc", ...)` 추가
  - Rate Limit, Retry, 캐싱 로직은 `G2BService` 내부에 이미 구현됨 → 재구현 불필요
- 기존 `g2b_cache` 테이블 캐시도 자동 활용됨

### 나라장터 API 파라미터 전략
- `min_budget`, `min_days_remaining`은 나라장터 API가 **직접 지원하지 않음** → 응답 후 후처리 필터
- `keywords`: API의 `bidNtceNm` 파라미터로 키워드별 별도 호출 후 합산 (중복 제거)
- `bid_types`: API 응답의 `bidClsfcNm` 필드로 후처리 필터 (API 파라미터 불안정)
- API 일일 호출량 관리: 키워드 5개 × 100건 = 500건/수집 → 일 2회 수집 시 1,000건 한도 초과 위험
  - **대응**: 기본값 키워드 최대 3개, 수집 주기 1회/일 권장, 필요 시 API 쿼터 증량 신청

### Claude 매칭 비용 최적화
- 20건 배치 → 단일 호출 (vs 건당 호출 대비 90% 비용 절감)
- 캐시 TTL 24h — 동일 공고 재분석 방지
- 프로필 변경 시에만 캐시 무효화

### 제안서 연동 방식
- 공고 상세 페이지 → "제안서 만들기" 클릭
- `bid_no` 기반으로 공고 원문(`content_text`)을 RFP 대신 사용
- 기존 `POST /api/proposals/generate` 재사용 (content 필드에 공고 내용 주입)

### API 역할 분담 (기존 routes_g2b.py와 구분)
| 라우터 | 용도 | 주요 엔드포인트 |
|--------|------|----------------|
| `routes_g2b.py` (기존) | 경쟁사 분석, 낙찰이력 조회 (제안서 생성 파이프라인용) | `/api/g2b/*` |
| `routes_bids.py` (신규) | 팀 공고 추천, 수집, 매칭 분석 | `/api/teams/{id}/bids/*` |

### 자격요건 판단 한계 및 대응
| 공고 유형 | 자격요건 접근성 | 처리 방식 |
|-----------|---------------|----------|
| 상세 API에 텍스트 있음 | 분석 가능 | 정상 판정 |
| "첨부파일 참조" 문구만 있음 | 분석 불가 | `ambiguous` + "원문 확인 필요" |
| 상세 API 응답 없음 | 분석 불가 | `ambiguous` + "상세 정보 미제공" |

---

## 우선순위 및 구현 순서

| 항목 | 우선순위 | 난이도 | 공수 |
|------|----------|--------|------|
| F-06 DB 스키마 | Critical | Low | ~1h |
| F-02 팀 프로필 + 검색 조건 | High | Low | ~4h |
| F-01 bid_fetcher (G2BService 재사용) | High | Medium | ~5h |
| F-03 AI 분석 엔진 (자격판정+매칭) | High | High | ~6h |
| F-04 추천 공고 API | High | Low | ~3h |
| F-05 추천 공고 UI | Medium | Medium | ~6h |

**구현 순서:** F-06 → F-02 → F-01 → F-03 → F-04 → F-05

총 예상 공수: **~25h**

---

## 성공 기준

- [ ] 검색 조건 프리셋 생성/수정/삭제/전환 가능
- [ ] 수집된 공고에 공사·물품 공고가 포함되지 않음 (용역만 수집)
- [ ] 키워드 기반 나라장터 공고 수집 동작
- [ ] 최소 금액 조건 적용 — 1억 미만 공고가 결과에 포함되지 않음
- [ ] 잔여일 조건 적용 — 5일 미만 마감 공고가 결과에 포함되지 않음
- [ ] 자격 불충족(fail) 공고가 추천 목록에 포함되지 않음
- [ ] 자격 불명확(ambiguous) 공고가 추천 목록에 포함되며 "자격 확인 필요" 배지 표시
- [ ] 제외된 공고 탭에서 fail 공고와 제외 이유 확인 가능
- [ ] 매칭 점수(0~100)와 카테고리별 추천 사유(1개 이상)가 항상 함께 생성됨
- [ ] 추천 카드에 high strength 사유가 카테고리 배지로 표시됨
- [ ] 공고 상세 페이지에서 전체 추천 사유 목록 확인 가능
- [ ] 상위 추천 공고에서 "제안서 만들기"로 바로 진입 가능
- [ ] Gap Analysis >= 90%

---

## 비범위

- 실시간 공고 알림 (이메일/슬랙 Push) — 후속 기능
- 나라장터 외 다른 공고 플랫폼 (e.g. 기업마당, K-Startup) — 후속 기능
- 공고 자동 응찰 — 비범위
- 경쟁업체 분석 — 후속 기능

---

## 환경 변수 추가 필요

```env
DATA_GO_KR_API_KEY=...   # 공공데이터포털 API 인증키
```
