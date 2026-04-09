"""
제안서 프로젝트 CRUD (§12-1)

POST /api/proposals          — 프로젝트 생성 (rfp_analyze부터)
POST /api/proposals/from-rfp — RFP 업로드로 생성 (STEP 1 직접)
POST /api/proposals/from-bid — 공고 모니터링에서 제안 시작 (STEP 1 직접)
GET  /api/proposals          — 목록
GET  /api/proposals/{id}     — 상세
"""

import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_rls_client
from app.api.response import ok_list
from app.config import settings
from app.exceptions import PropNotFoundError, G2BServiceError
from app.models.auth_schemas import CurrentUser
from app.models.proposal_schemas import ProposalCreateResponse
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


class ProposalUpdate(BaseModel):
    owner_id: str | None = None


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
    """공고 모니터링에서 제안결정 → 제안 프로젝트 생성.

    1. bid_announcements에서 공고 정보 조회
    2. 마크다운 문서 로드 (RFP분석, 공고문, 과업지시서)
    3. proposals 테이블에 제안 프로젝트 생성
    4. 공고 첨부파일 복사 (백그라운드)
    """
    proposal_id = str(uuid.uuid4())
    client = await get_async_client()

    # 현재 사용자의 ID 사용 (get_current_user가 항상 CurrentUser 반환, DEV_MODE에서도)
    print(f"[HTTP] Received user object: id={user.id[:8]}..., team_id={user.team_id}, email={user.email}")
    owner_id = user.id

    # 1) bid_announcements에서 공고 정보 조회
    try:
        bid_result = await client.table("bid_announcements").select("*").eq("bid_no", body.bid_no).maybe_single().execute()
        bid = bid_result.data if bid_result else None
        logger.info(f"[from-bid] bid 쿼리 결과: {bid is not None}")
    except Exception as e:
        logger.error(f"[from-bid] 공고 조회 실패: {str(e)}")
        bid = None

    # bid가 없으면 기본값 사용 (테스트 모드)
    if not bid:
        logger.warning(f"[from-bid] 공고 없음: {body.bid_no}, 기본값으로 진행")
        title = f"공고 {body.bid_no}"
        rfp_content = ""
        org_id = None
        division_id = None
    else:
        title = bid.get("bid_title", f"공고 {body.bid_no}")
        if not title:
            title = f"공고 {body.bid_no}"
        org_id = bid.get("org_id")
        division_id = bid.get("division_id")

        # 마크다운 콘텐츠 로드
        rfp_content = ""
        # ... (선택사항)

    # 3) proposals 테이블에 제안 프로젝트 생성
    print(f"\n=== [from-bid] 제안 생성 시작: {proposal_id} ===")
    logger.info(f"[from-bid] 제안 생성: {proposal_id}, owner_id={owner_id}, team_id={user.team_id}")
    try:
        proposal_data = {
            "id": proposal_id,
            "title": title,
            "status": "initialized",
            "rfp_content": rfp_content,
            "rfp_content_truncated": len(rfp_content) > 50000,
            "rfp_filename": f"{body.bid_no}.md",
            "owner_id": owner_id,  # RLS를 위해 owner_id 필수
        }

        # 사용자의 team_id를 자동으로 설정 (목록 조회 기본 필터가 team_id이므로 필수)
        if user.team_id:
            proposal_data["team_id"] = user.team_id
            logger.info(f"[from-bid] team_id 설정: {user.team_id}")
        else:
            logger.warning(f"[from-bid] 사용자의 team_id가 없음")

        # org_id와 division_id가 있으면 추가
        if org_id:
            proposal_data["org_id"] = org_id
        if division_id:
            proposal_data["division_id"] = division_id

        logger.info(f"[from-bid] INSERT 데이터: {proposal_data}")

        # Supabase insert
        insert_result = await client.table("proposals").insert(proposal_data).execute()

        logger.info(f"[from-bid] OK 제안 생성 완료: {proposal_id}, 데이터: {insert_result.data}")
    except Exception as e:
        error_msg = f"[from-bid] 제안 생성 실패: {str(e)}"
        print(error_msg)
        print(f"[from-bid] 에러 타입: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        logger.error(error_msg)
        logger.error(f"[from-bid] 시도한 데이터: {proposal_data}")
        raise G2BServiceError(f"제안 프로젝트 생성 중 오류: {str(e)}")

    return {
        "proposal_id": proposal_id,
        "title": title,
        "status": "initialized",
        "entry_point": "from_bid",
        "bid_no": body.bid_no,
    }


# ── 조회 ──

@router.get("")
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
    for col in ("deadline", "client_name", "budget"):
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
        # 기본: owner_id 필터 (팀 필터 대신, 사용자가 소유한 제안만)
        # team_id가 NULL인 제안들도 보이도록 함
        if user:
            query = query.eq("owner_id", user.id)

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
        # 기본: owner_id 필터 (팀 필터 대신)
        if user:
            count_query = count_query.eq("owner_id", user.id)
    if status and status in _STATUS_GROUPS:
        count_query = count_query.in_("status", _STATUS_GROUPS[status])
    elif status:
        count_query = count_query.eq("status", status)
    if search:
        count_query = count_query.ilike("title", f"%{search}%")
    count_result = await count_query.execute()
    total = count_result.count if count_result.count is not None else len(count_result.data or [])

    result = await query.execute()
    data = result.data or []

    # 데이터 보강: team_name, owner_name, fit_score
    if data:
        # Fetch team names
        team_ids = {p.get("team_id") for p in data if p.get("team_id")}
        team_map = {}
        if team_ids:
            teams_result = await client.table("teams").select("id, name").in_("id", list(team_ids)).execute()
            team_map = {t["id"]: t.get("name") for t in (teams_result.data or [])}

        # Fetch owner names
        owner_ids = {p.get("owner_id") for p in data if p.get("owner_id")}
        owner_map = {}
        if owner_ids:
            owners_result = await client.table("users").select("id, name").in_("id", list(owner_ids)).execute()
            owner_map = {u["id"]: u.get("name") for u in (owners_result.data or [])}

        # Fetch fit scores from go_no_go
        proposal_ids = [p["id"] for p in data]
        fit_map = {}
        if proposal_ids:
            gng_result = await client.table("go_no_go").select("proposal_id, feasibility_score").in_("proposal_id", proposal_ids).execute()
            fit_map = {g["proposal_id"]: g.get("feasibility_score") for g in (gng_result.data or [])}

        # Enrich data
        for p in data:
            p["team_name"] = team_map.get(p.get("team_id"))
            p["owner_name"] = owner_map.get(p.get("owner_id"))
            p["fit_score"] = fit_map.get(p["id"])

    return ok_list(data, total=total, offset=skip, limit=limit)


@router.get("/{proposal_id}")
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


@router.patch("/{proposal_id}")
async def update_proposal(
    proposal_id: str,
    body: ProposalUpdate,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """프로젝트 정보 수정 (owner_id 등).

    현재는 owner_id 업데이트만 지원. 소유자만 수정 가능.
    """
    client = rls_client

    # 프로젝트 존재 확인
    prop = await client.table("proposals").select("id, owner_id, status").eq("id", proposal_id).maybe_single().execute()
    if not prop.data:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다")

    # 작업대기 상태에서는 owner_id 업데이트 가능, 다른 상태에서는 소유자 확인
    if prop.data["status"] != "initialized" and prop.data["owner_id"] != user.id:
        raise HTTPException(403, "수정 권한이 없습니다")

    # 업데이트할 필드만 추출
    update_data = {}
    if body.owner_id:
        update_data["owner_id"] = body.owner_id

    if not update_data:
        raise HTTPException(400, "업데이트할 필드가 없습니다")

    result = await client.table("proposals").update(update_data).eq("id", proposal_id).execute()

    if not result.data:
        raise HTTPException(500, "프로젝트 업데이트 실패")

    return {"message": "프로젝트 정보 업데이트 완료"}


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
    # HOTFIX: Check for active workflow states (Phase 0 - was checking for "running" which violates CHECK constraint)
    active_states = ('processing', 'searching', 'analyzing', 'strategizing', 'submitted', 'presented')
    if prop.data["status"] in active_states:
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


# ── 워크플로우 시간 및 토큰 추적 ──


class StartWithMembersRequest(BaseModel):
    """제안작업 시작 시 참여자 선택."""
    participants: list[str]  # 선택된 참여자 user_id 리스트


@router.post("/{proposal_id}/start-with-members")
async def start_proposal_with_members(
    proposal_id: str,
    body: StartWithMembersRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """제안작업 시작 (참여자 선택).

    workflow_started_at 설정 + 참여자 저장 (proposal_members).

    Args:
        proposal_id: 제안서 ID
        body.participants: 선택된 참여자 user_id 리스트

    Returns:
        {
            "proposal_id": str,
            "started_at": str (ISO8601),
            "members_added": int
        }
    """
    from app.services.workflow_timer import WorkflowTimer

    try:
        result = await WorkflowTimer.start_workflow(proposal_id, body.participants)
        return result
    except Exception as e:
        logger.error(f"Error starting proposal {proposal_id} with members: {str(e)}")
        raise HTTPException(500, f"제안작업 시작 중 오류: {str(e)}")


@router.post("/{proposal_id}/track-tokens")
async def track_proposal_tokens(
    proposal_id: str,
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-sonnet-4-5-20250929",
    user: CurrentUser = Depends(get_current_user),
):
    """토큰 사용량 실시간 추적.

    제안작업 중 호출 → proposals 테이블에 누적 저장.

    Args:
        proposal_id: 제안서 ID
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        model: Claude 모델 이름

    Returns:
        {
            "proposal_id": str,
            "total_tokens": int,
            "total_cost_usd": float,
            "total_cost_formatted": str (e.g., "$4.26")
        }
    """
    from app.services.workflow_timer import WorkflowTimer

    try:
        result = await WorkflowTimer.track_token_usage(
            proposal_id, input_tokens, output_tokens, model
        )
        return result
    except Exception as e:
        logger.error(f"Error tracking tokens for {proposal_id}: {str(e)}")
        raise HTTPException(500, f"토큰 추적 중 오류: {str(e)}")


@router.get("/{proposal_id}/members")
async def get_proposal_members(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """해당 제안서의 참여자 목록 조회.

    Args:
        proposal_id: 제안서 ID

    Returns:
        {
            "members": [
                {
                    "user_id": str,
                    "role": str,
                    "joined_at": str,
                    "users": {
                        "name": str,
                        "email": str
                    }
                },
                ...
            ]
        }
    """
    try:
        client = rls_client
        result = await client.table("proposal_members").select(
            "user_id, role, joined_at, users(name, email)"
        ).eq("proposal_id", proposal_id).execute()

        return {"members": result.data or []}
    except Exception as e:
        logger.error(f"Error getting members for {proposal_id}: {str(e)}")
        raise HTTPException(500, f"참여자 조회 중 오류: {str(e)}")


@router.get("/{proposal_id}/workflow-stats")
async def get_workflow_stats(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """워크플로우 통계 조회.

    작업시간, 토큰비용, 참여자 정보를 한 번에 조회.

    Args:
        proposal_id: 제안서 ID

    Returns:
        {
            "proposal_id": str,
            "elapsed_seconds": int,
            "elapsed_formatted": str (e.g., "2h 30m"),
            "total_tokens": int,
            "total_cost_usd": float,
            "total_cost_formatted": str (e.g., "$4.26"),
            "members": list
        }
    """
    from app.services.workflow_timer import WorkflowTimer

    try:
        result = await WorkflowTimer.get_workflow_stats(proposal_id)
        return result
    except Exception as e:
        logger.error(f"Error getting workflow stats for {proposal_id}: {str(e)}")
        raise HTTPException(500, f"워크플로우 통계 조회 중 오류: {str(e)}")


# ── HITL 리뷰 엔드포인트 ──


class ReviewItemStatus(BaseModel):
    """검토 항목 상태."""
    id: str
    step_name: str
    section_name: str
    status: str  # pending | in_review | approved | rejected
    created_at: str
    updated_at: str | None = None


class ReviewFeedback(BaseModel):
    """검토 피드백."""
    id: str
    feedback_text: str
    submitted_by_name: str
    submitted_at: str
    decision: str | None = None


class ReviewItemDetail(BaseModel):
    """검토 항목 상세."""
    id: str
    step_name: str
    section_name: str
    artifact_content: str
    artifact_type: str  # text | markdown
    status: str
    feedback_history: list[ReviewFeedback] = []


class SubmitReviewFeedback(BaseModel):
    """검토 피드백 제출."""
    feedback_text: str
    decision: str  # approved | rejected | pending


@router.get("/{proposal_id}/review-items")
async def get_review_items(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """검토 대기 항목 목록 조회.

    Args:
        proposal_id: 제안서 ID

    Returns:
        {
            "items": [
                {
                    "id": str,
                    "step_name": str,
                    "section_name": str,
                    "status": str,
                    "created_at": str,
                    "updated_at": str | None
                }
            ],
            "stats": {
                "total": int,
                "pending": int,
                "in_review": int,
                "approved": int,
                "rejected": int
            }
        }
    """
    try:
        # proposal_id 검증 및 접근 권한 확인
        result = await rls_client.from_("proposals").select("id").eq("id", proposal_id).single()
        if not result.data:
            raise HTTPException(404, "제안서를 찾을 수 없습니다")

        # 검토 항목 조회 (step8_feedback 및 workflow_events 기반)
        # 현재는 더미 데이터로 반환 - 실제 구현 필요
        items = [
            {
                "id": "review-1",
                "step_name": "제안서 작성",
                "section_name": "Executive Summary",
                "status": "pending",
                "created_at": "2026-04-09T10:30:00+09:00",
                "updated_at": None,
            }
        ]

        stats = {
            "total": len(items),
            "pending": sum(1 for i in items if i["status"] == "pending"),
            "in_review": sum(1 for i in items if i["status"] == "in_review"),
            "approved": sum(1 for i in items if i["status"] == "approved"),
            "rejected": sum(1 for i in items if i["status"] == "rejected"),
        }

        return {"items": items, "stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review items for {proposal_id}: {str(e)}")
        raise HTTPException(500, f"검토 항목 조회 중 오류: {str(e)}")


@router.get("/{proposal_id}/review-items/{review_id}")
async def get_review_item_detail(
    proposal_id: str,
    review_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """검토 항목 상세 조회.

    Args:
        proposal_id: 제안서 ID
        review_id: 검토 항목 ID

    Returns:
        {
            "id": str,
            "step_name": str,
            "section_name": str,
            "artifact_content": str,
            "artifact_type": str,
            "status": str,
            "feedback_history": [
                {
                    "id": str,
                    "feedback_text": str,
                    "submitted_by_name": str,
                    "submitted_at": str,
                    "decision": str | None
                }
            ]
        }
    """
    try:
        # proposal_id 검증
        result = await rls_client.from_("proposals").select("id").eq("id", proposal_id).single()
        if not result.data:
            raise HTTPException(404, "제안서를 찾을 수 없습니다")

        # 더미 데이터로 반환 - 실제 구현 필요
        item_detail = {
            "id": review_id,
            "step_name": "제안서 작성",
            "section_name": "Executive Summary",
            "artifact_content": "제안서의 핵심을 3-5문장으로 요약하여 의사결정자의 주의를 끌어야 합니다.\n\n실제 산출물 내용이 여기에 표시됩니다.",
            "artifact_type": "text",
            "status": "pending",
            "feedback_history": [],
        }

        return item_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review item {review_id}: {str(e)}")
        raise HTTPException(500, f"검토 항목 상세 조회 중 오류: {str(e)}")


@router.post("/{proposal_id}/review-items/{review_id}/feedback")
async def submit_review_feedback(
    proposal_id: str,
    review_id: str,
    payload: SubmitReviewFeedback,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """검토 피드백 제출.

    Args:
        proposal_id: 제안서 ID
        review_id: 검토 항목 ID
        payload: 피드백 내용 및 의사결정

    Returns:
        {
            "id": str,
            "feedback_text": str,
            "decision": str,
            "submitted_by_name": str,
            "submitted_at": str
        }
    """
    try:
        # proposal_id 검증
        result = await rls_client.from_("proposals").select("id").eq("id", proposal_id).single()
        if not result.data:
            raise HTTPException(404, "제안서를 찾을 수 없습니다")

        # 피드백 저장 (step8_feedback 테이블)
        feedback_id = str(uuid.uuid4())
        feedback_data = {
            "id": feedback_id,
            "proposal_id": proposal_id,
            "feedback_text": payload.feedback_text,
            "submitted_by": user.id,
            "submitted_at": "2026-04-09T11:00:00+09:00",
            "decision": payload.decision,
        }

        # 실제 DB 저장 로직 필요
        # await rls_client.from_("step8_feedback").insert(feedback_data)

        return {
            "id": feedback_id,
            "feedback_text": payload.feedback_text,
            "decision": payload.decision,
            "submitted_by_name": user.name,
            "submitted_at": feedback_data["submitted_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting review feedback: {str(e)}")
        raise HTTPException(500, f"피드백 제출 중 오류: {str(e)}")
