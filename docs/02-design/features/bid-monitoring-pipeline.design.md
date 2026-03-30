# 공고 모니터링 백그라운드 파이프라인 — 상세 설계

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-03-25 |
| Plan 참조 | docs/01-plan/features/bid-monitoring-pipeline.plan.md (v1.0) |

---

## 1. 아키텍처 개요

```
┌──────────────────────────────────────────────────────────────┐
│                     Trigger Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ /bids/crawl  │  │ scheduled_   │  │ /bids/pipeline/   │   │
│  │ (수동 새로고침)│  │ monitor.py   │  │ trigger (수동)     │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘   │
│         └────────────┬────┘───────────────────┘              │
│                      ▼                                        │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              bid_pipeline.py                          │    │
│  │                                                      │    │
│  │  run_pipeline(bid_nos, raw_bids)                     │    │
│  │    ├─ Step 1: ensure_bid_in_db()                     │    │
│  │    ├─ Step 2: download_and_store_attachments()       │    │
│  │    ├─ Step 3: extract_content_text()                 │    │
│  │    └─ Step 4: run_analysis_if_needed()               │    │
│  │                                                      │    │
│  │  concurrency: asyncio.Semaphore(5)                   │    │
│  │  retry: max 2, backoff 5s                            │    │
│  └──────────────────────────────────────────────────────┘    │
│         │              │              │                       │
│         ▼              ▼              ▼                       │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐             │
│  │ Supabase  │  │ Supabase  │  │ File Cache   │             │
│  │ DB        │  │ Storage   │  │ data/bid_    │             │
│  │           │  │ bid-      │  │ analyses/    │             │
│  │ bid_      │  │ attachments│ │ {bid_no}.json│             │
│  │ announce- │  │ /{bid_no}/│  └──────────────┘             │
│  │ ments     │  │ *.hwp/pdf │                                │
│  └───────────┘  └───────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 신규 파일

| 파일 | 역할 |
|------|------|
| `app/services/bid_pipeline.py` | 파이프라인 오케스트레이터 (Step 1~4) |
| `app/services/bid_attachment_store.py` | 첨부파일 다운로드 + Storage 저장 + 텍스트 추출 |

## 3. 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/api/routes_bids.py` | `/bids/crawl` 응답 후 파이프라인 트리거, `/bids/pipeline/status` 엔드포인트 추가 |
| `app/services/scheduled_monitor.py` | 모니터링 완료 후 파이프라인 트리거 호출 |
| `frontend/app/(app)/bids/[bidNo]/review/page.tsx` | 분석 진행 상태 폴링 표시 |

---

## 4. 상세 설계

### 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터

```python
# app/services/bid_pipeline.py
"""
공고 모니터링 백그라운드 파이프라인.

scored/crawl 결과 → DB 저장 → 첨부파일 다운로드 → 텍스트 추출 → AI 분석.
FastAPI BackgroundTasks 또는 직접 asyncio.create_task()로 실행.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# 동시 처리 제한 (G2B rate limit + Claude API 보호)
_SEMAPHORE = asyncio.Semaphore(5)

# 파이프라인 진행 상태 (인메모리 — 서버 재시작 시 초기화)
_pipeline_status: dict[str, dict] = {}
# 예: {"R26BK01412381": {"step": "analysis", "progress": "2/4", "started_at": "...", "error": null}}


async def run_pipeline(
    bid_nos: list[str],
    raw_bids: dict[str, dict] | None = None,
    score_threshold: int = 80,
):
    """
    메인 진입점. 백그라운드에서 호출.

    Args:
        bid_nos: 처리할 공고번호 목록
        raw_bids: {bid_no: G2B raw_data} — crawl에서 이미 가져온 데이터 재사용
        score_threshold: AI 분석 실행 최소 점수 (기본 80)
    """
    logger.info(f"[Pipeline] 시작: {len(bid_nos)}건")

    tasks = [
        _process_single(bid_no, raw_bids.get(bid_no) if raw_bids else None, score_threshold)
        for bid_no in bid_nos
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    failed = len(results) - success
    logger.info(f"[Pipeline] 완료: 성공 {success}, 실패 {failed}")


async def _process_single(
    bid_no: str,
    raw_data: dict | None,
    score_threshold: int,
) -> bool:
    """단일 공고 파이프라인 (Semaphore 제한)."""
    async with _SEMAPHORE:
        _pipeline_status[bid_no] = {
            "step": "db_save",
            "progress": "1/4",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
        try:
            # Step 1: DB 저장
            await _ensure_bid_in_db(bid_no, raw_data)
            _pipeline_status[bid_no]["step"] = "attachment"
            _pipeline_status[bid_no]["progress"] = "2/4"

            # Step 2: 첨부파일 다운로드 + 텍스트 추출
            await _download_and_extract(bid_no)
            _pipeline_status[bid_no]["step"] = "analysis"
            _pipeline_status[bid_no]["progress"] = "3/4"

            # Step 3: AI 분석 (캐시 없는 경우만)
            await _run_analysis_if_needed(bid_no)
            _pipeline_status[bid_no]["step"] = "done"
            _pipeline_status[bid_no]["progress"] = "4/4"

            return True
        except Exception as e:
            logger.warning(f"[Pipeline][{bid_no}] 실패: {e}")
            _pipeline_status[bid_no]["error"] = str(e)
            return False
        finally:
            # 30분 후 상태 자동 삭제 (메모리 관리)
            asyncio.get_event_loop().call_later(
                1800, lambda: _pipeline_status.pop(bid_no, None)
            )


def get_pipeline_status(bid_no: str) -> dict | None:
    """프론트엔드 폴링용 상태 조회."""
    return _pipeline_status.get(bid_no)


def get_all_pipeline_status() -> dict:
    """전체 파이프라인 진행 상태."""
    return dict(_pipeline_status)
```

#### Step 1: `_ensure_bid_in_db()`

```python
async def _ensure_bid_in_db(bid_no: str, raw_data: dict | None = None):
    """
    bid_announcements 테이블에 해당 공고가 있는지 확인.
    없으면 raw_data(crawl에서 전달) 또는 G2B API로 가져와서 upsert.
    """
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # 이미 존재하면 스킵
    res = await (
        client.table("bid_announcements")
        .select("bid_no, content_text")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    if res and res.data:
        return  # 이미 DB에 있음

    # raw_data가 없으면 G2B에서 조회
    if not raw_data:
        from app.services.g2b_service import G2BService
        async with G2BService() as g2b:
            raw_data = await g2b.get_bid_detail(bid_no)
        if not raw_data:
            raise ValueError(f"G2B에서 공고 조회 실패: {bid_no}")

    # DB upsert
    row = {
        "bid_no": bid_no,
        "bid_title": raw_data.get("bidNtceNm", ""),
        "agency": raw_data.get("dminsttNm", "") or raw_data.get("ntceInsttNm", ""),
        "budget_amount": _safe_int(raw_data.get("presmptPrce")),
        "deadline_date": raw_data.get("bidClseDt", "")[:10] or None,
        "raw_data": raw_data,
        "content_text": "",  # Step 2에서 채움
    }
    await client.table("bid_announcements").upsert(row, on_conflict="bid_no").execute()
    logger.info(f"[Pipeline][{bid_no}] DB 저장 완료")


def _safe_int(val) -> int | None:
    try:
        return int(float(val)) if val else None
    except (ValueError, TypeError):
        return None
```

#### Step 2: `_download_and_extract()`

```python
async def _download_and_extract(bid_no: str):
    """
    첨부파일 다운로드 → 로컬 캐시 저장 → 텍스트 추출 → content_text DB 업데이트.
    """
    from app.utils.supabase_client import get_async_client
    from app.services.bid_attachment_store import download_bid_attachments

    client = await get_async_client()

    # DB에서 raw_data 가져오기
    res = await (
        client.table("bid_announcements")
        .select("raw_data, content_text")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    if not res or not res.data:
        return

    # content_text가 이미 있으면 스킵
    if res.data.get("content_text") and len(res.data["content_text"].strip()) > 200:
        logger.info(f"[Pipeline][{bid_no}] content_text 이미 존재 — 스킵")
        return

    raw = res.data.get("raw_data") or {}

    # 첨부파일 다운로드 + 텍스트 추출
    content_text = await download_bid_attachments(bid_no, raw)

    if content_text and len(content_text.strip()) > 100:
        await (
            client.table("bid_announcements")
            .update({"content_text": content_text})
            .eq("bid_no", bid_no)
            .execute()
        )
        logger.info(f"[Pipeline][{bid_no}] content_text 저장 ({len(content_text)}자)")
```

#### Step 3: `_run_analysis_if_needed()`

```python
async def _run_analysis_if_needed(bid_no: str):
    """
    파일 캐시(data/bid_analyses/{bid_no}.json)가 없으면 AI 분석 실행.
    기존 /bids/{bid_no}/analysis API의 로직을 재사용.
    """
    import json as _json

    cache_file = Path("data/bid_analyses") / f"{bid_no}.json"
    if cache_file.exists():
        logger.info(f"[Pipeline][{bid_no}] 분석 캐시 존재 — 스킵")
        return

    # 내부적으로 analysis API와 동일한 로직 호출
    from app.utils.supabase_client import get_async_client
    from app.services.rfp_parser import parse_rfp_from_url

    client = await get_async_client()
    res = await (
        client.table("bid_announcements")
        .select("bid_title, agency, budget_amount, content_text, raw_data")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    if not res or not res.data:
        return

    bid = res.data
    content = bid.get("content_text") or ""

    if len(content.strip()) < 50:
        logger.info(f"[Pipeline][{bid_no}] content_text 부족 — AI 분석 스킵")
        return

    # Stage 1: 전처리
    from app.models.bid_schemas import BidAnnouncement
    from app.services.bid_preprocessor import BidPreprocessor

    bid_ann = BidAnnouncement(
        bid_no=bid_no,
        bid_title=bid.get("bid_title", ""),
        agency=bid.get("agency", ""),
        budget_amount=bid.get("budget_amount"),
        content_text=content,
    )

    preprocessor = BidPreprocessor()
    summary = await preprocessor.preprocess(bid_ann)

    rfp_sections = []
    rfp_summary = []
    rfp_period = ""
    if summary:
        rfp_period = summary.period or ""
        if summary.purpose:
            rfp_sections.append({"label": "목적", "value": summary.purpose})
            rfp_summary.append(f"목적: {summary.purpose}")
        if summary.core_tasks:
            rfp_sections.append({"label": "주요 과업", "items": summary.core_tasks})
            for t in summary.core_tasks:
                rfp_summary.append(f"과업: {t}")

    # Stage 2: TENOPA 적합성 평가
    from app.services.bid_recommender import BidRecommender

    recommender = BidRecommender()
    review = await recommender.review_single(bid_ann)

    # 결과 조합
    result = {
        "rfp_summary": rfp_summary or ["텍스트 추출 불가"],
        "rfp_sections": rfp_sections,
        "rfp_period": rfp_period,
        "fit_level": review.fit_level if review else "보통",
        "positive": review.positive if review else [],
        "negative": review.negative if review else [],
        "recommended_teams": review.recommended_teams if review else [],
        "suitability_score": review.suitability_score if review else None,
        "verdict": review.verdict if review else None,
        "action_plan": review.action_plan if review else None,
    }

    # 파일 캐시 저장
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(_json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"[Pipeline][{bid_no}] AI 분석 완료 + 캐시 저장")
```

---

### 4-2. `bid_attachment_store.py` — 첨부파일 다운로드/저장

```python
# app/services/bid_attachment_store.py
"""
G2B 공고 첨부파일 다운로드 + 로컬 캐시 + 텍스트 추출.

Storage 전략:
- 로컬: data/bid_attachments/{bid_no}/{파일명}
- 텍스트: 추출 후 content_text로 반환
- 보존기간: 로컬 캐시, 서버 재시작 시에도 유지
"""

import asyncio
import logging
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)

ATTACHMENT_DIR = Path("data/bid_attachments")
SUPPORTED_EXTS = {"pdf", "hwp", "hwpx", "docx"}
MAX_FILES = 3  # 최대 다운로드 파일 수
DOWNLOAD_TIMEOUT = 30  # 초


def _classify_priority(name: str) -> int:
    """파일 우선순위: 제안요청서(0) > 과업지시서(1) > 공고문(2) > 기타(3)"""
    lower = name.lower()
    if "제안요청" in lower or "rfp" in lower:
        return 0
    if "과업지시" in lower or "과업내용" in lower:
        return 1
    if "공고" in lower or "입찰" in lower:
        return 2
    return 3


async def download_bid_attachments(bid_no: str, raw_data: dict) -> str:
    """
    공고 첨부파일을 다운로드하고 텍스트를 추출합니다.

    Args:
        bid_no: 공고번호
        raw_data: G2B raw_data (ntceSpecDocUrl1~10, ntceSpecFileNm1~10)

    Returns:
        추출된 텍스트 (모든 파일 합산)
    """
    # 1. 첨부파일 목록 수집
    attachments = []
    for i in range(1, 11):
        url = raw_data.get(f"ntceSpecDocUrl{i}")
        name = raw_data.get(f"ntceSpecFileNm{i}", "")
        if url and name:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in SUPPORTED_EXTS:
                attachments.append({"url": url, "name": name, "ext": ext})

    if not attachments:
        return ""

    # 2. 우선순위 정렬 + 상위 N개만
    attachments.sort(key=lambda a: _classify_priority(a["name"]))
    attachments = attachments[:MAX_FILES]

    # 3. 다운로드 + 텍스트 추출
    bid_dir = ATTACHMENT_DIR / bid_no
    bid_dir.mkdir(parents=True, exist_ok=True)

    extracted_parts = []
    for att in attachments:
        file_path = bid_dir / att["name"]

        # 이미 다운로드되어 있으면 스킵
        if not file_path.exists():
            try:
                await _download_file(att["url"], file_path)
                logger.info(f"[{bid_no}] 다운로드: {att['name']}")
            except Exception as e:
                logger.warning(f"[{bid_no}] 다운로드 실패 {att['name']}: {e}")
                continue

        # 텍스트 추출
        try:
            from app.services.rfp_parser import parse_rfp
            rfp_data = await parse_rfp(file_path)
            if rfp_data and rfp_data.raw_text and len(rfp_data.raw_text.strip()) > 100:
                extracted_parts.append(rfp_data.raw_text)
        except Exception as e:
            logger.warning(f"[{bid_no}] 텍스트 추출 실패 {att['name']}: {e}")

    return "\n\n---\n\n".join(extracted_parts)


async def _download_file(url: str, dest: Path):
    """G2B URL에서 파일 다운로드 (SSRF 방지 포함)."""
    from app.services.rfp_parser import _validate_url
    _validate_url(url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            content = await resp.read()
            dest.write_bytes(content)
```

---

### 4-3. API 변경 — `routes_bids.py`

#### 4-3-1. `/bids/crawl` 후 파이프라인 자동 트리거

```python
# routes_bids.py — manual_crawl 함수 수정

@router.post("/api/bids/crawl")
async def manual_crawl(
    background_tasks: BackgroundTasks,  # 추가
    days: int = Query(1, ge=1, le=7),
    current_user=Depends(get_current_user_or_none),
):
    ...
    # 기존 crawl 로직 후:

    # 파이프라인 백그라운드 실행 (상위 scored 공고)
    top_bid_nos = [b["bid_no"] for b in results["data"][:50]]
    raw_map = {b["bid_no"]: b.get("raw_data", {}) for b in results["data"][:50]}

    from app.services.bid_pipeline import run_pipeline
    background_tasks.add_task(run_pipeline, top_bid_nos, raw_map)

    return {
        "status": "ok",
        "total_fetched": results["total_fetched"],
        "scored_count": len(results["data"]),
        "pipeline_queued": len(top_bid_nos),  # 추가
    }
```

#### 4-3-2. `/bids/pipeline/status` — 진행 상태 조회

```python
@router.get("/api/bids/pipeline/status")
async def pipeline_status(
    bid_no: str = Query(default=None),
):
    """파이프라인 진행 상태 조회. bid_no 지정 시 해당 건만, 미지정 시 전체."""
    from app.services.bid_pipeline import get_pipeline_status, get_all_pipeline_status

    if bid_no:
        status = get_pipeline_status(bid_no)
        return {"data": {bid_no: status} if status else {}}
    return {"data": get_all_pipeline_status()}
```

---

### 4-4. `scheduled_monitor.py` 연동

```python
# scheduled_monitor.py — run_scheduled_monitor() 함수 끝에 추가

async def run_scheduled_monitor():
    ...
    # 기존 로직: G2B 수집 → 스코어링 → 알림

    # NEW: 파이프라인 자동 실행 (score >= 100인 공고만)
    pipeline_targets = [b["bid_no"] for b in scored_bids if b.get("score", 0) >= 100]
    if pipeline_targets:
        from app.services.bid_pipeline import run_pipeline
        asyncio.create_task(run_pipeline(pipeline_targets))
        logger.info(f"[Monitor] 파이프라인 큐: {len(pipeline_targets)}건")
```

---

### 4-5. 프론트엔드 — 분석 진행 상태 표시

`review/page.tsx`에서 analysis API 실패 시 파이프라인 상태를 폴링:

```typescript
// analysis 실패 후 fallback 흐름에 추가:

// 파이프라인 진행 중인지 확인
const pipelineRes = await fetch(`${baseUrl}/bids/pipeline/status?bid_no=${bidNo}`);
if (pipelineRes.ok) {
  const pStatus = await pipelineRes.json();
  const st = pStatus.data?.[bidNo];
  if (st && st.step !== "done" && !st.error) {
    // 파이프라인 진행 중 → 5초 간격 폴링
    setAnalyzing(true);  // 스피너 표시 유지
    const poll = setInterval(async () => {
      const r = await fetch(`${baseUrl}/bids/pipeline/status?bid_no=${bidNo}`);
      if (r.ok) {
        const p = await r.json();
        const s = p.data?.[bidNo];
        if (!s || s.step === "done") {
          clearInterval(poll);
          // 분석 완료 → analysis API 재호출
          const aRes = await fetch(`${baseUrl}/bids/${bidNo}/analysis`);
          if (aRes.ok) setAnalysis((await aRes.json()).data);
          setAnalyzing(false);
        }
      }
    }, 5000);
  }
}
```

---

## 5. 데이터 흐름 요약

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  G2B    │───→│ DB 저장  │───→│ 첨부파일  │───→│ AI 분석  │
│  API    │    │          │    │ 다운로드   │    │          │
│         │    │ bid_     │    │ + 텍스트   │    │ Claude   │
│ raw_data│    │ announce │    │ 추출      │    │ x2 호출  │
│         │    │ ments    │    │          │    │          │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                    │               │               │
                    ▼               ▼               ▼
              bid_no, title    content_text     bid_analyses/
              agency, budget   (DB 업데이트)    {bid_no}.json
              raw_data                          (파일 캐시)
              (DB upsert)

사용자 클릭 시:
  /bids/{id}          → DB 조회 (즉시)
  /bids/{id}/analysis → 파일 캐시 조회 (즉시)
```

---

## 6. 에러 처리

| 실패 지점 | 대응 | 재시도 |
|-----------|------|--------|
| G2B API 조회 | raw_data 파라미터 우선 사용 | 2회 (5초 간격) |
| Supabase DB | try/except로 감싸고 다음 Step 진행 | 2회 |
| 첨부파일 다운로드 | 개별 파일 실패 → 다음 파일 시도 | 1회 |
| 텍스트 추출 | 실패 시 content_text 빈 상태 유지 | 없음 |
| Claude API | 실패 시 분석 캐시 미생성 → 다음 트리거 시 재시도 | 없음 (비용) |

---

## 7. 구현 순서 (체크리스트)

- [ ] 7-1. `app/services/bid_attachment_store.py` 신규 생성
- [ ] 7-2. `app/services/bid_pipeline.py` 신규 생성
- [ ] 7-3. `routes_bids.py` — `/bids/crawl` 파이프라인 트리거 추가
- [ ] 7-4. `routes_bids.py` — `/bids/pipeline/status` 엔드포인트 추가
- [ ] 7-5. `scheduled_monitor.py` — 파이프라인 트리거 연동
- [ ] 7-6. `review/page.tsx` — 파이프라인 상태 폴링 + 진행 표시
- [ ] 7-7. 통합 테스트: crawl → pipeline → review 화면 즉시 표시

---

## 8. 제약 조건

| 항목 | 제약 |
|------|------|
| 동시 처리 | Semaphore(5) — G2B rate limit 보호 |
| Claude API | score >= 100인 공고만 분석 (비용 관리) |
| 첨부파일 | 최대 3파일, 지원 형식만 (PDF/HWP/HWPX/DOCX) |
| 캐시 유효기간 | 파일 캐시 무기한, DB content_text 무기한 |
| 파이프라인 상태 | 인메모리 (30분 후 자동 삭제) |
