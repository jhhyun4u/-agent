"""
STEP 1-①: RFP 분석 + Compliance Matrix 초안 (§6)

RFP 텍스트를 분석하여 구조화된 분석 결과 생성.
"""

import logging

from app.graph.state import ComplianceItem, ProposalState, RFPAnalysis
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


async def rfp_analyze(state: ProposalState) -> dict:
    """STEP 1-①: RFP 분석 + Compliance Matrix 초안 생성."""

    rfp_raw = state.get("rfp_raw", "")
    if not rfp_raw:
        return {"current_step": "rfp_analyze_error"}

    bid_detail = state.get("bid_detail")
    bid_context = ""
    if bid_detail:
        bid_context = f"""
## 공고 기본 정보
- 공고번호: {bid_detail.bid_no}
- 사업명: {bid_detail.project_name}
- 발주기관: {bid_detail.client}
- 예산: {bid_detail.budget}
- 마감일: {bid_detail.deadline}
"""

    prompt = f"""다음 RFP 문서를 분석하세요.

{bid_context}

## RFP 원문
{rfp_raw[:30000]}

## 분석 요구사항
1. 사업 유형 판단: 케이스 A (자유양식) vs 케이스 B (지정 서식)
2. 평가 항목 + 배점 역설계
3. 기술:가격 비중
4. Hot Buttons (발주처 핵심 관심사)
5. 필수 요건 (불충족 시 탈락)
6. 서식 템플릿 존재 여부 + 구조
7. 분량 규격
8. 특수 조건

## 출력 형식 (JSON)
{{
  "project_name": "사업명",
  "client": "발주기관",
  "deadline": "마감일",
  "case_type": "A 또는 B",
  "eval_items": [{{"item": "항목명", "weight": 30, "sub_items": ["세부항목"]}}],
  "tech_price_ratio": {{"tech": 90, "price": 10}},
  "hot_buttons": ["핫버튼 키워드"],
  "mandatory_reqs": ["필수 요건"],
  "format_template": {{"exists": false, "structure": null}},
  "volume_spec": {{"max_pages": 100, "font_size": "11pt"}},
  "special_conditions": ["특수 조건"],
  "compliance_items": [
    {{"req_id": "RFP-001", "content": "요건 내용", "source_step": "rfp_analyze"}}
  ]
}}
"""

    result = await claude_generate(prompt)

    # RFP 분석 결과 구성
    rfp_analysis = RFPAnalysis(
        project_name=result.get("project_name", state.get("project_name", "")),
        client=result.get("client", ""),
        deadline=result.get("deadline", ""),
        case_type=result.get("case_type", "A"),
        eval_items=result.get("eval_items", []),
        tech_price_ratio=result.get("tech_price_ratio", {"tech": 90, "price": 10}),
        hot_buttons=result.get("hot_buttons", []),
        mandatory_reqs=result.get("mandatory_reqs", []),
        format_template=result.get("format_template", {"exists": False, "structure": None}),
        volume_spec=result.get("volume_spec", {}),
        special_conditions=result.get("special_conditions", []),
    )

    # Compliance Matrix 초안
    compliance_items = [
        ComplianceItem(
            req_id=item.get("req_id", f"RFP-{i:03d}"),
            content=item.get("content", ""),
            source_step="rfp_analyze",
        )
        for i, item in enumerate(result.get("compliance_items", []), 1)
    ]

    # 동적 섹션 목록 생성 (케이스 A: 평가항목 기반, 케이스 B: 서식 구조 기반)
    if rfp_analysis.case_type == "B" and rfp_analysis.format_template.get("structure"):
        sections = list(rfp_analysis.format_template["structure"].keys())
    else:
        sections = [item.get("item", f"section_{i}") for i, item in enumerate(rfp_analysis.eval_items, 1)]

    # v3.5: 섹션 유형 자동 분류
    from app.prompts.section_prompts import classify_section_type
    section_type_map = {}
    for section_id in sections:
        section_type_map[section_id] = classify_section_type(section_id)

    return {
        "rfp_analysis": rfp_analysis,
        "compliance_matrix": compliance_items,
        "dynamic_sections": sections,
        "parallel_results": {"_section_type_map": section_type_map},
        "current_step": "rfp_analyze_complete",
        "project_name": rfp_analysis.project_name or state.get("project_name", ""),
    }
