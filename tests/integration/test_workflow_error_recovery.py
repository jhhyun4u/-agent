"""워크플로 에러 복구 테스트 — WF-05~06.

Mock 기반 (Level 1). Claude API 에러, self_review 라우팅 검증.

NOTE: Legacy test - required fixtures no longer exist
"""

import pytest

pytestmark = pytest.mark.skip(reason="Legacy test - required fixtures no longer exist in conftest")


# ── WF-05: self_review 라우팅 함수 검증 ──

@pytest.mark.asyncio
async def test_self_review_retry_route():
    """current_step이 매칭 안 되면 기본값 retry_sections 반환.

    라우팅 함수는 current_step 기반:
    - self_review_pass → pass
    - self_review_retry_research → retry_research
    - self_review_force_review → force_review
    - 그 외 → retry_sections (기본값)
    """
    from app.graph.edges import route_after_self_review

    # 기본값(retry_sections): 매칭 안 되는 current_step
    mock_state = {"current_step": "self_review_retry_sections"}
    result = route_after_self_review(mock_state)
    assert result == "retry_sections", f"Expected retry_sections, got {result}"

    # retry_research
    mock_state2 = {"current_step": "self_review_retry_research"}
    result2 = route_after_self_review(mock_state2)
    assert result2 == "retry_research", f"Expected retry_research, got {result2}"


@pytest.mark.asyncio
async def test_self_review_pass_route():
    """current_step=self_review_pass → pass 반환."""
    from app.graph.edges import route_after_self_review

    mock_state = {"current_step": "self_review_pass"}
    result = route_after_self_review(mock_state)
    assert result == "pass", f"Expected pass, got {result}"


@pytest.mark.asyncio
async def test_self_review_force_review_route():
    """current_step=self_review_force_review → force_review 반환."""
    from app.graph.edges import route_after_self_review

    mock_state = {"current_step": "self_review_force_review"}
    result = route_after_self_review(mock_state)
    assert result == "force_review", f"Expected force_review, got {result}"


# ── WF-06: Claude API 타임아웃 — HEAD 구간에서 검증 ──

@pytest.mark.asyncio
async def test_claude_timeout_in_strategy_node():
    """strategy_generate에서 Claude 타임아웃 발생 시 에러 전파.

    HEAD 구간(fork 전)에서만 테스트하여 다중 interrupt 문제 회피.
    """
    from app.exceptions import TenopAPIError

    timeout_mock = _make_claude_error_mock("timeout")

    async def claude_with_strategy_timeout(prompt, **kwargs):
        text = prompt if isinstance(prompt, str) else str(prompt)
        if "제안 전략을 수립" in text or "포지셔닝 매트릭스" in text:
            return await timeout_mock(prompt, **kwargs)
        return await _make_claude_mock()(prompt, **kwargs)

    patches, _, _ = build_all_patches(claude_side_effect=claude_with_strategy_timeout)

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        from app.graph.graph import build_graph
        graph = build_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "wf06-timeout"}}

        # HEAD: rfp → review_rfp
        state = {"project_id": "wf06", "rfp_raw": "사업명: 테스트\n예산: 1억", "current_step": ""}
        await graph.ainvoke(state, config=config)
        # resume review_rfp
        await graph.ainvoke(Command(resume=resume_approved()), config=config)
        # resume review_gng (go) → strategy_generate에서 timeout 기대
        snapshot = await graph.aget_state(config)
        assert any("review_gng" in str(n) for n in snapshot.next)

        with pytest.raises((TenopAPIError, Exception)) as exc_info:
            await graph.ainvoke(Command(resume=resume_go()), config=config)

        # TenopAPIError이면 AI_003, 아니면 LangGraph가 래핑한 에러
        err = exc_info.value
        if isinstance(err, TenopAPIError):
            assert err.error_code == "AI_003", f"Expected AI_003, got {err.error_code}"
        else:
            # LangGraph가 내부에서 에러를 래핑할 수 있음
            assert "timeout" in str(err).lower() or "AI_003" in str(err), \
                f"Unexpected error: {err}"
