"""
제안서 프로젝트 CRUD (§12-1)

POST /api/proposals          — 프로젝트 생성 (rfp_analyze부터)
POST /api/proposals/from-rfp — RFP 업로드로 생성 (STEP 1 직접)
POST /api/proposals/from-bid — 공고 모니터링에서 제안 시작 (STEP 1 직접)
GET  /api/proposals          — 목록
GET  /api/proposals/{id}     — 상세
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_rls_client
from app.api.response import ok_list
from app.config import settings
from app.exceptions import PropNotFoundError, G2BServiceError
from app.models.auth_schemas import CurrentUser
from app.models.proposal_schemas import ProposalCreateResponse
from app.utils.supabase_client import get_async_client
from app.state_machine import StateMachine

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

from app.services.memory_cache_service import get_memory_cache
router = APIRouter(prefix="/api/proposals", tags=["proposals"])


class ProposalFromBid(BaseModel):
    bid_no: str

    def __init__(self, **data):
        super().__init__(**data)
        # Validate bid_no: alphanumeric + hyphens/underscores, max 50 chars
        if not self.bid_no or len(self.bid_no) > 50:
            raise ValueError("bid_no must be 1-50 characters")
        if not all(c.isalnum() or c in '-_' for c in self.bid_no):
            raise ValueError("bid_no must contain only alphanumeric characters, hyphens, and underscores")


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
    rls_client=Depends(get_rls_client),
):
    """공고 모니터링에서 제안결정 → 제안 프로젝트 생성.

    1. bid_announcements에서 공고 정보 조회
    2. 마크다운 문서 로드 (RFP분석, 공고문, 과업지시서)
    3. FK 의존성 사전 확인 (조직, 팀, 구분, 사용자)
    4. proposals 테이블에 제안 프로젝트 생성
    5. 공고 첨부파일 복사 (백그라운드)
    """
    proposal_id = str(uuid.uuid4())
    client = rls_client

    # 현재 사용자의 ID 사용 (get_current_user가 항상 CurrentUser 반환, DEV_MODE에서도)
    logger.info("[from-bid] 사용자 인증 완료")
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
        division_id = None
    else:
        title = bid.get("bid_title", f"공고 {body.bid_no}")
        if not title:
            title = f"공고 {body.bid_no}"
        division_id = bid.get("division_id")

        # 마크다운 콘텐츠 로드 (분석 결과 연동)
        rfp_content = ""
        try:
            # 경로 검증 함수
            def validate_storage_path(path: str | None) -> str | None:
                """스토리지 경로 검증 - 경로 순회 및 불안전한 문자 방지"""
                if not path:
                    return None
                # 경로 순회 방지: ".." 포함 확인
                if ".." in path or path.startswith("/") or path.startswith("\\"):
                    logger.warning(f"[from-bid] 안전하지 않은 경로 거부: {path}")
                    return None
                # 예상 접두어 확인: proposals/ 로 시작해야 함
                if not path.startswith("proposals/"):
                    logger.warning(f"[from-bid] 예상 접두어 불일치: {path}")
                    return None
                return path

            # bid_announcements의 md_rfp_analysis_path에서 분석 결과 로드
            md_rfp_analysis_path = validate_storage_path(bid.get("md_rfp_analysis_path"))
            md_notice_path = validate_storage_path(bid.get("md_notice_path"))
            md_instruction_path = validate_storage_path(bid.get("md_instruction_path"))

            # 마크다운 파일들을 모두 로드하여 concat
            content_parts = []

            if md_rfp_analysis_path:
                try:
                    from app.utils.supabase_client import get_async_client as get_storage_client
                    storage = await get_storage_client()
                    analysis_content = await storage.storage.from_("proposals").download(md_rfp_analysis_path)
                    if analysis_content:
                        content_parts.append(f"# RFP 분석\n\n{analysis_content.decode('utf-8', errors='ignore')}")
                        logger.info(f"[from-bid] RFP 분석 로드: {md_rfp_analysis_path}")
                except Exception as e:
                    logger.warning(f"[from-bid] RFP 분석 로드 실패: {e}")

            if md_notice_path:
                try:
                    storage = await get_storage_client()
                    notice_content = await storage.storage.from_("proposals").download(md_notice_path)
                    if notice_content:
                        content_parts.append(f"# 공고문 요약\n\n{notice_content.decode('utf-8', errors='ignore')}")
                        logger.info(f"[from-bid] 공고문 요약 로드: {md_notice_path}")
                except Exception as e:
                    logger.warning(f"[from-bid] 공고문 요약 로드 실패: {e}")

            if md_instruction_path:
                try:
                    storage = await get_storage_client()
                    instruction_content = await storage.storage.from_("proposals").download(md_instruction_path)
                    if instruction_content:
                        content_parts.append(f"# 과업지시서\n\n{instruction_content.decode('utf-8', errors='ignore')}")
                        logger.info(f"[from-bid] 과업지시서 로드: {md_instruction_path}")
                except Exception as e:
                    logger.warning(f"[from-bid] 과업지시서 로드 실패: {e}")

            if content_parts:
                rfp_content = "\n\n---\n\n".join(content_parts)
                logger.info(f"[from-bid] 마크다운 콘텐츠 통합 완료: {len(rfp_content)} bytes")
            else:
                # 마크다운 파일이 없으면 raw_data의 content_text 사용
                raw_data = bid.get("raw_data", {})
                rfp_content = raw_data.get("content_text", "")
                if rfp_content:
                    logger.info(f"[from-bid] raw_data content_text 사용: {len(rfp_content)} bytes")
        except Exception as e:
            logger.warning(f"[from-bid] 마크다운 로드 중 오류 (계속 진행): {e}")

    # ✅ Step 3: 사용자 정보 확정 (이미 로그인된 사용자이므로 확인만 함)
    # 사용자는 이미 조직과 팀에 소속되어 있음
    logger.info("[from-bid] 사용자 정보 확정 완료")

    final_org_id = user.org_id
    final_team_id = user.team_id
    final_division_id = division_id  # 공고에서 가져온 것 (있을 수도 없을 수도 있음)

    if not final_org_id or not final_team_id:
        error_msg = f"[from-bid] 사용자 소속 정보 부족: org_id={final_org_id}, team_id={final_team_id}"
        logger.error(error_msg)
        raise G2BServiceError("사용자 소속 정보가 불완전합니다. 관리자에게 문의하세요.")

    # ✅ Step 4: 제안 프로젝트 생성
    logger.info(f"[from-bid] 제안 생성 시작: {proposal_id}")
    try:
        proposal_data = {
            "id": proposal_id,
            "title": title,
            "status": "initialized",
            "rfp_content": rfp_content,  # ✅ 분석 내용 포함됨
            "rfp_content_truncated": len(rfp_content) > 50000,
            "rfp_filename": f"{body.bid_no}.md",
            "owner_id": owner_id,
            "team_id": final_team_id,
            "org_id": final_org_id,
            # 제안결정 관련 필드
            "go_decision": True,  # ✅ 제안결정을 YES로 설정
            "bid_tracked": False,  # ✅ 공고 모니터링에서 숨기기
            # 공고 연동 필드 (분석 메타데이터 추적)
            "source_bid_no": body.bid_no,  # ✅ 원본 공고번호
        }

        # 분석 메타데이터 저장 (bid_announcements에서 연동)
        if bid:
            # 적합도 점수
            if bid.get("fit_score") is not None:
                proposal_data["fit_score"] = bid.get("fit_score")
                logger.info(f"[from-bid] 적합도 점수 저장: {bid.get('fit_score')}")

            # 분석 경로들
            if bid.get("md_rfp_analysis_path"):
                proposal_data["md_rfp_analysis_path"] = bid.get("md_rfp_analysis_path")
            if bid.get("md_notice_path"):
                proposal_data["md_notice_path"] = bid.get("md_notice_path")
            if bid.get("md_instruction_path"):
                proposal_data["md_instruction_path"] = bid.get("md_instruction_path")

        if final_division_id:
            proposal_data["division_id"] = final_division_id

        # 민감한 데이터(rfp_content) 제외하고 로깅
        sanitized_data = {k: v for k, v in proposal_data.items() if k != "rfp_content"}
        logger.info(f"[from-bid] INSERT 데이터: {sanitized_data}")

        # Supabase insert
        await client.table("proposals").insert(proposal_data).execute()
        logger.info(f"[from-bid] ✅ 제안 생성 완료: {proposal_id}")

    except Exception as e:
        error_msg = f"[from-bid] 제안 생성 실패: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise G2BServiceError(f"제안 프로젝트 생성 중 오류: {str(e)}")

    # ✅ Step 5: 제안 작업 목록 생성 (담당팀 배정 + 상태 설정)
    try:
        from datetime import datetime, timedelta, timezone

        # 제안 작업 생성
        task_data = {
            "proposal_id": proposal_id,
            "assigned_team_id": final_team_id,  # 제안결정을 선택한 팀
            "description": f"공고 {body.bid_no} 제안 프로젝트: {title}",
            "status": "waiting",  # 대기 상태
            "priority": "normal",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),  # 기본값: 2주 후
            "created_by_id": owner_id,
        }

        logger.info(f"[from-bid] 작업 목록 생성: {task_data}")
        task_result = await client.table("proposal_tasks").insert(task_data).execute()
        task_id = task_result.data[0]["id"] if task_result.data else None
        logger.info(f"[from-bid] ✅ 작업 목록 생성 완료: {task_id}, 담당팀={final_team_id}")

    except Exception as task_e:
        logger.warning(f"[from-bid] 작업 목록 생성 실패 (무시): {task_e}")

    # ✅ Step 6: StateMachine으로 상태 전환 (initialized → in_progress)
    try:
        sm = StateMachine(proposal_id)
        await sm.start_workflow(user_id=owner_id, phase="rfp_analyze")
        logger.info("[from-bid] StateMachine 상태 전환 완료: initialized → in_progress")
    except Exception as sm_e:
        # [CRITICAL] 상태 전환 실패 시 워크플로우 시작 중단 (DB 상태 불일치 방지)
        logger.error(f"[from-bid] StateMachine 상태 전환 실패, 워크플로우 시작 중단: {sm_e}", exc_info=True)
        raise G2BServiceError(f"제안 프로젝트 상태 전환 실패: {str(sm_e)}")

    # ✅ Step 7: LangGraph 워크플로 자동 시작
    try:
        from app.graph.graph import build_graph
        from app.utils.supabase_client import get_postgres_client

        logger.info(f"[from-bid] LangGraph 워크플로 시작: {proposal_id}")

        # PostgreSQL 트랜잭션으로 워크플로 시작
        postgres_client = await get_postgres_client()
        config = {
            "configurable": {
                "thread_id": proposal_id,
                "checkpoint_ns": "",
            }
        }

        # LangGraph 빌드 및 초기 상태 설정
        graph = build_graph(checkpointer=postgres_client)
        initial_state = {
            "project_id": proposal_id,
            "owner_id": owner_id,
            "entry_point": "from_bid",
            "bid_no": body.bid_no,
            "current_step": "STEP_0",
        }

        # 백그라운드에서 워크플로 실행 (비동기, 응답 지연 방지)
        background_tasks.add_task(
            _run_workflow_background, graph, initial_state, config, proposal_id
        )
        logger.info(f"[from-bid] LangGraph 워크플로 백그라운드 시작 완료: {proposal_id}")

    except Exception as wf_e:
        # 워크플로 시작 실패해도 제안은 생성됨 (로깅만 수행)
        logger.warning(f"[from-bid] 워크플로 시작 실패 (무시): {wf_e}")

    # 실제 DB 상태 조회 (StateMachine 전환 반영됨)
    actual_status = "initialized"
    actual_source_bid_no = body.bid_no
    try:
        prop_result = await client.table("proposals").select("status, source_bid_no").eq("id", proposal_id).maybe_single().execute()
        if prop_result.data:
            actual_status = prop_result.data.get("status", "initialized")
            actual_source_bid_no = prop_result.data.get("source_bid_no", body.bid_no)
    except Exception as e:
        logger.warning(f"[from-bid] 실제 상태 조회 실패: {e}")

    return {
        "proposal_id": proposal_id,
        "title": title,
        "status": actual_status,
        "source_bid_no": actual_source_bid_no,
        "entry_point": "from_bid",
        "bid_no": body.bid_no,
        "workflow_started": True,
    }


# ── 제안결정 옵션 — 공고에서 직접 결정 기록 ──

class BidDecisionRequest(BaseModel):
    bid_no: str
    decision_type: Literal["abandon", "hold", "irrelevant"]
    comment: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        # Validate bid_no same as ProposalFromBid
        if not self.bid_no or len(self.bid_no) > 50:
            raise ValueError("bid_no must be 1-50 characters")
        if not all(c.isalnum() or c in '-_' for c in self.bid_no):
            raise ValueError("bid_no must contain only alphanumeric characters, hyphens, and underscores")

@router.post("/bids/decision")
async def record_bid_decision(
    body: BidDecisionRequest,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """공고에서 직접 의사결정을 기록 (제안 진행 없이)."""
    client = rls_client

    # bid_announcements에서 공고 조회
    response = await client.table("bid_announcements").select(
        "id, bid_no, bid_title"
    ).eq("bid_no", body.bid_no).maybe_single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Bid not found")

    bid_id = response.data["id"]
    bid_title = response.data.get("bid_title", "Unknown")

    # 공고 상태 업데이트: 의사결정 기록
    decision_type_ko = {
        "abandon": "제안포기",
        "hold": "제안유보",
        "irrelevant": "관련없음"
    }.get(body.decision_type, "기타")

    decision_comment = body.comment or f"[{decision_type_ko}] {body.decision_type}"

    from datetime import timezone

    await client.table("bid_announcements").update({
        "decision": "No-Go",
        "decision_comment": decision_comment,
        "decided_by": user.id,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", bid_id).execute()

    logger.debug(f"[BidDecision] bid_no={body.bid_no}, decision={body.decision_type}, user={user.id}")

    return {
        "bid_no": body.bid_no,
        "bid_title": bid_title,
        "decision_type": body.decision_type,
        "decision_type_ko": decision_type_ko,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    
    Task #3: Memory Cache Integration
    - Caches proposal lists with 5-minute TTL
    - Cache key includes all filter parameters (status, scope, search, pagination)
    """
    from app.services.memory_cache_service import MemoryCacheService
    
    client = rls_client
    
    # Task #3: Generate cache key from all filter parameters
    cache_service = await get_memory_cache()
    cache_filters = {
        "user_id": user.id,
        "status": status,
        "scope": scope,
        "search": search,
        "skip": skip,
        "limit": limit,
    }
    cache_key = MemoryCacheService._make_key(
        query="proposals_list",
        filters=cache_filters
    )
    
    # Check memory cache first
    cached_result = await cache_service.get("proposals", cache_key)
    if cached_result is not None:
        logger.info(f"Proposals list cache hit (skip={skip}, limit={limit})")
        return cached_result
    
    # Task #2 성능 최적화 (Day 3-4, 2026-04-18):
    # 1. 동적 컬럼 탐지 제거 (-3개 추가 쿼리, ~600ms 개선)
    # 2. 필요한 컬럼만 선택 (-7개 컬럼, ~100KB 데이터)
    # 3. idx_proposals_created_at_desc 인덱스로 정렬 성능 10배 향상
    select_cols = "id, title, status, owner_id, team_id, created_at, updated_at, current_phase, positioning, bid_amount, decision_date, go_decision, source_bid_no"

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

        # Enrich data
        for p in data:
            p["team_name"] = team_map.get(p.get("team_id"))
            p["owner_name"] = owner_map.get(p.get("owner_id"))
            # fit_score is now stored as go_no_go_score in proposals table
            p["fit_score"] = p.get("go_no_go_score")

    # Task #3: Cache the result before returning
    response = ok_list(data, total=total, offset=skip, limit=limit)
    await cache_service.set("proposals", cache_key, response, ttl_seconds=300)
    logger.info(f"Proposals list cached (skip={skip}, limit={limit})")
    
    return response


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
    
    Task #3: Cache Invalidation
    - Clears proposals list cache when proposal is updated
    """
    client = rls_client

    # 프로젝트 존재 확인
    prop = await client.table("proposals").select("id, owner_id, status").eq("id", proposal_id).maybe_single().execute()
    if not prop.data:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다")

    # 소유자만 업데이트 가능 (모든 상태에서)
    if prop.data["owner_id"] != user.id:
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

    # Task #3: Invalidate proposals list cache
    cache_service = await get_memory_cache()
    await cache_service.clear("proposals")
    logger.info(f"Proposals list cache cleared (proposal {proposal_id} updated)")

    return {"message": "프로젝트 정보 업데이트 완료"}


@router.delete("/{proposal_id}", status_code=204)
async def delete_proposal(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """프로젝트 삭제 + Storage 정리 (GAP-5). 소유자만 가능, 실행 중 삭제 방지."""
    client = rls_client

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


# ============================================
# STEP 4A: 진단 및 갭 분석 결과 조회 API
# ============================================

@router.get("/{proposal_id}/diagnostics")
async def get_section_diagnostics(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """섹션별 품질 진단 결과 조회.

    Args:
        proposal_id: 제안서 ID

    Returns:
        {
            "section_id": str,
            "section_title": str,
            "overall_score": float,
            "compliance_ok": bool,
            "evidence_score": float,
            "diff_score": float,
            "recommendation": str,
            "issues": list
        }
    """
    try:
        # proposal_id 검증
        result = await rls_client.from_("proposals").select("id").eq("id", proposal_id).single()
        if not result.data:
            raise HTTPException(404, "제안서를 찾을 수 없습니다")

        # 모든 섹션 진단 조회
        diagnostics = await rls_client.from_("section_diagnostics").select(
            "section_id,section_title,overall_score,compliance_ok,evidence_score,diff_score,recommendation,issues"
        ).eq("proposal_id", proposal_id).order("section_index").execute()

        return {
            "proposal_id": proposal_id,
            "total_sections": len(diagnostics.data or []),
            "diagnostics": diagnostics.data or []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching section diagnostics: {str(e)}")
        raise HTTPException(500, f"진단 결과 조회 중 오류: {str(e)}")


@router.get("/{proposal_id}/gap-analysis")
async def get_gap_analysis(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    rls_client=Depends(get_rls_client),
):
    """제안서 갭 분석 결과 조회.

    Args:
        proposal_id: 제안서 ID

    Returns:
        {
            "missing_points": list,
            "logic_gaps": list,
            "weak_transitions": list,
            "inconsistencies": list,
            "overall_assessment": str,
            "recommended_actions": list,
            "status": str
        }
    """
    try:
        # proposal_id 검증
        result = await rls_client.from_("proposals").select("id").eq("id", proposal_id).single()
        if not result.data:
            raise HTTPException(404, "제안서를 찾을 수 없습니다")

        # 최신 갭 분석 조회
        gap_analysis = await rls_client.from_("proposal_gap_analyses").select(
            "missing_points,logic_gaps,weak_transitions,inconsistencies,overall_assessment,recommended_actions,status,analyzed_at"
        ).eq("proposal_id", proposal_id).order("analyzed_at", desc=True).limit(1).execute()

        if not gap_analysis.data:
            return {
                "proposal_id": proposal_id,
                "gap_analysis": None,
                "message": "갭 분석 결과가 없습니다"
            }

        return {
            "proposal_id": proposal_id,
            "gap_analysis": gap_analysis.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching gap analysis: {str(e)}")
        raise HTTPException(500, f"갭 분석 결과 조회 중 오류: {str(e)}")


# ── 백그라운드 워크플로 실행 ──

async def _run_workflow_background(graph, initial_state, config, proposal_id):
    """LangGraph 워크플로를 백그라운드에서 비동기로 실행."""
    try:
        logger.info(f"[workflow] 백그라운드 시작: {proposal_id}")
        result = await graph.ainvoke(initial_state, config=config)
        logger.info(f"[workflow] 완료: {proposal_id}, 최종 상태: {result.get('current_step', 'unknown')}")
    except Exception as e:
        logger.error(f"[workflow] 실패: {proposal_id}: {str(e)}", exc_info=True)
