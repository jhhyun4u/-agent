"""
성과 기반 KB 업데이트 서비스 (Phase 4-6)

입찰 결과에 따라 KB(역량 DB, 경쟁사 DB, 교훈 DB)를 자동 반영:
- 수주 시: capabilities 테이블에 수행 실적 추가 후보 알림
- 패찰 시: competitors 테이블에 낙찰업체 정보 업데이트
- 교훈 등록 시: lessons_learned 벡터 임베딩 생성
"""

import logging

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def trigger_kb_update(proposal_id: str, result: str) -> None:
    """입찰 결과에 따른 KB 자동 업데이트 트리거."""
    client = await get_async_client()

    # 프로젝트 정보 조회
    proposal = await client.table("proposals").select(
        "id, name, client, positioning, budget_amount, org_id, team_id"
    ).eq("id", proposal_id).single().execute()
    if not proposal.data:
        return

    p = proposal.data

    if result == "won":
        await _update_capabilities_on_win(client, p)
    elif result == "lost":
        await _update_competitors_on_loss(client, proposal_id, p)


async def _update_capabilities_on_win(client, proposal: dict) -> None:
    """수주 시: capabilities에 수행 실적 후보 생성."""
    try:
        org_id = proposal.get("org_id")
        if not org_id:
            return

        # 이미 등록된 역량인지 확인
        existing = await client.table("capabilities").select("id").eq(
            "org_id", org_id
        ).ilike("description", f"%{proposal.get('name', '')}%").execute()

        if existing.data:
            logger.info(f"수주 실적 이미 존재: {proposal['id']}")
            return

        # 역량 후보 등록 (draft 상태)
        capability_row = {
            "org_id": org_id,
            "category": "수행실적",
            "name": proposal.get("name", ""),
            "description": f"[자동등록후보] {proposal.get('client', '')} - {proposal.get('name', '')}",
            "evidence_type": "proposal_result",
            "evidence_ref": proposal["id"],
        }
        await client.table("capabilities").insert(capability_row).execute()
        logger.info(f"수주 실적 KB 후보 등록: {proposal['id']}")

    except Exception as e:
        logger.warning(f"역량 KB 업데이트 실패: {e}")


async def _update_competitors_on_loss(client, proposal_id: str, proposal: dict) -> None:
    """패찰 시: 낙찰업체 정보를 competitors에 업데이트."""
    try:
        # proposal_results에서 낙찰업체 조회
        pr = await client.table("proposal_results").select(
            "won_by, final_price, competitor_count"
        ).eq("proposal_id", proposal_id).single().execute()

        if not pr.data or not pr.data.get("won_by"):
            return

        won_by = pr.data["won_by"]
        org_id = proposal.get("org_id")
        if not org_id:
            return

        # 기존 경쟁사 레코드 확인
        existing = await client.table("competitors").select("id, win_count").eq(
            "org_id", org_id
        ).eq("company_name", won_by).execute()

        if existing.data:
            # 수주 횟수 증가
            comp = existing.data[0]
            win_count = (comp.get("win_count") or 0) + 1
            await client.table("competitors").update({
                "win_count": win_count,
            }).eq("id", comp["id"]).execute()
        else:
            # 새 경쟁사 등록
            await client.table("competitors").insert({
                "org_id": org_id,
                "company_name": won_by,
                "win_count": 1,
                "source": "proposal_result",
            }).execute()

        logger.info(f"경쟁사 KB 업데이트: {won_by} (proposal={proposal_id})")

    except Exception as e:
        logger.warning(f"경쟁사 KB 업데이트 실패: {e}")


async def generate_lesson_embedding(lesson_id: str, title: str, description: str) -> None:
    """교훈 벡터 임베딩 생성 + lessons_learned.embedding 업데이트."""
    try:
        from app.config import settings
        if not settings.openai_api_key:
            logger.info("OpenAI API 키 없음 — 임베딩 생성 스킵")
            return

        import openai
        oai = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        text = f"{title}\n{description}"
        response = await oai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        embedding = response.data[0].embedding

        client = await get_async_client()
        await client.table("lessons_learned").update({
            "embedding": embedding,
        }).eq("id", lesson_id).execute()

        logger.info(f"교훈 임베딩 생성 완료: {lesson_id}")

    except Exception as e:
        logger.warning(f"교훈 임베딩 생성 실패: {e}")
