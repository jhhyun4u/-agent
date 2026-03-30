"""LangGraph 워크플로 통합 테스트 — WF-01~04.

Mock 기반 (Level 1). CI에서 항상 실행.
전체 interrupt/resume 사이클, 상태 보존, 분기 검증.
"""

import pytest
from langgraph.types import Command

from tests.integration.conftest import resume_approved, resume_go, resume_rejected


# ── WF-01: Happy Path 전체 흐름 ──

@pytest.mark.asyncio
async def test_happy_path_head_section(graph_with_mocks, standard_rfp_state):
    """HEAD 구간: rfp_analyze → review_rfp → research → go_no_go → strategy.

    검증:
    - invoke 후 review_rfp에서 interrupt
    - resume(approved) → research_gather → go_no_go → review_gng
    - resume(go) → strategy_generate → review_strategy
    """
    graph = graph_with_mocks
    config = {"configurable": {"thread_id": "wf01-head"}}

    # 1. Start → rfp_analyze → review_rfp (interrupt)
    result = await graph.ainvoke(standard_rfp_state, config=config)
    snapshot = await graph.aget_state(config)
    assert snapshot.next, "그래프가 interrupt 없이 종료됨"
    waiting = [str(n) for n in snapshot.next]
    assert any("review_rfp" in n for n in waiting), f"Expected review_rfp, got {waiting}"

    # 2. Resume review_rfp → research → go_no_go → review_gng
    result = await graph.ainvoke(Command(resume=resume_approved()), config=config)
    snapshot = await graph.aget_state(config)
    assert snapshot.next, "go_no_go 후 interrupt 없음"
    waiting = [str(n) for n in snapshot.next]
    assert any("review_gng" in n for n in waiting), f"Expected review_gng, got {waiting}"

    # 3. Resume review_gng (go) → strategy → review_strategy
    result = await graph.ainvoke(Command(resume=resume_go()), config=config)
    snapshot = await graph.aget_state(config)
    assert snapshot.next, "strategy 후 interrupt 없음"
    waiting = [str(n) for n in snapshot.next]
    assert any("review_strategy" in n for n in waiting), f"Expected review_strategy, got {waiting}"

    # HEAD 구간의 state 검증
    state = snapshot.values
    assert state.get("rfp_analysis"), "rfp_analysis 산출물 없음"
    assert state.get("research_brief"), "research_brief 산출물 없음"
    assert state.get("go_no_go"), "go_no_go 산출물 없음"
    assert state.get("strategy"), "strategy 산출물 없음"


# ── WF-02: Interrupt/Resume 상태 보존 ──

@pytest.mark.asyncio
async def test_state_preservation_across_resumes(graph_with_mocks, standard_rfp_state):
    """각 interrupt/resume 사이클에서 이전 노드 출력이 보존되는지 검증."""
    graph = graph_with_mocks
    config = {"configurable": {"thread_id": "wf02-state"}}

    # Start → review_rfp
    await graph.ainvoke(standard_rfp_state, config=config)
    snapshot1 = await graph.aget_state(config)
    assert snapshot1.values.get("rfp_analysis"), "rfp_analysis가 저장되지 않음"

    # Resume → review_gng
    await graph.ainvoke(Command(resume=resume_approved()), config=config)
    snapshot2 = await graph.aget_state(config)
    # rfp_analysis가 여전히 존재해야 함
    assert snapshot2.values.get("rfp_analysis"), "resume 후 rfp_analysis 소실"
    assert snapshot2.values.get("research_brief"), "research_brief 없음"

    # Resume → review_strategy
    await graph.ainvoke(Command(resume=resume_go()), config=config)
    snapshot3 = await graph.aget_state(config)
    # 이전 모든 산출물 보존
    assert snapshot3.values.get("rfp_analysis"), "rfp_analysis 소실"
    assert snapshot3.values.get("research_brief"), "research_brief 소실"
    assert snapshot3.values.get("go_no_go"), "go_no_go 소실"
    assert snapshot3.values.get("strategy"), "strategy 소실"


# ── WF-03: No-Go 분기 → 조기 종료 ──

@pytest.mark.asyncio
async def test_no_go_early_termination(graph_with_mocks, standard_rfp_state):
    """Go/No-Go에서 no_go 결정 시 워크플로 즉시 종료."""
    graph = graph_with_mocks
    config = {"configurable": {"thread_id": "wf03-nogo"}}

    # Start → review_rfp
    await graph.ainvoke(standard_rfp_state, config=config)

    # Resume review_rfp → review_gng
    await graph.ainvoke(Command(resume=resume_approved()), config=config)

    # Resume review_gng (no_go) → END
    result = await graph.ainvoke(
        Command(resume={"decision": "no_go", "approved": True, "approved_by": "tester"}),
        config=config,
    )
    snapshot = await graph.aget_state(config)

    # 그래프 종료 확인 (next가 비어 있음)
    assert not snapshot.next, f"No-Go 후에도 그래프 계속 진행: {snapshot.next}"


# ── WF-04: review_rfp 거부 → rfp_analyze 재실행 ──

@pytest.mark.asyncio
async def test_review_rejection_loops_back(graph_with_mocks, standard_rfp_state):
    """review_rfp에서 거부(rejected) 시 rfp_analyze로 복귀."""
    graph = graph_with_mocks
    config = {"configurable": {"thread_id": "wf04-reject"}}

    # Start → review_rfp
    await graph.ainvoke(standard_rfp_state, config=config)
    snapshot1 = await graph.aget_state(config)
    assert any("review_rfp" in str(n) for n in snapshot1.next)

    # Resume review_rfp (rejected) → rfp_analyze 재실행 → review_rfp (다시 interrupt)
    result = await graph.ainvoke(
        Command(resume={"approved": False, "feedback": "RFP 분석 보완 필요"}),
        config=config,
    )
    snapshot2 = await graph.aget_state(config)
    assert snapshot2.next, "거부 후 그래프 종료됨 (재실행 기대)"
    waiting = [str(n) for n in snapshot2.next]
    assert any("review_rfp" in n for n in waiting), f"Expected review_rfp again, got {waiting}"


# ── WF-04b: Fork/Convergence 라우팅 함수 검증 ──

@pytest.mark.asyncio
async def test_fork_to_branches_returns_two_sends():
    """fork_to_branches가 Path A (plan) + Path B (submission_plan) 2개 Send 반환."""
    from langgraph.types import Send
    from app.graph.nodes.gate_nodes import fork_to_branches

    mock_state = {"project_id": "fork-test", "current_step": "strategy_complete"}
    sends = fork_to_branches(mock_state)

    assert isinstance(sends, list), f"Send 목록이 아님: {type(sends)}"
    assert len(sends) == 2, f"Expected 2 Send, got {len(sends)}"

    # Send 대상 노드 확인
    targets = [s.node for s in sends]
    assert "plan_fan_out_gate" in targets, f"plan_fan_out_gate 없음: {targets}"
    assert "submission_plan" in targets, f"submission_plan 없음: {targets}"


@pytest.mark.asyncio
async def test_convergence_gate_passthrough():
    """convergence_gate가 빈 dict를 반환 (상태 변경 없이 통과)."""
    from app.graph.nodes.gate_nodes import convergence_gate

    mock_state = {"project_id": "conv-test", "current_step": "path_a_done"}
    result = convergence_gate(mock_state)

    assert result == {}, f"convergence_gate가 빈 dict가 아님: {result}"


@pytest.mark.asyncio
async def test_plan_selective_fan_out_full():
    """rework_targets 없으면 ALL_PLAN_NODES 전체 실행."""
    from langgraph.types import Send
    from app.graph.nodes.gate_nodes import plan_selective_fan_out, ALL_PLAN_NODES

    mock_state = {"project_id": "fan-test"}
    sends = plan_selective_fan_out(mock_state)

    assert len(sends) == len(ALL_PLAN_NODES), f"Expected {len(ALL_PLAN_NODES)}, got {len(sends)}"


@pytest.mark.asyncio
async def test_plan_selective_fan_out_partial():
    """rework_targets 지정 시 해당 노드만 실행."""
    from langgraph.types import Send
    from app.graph.nodes.gate_nodes import plan_selective_fan_out

    mock_state = {"project_id": "fan-test2", "rework_targets": ["plan_team", "plan_story"]}
    sends = plan_selective_fan_out(mock_state)

    targets = [s.node for s in sends]
    assert set(targets) == {"plan_team", "plan_story"}, f"Unexpected: {targets}"
