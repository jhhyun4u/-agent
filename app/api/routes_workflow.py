"""
워크플로 제어 API (§12-1, Phase 2: Unified State System)

POST /api/proposals/{id}/start           — 워크플로 시작
GET  /api/proposals/{id}/state           — 현재 그래프 상태 (3-layer architecture)
POST /api/proposals/{id}/resume          — Human 리뷰 결과 입력 → 재개
GET  /api/proposals/{id}/stream          — SSE 스트리밍
GET  /api/proposals/{id}/history         — 체크포인트 이력 (LangGraph)
GET  /api/proposals/{id}/state-history   — 상태 전환 이력 (proposal_timelines) [NEW]
POST /api/proposals/{id}/goto/{step}     — 특정 체크포인트로 타임트래블
GET  /api/proposals/{id}/impact/{step}   — step 변경 시 영향 범위 조회
GET  /api/proposals/{id}/feedbacks       — 피드백 이력 조회 (Phase 2-2) [NEW]
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user, require_project_access
from app.config import settings
from app.middleware.rate_limit import limiter
from app.exceptions import PropNotFoundError, WFAlreadyRunningError, WFResumeValidationError
from app.models.auth_schemas import CurrentUser
from app.state_machine import StateMachine
from app.services.state_validator import ProposalStatus
from app.models.workflow_schemas import (
    AiActionResponse, AiStatusResponse, GotoResponse, ImpactResponse,
    SectionLockResponse, SectionUnlockResponse,
    TokenUsageResponse, WorkflowHistoryResponse,
    WorkflowResumeResponse, WorkflowStartResponse, WorkflowStateResponse,
    StateHistoryResponse, TimelineEntry,
    # EnhancedWorkflowStateResponse,  # Used in future /state endpoint enhancement
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/proposals", tags=["workflow"])

# C-4: 워크플로 initial_state 허용 키 화이트리스트
_ALLOWED_INITIAL_STATE_KEYS = frozenset({
    "search_query", "project_name", "rfp_raw", "picked_bid_no",
    "dynamic_sections", "team_id", "division_id", "participants",
})


class WorkflowStartRequest(BaseModel):
    initial_state: dict = {}


class WorkflowResumeRequest(BaseModel):
    """Human 리뷰 결과 (resume 입력). 필드는 단계별 가변."""
    # 공통
    quick_approve: bool | None = None
    approved: bool | None = None
    approved_by: str = ""
    feedback: str = ""
    timestamp: str = ""

    # STEP 0: 공고 선택
    picked_bid_no: str | None = None
    no_interest: bool | None = None
    reason: str = ""
    search_query: dict | None = None

    # STEP 0→1: RFP 업로드
    rfp_file_text: str | None = None
    skip_upload: bool | None = None

    # STEP 1-②: Go/No-Go
    decision: str | None = None
    positioning_override: str | None = None
    no_go_reason: str = ""
    approver_role: str = "lead"
    approver_name: str = ""
    approved_at: str = ""

    # 전략/제안서: 부분 재작업
    rework_targets: list[str] | None = None
    comments: dict | None = None
    selected_alt_id: str = ""


# ── 그래프 인스턴스 관리 (C-3: asyncio.Lock으로 동시성 보호) ──

_graph_instance = None
_graph_lock = asyncio.Lock()


async def _get_graph():
    """LangGraph 그래프 인스턴스 (싱글톤). checkpointer 연결."""
    global _graph_instance
    if _graph_instance is not None:
        return _graph_instance

    async with _graph_lock:
        if _graph_instance is not None:
            return _graph_instance

        from app.graph.graph import build_graph

        # C-2: database_url 사용 (supabase_url은 REST 엔드포인트, Postgres 아님)
        checkpointer = None
        if settings.database_url:
            try:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                checkpointer = AsyncPostgresSaver.from_conn_string(settings.database_url)
                await checkpointer.setup()
                logger.info("AsyncPostgresSaver 연결 성공")
            except Exception as e:
                logger.warning(f"PostgresSaver 연결 실패, MemorySaver 사용: {e}")
                checkpointer = None
        else:
            logger.warning("DATABASE_URL 미설정 — MemorySaver 사용 (서버 재시작 시 워크플로 상태 유실)")

        if checkpointer is None:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()

        _graph_instance = build_graph(checkpointer=checkpointer)
        return _graph_instance


# ── API 엔드포인트 ──

@router.post("/{proposal_id}/start", response_model=WorkflowStartResponse)
@limiter.limit("10/minute")
async def start_workflow(
    request: Request,
    proposal_id: str,
    body: WorkflowStartRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """워크플로 시작 — 그래프 invoke."""
    from app.middleware.request_id import get_request_id
    rid = get_request_id()
    logger.info(f"[WF_START] proposal={proposal_id}, user={user.id}", extra={
        "request_id": rid,
        "data": {"event": "workflow_start", "proposal_id": proposal_id, "initial_keys": list(body.initial_state.keys())},
    })

    client = await get_async_client()

    # 프로젝트 존재 확인
    proposal = await client.table("proposals").select("id, status, current_phase").eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise PropNotFoundError(proposal_id)

    # 활성 상태 확인: 이미 진행 중인 제안서는 재시작 불가
    current_status = proposal.data["status"]
    active_states = (ProposalStatus.IN_PROGRESS.value, ProposalStatus.COMPLETED.value)
    if current_status in active_states:
        raise WFAlreadyRunningError(proposal_id)

    # StateMachine: 상태 전환 (initialized/waiting → in_progress)
    try:
        sm = StateMachine(proposal_id)
        await sm.start_workflow(user_id=user.id, phase="rfp_analyze")
    except ValueError as e:
        logger.warning(f"상태 전환 실패 (proposal_id={proposal_id}): {e}")
        # 오류 발생 시 on_hold 상태로 전환 (재개 가능)
        try:
            sm_hold = StateMachine(proposal_id)
            await sm_hold.hold(user_id=user.id, reason=f"워크플로우 시작 오류: {str(e)}")
        except Exception as hold_error:
            logger.error(f"on_hold 전환 실패: {hold_error}")
        raise

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    # C-4: 허용 키만 initial_state에서 추출 (상태 인젝션 방지)
    safe_initial = {k: v for k, v in body.initial_state.items() if k in _ALLOWED_INITIAL_STATE_KEYS}
    initial_state = {
        "project_id": proposal_id,
        "mode": "full",
        "current_step": "start",
        **safe_initial,
    }

    try:
        result = await graph.ainvoke(initial_state, config=config)
        current_step = result.get("current_step", "unknown")

        update_fields = {"current_phase": current_step}
        await client.table("proposals").update(update_fields).eq("id", proposal_id).execute()

        # 3-Stream 상태 포함
        streams_status = await _get_streams_status_safe(proposal_id)

        return {
            "proposal_id": proposal_id,
            "status": "running",
            "current_step": current_step,
            "interrupted": _is_interrupted(result),
            "streams_status": streams_status,
        }
    except Exception as e:
        logger.error(f"워크플로 시작 실패: {e}")
        # 그래프 실행 오류 시 on_hold로 전환 (수동 재개 가능)
        try:
            sm_hold = StateMachine(proposal_id)
            await sm_hold.hold(user_id="workflow", reason=f"워크플로우 실행 오류: {type(e).__name__}: {str(e)}")
        except Exception as hold_error:
            logger.error(f"on_hold 전환 실패: {hold_error}")
        raise


@router.get("/{proposal_id}/state", response_model=WorkflowStateResponse)
async def get_workflow_state(proposal_id: str, user: CurrentUser = Depends(get_current_user), _access=Depends(require_project_access)):
    """현재 그래프 상태 조회 (3-layer: Business Status + Workflow Phase + AI Status)."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}
    client = await get_async_client()

    try:
        # Layer 1: Business Status (proposals 테이블)
        prop = await client.table("proposals").select(
            "status, current_phase, started_at, last_activity_at, completed_at, submitted_at, presentation_started_at, closed_at, archived_at, expired_at"
        ).eq("id", proposal_id).single().execute()

        business_status = prop.data.get("status", "") if prop.data else ""
        workflow_phase = prop.data.get("current_phase", "") if prop.data else ""

        timestamps = {}
        if prop.data:
            for ts_field in ["started_at", "last_activity_at", "completed_at", "submitted_at", "presentation_started_at", "closed_at", "archived_at", "expired_at"]:
                if prop.data.get(ts_field):
                    timestamps[ts_field] = prop.data[ts_field]

        # Layer 2: Workflow Phase (LangGraph state)
        snapshot = await graph.aget_state(config)
        state = snapshot.values if snapshot else {}

        # Layer 3: AI Status (ai_task_logs 테이블)
        ai_log = await client.table("ai_task_logs").select(
            "status, step, error_message, created_at"
        ).eq("proposal_id", proposal_id).order("created_at", desc=True).limit(1).maybe_single().execute()

        ai_status = {
            "status": ai_log.data.get("status", "idle") if ai_log.data else "idle",
            "current_node": ai_log.data.get("step", "") if ai_log.data else "",
            "error_message": ai_log.data.get("error_message") if ai_log.data and ai_log.data.get("error_message") else None,
            "last_updated_at": ai_log.data.get("created_at") if ai_log.data else None,
        }

        # 토큰 비용 요약
        token_usage = state.get("token_usage", {})
        total_cost = sum(v.get("cost_usd", 0) for v in token_usage.values())

        # 3-Stream 상태 포함
        streams_status = await _get_streams_status_safe(proposal_id)

        return {
            "proposal_id": proposal_id,
            # 3-Layer Architecture
            "business_status": business_status,
            "workflow_phase": workflow_phase,
            "ai_status": ai_status,
            "timestamps": timestamps,
            # Legacy fields for backward compatibility
            "current_step": state.get("current_step", ""),
            "positioning": state.get("positioning"),
            "approval": _serialize_approval(state.get("approval", {})),
            "has_pending_interrupt": bool(snapshot.next) if snapshot else False,
            "next_nodes": list(snapshot.next) if snapshot and snapshot.next else [],
            "token_summary": {
                "total_cost_usd": round(total_cost, 4),
                "nodes_tracked": len(token_usage),
            },
            "streams_status": streams_status,
            "dynamic_sections": state.get("dynamic_sections", []),
        }
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}", exc_info=True)
        return {"proposal_id": proposal_id, "error": "상태 조회 중 오류가 발생했습니다."}


@router.post("/{proposal_id}/resume", response_model=WorkflowResumeResponse)
@limiter.limit("20/minute")
async def resume_workflow(
    request: Request,
    proposal_id: str,
    body: WorkflowResumeRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """Human 리뷰 결과 입력 → 그래프 재개."""
    from app.middleware.request_id import get_request_id
    rid = get_request_id()

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    # 현재 상태 확인
    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.next:
        raise WFResumeValidationError(["재개할 인터럽트가 없습니다"])

    waiting_at = list(snapshot.next) if snapshot.next else []

    # resume 데이터 구성 (None이 아닌 필드만)
    resume_data = {k: v for k, v in body.model_dump().items() if v is not None}
    resume_data["approved_by"] = resume_data.get("approved_by") or user.name or user.id

    # 비즈니스 이벤트 로깅: 승인/거부/No-Go 분기
    event_type = "resume_approve" if resume_data.get("approved") or resume_data.get("quick_approve") else "resume_reject"
    if resume_data.get("decision") == "no_go":
        event_type = "resume_no_go"
    logger.info(f"[WF_RESUME] proposal={proposal_id}, event={event_type}, waiting_at={waiting_at}", extra={
        "request_id": rid,
        "data": {
            "event": event_type,
            "proposal_id": proposal_id,
            "waiting_at": waiting_at,
            "decision": resume_data.get("decision"),
            "has_feedback": bool(resume_data.get("feedback")),
            "rework_targets": resume_data.get("rework_targets", []),
        },
    })

    try:
        from langgraph.types import Command
        result = await graph.ainvoke(Command(resume=resume_data), config=config)
        current_step = result.get("current_step", "unknown")

        client = await get_async_client()

        # GAP-3: 피드백 DB 자동 저장 (Phase 2-2: approved 정보 포함)
        if resume_data.get("feedback") or resume_data.get("comments"):
            try:
                step_name = current_step.replace("_rejected", "").replace("_approved", "")
                # Phase 2-2: comments에 approved 정보 추가
                comments = resume_data.get("comments") or {}
                if isinstance(comments, dict):
                    comments["approved"] = resume_data.get("approved") or resume_data.get("quick_approve", False)
                else:
                    comments = {"approved": resume_data.get("approved") or resume_data.get("quick_approve", False)}

                await client.table("feedbacks").insert({
                    "proposal_id": proposal_id,
                    "step": step_name,
                    "feedback": resume_data.get("feedback", ""),
                    "comments": comments,
                    "rework_targets": resume_data.get("rework_targets"),
                    "author_id": user.id,
                }).execute()
            except Exception as e:
                logger.warning(f"피드백 DB 저장 실패 (무시): {e}")

        update_data = {"current_phase": current_step}

        # 종료 체크: StateMachine으로 상태 전환
        if current_step in ("go_no_go_no_go", "search_no_interest"):
            try:
                sm = StateMachine(proposal_id)
                win_result = "no_go" if current_step == "go_no_go_no_go" else "abandoned"
                reason = f"워크플로우 미진행: {current_step}"
                
                if win_result == "no_go":
                    await sm.decide_no_go(user_id=user.id, reason=reason)
                else:  # abandoned
                    await sm.abandon(user_id=user.id, reason=reason)
                
                logger.info(f"[WF_CLOSED] proposal={proposal_id}, reason={current_step}, win_result={win_result}", extra={
                    "request_id": rid,
                    "data": {"event": "workflow_closed", "proposal_id": proposal_id, "final_step": current_step, "win_result": win_result},
                })
            except Exception as e:
                logger.error(f"제안서 종료 처리 실패 (proposal_id={proposal_id}): {e}")
                # 실패 시 기존 방식으로 폴백
                update_data["status"] = "closed"

        await client.table("proposals").update(update_data).eq("id", proposal_id).execute()

        # 3-Stream 상태 포함
        streams_status = await _get_streams_status_safe(proposal_id)

        return {
            "proposal_id": proposal_id,
            "current_step": current_step,
            "interrupted": _is_interrupted(result),
            "streams_status": streams_status,
        }
    except Exception as e:
        logger.error(f"워크플로 재개 실패: {e}")
        raise


@router.get("/{proposal_id}/stream")
async def stream_workflow(
    proposal_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """SSE 스트리밍 — 그래프 실행 상태를 실시간 전송."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    async def event_generator():
        try:
            async for event in graph.astream_events(None, config=config, version="v2"):
                if await request.is_disconnected():
                    break

                event_type = event.get("event", "")
                data = {
                    "event": event_type,
                    "name": event.get("name", ""),
                }

                if event_type == "on_chain_start":
                    data["step"] = event.get("name", "")
                elif event_type == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    data["current_step"] = output.get("current_step", "") if isinstance(output, dict) else ""
                    # 산출물 1줄 요약 추출
                    data["output_summary"] = _extract_output_summary(event.get("name", ""), output)

                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"SSE 스트리밍 오류: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': '스트리밍 중 오류가 발생했습니다.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{proposal_id}/history", response_model=WorkflowHistoryResponse)
async def get_workflow_history(proposal_id: str, user: CurrentUser = Depends(get_current_user), _access=Depends(require_project_access)):
    """체크포인트 이력."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    try:
        history = []
        async for snapshot in graph.aget_state_history(config):
            history.append({
                "step": snapshot.values.get("current_step", ""),
                "next": list(snapshot.next) if snapshot.next else [],
                "config": snapshot.config,
            })
            if len(history) >= 50:
                break
        return {"proposal_id": proposal_id, "history": history}
    except Exception as e:
        logger.error(f"이력 조회 실패: {e}", exc_info=True)
        return {"proposal_id": proposal_id, "history": [], "error": "이력 조회 중 오류가 발생했습니다."}


@router.get("/{proposal_id}/state-history", response_model=StateHistoryResponse)
async def get_state_history(
    proposal_id: str,
    limit: int = 50,
    offset: int = 0,
    event_type: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """상태 전환 이력 조회 (proposal_timelines).

    Args:
        proposal_id: 제안서 ID
        limit: 반환할 항목 수 (기본값: 50)
        offset: 시작 위치 (기본값: 0)
        event_type: 필터링 이벤트 타입 (status_change, phase_change, approval, review, ai_status)

    Returns:
        StateHistoryResponse: 상태 전환 이력
    """
    client = await get_async_client()

    try:
        # proposal_timelines 테이블 쿼리
        query = client.table("proposal_timelines").select("*").eq("proposal_id", proposal_id)

        # event_type 필터 적용
        if event_type:
            query = query.eq("event_type", event_type)

        # 정렬 및 페이지네이션
        result = await query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        # 전체 개수 조회
        count_result = await client.table("proposal_timelines").select("count", count="exact").eq("proposal_id", proposal_id).execute()
        total_count = count_result.count if hasattr(count_result, "count") else len(result.data or [])

        # TimelineEntry로 변환
        history = [TimelineEntry(**item) for item in (result.data or [])]

        return {
            "proposal_id": proposal_id,
            "total_events": total_count,
            "history": history,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            },
        }
    except Exception as e:
        logger.error(f"상태 이력 조회 실패 (proposal_id={proposal_id}): {e}", exc_info=True)
        return {
            "proposal_id": proposal_id,
            "total_events": 0,
            "history": [],
            "pagination": {"limit": limit, "offset": offset, "has_more": False},
            "error": f"상태 이력 조회 중 오류: {str(e)}",
        }


@router.get("/{proposal_id}/token-usage", response_model=TokenUsageResponse)
async def get_token_usage(proposal_id: str, user: CurrentUser = Depends(get_current_user), _access=Depends(require_project_access)):
    """노드별 토큰 사용량 + 비용 상세 조회."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    state = snapshot.values if snapshot else {}
    token_usage = state.get("token_usage", {})

    total_input = sum(v.get("input_tokens", 0) for v in token_usage.values())
    total_output = sum(v.get("output_tokens", 0) for v in token_usage.values())
    total_cost = sum(v.get("cost_usd", 0) for v in token_usage.values())

    return {
        "proposal_id": proposal_id,
        "by_node": token_usage,
        "total": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "cost_usd": round(total_cost, 4),
            "nodes_executed": len(token_usage),
        },
    }


# ── 섹션 잠금 (§24) ──


@router.post("/{proposal_id}/sections/{section_id}/lock", response_model=SectionLockResponse)
async def lock_section(
    proposal_id: str,
    section_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """섹션 편집 잠금 획득."""
    from app.services.section_lock import acquire_lock

    return await acquire_lock(proposal_id, section_id, user.id)


@router.delete("/{proposal_id}/sections/{section_id}/lock", response_model=SectionUnlockResponse)
async def unlock_section(
    proposal_id: str,
    section_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """섹션 편집 잠금 해제."""
    from app.services.section_lock import release_lock

    released = await release_lock(proposal_id, section_id, user.id)
    return {"released": released}


@router.get("/{proposal_id}/sections/locks", response_model=dict)
async def list_section_locks(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """제안서의 모든 활성 잠금 목록."""
    from app.services.section_lock import get_locks

    locks = await get_locks(proposal_id)
    return {"locks": locks}


# ── AI 상태 (§22) ──


@router.get("/{proposal_id}/ai-status", response_model=AiStatusResponse)
async def get_ai_status(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """AI 작업 상태 조회."""
    from app.services.ai_status_manager import ai_status_manager

    return ai_status_manager.get_composite_status(proposal_id)


# ── AI 제어 (§22 확장) ──


@router.post("/{proposal_id}/ai-abort", response_model=AiActionResponse)
@limiter.limit("10/minute")
async def abort_ai_task(
    request: Request,
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """AI 작업 중단 (paused 상태로 전환, 완료 서브태스크 보존)."""
    from app.middleware.request_id import get_request_id
    from app.services.ai_status_manager import ai_status_manager

    rid = get_request_id()
    result = ai_status_manager.abort_task(proposal_id)
    if result is None:
        logger.info(f"[WF_ABORT] proposal={proposal_id}, result=no_running_task", extra={
            "request_id": rid,
            "data": {"event": "ai_abort_noop", "proposal_id": proposal_id},
        })
        return {"proposal_id": proposal_id, "status": "idle", "message": "실행 중인 작업 없음"}

    logger.info(f"[WF_ABORT] proposal={proposal_id}, step={result['step']}, paused", extra={
        "request_id": rid,
        "data": {"event": "ai_abort", "proposal_id": proposal_id, "step": result["step"], "status": result["status"]},
    })
    return {"proposal_id": proposal_id, "status": result["status"], "step": result["step"]}


@router.post("/{proposal_id}/ai-retry", response_model=AiActionResponse)
@limiter.limit("5/minute")
async def retry_ai_task(
    request: Request,
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """중단된 AI 작업 재시도 — 현재 STEP을 처음부터 재실행."""
    from app.services.ai_status_manager import ai_status_manager

    status = ai_status_manager.get_composite_status(proposal_id)
    if status["status"] not in ("paused", "error", "no_response"):
        return {
            "proposal_id": proposal_id,
            "error": f"재시도 불가 상태: {status['status']}",
        }

    # 기존 상태 제거 후 워크플로 재개
    step = status.get("step", "unknown")
    del ai_status_manager._statuses[proposal_id]

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}
    try:
        result = await graph.ainvoke(None, config=config)
        return {
            "proposal_id": proposal_id,
            "retried_step": step,
            "current_step": result.get("current_step", ""),
        }
    except Exception as e:
        logger.error(f"AI 재시도 실패: {proposal_id}: {e}", exc_info=True)
        return {"proposal_id": proposal_id, "error": "AI 재시도 중 오류가 발생했습니다."}


@router.get("/{proposal_id}/ai-logs")
async def get_ai_logs(
    proposal_id: str,
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """AI 작업 로그 이력 조회 (ai_task_logs 테이블)."""
    client = await get_async_client()
    try:
        resp = (
            await client.table("ai_task_logs")
            .select("*")
            .eq("proposal_id", proposal_id)
            .order("created_at", desc=True)
            .limit(min(limit, 100))
            .execute()
        )
        return {"proposal_id": proposal_id, "logs": resp.data or []}
    except Exception as e:
        logger.warning(f"AI 로그 조회 실패: {e}")
        return {"proposal_id": proposal_id, "logs": [], "error": "로그 조회 중 오류가 발생했습니다."}


# ── 타임트래블 (§12-1 확장) ──

# 그래프 노드 토폴로지: 순서대로 나열한 주요 노드
_NODE_ORDER = [
    "rfp_search", "review_search", "rfp_fetch",
    "rfp_analyze", "review_rfp",
    "research_gather", "go_no_go", "review_gng",
    "strategy_generate", "review_strategy",
    "plan_fan_out_gate", "plan_team", "plan_assign", "plan_schedule",
    "plan_story", "plan_price", "plan_merge", "review_plan",
    "proposal_start_gate", "proposal_write_next", "review_section",
    "self_review", "review_proposal",
    "presentation_strategy",
    "ppt_toc", "ppt_visual_brief", "ppt_storyboard", "review_ppt",
]


@router.post("/{proposal_id}/goto/{step}", response_model=GotoResponse)
async def goto_step(
    proposal_id: str,
    step: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """특정 체크포인트로 타임트래블 — 이력에서 해당 step의 config를 찾아 복원."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    # 이력에서 해당 step의 체크포인트를 검색
    target_config = None
    async for snapshot in graph.aget_state_history(config):
        snap_step = snapshot.values.get("current_step", "")
        # 정확히 일치하거나 step이 포함된 경우
        if snap_step == step or snap_step.startswith(step):
            target_config = snapshot.config
            break

    if not target_config:
        return {
            "success": False,
            "error": f"체크포인트 이력에서 '{step}' 단계를 찾을 수 없습니다.",
        }

    # 해당 체크포인트로 상태 복원 (aupdate_state with as_node)
    target_snapshot = await graph.aget_state(target_config)
    if not target_snapshot:
        return {"success": False, "error": "체크포인트 상태 복원 실패"}

    # 원래 thread의 상태를 타겟 체크포인트 값으로 덮어쓰기
    await graph.aupdate_state(config, target_snapshot.values)

    # DB의 current_phase도 동기화
    client = await get_async_client()
    await client.table("proposals").update({
        "current_phase": target_snapshot.values.get("current_step", step),
    }).eq("id", proposal_id).execute()

    from app.middleware.request_id import get_request_id
    rid = get_request_id()
    logger.info(f"[WF_GOTO] proposal={proposal_id}, target_step={step}", extra={
        "request_id": rid,
        "data": {"event": "time_travel", "proposal_id": proposal_id, "target_step": step},
    })

    return {
        "success": True,
        "proposal_id": proposal_id,
        "restored_step": target_snapshot.values.get("current_step", step),
        "message": f"'{step}' 단계로 복원되었습니다. 이후 단계의 산출물은 재실행이 필요합니다.",
    }


@router.get("/{proposal_id}/impact/{step}", response_model=ImpactResponse)
async def get_impact(
    proposal_id: str,
    step: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """특정 step 변경 시 재실행이 필요한 downstream 노드 목록 반환."""
    if step not in _NODE_ORDER:
        return {
            "step": step,
            "error": f"알 수 없는 노드: {step}",
            "downstream": [],
        }

    idx = _NODE_ORDER.index(step)
    downstream = _NODE_ORDER[idx + 1:]

    # STEP 분류
    step_labels = {
        "rfp_search": 0, "review_search": 0, "rfp_fetch": 0,
        "rfp_analyze": 1, "review_rfp": 1,
        "research_gather": 1, "go_no_go": 1, "review_gng": 1,
        "strategy_generate": 2, "review_strategy": 2,
        "plan_fan_out_gate": 3, "plan_team": 3, "plan_assign": 3,
        "plan_schedule": 3, "plan_story": 3, "plan_price": 3,
        "plan_merge": 3, "review_plan": 3,
        "proposal_start_gate": 4, "proposal_write_next": 4,
        "review_section": 4, "self_review": 4, "review_proposal": 4,
        "presentation_strategy": 4,
        "ppt_toc": 5, "ppt_visual_brief": 5, "ppt_storyboard": 5,
        "review_ppt": 5,
    }

    affected_steps = sorted(set(
        step_labels.get(n, -1) for n in downstream if n in step_labels
    ))

    return {
        "step": step,
        "step_number": step_labels.get(step, -1),
        "downstream_nodes": downstream,
        "downstream_count": len(downstream),
        "affected_steps": affected_steps,
        "message": f"'{step}' 변경 시 STEP {affected_steps}의 {len(downstream)}개 노드를 재실행해야 합니다." if downstream else "마지막 노드입니다.",
    }


# ── 헬퍼 ──

def _is_interrupted(result: dict) -> bool:
    """interrupt()에 의해 중단된 상태인지 확인."""
    step = result.get("current_step", "")
    return step.endswith("_complete") or "review" in step


def _serialize_approval(approval: dict) -> dict:
    """ApprovalStatus 객체를 JSON 직렬화."""
    serialized = {}
    for key, val in approval.items():
        if hasattr(val, "model_dump"):
            serialized[key] = val.model_dump()
        elif isinstance(val, dict):
            serialized[key] = val
        else:
            serialized[key] = str(val)
    return serialized


async def _get_streams_status_safe(proposal_id: str) -> dict | None:
    """3-Stream 상태 조회 (실패 시 None 반환).

    자동 복구: Go 결정 이후인데 스트림 레코드가 없으면 자동 초기화.
    """
    try:
        from app.services.stream_orchestrator import get_streams_status, initialize_streams
        result = await get_streams_status(proposal_id)

        # 자동 복구: Go 통과 후인데 스트림이 모두 not_started이면 초기화 재시도
        streams = result.get("streams", [])
        all_not_started = all(s.get("status") == "not_started" for s in streams if isinstance(s, dict))
        if all_not_started and streams:
            # Go 통과 여부 확인 (proposals.current_phase 기반)
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            prop = await (
                client.table("proposals")
                .select("current_phase")
                .eq("id", proposal_id)
                .single()
                .execute()
            )
            phase = (prop.data or {}).get("current_phase", "")
            go_passed_phases = {
                "go_no_go_go", "strategy", "bid_plan", "plan",
                "proposal", "ppt", "completed",
            }
            if any(gp in phase for gp in go_passed_phases):
                await initialize_streams(proposal_id)
                result = await get_streams_status(proposal_id)

        return result
    except Exception:
        return None


def _extract_output_summary(node_name: str, output: Any) -> str:
    """노드 완료 시 산출물에서 핵심 정보를 1줄 요약."""
    if not isinstance(output, dict):
        return ""
    try:
        if node_name == "rfp_analyze":
            rfp = output.get("rfp_analysis")
            if rfp:
                d = rfp.model_dump() if hasattr(rfp, "model_dump") else rfp
                n_eval = len(d.get("eval_items", []))
                n_hb = len(d.get("hot_buttons", []))
                return f"케이스 {d.get('case_type', '?')}, 평가항목 {n_eval}개, 핫버튼 {n_hb}개"
        elif node_name == "go_no_go":
            gng = output.get("go_no_go")
            if gng:
                d = gng.model_dump() if hasattr(gng, "model_dump") else gng
                return f"수주 가능성 {d.get('feasibility_score', 0)}%, 포지셔닝: {d.get('positioning', '?')}"
        elif node_name == "strategy_generate":
            s = output.get("strategy")
            if s:
                d = s.model_dump() if hasattr(s, "model_dump") else s
                return f"Win Theme: {(d.get('win_theme', '') or '')[:50]}"
        elif node_name == "research_gather":
            rb = output.get("research_brief", {})
            if isinstance(rb, dict):
                n_topics = len(rb.get("research_topics", []))
                return f"리서치 주제 {n_topics}개 도출"
        elif node_name == "proposal_write_next":
            sections = output.get("proposal_sections", [])
            return f"섹션 {len(sections)}개 작성"
        elif node_name == "self_review":
            pr = output.get("parallel_results", {})
            score = pr.get("_self_review_score", {})
            total = score.get("total", 0)
            return f"자가진단 {total}/100점"
        elif node_name == "plan_merge":
            return "계획 통합 완료"
        elif node_name == "ppt_storyboard":
            sb = output.get("ppt_storyboard", {})
            n_slides = sb.get("total_slides", len(sb.get("slides", [])))
            return f"PPT {n_slides}장 생성"
    except Exception:
        pass
    return ""


# ── Phase 2-2: 피드백 이력 조회 ──

class FeedbackRecord(BaseModel):
    id: str
    feedback: str
    created_at: str
    approved: bool | None = None


class FeedbackHistoryResponse(BaseModel):
    feedbacks: list[FeedbackRecord]


@router.get("/{proposal_id}/feedbacks", response_model=FeedbackHistoryResponse)
async def get_feedback_history(
    proposal_id: str,
    step: str,
    user: CurrentUser = Depends(get_current_user),
    _access = Depends(require_project_access),
):
    """Phase 2-2: 특정 STEP의 피드백 이력 조회.

    Query Parameters:
        step: review_strategy, review_plan, review_proposal, review_ppt 등
    """
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    try:
        # feedbacks 테이블에서 proposal_id + step으로 필터링
        result = await (
            client.table("feedbacks")
            .select("id, feedback, created_at, comments")
            .eq("proposal_id", proposal_id)
            .eq("step", step)
            .order("created_at", desc=False)
            .execute()
        )

        feedbacks = []
        if result.data:
            for row in result.data:
                # comments에 approved 정보가 있으면 추출
                approved = None
                if row.get("comments"):
                    comments = row["comments"]
                    if isinstance(comments, dict):
                        approved = comments.get("approved")

                feedbacks.append(
                    FeedbackRecord(
                        id=row["id"],
                        feedback=row.get("feedback", ""),
                        created_at=row.get("created_at", ""),
                        approved=approved,
                    )
                )

        return FeedbackHistoryResponse(feedbacks=feedbacks)

    except Exception as e:
        logger.warning(f"[{proposal_id}] 피드백 이력 조회 실패 (step={step}): {e}")
        return FeedbackHistoryResponse(feedbacks=[])
