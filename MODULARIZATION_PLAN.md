# API Router Modularization Plan (Stage 3)

## 목표
routes_bids.py (2,168줄) → app/api/bids/ 모듈 구조로 분해

## 현재 상태
```
app/api/routes_bids.py (2,168줄)
├── Imports (53줄)
├── Constants & Cache Setup (37줄)  
├── 21 Endpoint Handlers (1,000줄)
├── 22 Helper Functions (1,000줄)
└── Module-level setup
```

## 목표 구조
```
app/api/bids/
├── __init__.py          # Export router for main.py
├── routes.py            # Router creation + endpoint registration
├── handlers.py          # 21 public route handler functions  
├── helpers.py           # 22 private helper functions
├── utils.py             # Constants, caching, formatting utilities
└── schemas.py           # Optional: Pydantic models (if needed)
```

## 분해 계획

### 1. app/api/bids/utils.py (Utility Functions)
**Constants & Caching:**
- _SCORED_CACHE_FILE, _load_file_cache(), _save_file_cache()
- _BID_NO_PATTERN, _FETCH_COOLDOWN_HOURS, _MONITOR_BASE_FIELDS

**Helper Utils:**
- _escape_like() - SQL escaping
- _extract_content_from_raw() - Content parsing
- _check_analysis_cache() - Cache checking
- _load_bid_content() - Bid content loading
- _load_teams_info() - Teams info loading
- _format_rfp_sections() - Formatting
- _format_notice_markdown() - Formatting

### 2. app/api/bids/helpers.py (Handler Helpers)
**Monitoring Helpers:**
- _monitor_my()
- _monitor_team_or_division()
- _monitor_company()
- _enrich_monitor_data()

**Analysis Helpers:**
- _run_unified_analysis()
- _save_recommendations()

**Cache & Validation:**
- _invalidate_recommendations_cache()
- _get_preset_or_404()
- _get_active_preset_or_422()
- _get_profile_or_422()
- _get_cached_recommendations()
- _build_recommendations_response()

**Background Tasks:**
- _run_fetch_and_analyze()
- _queue_bid_analysis()
- _analyze_bid_background()
- _save_markdown_to_storage()

### 3. app/api/bids/handlers.py (Route Handlers)
**Team Bid Profile (2 endpoints):**
- get_bid_profile()
- upsert_bid_profile()

**Search Presets (5 endpoints):**
- list_search_presets()
- create_search_preset()
- update_search_preset()
- delete_search_preset()
- activate_search_preset()

**Team Operations (2 endpoints):**
- trigger_fetch()
- get_recommendations()

**Global Operations (13 endpoints):**
- list_announcements()
- pipeline_status()
- pipeline_trigger()
- get_scored_bids()
- manual_crawl()
- get_monitored_bids()
- update_bid_status()
- analyze_bid_for_proposal()
- toggle_bookmark()
- get_bid_detail()
- list_bid_attachments()
- download_bid_attachment()

### 4. app/api/bids/routes.py (Router Setup)
- Import all handlers and helpers
- Create APIRouter instance with "/api" prefix
- Register all 21 endpoints
- Export router for app/api/__init__.py

### 5. app/api/bids/__init__.py (Module Export)
```python
from .routes import router
__all__ = ["router"]
```

## 의존성 분석

### Internal Dependencies (모두 현재 routes_bids.py 내부):
- handlers → helpers, utils
- helpers → utils
- utils → 외부 라이브러리만

### External Dependencies:
- app.api.deps (get_current_user, get_current_user_or_none)
- app.api.permissions (require_team_member)
- app.api.response (ok, ok_list)
- app.models.bid_schemas
- app.services.domains.bidding.*
- app.utils.supabase_client

**순환 임포트 위험: 없음** ✅

## 구현 순서
1. ✅ Create app/api/bids/ folder
2. Create app/api/bids/utils.py (constants, caching, formatting)
3. Create app/api/bids/helpers.py (handler support functions)
4. Create app/api/bids/handlers.py (route endpoint functions)
5. Create app/api/bids/routes.py (router creation)
6. Create app/api/bids/__init__.py (module export)
7. Update app/api/__init__.py or app/main.py to import router
8. Delete routes_bids.py (after verification)
9. Test app startup
10. Run test suite to verify no regressions

## 검증 기준
- [ ] App starts without import errors
- [ ] All 21 endpoints accessible
- [ ] No circular import warnings
- [ ] All tests pass
- [ ] No performance regression

---
**Status**: Ready for implementation  
**Effort**: 2-3 hours (reading + splitting + testing)  
**Date**: 2026-04-24
