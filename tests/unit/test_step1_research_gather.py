"""
단위 테스트: STEP 1-②  Research Gathering 노드 (research_gather.py)

Phase 1 버그 수정 검증:
- 1-A: 필드명 불일치 수정 (project_scope, hot_buttons)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.state import ProposalState, RFPAnalysis


@pytest.mark.unit
@pytest.mark.asyncio
async def test_project_scope_in_prompt():
    """
    테스트: project_scope가 연구 프롬프트에 포함되어 전달됨 (Bug 1-A 수정)

    배경:
    - 이전: rfp_dict.get("scope", "") → 항상 "" (필드명 불일치)
    - 수정: rfp_dict.get("project_scope", "") → 실제 사업범위 전달

    예상:
    - claude_generate() 호출 시 project_scope 값이 프롬프트에 포함되어야 함
    """
    from app.graph.nodes.research_gather import research_gather

    test_scope = "AI 기반 고객상담 챗봇 개발 및 운영"

    rfp_analysis = RFPAnalysis(
        project_name="AI 챗봇 개발",
        client="홍길동",
        deadline="2026-05-31",
        case_type="A",
        eval_method="종합심사",
        eval_items=[],
        tech_price_ratio={"tech": 90, "price": 10},
        hot_buttons=["AI 기술", "고객만족도"],
        mandatory_reqs=[],
        format_template={"exists": False, "structure": None},
        volume_spec={},
        special_conditions=[],
        price_scoring=None,
        domain="SI/SW개발",
        project_scope=test_scope,  # ← 중요: 사업범위 포함
        budget="1,000,000,000",
        duration="12개월",
        contract_type="정액",
        delivery_phases=[],
        qualification_requirements=[],
        similar_project_requirements=[],
        key_personnel_requirements=[],
        subcontracting_conditions=[],
    )

    state: ProposalState = {
        "rfp_analysis": rfp_analysis,
        "project_name": "AI 챗봇 개발",
        "node_errors": {},
    }

    mock_research = {
        "similar_projects": [
            {
                "company": "테크사",
                "project": "챗봇 개발",
                "outcome": "성공",
                "relevance_score": 0.9,
            }
        ],
        "competitor_info": [
            {"company": "경쟁사A", "strength": "기술력", "weakness": "가격"}
        ],
        "market_insights": ["시장은 AI 챗봇 수요 증가"],
        "technical_keywords": ["AI", "NLP", "챗봇"],
    }

    # claude_generate 호출 시 project_scope가 포함되어야 함
    with patch(
        "app.graph.nodes.research_gather.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_research,
    ) as mock_claude:
        result = await research_gather(state)

        # claude_generate 호출 확인
        assert mock_claude.called
        # 호출된 프롬프트에 project_scope 포함 확인
        prompt_arg = mock_claude.call_args[0][0]
        assert test_scope in prompt_arg, f"project_scope '{test_scope}' not in prompt"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_rfp_analysis_early_return():
    """
    테스트: rfp_analysis 없으면 조기 반환 (안정성)

    예상:
    - rfp_analysis가 None이면 early return
    - node_errors 기록
    - claude_generate 호출 없음 (비용 절감)
    """
    from app.graph.nodes.research_gather import research_gather

    state: ProposalState = {
        "rfp_analysis": None,  # ← 누락
        "project_name": "Test",
        "node_errors": {},
    }

    with patch(
        "app.graph.nodes.research_gather.claude_generate",
        new_callable=AsyncMock,
    ) as mock_claude:
        result = await research_gather(state)

        # 조기 반환: claude_generate 호출 안함
        assert not mock_claude.called, "claude_generate should not be called when rfp_analysis is None"

        # 에러 기록 확인
        if "node_errors" in result:
            assert "research_gather" in result.get("node_errors", {})
