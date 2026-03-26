"""
사용자·조직·팀 관리 API (§12-7, Phase 0)

- 조직/본부/팀 CRUD (admin only)
- 사용자 관리 (admin only)
- 사용자 프로필 조회 (본인 + 같은 org)
- 결재 위임 관리
"""

import csv
import io
import logging

from fastapi import APIRouter, Depends, Query, UploadFile, File

from app.api.deps import get_current_user, require_role
from app.api.response import ok, ok_list
from app.exceptions import TenopAPIError
from app.utils.pagination import PageParams
from app.models.auth_schemas import CurrentUser
from app.models.user_schemas import (
    DelegationCreate,
    DivisionCreate,
    OrganizationCreate,
    ParticipantAdd,
    PasswordResetRequest,
    TeamCreate,
    TeamUpdate,
    UserCreateWithPassword,
    UserUpdate,
)
from app.services.audit_service import log_action
from app.services import user_account_service
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["users"])


# ══════════════════════════════════════════════
# 조직 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/admin/organizations")
async def create_organization(
    body: OrganizationCreate,
    user: CurrentUser = Depends(require_role("admin")),
):
    """조직 생성 (admin only)"""
    client = await get_async_client()
    res = await client.table("organizations").insert({"name": body.name}).execute()
    await log_action(user.id, "create", "organization", res.data[0]["id"])
    return ok(res.data[0])


@router.get("/admin/organizations")
async def list_organizations(user: CurrentUser = Depends(require_role("admin"))):
    """조직 목록 조회 (admin only)"""
    client = await get_async_client()
    res = await client.table("organizations").select("*").order("created_at").execute()
    return ok(res.data)


# ══════════════════════════════════════════════
# 본부 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/admin/divisions")
async def create_division(
    body: DivisionCreate,
    user: CurrentUser = Depends(require_role("admin")),
):
    """본부 생성 (admin only)"""
    client = await get_async_client()
    res = await client.table("divisions").insert({
        "name": body.name, "org_id": body.org_id,
    }).execute()
    await log_action(user.id, "create", "division", res.data[0]["id"])
    return ok(res.data[0])


@router.get("/admin/divisions")
async def list_divisions(
    org_id: str = Query(None),
    user: CurrentUser = Depends(require_role("admin")),
):
    """본부 목록 조회"""
    client = await get_async_client()
    query = client.table("divisions").select("*").order("created_at")
    if org_id:
        query = query.eq("org_id", org_id)
    res = await query.execute()
    return ok(res.data)


# ══════════════════════════════════════════════
# 팀 관리 (admin only)
# ══════════════════════════════════════════════

@router.post("/admin/teams")
async def create_team(
    body: TeamCreate,
    user: CurrentUser = Depends(require_role("admin")),
):
    """팀 생성 (admin only)"""
    client = await get_async_client()
    data = {"name": body.name, "division_id": body.division_id}
    if body.teams_webhook_url:
        data["teams_webhook_url"] = body.teams_webhook_url
    res = await client.table("teams").insert(data).execute()
    await log_action(user.id, "create", "team", res.data[0]["id"])
    return ok(res.data[0])


@router.get("/admin/teams")
async def list_teams(
    division_id: str = Query(None),
    user: CurrentUser = Depends(require_role("admin")),
):
    """팀 목록 조회"""
    client = await get_async_client()
    query = client.table("teams").select("*, divisions(name, org_id)").order("created_at")
    if division_id:
        query = query.eq("division_id", division_id)
    res = await query.execute()
    return ok(res.data)


@router.patch("/admin/teams/{team_id}")
async def update_team(
    team_id: str,
    body: TeamUpdate,
    user: CurrentUser = Depends(require_role("admin")),
):
    """팀 정보 수정"""
    client = await get_async_client()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise TenopAPIError("ADMIN_001", "수정할 항목이 없습니다.", 422)
    res = await client.table("teams").update(updates).eq("id", team_id).execute()
    if not res.data:
        raise TenopAPIError("ADMIN_002", "팀을 찾을 수 없습니다.", 404)
    await log_action(user.id, "update", "team", team_id, updates)
    return ok(res.data[0])


# ══════════════════════════════════════════════
# 사용자 관리
# ══════════════════════════════════════════════

@router.post("/admin/users")
async def create_user(
    body: UserCreateWithPassword,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 등록 (admin only) — Supabase Auth 계정 + users 행 동시 생성."""
    result = await user_account_service.create_auth_user(
        email=body.email,
        password=body.password,
        name=body.name,
        role=body.role,
        org_id=body.org_id,
        team_id=body.team_id,
        division_id=body.division_id,
    )
    await log_action(user.id, "create", "user", body.email)
    return ok({
        **result["user"],
        "temp_password": result["temp_password"],
    })


@router.post("/admin/users/bulk")
async def bulk_create_users(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role("admin")),
):
    """CSV 또는 XLSX 파일로 사용자 일괄 등록 (admin only).

    CSV 형식: email,name,role,team_id,division_id
    XLSX 형식: 헤더에 이메일/이름 컬럼 필수, 역할/팀/본부 선택
    """
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        rows = user_account_service.parse_xlsx_users(content)
    else:
        # CSV
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

    if not rows:
        raise TenopAPIError("ADMIN_001", "파일이 비어있거나 파싱할 수 없습니다.", 422)

    # team_name / division_name → team_id / division_id 변환
    needs_resolve = any(r.get("team_name") or r.get("division_name") for r in rows)
    if needs_resolve:
        client = await get_async_client()
        org_id = user.org_id

        # 본부명 → id 캐시
        div_res = await client.table("divisions").select("id, name").eq("org_id", org_id).execute()
        div_map = {d["name"]: d["id"] for d in (div_res.data or [])}

        # 팀명 → id 캐시
        team_res = await client.table("teams").select("id, name").execute()
        team_map = {t["name"]: t["id"] for t in (team_res.data or [])}

        for row in rows:
            if row.get("division_name") and not row.get("division_id"):
                row["division_id"] = div_map.get(row["division_name"])
            if row.get("team_name") and not row.get("team_id"):
                row["team_id"] = team_map.get(row["team_name"])

    result = await user_account_service.bulk_create_users(
        rows=rows,
        org_id=user.org_id,
    )
    await log_action(user.id, "bulk_create", "user", detail={
        "total": result["total"],
        "success": result["success_count"],
    })
    return ok(result)


@router.post("/admin/setup/bulk")
async def bulk_setup_org(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role("admin")),
):
    """XLSX 5개 시트(조직/본부/팀/사용자/역량) 일괄 등록 (admin only).

    tenopa team structure.xlsx 형식:
    - 1_조직: 조직명
    - 2_본부: 본부명, 소속 조직명
    - 3_팀: 팀명, 소속 본부명, 특화 분야, Teams Webhook URL
    - 4_사용자: 이메일, 이름, 직급, 역할, 소속 팀명, 소속 본부명, 소속 조직명
    - 5_역량: 유형, 제목, 상세 내용, 키워드, 소속 조직명
    """
    content = await file.read()
    filename = (file.filename or "").lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise TenopAPIError("ADMIN_001", "XLSX 파일만 지원합니다.", 422)

    parsed = user_account_service.parse_xlsx_all(content)
    if not parsed["users"]:
        raise TenopAPIError("ADMIN_001", "사용자 시트가 비어있습니다.", 422)

    result = await user_account_service.bulk_setup_org(parsed, org_id=user.org_id)
    await log_action(user.id, "bulk_setup_org", "organization", detail={
        "divisions": result["divisions"],
        "teams": result["teams"],
        "users_total": result["users"]["total"],
        "users_success": result["users"]["success_count"],
        "capabilities": result["capabilities"],
    })
    return ok(result)


@router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    body: PasswordResetRequest = PasswordResetRequest(),
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 비밀번호 초기화 (admin only)."""
    result = await user_account_service.reset_user_password(
        user_id=user_id,
        new_password=body.new_password,
    )
    await log_action(user.id, "reset_password", "user", user_id)
    return ok(result)


@router.get("/users")
async def list_users(
    role: str = Query(None),
    team_id: str = Query(None),
    status: str = Query("active"),
    pg: PageParams = Depends(),
    user: CurrentUser = Depends(get_current_user),
):
    """같은 조직 사용자 목록 조회."""
    client = await get_async_client()
    query = (
        client.table("users")
        .select("*", count="exact")
        .eq("org_id", user.org_id)
        .eq("status", status)
        .order("name")
    )
    if role:
        query = query.eq("role", role)
    if team_id:
        query = query.eq("team_id", team_id)

    query = pg.apply(query)
    res = await query.execute()

    return ok_list(res.data, total=res.count or len(res.data), offset=pg.offset, limit=pg.page_size)


@router.get("/users/{user_id}")
async def get_user(user_id: str, user: CurrentUser = Depends(get_current_user)):
    """사용자 프로필 조회 (같은 org)"""
    client = await get_async_client()
    res = (
        await client.table("users")
        .select("*")
        .eq("id", user_id)
        .eq("org_id", user.org_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise TenopAPIError("ADMIN_003", "사용자를 찾을 수 없습니다.", 404)
    return ok(res.data)


@router.patch("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdate,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 정보 수정 (admin only)"""
    client = await get_async_client()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise TenopAPIError("ADMIN_001", "수정할 항목이 없습니다.", 422)
    res = await client.table("users").update(updates).eq("id", user_id).execute()
    if not res.data:
        raise TenopAPIError("ADMIN_003", "사용자를 찾을 수 없습니다.", 404)
    await log_action(user.id, "update", "user", user_id, updates)
    return ok(res.data[0])


@router.post("/admin/users/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: str,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 비활성화 (admin only)"""
    from app.services.auth_service import deactivate_user
    result = await deactivate_user(user_id, reason="관리자에 의한 비활성화")
    return ok({"user": result}, message="사용자가 비활성화되었습니다.")


@router.delete("/admin/users/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    user: CurrentUser = Depends(require_role("admin", "executive")),
):
    """사용자 삭제 (admin/executive only). 본인 삭제 불가."""
    if user_id == user.id:
        from app.exceptions import InvalidRequestError
        raise InvalidRequestError("본인 계정은 삭제할 수 없습니다.")

    client = await get_async_client()
    # 사용자 존재 확인
    res = await client.table("users").select("id, name").eq("id", user_id).maybe_single().execute()
    if not res.data:
        from app.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("사용자")

    await client.table("users").delete().eq("id", user_id).execute()
    from app.services.audit_service import log_action
    await log_action(user.id, "delete", "user", user_id, {"deleted_name": res.data.get("name", "")})
    return ok(None, message="사용자가 삭제되었습니다.")


# ══════════════════════════════════════════════
# 프로젝트 참여자 관리
# ══════════════════════════════════════════════

@router.post("/proposals/{proposal_id}/participants")
async def add_participant(
    proposal_id: str,
    body: ParticipantAdd,
    user: CurrentUser = Depends(require_role("lead", "admin")),
):
    """프로젝트 참여자 추가 (팀장/admin)"""
    client = await get_async_client()
    res = await client.table("project_participants").insert({
        "proposal_id": proposal_id,
        "user_id": body.user_id,
        "role_in_project": body.role_in_project,
    }).execute()
    await log_action(user.id, "create", "participant", proposal_id, {"added_user": body.user_id})
    return ok(res.data[0] if res.data else None, message="참여자 추가 완료")


@router.get("/proposals/{proposal_id}/participants")
async def list_participants(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """프로젝트 참여자 목록"""
    client = await get_async_client()
    res = (
        await client.table("project_participants")
        .select("*, users(name, email, role)")
        .eq("proposal_id", proposal_id)
        .execute()
    )
    return ok(res.data)


@router.delete("/proposals/{proposal_id}/participants/{participant_user_id}")
async def remove_participant(
    proposal_id: str,
    participant_user_id: str,
    user: CurrentUser = Depends(require_role("lead", "admin")),
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
    await log_action(user.id, "delete", "participant", proposal_id, {"removed_user": participant_user_id})
    return ok(None, message="참여자가 제거되었습니다.")


# ══════════════════════════════════════════════
# 결재 위임 관리 (ULM-07)
# ══════════════════════════════════════════════

@router.post("/users/me/delegations")
async def create_delegation(
    body: DelegationCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """결재 위임 설정 (본인만)"""
    if user.role not in ("lead", "director", "executive"):
        raise TenopAPIError("AUTH_002", "결재 권한이 있는 역할만 위임 가능합니다.", 403)

    client = await get_async_client()
    res = await client.table("approval_delegations").insert({
        "delegator_id": user.id,
        "delegate_id": body.delegate_id,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "reason": body.reason,
    }).execute()
    await log_action(user.id, "create", "delegation", detail={"delegate": body.delegate_id})
    return ok(res.data[0] if res.data else None, message="위임 설정 완료")


@router.get("/users/me/delegations")
async def list_my_delegations(user: CurrentUser = Depends(get_current_user)):
    """내 위임 목록"""
    client = await get_async_client()
    res = (
        await client.table("approval_delegations")
        .select("*, users!approval_delegations_delegate_id_fkey(name, email)")
        .eq("delegator_id", user.id)
        .eq("is_active", True)
        .execute()
    )
    return ok(res.data)


@router.delete("/users/me/delegations/{delegation_id}")
async def cancel_delegation(
    delegation_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """위임 취소"""
    client = await get_async_client()
    await (
        client.table("approval_delegations")
        .update({"is_active": False})
        .eq("id", delegation_id)
        .eq("delegator_id", user.id)
        .execute()
    )
    return ok(None, message="위임이 취소되었습니다.")
