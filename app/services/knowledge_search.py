"""
통합 KB 검색 서비스 (§20-2)

시맨틱(pgvector cosine) + 키워드 하이브리드 검색.
5개 영역(content, client, competitor, lesson, capability) 병렬 검색 후 그룹화 반환.
"""

import asyncio
import logging
from typing import Any

from app.services.embedding_service import generate_embedding
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

KB_TOP_K = 5
KB_MAX_BODY_LENGTH = 500


async def unified_search(
    query: str,
    org_id: str,
    filters: dict[str, Any] | None = None,
    top_k: int = KB_TOP_K,
    max_body_length: int = KB_MAX_BODY_LENGTH,
) -> dict[str, list[dict]]:
    """
    통합 KB 검색 — 시맨틱 + 키워드 하이브리드.
    결과를 영역별로 그룹화하여 반환.
    """
    all_areas = ["content", "client", "competitor", "lesson", "capability"]
    areas = (filters or {}).get("areas", all_areas)

    # 임베딩 생성
    query_embedding = await generate_embedding(query)

    # 영역별 병렬 검색
    tasks = {}
    if "content" in areas:
        tasks["content"] = _search_content(query, query_embedding, org_id, top_k, max_body_length)
    if "client" in areas:
        tasks["client"] = _search_clients(query, query_embedding, org_id, top_k)
    if "competitor" in areas:
        tasks["competitor"] = _search_competitors(query, query_embedding, org_id, top_k)
    if "lesson" in areas:
        tasks["lesson"] = _search_lessons(query, query_embedding, org_id, top_k)
    if "capability" in areas:
        tasks["capability"] = _search_capabilities(query, org_id, top_k)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    grouped = {}
    for area, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.warning(f"KB 검색 실패 ({area}): {result}")
            grouped[area] = []
        else:
            grouped[area] = result

    return grouped


async def _search_content(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
    max_body: int,
) -> list[dict]:
    """콘텐츠 라이브러리 시맨틱 검색."""
    client = await get_async_client()

    # pgvector RPC 호출 (cosine similarity)
    try:
        result = await client.rpc("search_content_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
            "max_body_length": max_body,
        }).execute()
        return result.data or []
    except Exception:
        # RPC 미등록 시 키워드 폴백
        logger.info("search_content_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("content_library").select(
            "id, title, body, quality_score, type, tags"
        ).eq("org_id", org_id).eq("status", "published").ilike(
            "title", f"%{query}%"
        ).limit(top_k).execute()

        items = result.data or []
        for item in items:
            item["body_excerpt"] = (item.pop("body", "") or "")[:max_body]
            item["similarity"] = None
        return items


async def _search_clients(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """발주기관 DB 검색."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_clients_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        logger.info("search_clients_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("client_intelligence").select(
            "id, client_name, client_type, relationship, eval_tendency"
        ).eq("org_id", org_id).ilike(
            "client_name", f"%{query}%"
        ).limit(top_k).execute()
        return result.data or []


async def _search_competitors(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """경쟁사 DB 검색."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_competitors_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        logger.info("search_competitors_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("competitors").select(
            "id, company_name, scale, primary_area, strengths, weaknesses, price_pattern"
        ).eq("org_id", org_id).ilike(
            "company_name", f"%{query}%"
        ).limit(top_k).execute()
        return result.data or []


async def _search_lessons(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """교훈 아카이브 검색."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_lessons_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        logger.info("search_lessons_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("lessons_learned").select(
            "id, strategy_summary, effective_points, weak_points, result, positioning, client_name"
        ).eq("org_id", org_id).limit(top_k).execute()
        return result.data or []


async def _search_capabilities(
    query: str,
    org_id: str,
    top_k: int,
) -> list[dict]:
    """역량 DB 키워드 검색 (임베딩 미적용)."""
    client = await get_async_client()
    result = await client.table("capabilities").select(
        "id, description, tech_area, track_record, keywords"
    ).eq("org_id", org_id).ilike(
        "description", f"%{query}%"
    ).limit(top_k).execute()
    return result.data or []
