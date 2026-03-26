"""
학습 피드백 루프 (§20-4)

프로젝트 완료 시 KB 자동 환류:
- 발주기관 DB 업데이트 제안
- 경쟁사 이력 기록
- 콘텐츠 등록 후보 추천 (수주 시)
- 회고 워크시트 작성 알림
"""

import logging

from app.services.notification_service import create_notification
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def process_project_completion(proposal_id: str, result: str) -> dict:
    """
    프로젝트 결과 등록 후 KB 자동 환류 (LRN-03~07).

    result: "수주" | "패찰" | "유찰"
    """
    client = await get_async_client()
    actions = []

    # 프로젝트 정보 조회
    proposal = await client.table("proposals").select("*").eq("id", proposal_id).single().execute()
    if not proposal.data:
        return {"actions": []}

    p = proposal.data
    created_by = p.get("owner_id", "")
    org_id = p.get("org_id", "")
    project_name = p.get("title", "")

    # 1. 발주기관 DB 자동 업데이트 제안
    client_name = p.get("client_name") or p.get("client_org")
    if client_name:
        await _update_client_history(client, org_id, client_name, proposal_id, result, created_by)
        actions.append("client_history_updated")

    # 2. 콘텐츠 등록 후보 추천 (수주 시)
    if result == "수주":
        await create_notification(
            user_id=created_by,
            notification_type="content_suggestion",
            title=f"콘텐츠 등록 후보: {project_name}",
            body=f"수주 제안서 '{project_name}'의 섹션을 콘텐츠 라이브러리에 등록하시겠습니까?",
            link=f"/projects/{proposal_id}/artifacts/proposal",
        )
        actions.append("content_suggestion_sent")

    # 3. 회고 워크시트 작성 알림
    await create_notification(
        user_id=created_by,
        notification_type="retrospect_reminder",
        title=f"회고 작성 요청: {project_name}",
        body="프로젝트 결과가 등록되었습니다. 7일 이내에 회고 워크시트를 작성해 주세요.",
        link=f"/projects/{proposal_id}/retrospect",
    )
    actions.append("retrospect_reminder_sent")

    # 4. 참여자에게도 알림
    participants = await client.table("project_teams").select("user_id").eq(
        "proposal_id", proposal_id
    ).execute()
    for pt in (participants.data or []):
        if pt["user_id"] != created_by:
            await create_notification(
                user_id=pt["user_id"],
                notification_type="project_result",
                title=f"프로젝트 결과: {project_name}",
                body=f"'{project_name}' 프로젝트가 '{result}' 처리되었습니다.",
                link=f"/projects/{proposal_id}",
            )
    actions.append("participants_notified")

    return {"proposal_id": proposal_id, "result": result, "actions": actions}


async def _update_client_history(
    client,
    org_id: str,
    client_name: str,
    proposal_id: str,
    result: str,
    created_by: str,
):
    """발주기관 이력 업데이트 + 관계 수준 변경 제안."""
    # 발주기관 조회
    ci = await client.table("client_intelligence").select("id, relationship").eq(
        "org_id", org_id
    ).ilike("client_name", client_name).limit(1).execute()

    if not ci.data:
        return

    client_record = ci.data[0]
    client_id = client_record["id"]
    current_rel = client_record.get("relationship", "neutral")

    # 입찰 이력 기록
    result_map = {"수주": "won", "패찰": "lost", "유찰": "expired"}
    await client.table("client_bid_history").insert({
        "client_id": client_id,
        "proposal_id": proposal_id,
        "result": result_map.get(result, result),
    }).execute()

    # 관계 수준 업그레이드 제안 (수주 시)
    if result == "수주" and current_rel in ("new", "neutral"):
        suggested = "friendly" if current_rel == "neutral" else "neutral"
        await create_notification(
            user_id=created_by,
            notification_type="kb_update_suggestion",
            title=f"발주기관 관계 업데이트 제안: {client_name}",
            body=f"수주 성공! 관계 수준을 '{current_rel}' → '{suggested}'로 변경하시겠습니까?",
            link="/kb/clients",
        )
