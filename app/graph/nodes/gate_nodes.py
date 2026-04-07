"""
게이트 · Fan-out · 훅 노드 (v4.0)

graph.py에 인라인 정의되어 있던 유틸 노드를 모듈로 분리.
- passthrough: 빈 게이트 (라우팅 분기점)
- proposal_start_gate: 순차 작성 인덱스 초기화
- convergence_gate: A/B 경로 통합 대기점
- fork_to_branches: 전략 승인 → Path A + B 동시 분기
- plan_selective_fan_out: 계획 노드 부분 재작업 fan-out
- stream1_complete_hook: Stream 1 완료 시 후처리
"""

import asyncio
import logging

from langgraph.types import Send

from app.graph.state import ProposalState

logger = logging.getLogger(__name__)

ALL_PLAN_NODES = ["plan_team", "plan_assign", "plan_schedule", "plan_story", "plan_price"]


def passthrough(state: ProposalState) -> dict:
    """빈 게이트 — 라우팅 분기점으로만 사용."""
    return {}


def proposal_start_gate(state: ProposalState) -> dict:
    """섹션별 순차 작성 시작: current_section_index 초기화."""
    return {"current_section_index": 0}


def convergence_gate(state: ProposalState) -> dict:
    """6A/6B 통합 게이트 — Send() 암시적 동기화로 양쪽 경로 완료 대기."""
    return {}


def fork_to_branches(state: ProposalState) -> list[Send]:
    """전략 승인 후 → Path A (plan) + Path B (submission_plan) 동시 시작."""
    return [
        Send("plan_fan_out_gate", state),
        Send("submission_plan", state),
    ]


def plan_selective_fan_out(state: ProposalState) -> list[Send]:
    """부분 재작업: rework_targets에 지정된 항목만 재실행."""
    targets = state.get("rework_targets", [])
    if not targets:
        nodes_to_run = ALL_PLAN_NODES
    else:
        nodes_to_run = [n for n in ALL_PLAN_NODES if n in targets]
    return [Send(node, state) for node in nodes_to_run]


def stream1_complete_hook(state: ProposalState) -> dict:
    """Stream 1 완료 훅 — 진행상태 갱신 + 산출물 연결 + 아카이브 스냅샷."""
    proposal_id = state.get("project_id", "")
    if not proposal_id:
        return {}

    async def _mark():
        try:
            from app.services.stream_orchestrator import update_stream_progress
            await update_stream_progress(proposal_id, "proposal", status="completed", current_phase="workflow_done")
        except Exception as e:
            logger.warning(f"Stream 1 완료 갱신 실패: {e}")
        try:
            from app.services.submission_docs_service import link_stream1_artifacts
            await link_stream1_artifacts(proposal_id)
        except Exception as e:
            logger.warning(f"산출물 자동 연결 실패: {e}")
        try:
            from app.services.project_archive_service import snapshot_from_state
            await snapshot_from_state(proposal_id, state, created_by=state.get("created_by"))
        except Exception as e:
            logger.warning(f"아카이브 스냅샷 실패: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_mark())
    except RuntimeError:
        pass
    return {}
