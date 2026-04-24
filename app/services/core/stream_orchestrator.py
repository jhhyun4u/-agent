"""
3-Stream 오케스트레이터

Go 결정 이후 3개 스트림(proposal, bidding, documents)의 생애주기 관리.
- initialize_streams: Go 결정 시 3개 레코드 생성
- update_stream_progress: 진행률 갱신
- get_streams_status: 통합 조회
- check_convergence: 최종 제출 가능 여부
- mark_final_submission: 최종 제출 확정
"""

import logging
from datetime import datetime, timezone

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def initialize_streams(proposal_id: str) -> list[dict]:
    """Go 결정 시 3개 스트림 레코드 생성 (이미 존재하면 스킵)."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    streams = []
    for stream_name in ("proposal", "bidding", "documents"):
        # UPSERT: 이미 있으면 updated_at만 갱신
        res = await (
            client.table("stream_progress")
            .upsert(
                {
                    "proposal_id": proposal_id,
                    "stream": stream_name,
                    "status": "in_progress" if stream_name == "proposal" else "not_started",
                    "progress_pct": 0,
                    "current_phase": "go_decision" if stream_name == "proposal" else None,
                    "started_at": now if stream_name == "proposal" else None,
                    "updated_at": now,
                },
                on_conflict="proposal_id,stream",
            )
            .execute()
        )
        if res.data:
            streams.append(res.data[0])

    # proposals 테이블 streams_ready 초기화
    await (
        client.table("proposals")
        .update({
            "streams_ready": {"proposal": False, "bidding": False, "documents": False},
            "submission_gate_status": "pending",
        })
        .eq("id", proposal_id)
        .execute()
    )

    logger.info(f"3-Stream 초기화 완료: proposal={proposal_id}")
    return streams


async def update_stream_progress(
    proposal_id: str,
    stream: str,
    *,
    status: str | None = None,
    progress_pct: int | None = None,
    current_phase: str | None = None,
    blocked_reason: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """스트림 진행률 갱신."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    update_data: dict = {"updated_at": now}
    if status is not None:
        update_data["status"] = status
        if status == "in_progress" and progress_pct is None:
            # started_at이 없으면 설정
            update_data["started_at"] = now
        if status == "completed":
            update_data["completed_at"] = now
            update_data["progress_pct"] = 100
    if progress_pct is not None:
        update_data["progress_pct"] = progress_pct
    if current_phase is not None:
        update_data["current_phase"] = current_phase
    if blocked_reason is not None:
        update_data["blocked_reason"] = blocked_reason
    if metadata is not None:
        update_data["metadata"] = metadata

    res = await (
        client.table("stream_progress")
        .update(update_data)
        .eq("proposal_id", proposal_id)
        .eq("stream", stream)
        .execute()
    )

    # streams_ready 동기화
    if status == "completed":
        await _sync_streams_ready(client, proposal_id, stream, True)

    return res.data[0] if res.data else {}


async def _sync_streams_ready(client, proposal_id: str, stream: str, ready: bool):
    """proposals.streams_ready JSONB 필드 원자적 갱신 (race condition 방지).

    jsonb || 연산자로 단일 UPDATE — read-then-write 패턴 제거.
    """
    # 원자적 JSONB 머지: 기존 값과 새 값을 || 연산으로 합침
    import json as _json
    patch = _json.dumps({stream: ready})
    try:
        await client.rpc("exec_sql", {
            "query": (
                "UPDATE proposals "
                f"SET streams_ready = COALESCE(streams_ready, '{{}}'::jsonb) || '{patch}'::jsonb "
                f"WHERE id = '{proposal_id}'"
            ),
        }).execute()
    except Exception:
        # RPC가 없으면 fallback (비원자적이지만 동작은 함)
        prop = await (
            client.table("proposals")
            .select("streams_ready")
            .eq("id", proposal_id)
            .single()
            .execute()
        )
        if not prop.data:
            return
        sr = prop.data.get("streams_ready") or {}
        sr[stream] = ready
        await (
            client.table("proposals")
            .update({"streams_ready": sr})
            .eq("id", proposal_id)
            .execute()
        )


async def get_streams_status(proposal_id: str) -> dict:
    """3개 스트림 통합 조회."""
    client = await get_async_client()
    res = await (
        client.table("stream_progress")
        .select("*")
        .eq("proposal_id", proposal_id)
        .order("stream")
        .execute()
    )
    streams = res.data or []

    # 누락된 스트림 기본값 채우기
    existing = {s["stream"] for s in streams}
    for name in ("proposal", "bidding", "documents"):
        if name not in existing:
            streams.append({
                "stream": name,
                "status": "not_started",
                "progress_pct": 0,
                "current_phase": None,
                "blocked_reason": None,
                "started_at": None,
                "completed_at": None,
                "metadata": {},
            })

    convergence_ready, missing = _check_convergence_logic(streams)

    return {
        "streams": streams,
        "convergence_ready": convergence_ready,
        "missing_streams": missing,
    }


def _check_convergence_logic(streams: list[dict]) -> tuple[bool, list[str]]:
    """합류 가능 여부 판단."""
    missing = []
    for s in streams:
        if s["status"] != "completed":
            missing.append(s["stream"])
    return len(missing) == 0, missing


async def check_convergence(proposal_id: str) -> dict:
    """최종 제출 가능 여부."""
    result = await get_streams_status(proposal_id)
    return {
        "convergence_ready": result["convergence_ready"],
        "missing_streams": result["missing_streams"],
    }


async def mark_final_submission(proposal_id: str, user_id: str) -> dict:
    """최종 제출 확정 — 3개 스트림 모두 completed여야 실행."""
    convergence = await check_convergence(proposal_id)
    if not convergence["convergence_ready"]:
        return {
            "success": False,
            "message": f"미완료 스트림: {', '.join(convergence['missing_streams'])}",
            "submission_gate_status": "pending",
        }

    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    await (
        client.table("proposals")
        .update({
            "submission_gate_status": "submitted",
            "status": "completed",
            "updated_at": now,
        })
        .eq("id", proposal_id)
        .execute()
    )

    logger.info(f"최종 제출 확정: proposal={proposal_id}, user={user_id}")
    return {
        "success": True,
        "message": "최종 제출이 확정되었습니다.",
        "submission_gate_status": "submitted",
    }
