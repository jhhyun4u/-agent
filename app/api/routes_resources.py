"""섹션 라이브러리 및 제안서 아카이브 API (Platform v2 Phase A)

섹션 CRUD, 제안서 아카이브 조회.
모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
import math
import mimetypes
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.services.asset_extractor import extract_sections_from_asset
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["resources"])


# ── 스키마 ────────────────────────────────────────────────────────────

VALID_CATEGORIES = (
    "company_intro", "track_record", "methodology",
    "organization", "schedule", "cost", "other",
)


class SectionCreate(BaseModel):
    title: str
    category: str
    content: str
    tags: List[str] = []
    is_public: bool = False
    team_id: Optional[str] = None


class SectionUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


# ── 섹션 ─────────────────────────────────────────────────────────────

@router.get("/resources/sections")
async def list_sections(
    user=Depends(get_current_user),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    q: Optional[str] = Query(None, description="제목/내용 검색"),
    scope: str = Query("all", description="all | team | personal"),
):
    """섹션 라이브러리 목록 조회"""
    client = await get_async_client()

    query = client.table("sections").select(
        "id, title, category, content, tags, is_public, use_count, "
        "owner_id, team_id, created_at, updated_at"
    )

    if scope == "personal":
        query = query.eq("owner_id", user.id)
    elif scope == "team":
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)
    else:
        # all: 본인 소유 + 팀 소속 + 공개
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(
                f"owner_id.eq.{user.id},"
                f"team_id.in.({team_ids_csv}),"
                f"is_public.eq.true"
            )
        else:
            query = query.or_(f"owner_id.eq.{user.id},is_public.eq.true")

    if category:
        query = query.eq("category", category)
    if q:
        q_safe = q.replace("%", r"\%").replace("_", r"\_")
        query = query.or_(f"title.ilike.%{q_safe}%,content.ilike.%{q_safe}%")

    query = query.order("created_at", desc=True)
    res = await query.execute()
    return {"sections": res.data or []}


@router.post("/resources/sections", status_code=201)
async def create_section(body: SectionCreate, user=Depends(get_current_user)):
    """섹션 생성"""
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"category는 {', '.join(VALID_CATEGORIES)} 중 하나여야 합니다.",
        )
    client = await get_async_client()

    # 팀 소속 확인 (team_id 제공 시)
    if body.team_id:
        team_res = (
            await client.table("team_members")
            .select("role")
            .eq("team_id", body.team_id)
            .eq("user_id", user.id)
            .maybe_single()
            .execute()
        )
        if not team_res.data:
            raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")

    section_id = str(uuid4())
    insert_data = {
        "id": section_id,
        "owner_id": user.id,
        "title": body.title,
        "category": body.category,
        "content": body.content,
        "tags": body.tags,
        "is_public": body.is_public,
    }
    if body.team_id:
        insert_data["team_id"] = body.team_id

    await client.table("sections").insert(insert_data).execute()
    return {"section_id": section_id, "title": body.title, "category": body.category}


@router.put("/resources/sections/{section_id}")
async def update_section(
    section_id: str, body: SectionUpdate, user=Depends(get_current_user)
):
    """섹션 수정 (소유자만)"""
    if body.category is not None and body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"category는 {', '.join(VALID_CATEGORIES)} 중 하나여야 합니다.",
        )
    client = await get_async_client()

    res = (
        await client.table("sections")
        .select("owner_id")
        .eq("id", section_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
    if res.data["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="본인 섹션만 수정할 수 있습니다.")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")

    await (
        client.table("sections")
        .update(update_data)
        .eq("id", section_id)
        .eq("owner_id", user.id)
        .execute()
    )
    return {"section_id": section_id, **update_data}


@router.delete("/resources/sections/{section_id}", status_code=204)
async def delete_section(section_id: str, user=Depends(get_current_user)):
    """섹션 삭제 (소유자만)"""
    client = await get_async_client()

    res = (
        await client.table("sections")
        .select("owner_id")
        .eq("id", section_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
    if res.data["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="본인 섹션만 삭제할 수 있습니다.")

    await (
        client.table("sections")
        .delete()
        .eq("id", section_id)
        .eq("owner_id", user.id)
        .execute()
    )


# ── 회사 자료 ─────────────────────────────────────────────────────────

ALLOWED_ASSET_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/assets", status_code=201)
async def upload_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """회사 자료 파일 업로드 (PDF / DOCX)

    업로드 완료 후 백그라운드에서 AI 섹션 자동 추출을 실행합니다.
    추출 진행 중 status는 'processing', 완료 시 'done', 실패 시 'failed'로 변경됩니다.
    """
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="PDF 또는 DOCX 파일만 업로드 가능합니다.")

    mime_type = mimetypes.types_map.get(ext) or file.content_type or "application/octet-stream"

    # 스트림이므로 Storage 업로드 전에 미리 읽어야 함
    content = await file.read()

    storage_path = f"assets/{user.id}/{uuid4()}{ext}"
    client = await get_async_client()

    # Supabase Storage 업로드
    try:
        await client.storage.from_("proposal-files").upload(
            storage_path, content, {"content-type": mime_type}
        )
    except Exception as exc:
        logger.error("Storage upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="파일 업로드에 실패했습니다.")

    # 팀 ID 조회 (첫 번째 팀 소속 기준)
    team_res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user.id)
        .limit(1)
        .execute()
    )
    team_id = team_res.data[0]["team_id"] if team_res.data else None

    # DB 저장 (초기 status: 'pending' — 백그라운드 추출 대기)
    asset_id = str(uuid4())
    await client.table("company_assets").insert({
        "id": asset_id,
        "owner_id": user.id,
        "team_id": team_id,
        "filename": file.filename,
        "storage_path": storage_path,
        "file_type": ext.lstrip("."),
        "status": "pending",
    }).execute()

    # 백그라운드로 AI 섹션 추출 실행
    background_tasks.add_task(
        _run_extraction,
        asset_id=asset_id,
        owner_id=user.id,
        team_id=team_id,
        file_content=content,
        file_type=ext.lstrip("."),
        filename=file.filename or "",
    )

    return {"asset_id": asset_id, "filename": file.filename, "status": "pending"}


async def _run_extraction(
    asset_id: str,
    owner_id: str,
    team_id: str | None,
    file_content: bytes,
    file_type: str,
    filename: str,
) -> None:
    """백그라운드 섹션 추출 실행

    1. status를 'processing'으로 업데이트
    2. extract_sections_from_asset 호출
    3. 결과에 따라 status를 'done' 또는 'failed'로 업데이트
    """
    client = await get_async_client()
    try:
        # 처리 시작 표시
        await (
            client.table("company_assets")
            .update({"status": "processing"})
            .eq("id", asset_id)
            .execute()
        )

        # AI 섹션 추출
        section_ids = await extract_sections_from_asset(
            asset_id=asset_id,
            owner_id=owner_id,
            team_id=team_id,
            file_content=file_content,
            file_type=file_type,
            filename=filename,
        )

        # 완료 업데이트
        await (
            client.table("company_assets")
            .update({
                "status": "done",
                "extracted_sections": section_ids,
            })
            .eq("id", asset_id)
            .execute()
        )
        logger.info("[_run_extraction] asset_id=%s 완료, 섹션 %d개", asset_id, len(section_ids))

    except Exception as exc:
        logger.error("[_run_extraction] asset_id=%s 실패: %s", asset_id, exc)
        try:
            await (
                client.table("company_assets")
                .update({"status": "failed"})
                .eq("id", asset_id)
                .execute()
            )
        except Exception as update_exc:
            logger.error(
                "[_run_extraction] status 업데이트 실패 (asset_id=%s): %s",
                asset_id,
                update_exc,
            )


@router.get("/assets")
async def list_assets(user=Depends(get_current_user)):
    """회사 자료 목록 조회 (내 자료 + 팀 자료)"""
    client = await get_async_client()

    team_res = (
        await client.table("team_members")
        .select("team_id")
        .eq("user_id", user.id)
        .execute()
    )
    my_team_ids = [r["team_id"] for r in (team_res.data or [])]

    query = client.table("company_assets").select(
        "id, owner_id, team_id, filename, storage_path, file_type, status, created_at"
    )

    if my_team_ids:
        team_ids_csv = ",".join(my_team_ids)
        query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
    else:
        query = query.eq("owner_id", user.id)

    res = await query.order("created_at", desc=True).execute()
    return {"assets": res.data or []}


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(asset_id: str, user=Depends(get_current_user)):
    """회사 자료 삭제 (소유자만)"""
    client = await get_async_client()

    res = (
        await client.table("company_assets")
        .select("owner_id, storage_path")
        .eq("id", asset_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="자료를 찾을 수 없습니다.")
    if res.data["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="본인 자료만 삭제할 수 있습니다.")

    # Storage 파일 삭제 (실패해도 DB는 삭제)
    try:
        await client.storage.from_("proposal-files").remove([res.data["storage_path"]])
    except Exception as exc:
        logger.warning("Storage delete failed (continuing): %s", exc)

    await (
        client.table("company_assets")
        .delete()
        .eq("id", asset_id)
        .eq("owner_id", user.id)
        .execute()
    )


# ── 제안서 아카이브 ───────────────────────────────────────────────────

@router.get("/archive")
async def list_archive(
    user=Depends(get_current_user),
    scope: str = Query("personal", description="company | team | personal"),
    win_result: Optional[str] = Query(None, description="won | lost | pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """제안서 아카이브 조회 (완료된 제안서 중심)"""
    client = await get_async_client()

    query = client.table("proposals").select(
        "id, title, status, owner_id, team_id, win_result, bid_amount, "
        "notes, current_phase, phases_completed, created_at, updated_at"
    ).eq("status", "completed")

    if scope == "personal":
        query = query.eq("owner_id", user.id)
    elif scope == "team":
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)
    else:
        # company: 접근 가능한 모든 제안서
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)

    if win_result:
        if win_result not in ("won", "lost", "pending"):
            raise HTTPException(
                status_code=400, detail="win_result는 won, lost, pending 중 하나여야 합니다."
            )
        query = query.eq("win_result", win_result)

    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

    res = await query.execute()
    items = res.data or []

    # 전체 건수 (간이 방식: 반환된 결과 기반)
    total = len(items) + offset if len(items) == page_size else offset + len(items)
    pages = math.ceil(total / page_size) if page_size > 0 else 1

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }
