"""
입찰 추천 API

팀 프로필 관리, 검색 프리셋 CRUD, 공고 수집 트리거, AI 추천 목록 제공.
모든 엔드포인트는 Bearer JWT 인증 필수.

API 경로: /api/teams/{team_id}/bid-profile, /api/teams/{team_id}/search-presets,
          /api/teams/{team_id}/bids/*, /api/bids/{bid_no}
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.middleware.auth import get_current_user
from app.models.bid_schemas import (
    BidAnnouncement,
    BidRecommendation,
    ExcludedBid,
    QualificationResult,
    RecommendedBid,
    SearchPreset,
    SearchPresetCreate,
    TeamBidProfile,
    TeamBidProfileCreate,
)
from app.services.bid_fetcher import BidFetcher
from app.services.bid_recommender import BidRecommender
from app.services.g2b_service import G2BService
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bids"])

_BID_NO_PATTERN = re.compile(r'^[\d\-]+$')
_FETCH_COOLDOWN_HOURS = 1


# ── 권한 헬퍼 ────────────────────────────────────────────────

async def _require_team_member(client, team_id: str, user_id: str):
    res = (
        await client.table("team_members")
        .select("role")
        .eq("team_id", team_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=403, detail="팀 멤버만 접근 가능합니다.")
    return res.data["role"]


# ── F-02: 팀 프로필 ──────────────────────────────────────────

@router.get("/api/teams/{team_id}/bid-profile")
async def get_bid_profile(
    team_id: str,
    current_user=Depends(get_current_user),
):
    """팀 AI 매칭 프로필 조회"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    res = (
        await client.table("team_bid_profiles")
        .select("*")
        .eq("team_id", team_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return {"data": None}
    return {"data": res.data}


@router.put("/api/teams/{team_id}/bid-profile")
async def upsert_bid_profile(
    team_id: str,
    body: TeamBidProfileCreate,
    current_user=Depends(get_current_user),
):
    """팀 AI 매칭 프로필 생성/수정 (upsert)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "team_id": team_id,
        **body.model_dump(),
        "updated_at": now,
    }

    res = (
        await client.table("team_bid_profiles")
        .upsert(row, on_conflict="team_id")
        .execute()
    )

    # 프로필 변경 시 캐시 무효화 (bid_recommendations expires_at을 과거로 설정)
    await _invalidate_recommendations_cache(client, team_id)

    return {"data": res.data[0] if res.data else row}


# ── F-02: 검색 프리셋 CRUD ───────────────────────────────────

@router.get("/api/teams/{team_id}/search-presets")
async def list_search_presets(
    team_id: str,
    current_user=Depends(get_current_user),
):
    """검색 프리셋 목록 조회"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    res = (
        await client.table("search_presets")
        .select("*")
        .eq("team_id", team_id)
        .order("created_at", desc=False)
        .execute()
    )
    return {"data": res.data or []}


@router.post("/api/teams/{team_id}/search-presets", status_code=201)
async def create_search_preset(
    team_id: str,
    body: SearchPresetCreate,
    current_user=Depends(get_current_user),
):
    """검색 프리셋 생성"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "team_id": team_id,
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }

    res = await client.table("search_presets").insert(row).execute()
    return {"data": res.data[0]}


@router.put("/api/teams/{team_id}/search-presets/{preset_id}")
async def update_search_preset(
    team_id: str,
    preset_id: str,
    body: SearchPresetCreate,
    current_user=Depends(get_current_user),
):
    """검색 프리셋 수정"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    await _get_preset_or_404(client, team_id, preset_id)

    res = (
        await client.table("search_presets")
        .update({**body.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .execute()
    )
    return {"data": res.data[0]}


@router.delete("/api/teams/{team_id}/search-presets/{preset_id}", status_code=204)
async def delete_search_preset(
    team_id: str,
    preset_id: str,
    current_user=Depends(get_current_user),
):
    """검색 프리셋 삭제"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    await _get_preset_or_404(client, team_id, preset_id)

    await (
        client.table("search_presets")
        .delete()
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .execute()
    )


@router.post("/api/teams/{team_id}/search-presets/{preset_id}/activate")
async def activate_search_preset(
    team_id: str,
    preset_id: str,
    current_user=Depends(get_current_user),
):
    """활성 프리셋 전환 (팀당 1개 보장)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    await _get_preset_or_404(client, team_id, preset_id)

    # 기존 활성 프리셋 비활성화
    await (
        client.table("search_presets")
        .update({"is_active": False})
        .eq("team_id", team_id)
        .eq("is_active", True)
        .execute()
    )

    # 지정 프리셋 활성화
    res = (
        await client.table("search_presets")
        .update({"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", preset_id)
        .execute()
    )
    return {"data": res.data[0]}


# ── F-04: 공고 수집 트리거 ───────────────────────────────────

@router.post("/api/teams/{team_id}/bids/fetch")
async def trigger_fetch(
    team_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """활성 프리셋 기준 공고 수집 트리거 (백그라운드 실행)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    preset = await _get_active_preset_or_422(client, team_id)

    # Rate Limit: 1시간 이내 재수집 방지
    if preset.get("last_fetched_at"):
        last = datetime.fromisoformat(preset["last_fetched_at"])
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(timezone.utc) - last
        if elapsed < timedelta(hours=_FETCH_COOLDOWN_HOURS):
            remaining_min = int((_FETCH_COOLDOWN_HOURS * 60) - elapsed.total_seconds() / 60)
            raise HTTPException(
                status_code=429,
                detail=f"마지막 수집: {int(elapsed.total_seconds()/60)}분 전. "
                       f"{remaining_min}분 후 다시 시도하세요.",
            )

    # last_fetched_at 업데이트 (즉시)
    await (
        client.table("search_presets")
        .update({"last_fetched_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", preset["id"])
        .execute()
    )

    # 팀 프로필 조회
    profile_res = (
        await client.table("team_bid_profiles")
        .select("*")
        .eq("team_id", team_id)
        .maybe_single()
        .execute()
    )
    profile_data = profile_res.data or {}

    preset_obj = SearchPreset(
        id=preset["id"],
        team_id=team_id,
        name=preset["name"],
        keywords=preset["keywords"],
        min_budget=preset["min_budget"],
        min_days_remaining=preset["min_days_remaining"],
        bid_types=preset["bid_types"],
        preferred_agencies=preset.get("preferred_agencies") or [],
    )
    profile_obj = TeamBidProfile(team_id=team_id, **{
        k: v for k, v in profile_data.items()
        if k in TeamBidProfile.model_fields
    })

    background_tasks.add_task(
        _run_fetch_and_analyze, team_id, preset_obj, profile_obj
    )

    return {"status": "fetching", "message": "공고 수집을 시작합니다."}


# ── F-04: 추천 공고 목록 ─────────────────────────────────────

@router.get("/api/teams/{team_id}/bids/recommendations")
async def get_recommendations(
    team_id: str,
    refresh: bool = Query(default=False),
    current_user=Depends(get_current_user),
):
    """추천 공고 목록 (캐시 우선, match_score 내림차순)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    preset = await _get_active_preset_or_422(client, team_id)
    await _get_profile_or_422(client, team_id)

    now = datetime.now(timezone.utc)

    # 캐시 확인 (refresh=False이고 만료되지 않은 경우)
    if not refresh:
        cached = await _get_cached_recommendations(client, team_id, preset["id"], now)
        if cached is not None:
            return cached

    # 캐시 없거나 refresh=True → bid_recommendations 테이블에서 최신 분석 결과 반환
    # (수집+분석은 trigger_fetch가 백그라운드로 실행)
    return await _build_recommendations_response(client, team_id, preset["id"])


@router.get("/api/teams/{team_id}/bids/announcements")
async def list_announcements(
    team_id: str,
    keyword: Optional[str] = Query(default=None),
    min_budget: Optional[int] = Query(default=None, ge=0),
    min_days: Optional[int] = Query(default=None, ge=0),
    bid_type: Optional[str] = Query(default=None),
    agency: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """수집된 공고 목록 (필터/페이징)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user["id"])

    query = client.table("bid_announcements").select("*", count="exact")

    if keyword:
        query = query.ilike("bid_title", f"%{keyword}%")
    if min_budget is not None:
        query = query.gte("budget_amount", min_budget)
    if bid_type:
        query = query.eq("bid_type", bid_type)
    if agency:
        query = query.ilike("agency", f"%{agency}%")
    if min_days is not None:
        query = query.gte("days_remaining", min_days)

    offset = (page - 1) * per_page
    res = (
        await query
        .order("deadline_date", desc=False)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return {
        "data": res.data or [],
        "meta": {
            "total": res.count or 0,
            "page": page,
            "per_page": per_page,
        },
    }


@router.get("/api/bids/{bid_no}")
async def get_bid_detail(
    bid_no: str,
    team_id: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    """공고 상세 + AI 분석 결과"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise HTTPException(status_code=400, detail="유효하지 않은 공고번호 형식입니다.")

    client = await get_async_client()

    res = (
        await client.table("bid_announcements")
        .select("*")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다.")

    result = {"data": {"announcement": res.data, "recommendation": None}}

    # 팀 AI 분석 결과 포함 (team_id 파라미터가 있는 경우)
    if team_id:
        await _require_team_member(client, team_id, current_user["id"])
        rec_res = (
            await client.table("bid_recommendations")
            .select("*")
            .eq("bid_no", bid_no)
            .eq("team_id", team_id)
            .order("analyzed_at", desc=True)
            .limit(1)
            .execute()
        )
        if rec_res.data:
            result["data"]["recommendation"] = rec_res.data[0]

    return result


# ── F-04: 제안서 연동 ────────────────────────────────────────

@router.post("/api/proposals/from-bid/{bid_no}", status_code=201)
async def create_proposal_from_bid(
    bid_no: str,
    current_user=Depends(get_current_user),
):
    """공고 → 제안서 생성 (bid 원문을 RFP 내용으로 주입)"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise HTTPException(status_code=400, detail="유효하지 않은 공고번호 형식입니다.")

    client = await get_async_client()

    res = (
        await client.table("bid_announcements")
        .select("bid_title, content_text, agency, budget_amount")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다.")

    bid = res.data
    rfp_content = bid.get("content_text") or f"{bid['bid_title']} ({bid['agency']})"

    # 기존 제안서 생성 플로우에 bid 정보 주입
    # (실제 구현: POST /api/proposals/generate 재사용)
    return {
        "data": {
            "bid_no": bid_no,
            "bid_title": bid["bid_title"],
            "rfp_content": rfp_content,
            "message": "제안서 생성 페이지로 이동하여 내용을 확인하세요.",
        }
    }


# ── 내부 헬퍼 ────────────────────────────────────────────────

async def _invalidate_recommendations_cache(client, team_id: str) -> None:
    """팀 프로필 변경 시 bid_recommendations 캐시 즉시 만료"""
    try:
        past = datetime.now(timezone.utc).isoformat()
        await (
            client.table("bid_recommendations")
            .update({"expires_at": past})
            .eq("team_id", team_id)
            .execute()
        )
    except Exception as e:
        logger.warning(f"캐시 무효화 실패 (무시): {e}")


async def _get_preset_or_404(client, team_id: str, preset_id: str) -> dict:
    res = (
        await client.table("search_presets")
        .select("*")
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다.")
    return res.data


async def _get_active_preset_or_422(client, team_id: str) -> dict:
    res = (
        await client.table("search_presets")
        .select("*")
        .eq("team_id", team_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=422,
            detail="검색 조건 프리셋을 먼저 생성하고 활성화하세요.",
        )
    return res.data


async def _get_profile_or_422(client, team_id: str) -> dict:
    res = (
        await client.table("team_bid_profiles")
        .select("*")
        .eq("team_id", team_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=422,
            detail="팀 프로필을 먼저 설정하세요.",
        )
    return res.data


async def _get_cached_recommendations(
    client, team_id: str, preset_id: str, now: datetime
) -> Optional[dict]:
    """유효한 캐시 결과 반환. 없으면 None."""
    res = (
        await client.table("bid_recommendations")
        .select("expires_at")
        .eq("team_id", team_id)
        .eq("preset_id", preset_id)
        .gt("expires_at", now.isoformat())
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return await _build_recommendations_response(client, team_id, preset_id)


async def _build_recommendations_response(
    client, team_id: str, preset_id: str
) -> dict:
    """bid_recommendations 테이블에서 응답 조립"""
    res = (
        await client.table("bid_recommendations")
        .select("*, bid_announcements(bid_title, agency, budget_amount, deadline_date, days_remaining)")
        .eq("team_id", team_id)
        .eq("preset_id", preset_id)
        .order("match_score", desc=True)
        .execute()
    )

    rows = res.data or []
    recommended = []
    excluded = []
    analyzed_at = None

    for row in rows:
        ann = row.get("bid_announcements") or {}
        if not analyzed_at and row.get("analyzed_at"):
            analyzed_at = row["analyzed_at"]

        if row["qualification_status"] == "fail":
            excluded.append({
                "bid_no": row["bid_no"],
                "bid_title": ann.get("bid_title", ""),
                "agency": ann.get("agency", ""),
                "budget_amount": ann.get("budget_amount"),
                "deadline_date": ann.get("deadline_date"),
                "qualification_status": "fail",
                "disqualification_reason": row.get("disqualification_reason"),
            })
        else:
            recommended.append({
                "bid_no": row["bid_no"],
                "bid_title": ann.get("bid_title", ""),
                "agency": ann.get("agency", ""),
                "budget_amount": ann.get("budget_amount"),
                "deadline_date": ann.get("deadline_date"),
                "days_remaining": ann.get("days_remaining"),
                "qualification_status": row["qualification_status"],
                "qualification_notes": row.get("qualification_notes"),
                "match_score": row.get("match_score"),
                "match_grade": row.get("match_grade"),
                "recommendation_summary": row.get("recommendation_summary"),
                "recommendation_reasons": row.get("recommendation_reasons") or [],
                "risk_factors": row.get("risk_factors") or [],
                "win_probability_hint": row.get("win_probability_hint"),
                "recommended_action": row.get("recommended_action"),
            })

    return {
        "data": {"recommended": recommended, "excluded": excluded},
        "meta": {
            "total_fetched": len(rows),
            "analyzed_at": analyzed_at or datetime.now(timezone.utc).isoformat(),
        },
    }


async def _run_fetch_and_analyze(
    team_id: str,
    preset: SearchPreset,
    profile: TeamBidProfile,
) -> None:
    """백그라운드: 공고 수집 + AI 분석 + DB 저장"""
    try:
        client = await get_async_client()

        async with G2BService() as g2b:
            fetcher = BidFetcher(g2b, client)
            bids = await fetcher.fetch_bids_by_preset(preset)

        if not bids:
            logger.info(f"[팀 {team_id}] 수집된 공고 없음")
            return

        recommender = BidRecommender()
        recommendations, qual_results = await recommender.analyze_bids(profile, bids)

        await _save_recommendations(client, team_id, preset.id, recommendations, qual_results, bids)
        logger.info(f"[팀 {team_id}] 분석 완료: 추천 {len(recommendations)}건")

    except Exception as e:
        logger.error(f"[팀 {team_id}] 수집/분석 실패: {e}")
        # 실패 시 last_fetched_at 초기화 → 사용자가 즉시 재수집 가능 (Rate Limit 해제)
        try:
            client = await get_async_client()
            await (
                client.table("search_presets")
                .update({"last_fetched_at": None})
                .eq("id", preset.id)
                .execute()
            )
        except Exception as reset_err:
            logger.warning(f"[팀 {team_id}] Rate Limit 초기화 실패 (무시): {reset_err}")


async def _save_recommendations(
    client,
    team_id: str,
    preset_id: str,
    recommendations: list[BidRecommendation],
    qual_results: list[QualificationResult],
    bids: list[BidAnnouncement],
) -> None:
    """bid_recommendations 테이블에 분석 결과 저장"""
    rec_map = {r.bid_no: r for r in recommendations}
    qual_map = {q.bid_no: q for q in qual_results}
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(hours=24)).isoformat()

    rows = []
    for bid in bids:
        qual = qual_map.get(bid.bid_no)
        rec = rec_map.get(bid.bid_no)

        if not qual:
            continue

        row = {
            "team_id": team_id,
            "bid_no": bid.bid_no,
            "preset_id": preset_id,
            "qualification_status": qual.qualification_status,
            "disqualification_reason": qual.disqualification_reason,
            "qualification_notes": qual.qualification_notes,
            "analyzed_at": now.isoformat(),
            "expires_at": expires,
        }

        if rec:
            row.update({
                "match_score": rec.match_score,
                "match_grade": rec.match_grade,
                "recommendation_summary": rec.recommendation_summary,
                "recommendation_reasons": [r.model_dump() for r in rec.recommendation_reasons],
                "risk_factors": [r.model_dump() for r in rec.risk_factors],
                "win_probability_hint": rec.win_probability_hint,
                "recommended_action": rec.recommended_action,
            })

        rows.append(row)

    if rows:
        await (
            client.table("bid_recommendations")
            .upsert(rows, on_conflict="team_id,bid_no,preset_id")
            .execute()
        )
