"""
콘텐츠 라이브러리 서비스 (§20-3)

콘텐츠 CRUD + 품질 점수 산출 + 섹션 추천.
"""

import logging
from datetime import datetime, timezone

from app.services.embedding_service import (
    embedding_text_for_content,
    generate_embedding,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def create_content(
    org_id: str,
    author_id: str,
    title: str,
    body: str,
    content_type: str = "section_block",
    source_project_id: str | None = None,
    industry: str | None = None,
    tech_area: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """콘텐츠 등록 (draft 상태, 임베딩 자동 생성)."""
    embed_text = embedding_text_for_content(title, body, tags)
    embedding = await generate_embedding(embed_text)

    client = await get_async_client()
    row = {
        "org_id": org_id,
        "author_id": author_id,
        "title": title,
        "body": body,
        "type": content_type,
        "source_project_id": source_project_id,
        "industry": industry,
        "tech_area": tech_area,
        "tags": tags or [],
        "status": "draft",
        "embedding": embedding,
    }
    result = await client.table("content_library").insert(row).execute()
    return (result.data or [{}])[0]


async def update_content(
    content_id: str,
    updates: dict,
) -> dict:
    """콘텐츠 수정 (임베딩 재생성 포함)."""
    client = await get_async_client()

    # 기존 데이터 조회
    existing = await client.table("content_library").select("*").eq("id", content_id).single().execute()
    if not existing.data:
        return {}

    data = existing.data
    title = updates.get("title", data["title"])
    body = updates.get("body", data["body"])
    tags = updates.get("tags", data.get("tags"))

    # 본문이나 제목이 변경되면 임베딩 재생성
    if "title" in updates or "body" in updates:
        embed_text = embedding_text_for_content(title, body, tags)
        updates["embedding"] = await generate_embedding(embed_text)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await client.table("content_library").update(updates).eq("id", content_id).execute()
    return (result.data or [{}])[0]


async def approve_content(content_id: str, approver_id: str) -> dict:
    """콘텐츠 승인 (draft → published)."""
    client = await get_async_client()
    result = await client.table("content_library").update({
        "status": "published",
        "approved_by": approver_id,
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", content_id).execute()
    return (result.data or [{}])[0]


async def calculate_quality_score(content_id: str) -> float:
    """
    콘텐츠 품질 점수 산출 (CL-08):
    quality_score = (won_rate × 40) + (reuse_rate × 30) + (freshness × 30)
    """
    client = await get_async_client()
    result = await client.table("content_library").select(
        "won_count, lost_count, reuse_count, updated_at"
    ).eq("id", content_id).single().execute()

    if not result.data:
        return 0.0

    data = result.data
    total = (data.get("won_count") or 0) + (data.get("lost_count") or 0)
    won_rate = (data["won_count"] / total * 100) if total > 0 else 50
    reuse_rate = min((data.get("reuse_count") or 0) / 10 * 100, 100)

    # freshness: 6개월 내 = 100%, 이후 감쇠
    updated_str = data.get("updated_at", "")
    if updated_str:
        try:
            updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - updated).days
            freshness = max(0, 100 - (days - 180) * 0.5) if days > 180 else 100
        except ValueError:
            freshness = 50
    else:
        freshness = 50

    score = won_rate * 0.4 + reuse_rate * 0.3 + freshness * 0.3

    # DB 업데이트
    await client.table("content_library").update({
        "quality_score": round(score, 2),
    }).eq("id", content_id).execute()

    return round(score, 2)


async def suggest_content_for_section(
    section_topic: str,
    org_id: str,
    top_k: int = 5,
) -> list[dict]:
    """STEP 4 섹션 작성 시 유사 콘텐츠 자동 추천 (DOC-14)."""
    from app.services.knowledge_search import unified_search

    results = await unified_search(
        query=section_topic,
        org_id=org_id,
        filters={"areas": ["content"]},
        top_k=top_k,
    )
    items = results.get("content", [])
    return sorted(items, key=lambda x: x.get("quality_score", 0), reverse=True)
