"""
Knowledge Base API (§12-12, §20-6)

GET  /api/kb/search                         — 통합 KB 검색
GET/POST/PUT/DELETE /api/kb/content/*       — 콘텐츠 라이브러리 CRUD
POST /api/kb/content/{id}/approve           — 콘텐츠 승인
GET/POST/PUT/DELETE /api/kb/clients/*       — 발주기관 DB CRUD
GET/POST/PUT/DELETE /api/kb/competitors/*   — 경쟁사 DB CRUD
GET/POST          /api/kb/lessons/*         — 교훈 아카이브
POST /api/proposals/{id}/retrospect         — 회고 워크시트

GET/POST/PUT/DELETE /api/kb/labor-rates     — 노임단가 CRUD (v3.4)
POST /api/kb/labor-rates/import             — 노임단가 CSV 임포트
GET/POST/PUT/DELETE /api/kb/market-prices   — 시장 낙찰가 CRUD (v3.4)

GET /api/kb/export/{part}                   — KB CSV 내보내기
"""

import csv
import io
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role
from app.exceptions import TenopAPIError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


# ════════════════════════════════════════
# 통합 검색
# ════════════════════════════════════════

@router.get("/search")
async def kb_search(
    q: str = Query(..., min_length=1),
    areas: str | None = Query(None, description="content,client,competitor,lesson,capability"),
    top_k: int = Query(5, ge=1, le=20),
    user=Depends(get_current_user),
):
    """통합 KB 검색 (시맨틱 + 키워드 하이브리드)."""
    from app.services.knowledge_search import unified_search

    filters = {}
    if areas:
        filters["areas"] = [a.strip() for a in areas.split(",")]

    results = await unified_search(
        query=q,
        org_id=user["org_id"],
        filters=filters,
        top_k=top_k,
    )
    total = sum(len(v) for v in results.values())
    return {"query": q, "total": total, "results": results}


# ════════════════════════════════════════
# 콘텐츠 라이브러리
# ════════════════════════════════════════

class ContentCreateBody(BaseModel):
    title: str
    body: str
    type: str = "section_block"
    source_project_id: str | None = None
    industry: str | None = None
    tech_area: str | None = None
    tags: list[str] = []


class ContentUpdateBody(BaseModel):
    title: str | None = None
    body: str | None = None
    industry: str | None = None
    tech_area: str | None = None
    tags: list[str] | None = None


@router.get("/content")
async def list_content(
    status: str | None = None,
    content_type: str | None = Query(None, alias="type"),
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """콘텐츠 라이브러리 목록."""
    client = await get_async_client()
    query = client.table("content_library").select(
        "id, title, type, status, quality_score, reuse_count, tags, industry, tech_area, created_at"
    ).eq("org_id", user["org_id"]).order("quality_score", desc=True).range(skip, skip + limit - 1)

    if status:
        query = query.eq("status", status)
    if content_type:
        query = query.eq("type", content_type)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/content/{content_id}")
async def get_content(content_id: str, user=Depends(get_current_user)):
    """콘텐츠 상세."""
    client = await get_async_client()
    result = await client.table("content_library").select("*").eq("id", content_id).single().execute()
    if not result.data:
        raise TenopAPIError("KB_002", "콘텐츠를 찾을 수 없습니다.", 404)
    return result.data


@router.post("/content", status_code=201)
async def create_content_endpoint(body: ContentCreateBody, user=Depends(get_current_user)):
    """콘텐츠 등록."""
    from app.services.content_library import create_content

    result = await create_content(
        org_id=user["org_id"],
        author_id=user["id"],
        title=body.title,
        body=body.body,
        content_type=body.type,
        source_project_id=body.source_project_id,
        industry=body.industry,
        tech_area=body.tech_area,
        tags=body.tags,
    )
    return result


@router.put("/content/{content_id}")
async def update_content_endpoint(
    content_id: str,
    body: ContentUpdateBody,
    user=Depends(get_current_user),
):
    """콘텐츠 수정."""
    from app.services.content_library import update_content

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise TenopAPIError("KB_003", "수정할 필드가 없습니다.", 400)

    result = await update_content(content_id, updates)
    return result


@router.delete("/content/{content_id}")
async def delete_content(content_id: str, user=Depends(require_role("lead", "admin"))):
    """콘텐츠 삭제 (archived 처리)."""
    client = await get_async_client()
    await client.table("content_library").update({"status": "archived"}).eq("id", content_id).execute()
    return {"status": "ok"}


@router.post("/content/{content_id}/approve")
async def approve_content_endpoint(
    content_id: str,
    user=Depends(require_role("lead", "director", "admin")),
):
    """콘텐츠 승인 (draft → published)."""
    from app.services.content_library import approve_content

    result = await approve_content(content_id, user["id"])
    return result


# ════════════════════════════════════════
# 발주기관 DB
# ════════════════════════════════════════

class ClientCreateBody(BaseModel):
    client_name: str
    client_type: str | None = None
    scale: str | None = None
    parent_ministry: str | None = None
    location: str | None = None
    relationship: str = "neutral"
    eval_tendency: str | None = None
    notes: str | None = None


class ClientUpdateBody(BaseModel):
    client_type: str | None = None
    scale: str | None = None
    relationship: str | None = None
    eval_tendency: str | None = None
    notes: str | None = None


@router.get("/clients")
async def list_clients(
    relationship: str | None = None,
    client_type: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """발주기관 목록."""
    client = await get_async_client()
    query = client.table("client_intelligence").select(
        "id, client_name, client_type, scale, relationship, eval_tendency, location, updated_at"
    ).eq("org_id", user["org_id"]).order("updated_at", desc=True).range(skip, skip + limit - 1)

    if relationship:
        query = query.eq("relationship", relationship)
    if client_type:
        query = query.eq("client_type", client_type)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/clients/{client_id}")
async def get_client(client_id: str, user=Depends(get_current_user)):
    """발주기관 상세 (입찰 이력 포함)."""
    client = await get_async_client()
    ci = await client.table("client_intelligence").select("*").eq("id", client_id).single().execute()
    if not ci.data:
        raise TenopAPIError("KB_010", "발주기관을 찾을 수 없습니다.", 404)

    history = await client.table("client_bid_history").select("*").eq(
        "client_id", client_id
    ).order("created_at", desc=True).limit(20).execute()

    return {**ci.data, "bid_history": history.data or []}


@router.post("/clients", status_code=201)
async def create_client(body: ClientCreateBody, user=Depends(get_current_user)):
    """발주기관 등록."""
    from app.services.embedding_service import embedding_text_for_client, generate_embedding

    embed_text = embedding_text_for_client(body.client_name, body.client_type or "", body.notes or "")
    embedding = await generate_embedding(embed_text)

    client = await get_async_client()
    row = {
        **body.model_dump(),
        "org_id": user["org_id"],
        "created_by": user["id"],
        "embedding": embedding,
    }
    result = await client.table("client_intelligence").insert(row).execute()
    return (result.data or [{}])[0]


@router.put("/clients/{client_id}")
async def update_client(client_id: str, body: ClientUpdateBody, user=Depends(get_current_user)):
    """발주기관 수정."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise TenopAPIError("KB_011", "수정할 필드가 없습니다.", 400)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    client = await get_async_client()
    result = await client.table("client_intelligence").update(updates).eq("id", client_id).execute()
    return (result.data or [{}])[0]


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user=Depends(require_role("lead", "admin"))):
    """발주기관 삭제."""
    client = await get_async_client()
    await client.table("client_intelligence").delete().eq("id", client_id).execute()
    return {"status": "ok"}


# ════════════════════════════════════════
# 경쟁사 DB
# ════════════════════════════════════════

class CompetitorCreateBody(BaseModel):
    company_name: str
    scale: str | None = None
    primary_area: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    price_pattern: str | None = None
    notes: str | None = None


class CompetitorUpdateBody(BaseModel):
    scale: str | None = None
    primary_area: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    price_pattern: str | None = None
    avg_win_rate: float | None = None
    notes: str | None = None


@router.get("/competitors")
async def list_competitors(
    scale: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """경쟁사 목록."""
    client = await get_async_client()
    query = client.table("competitors").select(
        "id, company_name, scale, primary_area, price_pattern, avg_win_rate, updated_at"
    ).eq("org_id", user["org_id"]).order("updated_at", desc=True).range(skip, skip + limit - 1)

    if scale:
        query = query.eq("scale", scale)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/competitors/{competitor_id}")
async def get_competitor(competitor_id: str, user=Depends(get_current_user)):
    """경쟁사 상세 (경쟁 이력 포함)."""
    client = await get_async_client()
    comp = await client.table("competitors").select("*").eq("id", competitor_id).single().execute()
    if not comp.data:
        raise TenopAPIError("KB_020", "경쟁사를 찾을 수 없습니다.", 404)

    history = await client.table("competitor_history").select("*").eq(
        "competitor_id", competitor_id
    ).order("created_at", desc=True).limit(20).execute()

    return {**comp.data, "competition_history": history.data or []}


@router.post("/competitors", status_code=201)
async def create_competitor(body: CompetitorCreateBody, user=Depends(get_current_user)):
    """경쟁사 등록."""
    from app.services.embedding_service import embedding_text_for_competitor, generate_embedding

    embed_text = embedding_text_for_competitor(body.company_name, body.primary_area or "", body.strengths or "")
    embedding = await generate_embedding(embed_text)

    client = await get_async_client()
    row = {
        **body.model_dump(),
        "org_id": user["org_id"],
        "created_by": user["id"],
        "embedding": embedding,
    }
    result = await client.table("competitors").insert(row).execute()
    return (result.data or [{}])[0]


@router.put("/competitors/{competitor_id}")
async def update_competitor(
    competitor_id: str,
    body: CompetitorUpdateBody,
    user=Depends(get_current_user),
):
    """경쟁사 수정."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise TenopAPIError("KB_021", "수정할 필드가 없습니다.", 400)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    client = await get_async_client()
    result = await client.table("competitors").update(updates).eq("id", competitor_id).execute()
    return (result.data or [{}])[0]


@router.delete("/competitors/{competitor_id}")
async def delete_competitor(competitor_id: str, user=Depends(require_role("lead", "admin"))):
    """경쟁사 삭제."""
    client = await get_async_client()
    await client.table("competitors").delete().eq("id", competitor_id).execute()
    return {"status": "ok"}


# ════════════════════════════════════════
# 교훈 아카이브 + 회고 워크시트
# ════════════════════════════════════════

class LessonCreateBody(BaseModel):
    proposal_id: str | None = None
    strategy_summary: str | None = None
    effective_points: str | None = None
    weak_points: str | None = None
    improvements: str | None = None
    failure_category: str | None = None
    failure_detail: str | None = None
    positioning: str | None = None
    client_name: str | None = None
    industry: str | None = None
    result: str | None = None


@router.get("/lessons")
async def list_lessons(
    result_filter: str | None = Query(None, alias="result"),
    positioning: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """교훈 아카이브 목록."""
    client = await get_async_client()
    query = client.table("lessons_learned").select(
        "id, strategy_summary, result, positioning, client_name, industry, failure_category, created_at"
    ).eq("org_id", user["org_id"]).order("created_at", desc=True).range(skip, skip + limit - 1)

    if result_filter:
        query = query.eq("result", result_filter)
    if positioning:
        query = query.eq("positioning", positioning)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, user=Depends(get_current_user)):
    """교훈 상세."""
    client = await get_async_client()
    result = await client.table("lessons_learned").select("*").eq("id", lesson_id).single().execute()
    if not result.data:
        raise TenopAPIError("KB_030", "교훈을 찾을 수 없습니다.", 404)
    return result.data


@router.post("/lessons", status_code=201)
async def create_lesson(body: LessonCreateBody, user=Depends(get_current_user)):
    """교훈 등록."""
    from app.services.embedding_service import embedding_text_for_lesson, generate_embedding

    embed_text = embedding_text_for_lesson(
        body.strategy_summary or "", body.effective_points or "",
        body.weak_points or "", body.industry or "",
    )
    embedding = await generate_embedding(embed_text)

    client = await get_async_client()
    row = {
        **body.model_dump(),
        "org_id": user["org_id"],
        "author_id": user["id"],
        "embedding": embedding,
    }
    result = await client.table("lessons_learned").insert(row).execute()
    return (result.data or [{}])[0]


# ════════════════════════════════════════
# 회고 워크시트
# ════════════════════════════════════════

class RetrospectBody(BaseModel):
    strategy_summary: str = ""
    effective_points: str = ""
    weak_points: str = ""
    improvements: str = ""
    failure_category: str | None = None
    failure_detail: str | None = None


@router.post("/retrospect/{proposal_id}", status_code=201)
async def submit_retrospect(
    proposal_id: str,
    body: RetrospectBody,
    user=Depends(get_current_user),
):
    """회고 워크시트 제출 → lessons_learned 자동 등록."""
    client = await get_async_client()

    proposal = await client.table("proposals").select(
        "id, positioning, result, project_name, org_id"
    ).eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise TenopAPIError("KB_040", "프로젝트를 찾을 수 없습니다.", 404)

    p = proposal.data
    result_map = {"won": "수주", "lost": "패찰", "cancelled": "유찰"}

    lesson_body = LessonCreateBody(
        proposal_id=proposal_id,
        strategy_summary=body.strategy_summary,
        effective_points=body.effective_points,
        weak_points=body.weak_points,
        improvements=body.improvements,
        failure_category=body.failure_category,
        failure_detail=body.failure_detail,
        positioning=p.get("positioning"),
        client_name=p.get("client_name"),
        result=result_map.get(p.get("result", ""), p.get("result")),
    )

    # 교훈 등록 (재사용)
    from app.services.embedding_service import embedding_text_for_lesson, generate_embedding

    embed_text = embedding_text_for_lesson(
        body.strategy_summary, body.effective_points,
        body.weak_points, "",
    )
    embedding = await generate_embedding(embed_text)

    row = {
        **lesson_body.model_dump(),
        "org_id": p.get("org_id", user["org_id"]),
        "author_id": user["id"],
        "embedding": embedding,
    }
    result = await client.table("lessons_learned").insert(row).execute()

    # 프로젝트 상태 업데이트
    await client.table("proposals").update({"status": "retrospect_done"}).eq("id", proposal_id).execute()

    return {"status": "ok", "lesson_id": (result.data or [{}])[0].get("id")}


# ════════════════════════════════════════
# 노임단가 (v3.4)
# ════════════════════════════════════════

class LaborRateBody(BaseModel):
    standard_org: str  # KOSA | KEA | MOEF
    year: int
    grade: str
    monthly_rate: int
    daily_rate: int | None = None
    effective_date: str | None = None
    source_url: str | None = None


@router.get("/labor-rates")
async def list_labor_rates(
    standard_org: str | None = None,
    year: int | None = None,
    grade: str | None = None,
    user=Depends(get_current_user),
):
    """노임단가 목록."""
    client = await get_async_client()
    query = client.table("labor_rates").select("*").order("year", desc=True).order("grade")

    if standard_org:
        query = query.eq("standard_org", standard_org)
    if year:
        query = query.eq("year", year)
    if grade:
        query = query.eq("grade", grade)

    result = await query.limit(200).execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.post("/labor-rates", status_code=201)
async def create_labor_rate(body: LaborRateBody, user=Depends(require_role("lead", "admin"))):
    """노임단가 등록."""
    client = await get_async_client()
    result = await client.table("labor_rates").insert(body.model_dump()).execute()
    return (result.data or [{}])[0]


@router.put("/labor-rates/{rate_id}")
async def update_labor_rate(
    rate_id: str,
    body: LaborRateBody,
    user=Depends(require_role("lead", "admin")),
):
    """노임단가 수정."""
    client = await get_async_client()
    result = await client.table("labor_rates").update(body.model_dump()).eq("id", rate_id).execute()
    return (result.data or [{}])[0]


@router.delete("/labor-rates/{rate_id}")
async def delete_labor_rate(rate_id: str, user=Depends(require_role("admin"))):
    """노임단가 삭제."""
    client = await get_async_client()
    await client.table("labor_rates").delete().eq("id", rate_id).execute()
    return {"status": "ok"}


@router.post("/labor-rates/import")
async def import_labor_rates(
    file: UploadFile = File(...),
    user=Depends(require_role("admin")),
):
    """노임단가 CSV 일괄 임포트."""
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    rows = []
    for row in reader:
        try:
            rows.append({
                "standard_org": row["standard_org"],
                "year": int(row["year"]),
                "grade": row["grade"],
                "monthly_rate": int(row["monthly_rate"]),
                "daily_rate": int(row["daily_rate"]) if row.get("daily_rate") else None,
                "effective_date": row.get("effective_date") or None,
                "source_url": row.get("source_url") or None,
            })
        except (KeyError, ValueError) as e:
            raise TenopAPIError("KB_050", f"CSV 파싱 오류: {e}", 400)

    if not rows:
        raise TenopAPIError("KB_051", "임포트할 데이터가 없습니다.", 400)

    client = await get_async_client()
    await client.table("labor_rates").insert(rows).execute()
    return {"status": "ok", "imported": len(rows)}


# ════════════════════════════════════════
# 시장 낙찰가 벤치마크 (v3.4)
# ════════════════════════════════════════

class MarketPriceBody(BaseModel):
    project_title: str | None = None
    client_org: str | None = None
    domain: str
    budget: int | None = None
    winning_price: int | None = None
    bid_ratio: float | None = None
    num_bidders: int | None = None
    tech_price_ratio: str | None = None
    evaluation_method: str | None = None
    year: int
    source: str | None = None


@router.get("/market-prices")
async def list_market_prices(
    domain: str | None = None,
    year: int | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """시장 낙찰가 벤치마크 목록."""
    client = await get_async_client()
    query = client.table("market_price_data").select("*").order(
        "year", desc=True
    ).range(skip, skip + limit - 1)

    if domain:
        query = query.eq("domain", domain)
    if year:
        query = query.eq("year", year)
    if budget_min is not None:
        query = query.gte("budget", budget_min)
    if budget_max is not None:
        query = query.lte("budget", budget_max)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.post("/market-prices", status_code=201)
async def create_market_price(body: MarketPriceBody, user=Depends(require_role("lead", "admin"))):
    """시장 낙찰가 등록."""
    client = await get_async_client()
    row = body.model_dump()
    row["org_id"] = user["org_id"]
    result = await client.table("market_price_data").insert(row).execute()
    return (result.data or [{}])[0]


@router.put("/market-prices/{price_id}")
async def update_market_price(
    price_id: str,
    body: MarketPriceBody,
    user=Depends(require_role("lead", "admin")),
):
    """시장 낙찰가 수정."""
    client = await get_async_client()
    result = await client.table("market_price_data").update(body.model_dump()).eq("id", price_id).execute()
    return (result.data or [{}])[0]


@router.delete("/market-prices/{price_id}")
async def delete_market_price(price_id: str, user=Depends(require_role("admin"))):
    """시장 낙찰가 삭제."""
    client = await get_async_client()
    await client.table("market_price_data").delete().eq("id", price_id).execute()
    return {"status": "ok"}


# ════════════════════════════════════════
# KB 내보내기 (§20-5)
# ════════════════════════════════════════

@router.get("/export/{part}")
async def export_kb(
    part: str,
    user=Depends(require_role("lead", "director", "admin")),
):
    """KB CSV 내보내기 (capabilities, clients, competitors, content, lessons)."""
    client = await get_async_client()
    org_id = user["org_id"]

    table_map = {
        "capabilities": ("capabilities", ["id", "description", "tech_area", "track_record", "keywords"]),
        "clients": ("client_intelligence", ["id", "client_name", "client_type", "scale", "relationship", "eval_tendency", "location"]),
        "competitors": ("competitors", ["id", "company_name", "scale", "primary_area", "strengths", "weaknesses", "price_pattern"]),
        "content": ("content_library", ["id", "title", "type", "status", "quality_score", "industry", "tech_area", "tags"]),
        "lessons": ("lessons_learned", ["id", "strategy_summary", "result", "positioning", "client_name", "failure_category"]),
    }

    if part not in table_map:
        raise TenopAPIError("KB_060", f"유효하지 않은 내보내기 대상: {part}", 400)

    table_name, columns = table_map[part]
    result = await client.table(table_name).select(", ".join(columns)).eq(
        "org_id", org_id
    ).limit(5000).execute()

    rows = result.data or []
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for r in rows:
        writer.writerow({col: r.get(col, "") for col in columns})

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=kb_{part}.csv"},
    )
