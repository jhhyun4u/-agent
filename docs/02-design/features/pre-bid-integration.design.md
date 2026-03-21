# 사전규격 + 발주계획 통합 Design

| 항목 | 내용 |
|------|------|
| Feature | pre-bid-integration |
| 버전 | v1.0 |
| 작성일 | 2026-03-21 |
| 상태 | Design |
| Plan 참조 | `docs/01-plan/features/pre-bid-integration.plan.md` |

---

## 1. 데이터 흐름

```
                  ┌─ fetch_all_bids()          → 입찰공고 raw[]
                  │
fetch_bids_scored ├─ fetch_all_pre_specs()     → 사전규격 raw[]
(asyncio.gather)  │
                  └─ fetch_all_procurement_plans() → 발주계획 raw[]
                          │
                          ▼
                  normalize_for_scoring()  ← 3소스 → 공통 필드 dict[]
                          │
                          ▼
                  score_and_rank_bids()    ← 수의시담 제외 + 4단계 스코어링
                          │
                          ▼
                  중복 제거 (bid_no + title 정규화)
                          │
                          ▼
                  API 응답: { data[], sources{}, total_fetched }
```

## 2. G2B API 신규 메서드

### 2-1. `fetch_all_pre_specs()` — 사전규격 전수 수집

**파일**: `app/services/g2b_service.py`

```python
async def fetch_all_pre_specs(
    self,
    date_from: str,   # YYYYMMDDHHMM
    date_to: str,     # YYYYMMDDHHMM
    max_pages: int = 20,
) -> List[Dict]:
```

- `search_pre_bid_specifications()` 기반, **keyword 없이** 전수 조회
- 페이지네이션: `numOfRows=999`, `pageNo=1..max_pages`
- 중복 제거: `bfSpecRgstNo` 기준 dict
- graceful skip: 미신청 → `[]` 반환 + 로그
- `fetch_all_bids()`와 동일한 패턴

### 2-2. `fetch_all_procurement_plans()` — 발주계획 전수 수집

**파일**: `app/services/g2b_service.py`

```python
async def fetch_all_procurement_plans(
    self,
    date_from: str,   # YYYYMMDDHHMM
    date_to: str,     # YYYYMMDDHHMM
    max_pages: int = 10,
) -> List[Dict]:
```

- 엔드포인트: `OrderPlanSttusService/getOrderPlanSttusListThng`
- `SERVICE_PREFIX` 추가: `"OrderPlanSttusService": "ao"`
- 파라미터: `numOfRows=999, pageNo, inqryDiv=1, inqryBgnDt, inqryEndDt`
- 중복 제거: `orderPlanNo` 기준 dict (필드명은 raw 응답 확인 후 조정)
- graceful skip: 미신청 → `[]` 반환 + 로그
- `max_pages=10` — 발주계획은 건수가 적으므로 낮게 설정

### 2-3. SERVICE_PREFIX 변경

```python
SERVICE_PREFIX = {
    "BidPublicInfoService": "ad",
    "ScsbidInfoService": "as",
    "ContractInfoService": "ac",
    "BfSpecRgstInfoService": "",
    "OrderPlanSttusService": "ao",   # ← 추가
}
```

## 3. 스코어러 정규화 어댑터

### 3-1. 정규화 함수

**파일**: `app/services/bid_scorer.py`

`score_bid()`는 입찰공고 필드명(`bidNtceNm`, `bidNtceNo`, `ntceInsttNm` 등)을 직접 참조한다. 사전규격/발주계획의 필드명이 다르므로, **스코어러 진입 전에** 공통 형식으로 변환한다.

```python
def normalize_pre_spec_for_scoring(raw: dict) -> dict:
    """사전규격 raw → 입찰공고 형식으로 필드 매핑."""
    return {
        "bidNtceNo": f"PRE-{(raw.get('bfSpecRgstNo') or raw.get('prcSpcfNo') or '').strip()}",
        "bidNtceNm": (raw.get("bfSpecRgstNm") or raw.get("prcSpcfNm") or "").strip(),
        "ntceInsttNm": (raw.get("orderInsttNm") or raw.get("rlDminsttNm") or "").strip(),
        "presmptPrce": raw.get("asignBdgtAmt") or raw.get("presmptPrce") or "0",
        "bidClseDt": raw.get("bfSpecRgstClseDt") or raw.get("opninRgstClseDt") or "",
        "pubPrcrmntClsfcNm": "",   # 사전규격에 분류 없음 → 0점
        "pubPrcrmntLrgClsfcNm": "",
        "bidMethdNm": "",          # 수의시담 필터 대상 아님
        "_bid_stage": "사전규격",
    }


def normalize_plan_for_scoring(raw: dict) -> dict:
    """발주계획 raw → 입찰공고 형식으로 필드 매핑."""
    # 필드명은 API 실제 응답 확인 후 조정 (예상 필드 기반)
    return {
        "bidNtceNo": f"PLN-{(raw.get('orderPlanNo') or raw.get('bidNtceNo') or '').strip()}",
        "bidNtceNm": (raw.get("orderPlanNm") or raw.get("bidNtceNm") or "").strip(),
        "ntceInsttNm": (raw.get("orderInsttNm") or raw.get("dminsttNm") or "").strip(),
        "presmptPrce": raw.get("asignBdgtAmt") or raw.get("presmptPrce") or "0",
        "bidClseDt": raw.get("orderPlanRegDt") or "",  # 발주 예정일
        "pubPrcrmntClsfcNm": "",
        "pubPrcrmntLrgClsfcNm": "",
        "bidMethdNm": raw.get("cntrctMthdNm") or "",  # 수의시담 제외 대상
        "_bid_stage": "발주계획",
    }
```

### 3-2. 입찰공고 기본 태그

기존 `score_and_rank_bids()`에서 입찰공고 raw에 `_bid_stage`가 없으면 `"입찰공고"`로 기본값 설정:

```python
bid_stage = raw.get("_bid_stage", "입찰공고")
```

### 3-3. BidScore에 `bid_stage` 필드 추가

```python
@dataclass
class BidScore:
    # ... 기존 필드 ...
    bid_stage: str = "입찰공고"   # ← 추가: "입찰공고" | "사전규격" | "발주계획"
```

`score_bid()`에서 `result.bid_stage = raw.get("_bid_stage", "입찰공고")` 설정.

### 3-4. `_normalize_title()` 접두사 확장

```python
_NOISE_PREFIXES = re.compile(
    r"^\s*(\[?긴급\]?|\[?재공고\]?|\(긴급\)|\(재공고\)|\[재공고\]"
    r"|\[정보[,\s]*\d*\]|\[정책[,\s]*\d*\]|\[보안\]"
    r"|\[사전규격\]|\[발주계획\]"   # ← 추가
    r")\s*",
)
```

## 4. 파이프라인 통합

### 4-1. `fetch_bids_scored()` 수정

**파일**: `app/services/bid_fetcher.py`

```python
async def fetch_bids_scored(self, ...) -> dict:
    from app.services.bid_scorer import (
        score_and_rank_bids,
        normalize_pre_spec_for_scoring,
        normalize_plan_for_scoring,
    )

    # 1) 3소스 병렬 수집
    bids_task = self.g2b.fetch_all_bids(date_from, date_to)
    pre_task = self.g2b.fetch_all_pre_specs(date_from, date_to)
    plan_task = self.g2b.fetch_all_procurement_plans(date_from, date_to)

    all_bids, all_pre, all_plans = await asyncio.gather(
        bids_task, pre_task, plan_task,
        return_exceptions=True,
    )

    # 예외 발생 시 빈 리스트로 대체 (graceful skip)
    if isinstance(all_bids, Exception):
        logger.warning(f"입찰공고 수집 실패: {all_bids}")
        all_bids = []
    if isinstance(all_pre, Exception):
        logger.warning(f"사전규격 수집 실패: {all_pre}")
        all_pre = []
    if isinstance(all_plans, Exception):
        logger.warning(f"발주계획 수집 실패: {all_plans}")
        all_plans = []

    # 2) 정규화 + 합산
    combined = list(all_bids)  # 입찰공고는 이미 올바른 형식
    combined.extend(normalize_pre_spec_for_scoring(r) for r in all_pre)
    combined.extend(normalize_plan_for_scoring(r) for r in all_plans)

    total_fetched = len(all_bids) + len(all_pre) + len(all_plans)

    # 3) 스코어링
    scored = score_and_rank_bids(combined, ...)

    # 4) 후처리 + sources 집계
    sources = {"입찰공고": 0, "사전규격": 0, "발주계획": 0}
    results = []
    for bs in scored:
        # ... 기존 필터 + dict 변환 ...
        item["bid_stage"] = bs.bid_stage
        sources[bs.bid_stage] += 1
        results.append(item)

    return {
        "total_fetched": total_fetched,
        "sources": sources,
        "data": results,
    }
```

### 4-2. `asyncio` import 추가

`bid_fetcher.py` 상단에 `import asyncio` 추가.

## 5. API 응답 변경

### 5-1. `routes_bids.py` 응답 구조

**변경 전:**
```json
{
  "date_from": "20260314",
  "date_to": "20260321",
  "total_count": 187,
  "total_fetched": 5728,
  "data": [...]
}
```

**변경 후:**
```json
{
  "date_from": "20260314",
  "date_to": "20260321",
  "total_count": 215,
  "total_fetched": 6840,
  "sources": { "입찰공고": 187, "사전규격": 22, "발주계획": 6 },
  "data": [
    { "bid_no": "20260321001", "bid_stage": "입찰공고", ... },
    { "bid_no": "PRE-20260315002", "bid_stage": "사전규격", ... },
    { "bid_no": "PLN-2026Q1-003", "bid_stage": "발주계획", ... }
  ]
}
```

### 5-2. `routes_bids.py` 코드 변경

```python
data = results["data"]
return {
    "date_from": date_from_str[:8],
    "date_to": date_to_str[:8],
    "total_count": len(data),
    "total_fetched": results["total_fetched"],
    "sources": results.get("sources", {}),
    "data": data,
}
```

## 6. 프론트엔드 변경

### 6-1. 타입 확장

**파일**: `frontend/lib/api.ts`

```typescript
export interface ScoredBid {
  // ... 기존 필드 ...
  bid_stage: "입찰공고" | "사전규격" | "발주계획";  // ← 추가
}

// scored() 반환 타입
{ date_from: string; date_to: string; total_count: number;
  total_fetched: number;
  sources: { 입찰공고: number; 사전규격: number; 발주계획: number };  // ← 추가
  data: ScoredBid[] }
```

### 6-2. 결과 헤더 개선

**파일**: `frontend/app/bids/page.tsx` — `ScoredBidsView`

기존:
```
03/14~03/21 (7일간) · 전수 5,728건 중 187건 추천
```

변경:
```
03/14~03/21 (7일간) · 전수 6,840건 중 215건 추천 (공고 187 · 사전규격 22 · 발주계획 6)
```

- `sources` 상태 변수 추가
- 헤더에 소스별 건수 표시 (0건인 소스는 생략)

### 6-3. 단계 뱃지 컬럼

테이블 `<thead>`에 `단계` 컬럼 추가 (# 다음, 적합도 앞):

```tsx
function StageBadge({ stage }: { stage: string }) {
  const style = {
    "입찰공고": "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]",
    "사전규격": "text-blue-400 bg-blue-950/60 border-blue-900",
    "발주계획": "text-purple-400 bg-purple-950/60 border-purple-900",
  }[stage] || "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]";

  const label = {
    "입찰공고": "공고",
    "사전규격": "사전",
    "발주계획": "계획",
  }[stage] || stage;

  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${style}`}>
      {label}
    </span>
  );
}
```

### 6-4. 단계 필터

필터 바에 체크박스 3개 추가:

```tsx
const [stageFilter, setStageFilter] = useState<Set<string>>(
  new Set(["입찰공고", "사전규격", "발주계획"])
);
```

- 기본: 3개 모두 선택
- 체크 해제 시 해당 단계 숨김 (클라이언트 필터)
- 필터 적용: `bids.filter(b => stageFilter.has(b.bid_stage))`

## 7. 수정 파일 요약

| # | 파일 | 변경 | 라인 추정 |
|---|------|------|----------|
| 1 | `app/services/g2b_service.py` | SERVICE_PREFIX + `fetch_all_pre_specs()` + `fetch_all_procurement_plans()` | +60 |
| 2 | `app/services/bid_scorer.py` | `normalize_*_for_scoring()` x2 + BidScore.bid_stage + _NOISE_PREFIXES 확장 | +45 |
| 3 | `app/services/bid_fetcher.py` | `fetch_bids_scored()` 3소스 병렬 + sources 집계 | +30 (수정) |
| 4 | `app/api/routes_bids.py` | 응답에 `sources` 필드 추가 | +2 |
| 5 | `frontend/lib/api.ts` | `ScoredBid.bid_stage` + 응답 `sources` 타입 | +3 |
| 6 | `frontend/app/bids/page.tsx` | StageBadge + 소스 헤더 + 단계 필터 | +50 |
| **합계** | | | **~190줄** |

## 8. 구현 순서

```
Step 1: g2b_service.py    — fetch_all_pre_specs + fetch_all_procurement_plans
Step 2: bid_scorer.py     — normalize 어댑터 + BidScore.bid_stage + 접두사 확장
Step 3: bid_fetcher.py    — 3소스 병렬 수집 + sources 집계
Step 4: routes_bids.py    — sources 필드 전달
Step 5: api.ts            — 타입 확장
Step 6: bids/page.tsx     — StageBadge + 헤더 + 필터
```

## 9. 검증 항목

| # | 검증 | 기대 결과 |
|---|------|----------|
| V1 | `GET /api/bids/scored?days=7` | `sources` 필드에 3개 소스 건수 |
| V2 | 사전규격 API 미신청 | `sources.사전규격 = 0`, 나머지 정상 |
| V3 | 발주계획 API 미신청 | `sources.발주계획 = 0`, 나머지 정상 |
| V4 | `days=30` 30일 검색 | 3소스 합산, 중복 없음 |
| V5 | 수의시담 발주계획 | `bidMethdNm`에 "수의" → 제외됨 |
| V6 | 사전규격→입찰공고 전환 건 | 제목 유사도 기반 1건만 표시 |
| V7 | 프론트엔드 단계 필터 | 체크 해제 시 해당 단계 숨김 |
| V8 | TypeScript 빌드 | 에러 0건 |
