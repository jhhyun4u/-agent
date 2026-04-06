"""
투찰 관리 API

POST /api/proposals/{id}/bid-submission     — 투찰 기록 (나라장터 실제 투찰)
POST /api/proposals/{id}/bid-submission/verify — 투찰 완료 확인 (팀장)
GET  /api/proposals/{id}/bid-submission     — 투찰 상태 조회
GET  /api/proposals/{id}/bid-price-history  — 가격 변경 이력
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, require_project_access, require_role
from app.api.response import ok
from app.exceptions import ConflictError, PropNotFoundError
from app.models.auth_schemas import CurrentUser

router = APIRouter(prefix="/api/proposals", tags=["bid-submission"])
logger = logging.getLogger(__name__)


class BidSubmissionRequest(BaseModel):
    """투찰 기록 요청."""
    submitted_price: int
    note: str = ""


@router.post("/{proposal_id}/bid-submission")
async def submit_bid(
    proposal_id: str,
    body: BidSubmissionRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """투찰 담당자가 나라장터에 실제 투찰한 가격을 기록."""
    from app.services.bid_handoff import get_bid_submission_status, record_bid_submission

    # 중복 투찰 방어
    status = await get_bid_submission_status(proposal_id)
    if not status:
        raise PropNotFoundError(proposal_id)
    current = status.get("bid_submission_status")
    if current in ("submitted", "verified"):
        raise ConflictError(
            f"이미 투찰 완료 상태입니다 (status={current}). 변경이 필요하면 관리자에게 문의하세요."
        )

    result = await record_bid_submission(
        proposal_id=proposal_id,
        submitted_price=body.submitted_price,
        user_id=user.id,
        user_name=user.name,
        note=body.note,
    )

    # 비동기 알림
    async def _notify():
        try:
            from app.services.notification_service import notify_bid_submitted
            await notify_bid_submitted(
                proposal_id=proposal_id,
                submitted_price=body.submitted_price,
            )
        except Exception as e:
            logger.warning(f"투찰 알림 실패: {e}")

    background_tasks.add_task(_notify)

    return ok(result)


@router.post("/{proposal_id}/bid-submission/verify")
async def verify_bid(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
    _role=Depends(require_role("lead")),
):
    """투찰 완료 확인 (팀장 이상)."""
    from app.services.bid_handoff import verify_bid_submission

    try:
        return ok(await verify_bid_submission(
            proposal_id=proposal_id,
            user_id=user.id,
            user_name=user.name,
        ))
    except ValueError:
        raise PropNotFoundError(proposal_id)


@router.get("/{proposal_id}/bid-submission")
async def get_bid_status(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """투찰 상태 조회."""
    from app.services.bid_handoff import get_bid_submission_status

    status = await get_bid_submission_status(proposal_id)
    if not status:
        raise PropNotFoundError(proposal_id)
    return ok(status)


@router.get("/{proposal_id}/bid-price-history")
async def get_price_history(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """가격 변경 이력 조회."""
    from app.services.bid_handoff import get_bid_price_history

    return ok(await get_bid_price_history(proposal_id))


# ── 3-Stream 비딩 워크스페이스 확장 ──


class BidPriceAdjustRequest(BaseModel):
    """워크플로 완료 후 가격 조정."""
    adjusted_price: int
    reason: str


@router.put("/{proposal_id}/bid-submission/adjust")
async def adjust_bid_price(
    proposal_id: str,
    body: BidPriceAdjustRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
    _role=Depends(require_role("lead")),
):
    """워크플로 완료 후 가격 조정 — 사유 필수."""
    from app.services.bidding_stream import update_bid_price_post_workflow

    return ok(await update_bid_price_post_workflow(
        proposal_id=proposal_id,
        adjusted_price=body.adjusted_price,
        reason=body.reason,
        user_id=user.id,
        user_name=user.name,
    ))


@router.get("/{proposal_id}/bidding-workspace")
async def get_bidding_workspace(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """통합 비딩 대시보드."""
    from app.services.bidding_stream import get_bidding_workspace

    return ok(await get_bidding_workspace(proposal_id))
