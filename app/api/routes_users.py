"""
사용자·조직·팀 관리 API (§12-7, Phase 0)

- 조직/본부/팀 CRUD (admin only)
- 사용자 관리 (admin only)
- 사용자 프로필 조회 (본인 + 같은 org)
- 결재 위임 관리
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_role
from app.exceptions import TenopAPIError
from app.models.user_schemas import (
    DelegationCreate,
    DivisionCreate,
    DivisionResponse,
    OrganizationCreate,
    OrganizationResponse,
    ParticipantAdd,
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.audit_service import log_action
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["users"])


# ══════════════════════════════════════════════
# 조직 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/api/admin/organizations", response_model=OrganizationResponse)
async def create_organization(
    body: OrganizationCreate,
    user: dict = Depends(require_role("admin")),
):
    """조직 생성 (admin only)"""
    client = await get_async_client()
    res = await client.table("organizations").insert({"name": body.name}).execute()
    await log_action(user["id"], "create", "organization", res.data[0]["id"])
    return res.data[0]


@router.get("/api/admin/organizations")
async def list_organizations(user: dict = Depends(require_role("admin"))):
    """조직 목록 조회 (admin only)"""
    client = await get_async_client()
    res = await client.table("organizations").select("*").order("created_at").execute()
    return res.data


# ══════════════════════════════════════════════
# 본부 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/api/admin/divisions", response_model=DivisionResponse)
async def create_division(
    body: DivisionCreate,
    user: dict = Depends(require_role("admin")),
):
    """본부 생성 (admin only)"""
    client = await get_async_client()
    res = await client.table("divisions").insert({
        "name": body.name, "org_id": body.org_id,
    }).execute()
    await log_action(user["id"], "create", "division", res.data[0]["id"])
    return res.data[0]


@router.get("/api/admin/divisions")
async def list_divisions(
    org_id: str = Query(None),
    user: dict = Depends(require_role("admin")),
):
    """본부 목록 조회"""
    client = await get_async_client()
    query = client.table("divisions").select("*").order("created_at")
    if org_id:
        query = query.eq("org_id", org_id)
    res = await query.execute()
    return res.data


# ══════════════════════════════════════════════
# 팀 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/api/admin/teams", response_model=TeamResponse)
async def create_team(
    body: TeamCreate,
    user: dict = Depends(require_role("admin")),
):
    """팀 생성 (admin only)"""
    client = await get_async_client()
    data = {"name": body.name, "division_id": body.division_id}
    if body.teams_webhook_url:
        data["teams_webhook_url"] = body.teams_webhook_url
    res = await client.table("teams").insert(data).execute()
    await log_action(user["id"], "create", "team", res.data[0]["id"])
    return res.data[0]


@router.get("/api/admin/teams")
async def list_teams(
    division_id: str = Query(None),
    user: dict = Depends(require_role("admin")),
):
    """팀 목록 조회"""
    client = await get_async_client()
    query = client.table("teams").select("*, divisions(name, org_id)").order("created_at")
    if division_id:
        query = query.eq("division_id", division_id)
    res = await query.execute()
    return res.data


@router.patch("/api/admin/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    body: TeamUpdate,
    user: dict = Depends(require_role("admin")),
):
    """팀 정보 수정"""
    client = await get_async_client()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise TenopAPIError("ADMIN_001", "수정할 항목이 없습니다.", 422)
    res = await client.table("teams").update(updates).eq("id", team_id).execute()
    if not res.data:
        raise TenopAPIError("ADMIN_002", "팀을 찾을 수 없습니다.", 404)
    await log_action(user["id"], "update", "team", team_id, updates)
    return res.data[0]


# ══════════════════════════════════════════════
# 사용자 관리
# ══════════════════════════════════════════════

@router.post("/api/admin/users", response_model=UserResponse)
async def create_user(
    body: UserCreate,
    user: dict = Depends(require_role("admin")),
):
    """사용자 사전 등록 (admin only).

    Azure AD OID를 미리 등록하면, 해당 사용자가 최초 로그인 시
    auth_service.get_or_create_user_profile에서 자동 매핑.
    """
    client = await get_async_client()
    data = body.model_dump(exclude_none=True)
    res = await client.table("users").insert(data).execute()
    await log_action(user["id"], "create", "user", data.get("email"))
    return res.data[0]


@router.get("/api/users", response_model=UserListResponse)
async def list_users(
    role: str = Query(None),
    team_id: str = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """같은 조직 사용자 목록 조회."""
    client = await get_async_client()
    query = (
        client.table("users")
        .select("*", count="exact")
        .eq("org_id", user["org_id"])
        .eq("status", status)
        .order("name")
    )
    if role:
        query = query.eq("role", role)
    if team_id:
        query = query.eq("team_id", team_id)

    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    res = await query.execute()

    return {
        "users": res.data,
        "total": res.count or len(res.data),
    }


@router.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, user: dict = Depends(get_current_user)):
    """사용자 프로필 조회 (같은 org)"""
    client = await get_async_client()
    res = (
        await client.table("users")
        .select("*")
        .eq("id", user_id)
        .eq("org_id", user["org_id"])
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise TenopAPIError("ADMIN_003", "사용자를 찾을 수 없습니다.", 404)
    return res.data


@router.patch("/api/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    user: dict = Depends(require_role("admin")),
):
    """사용자 정보 수정 (admin only)"""
    client = await get_async_client()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise TenopAPIError("ADMIN_001", "수정할 항목이 없습니다.", 422)
    res = await client.table("users").update(updates).eq("id", user_id).execute()
    if not res.data:
        raise TenopAPIError("ADMIN_003", "사용자를 찾을 수 없습니다.", 404)
    await log_action(user["id"], "update", "user", user_id, updates)
    return res.data[0]


@router.post("/api/admin/users/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: str,
    user: dict = Depends(require_role("admin")),
):
    """사용자 비활성화 (admin only)"""
    from app.services.auth_service import deactivate_user
    result = await deactivate_user(user_id, reason="관리자에 의한 비활성화")
    return {"message": "사용자가 비활성화되었습니다.", "user": result}


# ══════════════════════════════════════════════
# 프로젝트 참여자 관리
# ══════════════════════════════════════════════

@router.post("/api/proposals/{proposal_id}/participants")
async def add_participant(
    proposal_id: str,
    body: ParticipantAdd,
    user: dict = Depends(require_role("lead", "admin")),
):
    """프로젝트 참여자 추가 (팀장/admin)"""
    client = await get_async_client()
    res = await client.table("project_participants").insert({
        "proposal_id": proposal_id,
        "user_id": body.user_id,
        "role_in_project": body.role_in_project,
    }).execute()
    await log_action(user["id"], "create", "participant", proposal_id, {"added_user": body.user_id})
    return res.data[0] if res.data else {"message": "참여자 추가 완료"}


@router.get("/api/proposals/{proposal_id}/participants")
async def list_participants(
    proposal_id: str,
    user: dict = Depends(get_current_user),
):
    """프로젝트 참여자 목록"""
    client = await get_async_client()
    res = (
        await client.table("project_participants")
        .select("*, users(name, email, role)")
        .eq("proposal_id", proposal_id)
        .execute()
    )
    return res.data


@router.delete("/api/proposals/{proposal_id}/participants/{participant_user_id}")
async def remove_participant(
    proposal_id: str,
    participant_user_id: str,
    user: dict = Depends(require_role("lead", "admin")),
):
    """프로젝트 참여자 제거"""
    client = await get_async_client()
    await (
        client.table("project_participants")
        .delete()
        .eq("proposal_id", proposal_id)
        .eq("user_id", participant_user_id)
        .execute()
    )
    await log_action(user["id"], "delete", "participant", proposal_id, {"removed_user": participant_user_id})
    return {"message": "참여자가 제거되었습니다."}


# ══════════════════════════════════════════════
# 결재 위임 관리 (ULM-07)
# ══════════════════════════════════════════════

@router.post("/api/users/me/delegations")
async def create_delegation(
    body: DelegationCreate,
    user: dict = Depends(get_current_user),
):
    """결재 위임 설정 (본인만)"""
    if user["role"] not in ("lead", "director", "executive"):
        raise TenopAPIError("AUTH_002", "결재 권한이 있는 역할만 위임 가능합니다.", 403)

    client = await get_async_client()
    res = await client.table("approval_delegations").insert({
        "delegator_id": user["id"],
        "delegate_id": body.delegate_id,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "reason": body.reason,
    }).execute()
    await log_action(user["id"], "create", "delegation", detail={"delegate": body.delegate_id})
    return res.data[0] if res.data else {"message": "위임 설정 완료"}


@router.get("/api/users/me/delegations")
async def list_my_delegations(user: dict = Depends(get_current_user)):
    """내 위임 목록"""
    client = await get_async_client()
    res = (
        await client.table("approval_delegations")
        .select("*, users!approval_delegations_delegate_id_fkey(name, email)")
        .eq("delegator_id", user["id"])
        .eq("is_active", True)
        .execute()
    )
    return res.data


@router.delete("/api/users/me/delegations/{delegation_id}")
async def cancel_delegation(
    delegation_id: str,
    user: dict = Depends(get_current_user),
):
    """위임 취소"""
    client = await get_async_client()
    await (
        client.table("approval_delegations")
        .update({"is_active": False})
        .eq("id", delegation_id)
        .eq("delegator_id", user["id"])
        .execute()
    )
    return {"message": "위임이 취소되었습니다."}
