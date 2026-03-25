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


async def trigger_kb_update(proposal_id: str, result: str, _retry: int = 0) -> None:
    """입찰 결과에 따른 KB 자동 업데이트 트리거. 실패 시 1회 재시도."""
    try:
        await _trigger_kb_update_impl(proposal_id, result)
    except Exception as e:
        if _retry < 1:
            logger.warning(f"KB 업데이트 실패, 재시도: {e}")
            import asyncio
            await asyncio.sleep(2)
            await trigger_kb_update(proposal_id, result, _retry=_retry + 1)
        else:
            logger.error(f"KB 업데이트 최종 실패 (proposal={proposal_id}): {e}")


async def _trigger_kb_update_impl(proposal_id: str, result: str) -> None:
    """KB 업데이트 실제 구현."""
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

    # 콘텐츠 라이브러리 성과 카운터 갱신
    await _update_content_library_counters(client, proposal_id, result)


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

        # 낙찰업체의 bid_ratio 계산 (가격 패턴 분석용)
        actual_bid_ratio = None
        if pr.data.get("final_price"):
            prop_detail = await client.table("proposals").select("budget_amount").eq(
                "id", proposal_id
            ).single().execute()
            prop_budget = prop_detail.data.get("budget_amount", 0) if prop_detail.data else 0
            if prop_budget and prop_budget > 0:
                actual_bid_ratio = round(pr.data["final_price"] / prop_budget, 4)

        # 기존 경쟁사 레코드 확인
        existing = await client.table("competitors").select("id, win_count, avg_bid_ratio, total_bids").eq(
            "org_id", org_id
        ).eq("company_name", won_by).execute()

        if existing.data:
            comp = existing.data[0]
            win_count = (comp.get("win_count") or 0) + 1
            total_bids = (comp.get("total_bids") or 0) + 1

            update_data: dict = {"win_count": win_count, "total_bids": total_bids}

            # avg_bid_ratio 업데이트 (이동 평균)
            if actual_bid_ratio is not None:
                old_avg = comp.get("avg_bid_ratio")
                old_count = (comp.get("total_bids") or 0)
                if old_avg and old_count > 0:
                    new_avg = round((old_avg * old_count + actual_bid_ratio) / (old_count + 1), 4)
                else:
                    new_avg = actual_bid_ratio
                update_data["avg_bid_ratio"] = new_avg

            await client.table("competitors").update(update_data).eq("id", comp["id"]).execute()
        else:
            # 새 경쟁사 등록
            new_comp: dict = {
                "org_id": org_id,
                "company_name": won_by,
                "win_count": 1,
                "total_bids": 1,
                "source": "proposal_result",
            }
            if actual_bid_ratio is not None:
                new_comp["avg_bid_ratio"] = actual_bid_ratio
            await client.table("competitors").insert(new_comp).execute()

        logger.info(f"경쟁사 KB 업데이트: {won_by} (proposal={proposal_id})")

    except Exception as e:
        logger.warning(f"경쟁사 KB 업데이트 실패: {e}")


async def _update_content_library_counters(client, proposal_id: str, result: str) -> None:
    """수주/패찰 시 해당 제안서에서 참조한 콘텐츠의 성과 카운터 갱신."""
    try:
        # prompt_artifact_link에서 이 제안서가 사용한 프롬프트 → 섹션 조회
        links = await client.table("prompt_artifact_link").select(
            "section_id"
        ).eq("proposal_id", proposal_id).execute()

        if not links.data:
            return

        section_ids = list({l["section_id"] for l in links.data if l.get("section_id")})
        if not section_ids:
            return

        # content_library에서 이 제안서 관련 콘텐츠 조회
        contents = await client.table("content_library").select(
            "id, won_count, lost_count"
        ).eq("proposal_id", proposal_id).execute()

        col = "won_count" if result == "won" else "lost_count"
        updated = 0
        for c in (contents.data or []):
            current = c.get(col, 0) or 0
            await client.table("content_library").update(
                {col: current + 1}
            ).eq("id", c["id"]).execute()
            updated += 1

        if updated:
            logger.info(f"콘텐츠 라이브러리 성과 갱신: proposal={proposal_id}, {col}+1 x {updated}건")

    except Exception as e:
        logger.warning(f"콘텐츠 라이브러리 성과 갱신 실패 (무시): {e}")


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


async def save_research_to_kb(
    org_id: str,
    proposal_id: str,
    research_brief: dict,
) -> int:
    """리서치 결과를 content_library에 축적 (A-2).

    high/medium credibility 데이터만 topic 단위로 저장.
    """
    if not org_id or not proposal_id or not research_brief:
        return 0

    from app.services.embedding_service import embedding_text_for_content, generate_embedding

    topics = research_brief.get("research_topics", [])
    if not topics:
        return 0

    client = await get_async_client()
    saved = 0

    for topic in topics:
        if not isinstance(topic, dict):
            continue

        topic_name = topic.get("topic", "")
        if not topic_name:
            continue

        # high/medium credibility 데이터만 추출
        data_points = topic.get("data_points", [])
        credible = [
            dp for dp in data_points
            if isinstance(dp, dict) and dp.get("credibility") in ("high", "medium")
        ]
        if not credible:
            continue

        findings = topic.get("findings", [])
        body_parts = []
        if findings:
            body_parts.append("주요 발견:\n" + "\n".join(f"- {f}" for f in findings))
        body_parts.append("근거 데이터:\n" + "\n".join(
            f"- {dp.get('content', '')} [{dp.get('source', '')}] ({dp.get('credibility', '')})"
            for dp in credible
        ))
        body = "\n\n".join(body_parts)

        tags = ["research", topic.get("rfp_alignment", "")]
        embed_text = embedding_text_for_content(topic_name, body, tags)
        embedding = await generate_embedding(embed_text)

        try:
            await client.table("content_library").insert({
                "org_id": org_id,
                "title": f"[리서치] {topic_name}",
                "body": body,
                "type": "research_data",
                "source_project_id": proposal_id,
                "tags": [t for t in tags if t],
                "status": "draft",
                "embedding": embedding,
            }).execute()
            saved += 1
        except Exception as e:
            logger.debug(f"리서치 KB 저장 실패 ({topic_name}): {e}")

    logger.info(f"리서치 KB 축적: {saved}건 (proposal={proposal_id})")
    return saved


async def save_strategy_to_kb(
    org_id: str,
    proposal_id: str,
    client_name: str,
    positioning: str,
    strategy_result: dict,
) -> dict | None:
    """전략 결과를 content_library에 축적 (A-3).

    SWOT, Win Theme, Ghost Theme, key_messages 등 보존.
    """
    if not org_id or not proposal_id or not strategy_result:
        return None

    from app.services.embedding_service import embedding_text_for_content, generate_embedding

    title = f"전략: {client_name} ({positioning})"

    body_parts = []
    if strategy_result.get("win_theme"):
        body_parts.append(f"Win Theme: {strategy_result['win_theme']}")
    if strategy_result.get("ghost_theme"):
        body_parts.append(f"Ghost Theme: {strategy_result['ghost_theme']}")
    if strategy_result.get("key_messages"):
        body_parts.append("Key Messages:\n" + "\n".join(f"- {m}" for m in strategy_result["key_messages"]))
    if strategy_result.get("focus_areas"):
        body_parts.append("Focus Areas:\n" + "\n".join(f"- {a}" for a in strategy_result["focus_areas"]))
    if strategy_result.get("competitor_analysis"):
        body_parts.append(f"경쟁 분석: {strategy_result['competitor_analysis']}")

    body = "\n\n".join(body_parts)
    if not body:
        return None

    tags = [positioning, client_name, "strategy"]
    embed_text = embedding_text_for_content(title, body, tags)
    embedding = await generate_embedding(embed_text)

    try:
        client = await get_async_client()
        result = await client.table("content_library").insert({
            "org_id": org_id,
            "title": title,
            "body": body,
            "type": "strategy_record",
            "source_project_id": proposal_id,
            "industry": strategy_result.get("domain", ""),
            "tags": [t for t in tags if t],
            "status": "draft",
            "embedding": embedding,
        }).execute()
        logger.info(f"전략 KB 축적: {title} (proposal={proposal_id})")
        return (result.data or [None])[0]
    except Exception as e:
        logger.warning(f"전략 KB 저장 실패: {e}")
        return None
