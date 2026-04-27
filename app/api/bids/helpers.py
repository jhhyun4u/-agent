"""
Helper functions for bid API handlers.

NOTE: Temporarily re-exporting from routes_bids.py.
This module will be populated with actual helpers during Phase 3.2 refactoring.
"""

# Temporary re-exports from original routes_bids.py (during transition)
from app.api.routes_bids import (
    # Monitoring helpers (3)
    _monitor_my,
    _monitor_team_or_division,
    _monitor_company,
    # Data enrichment (1)
    _enrich_monitor_data,
    # Analysis (1)
    _run_unified_analysis,
    # Recommendations (1)
    _save_recommendations,
    # Cache invalidation (1)
    _invalidate_recommendations_cache,
    # Validation helpers (3)
    _get_preset_or_404,
    _get_active_preset_or_422,
    _get_profile_or_422,
    # Recommendation helpers (2)
    _get_cached_recommendations,
    _build_recommendations_response,
    # Background tasks (4)
    _run_fetch_and_analyze,
    _queue_bid_analysis,
    _analyze_bid_background,
    _save_markdown_to_storage,
)

__all__ = [
    "_monitor_my",
    "_monitor_team_or_division",
    "_monitor_company",
    "_enrich_monitor_data",
    "_run_unified_analysis",
    "_save_recommendations",
    "_invalidate_recommendations_cache",
    "_get_preset_or_404",
    "_get_active_preset_or_422",
    "_get_profile_or_422",
    "_get_cached_recommendations",
    "_build_recommendations_response",
    "_run_fetch_and_analyze",
    "_queue_bid_analysis",
    "_analyze_bid_background",
    "_save_markdown_to_storage",
]
