"""
워크플로 제어 API (§12-1)

POST /api/proposals/{id}/start   — 워크플로 시작
GET  /api/proposals/{id}/state   — 현재 그래프 상태
POST /api/proposals/{id}/resume  — Human 리뷰 결과 입력 → 재개
GET  /api/proposals/{id}/stream  — SSE 스트리밍
GET  /api/proposals/{id}/history — 체크포인트 이력
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.config import settings
from app.exceptions import PropNotFoundError, WFAlreadyRunningError, WFResumeValidationError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/proposals", tags=["workflow"])


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


# ── 그래프 인스턴스 관리 ──

_graph_instance = None


async def _get_graph():
    """LangGraph 그래프 인스턴스 (싱글톤). checkpointer 연결."""
    global _graph_instance
    if _graph_instance is None:
        from app.graph.graph import build_graph

        # PostgresSaver 연결 시도 (실패 시 메모리 checkpointer)
        checkpointer = None
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver.from_conn_string(settings.supabase_url)
            await checkpointer.setup()
            logger.info("AsyncPostgresSaver 연결 성공")
        except Exception as e:
            logger.warning(f"PostgresSaver 연결 실패, MemorySaver 사용: {e}")
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()

        _graph_instance = build_graph(checkpointer=checkpointer)
    return _graph_instance


# ── API 엔드포인트 ──

@router.post("/{proposal_id}/start")
async def start_workflow(
    proposal_id: str,
    body: WorkflowStartRequest,
    user=Depends(get_current_user),
):
    """워크플로 시작 — 그래프 invoke."""
    client = await get_async_client()

    # 프로젝트 존재 확인
    proposal = await client.table("proposals").select("id, status").eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise PropNotFoundError(proposal_id)
    if proposal.data["status"] == "running":
        raise WFAlreadyRunningError(proposal_id)

    # 상태 업데이트
    await client.table("proposals").update({
        "status": "running",
        "current_step": "start",
    }).eq("id", proposal_id).execute()

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    initial_state = {
        "project_id": proposal_id,
        "mode": "full",
        "current_step": "start",
        **body.initial_state,
    }

    try:
        result = await graph.ainvoke(initial_state, config=config)
        current_step = result.get("current_step", "unknown")

        await client.table("proposals").update({
            "current_step": current_step,
            "positioning": result.get("positioning"),
        }).eq("id", proposal_id).execute()

        return {
            "proposal_id": proposal_id,
            "status": "running",
            "current_step": current_step,
            "interrupted": _is_interrupted(result),
        }
    except Exception as e:
        logger.error(f"워크플로 시작 실패: {e}")
        await client.table("proposals").update({
            "status": "error",
            "current_step": f"error: {str(e)[:100]}",
        }).eq("id", proposal_id).execute()
        raise


@router.get("/{proposal_id}/state")
async def get_workflow_state(proposal_id: str, user=Depends(get_current_user)):
    """현재 그래프 상태 조회."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    try:
        snapshot = await graph.aget_state(config)
        state = snapshot.values if snapshot else {}
        return {
            "proposal_id": proposal_id,
            "current_step": state.get("current_step", ""),
            "positioning": state.get("positioning"),
            "approval": _serialize_approval(state.get("approval", {})),
            "has_pending_interrupt": bool(snapshot.next) if snapshot else False,
            "next_nodes": list(snapshot.next) if snapshot and snapshot.next else [],
        }
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        return {"proposal_id": proposal_id, "error": str(e)}


@router.post("/{proposal_id}/resume")
async def resume_workflow(
    proposal_id: str,
    body: WorkflowResumeRequest,
    user=Depends(get_current_user),
):
    """Human 리뷰 결과 입력 → 그래프 재개."""
    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    # 현재 상태 확인
    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.next:
        raise WFResumeValidationError("재개할 인터럽트가 없습니다")

    # resume 데이터 구성 (None이 아닌 필드만)
    resume_data = {k: v for k, v in body.model_dump().items() if v is not None}
    resume_data["approved_by"] = resume_data.get("approved_by") or user.get("name", user["id"])

    try:
        result = await graph.ainvoke(None, config=config, input=resume_data)
        current_step = result.get("current_step", "unknown")

        client = await get_async_client()
        update_data = {"current_step": current_step}
        if result.get("positioning"):
            update_data["positioning"] = result["positioning"]
        # 종료 체크
        if current_step in ("go_no_go_no_go", "search_no_interest"):
            update_data["status"] = "cancelled"
        await client.table("proposals").update(update_data).eq("id", proposal_id).execute()

        return {
            "proposal_id": proposal_id,
            "current_step": current_step,
            "interrupted": _is_interrupted(result),
        }
    except Exception as e:
        logger.error(f"워크플로 재개 실패: {e}")
        raise


@router.get("/{proposal_id}/stream")
async def stream_workflow(
    proposal_id: str,
    request: Request,
    user=Depends(get_current_user),
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

                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'event': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{proposal_id}/history")
async def get_workflow_history(proposal_id: str, user=Depends(get_current_user)):
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
        return {"proposal_id": proposal_id, "history": [], "error": str(e)}


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
