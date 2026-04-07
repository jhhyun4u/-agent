"""
프로젝트 아카이브 API — 마스터 파일 일람 + 스냅샷 + 개별 다운로드 + ZIP 번들

GET  /api/proposals/{id}/archive                      — 마스터 파일 일람
POST /api/proposals/{id}/archive/snapshot              — 현재 state → 전체 스냅샷
GET  /api/proposals/{id}/archive/{doc_type}/download   — 개별 파일 다운로드
GET  /api/proposals/{id}/archive/{doc_type}/versions   — 버전 이력
GET  /api/proposals/{id}/archive/bundle                — 전체 ZIP 다운로드
"""

import io
import logging
import zipfile
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import Response, StreamingResponse

from app.api.deps import get_current_user, require_project_access
from app.api.response import ok, ok_list
from app.config import settings
from app.models.auth_schemas import CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/proposals", tags=["project-archive"])

BUCKET = settings.storage_bucket_proposals


@router.get("/{proposal_id}/archive")
async def get_project_manifest(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """프로젝트 마스터 파일 일람 (전체 카테고리 통합 인덱스).

    카테고리: rfp, analysis, strategy, plan, proposal, presentation,
             bidding, review, submission, reference
    """
    from app.services.project_archive_service import get_project_manifest
    manifest = await get_project_manifest(proposal_id)
    return ok(manifest)


@router.post("/{proposal_id}/archive/snapshot", status_code=201)
async def create_snapshot(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """현재 LangGraph state에서 모든 중간 산출물을 파일화하여 아카이브.

    동기 실행: state 추출 후 모든 산출물을 파일화하고 201 응답 반환.
    """
    from app.api.routes_workflow import _get_graph
    from app.services.project_archive_service import snapshot_from_state

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}
    snapshot = await graph.aget_state(config)

    if not snapshot or not snapshot.values:
        from app.exceptions import PropNotFoundError
        raise PropNotFoundError(proposal_id)

    state = snapshot.values

    # 동기 실행 (state를 즉시 사용해야 하므로)
    archived = await snapshot_from_state(
        proposal_id,
        state,
        created_by=user.id,
    )

    return ok({
        "archived_count": len(archived),
        "items": [
            {"doc_type": r.get("doc_type"), "title": r.get("title"), "version": r.get("version")}
            for r in archived
        ],
    }, message="완료")


@router.get("/{proposal_id}/archive/{doc_type}/download")
async def download_archive_file(
    proposal_id: str,
    doc_type: str,
    version: int | None = Query(None, description="특정 버전 (미지정 시 최신)"),
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """아카이브 파일 개별 다운로드.

    Supabase Storage에 파일이 있으면 서명 URL 반환,
    없으면 현재 state에서 실시간 렌더링.
    """
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # DB에서 파일 조회
    query = client.table("project_archive").select("*").eq(
        "proposal_id", proposal_id
    ).eq("doc_type", doc_type)
    if version:
        query = query.eq("version", version)
    else:
        query = query.eq("is_latest", True)

    result = await query.maybe_single().execute()

    if result.data and result.data.get("storage_path"):
        # Storage에서 다운로드
        storage_path = result.data["storage_path"]
        file_format = result.data.get("file_format", "md")
        title = result.data.get("title", doc_type)

        try:
            data = await client.storage.from_(BUCKET).download(storage_path)
            content_type_map = {
                "md": "text/markdown; charset=utf-8",
                "txt": "text/plain; charset=utf-8",
                "json": "application/json; charset=utf-8",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "hwpx": "application/hwp+zip",
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            }
            return Response(
                content=data,
                media_type=content_type_map.get(file_format, "application/octet-stream"),
                headers={"Content-Disposition": f'attachment; filename="{title}.{file_format}"'},
            )
        except Exception as e:
            logger.warning(f"Storage 다운로드 실패 ({storage_path}), 실시간 렌더링 시도: {e}")

    # Storage에 없으면 현재 state에서 실시간 렌더링
    from app.services.project_archive_service import _DEF_MAP, render_artifact
    from app.api.routes_workflow import _get_graph

    defn = _DEF_MAP.get(doc_type)
    if not defn:
        from app.exceptions import InvalidRequestError
        raise InvalidRequestError(f"알 수 없는 문서 유형: {doc_type}")

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}
    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        from app.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("워크플로 데이터")

    content = render_artifact(defn, snapshot.values)
    if content is None:
        raise ResourceNotFoundError(f"{doc_type} 산출물")

    file_format = defn["file_format"]
    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8" if file_format == "md" else "text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{defn["title"]}.{file_format}"'},
    )


@router.get("/{proposal_id}/archive/{doc_type}/versions")
async def list_archive_versions(
    proposal_id: str,
    doc_type: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """산출물 버전 이력 조회."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    result = await client.table("project_archive").select(
        "id, version, file_size, source, graph_step, is_latest, created_by, created_at"
    ).eq("proposal_id", proposal_id).eq("doc_type", doc_type).order("version", desc=True).execute()

    versions = result.data or []
    return ok_list(versions, total=len(versions))


@router.get("/{proposal_id}/archive/bundle")
async def download_archive_bundle(
    proposal_id: str,
    category: str | None = Query(None, description="카테고리 필터 (미지정 시 전체)"),
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """프로젝트 전체 산출물 ZIP 번들 다운로드."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    query = client.table("project_archive").select(
        "doc_type, title, file_format, storage_path, category"
    ).eq("proposal_id", proposal_id).eq("is_latest", True)
    if category:
        query = query.eq("category", category)
    result = await query.execute()
    files = result.data or []

    if not files:
        from app.exceptions import FileNotFoundError_
        raise FileNotFoundError_("다운로드할 아카이브 파일이 없습니다")

    async def generate_zip() -> AsyncGenerator[bytes, None]:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                if not f.get("storage_path"):
                    continue
                try:
                    data = await client.storage.from_(BUCKET).download(f["storage_path"])
                    # 카테고리별 폴더에 정리
                    filename = f"{f['category']}/{f['title']}.{f['file_format']}"
                    zf.writestr(filename, data)
                except Exception as e:
                    logger.warning(f"번들 다운로드 파일 스킵: {f['title']} ({e})")
        yield buf.getvalue()

    return StreamingResponse(
        generate_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="archive_{proposal_id[:8]}.zip"'},
    )
