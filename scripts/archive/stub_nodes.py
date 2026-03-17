"""
Stub 노드 (Phase 2~5에서 실제 구현 예정)

각 노드는 실행 시 current_step만 갱신하여 그래프 흐름을 유지.
"""

import logging

from app.graph.state import ProposalState

logger = logging.getLogger(__name__)


async def strategy_generate(state: ProposalState) -> dict:
    """STEP 2: 전략 수립 (Phase 2 구현 예정)."""
    logger.info("[STUB] strategy_generate — Phase 2 구현 예정")
    return {"current_step": "strategy_complete"}


async def plan_team(state: ProposalState) -> dict:
    """STEP 3: 팀 구성 계획."""
    logger.info("[STUB] plan_team")
    return {"parallel_results": {"team": []}}


async def plan_assign(state: ProposalState) -> dict:
    """STEP 3: 역할 배분."""
    logger.info("[STUB] plan_assign")
    return {"parallel_results": {"deliverables": []}}


async def plan_schedule(state: ProposalState) -> dict:
    """STEP 3: 일정 계획."""
    logger.info("[STUB] plan_schedule")
    return {"parallel_results": {"schedule": {}}}


async def plan_story(state: ProposalState) -> dict:
    """STEP 3: 스토리라인."""
    logger.info("[STUB] plan_story")
    return {"parallel_results": {"storylines": {}}}


async def plan_price(state: ProposalState) -> dict:
    """STEP 3: 가격 산정."""
    logger.info("[STUB] plan_price")
    return {"parallel_results": {"bid_price": {}}}


async def proposal_section(state: ProposalState) -> dict:
    """STEP 4: 섹션별 제안서 작성."""
    section_id = state.get("_current_section_id", "unknown")
    logger.info(f"[STUB] proposal_section — {section_id}")
    return {"parallel_results": {"sections": []}}


async def self_review_with_auto_improve(state: ProposalState) -> dict:
    """STEP 4: 자가진단 + 자동 개선 루프 (Phase 4 구현 예정)."""
    logger.info("[STUB] self_review_with_auto_improve")
    return {"current_step": "self_review_pass"}


async def presentation_strategy(state: ProposalState) -> dict:
    """v3.2: 발표전략 수립 (Phase 5 구현 예정). 서류심사 시 건너뛰기."""
    logger.info("[STUB] presentation_strategy")
    return {"current_step": "presentation_strategy_complete"}


async def ppt_slide(state: ProposalState) -> dict:
    """STEP 5: PPT 슬라이드 생성."""
    logger.info("[STUB] ppt_slide")
    return {"parallel_results": {"slides": []}}
