"""
결재선 서비스 (§17-2)

프로젝트 예산 기준 결재선 자동 구성:
- 3억 미만: [팀장]
- 3~5억: [팀장, 본부장]
- 5억 이상: [팀장, 본부장, 경영진]

임시 위임(ULM-07) 지원.
"""

import logging
from datetime import date

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def build_approval_chain(proposal_id: str, step: str) -> list[dict]:
    """프로젝트 예산 기준으로 결재선 구성."""
    client = await get_async_client()

    res = (
        await client.table("proposals")
        .select("budget_amount, team_id, division_id, org_id")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    proposal = res.data
    budget = proposal.get("budget_amount") or 0
    team_id = proposal["team_id"]
    division_id = proposal["division_id"]

    chain = []

    # 팀장 (항상 필요)
    lead = await _get_role_user("lead", team_id=team_id)
    if lead:
        actual_lead = await _check_delegation(lead["id"])
        chain.append({
            "role": "lead",
            "user_id": actual_lead["id"],
            "user_name": actual_lead["name"],
            "is_delegated": actual_lead["id"] != lead["id"],
            "original_user_id": lead["id"] if actual_lead["id"] != lead["id"] else None,
        })

    # 본부장 (3억 이상)
    if budget >= 300_000_000:
        director = await _get_role_user("director", division_id=division_id)
        if director:
            actual_director = await _check_delegation(director["id"])
            chain.append({
                "role": "director",
                "user_id": actual_director["id"],
                "user_name": actual_director["name"],
                "is_delegated": actual_director["id"] != director["id"],
                "original_user_id": director["id"] if actual_director["id"] != director["id"] else None,
            })

    # 경영진 (5억 이상)
    if budget >= 500_000_000:
        executive = await _get_role_user("executive")
        if executive:
            actual_exec = await _check_delegation(executive["id"])
            chain.append({
                "role": "executive",
                "user_id": actual_exec["id"],
                "user_name": actual_exec["name"],
                "is_delegated": actual_exec["id"] != executive["id"],
                "original_user_id": executive["id"] if actual_exec["id"] != executive["id"] else None,
            })

    return chain


async def check_can_approve(user: dict, proposal_id: str, step: str) -> bool:
    """현재 사용자가 이 단계를 승인할 권한이 있는지 확인."""
    chain = await build_approval_chain(proposal_id, step)
    return any(
        c["user_id"] == user["id"] for c in chain
    )


async def get_approval_status(proposal_id: str, step: str) -> dict:
    """결재선 현황 조회."""
    client = await get_async_client()
    chain = await build_approval_chain(proposal_id, step)

    approvals = (
        await client.table("approvals")
        .select("*")
        .eq("proposal_id", proposal_id)
        .eq("step", step)
        .execute()
    )
    approval_map = {a["approver_role"]: a for a in (approvals.data or [])}

    result = []
    for c in chain:
        approval = approval_map.get(c["role"])
        result.append({
            **c,
            "status": approval["decision"] if approval else "pending",
            "approved_at": approval["approved_at"] if approval else None,
        })

    all_approved = all(r["status"] == "approved" for r in result)
    any_rejected = any(r["status"] == "rejected" for r in result)

    return {
        "chain": result,
        "all_approved": all_approved,
        "any_rejected": any_rejected,
        "next_approver": next(
            (r for r in result if r["status"] == "pending"), None
        ),
    }


async def _get_role_user(
    role: str,
    team_id: str | None = None,
    division_id: str | None = None,
) -> dict | None:
    """역할별 담당자 조회."""
    client = await get_async_client()
    query = client.table("users").select("id, name, role, email").eq("role", role).eq("status", "active")

    if team_id:
        query = query.eq("team_id", team_id)
    if division_id:
        query = query.eq("division_id", division_id)

    res = await query.limit(1).execute()
    return res.data[0] if res.data else None


async def _check_delegation(user_id: str) -> dict:
    """임시 위임 확인 (ULM-07). 위임 중이면 대리인 반환."""
    client = await get_async_client()
    today = date.today().isoformat()

    res = (
        await client.table("approval_delegations")
        .select("delegate_id")
        .eq("delegator_id", user_id)
        .eq("is_active", True)
        .lte("start_date", today)
        .gte("end_date", today)
        .limit(1)
        .execute()
    )
    if res.data:
        delegate_id = res.data[0]["delegate_id"]
        delegate = (
            await client.table("users")
            .select("id, name, role, email")
            .eq("id", delegate_id)
            .single()
            .execute()
        )
        return delegate.data

    # 위임 없으면 원래 사용자 반환
    user = (
        await client.table("users")
        .select("id, name, role, email")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return user.data
