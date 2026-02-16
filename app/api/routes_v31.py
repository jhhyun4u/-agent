"""v3.1.1 Phase 기반 API 엔드포인트"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.services.session_manager import session_manager
from app.exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v3.1", tags=["v3.1"])


@router.post("/proposals/generate")
async def generate_proposal_v31(
    rfp_title: str,
    client_name: str,
    rfp_content: Optional[str] = None,
    rfp_file: Optional[UploadFile] = File(None),
    express_mode: bool = False,
):
    """
    v3.1.1 Phase 기반 제안서 자동 생성

    입력:
    - rfp_title: RFP 제목
    - client_name: 고객사 명
    - rfp_content: RFP 내용 (직접 입력)
    - rfp_file: RFP 파일 (선택)
    - express_mode: 빠른 모드 (HITL 자동 통과)

    출력:
    - proposal_id: 제안서 고유ID
    - status: 처리 상태
    - phases: 진행 단계
    """
    logger.info(f"[DEBUG] Function called: rfp_title={rfp_title}, client_name={client_name}")

    from graph import build_phased_supervisor_graph
    from state.phased_state import initialize_phased_supervisor_state

    logger.info(f"[DEBUG] Imports successful")

    proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # RFP 콘텐츠 준비
        rfp_text = ""
        if rfp_file:
            rfp_text = (await rfp_file.read()).decode("utf-8", errors="ignore")
        elif rfp_content:
            rfp_text = rfp_content
        else:
            raise HTTPException(status_code=400, detail="RFP 콘텐츠가 필요합니다.")

        # 회사 프로필 (Mock)
        company_profile = {
            "name": "제안사",
            "capabilities": ["클라우드", "AI/ML", "DevOps"],
            "experience_years": 10,
        }

        # State 초기화 (v3.1.1)
        state = initialize_phased_supervisor_state(
            rfp_document_ref=proposal_id,
            company_profile=company_profile,
            express_mode=express_mode,
        )

        # RFP 정보 저장
        state["proposal_state"] = {
            "rfp_title": rfp_title,
            "client_name": client_name,
            "rfp_content": rfp_text,
            "company_profile": company_profile,
        }

        # Phase Graph 빌드
        graph = build_phased_supervisor_graph()

        # 세션 저장
        session_manager.create_session(
            proposal_id=proposal_id,
            initial_data={
                "state": state,
                "graph": graph,
                "rfp_title": rfp_title,
                "client_name": client_name,
                "phases_completed": 0,
            },
            session_type="v3.1",
        )

        logger.info(f"✅ v3.1.1 제안서 생성 시작: {proposal_id}")
        logger.info(f"   RFP: {rfp_title} ({client_name})")
        logger.info(f"   Express Mode: {express_mode}")

        return {
            "proposal_id": proposal_id,
            "status": "initialized",
            "message": "Phase 기반 제안서 생성을 시작했습니다.",
            "rfp_title": rfp_title,
            "client_name": client_name,
            "estimated_duration_seconds": 120,
            "phases": ["research", "analysis", "plan", "implement", "quality"],
        }

    except Exception as e:
        logger.error(f"❌ v3.1.1 제안서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}/status")
async def get_proposal_status_v31(proposal_id: str):
    """
    v3.1.1 제안서 진행 상태 조회

    반환:
    - status: 전체 상태 (initialized, processing, completed, failed)
    - current_phase: 현재 진행 중인 Phase
    - phases_completed: 완료된 Phase 수
    - messages: 처리 로그
    """
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    state = session.get("state", {})

    return {
        "proposal_id": proposal_id,
        "rfp_title": session.get("rfp_title", ""),
        "client_name": session.get("client_name", ""),
        "status": session.get("status", "unknown"),
        "current_phase": state.get("current_phase", "pending"),
        "phases_completed": session.get("phases_completed", 0),
        "created_at": session.get("created_at").isoformat(),
        "messages": state.get("messages", [])[-5:],  # 최근 5개 메시지
    }


@router.get("/proposals/{proposal_id}/result")
async def get_proposal_result_v31(proposal_id: str):
    """
    v3.1.1 제안서 최종 결과 조회

    반환:
    - artifacts: Phase별 산출물
    - quality_score: 최종 품질 점수
    - document_path: 생성된 문서 경로
    """
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    state = session.get("state", {})

    # 산출물 수집
    artifacts = {
        "phase_1_research": state.get("phase_artifact_1", {}),
        "phase_2_analysis": state.get("phase_artifact_2", {}),
        "phase_3_plan": state.get("phase_artifact_3", {}),
        "phase_4_implement": state.get("phase_artifact_4", {}),
    }

    working_state = state.get("phase_working_state", {})

    return {
        "proposal_id": proposal_id,
        "status": session.get("status", "unknown"),
        "rfp_title": session.get("rfp_title", ""),
        "client_name": session.get("client_name", ""),
        "phases_completed": session.get("phases_completed", 0),
        "artifacts": artifacts,
        "quality_score": working_state.get("quality_score", 0),
        "document_path": working_state.get("document_store_path", ""),
        "executive_summary": working_state.get("executive_summary", ""),
    }


@router.post("/proposals/{proposal_id}/execute")
async def execute_proposal_phase_v31(proposal_id: str, auto_run: bool = False):
    """
    v3.1.1 제안서 Phase 실행

    매개변수:
    - auto_run: True면 모든 Phase 자동 실행, False면 수동 제어
    """
    try:
        session = session_manager.get_session(proposal_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))

    try:
        state = session["state"]

        logger.info(f"🚀 Phase 실행 시작: {proposal_id} (auto_run={auto_run})")

        if auto_run:
            # 모든 Phase 자동 실행 (Mock 데이터 사용)
            phase_names = ["research", "analysis", "plan", "implement", "quality"]

            for i, phase in enumerate(phase_names, start=1):
                logger.info(f"  → Phase {i}: {phase}...")
                state["current_phase"] = f"phase_{i}_{phase}"

            session_manager.update_session(
                proposal_id,
                {"status": "completed", "phases_completed": 5}
            )

            logger.info(f"✅ 모든 Phase 완료: {proposal_id}")

            return {
                "proposal_id": proposal_id,
                "status": "completed",
                "phases_completed": 5,
                "message": "모든 Phase가 완료되었습니다.",
            }
        else:
            # 다음 Phase 실행
            current_phase_num = session.get("phases_completed", 0)
            next_phase_num = current_phase_num + 1

            if next_phase_num > 5:
                return {
                    "proposal_id": proposal_id,
                    "status": "completed",
                    "message": "모든 Phase가 이미 완료되었습니다.",
                }

            phase_names = ["research", "analysis", "plan", "implement", "quality"]
            next_phase = phase_names[next_phase_num - 1]

            logger.info(f"  → Phase {next_phase_num}: {next_phase}...")

            state["current_phase"] = f"phase_{next_phase_num}_{next_phase}"
            session_manager.update_session(
                proposal_id,
                {"phases_completed": next_phase_num}
            )

            return {
                "proposal_id": proposal_id,
                "status": "processing",
                "current_phase": next_phase,
                "phases_completed": next_phase_num,
                "message": f"Phase {next_phase_num}이 실행되었습니다.",
            }

    except Exception as e:
        logger.error(f"❌ Phase 실행 실패: {e}")
        session_manager.update_session(proposal_id, {"status": "failed"})
        raise HTTPException(status_code=500, detail=str(e))
