"""
알림 서비스 (§18)

Teams Incoming Webhook + 인앱 알림 + 이메일 (옵트인).
승인 요청, 승인 결과, 마감 임박, AI 완료/오류 알림.
"""

import logging

import httpx

from app.config import settings
from app.services.core.email_service import build_email_html, send_email
from app.services.core.ws_events import broadcast_notification
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


# ── 이메일 옵트인 확인 헬퍼 ──

async def _get_user_email_info(user_id: str) -> dict:
    """사용자 이메일 + 알림 설정 조회."""
    try:
        client = await get_async_client()
        result = await (
            client.table("users")
            .select("notification_settings, email")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            return {"settings": {}, "email": ""}
        return {
            "settings": result.data.get("notification_settings") or {},
            "email": result.data.get("email") or "",
        }
    except Exception as e:
        logger.debug(f"사용자 이메일 정보 조회 실패 ({user_id}): {e}")
        return {"settings": {}, "email": ""}


def _should_send_email(user_data: dict, setting_key: str) -> bool:
    """특정 이메일 알림 유형이 옵트인 되어있는지 확인."""
    if not settings.email_enabled:
        return False
    s = user_data.get("settings", {})
    return bool(s.get(setting_key, False)) and bool(user_data.get("email"))


async def _try_send_email(user_id: str, setting_key: str, subject: str, title: str, body: str, link: str = "") -> None:
    """사용자의 옵트인 확인 후 이메일 발송 (fire-and-forget)."""
    user_data = await _get_user_email_info(user_id)
    if not _should_send_email(user_data, setting_key):
        return
    html = build_email_html(title, body, link)
    await send_email(user_data["email"], subject, html)


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
        async with httpx.AsyncClient(timeout=float(settings.webhook_timeout_seconds)) as http:
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
        result = await client.table("notifications").insert({
            "user_id": user_id,
            "proposal_id": proposal_id,
            "type": type,
            "title": title,
            "body": body,
            "link": link,
            "is_read": False,
            "teams_sent": False,
        }).execute()

        # WebSocket 브로드캐스트 (fire-and-forget)
        if result.data and len(result.data) > 0:
            notification_id = result.data[0].get("id")
            import asyncio
            asyncio.create_task(
                broadcast_notification(
                    user_id=user_id,
                    notification_id=notification_id,
                    type=type,
                    title=title,
                    message=body,
                    link=link,
                )
            )
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
        proposal = await client.table("proposals").select("title, team_id").eq("id", proposal_id).single().execute()
        approver = await client.table("users").select("name").eq("id", approver_id).single().execute()

        proposal_name = proposal.data.get("title", "") if proposal.data else ""
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

        # 이메일 (옵트인)
        await _try_send_email(
            approver_id, "email_proposal",
            f"[승인 요청] {proposal_name}",
            f"승인 요청: {proposal_name}",
            f"{step} 단계 승인이 필요합니다.",
            f"{settings.frontend_url}/projects/{proposal_id}/review/{step}",
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
        proposal = await client.table("proposals").select("title, owner_id").eq("id", proposal_id).single().execute()
        proposal_name = proposal.data.get("title", "") if proposal.data else ""
        created_by = proposal.data.get("owner_id", "") if proposal.data else ""

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
            # 이메일 (옵트인)
            await _try_send_email(
                uid, "email_proposal",
                f"[{status_text}] {proposal_name}",
                f"승인 {status_text}: {proposal_name}",
                f"{step} 단계가 {status_text}되었습니다.",
                f"{settings.frontend_url}/projects/{proposal_id}",
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
        proposal = await client.table("proposals").select("title, team_id").eq("id", proposal_id).single().execute()
        proposal_name = proposal.data.get("title", "") if proposal.data else ""
        team_id = proposal.data.get("team_id", "") if proposal.data else ""

        # 참여자 목록 조회
        participants = await client.table("project_participants").select("user_id").eq("proposal_id", proposal_id).execute()

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

        # 이메일 (옵트인, D-3/D-1만)
        if days_left <= 3:
            for p in (participants.data or []):
                await _try_send_email(
                    p["user_id"], "email_monitoring",
                    f"[마감 D-{days_left}] {proposal_name}",
                    f"마감 D-{days_left}: {proposal_name}",
                    f"제출 마감까지 {days_left}일 남았습니다.",
                    f"{settings.frontend_url}/projects/{proposal_id}",
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
        title="AI 작업 완료",
        body=f"{step} 단계 AI 생성이 완료되었습니다. 검토해 주세요.",
        link=f"/projects/{proposal_id}/review/{step}",
    )

    # 이메일 (옵트인)
    if created_by:
        await _try_send_email(
            created_by, "email_proposal",
            "AI 작업 완료",
            "AI 작업 완료",
            f"{step} 단계 AI 생성이 완료되었습니다. 검토해 주세요.",
            f"{settings.frontend_url}/projects/{proposal_id}/review/{step}",
        )


async def notify_agent_error(
    proposal_id: str,
    node_name: str,
    error_summary: str,
):
    """에이전트 노드 에러 알림 — Teams + 인앱 (MON-05, MON-06)."""
    try:
        client = await get_async_client()
        proposal = await client.table("proposals").select(
            "title, team_id, created_by"
        ).eq("id", proposal_id).single().execute()

        if not proposal.data:
            return

        title = proposal.data.get("title", "")
        team_id = proposal.data.get("team_id", "")
        created_by = proposal.data.get("created_by", "")

        # 1) Teams Webhook 알림
        if team_id:
            await send_teams_notification(
                team_id=team_id,
                title=f"AI 작업 오류: {node_name}",
                body=(
                    f"**제안서**: {title}\n\n"
                    f"**노드**: {node_name}\n\n"
                    f"**오류**: {error_summary}\n\n"
                    f"관리자 확인이 필요합니다."
                ),
                link=f"/projects/{proposal_id}",
            )

        # 2) 인앱 알림 (생성자에게)
        if created_by:
            await create_notification(
                user_id=created_by,
                proposal_id=proposal_id,
                type="ai_error",
                title=f"AI 작업 오류 — {node_name}",
                body=f"'{title}' 프로젝트의 {node_name} 단계에서 오류 발생: {error_summary[:100]}",
                link=f"/projects/{proposal_id}",
            )

            # 이메일 (옵트인 — AI 완료 설정과 공유: 에러도 AI 작업 결과의 일부)
            await _try_send_email(
                created_by, "email_proposal",
                f"AI 작업 오류: {node_name}",
                f"AI 작업 오류 — {node_name}",
                f"'{title}' 프로젝트의 {node_name} 단계에서 오류가 발생했습니다.",
                f"{settings.frontend_url}/projects/{proposal_id}",
            )
    except Exception as e:
        logger.warning(f"에이전트 에러 알림 실패 (무시): {e}")


async def notify_bid_confirmed(
    proposal_id: str,
    bid_price: int,
    scenario_name: str,
    team_id: str = "",
):
    """입찰가 확정 알림 — 투찰 담당자 + 참여자에게 발송."""
    try:
        client = await get_async_client()
        proposal = await (
            client.table("proposals")
            .select("title, team_id, owner_id")
            .eq("id", proposal_id).single().execute()
        )
        proposal_name = proposal.data.get("title", "") if proposal.data else ""
        tid = team_id or (proposal.data.get("team_id", "") if proposal.data else "")
        owner_id = proposal.data.get("owner_id", "") if proposal.data else ""

        price_text = f"{bid_price / 100_000_000:.1f}억원" if bid_price >= 100_000_000 else f"{bid_price:,}원"
        scenario_label = {"conservative": "보수적", "balanced": "균형", "aggressive": "공격적"}.get(scenario_name, scenario_name)

        body = (
            f"입찰가가 확정되었습니다.\n"
            f"확정가: {price_text} ({scenario_label})\n"
            f"투찰 담당자는 나라장터 투찰을 진행해 주세요."
        )

        # 참여자 목록 조회
        participants = await (
            client.table("project_participants")
            .select("user_id")
            .eq("proposal_id", proposal_id)
            .execute()
        )
        user_ids = list({p["user_id"] for p in (participants.data or [])})
        if owner_id and owner_id not in user_ids:
            user_ids.append(owner_id)

        # 인앱 알림
        for uid in user_ids:
            await create_notification(
                user_id=uid,
                proposal_id=proposal_id,
                type="bid_confirmed",
                title=f"[입찰가 확정] {proposal_name}",
                body=body,
                link=f"/projects/{proposal_id}",
            )

        # Teams 알림
        await send_teams_notification(
            team_id=tid,
            title=f"입찰가 확정: {proposal_name}",
            body=body,
            link=f"/projects/{proposal_id}",
        )

        # 이메일 (옵트인)
        for uid in user_ids:
            await _try_send_email(
                uid, "email_bidding",
                f"[입찰가 확정] {proposal_name}",
                f"입찰가 확정: {proposal_name}",
                body,
                f"{settings.frontend_url}/projects/{proposal_id}",
            )
    except Exception as e:
        logger.warning(f"입찰가 확정 알림 실패: {e}")


async def notify_bid_submitted(
    proposal_id: str,
    submitted_price: int,
    team_id: str = "",
):
    """투찰 완료 알림 — 팀장 + 프로젝트 오너에게 발송."""
    try:
        client = await get_async_client()
        proposal = await (
            client.table("proposals")
            .select("title, team_id, owner_id")
            .eq("id", proposal_id).single().execute()
        )
        proposal_name = proposal.data.get("title", "") if proposal.data else ""
        tid = team_id or (proposal.data.get("team_id", "") if proposal.data else "")
        owner_id = proposal.data.get("owner_id", "") if proposal.data else ""

        price_text = f"{submitted_price / 100_000_000:.1f}억원" if submitted_price >= 100_000_000 else f"{submitted_price:,}원"

        body = f"나라장터 투찰이 완료되었습니다.\n투찰가: {price_text}"

        if owner_id:
            await create_notification(
                user_id=owner_id,
                proposal_id=proposal_id,
                type="bid_submitted",
                title=f"[투찰 완료] {proposal_name}",
                body=body,
                link=f"/projects/{proposal_id}",
            )

        await send_teams_notification(
            team_id=tid,
            title=f"투찰 완료: {proposal_name}",
            body=body,
            link=f"/projects/{proposal_id}",
        )

        # 이메일 (옵트인)
        if owner_id:
            await _try_send_email(
                owner_id, "email_bidding",
                f"[투찰 완료] {proposal_name}",
                f"투찰 완료: {proposal_name}",
                body,
                f"{settings.frontend_url}/projects/{proposal_id}",
            )
    except Exception as e:
        logger.warning(f"투찰 완료 알림 실패: {e}")
