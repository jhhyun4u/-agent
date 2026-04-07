"""
통합 KB 검색 서비스 (§20-2)

시맨틱(pgvector cosine) + 키워드 하이브리드 검색.
6개 영역(content, client, competitor, lesson, capability, qa) 병렬 검색 후 그룹화 반환.
B-1: capabilities 시맨틱 검색 전환.
B-2: 키워드 폴백 body/strategy_summary 추가.
B-3: 하이브리드 랭킹 (similarity + quality + freshness).
"""

import asyncio
import logging
from datetime import datetime, timezone
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
    all_areas = ["content", "client", "competitor", "lesson", "capability", "qa",
                  "intranet_doc", "intranet_project"]
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
        tasks["capability"] = _search_capabilities(query, query_embedding, org_id, top_k)
    if "qa" in areas:
        tasks["qa"] = _search_qa(query, query_embedding, org_id, top_k)
    if "intranet_doc" in areas:
        tasks["intranet_doc"] = _search_intranet_docs(query, query_embedding, org_id, top_k, max_body_length)
    if "intranet_project" in areas:
        tasks["intranet_project"] = _search_intranet_projects(query, query_embedding, org_id, top_k)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    grouped = {}
    for area, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.warning(f"KB 검색 실패 ({area}): {result}")
            grouped[area] = []
        else:
            grouped[area] = result

    # B-3: content 영역에 하이브리드 랭킹 적용
    if "content" in grouped and grouped["content"]:
        grouped["content"] = _apply_hybrid_ranking(grouped["content"])

    return grouped


# ── B-3: 하이브리드 랭킹 ──


def _apply_hybrid_ranking(items: list[dict]) -> list[dict]:
    """content 영역에 하이브리드 랭킹 적용.

    final_score = similarity × 0.5 + quality_score × 0.3 + freshness × 0.2
    """
    now = datetime.now(timezone.utc)
    for item in items:
        sim = item.get("similarity") or 0.0
        quality = (item.get("quality_score") or 0.0) / 100.0  # 0~1 정규화

        # freshness: 6개월 이내 = 1.0, 이후 감쇠
        updated = item.get("updated_at", "")
        try:
            if updated:
                dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                days = (now - dt).days
                freshness = max(0.0, 1.0 - max(0, days - 180) * 0.005)
            else:
                freshness = 0.5
        except (ValueError, TypeError):
            freshness = 0.5

        item["_rank_score"] = sim * 0.5 + quality * 0.3 + freshness * 0.2

    return sorted(items, key=lambda x: x.get("_rank_score", 0), reverse=True)


# ── 영역별 검색 함수 ──


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
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        # B-2: RPC 미등록 시 키워드 폴백 — body도 검색
        logger.info("search_content_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("content_library").select(
            "id, title, body, quality_score, type, tags, updated_at"
        ).eq("org_id", org_id).eq("status", "published").or_(
            f"title.ilike.%{query}%,body.ilike.%{query}%"
        ).limit(top_k).execute()

        items = result.data or []
        for item in items:
            item["body_excerpt"] = (item.pop("body", "") or "")[:max_body]
            item["similarity"] = None
            item["match_type"] = "keyword"
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
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_clients_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("client_intelligence").select(
            "id, client_name, client_type, relationship, eval_tendency"
        ).eq("org_id", org_id).ilike(
            "client_name", f"%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items


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
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_competitors_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("competitors").select(
            "id, company_name, scale, primary_area, strengths, weaknesses, price_pattern"
        ).eq("org_id", org_id).ilike(
            "company_name", f"%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items


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
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        # B-2: 키워드 폴백 — strategy_summary, effective_points, weak_points 검색
        logger.info("search_lessons_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("lessons_learned").select(
            "id, strategy_summary, effective_points, weak_points, result, positioning, client_name"
        ).eq("org_id", org_id).or_(
            f"strategy_summary.ilike.%{query}%,"
            f"effective_points.ilike.%{query}%,"
            f"weak_points.ilike.%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items


async def _search_capabilities(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """역량 DB 시맨틱 검색 (B-1: 임베딩 적용)."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_capabilities_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        # 폴백: title + detail 키워드 검색
        logger.info("search_capabilities_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("capabilities").select(
            "id, type, title, detail, keywords"
        ).eq("org_id", org_id).or_(
            f"title.ilike.%{query}%,detail.ilike.%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items


async def _search_qa(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """Q&A 시맨틱 검색 (PSM-16)."""
    client = await get_async_client()
    try:
        result = await client.rpc("search_qa_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_qa_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("presentation_qa").select(
            "id, question, answer, category, created_at, "
            "proposals!inner(org_id)"
        ).eq("proposals.org_id", org_id).or_(
            f"question.ilike.%{query}%,answer.ilike.%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item.pop("proposals", None)
            item["match_type"] = "keyword"
        return items


async def _search_intranet_docs(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
    max_body: int,
) -> list[dict]:
    """인트라넷 문서 청크 벡터 검색."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_document_chunks_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        items = result.data or []
        for item in items:
            item["content"] = (item.get("content") or "")[:max_body]
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_document_chunks_by_embedding RPC 미등록, 키워드 폴백")
        result = await client.table("document_chunks").select(
            "id, section_title, content, document_id"
        ).eq("org_id", org_id).ilike(
            "content", f"%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["content"] = (item.get("content") or "")[:max_body]
            item["match_type"] = "keyword"
        return items


async def _search_intranet_projects(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """인트라넷 프로젝트 벡터 검색 (공고 매칭용)."""
    client = await get_async_client()

    try:
        result = await client.rpc("search_projects_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_projects_by_embedding RPC 미등록, 키워드 폴백")
        result = await client.table("intranet_projects").select(
            "id, project_name, client_name, department, budget_krw, keywords, status"
        ).eq("org_id", org_id).or_(
            f"project_name.ilike.%{query}%,client_name.ilike.%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items
