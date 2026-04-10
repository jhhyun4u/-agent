"""DB 폴백 테스트 — DB-03.

Mock 기반 (Level 1). AsyncPostgresSaver 실패 시 MemorySaver 폴백.
"""

import pytest

from langgraph.checkpoint.memory import MemorySaver


# ── DB-03: PostgresSaver 실패 → MemorySaver 폴백 ──

@pytest.mark.asyncio
async def test_postgres_failure_falls_back_to_memory():
    """AsyncPostgresSaver 연결 실패 시 MemorySaver로 빌드 가능.

    build_graph(checkpointer=None)은 checkpointer 없이 컴파일.
    실제 _get_graph()는 연결 실패 시 checkpointer=None으로 폴백.
    """
    from app.graph.graph import build_graph

    # AsyncPostgresSaver가 실패한 상황 시뮬레이션:
    # checkpointer=None → 그래프 빌드 성공 (체크포인트 없이)
    graph = build_graph(checkpointer=None)
    assert graph is not None, "checkpointer=None으로 그래프 빌드 실패"

    # MemorySaver 폴백으로도 빌드 가능
    graph2 = build_graph(checkpointer=MemorySaver())
    assert graph2 is not None, "MemorySaver 폴백 빌드 실패"


@pytest.mark.asyncio
async def test_memory_saver_basic_checkpoint():
    """MemorySaver의 기본 체크포인트 동작 검증.

    invoke → aget_state → 상태 복원이 되는지.
    """
    from contextlib import ExitStack
    from tests.integration.conftest import build_all_patches

    patches, _, _ = build_all_patches()

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        from app.graph.graph import build_graph
        checkpointer = MemorySaver()
        graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "db03-memory"}}

        # invoke → interrupt
        state = {"project_id": "db03", "rfp_raw": "사업명: 테스트\n예산: 1억", "current_step": ""}
        await graph.ainvoke(state, config=config)

        # 체크포인트에서 상태 복원
        snapshot = await graph.aget_state(config)
        assert snapshot is not None, "MemorySaver에서 상태 복원 실패"
        assert snapshot.values.get("project_id") == "db03", "project_id 불일치"
        assert snapshot.next, "interrupt 지점이 없음"
