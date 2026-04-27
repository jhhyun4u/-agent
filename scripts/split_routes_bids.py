#!/usr/bin/env python3
"""
Automated routes_bids.py modularization script.
Splits 2,168-line file into modular app/api/bids/ structure.
"""

import re
from pathlib import Path


def extract_imports_and_globals(lines: list[str]) -> tuple[list[str], int]:
    """Extract imports and globals until first function"""
    end_idx = 0
    for i, line in enumerate(lines):
        if re.match(r'^(async )?def ', line):
            end_idx = i
            break
    return lines[:end_idx], end_idx


def extract_function(lines: list[str], start_idx: int, all_func_starts: list[int]) -> tuple[str, int]:
    """Extract function from start_idx until next function or EOF"""
    func_lines = [lines[start_idx]]
    end_idx = start_idx + 1

    # Find next function start
    next_func_start = None
    for fn_start in all_func_starts:
        if fn_start > start_idx:
            next_func_start = fn_start
            break

    # Find actual end by looking for dedent
    if next_func_start:
        end_idx = next_func_start
    else:
        end_idx = len(lines)

    func_lines.extend(lines[start_idx + 1:end_idx])

    # Remove trailing blank lines but keep essential spacing
    while func_lines and not func_lines[-1].strip():
        func_lines.pop()

    return '\n'.join(func_lines) + '\n', end_idx - start_idx


def categorize_function(fname: str) -> str:
    """Categorize function into utils, helpers, or handlers"""
    utils_funcs = {
        '_load_file_cache', '_save_file_cache', '_escape_like',
        '_extract_content_from_raw', '_check_analysis_cache', '_load_bid_content',
        '_load_teams_info', '_format_rfp_sections', '_format_notice_markdown',
    }

    helpers_funcs = {
        '_monitor_my', '_monitor_team_or_division', '_monitor_company',
        '_enrich_monitor_data', '_run_unified_analysis', '_save_recommendations',
        '_invalidate_recommendations_cache', '_get_preset_or_404',
        '_get_active_preset_or_422', '_get_profile_or_422',
        '_get_cached_recommendations', '_build_recommendations_response',
        '_run_fetch_and_analyze', '_queue_bid_analysis', '_analyze_bid_background',
        '_save_markdown_to_storage',
    }

    if fname in utils_funcs:
        return 'utils'
    elif fname in helpers_funcs:
        return 'helpers'
    else:
        return 'handlers'


def main():
    """Main modularization process"""
    source = Path(__file__).parent.parent / "app" / "api" / "routes_bids.py"
    bids_dir = source.parent / "bids"
    bids_dir.mkdir(exist_ok=True)

    print(f"📖 Reading {source}...")
    content = source.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Find all function starts
    func_starts = []
    for i, line in enumerate(lines):
        if re.match(r'^(async )?def ', line):
            func_starts.append(i)

    print(f"✅ Found {len(func_starts)} functions")

    # Extract imports/globals
    imports_lines, first_func_idx = extract_imports_and_globals(lines)
    imports_text = '\n'.join(imports_lines)

    print(f"\n📦 Extracting functions by category...")

    # Categorize and store functions
    utils_content = []
    helpers_content = []
    handlers_content = []
    router_lines = []

    for func_start in func_starts:
        func_line = lines[func_start]
        func_match = re.match(r'^(async )?def (\w+)', func_line)
        if not func_match:
            continue

        fname = func_match.group(2)
        category = categorize_function(fname)

        # Extract function
        next_start = None
        for fs in func_starts:
            if fs > func_start:
                next_start = fs
                break

        if not next_start:
            next_start = len(lines)

        func_text = '\n'.join(lines[func_start:next_start]).rstrip() + '\n'

        if category == 'utils':
            utils_content.append((fname, func_text))
        elif category == 'helpers':
            helpers_content.append((fname, func_text))
        else:
            handlers_content.append((fname, func_text))
            if func_line.startswith('@router.'):
                router_lines.append(lines[func_start - 1:func_start + 5])

    print(f"  Utils: {len(utils_content)} functions")
    print(f"  Helpers: {len(helpers_content)} functions")
    print(f"  Handlers: {len(handlers_content)} functions")

    # ─── Write files ───────────────────────────────────────

    # 1. utils.py (updated with correct content from routes_bids.py)
    print("\n✍️  Writing files...")

    # Read exact utils section from original
    utils_start = None
    for i, line in enumerate(lines):
        if '_SCORED_CACHE_FILE' in line:
            utils_start = i
            break

    if utils_start and len(utils_content) > 0:
        # Find end of utils (before first handler function)
        utils_end = func_starts[0]  # First function
        utils_functions_text = '\n'.join(lines[utils_start:utils_end])

        utils_py = f"""'''
Utility functions and constants for bid API.
'''

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings
from app.exceptions import FileNotFoundError_

logger = logging.getLogger(__name__)

{utils_functions_text}
"""
        (bids_dir / "utils.py").write_text(utils_py, encoding='utf-8')
        print(f"  ✅ app/api/bids/utils.py ({len(utils_py)} bytes)")

    # 2. helpers.py
    if helpers_content:
        helpers_py = f'''"""
Helper functions for bid API handlers.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.exceptions import InternalServiceError, ResourceNotFoundError
from app.utils.supabase_client import get_async_client
from app.services.core.claude_client import _get_client as _get_claude_client
from app.prompts.bid_review import UNIFIED_ANALYSIS_USER, build_unified_analysis_system

from .utils import _escape_like, _MONITOR_BASE_FIELDS, _load_file_cache, _save_file_cache

logger = logging.getLogger(__name__)


{"".join(text for _, text in helpers_content)}
'''
        (bids_dir / "helpers.py").write_text(helpers_py, encoding='utf-8')
        print(f"  ✅ app/api/bids/helpers.py ({len(helpers_py)} bytes)")

    # 3. handlers.py
    if handlers_content:
        handlers_py = f'''"""
Bid API endpoint handlers (21 endpoints).
"""

import asyncio
import json
import logging
import time
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
from app.services.domains.bidding.bid_attachment_store import download_bid_attachments
from app.services.domains.bidding.bid_fetcher import BidFetcher
from app.services.domains.bidding.bid_pipeline import (
    get_all_pipeline_status,
    get_pipeline_status,
    run_pipeline,
)
from app.services.domains.bidding.bid_recommender import BidRecommender
from app.services.domains.bidding.g2b_service import G2BService
from app.utils.supabase_client import get_async_client

from .utils import (
    _BID_NO_PATTERN,
    _FETCH_COOLDOWN_HOURS,
    _load_file_cache,
    _save_file_cache,
    _escape_like,
    _check_analysis_cache,
    _load_bid_content,
    _load_teams_info,
    _format_rfp_sections,
    _format_notice_markdown,
)
from .helpers import (
    _monitor_my,
    _monitor_team_or_division,
    _monitor_company,
    _enrich_monitor_data,
    _run_unified_analysis,
    _save_recommendations,
    _invalidate_recommendations_cache,
    _get_preset_or_404,
    _get_active_preset_or_422,
    _get_profile_or_422,
    _get_cached_recommendations,
    _build_recommendations_response,
    _run_fetch_and_analyze,
    _queue_bid_analysis,
    _analyze_bid_background,
    _save_markdown_to_storage,
)

logger = logging.getLogger(__name__)


{"".join(text for _, text in handlers_content)}
'''
        (bids_dir / "handlers.py").write_text(handlers_py, encoding='utf-8')
        print(f"  ✅ app/api/bids/handlers.py ({len(handlers_py)} bytes)")

    # 4. routes.py
    routes_py = '''"""
Bid API router configuration.
"""

from fastapi import APIRouter

from .handlers import (
    get_bid_profile,
    upsert_bid_profile,
    list_search_presets,
    create_search_preset,
    update_search_preset,
    delete_search_preset,
    activate_search_preset,
    trigger_fetch,
    get_recommendations,
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

# Team Bid Profile endpoints
router.add_api_route("/teams/{team_id}/bid-profile", get_bid_profile, methods=["GET"])
router.add_api_route("/teams/{team_id}/bid-profile", upsert_bid_profile, methods=["PUT"])

# Search Presets endpoints
router.add_api_route("/teams/{team_id}/search-presets", list_search_presets, methods=["GET"])
router.add_api_route("/teams/{team_id}/search-presets", create_search_preset, methods=["POST"], status_code=201)
router.add_api_route("/teams/{team_id}/search-presets/{preset_id}", update_search_preset, methods=["PUT"])
router.add_api_route("/teams/{team_id}/search-presets/{preset_id}", delete_search_preset, methods=["DELETE"], status_code=204)
router.add_api_route("/teams/{team_id}/search-presets/{preset_id}/activate", activate_search_preset, methods=["POST"])

# Bid Operations endpoints
router.add_api_route("/teams/{team_id}/bids/fetch", trigger_fetch, methods=["POST"])
router.add_api_route("/teams/{team_id}/bids/recommendations", get_recommendations, methods=["GET"])

# Global endpoints
router.add_api_route("/teams/{team_id}/bids/announcements", list_announcements, methods=["GET"])
router.add_api_route("/bids/pipeline/status", pipeline_status, methods=["GET"])
router.add_api_route("/bids/pipeline/trigger", pipeline_trigger, methods=["POST"])
router.add_api_route("/bids/scored", get_scored_bids, methods=["GET"])
router.add_api_route("/bids/crawl", manual_crawl, methods=["POST"])
router.add_api_route("/bids/monitor", get_monitored_bids, methods=["GET"])
router.add_api_route("/bids/{bid_no}/status", update_bid_status, methods=["PUT"])
router.add_api_route("/bids/{bid_no}/analysis", analyze_bid_for_proposal, methods=["GET"])
router.add_api_route("/bids/{bid_no}/bookmark", toggle_bookmark, methods=["POST"])
router.add_api_route("/bids/{bid_no}", get_bid_detail, methods=["GET"])
router.add_api_route("/bids/{bid_no}/attachments", list_bid_attachments, methods=["GET"])
router.add_api_route("/bids/{bid_no}/attachments/{file_name}/download", download_bid_attachment, methods=["POST"])

__all__ = ["router"]
'''
    (bids_dir / "routes.py").write_text(routes_py, encoding='utf-8')
    print(f"  ✅ app/api/bids/routes.py ({len(routes_py)} bytes)")

    # 5. __init__.py
    init_py = '''"""
Bid API module.
"""

from .routes import router

__all__ = ["router"]
'''
    (bids_dir / "__init__.py").write_text(init_py, encoding='utf-8')
    print(f"  ✅ app/api/bids/__init__.py ({len(init_py)} bytes)")

    print("\n✅ Modularization complete!")
    print(f"\n📊 Summary:")
    print(f"  Source: {source} (2,168 lines)")
    print(f"  Target: {bids_dir}/")
    print(f"  Files created: 5")
    print(f"  Total new code: ~{sum(len(p) for p in [utils_py, helpers_py, handlers_py, routes_py, init_py])} bytes")
    print(f"\n⚠️  Next steps:")
    print(f"  1. Verify imports in app/main.py or app/api/__init__.py")
    print(f"  2. Delete app/api/routes_bids.py (backup first if needed)")
    print(f"  3. Run: python -m py_compile app/api/bids/*.py")
    print(f"  4. Run tests to verify no regressions")


if __name__ == "__main__":
    main()
