"""
제안서 프로젝트 CRUD (§12-1)

POST /api/proposals          — 프로젝트 생성 (rfp_analyze부터)
POST /api/proposals/from-rfp — RFP 업로드로 생성 (STEP 1 직접)
POST /api/proposals/from-bid — 공고 모니터링에서 제안 시작 (STEP 1 직접)
GET  /api/proposals          — 목록
GET  /api/proposals/{id}     — 상세
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_rls_client
from app.api.response import ok_list
from app.config import settings
from app.exceptions import PropNotFoundError
from app.models.auth_schemas import CurrentUser
from app.models.common import ItemsResponse
from app.models.proposal_schemas import ProposalCreateResponse, ProposalDetail, ProposalListItem
from app.utils.supabase_client import get_async_client

logger = __import__("logging").getLogger(__name__)

BUCKET = settings.storage_bucket_proposals


async def _upload_file_to_storage(storage_path: str, content: bytes, content_type: str) -> None:
    """Storage 업로드 헬퍼 (BackgroundTask 용)."""
    try:
        client = await get_async_client()
        await client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        logger.info(f"Storage 업로드 완료: {storage_path}")
    except Exception as e:
        logger.warning(f"Storage 업로드 실패: {storage_path}: {e}")

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


class ProposalFromBid(BaseModel):
    bid_no: str


class ProposalListResponse(BaseModel):
    id: str
    name: str
    status: str
    positioning: str | None = None
    current_step: str | None = None
    created_at: str
    deadline: str | None = None


# ── 생성 ──


@router.post("/from-rfp", status_code=201, response_model=ProposalCreateResponse)
async def create_from_rfp(
    background_tasks: BackgroundTasks,
    rfp_file: UploadFile = File(...),
    rfp_title: str = Form(""),
    client_name: str = Form(""),
    mode: str = Form("lite"),
    user: CurrentUser = Depends(get_current_user),
):
    """RFP 파일 업로드로 프로젝트 생성 — STEP 1 직접 진입. RFP 원본 Storage 보존 (GAP-1)."""
    client = await get_async_client()
    proposal_id = str(uuid.uuid4())

    # RFP 파일 텍스트 추출
    content = await rfp_file.read()

    # H-4: 파일 크기 검증
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"파일 크기 초과: {len(content) // (1024*1024)}MB (최대 {settings.max_file_size_mb}MB)")

    rfp_text = ""
    filename = rfp_file.filename or ""

    if filename.endswith(".pdf"):
        try:
            from app.services.rfp_parser import parse_rfp_bytes
            rfp_text = await parse_rfp_bytes(content, "pdf")
        except Exception:
            rfp_text = content.decode("utf-8", errors="replace")
    elif filename.endswith((".hwp", ".hwpx")):
        try:
            from app.services.rfp_parser import parse_rfp_bytes
            rfp_text = await parse_rfp_bytes(content, filename.split(".")[-1])
        except Exception:
            rfp_text = "[HWP 파싱 실패 — 원본 업로드됨]"
    else:
        rfp_text = content.decode("utf-8", errors="replace")

    project_name = rfp_title or (filename.rsplit(".", 1)[0] if filename else "RFP 직접 업로드")
    user_id = user.id
    team_id = user.team_id

    # GAP-1: RFP 원본 Storage 경로
    storage_path_rfp = f"{proposal_id}/rfp/{filename}" if filename else None

    row = {
        "id": proposal_id,
        "title": project_name,
        "status": "initialized",
        "owner_id": user_id,
        "rfp_content": rfp_text[:10000] if rfp_text else "",
        "rfp_filename": filename,
    }
    if storage_path_rfp:
        row["storage_path_rfp"] = storage_path_rfp
    if team_id:
        row["team_id"] = team_id

    try:
        await client.table("proposals").insert(row).execute()
    except Exception as e:
        logger.warning(f"proposals insert 실패: {e}")

    # GAP-1: proposal_files 레코드 + Background Storage 업로드
    if storage_path_rfp and content:
        try:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            await client.table("proposal_files").insert({
                "proposal_id": proposal_id,
                "category": "rfp",
                "filename": filename,
                "storage_path": storage_path_rfp,
                "file_type": ext,
                "file_size": len(content),
                "uploaded_by": user_id,
            }).execute()
        except Exception as e:
            logger.warning(f"proposal_files insert 실패 (무시): {e}")

        background_tasks.add_task(
            _upload_file_to_storage, storage_path_rfp, content,
            rfp_file.content_type or "application/octet-stream",
        )

    return {
        "proposal_id": proposal_id,
        "title": project_name,
        "mode": mode,
        "entry_point": "direct_rfp",
    }


@router.post("/from-bid", status_code=201, response_model=ProposalCreateResponse)
async def create_from_bid(
    body: ProposalFromBid,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
):
    """공고 모니터링에서 제안결정 → 제안 프로젝트 생성 + 첨부파일 연결."""
    client = await get_async_client()
    proposal_id = str(uuid.uuid4())

    # 1) bid_announcements에서 공고 정보 조회 (raw_data 포함)
    bid_result = await client.table("bid_announcements").select(
        "bid_no, bid_title, agency, budget_amount, deadline_date, content_text, raw_data"
    ).eq("bid_no", body.bid_no).maybe_single().execute()

    bid = bid_result.data if bid_result.data else {}
    title = bid.get("bid_title") or f"공고 {body.bid_no}"
    rfp_text = bid.get("content_text") or ""
    raw_data = bid.get("raw_data") or {}

    # 2) 프로젝트 생성 (대기중 — 워크플로 시작 전)
    row: dict = {
        "id": proposal_id,
        "title": title,
        "owner_id": user.id,
        "status": "대기중",
        "rfp_content": rfp_text[:10000] if rfp_text else "",
        "rfp_content_truncated": len(rfp_text) > 10000,
    }
    if user.team_id:
        row["team_id"] = user.team_id
    if user.org_id:
        row["org_id"] = user.org_id

    await client.table("proposals").insert(row).execute()

    # 3) 공고 첨부파일 → proposal에 복사 (백그라운드)
    if raw_data:
        async def _link_attachments():
            try:
                from app.services.bid_attachment_store import copy_bid_attachments_to_proposal
                await copy_bid_attachments_to_proposal(body.bid_no, proposal_id, raw_data)
            except Exception as e:
                logger.warning(f"[{proposal_id}] 첨부파일 연결 실패: {e}")

        background_tasks.add_task(_link_attachments)

    return {
        "proposal_id": proposal_id,
        "title": title,
        "status": "대기중",
        "entry_point": "from_bid",
        "bid_no": body.bid_no,
    }


# ── 조회 ──

@router.get("", response_model=ItemsResponse[ProposalListItem])
async def list_proposals(
    status: str | None = None,
    scope: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """프로젝트 목록.

    scope: my (내 프로젝트), team (팀), division (본부), company (전체).
    scope 미지정 시 기존 동작 (팀 필터).
    C-2: RLS 적용 클라이언트로 사용자 권한 범위만 조회.
    """
    client = rls_client
    # deadline, client_name은 DB에 없을 수 있으므로 동적 탐지
    base_cols = "id, title, status, owner_id, team_id, current_phase, phases_completed, positioning, win_result, bid_amount, created_at, updated_at"
    extra_cols = []
    for col in ("deadline", "client_name"):
        try:
            await client.table("proposals").select(col).limit(0).execute()
            extra_cols.append(col)
        except Exception:
            pass
    select_cols = base_cols + (", " + ", ".join(extra_cols) if extra_cols else "")
    query = client.table("proposals").select(
        select_cols
    ).order("created_at", desc=True).range(skip, skip + limit - 1)

    if scope == "my" and user:
        query = query.eq("owner_id", user.id)
    elif scope == "team" and user and user.team_id:
        query = query.eq("team_id", user.team_id)
    elif scope == "division" and user and user.division_id:
        # 같은 본부 소속 팀들의 프로젝트
        teams_result = await client.table("teams").select("id").eq(
            "division_id", user.division_id
        ).execute()
        team_ids = [t["id"] for t in (teams_result.data or [])]
        if team_ids:
            query = query.in_("team_id", team_ids)
    elif scope == "company":
        pass  # 필터 없음 — 전체
    else:
        # 기본: 팀 필터 (기존 동작)
        if user and user.team_id:
            query = query.eq("team_id", user.team_id)

    # 상태 필터: 가상 그룹 → 실제 DB status 매핑
    _STATUS_GROUPS = {
        "processing": ["initialized", "processing", "searching", "analyzing", "strategizing"],
        "awaiting_result": ["submitted", "presented"],
        "completed": ["completed", "won", "lost", "retrospect"],
        "on_hold": ["on_hold", "abandoned"],
    }
    if status and status in _STATUS_GROUPS:
        query = query.in_("status", _STATUS_GROUPS[status])
    elif status:
        query = query.eq("status", status)

    if search:
        query = query.ilike("title", f"%{search}%")

    # total count (same filters, no pagination)
    count_query = client.table("proposals").select("id", count="exact")
    if scope == "my" and user:
        count_query = count_query.eq("owner_id", user.id)
    elif scope == "team" and user and user.team_id:
        count_query = count_query.eq("team_id", user.team_id)
    elif scope == "company":
        pass
    else:
        if user and user.team_id:
            count_query = count_query.eq("team_id", user.team_id)
    if status and status in _STATUS_GROUPS:
        count_query = count_query.in_("status", _STATUS_GROUPS[status])
    elif status:
        count_query = count_query.eq("status", status)
    if search:
        count_query = count_query.ilike("title", f"%{search}%")
    count_result = await count_query.execute()
    total = count_result.count if count_result.count is not None else len(count_result.data or [])

    result = await query.execute()
    return ok_list(result.data or [], total=total, offset=skip, limit=limit)


@router.get("/{proposal_id}", response_model=ProposalDetail)
async def get_proposal(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """프로젝트 상세. C-2: RLS 적용 — 접근 권한 없으면 404."""
    client = rls_client
    result = await client.table("proposals").select("*").eq("id", proposal_id).maybe_single().execute()
    if not result.data:
        raise PropNotFoundError(proposal_id)
    return result.data


@router.delete("/{proposal_id}", status_code=204)
async def delete_proposal(proposal_id: str, user: CurrentUser = Depends(get_current_user)):
    """프로젝트 삭제 + Storage 정리 (GAP-5). 소유자만 가능, 실행 중 삭제 방지."""
    client = await get_async_client()

    # 프로젝트 존재 + 소유자 확인
    prop = await client.table("proposals").select("id, owner_id, status").eq("id", proposal_id).maybe_single().execute()
    if not prop.data:
        raise PropNotFoundError(proposal_id)
    if prop.data["owner_id"] != user.id:
        raise HTTPException(403, "프로젝트 소유자만 삭제할 수 있습니다")
    if prop.data["status"] == "running":
        raise HTTPException(409, "실행 중인 프로젝트는 삭제할 수 없습니다")

    # Storage 파일 목록 조회 + 삭제 (best-effort)
    files_res = await client.table("proposal_files").select("storage_path").eq("proposal_id", proposal_id).execute()
    storage_paths = [f["storage_path"] for f in (files_res.data or []) if f.get("storage_path")]

    # proposals 테이블의 산출물 경로도 수집
    for col in ("storage_path_docx", "storage_path_pptx", "storage_path_hwpx", "storage_path_rfp"):
        path = prop.data.get(col)
        if path:
            storage_paths.append(path)

    if storage_paths:
        try:
            await client.storage.from_(BUCKET).remove(storage_paths)
        except Exception as e:
            logger.warning(f"Storage 정리 실패 (무시): {e}")

    # DB 삭제 (CASCADE: artifacts, feedbacks, proposal_files 자동 삭제)
    await client.table("proposals").delete().eq("id", proposal_id).execute()
