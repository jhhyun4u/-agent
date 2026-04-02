"""
입찰 추천 API

팀 프로필 관리, 검색 프리셋 CRUD, 공고 수집 트리거, AI 추천 목록 제공.
모든 엔드포인트는 Bearer JWT 인증 필수.

API 경로: /api/teams/{team_id}/bid-profile, /api/teams/{team_id}/search-presets,
          /api/teams/{team_id}/bids/*, /api/bids/{bid_no}
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps import get_current_user, get_current_user_or_none
from app.api.permissions import require_team_member as _require_team_member
from app.api.response import ok, ok_list
from app.config import settings
from app.exceptions import (
    BidNotFoundError,
    BidValidationError,
    FileNotFoundError_,
    InternalServiceError,
    InvalidRequestError,
    RateLimitError,
    ResourceNotFoundError,
)
from app.models.auth_schemas import CurrentUser
from app.models.bid_schemas import (
    BidAnnouncement,
    BidRecommendation,
    BidStatusUpdate,
    QualificationResult,
    SearchPreset,
    SearchPresetCreate,
    TeamBidProfile,
    TeamBidProfileCreate,
)
from app.prompts.bid_review import UNIFIED_ANALYSIS_USER, build_unified_analysis_system
from app.services.bid_attachment_store import download_bid_attachments
from app.services.bid_fetcher import BidFetcher
from app.services.bid_pipeline import get_all_pipeline_status, get_pipeline_status, run_pipeline
from app.services.bid_recommender import BidRecommender
from app.services.bid_scorer import score_and_rank_bids
from app.services.claude_client import _get_client as _get_claude_client
from app.services.g2b_service import G2BService
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["bids"])

_BID_NO_PATTERN = re.compile(r'^[A-Za-z0-9\-]+$')
_FETCH_COOLDOWN_HOURS = 1


def _escape_like(value: str) -> str:
    """PostgREST ilike 메타문자(%, _, \\) 이스케이프"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ── F-02: 팀 프로필 ──────────────────────────────────────────

@router.get("/teams/{team_id}/bid-profile")
async def get_bid_profile(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """팀 AI 매칭 프로필 조회"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    res = (
        await client.table("team_bid_profiles")
        .select("*")
        .eq("team_id", team_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return ok(None)
    return ok(res.data)


@router.put("/teams/{team_id}/bid-profile")
async def upsert_bid_profile(
    team_id: str,
    body: TeamBidProfileCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """팀 AI 매칭 프로필 생성/수정 (upsert)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

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

    return ok(res.data[0] if res.data else row)


# ── F-02: 검색 프리셋 CRUD ───────────────────────────────────

@router.get("/teams/{team_id}/search-presets")
async def list_search_presets(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """검색 프리셋 목록 조회"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    res = (
        await client.table("search_presets")
        .select("*")
        .eq("team_id", team_id)
        .order("created_at", desc=False)
        .execute()
    )
    return ok(res.data or [])


@router.post("/teams/{team_id}/search-presets", status_code=201)
async def create_search_preset(
    team_id: str,
    body: SearchPresetCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """검색 프리셋 생성"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "team_id": team_id,
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }

    res = await client.table("search_presets").insert(row).execute()
    return ok(res.data[0])


@router.put("/teams/{team_id}/search-presets/{preset_id}")
async def update_search_preset(
    team_id: str,
    preset_id: str,
    body: SearchPresetCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """검색 프리셋 수정"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    await _get_preset_or_404(client, team_id, preset_id)

    res = (
        await client.table("search_presets")
        .update({**body.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .execute()
    )
    return ok(res.data[0])


@router.delete("/teams/{team_id}/search-presets/{preset_id}", status_code=204)
async def delete_search_preset(
    team_id: str,
    preset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """검색 프리셋 삭제"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    await _get_preset_or_404(client, team_id, preset_id)

    await (
        client.table("search_presets")
        .delete()
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .execute()
    )


@router.post("/teams/{team_id}/search-presets/{preset_id}/activate")
async def activate_search_preset(
    team_id: str,
    preset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """활성 프리셋 전환 (팀당 1개 보장, 활성화 우선 → 비활성화 후행)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    await _get_preset_or_404(client, team_id, preset_id)

    # 1) 지정 프리셋 먼저 활성화 (실패 시 기존 활성 프리셋 유지)
    res = (
        await client.table("search_presets")
        .update({"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", preset_id)
        .eq("team_id", team_id)
        .execute()
    )

    # 2) 이전 활성 프리셋 비활성화 (방금 활성화한 것 제외)
    await (
        client.table("search_presets")
        .update({"is_active": False})
        .eq("team_id", team_id)
        .eq("is_active", True)
        .neq("id", preset_id)
        .execute()
    )

    return ok(res.data[0])


# ── F-04: 공고 수집 트리거 ───────────────────────────────────

@router.post("/teams/{team_id}/bids/fetch")
async def trigger_fetch(
    team_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
    """활성 프리셋 기준 공고 수집 트리거 (백그라운드 실행)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    preset = await _get_active_preset_or_422(client, team_id)

    # Rate Limit: 1시간 이내 재수집 방지
    if preset.get("last_fetched_at"):
        last = datetime.fromisoformat(preset["last_fetched_at"])
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = datetime.now(timezone.utc) - last
        if elapsed < timedelta(hours=_FETCH_COOLDOWN_HOURS):
            remaining_min = int((_FETCH_COOLDOWN_HOURS * 60) - elapsed.total_seconds() / 60)
            raise RateLimitError(
                f"마지막 수집: {int(elapsed.total_seconds()/60)}분 전. "
                f"{remaining_min}분 후 다시 시도하세요."
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
        if k in TeamBidProfile.model_fields and k != "team_id"
    })

    background_tasks.add_task(
        _run_fetch_and_analyze, team_id, preset_obj, profile_obj
    )

    return ok(None, message="공고 수집을 시작합니다.")


# ── F-04: 추천 공고 목록 ─────────────────────────────────────

@router.get("/teams/{team_id}/bids/recommendations")
async def get_recommendations(
    team_id: str,
    refresh: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
):
    """추천 공고 목록 (캐시 우선, match_score 내림차순)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

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


@router.get("/teams/{team_id}/bids/announcements")
async def list_announcements(
    team_id: str,
    keyword: Optional[str] = Query(default=None),
    min_budget: Optional[int] = Query(default=None, ge=0),
    min_days: Optional[int] = Query(default=None, ge=0),
    bid_type: Optional[str] = Query(default=None),
    agency: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    """수집된 공고 목록 (필터/페이징)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, current_user.id)

    query = client.table("bid_announcements").select("*", count="exact")

    if keyword:
        query = query.ilike("bid_title", f"%{_escape_like(keyword)}%")
    if min_budget is not None:
        query = query.gte("budget_amount", min_budget)
    if bid_type:
        query = query.eq("bid_type", bid_type)
    if agency:
        query = query.ilike("agency", f"%{_escape_like(agency)}%")
    if min_days is not None:
        min_deadline = (datetime.now(timezone.utc) + timedelta(days=min_days)).isoformat()
        query = query.gte("deadline_date", min_deadline)

    offset = (page - 1) * per_page
    res = (
        await query
        .order("deadline_date", desc=False)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return ok_list(res.data or [], total=res.count or 0, offset=offset, limit=per_page)


# ── 파이프라인 상태 조회 ────────────────────────────────

@router.get("/bids/pipeline/status")
async def pipeline_status(
    bid_no: str = Query(default=None),
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """파이프라인 진행 상태 조회. bid_no 지정 시 해당 건만."""
    if bid_no:
        status = get_pipeline_status(bid_no)
        return ok({bid_no: status} if status else {})
    return ok(get_all_pipeline_status())


@router.post("/bids/pipeline/trigger")
async def pipeline_trigger(
    background_tasks: BackgroundTasks,
    bid_nos: list[str] | None = None,
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """수동 파이프라인 트리거. bid_nos 미지정 시 DB 최근 공고 대상."""
    if not bid_nos:
        try:
            client = await get_async_client()
            res = await (
                client.table("bid_announcements")
                .select("bid_no")
                .is_("content_text", "null")
                .order("created_at", desc=True)
                .limit(20)
                .execute()
            )
            bid_nos = [r["bid_no"] for r in (res.data or [])]
        except Exception:
            bid_nos = []

    if bid_nos:
        background_tasks.add_task(run_pipeline, bid_nos)
    return ok({"queued": len(bid_nos or [])})


# ── 적합도 스코어링 기반 공고 조회 (v2) ────────────────

@router.get("/bids/scored")
async def get_scored_bids(
    days: int = Query(7, ge=1, le=30, description="조회 일수 (최근 N일)"),
    min_budget: int = Query(0, ge=0, description="최소 예산 (원)"),
    max_results: int = Query(100, ge=1, le=300, description="최대 반환 건수"),
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """
    DB 저장된 공고 목록 조회 (적합도 스코어링 기반).

    정기 스케줄러(평일 08~18시 매시 정각)가 수집한 데이터 조회.
    실시간 G2B 호출 없음 — 수동 크롤링은 POST /bids/crawl 사용.
    """
    try:
        # G2B API에서 직접 공고 검색 (최근 N일)
        from app.services.g2b_service import G2BService

        g2b = G2BService()
        bids = await g2b.search_bids(lookback_days=days)

        # 적합도 스코어링
        scored = score_and_rank_bids(
            bids,
            reference_date=datetime.now(timezone.utc).date(),
            min_score=0,
            exclude_expired=True,
            max_results=max_results,
            min_days_remaining=3,
        )

        # "관련없음" 공고 제외 (파일 캐시 기반)
        try:
            cache_dir = Path("data/bid_status")
            excluded_nos: set[str] = set()
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        data = json.loads(cache_file.read_text(encoding="utf-8"))
                        if data.get("status") == "관련없음":
                            excluded_nos.add(data.get("bid_no", ""))
                    except Exception:
                        pass
            if excluded_nos:
                scored = [bs for bs in scored if bs.bid_no not in excluded_nos]
        except Exception as e:
            logger.warning(f"bid_status 캐시 읽기 실패 (필터링 건너뜀): {e}")

        return ok({
            "data": scored,
            "total_fetched": len(bids),
            "date_from": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),
            "date_to": datetime.now(timezone.utc).isoformat(),
            "sources": {"입찰공고": len(bids)},
        })
    except Exception as e:
        logger.error(f"get_scored_bids 오류: {e}", exc_info=True)
        raise InternalServiceError("G2B 공고 조회 실패")


@router.post("/bids/crawl")
async def manual_crawl(
    background_tasks: BackgroundTasks,
    days: int = Query(1, ge=1, le=7, description="수집 일수"),
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """
    수동 크롤링 — G2B에서 최신 공고 수집 후 DB 저장 + 백그라운드 파이프라인.

    프론트엔드 "새로고침" 버튼에서만 호출.
    """
    try:
        date_to_dt = datetime.now(timezone.utc)
        date_from_dt = date_to_dt - timedelta(days=days - 1)
        date_from_str = date_from_dt.strftime("%Y%m%d") + "0000"
        date_to_str = date_to_dt.strftime("%Y%m%d") + "2359"

        async with G2BService() as g2b:
            fetcher = BidFetcher(g2b_service=g2b, supabase_client=None)
            results = await fetcher.fetch_bids_scored(
                date_from=date_from_str,
                date_to=date_to_str,
                min_budget=0,
                min_score=0,
                max_results=300,
            )

        # 백그라운드 파이프라인: 상위 scored 공고 DB 저장 + 첨부파일 + AI 분석
        scored_data = results.get("data", [])
        top_bid_nos = [b["bid_no"] for b in scored_data[:50] if b.get("score", 0) >= 80]
        if top_bid_nos:
            raw_map = {b["bid_no"]: b.get("raw_data", {}) for b in scored_data if b["bid_no"] in set(top_bid_nos)}
            background_tasks.add_task(run_pipeline, top_bid_nos, raw_map)

        return ok({
            "total_fetched": results["total_fetched"],
            "scored_count": len(results["data"]),
            "pipeline_queued": len(top_bid_nos),
        })
    except Exception as e:
        logger.error(f"수동 크롤링 오류: {e}")
        raise InternalServiceError("공고 수집 중 오류가 발생했습니다.")


@router.get("/bids/monitor")
async def get_monitored_bids(
    scope: str = Query(default="company", pattern="^(my|team|division|company)$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    show_all: bool = Query(default=False),
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """공고 모니터링 — 스코프별 공고 목록.

    - my: 사용자 북마크 + 관심분야 매칭
    - team: 사용자 소속 팀의 추천 공고
    - division: 사용자 소속 본부 내 모든 팀의 추천 공고
    - company: 전체 조직 추천 공고 (모든 팀 합산)
    """
    client = await get_async_client()
    user_id = current_user.id if current_user else None
    offset = (page - 1) * per_page

    if not user_id and scope != "company":
        scope = "company"

    if scope == "my":
        data, total = await _monitor_my(client, user_id, offset, per_page)
    elif scope in ("team", "division"):
        result = await _monitor_team_or_division(client, user_id, scope, offset, per_page)
        if result is None:
            return ok_list([], total=0, offset=offset, limit=per_page)
        data, total = result
    else:
        data, total = await _monitor_company(client, offset, per_page)

    await _enrich_monitor_data(client, data, user_id)

    if not show_all:
        hidden = {"제안포기", "관련없음"}
        data = [b for b in data if b.get("proposal_status") not in hidden]
        total = len(data)

    return ok_list(data, total=total, offset=offset, limit=per_page)


@router.put("/bids/{bid_no}/status")
async def update_bid_status(
    bid_no: str,
    body: BidStatusUpdate,
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """공고 제안여부 상태 변경 (DB + 파일 캐시 이중 저장)"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    status = body.status

    # 의사결정자 이름 조회
    decided_by = ""
    client = await get_async_client()
    user_id = current_user.id if current_user else None
    if user_id:
        try:
            u_res = (
                await client.table("users")
                .select("name")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            decided_by = (u_res.data or {}).get("name", "")
        except Exception:
            pass

    # 1) DB bid_announcements.proposal_status 업데이트
    try:
        await (
            client.table("bid_announcements")
            .update({"proposal_status": status, "decided_by": decided_by})
            .eq("bid_no", bid_no)
            .execute()
        )
    except Exception as e:
        # DB 컬럼이 아직 마이그레이션되지 않은 경우 — 파일 캐시로 폴백
        logger.warning(f"bid_announcements DB 업데이트 실패 (파일 캐시로 폴백): {e}")

    # 2) 파일 캐시에도 저장 (하위 호환)
    cache_dir = Path("data/bid_status")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{bid_no}.json"
    cache_file.write_text(
        json.dumps({"bid_no": bid_no, "status": status, "decided_by": decided_by}, ensure_ascii=False),
        encoding="utf-8",
    )

    return ok({"bid_no": bid_no, "status": status, "decided_by": decided_by})


@router.get("/bids/{bid_no}/analysis")
async def analyze_bid_for_proposal(
    bid_no: str,
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """
    RFP 요약 + TENOPA 적합성 분석 (2단계 파이프라인)

    Stage 1: 전처리 에이전트 — 공고문 핵심 섹션 타겟팅 추출
    Stage 2: TENOPA 수주 심의위원 — 도메인 적합성 0~100점 평가
    """
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    cache_dir = Path("data/bid_analyses")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{bid_no}.json"

    # 캐시 히트 확인
    cached = _check_analysis_cache(cache_file, bid_no)
    if cached is not None:
        return ok(cached)

    # 공고 데이터 + 본문 로드 (DB → G2B fallback → 첨부파일)
    bid, content = await _load_bid_content(bid_no)

    # 팀 조직도 로드
    teams_info_text, valid_team_names = _load_teams_info()

    # AI 통합 분석
    result = await _run_unified_analysis(bid_no, bid, content, teams_info_text, valid_team_names)

    # 캐시 저장 (score > 0인 경우만)
    if result["suitability_score"] > 0:
        try:
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"[{bid_no}] 분석 캐시 저장 완료")
        except Exception as e:
            logger.warning(f"분석 캐시 저장 실패 (무시): {e}")
    else:
        logger.info(f"[{bid_no}] 부분 결과 반환 (캐시 미저장, 다음에 재시도)")

    return ok(result)


@router.post("/bids/{bid_no}/bookmark")
async def toggle_bookmark(
    bid_no: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """공고 북마크 토글"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    client = await get_async_client()
    user_id = current_user.id

    existing = (
        await client.table("bid_bookmarks")
        .select("id")
        .eq("user_id", user_id)
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )

    if existing.data:
        await client.table("bid_bookmarks").delete().eq("id", existing.data["id"]).execute()
        return ok({"bookmarked": False})
    else:
        await client.table("bid_bookmarks").insert({"user_id": user_id, "bid_no": bid_no}).execute()
        return ok({"bookmarked": True})


@router.get("/bids/{bid_no}")
async def get_bid_detail(
    bid_no: str,
    team_id: Optional[str] = Query(default=None),
    current_user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """공고 상세 + AI 분석 결과. DB에 없으면 G2B API에서 실시간 조회 + DB 저장."""
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    # DB 조회 시도
    client = await get_async_client()
    res_data = None
    try:
        res = (
            await client.table("bid_announcements")
            .select("*")
            .eq("bid_no", bid_no)
            .maybe_single()
            .execute()
        )
        if res and res.data:
            res_data = res.data
    except Exception as e:
        logger.warning(f"DB 조회 실패 ({bid_no}): {e}")

    # DB에 없으면 G2B API로 실시간 조회
    if not res_data:
        try:
            async with G2BService() as g2b:
                g2b_detail = await g2b.get_bid_detail(bid_no)
            if not g2b_detail:
                raise BidNotFoundError(bid_no=bid_no)

            # G2B 응답 → bid_announcements 형태로 매핑
            content_text = _extract_content_from_raw(g2b_detail) or None
            row = {
                "bid_no": bid_no,
                "bid_title": g2b_detail.get("bidNtceNm", ""),
                "agency": g2b_detail.get("dminsttNm", ""),
                "budget_amount": int(float(g2b_detail["presmptPrce"])) if g2b_detail.get("presmptPrce") else None,
                "deadline_date": None,
                "content_text": content_text,
                "raw_data": g2b_detail,
            }
            bid_close = g2b_detail.get("bidClseDt", "")
            if bid_close:
                row["deadline_date"] = bid_close[:10]

            # DB 저장 시도 (실패해도 무시)
            try:
                await client.table("bid_announcements").upsert(row, on_conflict="bid_no").execute()
                res = (
                    await client.table("bid_announcements")
                    .select("*")
                    .eq("bid_no", bid_no)
                    .maybe_single()
                    .execute()
                )
                if res and res.data:
                    res_data = res.data
            except Exception as e:
                logger.warning(f"DB upsert 실패 ({bid_no}): {e}")

            if not res_data:
                res_data = row
        except BidNotFoundError:
            raise
        except Exception as e:
            logger.warning(f"G2B fallback 실패 ({bid_no}): {e}")
            raise BidNotFoundError(bid_no=bid_no)

    result = {"announcement": res_data, "recommendation": None}

    # 팀 AI 분석 결과 포함 (team_id 파라미터가 있는 경우)
    if team_id and current_user:
        await _require_team_member(client, team_id, current_user.id)
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
            result["recommendation"] = rec_res.data[0]

    return ok(result)


# ── F-04: 제안서 연동 ────────────────────────────────────────

# ── 첨부파일 조회 + 다운로드 ────────────────────────────────

@router.get("/bids/{bid_no}/attachments")
async def list_bid_attachments(
    bid_no: str,
    proposal_id: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """공고 첨부파일 목록 (Storage 저장된 파일 포함)"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    client = await get_async_client()

    # proposal이 지정된 경우 해당 프로젝트의 첨부파일 확인
    lookup_id = proposal_id or bid_no
    try:
        files = await client.storage.from_(settings.storage_bucket_proposals).list(
            path=f"{lookup_id}/attachments"
        )
        stored = [
            {
                "name": f.get("name", ""),
                "size": f.get("metadata", {}).get("size", 0),
                "storage_path": f"{lookup_id}/attachments/{f['name']}",
                "created_at": f.get("created_at", ""),
            }
            for f in (files or [])
            if f.get("name")
        ]
    except Exception:
        stored = []

    # G2B 원본 URL도 함께 반환 (bid_announcements에 저장된 경우)
    ann_res = (
        await client.table("bid_announcements")
        .select("raw_data")
        .eq("bid_no", bid_no)
        .maybe_single()
        .execute()
    )
    g2b_urls = []
    if ann_res.data and ann_res.data.get("raw_data"):
        raw = ann_res.data["raw_data"]
        for i in range(1, 6):
            url = raw.get(f"ntceSpecDocUrl{i}", "")
            if url:
                g2b_urls.append({"index": i, "url": url})
        detail_url = raw.get("bidNtceDtlUrl", "")
        if detail_url:
            g2b_urls.insert(0, {"index": 0, "url": detail_url, "label": "나라장터 공고 상세"})

    return ok({
        "stored_files": stored,
        "g2b_urls": g2b_urls,
    })


@router.get("/bids/{bid_no}/attachments/{file_name}")
async def download_bid_attachment(
    bid_no: str,
    file_name: str,
    proposal_id: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """첨부파일 다운로드 (Supabase Storage에서 Signed URL 발급)"""
    if not _BID_NO_PATTERN.match(bid_no):
        raise BidValidationError("유효하지 않은 공고번호 형식입니다.")

    client = await get_async_client()
    lookup_id = proposal_id or bid_no
    storage_path = f"{lookup_id}/attachments/{file_name}"

    try:
        result = await client.storage.from_(settings.storage_bucket_proposals).create_signed_url(
            path=storage_path,
            expires_in=settings.signed_url_expiry_seconds,
        )
        signed_url = result.get("signedURL") or result.get("signedUrl", "")
        if not signed_url:
            raise FileNotFoundError_("파일을 찾을 수 없습니다.")
        return ok({"url": signed_url, "file_name": file_name, "expires_in": settings.signed_url_expiry_seconds})
    except FileNotFoundError_:
        raise
    except Exception as e:
        logger.warning(f"첨부파일 다운로드 URL 생성 실패: {e}")
        raise FileNotFoundError_("파일을 찾을 수 없습니다.")


# NOTE: POST /api/proposals/from-bid는 routes_proposal.py에서 처리 (제안 프로젝트 생성 + 첨부파일 연결)
# 이 파일의 레거시 라우트는 2026-03-25 제거됨 (라우트 충돌 해소)


# ── 모니터 스코프별 헬퍼 ─────────────────────────────────────

_MONITOR_BASE_FIELDS = (
    "bid_no, bid_title, agency, budget_amount, deadline_date, "
    "days_remaining, bid_type, content_text, raw_data"
)


async def _monitor_my(client, user_id: str, offset: int, per_page: int) -> tuple[list, int]:
    """my 스코프: 북마크 + 관심분야 매칭 공고"""
    bookmarked = (
        await client.table("bid_bookmarks")
        .select("bid_no")
        .eq("user_id", user_id)
        .execute()
    )
    bookmarked_nos = {b["bid_no"] for b in (bookmarked.data or [])}

    user_res = (
        await client.table("users")
        .select("interests, team_id")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    user_data = user_res.data or {}
    interests = user_data.get("interests") or []
    now_iso = datetime.now(timezone.utc).isoformat()

    matched_bids = []
    if interests:
        or_filter = ",".join(
            f"bid_title.ilike.%{_escape_like(kw)}%" for kw in interests[:5]
        )
        kw_res = (
            await client.table("bid_announcements")
            .select(_MONITOR_BASE_FIELDS)
            .or_(or_filter)
            .gte("deadline_date", now_iso)
            .order("deadline_date", desc=False)
            .limit(50)
            .execute()
        )
        matched_bids.extend(kw_res.data or [])

    if bookmarked_nos:
        bm_res = (
            await client.table("bid_announcements")
            .select(_MONITOR_BASE_FIELDS)
            .in_("bid_no", list(bookmarked_nos))
            .order("days_remaining", desc=False)
            .execute()
        )
        matched_bids.extend(bm_res.data or [])

    seen: set[str] = set()
    unique = []
    for b in matched_bids:
        if b["bid_no"] not in seen:
            seen.add(b["bid_no"])
            b["is_bookmarked"] = b["bid_no"] in bookmarked_nos
            unique.append(b)

    unique.sort(key=lambda x: (not x.get("is_bookmarked", False), x.get("days_remaining") or 999))
    return unique[offset:offset + per_page], len(unique)


async def _monitor_team_or_division(
    client, user_id: str, scope: str, offset: int, per_page: int
) -> tuple[list, int] | None:
    """team/division 스코프: AI 추천 공고. 팀/본부 미소속이면 None 반환."""
    user_res = (
        await client.table("users")
        .select("team_id, division_id")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    user_data = user_res.data or {}

    try:
        if scope == "team":
            team_id = user_data.get("team_id")
            if not team_id:
                return None
            rec_res = (
                await client.table("bid_recommendations")
                .select("*, bid_announcements(bid_no, bid_title, agency, budget_amount, deadline_date, days_remaining)")
                .eq("team_id", team_id)
                .neq("qualification_status", "fail")
                .order("match_score", desc=True)
                .range(offset, offset + per_page - 1)
                .execute()
            )
        else:
            division_id = user_data.get("division_id")
            if not division_id:
                return None
            teams_res = (
                await client.table("teams")
                .select("id")
                .eq("division_id", division_id)
                .execute()
            )
            team_ids = [t["id"] for t in (teams_res.data or [])]
            if not team_ids:
                return None
            rec_res = (
                await client.table("bid_recommendations")
                .select("*, bid_announcements(bid_no, bid_title, agency, budget_amount, deadline_date, days_remaining)")
                .in_("team_id", team_ids)
                .neq("qualification_status", "fail")
                .order("match_score", desc=True)
                .range(offset, offset + per_page - 1)
                .execute()
            )
    except Exception as e:
        logger.warning(f"bid_recommendations 조회 실패 ({scope}): {e}")
        rec_res = type("R", (), {"data": []})()

    data = []
    seen_bids: set[str] = set()
    for row in (rec_res.data or []):
        ann = row.get("bid_announcements") or {}
        bid_no = ann.get("bid_no") or row.get("bid_no")
        if bid_no in seen_bids:
            continue
        seen_bids.add(bid_no)
        data.append({
            **ann,
            "match_score": row.get("match_score"),
            "match_grade": row.get("match_grade"),
            "recommendation_summary": row.get("recommendation_summary"),
            "recommendation_reasons": row.get("recommendation_reasons") or [],
            "qualified": row.get("qualification_status") == "pass",
        })
    return data, len(data)


async def _monitor_company(client, offset: int, per_page: int) -> tuple[list, int]:
    """company 스코프: 전체 마감 전 공고 + AI 추천 점수 병합"""
    now_iso = datetime.now(timezone.utc).isoformat()
    ann_res = (
        await client.table("bid_announcements")
        .select(_MONITOR_BASE_FIELDS, count="exact")
        .gte("deadline_date", now_iso)
        .order("deadline_date", desc=False)
        .range(offset, offset + per_page - 1)
        .execute()
    )
    data = ann_res.data or []
    total = ann_res.count or 0

    if data:
        bid_nos = [b["bid_no"] for b in data]
        rec_res = (
            await client.table("bid_recommendations")
            .select("bid_no, match_score, match_grade, recommendation_summary, qualification_status")
            .in_("bid_no", bid_nos)
            .order("match_score", desc=True)
            .execute()
        )
        rec_map: dict[str, dict] = {}
        for r in (rec_res.data or []):
            if r["bid_no"] not in rec_map:
                rec_map[r["bid_no"]] = r

        for b in data:
            rec = rec_map.get(b["bid_no"])
            if rec:
                b["match_score"] = rec.get("match_score")
                b["match_grade"] = rec.get("match_grade")
                b["recommendation_summary"] = rec.get("recommendation_summary")

    return data, total


async def _enrich_monitor_data(client, data: list[dict], user_id: str | None) -> None:
    """모니터 공통 후처리: days_remaining 재계산, raw_data 추출, 팀매칭, 북마크, 제안여부"""
    # days_remaining 동적 재계산
    _today = datetime.now(timezone.utc).date()
    for b in data:
        dl = b.get("deadline_date")
        if dl:
            try:
                dl_date = datetime.fromisoformat(str(dl).replace("Z", "+00:00")).date()
                b["days_remaining"] = (dl_date - _today).days
            except (ValueError, TypeError):
                pass

    # raw_data → 첨부파일 + 공고단계 추출
    for b in data:
        raw = b.pop("raw_data", None) or {}
        attachments = []
        for i in range(1, 11):
            url = raw.get(f"ntceSpecDocUrl{i}")
            name = raw.get(f"ntceSpecFileNm{i}")
            if url and name:
                attachments.append({"name": name, "url": url})
        b["attachments"] = attachments

        bid_no = b.get("bid_no", "")
        kind = raw.get("ntceKindNm", "")
        if bid_no.startswith("PRE-") or "사전" in kind or "규격" in kind:
            b["bid_stage"] = "사전공고"
        else:
            b["bid_stage"] = "본공고"

    # 팀 매칭 + 관련성 평가
    team_list = []
    profile_map: dict[str, dict] = {}
    try:
        teams_res = await client.table("teams").select("id, name").execute()
        team_list = teams_res.data or []
    except Exception as e:
        logger.warning(f"팀 조회 실패 (무시): {e}")

    try:
        profiles_res = (
            await client.table("team_bid_profiles")
            .select("team_id, expertise_areas, tech_keywords")
            .execute()
        )
        profile_map = {p["team_id"]: p for p in (profiles_res.data or [])}
    except Exception as e:
        logger.warning(f"팀 프로필 조회 실패 (무시): {e}")

    for b in data:
        text = ((b.get("bid_title") or "") + " " + (b.get("content_text") or "")).lower()
        matched_teams = []
        max_score = 0

        for team in team_list:
            keywords = []
            if team.get("specialty"):
                keywords.extend([k.strip() for k in team["specialty"].split(",") if k.strip()])
            profile = profile_map.get(team["id"])
            if profile:
                keywords.extend(profile.get("expertise_areas") or [])
                keywords.extend(profile.get("tech_keywords") or [])
            if not keywords:
                continue

            hits = sum(1 for kw in keywords if kw.lower() in text)
            if hits > 0:
                matched_teams.append({"name": team["name"], "hits": hits})
                max_score = max(max_score, hits)

        matched_teams.sort(key=lambda t: t["hits"], reverse=True)
        b["related_teams"] = [t["name"] for t in matched_teams[:2]]
        b["relevance"] = "적극 추천" if max_score >= 3 else ("보통" if max_score >= 1 else "낮음")

    # 북마크 정보
    if user_id:
        bm_res = (
            await client.table("bid_bookmarks")
            .select("bid_no")
            .eq("user_id", user_id)
            .execute()
        )
        bm_set = {r["bid_no"] for r in (bm_res.data or [])}
        for b in data:
            b.setdefault("is_bookmarked", b["bid_no"] in bm_set)
    else:
        for b in data:
            b.setdefault("is_bookmarked", False)

    # 제안여부 (DB 우선, 파일 캐시 폴백)
    status_dir = Path("data/bid_status")
    for b in data:
        if b.get("proposal_status"):
            continue
        if status_dir.exists():
            sf = status_dir / f"{b['bid_no']}.json"
            if sf.exists():
                try:
                    st = json.loads(sf.read_text(encoding="utf-8"))
                    b["proposal_status"] = st.get("status")
                    b["decided_by"] = st.get("decided_by")
                except Exception:
                    pass


# ── 분석 헬퍼 ────────────────────────────────────────────────


def _extract_content_from_raw(raw: dict) -> str:
    """raw_data에서 공고 본문 텍스트 추출 (우선순위: ntceSpecCn > bidNtceDtlCn > specDocCn > bidNtceDtl > bidNtceNm)"""
    return (
        raw.get("ntceSpecCn")
        or raw.get("bidNtceDtlCn")
        or raw.get("specDocCn")
        or raw.get("bidNtceDtl")
        or raw.get("bidNtceNm", "")
    )


def _check_analysis_cache(cache_file, bid_no: str) -> dict | None:
    """유효한 분석 캐시가 있으면 반환, 없으면 None"""
    if not cache_file.exists():
        return None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        has_sections = bool(cached.get("rfp_sections"))
        has_summary = cached.get("rfp_summary") and cached["rfp_summary"] != [
            "공고 상세 텍스트를 가져올 수 없습니다. 첨부파일을 확인해주세요."
        ]
        has_score = cached.get("suitability_score") and cached["suitability_score"] > 0
        if (has_sections or has_summary) and has_score:
            logger.info(f"[{bid_no}] 분석 캐시 히트")
            return cached
        logger.info(f"[{bid_no}] 분석 캐시 무효 (빈 결과) → 재분석")
        cache_file.unlink(missing_ok=True)
    except Exception:
        pass
    return None


async def _load_bid_content(bid_no: str) -> tuple[dict, str]:
    """공고 데이터 + 본문 텍스트 로드 (DB → G2B fallback → 첨부파일 추출)"""
    bid = None
    client = await get_async_client()

    try:
        res = (
            await client.table("bid_announcements")
            .select("bid_title, agency, budget_amount, deadline_date, content_text, raw_data")
            .eq("bid_no", bid_no)
            .maybe_single()
            .execute()
        )
        if res:
            bid = res.data
    except Exception as e:
        logger.warning(f"[{bid_no}] DB 조회 실패: {e}")

    raw = {}
    content = ""

    if bid:
        raw = bid.get("raw_data") or {}
        content = bid.get("content_text") or ""
        if not content:
            content = _extract_content_from_raw(raw)
            if not content:
                content = raw.get("bidNtceNm", "")
    else:
        logger.info(f"[{bid_no}] DB 미존재 → G2B 실시간 조회")
        try:
            async with G2BService() as g2b:
                g2b_detail = await g2b.get_bid_detail(bid_no)
            if g2b_detail:
                bid = {
                    "bid_title": g2b_detail.get("bidNtceNm", ""),
                    "agency": g2b_detail.get("dminsttNm", "") or g2b_detail.get("ntceInsttNm", ""),
                    "budget_amount": int(g2b_detail.get("presmptPrce", 0) or 0) or None,
                }
                raw = g2b_detail
                content = _extract_content_from_raw(raw)
        except Exception as e:
            logger.warning(f"[{bid_no}] G2B 조회 실패: {e}")

        if not bid:
            raise BidNotFoundError(bid_no=bid_no)

    # 본문 부족 시 첨부파일 다운로드 + 텍스트 추출
    if len(content.strip()) < 200:
        try:
            attachment_text = await download_bid_attachments(bid_no, raw)
            if attachment_text:
                content = attachment_text
                try:
                    await client.table("bid_announcements").update(
                        {"content_text": attachment_text}
                    ).eq("bid_no", bid_no).execute()
                except Exception:
                    pass
                logger.info(f"[{bid_no}] 첨부파일 다운로드+추출 성공 ({len(attachment_text)}자)")
        except Exception as e:
            logger.warning(f"[{bid_no}] 첨부파일 처리 실패 (무시): {e}")

    return bid, content


def _load_teams_info() -> tuple[str, set[str]]:
    """팀 조직도 파일에서 팀명 + 전문분야 로드"""
    teams_info_text = ""
    valid_team_names: set[str] = set()
    try:
        team_file = Path("data/team_structure.json")
        if team_file.exists():
            team_data = json.loads(team_file.read_text(encoding="utf-8"))
            lines = []
            for t in team_data.get("teams", []):
                name = t.get("name", "")
                div = t.get("division", "")
                specs = t.get("specializations", [])
                if name and specs:
                    valid_team_names.add(name)
                    lines.append(f"- {name} ({div}): {', '.join(specs)}")
            teams_info_text = "\n".join(lines)
    except Exception:
        pass
    return teams_info_text, valid_team_names


async def _run_unified_analysis(
    bid_no: str,
    bid: dict,
    content: str,
    teams_info_text: str,
    valid_team_names: set[str],
) -> dict:
    """Claude 통합 분석 실행 → 결과 dict 반환"""
    rfp_sections: list[dict] = []
    rfp_summary: list[str] = []
    rfp_period = ""
    score = 0
    verdict = "제외"
    fit_level = "보통"
    positive: list[str] = []
    negative: list[str] = []
    action_plan = ""
    recommended_teams: list[str] = []

    if content.strip():
        try:
            ai_client = _get_claude_client()
            system_prompt = build_unified_analysis_system(teams_info=teams_info_text)
            user_msg = UNIFIED_ANALYSIS_USER.format(
                bid_no=bid_no,
                bid_title=bid.get("bid_title", ""),
                agency=bid.get("agency", ""),
                content_text=content[:8000],
            )
            response = await asyncio.wait_for(
                ai_client.messages.create(
                    model=settings.claude_model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                ),
                timeout=45,
            )
            text = response.content[0].text

            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])

                s = parsed.get("summary", {})
                rfp_period = s.get("period", "")
                if s.get("purpose"):
                    rfp_sections.append({"label": "목적", "value": s["purpose"]})
                    rfp_summary.append(f"목적: {s['purpose']}")
                if s.get("core_tasks"):
                    rfp_sections.append({"label": "주요 과업", "items": s["core_tasks"]})
                    for t in s["core_tasks"]:
                        rfp_summary.append(f"과업: {t}")

                r = parsed.get("review", {})
                score = max(0, min(100, int(r.get("suitability_score", 0))))
                verdict = r.get("verdict", "제외")
                if verdict not in ("추천", "검토 필요", "제외"):
                    verdict = "검토 필요" if score >= 40 else "제외"
                positive = r.get("strengths", [])
                negative = r.get("risks", [])
                action_plan = r.get("action_plan", "")

                if score >= 80:
                    fit_level = "적극 추천"
                elif score >= 70:
                    fit_level = "추천"
                elif score >= 40:
                    fit_level = "보통"
                else:
                    fit_level = "낮음"

                ai_teams = r.get("recommended_teams", [])
                if isinstance(ai_teams, list) and valid_team_names:
                    recommended_teams = [t for t in ai_teams if t in valid_team_names][:2]
                elif isinstance(ai_teams, list):
                    recommended_teams = ai_teams[:2]

                logger.info(f"[{bid_no}] 통합 분석 완료: {score}점 ({verdict}), 추천팀: {recommended_teams}")
            else:
                logger.warning(f"[{bid_no}] 통합 분석 JSON 미발견")

        except asyncio.TimeoutError:
            logger.warning(f"[{bid_no}] 통합 분석 타임아웃 (45초)")
        except Exception as e:
            logger.warning(f"[{bid_no}] 통합 분석 실패: {e}")

    if not rfp_summary:
        rfp_summary = ["공고 상세 텍스트를 가져올 수 없습니다. 첨부파일을 확인해주세요."]
    if score == 0:
        negative = negative or ["AI 분석을 수행할 수 없습니다. 첨부된 제안요청서를 직접 검토해주세요."]

    return {
        "rfp_summary": rfp_summary,
        "rfp_sections": rfp_sections,
        "rfp_period": rfp_period,
        "fit_level": fit_level,
        "positive": positive,
        "negative": negative,
        "recommended_teams": recommended_teams,
        "suitability_score": score,
        "verdict": verdict,
        "action_plan": action_plan,
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
        raise ResourceNotFoundError("프리셋")
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
        raise InvalidRequestError("검색 조건 프리셋을 먼저 생성하고 활성화하세요.")
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
        raise InvalidRequestError("팀 프로필을 먼저 설정하세요.")
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

    return ok({
        "recommended": recommended,
        "excluded": excluded,
        "total_fetched": len(rows),
        "analyzed_at": analyzed_at or datetime.now(timezone.utc).isoformat(),
    })


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
            # 사전규격도 수집
            try:
                pre_bids = await fetcher.fetch_pre_bids_by_preset(preset)
                bids.extend(pre_bids)
            except Exception as e:
                logger.debug(f"사전규격 수집 실패 (무시): {e}")

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
