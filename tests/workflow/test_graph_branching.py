"""LangGraph 워크플로 분기·재작업 테스트.

전략 리젝, No-Go 후 재시도, 섹션 재작성 등 핵심 분기 경로를 검증한다.
"""
import pytest
from contextlib import ExitStack
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command


def _resume_approved(**extra):
    data = {"approved": True, "approved_by": "tester", "feedback": ""}
    data.update(extra)
    return data


def _resume_go(**extra):
    data = {"decision": "go", "approved": True, "approved_by": "tester"}
    data.update(extra)
    return data


def _resume_rejected(**extra):
    data = {"approved": False, "approved_by": "tester", "feedback": "재작업 필요"}
    data.update(extra)
    return data


async def _advance_to_step(graph, config, initial_state, target_step, workflow_patches_list):
    """워크플로를 target_step까지 진행하는 헬퍼."""
    with ExitStack() as stack:
        for p in workflow_patches_list:
            stack.enter_context(p)

        from app.graph.graph import build_graph
        g = build_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": config}}

        # Start → review_rfp
        await g.ainvoke(initial_state, config=config)
        # review_rfp → review_gng
        await g.ainvoke(Command(resume=_resume_approved()), config=config)
        # review_gng (Go) → review_strategy
        await g.ainvoke(Command(resume=_resume_go()), config=config)

        if target_step == "review_strategy":
            return g, config

        # review_strategy → review_bid_plan
        await g.ainvoke(Command(resume=_resume_approved()), config=config)

        if target_step == "review_bid_plan":
            return g, config

        # review_bid_plan → review_plan
        await g.ainvoke(Command(resume=_resume_approved()), config=config)

        if target_step == "review_plan":
            return g, config

        return g, config


# ── 전략 리젝 → 재생성 → 재승인 ──

@pytest.mark.asyncio
async def test_strategy_rejection_and_retry(initial_state, workflow_patches):
    """전략 리뷰에서 리젝 시 strategy_generate를 재실행하고 다시 review_strategy에 도달한다."""
    patches_list, _, _ = workflow_patches()

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        from app.graph.graph import build_graph
        g = build_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "strategy-reject-001"}}

        # Start → review_rfp
        await g.ainvoke(initial_state, config=config)
        # review_rfp → review_gng
        await g.ainvoke(Command(resume=_resume_approved()), config=config)
        # review_gng (Go) → review_strategy
        await g.ainvoke(Command(resume=_resume_go()), config=config)

        snapshot = await g.aget_state(config)
        assert any("review_strategy" in str(n) for n in snapshot.next)

        # 전략 리젝 → strategy_generate 재실행 → 다시 review_strategy
        await g.ainvoke(Command(resume=_resume_rejected()), config=config)

        snapshot = await g.aget_state(config)
        assert any("review_strategy" in str(n) for n in snapshot.next), \
            f"전략 리젝 후 review_strategy 재도달 실패: {snapshot.next}"


# ── Go/No-Go 리젝 → 재시도 → Go ──

@pytest.mark.asyncio
async def test_gng_rejection_and_retry(initial_state, workflow_patches):
    """Go/No-Go 리뷰에서 리젝 시 go_no_go를 재실행하고 다시 review_gng에 도달한다."""
    patches_list, _, _ = workflow_patches()

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        from app.graph.graph import build_graph
        g = build_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "gng-reject-001"}}

        # Start → review_rfp
        await g.ainvoke(initial_state, config=config)
        # review_rfp → review_gng
        await g.ainvoke(Command(resume=_resume_approved()), config=config)

        snapshot = await g.aget_state(config)
        assert any("review_gng" in str(n) for n in snapshot.next)

        # Go/No-Go 리젝 → go_no_go 재실행 → 다시 review_gng
        await g.ainvoke(
            Command(resume={"decision": "rejected", "approved": False, "approved_by": "tester"}),
            config=config,
        )

        snapshot = await g.aget_state(config)
        assert any("review_gng" in str(n) for n in snapshot.next), \
            f"Go/No-Go 리젝 후 review_gng 재도달 실패: {snapshot.next}"

        # 이번엔 Go 결정 → strategy로 진행
        await g.ainvoke(Command(resume=_resume_go()), config=config)

        snapshot = await g.aget_state(config)
        assert any("review_strategy" in str(n) for n in snapshot.next), \
            f"Go 결정 후 review_strategy 미도달: {snapshot.next}"
