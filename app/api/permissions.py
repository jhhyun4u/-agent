"""
공유 권한 체크 헬퍼 (팀 멤버십, 제안서 접근)

routes_team.py, routes_bids.py 등에서 중복되던 로직 통합.
"""

from typing import Optional

from app.exceptions import PropNotFoundError, TeamAccessDeniedError


async def get_team_member_role(client, team_id: str, user_id: str) -> Optional[str]:
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


async def require_team_member(client, team_id: str, user_id: str) -> str:
    """팀 멤버 확인. 미소속이면 403. 역할 문자열 반환."""
    role = await get_team_member_role(client, team_id, user_id)
    if role is None:
        raise TeamAccessDeniedError()
    return role


async def require_team_admin(client, team_id: str, user_id: str):
    """팀 관리자 확인. admin이 아니면 403."""
    role = await get_team_member_role(client, team_id, user_id)
    if role != "admin":
        raise TeamAccessDeniedError("팀 관리자만 가능합니다.")


async def get_user_team_ids(client, user_id: str) -> list[str]:
    """사용자 소속 팀 ID 목록 반환."""
    res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user_id)
        .execute()
    )
    return [r["team_id"] for r in (res.data or [])]


async def can_access_proposal(client, proposal_id: str, user_id: str) -> dict:
    """소유자이거나 팀 멤버이면 제안서 dict 반환, 아니면 403."""
    res = (
        await client.table("proposals")
        .select("*")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise PropNotFoundError(proposal_id)
    proposal = res.data
    if proposal["owner_id"] == user_id:
        return proposal
    if proposal.get("team_id"):
        role = await get_team_member_role(client, proposal["team_id"], user_id)
        if role:
            return proposal
    raise TeamAccessDeniedError("접근 권한이 없습니다.")
