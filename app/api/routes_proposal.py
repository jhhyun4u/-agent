"""
제안서 프로젝트 CRUD (§12-1)

POST /api/proposals          — 프로젝트 생성 (STEP 0부터)
POST /api/proposals/from-rfp — RFP 업로드로 생성 (STEP 1 직접)
POST /api/proposals/from-search — 공고번호로 생성 (rfp_fetch부터)
GET  /api/proposals          — 목록
GET  /api/proposals/{id}     — 상세
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role
from app.exceptions import PropNotFoundError
from app.utils.supabase_client import get_async_client

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


class ProposalCreate(BaseModel):
    name: str = ""
    mode: str = "full"
    search_query: dict | None = None


class ProposalFromSearch(BaseModel):
    bid_no: str
    mode: str = "full"


class ProposalListResponse(BaseModel):
    id: str
    name: str
    status: str
    positioning: str | None = None
    current_step: str | None = None
    created_at: str
    deadline: str | None = None


# ── 생성 ──

@router.post("", status_code=201)
async def create_proposal(body: ProposalCreate, user=Depends(get_current_user)):
    """프로젝트 생성 — STEP 0(공고 검색)부터 시작."""
    client = await get_async_client()
    proposal_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    row = {
        "id": proposal_id,
        "project_name": body.name or "새 프로젝트",
        "team_id": user.get("team_id", ""),
        "created_by": user["id"],
        "mode": body.mode,
        "status": "draft",
        "current_step": "start",
        "created_at": now,
        "updated_at": now,
    }
    await client.table("proposals").insert(row).execute()

    return {
        "id": proposal_id,
        "name": row["project_name"],
        "mode": body.mode,
        "entry_point": "search",
        "initial_state": {
            "project_id": proposal_id,
            "project_name": body.name or "",
            "mode": body.mode,
            "search_query": body.search_query or {},
        },
    }


@router.post("/from-rfp", status_code=201)
async def create_from_rfp(
    mode: str = Form("lite"),
    rfp_file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """RFP 파일 업로드로 프로젝트 생성 — STEP 1 직접 진입."""
    client = await get_async_client()
    proposal_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # RFP 파일 텍스트 추출
    content = await rfp_file.read()
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

    row = {
        "id": proposal_id,
        "project_name": filename.rsplit(".", 1)[0] if filename else "RFP 직접 업로드",
        "team_id": user.get("team_id", ""),
        "created_by": user["id"],
        "mode": mode,
        "status": "draft",
        "current_step": "start",
        "created_at": now,
        "updated_at": now,
    }
    await client.table("proposals").insert(row).execute()

    return {
        "id": proposal_id,
        "name": row["project_name"],
        "mode": mode,
        "entry_point": "direct_rfp",
        "initial_state": {
            "project_id": proposal_id,
            "project_name": row["project_name"],
            "mode": mode,
            "rfp_raw": rfp_text,
        },
    }


@router.post("/from-search", status_code=201)
async def create_from_search(body: ProposalFromSearch, user=Depends(get_current_user)):
    """공고번호로 프로젝트 생성 — rfp_fetch부터 시작."""
    client = await get_async_client()
    proposal_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    row = {
        "id": proposal_id,
        "project_name": f"공고 {body.bid_no}",
        "team_id": user.get("team_id", ""),
        "created_by": user["id"],
        "mode": body.mode,
        "status": "draft",
        "current_step": "start",
        "created_at": now,
        "updated_at": now,
    }
    await client.table("proposals").insert(row).execute()

    return {
        "id": proposal_id,
        "name": row["project_name"],
        "mode": body.mode,
        "entry_point": "direct_fetch",
        "initial_state": {
            "project_id": proposal_id,
            "project_name": row["project_name"],
            "mode": body.mode,
            "picked_bid_no": body.bid_no,
        },
    }


# ── 조회 ──

@router.get("")
async def list_proposals(
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """프로젝트 목록 (포지셔닝·단계·마감일 포함)."""
    client = await get_async_client()
    query = client.table("proposals").select(
        "id, project_name, status, positioning, current_step, created_at, deadline, mode"
    ).eq("team_id", user.get("team_id", "")).order("created_at", desc=True).range(skip, skip + limit - 1)

    if status:
        query = query.eq("status", status)

    result = await query.execute()
    return {"items": result.data or [], "total": len(result.data or [])}


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, user=Depends(get_current_user)):
    """프로젝트 상세."""
    client = await get_async_client()
    result = await client.table("proposals").select("*").eq("id", proposal_id).single().execute()
    if not result.data:
        raise PropNotFoundError(proposal_id)
    return result.data
