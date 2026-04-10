"""Live DB 통합 테스트 — WF-07~08, DB-01~02, DB-05.

실제 PostgreSQL 연결 필요.
pytest -m live 로 실행.
"""

import pytest
from contextlib import ExitStack

from langgraph.types import Command


pytestmark = pytest.mark.live


# ── DB-01: AsyncPostgresSaver 기본 동작 ──

@pytest.mark.asyncio
async def test_checkpointer_write_read(pg_checkpointer):
    """체크포인트 저장 → 읽기 왕복 검증."""
    from tests.integration.conftest import build_all_patches
    from app.graph.graph import build_graph

    patches, _, _ = build_all_patches()

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        graph = build_graph(checkpointer=pg_checkpointer)
        config = {"configurable": {"thread_id": "live-db01"}}

        state = {"project_id": "live-db01", "rfp_raw": "사업명: Live 테스트", "current_step": ""}
        await graph.ainvoke(state, config=config)

        # 체크포인트에서 복원
        snapshot = await graph.aget_state(config)
        assert snapshot is not None
        assert snapshot.values.get("project_id") == "live-db01"
        assert snapshot.next, "interrupt 지점 없음"


# ── WF-07: 체크포인터 저장/복원 (resume 포함) ──

@pytest.mark.asyncio
async def test_checkpoint_survives_resume(pg_checkpointer):
    """interrupt → resume 사이클이 PostgreSQL 체크포인터에서 동작."""
    from tests.integration.conftest import build_all_patches, resume_approved
    from app.graph.graph import build_graph

    patches, _, _ = build_all_patches()

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        graph = build_graph(checkpointer=pg_checkpointer)
        config = {"configurable": {"thread_id": "live-wf07"}}

        # invoke → review_rfp
        state = {"project_id": "live-wf07", "rfp_raw": "사업명: Live Resume 테스트", "current_step": ""}
        await graph.ainvoke(state, config=config)

        # resume → 다음 interrupt
        await graph.ainvoke(Command(resume=resume_approved()), config=config)
        snapshot = await graph.aget_state(config)

        assert snapshot.values.get("rfp_analysis"), "resume 후 rfp_analysis 없음"
        assert snapshot.next, "resume 후 다음 interrupt 없음"


# ── DB-05: 동시 proposals 체크포인터 격리 ──

@pytest.mark.asyncio
async def test_concurrent_proposals_isolation(pg_checkpointer):
    """2개 thread_id로 동시 실행 시 체크포인트 격리."""
    from tests.integration.conftest import build_all_patches, resume_approved
    from app.graph.graph import build_graph

    patches, _, _ = build_all_patches()

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        graph = build_graph(checkpointer=pg_checkpointer)
        config_a = {"configurable": {"thread_id": "live-db05-a"}}
        config_b = {"configurable": {"thread_id": "live-db05-b"}}

        state_a = {"project_id": "db05-a", "rfp_raw": "사업명: 프로젝트 A", "current_step": ""}
        state_b = {"project_id": "db05-b", "rfp_raw": "사업명: 프로젝트 B", "current_step": ""}

        # 각각 invoke
        await graph.ainvoke(state_a, config=config_a)
        await graph.ainvoke(state_b, config=config_b)

        # 상태 격리 확인
        snap_a = await graph.aget_state(config_a)
        snap_b = await graph.aget_state(config_b)

        assert snap_a.values.get("project_id") == "db05-a"
        assert snap_b.values.get("project_id") == "db05-b"

        # A의 resume가 B에 영향 없음
        await graph.ainvoke(Command(resume=resume_approved()), config=config_a)

        snap_b_after = await graph.aget_state(config_b)
        # B는 여전히 review_rfp에서 대기 (A의 resume 영향 없음)
        assert any("review_rfp" in str(n) for n in snap_b_after.next), \
            "A의 resume가 B에 영향을 줌"
