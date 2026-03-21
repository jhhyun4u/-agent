"""
Q&A 기록 검색 가능 저장 서비스 (PSM-16)

발표 현장 Q&A → presentation_qa 저장 → content_library 등록
→ 임베딩 생성 → 교훈 아카이브 요약 기록.
"""

import logging

from app.services.embedding_service import generate_embedding
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def save_qa_records(
    proposal_id: str,
    qa_records: list[dict],
    created_by: str | None = None,
) -> list[dict]:
    """
    Q&A 기록 일괄 저장 + KB 연동.

    1) presentation_qa 테이블 저장
    2) content_library에 qa_record 유형 등록 (status=published)
    3) 임베딩 생성 → presentation_qa.embedding + content_library.embedding
    4) lessons_learned에 Q&A 요약 기록
    """
    client = await get_async_client()

    # 프로젝트 정보 조회
    proposal = await client.table("proposals").select(
        "id, name, client, org_id, industry"
    ).eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise ValueError(f"프로젝트 미존재: {proposal_id}")

    p = proposal.data
    saved = []

    for qa in qa_records:
        # 1) presentation_qa 저장
        qa_row = {
            "proposal_id": proposal_id,
            "question": qa["question"],
            "answer": qa["answer"],
            "category": qa.get("category", "general"),
            "evaluator_reaction": qa.get("evaluator_reaction"),
            "memo": qa.get("memo"),
            "created_by": created_by,
        }
        result = await client.table("presentation_qa").insert(qa_row).execute()
        qa_record = result.data[0]

        # 2) content_library에 qa_record 등록
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        cl_row = {
            "org_id": p["org_id"],
            "type": "qa_record",
            "title": f"[Q&A] {qa['question'][:50]}",
            "body": content_body,
            "source_project_id": proposal_id,
            "industry": p.get("industry"),
            "tags": [qa.get("category", "general"), "qa", "presentation"],
            "status": "published",
            "author_id": created_by,
        }
        cl_result = await client.table("content_library").insert(cl_row).execute()
        content_id = cl_result.data[0]["id"]

        # presentation_qa에 content_library_id 연결
        await client.table("presentation_qa").update({
            "content_library_id": content_id,
        }).eq("id", qa_record["id"]).execute()

        # 3) 임베딩 생성
        try:
            embedding = await generate_embedding(content_body)
            await client.table("presentation_qa").update({
                "embedding": embedding,
            }).eq("id", qa_record["id"]).execute()
            await client.table("content_library").update({
                "embedding": embedding,
            }).eq("id", content_id).execute()
        except Exception as e:
            logger.warning(f"Q&A 임베딩 생성 실패 (계속 진행): {e}")

        qa_record["content_library_id"] = content_id
        saved.append(qa_record)

    # 4) 교훈 아카이브에 Q&A 요약 기록
    if qa_records:
        await _save_qa_lesson_summary(client, proposal_id, p, qa_records, created_by)

    return saved


async def _save_qa_lesson_summary(
    client, proposal_id: str, proposal: dict,
    qa_records: list[dict], created_by: str | None,
) -> None:
    """Q&A 요약을 교훈 아카이브에 기록."""
    try:
        qa_summary = "\n".join(
            f"• Q: {qa['question'][:80]} → A: {qa['answer'][:80]}"
            for qa in qa_records
        )
        lesson_row = {
            "proposal_id": proposal_id,
            "org_id": proposal["org_id"],
            "category": "qa_insight",
            "strategy_summary": f"발표 Q&A ({len(qa_records)}건) - {proposal.get('name', '')}",
            "effective_points": qa_summary,
            "result": "presented",
            "client_name": proposal.get("client", ""),
            "created_by": created_by,
        }
        result = await client.table("lessons_learned").insert(lesson_row).execute()

        # 교훈 임베딩 생성
        if result.data:
            from app.services.kb_updater import generate_lesson_embedding
            lesson = result.data[0]
            await generate_lesson_embedding(
                lesson["id"],
                lesson_row["strategy_summary"],
                qa_summary,
            )
    except Exception as e:
        logger.warning(f"Q&A 교훈 요약 저장 실패 (계속 진행): {e}")


async def get_proposal_qa(proposal_id: str) -> list[dict]:
    """프로젝트별 Q&A 기록 조회."""
    client = await get_async_client()
    result = await client.table("presentation_qa").select(
        "id, proposal_id, question, answer, category, "
        "evaluator_reaction, memo, content_library_id, created_at, created_by"
    ).eq("proposal_id", proposal_id).order("created_at").execute()
    return result.data or []


async def update_qa_record(qa_id: str, updates: dict) -> dict:
    """개별 Q&A 기록 수정 + 임베딩 재생성."""
    client = await get_async_client()

    result = await client.table("presentation_qa").update(
        {k: v for k, v in updates.items() if v is not None}
    ).eq("id", qa_id).execute()
    if not result.data:
        raise ValueError(f"Q&A 레코드 미존재: {qa_id}")

    qa = result.data[0]

    # question 또는 answer 변경 시 임베딩 + content_library 동기화
    if "question" in updates or "answer" in updates:
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        try:
            embedding = await generate_embedding(content_body)
            await client.table("presentation_qa").update({
                "embedding": embedding,
            }).eq("id", qa_id).execute()

            if qa.get("content_library_id"):
                await client.table("content_library").update({
                    "title": f"[Q&A] {qa['question'][:50]}",
                    "body": content_body,
                    "embedding": embedding,
                }).eq("id", qa["content_library_id"]).execute()
        except Exception as e:
            logger.warning(f"Q&A 임베딩 업데이트 실패: {e}")

    return qa


async def delete_qa_record(qa_id: str) -> None:
    """개별 Q&A 기록 삭제 + content_library 연결 해제."""
    client = await get_async_client()

    qa = await client.table("presentation_qa").select(
        "id, content_library_id"
    ).eq("id", qa_id).single().execute()
    if not qa.data:
        raise ValueError(f"Q&A 레코드 미존재: {qa_id}")

    # content_library에서도 삭제
    if qa.data.get("content_library_id"):
        await client.table("content_library").delete().eq(
            "id", qa.data["content_library_id"]
        ).execute()

    await client.table("presentation_qa").delete().eq("id", qa_id).execute()


async def search_qa(
    query: str,
    org_id: str,
    category: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Q&A 하이브리드 검색 (시맨틱 + 키워드 폴백)."""
    client = await get_async_client()

    try:
        query_embedding = await generate_embedding(query)
        result = await client.rpc("search_qa_by_embedding", {
            "query_embedding": query_embedding,
            "match_org_id": org_id,
            "match_count": limit,
            "filter_category": category,
        }).execute()

        items = result.data or []

        # 프로젝트 이름/발주기관 부가정보 보강
        if items:
            proposal_ids = list({it["proposal_id"] for it in items})
            proposals = await client.table("proposals").select(
                "id, name, client"
            ).in_("id", proposal_ids).execute()
            pmap = {p["id"]: p for p in (proposals.data or [])}
            for it in items:
                p = pmap.get(it["proposal_id"], {})
                it["proposal_name"] = p.get("name")
                it["client"] = p.get("client")

        return items

    except Exception:
        logger.info("search_qa_by_embedding RPC 미등록, 키워드 검색 폴백")
        return await _keyword_search_qa(client, query, org_id, category, limit)


async def _keyword_search_qa(
    client, query: str, org_id: str, category: str | None, limit: int,
) -> list[dict]:
    """키워드 폴백 검색."""
    q = client.table("presentation_qa").select(
        "id, proposal_id, question, answer, category, "
        "evaluator_reaction, memo, created_at, "
        "proposals!inner(name, client, org_id)"
    ).eq("proposals.org_id", org_id)

    if category:
        q = q.eq("category", category)

    q = q.or_(f"question.ilike.%{query}%,answer.ilike.%{query}%")
    result = await q.order("created_at", desc=True).limit(limit).execute()

    items = []
    for row in result.data or []:
        prop = row.pop("proposals", {})
        row["proposal_name"] = prop.get("name")
        row["client"] = prop.get("client")
        row["similarity"] = None
        items.append(row)
    return items
