"""팀 협업 API (Phase E)

팀 CRUD, 팀원 관리, 초대, 댓글, 수주결과, 제안서 목록.
모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.utils.supabase_client import get_async_client
from app.utils.edge_functions import notify_comment_created

logger = logging.getLogger(__name__)
router = APIRouter(tags=["team"])


# ── 헬퍼 ──────────────────────────────────────────────────────────────

async def _get_member_role(client, team_id: str, user_id: str) -> Optional[str]:
    """팀에서 사용자 역할 반환. 미소속이면 None."""
    res = (
        await client.table("team_members")
        .select("role")
        .eq("team_id", team_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return res.data["role"] if res.data else None


async def _require_team_admin(client, team_id: str, user_id: str):
    role = await _get_member_role(client, team_id, user_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="팀 관리자만 가능합니다.")


async def _require_team_member(client, team_id: str, user_id: str):
    role = await _get_member_role(client, team_id, user_id)
    if role is None:
        raise HTTPException(status_code=403, detail="팀 멤버만 접근 가능합니다.")


async def _can_access_proposal(client, proposal_id: str, user_id: str) -> dict:
    """소유자이거나 팀 멤버이면 제안서 dict 반환, 아니면 403."""
    res = (
        await client.table("proposals")
        .select("*")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다.")
    proposal = res.data
    if proposal["owner_id"] == user_id:
        return proposal
    if proposal.get("team_id"):
        role = await _get_member_role(client, proposal["team_id"], user_id)
        if role:
            return proposal
    raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")


# ── 팀 ───────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str


@router.get("/teams/me")
async def list_my_teams(user=Depends(get_current_user)):
    """내가 속한 팀 목록"""
    client = await get_async_client()
    res = (
        await client.table("team_members")
        .select("team_id, role, teams(id, name, created_at)")
        .eq("user_id", user.id)
        .execute()
    )
    return {"teams": res.data or []}


@router.post("/teams", status_code=201)
async def create_team(body: TeamCreate, user=Depends(get_current_user)):
    """팀 생성 (본인을 admin으로 자동 추가)"""
    client = await get_async_client()
    team_id = str(uuid4())
    await client.table("teams").insert(
        {"id": team_id, "name": body.name, "created_by": user.id}
    ).execute()
    await client.table("team_members").insert(
        {"team_id": team_id, "user_id": user.id, "role": "admin"}
    ).execute()
    return {"team_id": team_id, "name": body.name}


@router.get("/teams/{team_id}")
async def get_team(team_id: str, user=Depends(get_current_user)):
    """팀 상세 조회"""
    client = await get_async_client()
    await _require_team_member(client, team_id, user.id)
    res = (
        await client.table("teams").select("*").eq("id", team_id).maybe_single().execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    return res.data


@router.patch("/teams/{team_id}")
async def update_team(team_id: str, body: TeamUpdate, user=Depends(get_current_user)):
    """팀 이름 변경 (admin only)"""
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    await client.table("teams").update({"name": body.name}).eq("id", team_id).execute()
    return {"team_id": team_id, "name": body.name}


@router.delete("/teams/{team_id}", status_code=204)
async def delete_team(team_id: str, user=Depends(get_current_user)):
    """팀 삭제 (admin only)"""
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    await client.table("teams").delete().eq("id", team_id).execute()


# ── 팀원 ─────────────────────────────────────────────────────────────

class MemberRoleUpdate(BaseModel):
    role: str  # 'admin' | 'member'


@router.get("/teams/{team_id}/members")
async def list_team_members(team_id: str, user=Depends(get_current_user)):
    """팀원 목록"""
    client = await get_async_client()
    await _require_team_member(client, team_id, user.id)
    res = (
        await client.table("team_members")
        .select("*")
        .eq("team_id", team_id)
        .execute()
    )
    return {"members": res.data or []}


@router.patch("/teams/{team_id}/members/{target_user_id}")
async def update_member_role(
    team_id: str,
    target_user_id: str,
    body: MemberRoleUpdate,
    user=Depends(get_current_user),
):
    """역할 변경 (admin only)"""
    if body.role not in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail="role은 admin, member, viewer 중 하나여야 합니다.")
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    await (
        client.table("team_members")
        .update({"role": body.role})
        .eq("team_id", team_id)
        .eq("user_id", target_user_id)
        .execute()
    )
    return {"team_id": team_id, "user_id": target_user_id, "role": body.role}


@router.delete("/teams/{team_id}/members/{target_user_id}", status_code=204)
async def remove_team_member(
    team_id: str, target_user_id: str, user=Depends(get_current_user)
):
    """팀원 제거 (admin only 또는 본인 탈퇴)"""
    client = await get_async_client()
    if target_user_id != user.id:
        await _require_team_admin(client, team_id, user.id)
    else:
        await _require_team_member(client, team_id, user.id)
    await (
        client.table("team_members")
        .delete()
        .eq("team_id", team_id)
        .eq("user_id", target_user_id)
        .execute()
    )


# ── 초대 ─────────────────────────────────────────────────────────────

class InvitationCreate(BaseModel):
    email: str
    role: str = "member"


class InvitationAccept(BaseModel):
    invitation_id: str


@router.post("/teams/{team_id}/invitations", status_code=201)
async def invite_member(
    team_id: str, body: InvitationCreate, user=Depends(get_current_user)
):
    """팀원 초대 (admin only). 실제 이메일은 Supabase Edge Function에서 발송."""
    if body.role not in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail="role은 admin, member, viewer 중 하나여야 합니다.")
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    inv_id = str(uuid4())
    try:
        await client.table("invitations").insert(
            {
                "id": inv_id,
                "team_id": team_id,
                "email": body.email,
                "role": body.role,
                "invited_by": user.id,
            }
        ).execute()
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="이미 초대된 이메일입니다.")
        raise HTTPException(status_code=500, detail=str(e))
    return {"invitation_id": inv_id, "email": body.email, "role": body.role, "status": "pending"}


@router.get("/teams/{team_id}/invitations")
async def list_invitations(team_id: str, user=Depends(get_current_user)):
    """초대 목록 (admin only)"""
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    res = (
        await client.table("invitations").select("*").eq("team_id", team_id).execute()
    )
    return {"invitations": res.data or []}


@router.delete("/teams/{team_id}/invitations/{invitation_id}", status_code=204)
async def cancel_invitation(
    team_id: str, invitation_id: str, user=Depends(get_current_user)
):
    """초대 취소 (admin only)"""
    client = await get_async_client()
    await _require_team_admin(client, team_id, user.id)
    await (
        client.table("invitations")
        .delete()
        .eq("id", invitation_id)
        .eq("team_id", team_id)
        .execute()
    )


@router.post("/invitations/accept")
async def accept_invitation(body: InvitationAccept, user=Depends(get_current_user)):
    """초대 수락: invitation_id로 팀에 합류"""
    client = await get_async_client()

    res = (
        await client.table("invitations")
        .select("*")
        .eq("id", body.invitation_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="초대를 찾을 수 없습니다.")
    inv = res.data

    if inv["status"] != "pending":
        raise HTTPException(status_code=409, detail="이미 처리된 초대입니다.")

    # 초대 이메일 vs 로그인 계정 확인
    user_email = getattr(user, "email", "") or ""
    if inv["email"].lower() != user_email.lower():
        raise HTTPException(status_code=403, detail="초대 이메일과 로그인 계정이 다릅니다.")

    # 만료 확인
    expires_at_str = inv.get("expires_at", "")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            await (
                client.table("invitations")
                .update({"status": "expired"})
                .eq("id", body.invitation_id)
                .execute()
            )
            raise HTTPException(status_code=410, detail="만료된 초대입니다.")

    # 팀 합류
    try:
        await client.table("team_members").insert(
            {
                "team_id": inv["team_id"],
                "user_id": user.id,
                "role": inv.get("role", "member"),
            }
        ).execute()
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="이미 팀에 속해 있습니다.")
        raise HTTPException(status_code=500, detail=str(e))

    await (
        client.table("invitations")
        .update({"status": "accepted"})
        .eq("id", body.invitation_id)
        .execute()
    )
    return {"team_id": inv["team_id"], "role": inv.get("role", "member"), "message": "팀에 합류했습니다."}


# ── 댓글 ─────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    body: Optional[str] = None  # 설계 명세: body 필드
    content: Optional[str] = None  # 하위 호환성 (기존 클라이언트 지원)
    section: Optional[str] = None  # 제안서 섹션 참조


class CommentUpdate(BaseModel):
    content: str


@router.get("/proposals/{proposal_id}/comments")
async def list_comments(proposal_id: str, user=Depends(get_current_user)):
    """제안서 댓글 목록"""
    client = await get_async_client()
    await _can_access_proposal(client, proposal_id, user.id)
    res = (
        await client.table("comments")
        .select("*")
        .eq("proposal_id", proposal_id)
        .order("created_at")
        .execute()
    )
    return {"comments": res.data or []}


@router.post("/proposals/{proposal_id}/comments", status_code=201)
async def create_comment(
    proposal_id: str, body: CommentCreate, background_tasks: BackgroundTasks, user=Depends(get_current_user)
):
    """댓글 작성"""
    client = await get_async_client()
    await _can_access_proposal(client, proposal_id, user.id)
    comment_id = str(uuid4())
    # body 필드 우선, content는 하위 호환성 폴백
    comment_text = body.body or body.content or ""
    if not comment_text:
        raise HTTPException(status_code=400, detail="body 또는 content 필드가 필요합니다.")
    insert_data = {
        "id": comment_id,
        "proposal_id": proposal_id,
        "user_id": user.id,
        "content": comment_text,
    }
    if body.section:
        insert_data["section"] = body.section
    await client.table("comments").insert(insert_data).execute()

    # 팀원 알림 이메일 (BackgroundTasks, 실패해도 무시)
    background_tasks.add_task(notify_comment_created, comment_id)

    return {"comment_id": comment_id, "body": comment_text, "section": body.section}


@router.patch("/comments/{comment_id}")
async def update_comment(
    comment_id: str, body: CommentUpdate, user=Depends(get_current_user)
):
    """댓글 수정 (본인만)"""
    client = await get_async_client()
    res = (
        await client.table("comments")
        .select("user_id")
        .eq("id", comment_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if res.data["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 수정할 수 있습니다.")
    await client.table("comments").update({"content": body.content}).eq("id", comment_id).execute()
    return {"comment_id": comment_id, "content": body.content}


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(comment_id: str, user=Depends(get_current_user)):
    """댓글 삭제 (본인만)"""
    client = await get_async_client()
    res = (
        await client.table("comments")
        .select("user_id")
        .eq("id", comment_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if res.data["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 삭제할 수 있습니다.")
    await client.table("comments").delete().eq("id", comment_id).execute()


# ── 제안서 목록 + 수주결과 ────────────────────────────────────────────

class WinResultUpdate(BaseModel):
    win_result: str  # 'won' | 'lost' | 'pending'
    bid_amount: Optional[int] = None
    notes: Optional[str] = None


@router.get("/proposals")
async def list_proposals(
    user=Depends(get_current_user),
    q: Optional[str] = Query(None, description="제목 검색"),
    status: Optional[str] = Query(None, description="상태 필터"),
    team_id: Optional[str] = Query(None, description="팀 필터"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """내 제안서 목록 (검색, 필터, 페이지네이션)"""
    client = await get_async_client()

    # 내가 속한 팀 ID 목록
    team_res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user.id)
        .execute()
    )
    my_team_ids = [r["team_id"] for r in (team_res.data or [])]

    query = client.table("proposals").select(
        "id, title, status, owner_id, team_id, current_phase, "
        "phases_completed, win_result, bid_amount, created_at, updated_at"
    )

    # 소유자 또는 팀 멤버 조건
    if my_team_ids:
        team_ids_csv = ",".join(my_team_ids)
        query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
    else:
        query = query.eq("owner_id", user.id)

    if q:
        q_safe = q.replace("%", r"\%").replace("_", r"\_")
        query = query.ilike("title", f"%{q_safe}%")
    if status:
        query = query.eq("status", status)
    if team_id:
        query = query.eq("team_id", team_id)

    # 전체 건수 조회 (count 파라미터 사용)
    count_query = client.table("proposals").select("id", count="exact")
    if my_team_ids:
        team_ids_csv = ",".join(my_team_ids)
        count_query = count_query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
    else:
        count_query = count_query.eq("owner_id", user.id)
    if q:
        count_query = count_query.ilike("title", f"%{q_safe}%")
    if status:
        count_query = count_query.eq("status", status)
    if team_id:
        count_query = count_query.eq("team_id", team_id)
    count_res = await count_query.execute()
    total = count_res.count if hasattr(count_res, "count") and count_res.count is not None else len(count_res.data or [])

    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

    res = await query.execute()
    pages = math.ceil(total / page_size) if page_size > 0 else 1
    return {
        "items": res.data or [],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }


@router.patch("/proposals/{proposal_id}/win-result")
async def update_win_result(
    proposal_id: str, body: WinResultUpdate, user=Depends(get_current_user)
):
    """수주/낙찰 결과 저장"""
    if body.win_result not in ("won", "lost", "pending"):
        raise HTTPException(
            status_code=400, detail="win_result는 won, lost, pending 중 하나여야 합니다."
        )
    client = await get_async_client()
    proposal = await _can_access_proposal(client, proposal_id, user.id)

    # 소유자 또는 팀 admin만 수주 결과 변경 가능 (require_role_or_owner)
    if proposal["owner_id"] != user.id and proposal.get("team_id"):
        role = await _get_member_role(client, proposal["team_id"], user.id)
        if role != "admin":
            raise HTTPException(status_code=403, detail="제안서 소유자 또는 팀 관리자만 수주 결과를 변경할 수 있습니다.")

    update_data: dict = {"win_result": body.win_result}
    if body.bid_amount is not None:
        update_data["bid_amount"] = body.bid_amount
    if body.notes is not None:
        update_data["notes"] = body.notes

    await client.table("proposals").update(update_data).eq("id", proposal_id).execute()
    return {"proposal_id": proposal_id, **update_data}


# ── 제안서 상태 변경 ──────────────────────────────────────────────────

class ProposalStatusUpdate(BaseModel):
    status: str  # 'reviewing' | 'approved' | 'pending' | 'failed'


@router.patch("/proposals/{proposal_id}/status")
async def update_proposal_status(
    proposal_id: str, body: ProposalStatusUpdate, user=Depends(get_current_user)
):
    """제안서 상태 변경 (owner 또는 팀 admin)"""
    allowed_statuses = ("pending", "reviewing", "approved", "completed", "failed", "processing")
    if body.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"status는 {', '.join(allowed_statuses)} 중 하나여야 합니다.",
        )
    client = await get_async_client()
    proposal = await _can_access_proposal(client, proposal_id, user.id)

    # 팀 제안서이면 admin/owner만 상태 변경 가능
    if proposal.get("team_id"):
        role = await _get_member_role(client, proposal["team_id"], user.id)
        if role not in ("admin",) and proposal["owner_id"] != user.id:
            raise HTTPException(status_code=403, detail="제안서 소유자 또는 팀 관리자만 상태를 변경할 수 있습니다.")

    await client.table("proposals").update({"status": body.status}).eq("id", proposal_id).execute()
    return {"proposal_id": proposal_id, "status": body.status}


# ── 댓글 resolve ──────────────────────────────────────────────────────

@router.patch("/comments/{comment_id}/resolve")
async def resolve_comment(comment_id: str, user=Depends(get_current_user)):
    """댓글 resolve 처리 (토글). 제안서 접근 권한이 있는 팀 멤버 가능."""
    client = await get_async_client()

    # 댓글 조회 (proposal_id 확인용)
    res = (
        await client.table("comments")
        .select("id, proposal_id, resolved")
        .eq("id", comment_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    comment = res.data

    # 제안서 접근 권한 확인
    await _can_access_proposal(client, comment["proposal_id"], user.id)

    new_resolved = not comment.get("resolved", False)
    await client.table("comments").update({"resolved": new_resolved}).eq("id", comment_id).execute()
    return {"comment_id": comment_id, "resolved": new_resolved}


# ── 사용량 조회 ────────────────────────────────────────────────────────

@router.get("/usage")
async def get_usage(
    user=Depends(get_current_user),
    proposal_id: Optional[str] = Query(None, description="특정 제안서 필터"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """토큰 사용량 조회 (본인 제안서 기준)"""
    client = await get_async_client()

    # 내가 접근 가능한 proposal_id 목록 조회
    team_res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user.id)
        .execute()
    )
    my_team_ids = [r["team_id"] for r in (team_res.data or [])]

    proposal_query = client.table("proposals").select("id")
    if my_team_ids:
        team_ids_csv = ",".join(my_team_ids)
        proposal_query = proposal_query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
    else:
        proposal_query = proposal_query.eq("owner_id", user.id)

    proposal_res = await proposal_query.execute()
    accessible_ids = [r["id"] for r in (proposal_res.data or [])]

    if not accessible_ids:
        return {"items": [], "total_tokens": 0, "page": page, "page_size": page_size}

    query = client.table("usage_logs").select("*")

    if proposal_id:
        if proposal_id not in accessible_ids:
            raise HTTPException(status_code=403, detail="접근 권한이 없는 제안서입니다.")
        query = query.eq("proposal_id", proposal_id)
    else:
        ids_csv = ",".join(accessible_ids)
        query = query.in_("proposal_id", accessible_ids)

    offset = (page - 1) * page_size
    query = query.order("logged_at", desc=True).range(offset, offset + page_size - 1)

    res = await query.execute()
    items = res.data or []
    total_tokens = sum(r.get("total_tokens", 0) for r in items)

    return {
        "items": items,
        "total_tokens": total_tokens,
        "page": page,
        "page_size": page_size,
    }
