"""
v4.0: Path B 제출서류 경로 노드 (3B, 5B, 6B)

3B — submission_plan: RFP에서 제출서류 목록 추출 + 준비 계획
5B — cost_sheet_generate: 가격 산출내역서 작성
6B — submission_checklist: 제출서류 체크리스트 최종 확인
"""

import logging

from app.graph.state import ProposalState
from app.services.core.claude_client import claude_generate

logger = logging.getLogger(__name__)


# ── 3B: 제출서류 계획 ──

async def submission_plan(state: ProposalState) -> dict:
    """RFP에서 제출서류 목록을 추출하고 준비 계획을 수립."""
    rfp = state.get("rfp_analysis")
    rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
    rfp_raw = state.get("rfp_raw", "")
    strategy = state.get("strategy")
    strategy_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    prompt = f"""다음 RFP를 분석하여 제출서류 준비 계획을 수립하세요.

## RFP 원문 (일부)
{rfp_raw[:8000]}

## RFP 분석 요약
- 과제명: {rfp_dict.get('title', '')}
- 평가방법: {rfp_dict.get('eval_method', '')}
- 필수요건: {rfp_dict.get('mandatory_reqs', [])}

## 전략 요약
- 포지셔닝: {strategy_dict.get('positioning', '')}

## 출력 형식 (JSON)
{{
  "documents": [
    {{
      "doc_id": "D-01",
      "name": "제안서 (기술 부문)",
      "type": "proposal",
      "required": true,
      "format": "DOCX/HWP",
      "deadline_note": "제출 마감일까지",
      "responsible": "제안팀",
      "status": "pending",
      "source": "AI 워크플로 자동 생성"
    }}
  ],
  "timeline": {{
    "preparation_start": "전략수립 완료 후 즉시",
    "milestones": [
      {{"date_relative": "D-7", "task": "초안 완료"}},
      {{"date_relative": "D-3", "task": "최종 검토"}},
      {{"date_relative": "D-1", "task": "인쇄/제본"}}
    ]
  }},
  "risks": ["서류 누락 리스크 항목..."],
  "notes": "기타 참고사항"
}}
"""

    try:
        result = await claude_generate(
            prompt=prompt,
            system_prompt="당신은 공공기관 용역 입찰 전문가입니다. 제출서류 목록을 빠짐없이 추출하세요.",
            response_format="json",
        )
        return {
            "submission_plan": result,
            "current_step": "submission_plan_complete",
        }
    except Exception as e:
        logger.error(f"[NODE CRITICAL] submission_plan: {e}", exc_info=True)
        return {
            "submission_plan": {"error": str(e), "documents": []},
            "current_step": "submission_plan_error",
            "node_errors": {
                **state.get("node_errors", {}),
                "submission_plan": {
                    "error": f"{type(e).__name__}: {str(e)[:300]}",
                    "step": "submission_plan",
                },
            },
        }


# ── 5B: 산출내역서 작성 ──

async def cost_sheet_generate(state: ProposalState) -> dict:
    """입찰가 결정 결과를 기반으로 가격 산출내역서를 생성."""
    bid_plan = state.get("bid_plan")
    bid_plan.model_dump() if hasattr(bid_plan, "model_dump") else (bid_plan if isinstance(bid_plan, dict) else {})
    constraint = state.get("bid_budget_constraint", {})
    rfp = state.get("rfp_analysis")
    rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
    plan = state.get("plan")
    plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})

    prompt = f"""입찰 가격 결정 결과를 바탕으로 가격 산출내역서를 작성하세요.

## 입찰가격 계획
- 목표 투찰가: {constraint.get('total_bid_price', 0):,}원
- 투찰률: {constraint.get('bid_ratio', 0)}%
- 시나리오: {constraint.get('scenario_name', '')}
- 원가표준: {constraint.get('cost_standard', 'KOSA')}

## 팀 구성 (인건비 기초)
{plan_dict.get('team', [])}

## RFP 예산
{rfp_dict.get('budget', '미기재')}

## 출력 형식 (JSON)
{{
  "summary": {{
    "total_amount": 0,
    "labor_cost": 0,
    "direct_expense": 0,
    "overhead": 0,
    "profit": 0,
    "vat": 0
  }},
  "labor_breakdown": [
    {{
      "role": "PM",
      "grade": "특급",
      "unit_price": 0,
      "person_months": 0,
      "subtotal": 0,
      "note": ""
    }}
  ],
  "direct_expenses": [
    {{"item": "항목명", "amount": 0, "note": ""}}
  ],
  "calculation_basis": "산출 근거 설명",
  "notes": "특이사항"
}}
"""

    try:
        result = await claude_generate(
            prompt=prompt,
            system_prompt="당신은 공공기관 용역 가격 산출 전문가입니다. KOSA 노임단가 기준으로 정확한 산출내역서를 작성하세요.",
            response_format="json",
        )
        return {
            "cost_sheet": result,
            "current_step": "cost_sheet_complete",
        }
    except Exception as e:
        logger.error(f"[NODE CRITICAL] cost_sheet_generate: {e}", exc_info=True)
        return {
            "cost_sheet": {"error": str(e)},
            "current_step": "cost_sheet_error",
            "node_errors": {
                **state.get("node_errors", {}),
                "cost_sheet_generate": {
                    "error": f"{type(e).__name__}: {str(e)[:300]}",
                    "step": "cost_sheet_generate",
                },
            },
        }


# ── 6B: 제출서류 확인 (체크리스트) ──

async def submission_checklist(state: ProposalState) -> dict:
    """모든 제출서류의 준비 상태를 체크리스트로 최종 확인."""
    sub_plan = state.get("submission_plan", {})
    documents = sub_plan.get("documents", [])
    cost_sheet = state.get("cost_sheet", {})
    proposal_sections = state.get("proposal_sections", [])
    ppt_slides = state.get("ppt_slides", [])

    # 자동 체크: 산출물 존재 여부
    checklist = []
    for doc in documents:
        item = {
            "doc_id": doc.get("doc_id", ""),
            "name": doc.get("name", ""),
            "required": doc.get("required", True),
            "status": "not_ready",
            "note": "",
        }
        dtype = doc.get("type", "")
        if dtype == "proposal" and len(proposal_sections) > 0:
            item["status"] = "ready"
            item["note"] = f"제안서 {len(proposal_sections)}개 섹션 작성 완료"
        elif dtype == "cost_sheet" and cost_sheet and not cost_sheet.get("error"):
            item["status"] = "ready"
            item["note"] = "산출내역서 생성 완료"
        elif dtype == "ppt" and len(ppt_slides) > 0:
            item["status"] = "ready"
            item["note"] = f"PPT {len(ppt_slides)}장 생성 완료"
        elif dtype == "certificate":
            item["status"] = "manual_check"
            item["note"] = "수동 확인 필요 (자격증, 인증서 등)"
        else:
            item["status"] = "manual_check"
            item["note"] = doc.get("source", "준비 상태 확인 필요")

        checklist.append(item)

    ready_count = sum(1 for c in checklist if c["status"] == "ready")
    total_required = sum(1 for c in checklist if c["required"])
    manual_count = sum(1 for c in checklist if c["status"] == "manual_check")

    result = {
        "checklist": checklist,
        "summary": {
            "total": len(checklist),
            "ready": ready_count,
            "manual_check": manual_count,
            "not_ready": len(checklist) - ready_count - manual_count,
            "all_required_ready": ready_count >= total_required,
        },
        "recommendation": (
            "모든 필수 서류가 준비되었습니다." if ready_count >= total_required
            else f"필수 서류 {total_required - ready_count}건 미준비 — 확인이 필요합니다."
        ),
    }

    return {
        "submission_checklist_result": result,
        "current_step": "submission_checklist_complete",
    }
