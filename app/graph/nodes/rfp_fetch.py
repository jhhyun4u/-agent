"""
STEP 0→1 전환: G2B 상세 수집 + RFP 업로드 게이트 (§6-1)

하이브리드 방식: G2B 자동 수집 + 사용자 RFP 파일 업로드.
"""

import logging

from langgraph.types import interrupt

from app.graph.state import BidDetail, ProposalState

logger = logging.getLogger(__name__)


async def rfp_fetch(state: ProposalState) -> dict:
    """STEP 0→1: G2B 상세 수집 + RFP 파일 업로드 게이트."""

    bid_no = state.get("picked_bid_no", "")

    # 1) G2B 공고 상세 자동 수집
    from app.services.g2b_service import get_bid_detail
    try:
        detail = await get_bid_detail(bid_no)
    except Exception as e:
        logger.warning(f"G2B 상세 수집 실패: {e}")
        detail = {
            "project_name": state.get("project_name", bid_no),
            "client": "", "budget": "", "deadline": "",
            "description": "", "requirements_summary": "",
            "attachments": [],
        }

    bid_detail = BidDetail(
        bid_no=bid_no,
        project_name=detail.get("project_name", ""),
        client=detail.get("client", ""),
        budget=detail.get("budget", ""),
        deadline=detail.get("deadline", ""),
        description=detail.get("description", ""),
        requirements_summary=detail.get("requirements_summary", ""),
        attachments=detail.get("attachments", []),
    )

    # 2) G2B 첨부파일에서 RFP 자동 추출 시도
    auto_rfp_text = ""
    for att in bid_detail.attachments:
        if att.get("type") in ("pdf", "hwp", "hwpx"):
            try:
                from app.services.rfp_parser import parse_rfp_from_url
                auto_rfp_text = await parse_rfp_from_url(att["url"], att["type"])
                break
            except Exception:
                continue

    bid_detail.rfp_auto_text = auto_rfp_text

    # 3) interrupt: 사용자에게 RFP 파일 업로드 기회
    human_input = interrupt({
        "step": "rfp_fetch",
        "bid_detail": bid_detail.model_dump(),
        "has_auto_rfp": bool(auto_rfp_text),
        "message": "공고 상세를 수집했습니다. RFP 원본 파일이 있으면 업로드하세요.",
        "hint": (
            "G2B 첨부파일에서 RFP를 자동 추출했습니다."
            if auto_rfp_text
            else "G2B 첨부파일에서 RFP를 찾지 못했습니다. 직접 업로드해 주세요."
        ),
    })

    # 4) 사용자 응답 처리
    if human_input.get("rfp_file_text"):
        rfp_raw = human_input["rfp_file_text"]
    elif auto_rfp_text:
        rfp_raw = auto_rfp_text
    else:
        rfp_raw = f"[공고 상세 기반]\n{bid_detail.description}\n\n{bid_detail.requirements_summary}"

    return {
        "bid_detail": bid_detail,
        "rfp_raw": rfp_raw,
        "project_name": bid_detail.project_name,
        "current_step": "rfp_fetch_complete",
    }
