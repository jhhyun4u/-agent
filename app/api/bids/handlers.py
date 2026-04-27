"""
Bid API endpoint handlers (21 endpoints).

NOTE: Temporarily re-exporting from routes_bids.py.
This module will be populated with actual handlers during Phase 3.2 refactoring.
"""

# Temporary re-exports from original routes_bids.py (during transition)
from app.api.routes_bids import (
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

__all__ = [
    "get_bid_profile",
    "upsert_bid_profile",
    "list_search_presets",
    "create_search_preset",
    "update_search_preset",
    "delete_search_preset",
    "activate_search_preset",
    "trigger_fetch",
    "get_recommendations",
    "list_announcements",
    "pipeline_status",
    "pipeline_trigger",
    "get_scored_bids",
    "manual_crawl",
    "get_monitored_bids",
    "update_bid_status",
    "analyze_bid_for_proposal",
    "toggle_bookmark",
    "get_bid_detail",
    "list_bid_attachments",
    "download_bid_attachment",
]
