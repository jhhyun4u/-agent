"""
알림 서비스 (§18)

Teams Incoming Webhook + 인앱 알림.
승인 요청, 승인 결과, 마감 임박, AI 완료/오류 알림.
"""

import logging

import httpx

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


# ── Teams Webhook ──

async def send_teams_notification(
    team_id: str,
    title: str,
    body: str,
    link: str = "",
):
    """Teams Incoming Webhook으로 Adaptive Card 알림 발송."""
    # 팀별 Webhook URL 조회
    webhook_url = settings.teams_webhook_url
    try:
        client = await get_async_client()
        team = await client.table("teams").select("teams_webhook_url").eq("id", team_id).single().execute()
        if team.data and team.data.get("teams_webhook_url"):
            webhook_url = team.data["teams_webhook_url"]
    except Exception:
        pass

    if not webhook_url:
        logger.debug("Teams Webhook URL 미설정 — 알림 생략")
        return

    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": title, "weight": "bolder", "size": "medium"},
                    {"type": "TextBlock", "text": body, "wrap": True},
                ],
                "actions": (
                    [{"type": "Action.OpenUrl", "title": "바로 가기", "url": link}]
                    if link else []
                ),
            },
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.post(webhook_url, json=card)
            if resp.status_code != 200:
                logger.warning(f"Teams 알림 전송 실패: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Teams 알림 전송 오류: {e}")


# ── 인앱 알림 ──

async def create_notification(
    user_id: str,
    proposal_id: str | None,
    type: str,
    title: str,
    body: str = "",
    link: str = "",
):
    """인앱 알림 생성 (notifications 테이블)."""
    try:
        client = await get_async_client()
        await client.table("notifications").insert({
            "user_id": user_id,
            "proposal_id": proposal_id,
            "type": type,
            "title": title,
            "body": body,
            "link": link,
            "is_read": False,
            "teams_sent": False,
        }).execute()
    except Exception as e:
        logger.warning(f"인앱 알림 생성 실패: {e}")


# ── 복합 알림 (Teams + 인앱) ──

async def notify_approval_request(
    proposal_id: str,
    step: str,
    approver_id: str,
    team_id: str = "",
):
    """승인 요청 알림 (Teams + 인앱)."""
    try:
        client = await get_async_client()
        proposal = await client.table("proposals").select("project_name, team_id").eq("id", proposal_id).single().execute()
        approver = await client.table("users").select("name").eq("id", approver_id).single().execute()

        proposal_name = proposal.data.get("project_name", "") if proposal.data else ""
        approver_name = approver.data.get("name", "") if approver.data else ""
        tid = team_id or (proposal.data.get("team_id", "") if proposal.data else "")

        # 인앱 알림
        await create_notification(
            user_id=approver_id,
            proposal_id=proposal_id,
            type="approval_request",
            title=f"[승인 요청] {proposal_name}",
            body=f"{step} 단계 승인이 필요합니다.",
            link=f"/projects/{proposal_id}/review/{step}",
        )

        # Teams 알림
        await send_teams_notification(
            team_id=tid,
            title=f"승인 요청: {proposal_name}",
            body=f"{approver_name}님, {step} 단계 승인을 요청드립니다.",
            link=f"/projects/{proposal_id}/review/{step}",
        )
    except Exception as e:
        logger.warning(f"승인 요청 알림 실패: {e}")


async def notify_approval_result(
    proposal_id: str,
    step: str,
    result: str,
    target_user_ids: list[str] | None = None,
):
    """승인 결과 알림 (approved/rejected)."""
    try:
        client = await get_async_client()
        proposal = await client.table("proposals").select("project_name, created_by").eq("id", proposal_id).single().execute()
        proposal_name = proposal.data.get("project_name", "") if proposal.data else ""
        created_by = proposal.data.get("created_by", "") if proposal.data else ""

        status_text = "승인" if result == "approved" else "반려"
        users = target_user_ids or ([created_by] if created_by else [])

        for uid in users:
            await create_notification(
                user_id=uid,
                proposal_id=proposal_id,
                type="approval_result",
                title=f"[{status_text}] {proposal_name}",
                body=f"{step} 단계가 {status_text}되었습니다.",
                link=f"/projects/{proposal_id}",
            )
    except Exception as e:
        logger.warning(f"승인 결과 알림 실패: {e}")


async def notify_deadline_alert(
    proposal_id: str,
    days_left: int,
):
    """마감 임박 알림 (D-7, D-3, D-1)."""
    try:
        client = await get_async_client()
        proposal = await client.table("proposals").select("project_name, team_id").eq("id", proposal_id).single().execute()
        proposal_name = proposal.data.get("project_name", "") if proposal.data else ""
        team_id = proposal.data.get("team_id", "") if proposal.data else ""

        # 참여자 목록 조회
        participants = await client.table("project_teams").select("user_id").eq("proposal_id", proposal_id).execute()

        for p in (participants.data or []):
            await create_notification(
                user_id=p["user_id"],
                proposal_id=proposal_id,
                type="deadline",
                title=f"마감 D-{days_left}: {proposal_name}",
                body=f"제출 마감까지 {days_left}일 남았습니다.",
                link=f"/projects/{proposal_id}",
            )

        await send_teams_notification(
            team_id=team_id,
            title=f"마감 D-{days_left}: {proposal_name}",
            body=f"제출 마감까지 {days_left}일 남았습니다.",
            link=f"/projects/{proposal_id}",
        )
    except Exception as e:
        logger.warning(f"마감 알림 실패: {e}")


async def notify_ai_complete(
    proposal_id: str,
    step: str,
    created_by: str = "",
):
    """AI 작업 완료 알림 (NOTI-09)."""
    await create_notification(
        user_id=created_by,
        proposal_id=proposal_id,
        type="ai_complete",
        title=f"AI 작업 완료",
        body=f"{step} 단계 AI 생성이 완료되었습니다. 검토해 주세요.",
        link=f"/projects/{proposal_id}/review/{step}",
    )
