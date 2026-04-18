"""
단위 테스트: STEP 1-① RFP 분석 노드 (rfp_analyze.py)

Phase 1 버그 수정 검증:
- 1-C: format_template 타입 체크
- 1-D: 에러 처리 패턴 통일
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.state import ProposalState, RFPAnalysis, ComplianceItem
from app.graph.nodes.rfp_analyze import rfp_analyze


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_rfp_raw_records_node_error():
    """
    테스트: rfp_raw가 비어있을 때 구조화된 node_errors 기록 (Bug 1-D 수정)

    예상:
    - current_step = "rfp_analyze_error"
    - node_errors["rfp_analyze"] 구조체에 error, step, hint 포함
    """
    state: ProposalState = {
        "rfp_raw": "",
        "project_name": "Test Project",
        "node_errors": {},
    }

    result = await rfp_analyze(state)

    assert result["current_step"] == "rfp_analyze_error"
    assert "rfp_analyze" in result["node_errors"]

    error_detail = result["node_errors"]["rfp_analyze"]
    assert "error" in error_detail
    assert "step" in error_detail
    assert "hint" in error_detail
    assert error_detail["step"] == "rfp_analyze"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_template_list_no_crash():
    """
    테스트: format_template.structure가 list일 때 크래시 없이 처리 (Bug 1-C 수정)

    예상:
    - isinstance 체크로 인해 list 타입도 정상 처리
    - sections 리스트 생성 성공
    - 크래시 없이 반환
    """
    test_rfp = "평가기준: 기술 90점, 가격 10점\n과업범위: AI 개발"

    # format_template.structure가 list인 경우 모킹
    mock_result = {
        "project_name": "Test Project",
        "client": "Test Client",
        "deadline": "2026-05-31",
        "case_type": "B",
        "eval_method": "종합심사",
        "eval_items": [{"item": "기술", "weight": 90}],
        "tech_price_ratio": {"tech": 90, "price": 10},
        "hot_buttons": [],
        "mandatory_reqs": [],
        "format_template": {
            "exists": True,
            "structure": [  # ← LIST 타입 (dict 아님)
                {"section1": "내용1"},
                "section2",
            ]
        },
        "volume_spec": {},
        "special_conditions": [],
        "price_scoring": None,
        "domain": "SI/SW개발",
        "project_scope": "테스트",
        "budget": "1,000,000,000",
        "duration": "12개월",
        "contract_type": "정액",
        "delivery_phases": [],
        "qualification_requirements": [],
        "similar_project_requirements": [],
        "key_personnel_requirements": [],
        "subcontracting_conditions": [],
        "compliance_items": [],
    }

    state: ProposalState = {
        "rfp_raw": test_rfp,
        "project_name": "Test Project",
        "node_errors": {},
    }

    with patch(
        "app.graph.nodes.rfp_analyze.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await rfp_analyze(state)

    # 크래시 없이 성공적으로 섹션 생성
    assert result["current_step"] == "rfp_analyze_complete"
    assert "dynamic_sections" in result
    assert isinstance(result["dynamic_sections"], list)
    assert len(result["dynamic_sections"]) > 0
