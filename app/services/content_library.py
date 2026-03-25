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


async def auto_register_section(
    org_id: str,
    proposal_id: str,
    section_id: str,
    title: str,
    content: str,
    section_type: str,
    self_review_score: int | None = None,
    rfp_keywords: list[str] | None = None,
    industry: str | None = None,
) -> dict | None:
    """제안서 섹션 완료 시 content_library에 자동 등록 (A-1).

    품질 필터: 500자 미만 또는 자가진단 70점 미만 → 스킵.
    동일 제안서의 같은 섹션 → upsert (최신만 유지).
    """
    if len(content) < 500:
        return None
    if self_review_score is not None and self_review_score < 70:
        return None
    if not org_id or not proposal_id:
        return None

    tags = list((rfp_keywords or [])[:10]) + [section_type]
    embed_text = embedding_text_for_content(title, content, tags)
    embedding = await generate_embedding(embed_text)

    client = await get_async_client()

    # 동일 제안서+섹션 중복 체크 → upsert
    existing = await (
        client.table("content_library")
        .select("id")
        .eq("source_project_id", proposal_id)
        .eq("title", title)
        .eq("type", "section_block")
        .limit(1)
        .execute()
    )

    row = {
        "org_id": org_id,
        "title": title,
        "body": content,
        "type": "section_block",
        "source_project_id": proposal_id,
        "industry": industry,
        "tags": tags,
        "status": "draft",
        "embedding": embedding,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if existing.data:
        result = await (
            client.table("content_library")
            .update(row)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = await client.table("content_library").insert(row).execute()

    return (result.data or [None])[0]


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
