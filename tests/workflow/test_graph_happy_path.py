"""LangGraph 워크플로 실행 테스트 — Happy Path.

실제 그래프를 MemorySaver로 컴파일하고,
Claude API + Supabase를 mock하여 전체 interrupt/resume 사이클을 검증한다.
"""
import json
import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command


# ── Helpers ──

async def _build_graph_with_mocks(patches_list):
    """Mock patches를 적용한 상태로 그래프를 빌드."""
    from app.graph.graph import build_graph
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    return graph


def _resume_approved(**extra):
    """표준 승인 resume 데이터."""
    data = {"approved": True, "approved_by": "tester", "feedback": ""}
    data.update(extra)
    return data


def _resume_go(**extra):
    """Go/No-Go 승인 resume 데이터."""
    data = {"decision": "go", "approved": True, "approved_by": "tester"}
    data.update(extra)
    return data


# ── Happy Path: Case A + PPT ──

@pytest.mark.asyncio
async def test_happy_path_full_workflow(initial_state, workflow_patches):
    """전체 워크플로 Happy Path: RFP 분석 → 전략 → 계획 → 제안서 → PPT → END."""
    patches_list, mock_claude, mock_sb = workflow_patches()

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        graph = await _build_graph_with_mocks(patches_list)
        config = {"configurable": {"thread_id": "happy-path-001"}}

        # 1. Start → rfp_analyze → review_rfp (first interrupt)
        result = await graph.ainvoke(initial_state, config=config)
        snapshot = await graph.aget_state(config)
        assert snapshot.next, "그래프가 interrupt 없이 종료됨"
        assert any("review_rfp" in str(n) for n in snapshot.next), \
            f"Expected review_rfp, got {snapshot.next}"

        # 2. Resume review_rfp → research_gather → go_no_go → review_gng
        result = await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert snapshot.next, "review_rfp 승인 후 interrupt 없이 종료됨"
        assert any("review_gng" in str(n) for n in snapshot.next), \
            f"Expected review_gng, got {snapshot.next}"

        # 3. Resume Go → strategy_generate → review_strategy
        result = await graph.ainvoke(
            Command(resume=_resume_go()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert any("review_strategy" in str(n) for n in snapshot.next), \
            f"Expected review_strategy, got {snapshot.next}"

        # 4. Resume strategy → bid_plan → review_bid_plan
        result = await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert any("review_bid_plan" in str(n) for n in snapshot.next), \
            f"Expected review_bid_plan, got {snapshot.next}"

        # 5. Resume bid_plan → plan nodes → plan_merge → review_plan
        result = await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert any("review_plan" in str(n) for n in snapshot.next), \
            f"Expected review_plan, got {snapshot.next}"

        # 6. Resume plan → proposal_start_gate → proposal_write_next → review_section
        result = await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert any("review_section" in str(n) for n in snapshot.next), \
            f"Expected review_section, got {snapshot.next}"

        # 7. Resume sections (approve each until all_done → self_review → review_proposal)
        max_section_loops = 20
        for i in range(max_section_loops):
            result = await graph.ainvoke(
                Command(resume=_resume_approved()), config=config
            )
            snapshot = await graph.aget_state(config)
            if not snapshot.next:
                break  # 그래프 종료
            next_nodes = str(snapshot.next)
            if "review_proposal" in next_nodes:
                break
            if "review_section" not in next_nodes:
                break  # 예상치 못한 노드

        snapshot = await graph.aget_state(config)
        if snapshot.next:
            assert any("review_proposal" in str(n) for n in snapshot.next), \
                f"Expected review_proposal after sections, got {snapshot.next}"

            # 8. Resume proposal → presentation_strategy → ppt → review_ppt
            result = await graph.ainvoke(
                Command(resume=_resume_approved()), config=config
            )
            snapshot = await graph.aget_state(config)

            if snapshot.next:
                assert any("review_ppt" in str(n) for n in snapshot.next), \
                    f"Expected review_ppt, got {snapshot.next}"

                # 9. Resume PPT → stream1_complete_hook → END
                result = await graph.ainvoke(
                    Command(resume=_resume_approved()), config=config
                )
                snapshot = await graph.aget_state(config)

        # 최종 검증: 그래프가 END에 도달
        final_snapshot = await graph.aget_state(config)
        assert not final_snapshot.next, \
            f"그래프가 END에 도달하지 못함: next={final_snapshot.next}"

        # State 검증
        final_state = final_snapshot.values
        assert final_state.get("positioning"), "positioning이 설정되지 않음"


# ── No-Go 종료 ──

@pytest.mark.asyncio
async def test_no_go_terminates_workflow(initial_state, workflow_patches):
    """Go/No-Go에서 No-Go 결정 시 워크플로가 즉시 종료된다."""
    patches_list, _, _ = workflow_patches()

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        graph = await _build_graph_with_mocks(patches_list)
        config = {"configurable": {"thread_id": "no-go-001"}}

        # Start → review_rfp
        await graph.ainvoke(initial_state, config=config)

        # Resume review_rfp → review_gng
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)
        snapshot = await graph.aget_state(config)
        assert any("review_gng" in str(n) for n in snapshot.next)

        # Resume with No-Go → END
        await graph.ainvoke(
            Command(resume={"decision": "no_go", "approved": False, "approved_by": "tester"}),
            config=config,
        )

        final = await graph.aget_state(config)
        assert not final.next, f"No-Go 후 워크플로가 종료되지 않음: next={final.next}"


# ── Document-Only (PPT 스킵) ──

@pytest.mark.asyncio
async def test_document_only_skips_ppt(initial_state_doc_only, workflow_patches):
    """서류심사(document_only) 시 PPT 노드를 건너뛰고 END에 도달한다."""
    patches_list, _, _ = workflow_patches("rfp_analyze_doc_only.json")

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        graph = await _build_graph_with_mocks(patches_list)
        config = {"configurable": {"thread_id": "doc-only-001"}}

        # Start → review_rfp
        await graph.ainvoke(initial_state_doc_only, config=config)

        # review_rfp → review_gng
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        # review_gng (Go) → review_strategy
        await graph.ainvoke(Command(resume=_resume_go()), config=config)

        # review_strategy → review_bid_plan
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        # review_bid_plan → review_plan
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        # review_plan → sections...
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        # Approve sections until review_proposal
        for _ in range(20):
            snapshot = await graph.aget_state(config)
            if not snapshot.next:
                break
            next_str = str(snapshot.next)
            if "review_proposal" in next_str:
                break
            await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        snapshot = await graph.aget_state(config)
        if snapshot.next and "review_proposal" in str(snapshot.next):
            # review_proposal → presentation_strategy → document_only → END
            await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        # PPT review가 나타나지 않고 END에 도달해야 함
        final = await graph.aget_state(config)
        assert not final.next, \
            f"Document-only인데 워크플로가 계속됨: next={final.next}"
