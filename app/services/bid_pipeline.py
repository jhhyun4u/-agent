"""
공고 모니터링 백그라운드 파이프라인.

scored/crawl 결과 → DB 저장 → 첨부파일 다운로드 → 텍스트 추출 → AI 분석.
FastAPI BackgroundTasks 또는 asyncio.create_task()로 실행.
"""

import asyncio
import json as _json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_SEMAPHORE = asyncio.Semaphore(5)

# 인메모리 파이프라인 상태
_pipeline_status: dict[str, dict] = {}


async def run_pipeline(
    bid_nos: list[str],
    raw_bids: dict[str, dict] | None = None,
):
    """메인 진입점. 백그라운드에서 호출."""
    logger.info(f"[Pipeline] 시작: {len(bid_nos)}건")

    tasks = [
        _process_single(bid_no, raw_bids.get(bid_no) if raw_bids else None)
        for bid_no in bid_nos
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    failed = len(results) - success
    logger.info(f"[Pipeline] 완료: 성공 {success}, 실패 {failed}")


async def _process_single(bid_no: str, raw_data: dict | None) -> bool:
    async with _SEMAPHORE:
        _pipeline_status[bid_no] = {
            "step": "db_save",
            "progress": "1/4",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
        try:
            # 건당 전체 타임아웃 (DB + 첨부 + AI)
            await asyncio.wait_for(_run_all_steps(bid_no, raw_data), timeout=settings.bid_pipeline_timeout_seconds)
            _update_status(bid_no, "done", "4/4")
            return True
        except asyncio.TimeoutError:
            logger.error(f"[Pipeline][{bid_no}] 전체 타임아웃 ({settings.bid_pipeline_timeout_seconds}초)")
            _pipeline_status[bid_no]["error"] = "처리 시간 초과"
            return False
        except Exception as e:
            logger.error(f"[Pipeline][{bid_no}] 실패: {e}")
            _pipeline_status[bid_no]["error"] = str(e)
            return False
        finally:
            loop = asyncio.get_event_loop()
            loop.call_later(1800, lambda: _pipeline_status.pop(bid_no, None))


async def _run_all_steps(bid_no: str, raw_data: dict | None):
    """파이프라인 3단계 순차 실행."""
    # Step 1: DB 저장
    await _ensure_bid_in_db(bid_no, raw_data)
    _update_status(bid_no, "attachment", "2/4")

    # Step 2: 첨부파일 다운로드 + 텍스트 추출
    await _download_and_extract(bid_no)
    _update_status(bid_no, "analysis", "3/4")

    # Step 3: AI 분석 (캐시 없는 경우만)
    await _run_analysis_if_needed(bid_no)


def _update_status(bid_no: str, step: str, progress: str):
    if bid_no in _pipeline_status:
        _pipeline_status[bid_no]["step"] = step
        _pipeline_status[bid_no]["progress"] = progress


def get_pipeline_status(bid_no: str) -> dict | None:
    return _pipeline_status.get(bid_no)


def get_all_pipeline_status() -> dict:
    return dict(_pipeline_status)


# ── Step 1: DB 저장 ──

async def _ensure_bid_in_db(bid_no: str, raw_data: dict | None = None):
    from app.utils.supabase_client import get_async_client

    try:
        client = await get_async_client()
        res = await (
            client.table("bid_announcements")
            .select("bid_no")
            .eq("bid_no", bid_no)
            .maybe_single()
            .execute()
        )
        if res and res.data:
            return
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] DB 조회 실패: {e}")

    if not raw_data:
        from app.services.g2b_service import G2BService
        async with G2BService() as g2b:
            raw_data = await g2b.get_bid_detail(bid_no)
        if not raw_data:
            raise ValueError(f"G2B에서 공고 조회 실패: {bid_no}")

    # content_text 추출: ntceSpecCn > bidNtceDtlCn > specDocCn > bidNtceDtl
    content_text = (
        raw_data.get("ntceSpecCn")
        or raw_data.get("bidNtceDtlCn")
        or raw_data.get("specDocCn")
        or raw_data.get("bidNtceDtl")
        or ""
    )
    row = {
        "bid_no": bid_no,
        "bid_title": raw_data.get("bidNtceNm", ""),
        "agency": raw_data.get("dminsttNm", "") or raw_data.get("ntceInsttNm", ""),
        "budget_amount": _safe_int(raw_data.get("presmptPrce")),
        "deadline_date": raw_data.get("bidClseDt", "")[:10] or None,
        "raw_data": raw_data,
        "content_text": content_text,
    }

    try:
        client = await get_async_client()
        await client.table("bid_announcements").upsert(row, on_conflict="bid_no").execute()
        logger.info(f"[Pipeline][{bid_no}] DB 저장 완료")
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] DB upsert 실패: {e}")


def _safe_int(val) -> int | None:
    try:
        return int(float(val)) if val else None
    except (ValueError, TypeError):
        return None


# ── Step 2: 첨부파일 다운로드 + 텍스트 추출 ──

async def _download_and_extract(bid_no: str):
    from app.utils.supabase_client import get_async_client
    from app.services.bid_attachment_store import download_bid_attachments

    try:
        client = await get_async_client()
        res = await (
            client.table("bid_announcements")
            .select("raw_data, content_text")
            .eq("bid_no", bid_no)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] DB 조회 실패 (Step 2): {e}")
        return

    if not res or not res.data:
        return

    existing_text = res.data.get("content_text") or ""
    if len(existing_text.strip()) > 200:
        logger.info(f"[Pipeline][{bid_no}] content_text 이미 존재 — 스킵")
        return

    raw = res.data.get("raw_data") or {}
    content_text = await download_bid_attachments(bid_no, raw)

    if content_text and len(content_text.strip()) > 100:
        try:
            await (
                client.table("bid_announcements")
                .update({"content_text": content_text})
                .eq("bid_no", bid_no)
                .execute()
            )
            logger.info(f"[Pipeline][{bid_no}] content_text 저장 ({len(content_text)}자)")
        except Exception as e:
            logger.warning(f"[Pipeline][{bid_no}] content_text DB 저장 실패: {e}")


# ── Step 3: AI 분석 ──

async def _run_analysis_if_needed(bid_no: str):
    cache_dir = Path("data/bid_analyses")
    cache_file = cache_dir / f"{bid_no}.json"
    if cache_file.exists():
        logger.info(f"[Pipeline][{bid_no}] 분석 캐시 존재 — 스킵")
        return

    from app.utils.supabase_client import get_async_client

    try:
        client = await get_async_client()
        res = await (
            client.table("bid_announcements")
            .select("bid_title, agency, budget_amount, content_text")
            .eq("bid_no", bid_no)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] DB 조회 실패 (Step 3): {e}")
        return

    if not res or not res.data:
        return

    bid = res.data
    content = bid.get("content_text") or ""

    if len(content.strip()) < 50:
        logger.info(f"[Pipeline][{bid_no}] content_text 부족 — AI 분석 스킵")
        return

    from app.models.bid_schemas import BidAnnouncement
    from app.services.bidding.monitor.preprocessor import BidPreprocessor
    from app.services.bidding.monitor.recommender import BidRecommender

    bid_ann = BidAnnouncement(
        bid_no=bid_no,
        bid_title=bid.get("bid_title", ""),
        agency=bid.get("agency", ""),
        budget_amount=bid.get("budget_amount"),
        content_text=content,
    )

    # Stage 1: 전처리
    preprocessor = BidPreprocessor()
    summary = None
    try:
        summary = await preprocessor.preprocess(bid_ann)
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] 전처리 실패: {e}")

    rfp_sections: list[dict] = []
    rfp_summary: list[str] = []
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
    review = None
    try:
        recommender = BidRecommender()
        review = await recommender.review_single(bid_ann)
    except Exception as e:
        logger.warning(f"[Pipeline][{bid_no}] 적합성 평가 실패: {e}")

    # TenopaBidReview → 프론트엔드 포맷 변환
    if review:
        score = review.suitability_score
        if score >= 80:
            fit_level = "적극 추천"
        elif score >= 70:
            fit_level = "추천"
        elif score >= 40:
            fit_level = "보통"
        else:
            fit_level = "낮음"
        positive = review.reason_analysis.strengths
        negative = review.reason_analysis.risks
    else:
        score = 0
        fit_level = "보통"
        positive = []
        negative = ["AI 분석을 수행할 수 없습니다."]

    result = {
        "rfp_summary": rfp_summary or ["텍스트 추출 불가"],
        "rfp_sections": rfp_sections,
        "rfp_period": rfp_period,
        "fit_level": fit_level,
        "positive": positive,
        "negative": negative,
        "recommended_teams": [],
        "suitability_score": score if review else None,
        "verdict": review.verdict if review else None,
        "action_plan": review.action_plan if review else None,
    }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        _json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"[Pipeline][{bid_no}] AI 분석 완료 + 캐시 저장")
