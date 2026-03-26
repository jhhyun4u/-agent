"""공통서식 라이브러리 API (Phase C)

form_templates CRUD + Storage 연동.
모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
import mimetypes
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.api.response import ok, ok_list
from app.config import settings
from app.exceptions import (
    FileUploadError,
    InvalidRequestError,
    OwnershipRequiredError,
    ResourceNotFoundError,
    TeamAccessDeniedError,
)
from app.utils.file_utils import validate_extension
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["form-templates"])


# ── 스키마 ────────────────────────────────────────────────────────────

class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    agency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


# ── 엔드포인트 ────────────────────────────────────────────────────────

@router.get("/form-templates")
async def list_form_templates(
    user=Depends(get_current_user),
    agency: Optional[str] = Query(None, description="발주 기관 필터"),
    category: Optional[str] = Query(None, description="서식 유형 필터"),
    scope: str = Query("all", description="all | team | personal"),
):
    """공통서식 목록 조회"""
    client = await get_async_client()

    query = client.table("form_templates").select(
        "id, owner_id, team_id, title, agency, category, description, "
        "storage_path, file_type, is_public, use_count, created_at"
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

    if agency:
        query = query.eq("agency", agency)
    if category:
        query = query.eq("category", category)

    query = query.order("created_at", desc=True)
    res = await query.execute()
    items = res.data or []
    return ok_list(items, total=len(items))


@router.post("/form-templates", status_code=201)
async def upload_form_template(
    file: UploadFile = File(...),
    title: str = Form(...),
    agency: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    team_id: Optional[str] = Form(None),
    user=Depends(get_current_user),
):
    """공통서식 업로드 (PDF / DOCX)"""
    ext_raw = validate_extension(file.filename or "", "template")
    ext = f".{ext_raw}"

    # 팀 소속 확인 (team_id 제공 시)
    client = await get_async_client()
    if team_id:
        team_res = (
            await client.table("team_members")
            .select("role")
            .eq("team_id", team_id)
            .eq("user_id", user.id)
            .maybe_single()
            .execute()
        )
        if not team_res.data:
            raise TeamAccessDeniedError("해당 팀의 멤버가 아닙니다.")

    mime_type = mimetypes.types_map.get(ext) or file.content_type or "application/octet-stream"
    content = await file.read()

    storage_path = f"templates/{user.id}/{uuid4()}{ext}"

    # Supabase Storage 업로드
    try:
        await client.storage.from_(settings.storage_bucket_proposals).upload(
            storage_path, content, {"content-type": mime_type}
        )
    except Exception as exc:
        logger.error("Storage upload failed: %s", exc)
        raise FileUploadError("파일 업로드에 실패했습니다.")

    # DB 저장
    template_id = str(uuid4())
    insert_data = {
        "id": template_id,
        "owner_id": user.id,
        "title": title,
        "storage_path": storage_path,
        "file_type": ext.lstrip("."),
        "is_public": is_public,
    }
    if agency:
        insert_data["agency"] = agency
    if category:
        insert_data["category"] = category
    if description:
        insert_data["description"] = description
    if team_id:
        insert_data["team_id"] = team_id

    await client.table("form_templates").insert(insert_data).execute()
    return ok({"template_id": template_id, "title": title})


@router.patch("/form-templates/{template_id}")
async def update_form_template(
    template_id: str,
    body: TemplateUpdate,
    user=Depends(get_current_user),
):
    """공통서식 메타데이터 수정 (소유자만)"""
    client = await get_async_client()

    res = (
        await client.table("form_templates")
        .select("owner_id")
        .eq("id", template_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise ResourceNotFoundError("서식")
    if res.data["owner_id"] != user.id:
        raise OwnershipRequiredError("본인 서식만 수정할 수 있습니다.")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise InvalidRequestError("수정할 필드가 없습니다.")

    await (
        client.table("form_templates")
        .update(update_data)
        .eq("id", template_id)
        .eq("owner_id", user.id)
        .execute()
    )
    return ok({"template_id": template_id, **update_data})


@router.delete("/form-templates/{template_id}", status_code=204)
async def delete_form_template(template_id: str, user=Depends(get_current_user)):
    """공통서식 삭제 (소유자만, Storage + DB 동시 삭제)"""
    client = await get_async_client()

    res = (
        await client.table("form_templates")
        .select("owner_id, storage_path")
        .eq("id", template_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise ResourceNotFoundError("서식")
    if res.data["owner_id"] != user.id:
        raise OwnershipRequiredError("본인 서식만 삭제할 수 있습니다.")

    # Storage 파일 삭제 (실패해도 DB는 삭제)
    try:
        await client.storage.from_(settings.storage_bucket_proposals).remove([res.data["storage_path"]])
    except Exception as exc:
        logger.warning("Storage delete failed (continuing): %s", exc)

    await (
        client.table("form_templates")
        .delete()
        .eq("id", template_id)
        .eq("owner_id", user.id)
        .execute()
    )
