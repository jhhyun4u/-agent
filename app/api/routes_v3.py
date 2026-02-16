"""v3.0 Multi-Agent API 엔드포인트"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path

from app.models.schemas import ProjectInput
from app.services.session_manager import session_manager
from app.exceptions import SessionNotFoundError

# Optional: v3.0 호환성 (있으면 사용, 없으면 스킵)
try:
    from app.state import initialize_proposal_state, initialize_supervisor_state
except ImportError:
    initialize_proposal_state = None
    initialize_supervisor_state = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v3", tags=["v3.0"])


@router.post("/proposals/start")
async def start_proposal_v3(
    request: ProjectInput,
    rfp_file: Optional[UploadFile] = File(None),
):
    """
    제안서 작업 시작 (v3.0).

    - 직접 입력 또는 RFP 파일 업로드
    - Supervisor 오케스트레이터 초기화
    - 비동기 처리 시작
    """
    proposal_id = str(uuid.uuid4())[:12]

    try:
        # RFP 문서 준비
        rfp_content = ""
        if rfp_file:
            if not rfp_file.filename:
                raise HTTPException(status_code=400, detail="파일이 필요합니다.")

            suffix = Path(rfp_file.filename).suffix.lower()
            if suffix not in (".pdf", ".docx", ".hwp", ".txt"):
                raise HTTPException(
                    status_code=400,
                    detail=f"지원하지 않는 파일: {suffix}"
                )

            content = await rfp_file.read()
            rfp_content = content.decode("utf-8", errors="ignore")

        # 회사 프로필
        company_profile = {
            "name": "우리 회사",
            "id": "company-001",
            "capabilities": [],
        }

        # State 초기화
        proposal_state = initialize_proposal_state(
            proposal_id=proposal_id,
            rfp_document=rfp_content or request.project_scope,
            company_profile=company_profile,
        )

        supervisor_state = initialize_supervisor_state(proposal_state)

        # 세션 저장
        session_manager.create_session(
            proposal_id=proposal_id,
            initial_data={
                "supervisor_state": supervisor_state,
            },
            session_type="v3",
        )

        logger.info(f"✅ 제안서 작업 시작: {proposal_id}")

        return {
            "proposal_id": proposal_id,
            "status": "processing",
            "message": "제안서 작업을 시작했습니다.",
            "estimated_duration_minutes": 30,
        }

    except Exception as e:
        logger.error(f"❌ 제안서 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}/status")
async def get_proposal_status_v3(proposal_id: str):
    """제안서 진행 상태 조회"""
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    state = session["supervisor_state"]

    return {
        "proposal_id": proposal_id,
        "current_phase": state.get("current_phase", "unknown"),
        "workflow_plan": state.get("workflow_plan", []),
        "completed_agents": [
            k for k, v in state.get("agent_status", {}).items() if v == "completed"
        ],
        "error_count": len(state.get("errors", [])),
        "quality_score": state.get("proposal_state", {}).get("quality_score", 0),
        "revision_round": state.get("proposal_state", {}).get("revision_round", 0),
    }


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal_v3(proposal_id: str, feedback: Optional[str] = None):
    """HITL 게이트에서 최종 승인"""
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    state = session["supervisor_state"]
    phase = state.get("current_phase", "")

    if phase not in ["hitl_strategy", "hitl_personnel", "hitl_final"]:
        raise HTTPException(
            status_code=400,
            detail=f"현재 단계({phase})에서는 승인할 수 없습니다."
        )

    if feedback:
        state.get("messages", []).append({
            "role": "user",
            "content": feedback,
        })

    phase_map = {
        "hitl_strategy": "strategy_development",
        "hitl_personnel": "section_generation",
        "hitl_final": "document_finalization",
    }

    state["current_phase"] = phase_map.get(phase, phase)

    logger.info(f"✅ HITL 승인: {proposal_id}, {phase} → {state['current_phase']}")

    return {
        "proposal_id": proposal_id,
        "message": "승인되었습니다.",
        "next_phase": state.get("current_phase"),
    }


@router.get("/proposals/{proposal_id}/result")
async def get_proposal_result_v3(proposal_id: str):
    """최종 제안서 정보"""
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    state = session["supervisor_state"]

    return {
        "proposal_id": proposal_id,
        "current_phase": state.get("current_phase"),
        "status": "completed" if state.get("current_phase") == "completed" else "processing",
        "total_pages": state.get("proposal_state", {}).get("total_pages", 0),
        "quality_score": state.get("proposal_state", {}).get("quality_score", 0),
        "sections": len(state.get("proposal_state", {}).get("sections", {})),
    }


@router.delete("/proposals/{proposal_id}")
async def delete_proposal_v3(proposal_id: str):
    """제안서 작업 삭제"""
    try:
        session_manager.delete_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    logger.info(f"🗑️ 제안서 삭제: {proposal_id}")

    return {
        "proposal_id": proposal_id,
        "message": "제안서가 삭제되었습니다.",
    }


@router.get("/info")
async def get_system_info_v3():
    """시스템 정보"""
    return {
        "name": "용역 제안서 자동 생성 에이전트",
        "version": "3.0.0",
        "architecture": "Multi-Agent (Supervisor + 5 Sub-agents)",
        "components": {
            "supervisor": "오케스트레이터",
            "agents": [
                "RFP 분석",
                "전략 수립",
                "섹션 생성",
                "품질 관리",
                "문서 출력",
            ],
            "tools": "6개 공유 Tool + MCP 서버",
            "optimization": "Claude 토큰/비용 최적화",
        },
        "active_proposals": session_manager.get_session_count("v3"),
    }
