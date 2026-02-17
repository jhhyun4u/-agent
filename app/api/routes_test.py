"""테스트 엔드포인트"""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test", tags=["test"])


@router.get("/ping")
async def ping():
    """간단한 핑 테스트"""
    return {"message": "pong"}


@router.post("/initialize-state")
async def test_initialize_state():
    """initialize_phased_supervisor_state 직접 테스트"""
    logger.info("=== TEST: initialize_phased_supervisor_state ===")

    try:
        from state.phased_state import initialize_phased_supervisor_state

        logger.info("Import successful")

        state = initialize_phased_supervisor_state(
            rfp_document_ref="test_123",
            company_profile={"name": "Test Company"},
            express_mode=False
        )

        logger.info(f"State created: {list(state.keys())[:5]}")

        return {
            "success": True,
            "message": "State initialized successfully",
            "state_keys": list(state.keys())
        }
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
