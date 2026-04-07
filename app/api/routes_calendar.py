"""RFP 일정 관리 API (Phase D)

GET    /api/calendar         — 목록 조회
POST   /api/calendar         — 일정 등록
PUT    /api/calendar/{id}    — 일정 수정/상태 변경
DELETE /api/calendar/{id}    — 일정 삭제

모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.api.response import ok, ok_list
from app.exceptions import InvalidRequestError, OwnershipRequiredError, ResourceNotFoundError
from app.models.auth_schemas import CurrentUser
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["calendar"])

VALID_STATUSES = ("open", "submitted", "won", "lost")


# ── 스키마 ────────────────────────────────────────────────────────────

class CalendarItem(BaseModel):
    id: str
    title: str
    agency: Optional[str]
    deadline: str          # ISO string
    proposal_id: Optional[str]
    status: str
    created_at: str


class CalendarCreate(BaseModel):
    title: str
    agency: Optional[str] = None
    deadline: str          # ISO datetime string
    proposal_id: Optional[str] = None


class CalendarUpdate(BaseModel):
    title: Optional[str] = None
    agency: Optional[str] = None
    deadline: Optional[str] = None
    proposal_id: Optional[str] = None
    status: Optional[str] = None


# ── 목록 조회 ─────────────────────────────────────────────────────────

@router.get("/calendar")
async def list_calendar(
    user: CurrentUser = Depends(get_current_user),
    scope: str = Query("personal", description="personal | team | company"),
    status: Optional[str] = Query(None, description="open | submitted | won | lost"),
):
    """RFP 일정 목록 조회 (deadline 오름차순)"""
    if status and status not in VALID_STATUSES:
        raise InvalidRequestError(f"status는 {', '.join(VALID_STATUSES)} 중 하나여야 합니다.")

    client = await get_async_client()

    query = client.table("rfp_calendar").select(
        "id, title, agency, deadline, proposal_id, status, owner_id, team_id, created_at"
    )

    if scope == "personal":
        query = query.eq("owner_id", user.id)
    elif scope == "team":
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)
    else:
        # company: 본인 소유 + 팀 소속
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)

    if status:
        query = query.eq("status", status)

    # deadline 오름차순 정렬 (null은 마지막)
    query = query.order("deadline", desc=False)

    res = await query.execute()
    items = res.data or []
    return ok_list(items, total=len(items))


# ── 등록 ─────────────────────────────────────────────────────────────

@router.post("/calendar", status_code=201)
async def create_calendar(body: CalendarCreate, user: CurrentUser = Depends(get_current_user)):
    """RFP 일정 등록"""
    # 현재 유저의 팀 조회 (team_id 자동 할당)
    client = await get_async_client()

    team_res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user.id)
        .limit(1)
        .execute()
    )
    team_id = team_res.data[0]["team_id"] if team_res.data else None

    item_id = str(uuid4())
    insert_data: dict = {
        "id": item_id,
        "owner_id": user.id,
        "title": body.title,
        "deadline": body.deadline,
        "status": "open",
    }
    if team_id:
        insert_data["team_id"] = team_id
    if body.agency:
        insert_data["agency"] = body.agency
    if body.proposal_id:
        insert_data["proposal_id"] = body.proposal_id

    await client.table("rfp_calendar").insert(insert_data).execute()

    return ok({"id": item_id, "title": body.title, "status": "open"})


# ── 수정 ─────────────────────────────────────────────────────────────

@router.put("/calendar/{item_id}")
async def update_calendar(
    item_id: str, body: CalendarUpdate, user: CurrentUser = Depends(get_current_user)
):
    """RFP 일정 수정 / 상태 변경 (소유자만)"""
    if body.status is not None and body.status not in VALID_STATUSES:
        raise InvalidRequestError(f"status는 {', '.join(VALID_STATUSES)} 중 하나여야 합니다.")

    client = await get_async_client()

    # 소유자 확인
    res = (
        await client.table("rfp_calendar")
        .select("owner_id")
        .eq("id", item_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise ResourceNotFoundError("일정")
    if res.data["owner_id"] != user.id:
        raise OwnershipRequiredError("본인 일정만 수정할 수 있습니다.")

    # None이 아닌 필드만 업데이트 (빈 문자열도 허용)
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise InvalidRequestError("수정할 필드가 없습니다.")

    await (
        client.table("rfp_calendar")
        .update(update_data)
        .eq("id", item_id)
        .eq("owner_id", user.id)
        .execute()
    )

    return ok({"id": item_id, **update_data})


# ── 삭제 ─────────────────────────────────────────────────────────────

@router.delete("/calendar/{item_id}", status_code=204)
async def delete_calendar(item_id: str, user: CurrentUser = Depends(get_current_user)):
    """RFP 일정 삭제 (소유자만)"""
    client = await get_async_client()

    res = (
        await client.table("rfp_calendar")
        .select("owner_id")
        .eq("id", item_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise ResourceNotFoundError("일정")
    if res.data["owner_id"] != user.id:
        raise OwnershipRequiredError("본인 일정만 삭제할 수 있습니다.")

    await (
        client.table("rfp_calendar")
        .delete()
        .eq("id", item_id)
        .eq("owner_id", user.id)
        .execute()
    )
