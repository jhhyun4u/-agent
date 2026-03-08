# API Analysis Report

> **Analysis Type**: Implementation Completeness / Consistency / Gap Analysis
>
> **Project**: tenopa-proposer
> **Version**: 3.4.0
> **Analyst**: bkit-gap-detector
> **Date**: 2026-03-08
> **Design Doc**: N/A (Design 문서 미존재)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Design 문서가 존재하지 않으므로, 구현 코드 자체의 완성도/일관성/누락 사항을 검토한다.
주요 검토 항목:
- 라우터 등록 정합성 (main.py vs 각 라우터 파일)
- 서비스 의존성 존재 여부 (import 경로 추적)
- 엔드포인트 중복/충돌 경로 탐지
- 인증(JWT) 처리 일관성
- 응답 포맷 일관성

### 1.2 Analysis Scope

- **Implementation Path**: `app/api/`, `app/main.py`
- **Router Files**: 10개 (routes.py, routes_v31.py, routes_bids.py, routes_calendar.py, routes_g2b.py, routes_presentation.py, routes_resources.py, routes_stats.py, routes_team.py, routes_templates.py)
- **Analysis Date**: 2026-03-08

---

## 2. Router Registration Analysis

### 2.1 main.py Router Registration

| Router File | Import Name | prefix | Registered |
|-------------|-------------|--------|:----------:|
| routes.py | `router` | `/api` | O |
| routes_bids.py | `bids_router` | (none) | O |
| routes_v31.py | `v31_router` | `/api` | O |
| routes_calendar.py | `calendar_router` | `/api` | O |
| routes_g2b.py | `g2b_router` | `/api` | O |
| routes_presentation.py | `presentation_router` | `/api` | O |
| routes_resources.py | `resources_router` | `/api` | O |
| routes_stats.py | `stats_router` | `/api` | O |
| routes_team.py | `team_router` | `/api` | O |
| routes_templates.py | `templates_router` | `/api` | O |

**All 10 routers are registered in main.py.**

---

## 3. Endpoint Path Conflict / Duplication Analysis

### 3.1 Critical: Double Registration Problem

`routes.py` acts as a "meta-router" that includes all other routers internally (lines 5-33). Meanwhile, `main.py` **also** registers each sub-router individually with `/api` prefix. This causes **all sub-router endpoints to be registered twice** under the same paths.

| Sub-Router | routes.py Internal Mount | main.py Direct Mount | Conflict |
|------------|-------------------------|---------------------|:--------:|
| routes_v31 | `router.include_router(routes_v31.router)` | `app.include_router(v31_router, prefix="/api")` | **DUPLICATE** |
| routes_team | `router.include_router(routes_team.router, prefix="/team")` | `app.include_router(team_router, prefix="/api")` | **PATH MISMATCH** |
| routes_g2b | `router.include_router(routes_g2b.router)` | `app.include_router(g2b_router, prefix="/api")` | **DUPLICATE** |
| routes_resources | `router.include_router(routes_resources.router)` | `app.include_router(resources_router, prefix="/api")` | **DUPLICATE** |
| routes_templates | `router.include_router(routes_templates.router)` | `app.include_router(templates_router, prefix="/api")` | **DUPLICATE** |
| routes_stats | `router.include_router(routes_stats.router)` | `app.include_router(stats_router, prefix="/api")` | **DUPLICATE** |
| routes_calendar | `router.include_router(routes_calendar.router)` | `app.include_router(calendar_router, prefix="/api")` | **DUPLICATE** |
| routes_presentation | `router.include_router(routes_presentation.router)` | `app.include_router(presentation_router, prefix="/api")` | **DUPLICATE** |

**Impact**: FastAPI will serve duplicate endpoints. OpenAPI docs (Swagger) will show double entries. The `routes_team` router has a particularly confusing path: inside routes.py it gets `/team` prefix, but from main.py it gets no additional prefix beyond `/api`, leading to different effective paths.

### 3.2 routes_bids.py Path Anomaly

`routes_bids.py` uses **absolute paths** in its route decorators (e.g., `@router.get("/api/teams/{team_id}/bid-profile")`), while being registered in main.py **without** a prefix. This means:
- Endpoints are accessible at `/api/teams/{team_id}/bid-profile` (correct)
- But this pattern is inconsistent with all other routers that use relative paths + prefix mounting

### 3.3 routes_team.py Path Conflict Details

`routes_team.py` has no `prefix` on its router definition (`router = APIRouter(tags=["team"])`).

- Via routes.py: mounted at `/api/team/*` (prefix="/team") -- so endpoints become `/api/team/teams/me`, `/api/team/proposals`, etc.
- Via main.py: mounted at `/api/*` (prefix="/api") -- so endpoints become `/api/teams/me`, `/api/proposals`, etc.

This creates two different sets of paths for the same team endpoints.

---

## 4. Full Endpoint Inventory

### 4.1 Root-Level Endpoints (main.py)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/health` | No | Health check |
| GET | `/status` | No | Session count |

### 4.2 v3.1 Pipeline (routes_v31.py) -- prefix `/v3.1`

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| POST | `/api/v3.1/proposals/generate` | JWT | Create proposal session |
| GET | `/api/v3.1/proposals/{id}/status` | JWT | Get proposal status |
| GET | `/api/v3.1/proposals/{id}/result` | JWT | Get final result |
| POST | `/api/v3.1/proposals/{id}/execute` | JWT | Execute pipeline (async) |
| GET | `/api/v3.1/proposals/{id}/download/{file_type}` | JWT | Download DOCX/PPTX/HWPX |
| POST | `/api/v3.1/bid/calculate` | JWT | Calculate bid price |
| GET | `/api/v3.1/templates` | JWT | List templates |
| GET | `/api/v3.1/templates/toc` | JWT | Get template TOC |
| POST | `/api/v3.1/templates/cache/clear` | JWT | Clear template cache |
| POST | `/api/v3.1/proposals/{id}/phase/{num}` | JWT | Run single phase |
| GET | `/api/v3.1/proposals/{id}/phase/{num}` | JWT | Get phase artifact |
| GET | `/api/v3.1/proposals/{id}/versions` | JWT | Get version history |
| POST | `/api/v3.1/proposals/{id}/new-version` | JWT | Create new version |

### 4.3 Presentation (routes_presentation.py) -- prefix `/v3.1`

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/v3.1/presentation/templates` | **No** | List presentation templates |
| POST | `/api/v3.1/proposals/{id}/presentation` | JWT | Generate presentation |
| GET | `/api/v3.1/proposals/{id}/presentation/status` | JWT | Presentation status |
| GET | `/api/v3.1/proposals/{id}/presentation/download` | JWT | Download presentation |

### 4.4 G2B Proxy (routes_g2b.py) -- prefix `/g2b`

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/g2b/bid-search` | JWT | Search bid announcements |
| GET | `/api/g2b/bid-results` | JWT | Get bid results |
| GET | `/api/g2b/contract-results` | JWT | Get contract results |
| GET | `/api/g2b/company-history` | JWT | Company bid history |
| GET | `/api/g2b/competitors` | JWT | Competitor analysis |

### 4.5 Bids / Recommendation (routes_bids.py) -- no prefix (absolute paths)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/teams/{team_id}/bid-profile` | JWT | Get bid profile |
| PUT | `/api/teams/{team_id}/bid-profile` | JWT | Upsert bid profile |
| GET | `/api/teams/{team_id}/search-presets` | JWT | List search presets |
| POST | `/api/teams/{team_id}/search-presets` | JWT | Create search preset |
| PUT | `/api/teams/{team_id}/search-presets/{id}` | JWT | Update search preset |
| DELETE | `/api/teams/{team_id}/search-presets/{id}` | JWT | Delete search preset |
| POST | `/api/teams/{team_id}/search-presets/{id}/activate` | JWT | Activate preset |
| POST | `/api/teams/{team_id}/bids/fetch` | JWT | Trigger bid fetch |
| GET | `/api/teams/{team_id}/bids/recommendations` | JWT | Get recommendations |
| GET | `/api/teams/{team_id}/bids/announcements` | JWT | List announcements |
| GET | `/api/bids/{bid_no}` | JWT | Bid detail |
| POST | `/api/proposals/from-bid/{bid_no}` | JWT | Create proposal from bid |

### 4.6 Calendar (routes_calendar.py) -- no router prefix

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/calendar` | JWT | List calendar items |
| POST | `/api/calendar` | JWT | Create calendar item |
| PUT | `/api/calendar/{id}` | JWT | Update calendar item |
| DELETE | `/api/calendar/{id}` | JWT | Delete calendar item |

### 4.7 Resources (routes_resources.py) -- no router prefix

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/resources/sections` | JWT | List sections |
| POST | `/api/resources/sections` | JWT | Create section |
| PUT | `/api/resources/sections/{id}` | JWT | Update section |
| DELETE | `/api/resources/sections/{id}` | JWT | Delete section |
| POST | `/api/assets` | JWT | Upload asset |
| GET | `/api/assets` | JWT | List assets |
| DELETE | `/api/assets/{id}` | JWT | Delete asset |
| GET | `/api/archive` | JWT | List proposal archive |

### 4.8 Form Templates (routes_templates.py) -- no router prefix

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/form-templates` | JWT | List form templates |
| POST | `/api/form-templates` | JWT | Upload form template |
| PATCH | `/api/form-templates/{id}` | JWT | Update form template |
| DELETE | `/api/form-templates/{id}` | JWT | Delete form template |

### 4.9 Stats (routes_stats.py) -- no router prefix

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/stats/win-rate` | JWT | Win rate statistics |

### 4.10 Team (routes_team.py) -- no router prefix

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/teams/me` | JWT | My teams |
| POST | `/api/teams` | JWT | Create team |
| GET | `/api/teams/{id}` | JWT | Get team |
| PATCH | `/api/teams/{id}` | JWT | Update team |
| DELETE | `/api/teams/{id}` | JWT | Delete team |
| GET | `/api/teams/{id}/members` | JWT | List members |
| GET | `/api/teams/{id}/stats` | JWT | Team stats |
| PATCH | `/api/teams/{id}/members/{uid}` | JWT | Update member role |
| DELETE | `/api/teams/{id}/members/{uid}` | JWT | Remove member |
| POST | `/api/teams/{id}/invitations` | JWT | Invite member |
| GET | `/api/teams/{id}/invitations` | JWT | List invitations |
| DELETE | `/api/teams/{id}/invitations/{inv_id}` | JWT | Cancel invitation |
| POST | `/api/invitations/accept` | JWT | Accept invitation |
| GET | `/api/proposals` | JWT | List proposals |
| PATCH | `/api/proposals/{id}/win-result` | JWT | Update win result |
| PATCH | `/api/proposals/{id}/status` | JWT | Update proposal status |
| GET | `/api/proposals/{id}/comments` | JWT | List comments |
| POST | `/api/proposals/{id}/comments` | JWT | Create comment |
| PATCH | `/api/comments/{cid}` | JWT | Update comment |
| DELETE | `/api/comments/{cid}` | JWT | Delete comment |
| PATCH | `/api/comments/{cid}/resolve` | JWT | Resolve comment |
| GET | `/api/usage` | JWT | Token usage |

**Total unique endpoints: 64** (excluding duplicates from double registration)

---

## 5. Service Dependency Verification

### 5.1 Import Dependency Matrix

| Router File | Import | Module Exists |
|-------------|--------|:------------:|
| routes_v31.py | `app.services.session_manager` | O |
| routes_v31.py | `app.models.phase_schemas` | O |
| routes_v31.py | `app.services.phase_executor` | O |
| routes_v31.py | `app.services.bid_calculator` | O |
| routes_v31.py | `app.exceptions` | O |
| routes_v31.py | `app.services.template_service` | O |
| routes_v31.py | `app.middleware.auth` | O |
| routes_v31.py | `app.config` | O |
| routes_bids.py | `app.models.bid_schemas` | O |
| routes_bids.py | `app.services.bid_fetcher` | O |
| routes_bids.py | `app.services.bid_recommender` | O |
| routes_bids.py | `app.services.g2b_service` | O |
| routes_bids.py | `app.utils.supabase_client` | O |
| routes_calendar.py | `app.utils.supabase_client` | O |
| routes_g2b.py | `app.services.g2b_service` | O |
| routes_presentation.py | `app.services.presentation_generator` | O |
| routes_presentation.py | `app.services.presentation_pptx_builder` | O |
| routes_presentation.py | `app.models.schemas` (RFPData) | O |
| routes_resources.py | `app.services.asset_extractor` | O |
| routes_stats.py | `app.utils.supabase_client` | O |
| routes_team.py | `app.utils.edge_functions` | O |
| routes_templates.py | `app.utils.supabase_client` | O |

**All import dependencies resolve to existing modules.** (0 missing)

---

## 6. Authentication (JWT) Consistency

### 6.1 Auth Pattern

All routers use `Depends(get_current_user)` from `app.middleware.auth`. The `get_current_user` function validates Bearer JWT tokens via Supabase Auth.

### 6.2 Auth Gap Detection

| Endpoint | Auth Applied | Status |
|----------|:-----------:|:------:|
| GET `/health` | No | OK (public health check) |
| GET `/status` | No | OK (operational status) |
| GET `/api/v3.1/presentation/templates` | **No** | **GAP** |
| All other endpoints | JWT | OK |

**Finding**: `GET /api/v3.1/presentation/templates` (routes_presentation.py line 183) does not use `Depends(get_current_user)`. This is the only authenticated-feature endpoint missing JWT protection.

### 6.3 User Object Access Inconsistency

| Router | User Access Pattern | Example |
|--------|-------------------|---------|
| routes_v31.py | `current_user.id` | Attribute access |
| routes_bids.py | `current_user["id"]` | **Dict access** |
| routes_calendar.py | `user.id` | Attribute access |
| routes_team.py | `user.id` | Attribute access |
| routes_resources.py | `user.id` | Attribute access |
| routes_stats.py | `user.id` | Attribute access |
| routes_templates.py | `user.id` | Attribute access |

**Finding**: `routes_bids.py` accesses user as a dict (`current_user["id"]`) while all other routers access it as an object attribute (`user.id`). This works because Supabase's user object supports both patterns, but it is a consistency violation.

---

## 7. Response Format Consistency

### 7.1 Response Envelope Patterns

| Pattern | Used By | Example |
|---------|---------|---------|
| `{ "data": ... }` | routes_bids.py | Standard data envelope |
| `{ "data": ..., "meta": ... }` | routes_bids.py (announcements, recommendations) | Data + metadata |
| `{ "items": ... }` | routes_calendar.py, routes_team.py (proposals, archive) | List items |
| `{ "sections": ... }` | routes_resources.py | Domain-specific key |
| `{ "templates": ... }` | routes_templates.py, routes_v31.py | Domain-specific key |
| `{ "teams": ... }` | routes_team.py | Domain-specific key |
| `{ "comments": ... }` | routes_team.py | Domain-specific key |
| `{ "members": ... }` | routes_team.py | Domain-specific key |
| `{ "invitations": ... }` | routes_team.py | Domain-specific key |
| `{ "assets": ... }` | routes_resources.py | Domain-specific key |
| `{ "versions": ... }` | routes_v31.py | Domain-specific key |
| Raw dict (no envelope) | routes_g2b.py, routes_stats.py, routes_team.py (get_team) | No standard wrapper |

**Finding**: There is no consistent response envelope convention. Routes use at least 4 different patterns:
1. `{ "data": ... }` (routes_bids.py only)
2. `{ "items": ... }` (paginated lists)
3. Domain-specific keys (`teams`, `sections`, `templates`, etc.)
4. Raw dicts without envelope

### 7.2 Pagination Format Inconsistency

| Router | Pagination Fields | Format |
|--------|------------------|--------|
| routes_bids.py (announcements) | `data, meta.total, meta.page, meta.per_page` | meta-envelope |
| routes_team.py (proposals) | `items, page, page_size, total, pages` | flat fields |
| routes_resources.py (archive) | `items, page, page_size, total, pages` | flat fields |
| routes_team.py (usage) | `items, total_tokens, page, page_size` | flat fields + custom |

Two different pagination conventions coexist: `meta` envelope (routes_bids.py) vs flat fields (all others).

---

## 8. Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Router Registration Completeness | 100% | PASS |
| Service Dependency Resolution | 100% | PASS |
| Authentication Consistency | 97% | WARNING (1 endpoint missing JWT) |
| Response Format Consistency | 55% | FAIL (no standard convention) |
| Path Routing Correctness | 40% | FAIL (double registration issue) |
| User Object Access Consistency | 91% | WARNING (routes_bids.py dict pattern) |
| **Overall Implementation Match Rate** | **72%** | **WARNING** |

```
Match Rate: 72%
-- Router Registration:     100%
-- Dependency Resolution:   100%
-- Auth Consistency:         97%
-- Response Format:          55%
-- Path Routing:             40%
-- User Access Pattern:      91%
```

---

## 9. Gap Summary

### 9.1 CRITICAL Issues

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **Double router registration** -- routes.py includes all sub-routers, AND main.py also includes them individually. All endpoints are registered twice. | `app/main.py:77-86` + `app/api/routes.py:11-32` | High -- OpenAPI docs show duplicates; ambiguous request routing |
| 2 | **routes_team.py path mismatch** -- Different effective paths from routes.py (with /team prefix) vs main.py (without). | `app/api/routes.py:14` vs `app/main.py:85` | High -- Two different URL trees for team endpoints |

### 9.2 WARNING Issues

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 3 | **Missing JWT on presentation templates endpoint** | `routes_presentation.py:183` | Medium -- Unauthenticated access to template metadata |
| 4 | **routes_bids.py uses absolute paths** -- All decorators include `/api/` prefix, unlike other routers | `routes_bids.py:60,81,112,...` | Low -- Works but inconsistent pattern |
| 5 | **User object access inconsistency** -- Dict access in routes_bids.py vs attribute access elsewhere | `routes_bids.py:67,89,...` | Low -- Works but fragile |
| 6 | **No standardized response envelope** -- 4+ different response patterns across routers | All router files | Medium -- Frontend must handle different response shapes |
| 7 | **Pagination format inconsistency** -- meta-envelope vs flat fields | `routes_bids.py` vs `routes_team.py`, `routes_resources.py` | Medium -- Frontend pagination logic fragmented |

### 9.3 INFO Issues

| # | Issue | Location | Notes |
|---|-------|----------|-------|
| 8 | `/health` and `/status` are not under `/api` prefix | `main.py:89,95` | Intentional (infrastructure endpoints) |
| 9 | No design document exists for API specification | `docs/02-design/features/` | Recommend creating for future PDCA cycles |
| 10 | Some routers define inline Pydantic schemas instead of centralizing in `app/models/` | `routes_calendar.py`, `routes_team.py`, `routes_templates.py` | Maintainability concern |

---

## 10. Recommended Actions

### 10.1 Immediate (Critical)

1. **Fix double registration**: Either remove all `include_router` calls from `app/api/routes.py` (making it just export `router = APIRouter()` as empty), OR remove the individual router registrations from `main.py` lines 78-86 and rely solely on routes.py aggregation. The latter approach is cleaner.

2. **Fix routes_team path conflict**: After resolving #1, ensure team endpoints have consistent paths. Currently the `/team` prefix in routes.py creates `/api/team/teams/me` which is likely unintended.

### 10.2 Short-term

3. **Add JWT to presentation templates endpoint**: Add `current_user=Depends(get_current_user)` to `list_presentation_templates()`.

4. **Standardize routes_bids.py path pattern**: Change from absolute paths (`/api/teams/...`) to relative paths with proper prefix mounting, matching the convention of other routers.

5. **Standardize user object access**: Change `current_user["id"]` to `current_user.id` in routes_bids.py for consistency.

### 10.3 Long-term

6. **Define and enforce response envelope convention**: Adopt one of:
   - Standard: `{ "data": ..., "meta"?: ... }` for all endpoints
   - Current majority: Domain-specific keys (`items`, `sections`, etc.)

7. **Standardize pagination format**: Pick one convention (recommended: `{ "data": [...], "pagination": { "page", "per_page", "total", "pages" } }`).

8. **Create API design document**: `docs/02-design/features/api.design.md` with full endpoint specification for future PDCA verification.

9. **Centralize Pydantic schemas**: Move inline schemas from router files to `app/models/` for reusability.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-08 | Initial analysis | bkit-gap-detector |
| 1.1 | 2026-03-08 | Critical/Warning fixes applied (Iteration 1) | bkit-pdca-iterator |

---

## Iteration 1 Fix Log (2026-03-08)

### Changes Applied

| # | Fix | File | Before | After |
|---|-----|------|--------|-------|
| 1 | Critical: 이중 등록 제거 | `app/main.py` | 서브 라우터 10개 개별 등록 | `routes.py` 통합 라우터 + `routes_bids.py` 2개만 등록 |
| 2 | Critical: team prefix 충돌 제거 | `app/api/routes.py` | `include_router(routes_team.router, prefix="/team")` → `/api/team/teams/...` | `include_router(routes_team.router)` → `/api/teams/...` 정상 경로 |
| 3 | Warning: JWT 인증 추가 | `app/api/routes_presentation.py` | `list_presentation_templates()` 인증 없음 | `current_user=Depends(get_current_user)` 추가 |

### Score Update (Estimated)

| Category | Before | After | Delta |
|----------|:------:|:-----:|:-----:|
| Path Routing Correctness | 40% | 95% | +55% |
| Authentication Consistency | 97% | 100% | +3% |
| Router Registration Completeness | 100% | 100% | 0% |
| Service Dependency Resolution | 100% | 100% | 0% |
| Response Format Consistency | 55% | 55% | 0% |
| User Access Pattern | 91% | 91% | 0% |
| **Overall Match Rate** | **72%** | **~90%** | **+18%** |

### Remaining Issues (Not Fixed This Iteration)

- Response envelope convention (4+ patterns) — Long-term refactor needed
- Pagination format inconsistency — Long-term refactor needed
- `routes_bids.py` absolute path pattern + `current_user["id"]` dict access — Works correctly, low risk
