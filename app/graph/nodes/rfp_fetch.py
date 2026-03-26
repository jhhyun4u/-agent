"""
STEP 0→1 전환: G2B 상세 수집 + RFP 업로드 게이트 (§6-1)

하이브리드 방식: G2B 자동 수집 + 사용자 RFP 파일 업로드.
첨부파일은 Supabase Storage에 저장하여 사용자가 열람/다운로드 가능.
"""

import logging

from langgraph.types import interrupt

from app.config import settings
from app.graph.state import BidDetail, ProposalState

logger = logging.getLogger(__name__)

STORAGE_BUCKET = settings.storage_bucket_proposals


async def rfp_fetch(state: ProposalState) -> dict:
    """STEP 0→1: G2B 상세 수집 + RFP 파일 업로드 게이트."""

    bid_no = state.get("picked_bid_no", "")
    proposal_id = state.get("proposal_id", "")

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

    # 2) 첨부파일 다운로드 + Storage 저장 + 텍스트 추출
    auto_rfp_text = ""
    stored_attachments = []

    for att in bid_detail.attachments:
        file_type = att.get("type", "unknown")
        url = att.get("url", "")

        if not url or file_type == "link":
            stored_attachments.append(att)
            continue

        # 파일 다운로드
        from app.services.rfp_parser import download_file_from_url
        file_bytes, content_type = await download_file_from_url(url)

        if not file_bytes:
            logger.warning(f"첨부파일 다운로드 실패: {att.get('name', url)}")
            stored_attachments.append(att)
            continue

        # Storage 저장
        storage_path = await _upload_attachment_to_storage(
            proposal_id or bid_no, att, file_bytes, content_type,
        )
        att_with_storage = {**att, "storage_path": storage_path, "size": len(file_bytes)}
        stored_attachments.append(att_with_storage)

        # 텍스트 추출 (첫 번째 문서형 파일에서만)
        if not auto_rfp_text and file_type in ("pdf", "hwp", "hwpx", "docx"):
            try:
                from app.services.rfp_parser import parse_rfp_from_url
                auto_rfp_text = await parse_rfp_from_url(url, file_type)
            except Exception:
                pass

    bid_detail.attachments = stored_attachments
    bid_detail.rfp_auto_text = auto_rfp_text

    # 3) interrupt: 사용자에게 RFP 파일 업로드 기회
    human_input = interrupt({
        "step": "rfp_fetch",
        "bid_detail": bid_detail.model_dump(),
        "has_auto_rfp": bool(auto_rfp_text),
        "attachments_count": len([a for a in stored_attachments if a.get("storage_path")]),
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


async def _upload_attachment_to_storage(
    proposal_or_bid_id: str,
    att: dict,
    file_bytes: bytes,
    content_type: str,
) -> str:
    """첨부파일을 Supabase Storage에 업로드. 실패 시 빈 문자열 반환."""
    from app.utils.supabase_client import get_async_client

    file_name = att.get("name", f"attachment_{att.get('index', 0)}")
    storage_path = f"{proposal_or_bid_id}/attachments/{file_name}"

    try:
        client = await get_async_client()
        await client.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        logger.info(f"첨부파일 Storage 저장: {storage_path}")
        return storage_path
    except Exception as e:
        logger.warning(f"첨부파일 Storage 저장 실패 ({file_name}): {e}")
        return ""
