"""LangGraph 워크플로 실행 테스트 — Happy Path.

실제 그래프를 MemorySaver로 컴파일하고,
Claude API + Supabase를 mock하여 전체 interrupt/resume 사이클을 검증한다.

v4.0: fork_gate 병렬 분기 (Path A + Path B) 반영.
"""
import pytest
from contextlib import ExitStack

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


def _get_interrupt_ids(snapshot):
    """스냅샷에서 pending interrupt ID 목록 추출."""
    ids = []
    for task in getattr(snapshot, "tasks", []):
        for intr in getattr(task, "interrupts", []):
            if hasattr(intr, "id"):
                ids.append(intr.id)
    return ids


async def _resume_all_pending(graph, config, resume_data):
    """모든 pending interrupt를 한 번에 resume.

    LangGraph Command.resume은 dict[interrupt_id, value]를 지원하여
    다중 interrupt를 한 번의 ainvoke로 처리할 수 있다.
    """
    snapshot = await graph.aget_state(config)
    interrupt_ids = _get_interrupt_ids(snapshot)
    if len(interrupt_ids) > 1:
        # 다중 interrupt: ID → resume_data 매핑
        resume_map = {iid: resume_data for iid in interrupt_ids}
        await graph.ainvoke(Command(resume=resume_map), config=config)
    else:
        # 단일 interrupt
        await graph.ainvoke(Command(resume=resume_data), config=config)
    return await graph.aget_state(config)


# ── Happy Path: Case A + PPT ──

@pytest.mark.asyncio
async def test_happy_path_full_workflow(initial_state, workflow_patches):
    """전체 워크플로 Happy Path: RFP 분석 → 전략 → fork(A+B) → 통합 → END."""
    patches_list, mock_claude, mock_sb = workflow_patches()

    with ExitStack() as stack:
        for p in patches_list:
            stack.enter_context(p)

        graph = await _build_graph_with_mocks(patches_list)
        config = {"configurable": {"thread_id": "happy-path-001"}}

        # 1. Start → rfp_analyze → review_rfp (first interrupt)
        await graph.ainvoke(initial_state, config=config)
        snapshot = await graph.aget_state(config)
        assert snapshot.next, "그래프가 interrupt 없이 종료됨"
        assert any("review_rfp" in str(n) for n in snapshot.next), \
            f"Expected review_rfp, got {snapshot.next}"

        # 2. Resume review_rfp → research_gather → go_no_go → review_gng
        await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert snapshot.next, "review_rfp 승인 후 interrupt 없이 종료됨"
        assert any("review_gng" in str(n) for n in snapshot.next), \
            f"Expected review_gng, got {snapshot.next}"

        # 3. Resume Go → strategy_generate → review_strategy
        await graph.ainvoke(
            Command(resume=_resume_go()), config=config
        )
        snapshot = await graph.aget_state(config)
        assert any("review_strategy" in str(n) for n in snapshot.next), \
            f"Expected review_strategy, got {snapshot.next}"

        # 4. Resume strategy → fork_gate → Path A (plan) + Path B (submission_plan)
        #    Both paths run in parallel. We may get multiple interrupts.
        await graph.ainvoke(
            Command(resume=_resume_approved()), config=config
        )

        # After fork, process all interrupts from both paths until convergence → END.
        max_loops = 40
        for _ in range(max_loops):
            snapshot = await graph.aget_state(config)
            if not snapshot.next:
                break

            # Resume all pending interrupts (handles both single and multiple)
            await _resume_all_pending(graph, config, _resume_approved())

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
    """서류심사(document_only) 시 PPT 노드를 건너뛰고 END에 도달한다.

    v4.0: fork_gate 병렬 분기 반영. 다중 interrupt 시 interrupt_id 지정.
    """
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

        # review_strategy → fork_gate → Path A + Path B (parallel)
        # Process all interrupts until END
        await graph.ainvoke(Command(resume=_resume_approved()), config=config)

        ppt_review_seen = False
        max_loops = 40
        for _ in range(max_loops):
            snapshot = await graph.aget_state(config)
            if not snapshot.next:
                break

            next_str = str(snapshot.next)
            if "review_ppt" in next_str:
                ppt_review_seen = True

            # Resume all pending interrupts (handles both single and multiple)
            await _resume_all_pending(graph, config, _resume_approved())

        # PPT review가 나타나지 않고 END에 도달해야 함
        final = await graph.aget_state(config)
        assert not final.next, \
            f"Document-only인데 워크플로가 계속됨: next={final.next}"
        # document_only에서는 PPT 리뷰가 나타나지 않아야 함 (mock_evaluation으로 직행)
        assert not ppt_review_seen, "Document-only인데 review_ppt가 나타남"
