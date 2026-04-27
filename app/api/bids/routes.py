"""
Bid API router configuration (21 endpoints).
"""

from fastapi import APIRouter

from .handlers import (
    # Team Bid Profile (2)
    get_bid_profile,
    upsert_bid_profile,
    # Search Presets (5)
    list_search_presets,
    create_search_preset,
    update_search_preset,
    delete_search_preset,
    activate_search_preset,
    # Bid Operations (2)
    trigger_fetch,
    get_recommendations,
    # Global Operations (13)
    list_announcements,
    pipeline_status,
    pipeline_trigger,
    get_scored_bids,
    manual_crawl,
    get_monitored_bids,
    update_bid_status,
    analyze_bid_for_proposal,
    toggle_bookmark,
    get_bid_detail,
    list_bid_attachments,
    download_bid_attachment,
)

router = APIRouter(prefix="/api", tags=["bids"])

# ── Team Bid Profile (2 endpoints) ──────────────────────
router.add_api_route(
    "/teams/{team_id}/bid-profile",
    get_bid_profile,
    methods=["GET"],
    name="get_bid_profile"
)
router.add_api_route(
    "/teams/{team_id}/bid-profile",
    upsert_bid_profile,
    methods=["PUT"],
    name="upsert_bid_profile"
)

# ── Search Presets (5 endpoints) ───────────────────────
router.add_api_route(
    "/teams/{team_id}/search-presets",
    list_search_presets,
    methods=["GET"],
    name="list_search_presets"
)
router.add_api_route(
    "/teams/{team_id}/search-presets",
    create_search_preset,
    methods=["POST"],
    status_code=201,
    name="create_search_preset"
)
router.add_api_route(
    "/teams/{team_id}/search-presets/{preset_id}",
    update_search_preset,
    methods=["PUT"],
    name="update_search_preset"
)
router.add_api_route(
    "/teams/{team_id}/search-presets/{preset_id}",
    delete_search_preset,
    methods=["DELETE"],
    status_code=204,
    name="delete_search_preset"
)
router.add_api_route(
    "/teams/{team_id}/search-presets/{preset_id}/activate",
    activate_search_preset,
    methods=["POST"],
    name="activate_search_preset"
)

# ── Bid Operations (2 endpoints) ───────────────────────
router.add_api_route(
    "/teams/{team_id}/bids/fetch",
    trigger_fetch,
    methods=["POST"],
    name="trigger_fetch"
)
router.add_api_route(
    "/teams/{team_id}/bids/recommendations",
    get_recommendations,
    methods=["GET"],
    name="get_recommendations"
)

# ── Global Operations (13 endpoints) ────────────────────
router.add_api_route(
    "/teams/{team_id}/bids/announcements",
    list_announcements,
    methods=["GET"],
    name="list_announcements"
)
router.add_api_route(
    "/bids/pipeline/status",
    pipeline_status,
    methods=["GET"],
    name="pipeline_status"
)
router.add_api_route(
    "/bids/pipeline/trigger",
    pipeline_trigger,
    methods=["POST"],
    name="pipeline_trigger"
)
router.add_api_route(
    "/bids/scored",
    get_scored_bids,
    methods=["GET"],
    name="get_scored_bids"
)
router.add_api_route(
    "/bids/crawl",
    manual_crawl,
    methods=["POST"],
    name="manual_crawl"
)
router.add_api_route(
    "/bids/monitor",
    get_monitored_bids,
    methods=["GET"],
    name="get_monitored_bids"
)
router.add_api_route(
    "/bids/{bid_no}/status",
    update_bid_status,
    methods=["PUT"],
    name="update_bid_status"
)
router.add_api_route(
    "/bids/{bid_no}/analysis",
    analyze_bid_for_proposal,
    methods=["GET"],
    name="analyze_bid_for_proposal"
)
router.add_api_route(
    "/bids/{bid_no}/bookmark",
    toggle_bookmark,
    methods=["POST"],
    name="toggle_bookmark"
)
router.add_api_route(
    "/bids/{bid_no}",
    get_bid_detail,
    methods=["GET"],
    name="get_bid_detail"
)
router.add_api_route(
    "/bids/{bid_no}/attachments",
    list_bid_attachments,
    methods=["GET"],
    name="list_bid_attachments"
)
router.add_api_route(
    "/bids/{bid_no}/attachments/{file_name}/download",
    download_bid_attachment,
    methods=["POST"],
    name="download_bid_attachment"
)

__all__ = ["router"]
