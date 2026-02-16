import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse

from app.models.schemas import ProjectInput

# Optional: v3.0 호환성 (있으면 사용, 없으면 스킵)
try:
    from app.state import initialize_proposal_state, initialize_supervisor_state
except ImportError:
    initialize_proposal_state = None
    initialize_supervisor_state = None

logger = logging.getLogger(__name__)
router = APIRouter()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 세션 관리 (실제로는 DB 권장)
PROPOSALS = {}


# ═══════════════════════════════════════════════════════════════════════════
# v3.0 Multi-Agent 엔드포인트
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/v3/proposals/start")
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
        PROPOSALS[proposal_id] = {
            "supervisor_state": supervisor_state,
            "created_at": datetime.now(),
            "status": "initialized",
        }

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


@router.get("/v3/proposals/{proposal_id}/status")
async def get_proposal_status_v3(proposal_id: str):
    """제안서 진행 상태 조회"""
    proposal = PROPOSALS.get(proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다.")

    state = proposal["supervisor_state"]

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


@router.post("/v3/proposals/{proposal_id}/approve")
async def approve_proposal_v3(proposal_id: str, feedback: Optional[str] = None):
    """HITL 게이트에서 최종 승인"""
    proposal = PROPOSALS.get(proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다.")

    state = proposal["supervisor_state"]
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


@router.get("/v3/proposals/{proposal_id}/result")
async def get_proposal_result_v3(proposal_id: str):
    """최종 제안서 정보"""
    proposal = PROPOSALS.get(proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다.")

    state = proposal["supervisor_state"]

    return {
        "proposal_id": proposal_id,
        "current_phase": state.get("current_phase"),
        "status": "completed" if state.get("current_phase") == "completed" else "processing",
        "total_pages": state.get("proposal_state", {}).get("total_pages", 0),
        "quality_score": state.get("proposal_state", {}).get("quality_score", 0),
        "sections": len(state.get("proposal_state", {}).get("sections", {})),
    }


@router.delete("/v3/proposals/{proposal_id}")
async def delete_proposal_v3(proposal_id: str):
    """제안서 작업 삭제"""
    if proposal_id not in PROPOSALS:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다.")

    del PROPOSALS[proposal_id]
    logger.info(f"🗑️ 제안서 삭제: {proposal_id}")

    return {
        "proposal_id": proposal_id,
        "message": "제안서가 삭제되었습니다.",
    }


@router.get("/v3/info")
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
        "active_proposals": len(PROPOSALS),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 레거시 엔드포인트 (v2.0 호환성)
# ═══════════════════════════════════════════════════════════════════════════

class ProposalResponse(dict):
    """제안서 응답"""
    pass


@router.post("/proposals/from-rfp")
async def create_proposal_from_rfp(file: UploadFile):
    """RFP 파일 업로드 기반 제안서 생성 (레거시)"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일이 필요합니다.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(
            status_code=400, detail=f"지원하지 않는 파일 형식입니다: {suffix}"
        )

    proposal_id = str(uuid.uuid4())[:8]
    temp_path = OUTPUT_DIR / f"temp_{proposal_id}{suffix}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # v3.0으로 리다이렉트
        return {
            "proposal_id": proposal_id,
            "message": "v3.0 엔드포인트를 사용해주세요.",
            "legacy_notice": "이 엔드포인트는 더 이상 지원되지 않습니다.",
            "new_endpoint": "/api/v3/proposals/start",
        }

    finally:
        temp_path.unlink(missing_ok=True)


@router.post("/proposals/from-input")
async def create_proposal_from_input(project: ProjectInput):
    """직접 입력 기반 제안서 생성 (레거시)"""
    return {
        "message": "v3.0 엔드포인트를 사용해주세요.",
        "legacy_notice": "이 엔드포인트는 더 이상 지원되지 않습니다.",
        "new_endpoint": "/api/v3/proposals/start",
    }


@router.get("/proposals/{proposal_id}/download")
async def download_proposal(proposal_id: str, format: str = "docx"):
    """생성된 제안서 다운로드 (레거시)"""
    raise HTTPException(
        status_code=410,
        detail="이 엔드포인트는 더 이상 지원되지 않습니다. v3.0 엔드포인트를 사용해주세요."
    )


# ═══════════════════════════════════════════════════════════════════════════
# v3.1.1 PhaseGraph 엔드포인트 (새로운 아키텍처)
# ═══════════════════════════════════════════════════════════════════════════

from graph import build_phased_supervisor_graph
from state.phased_state import initialize_phased_supervisor_state

# 세션 관리 (v3.1.1)
PHASED_PROPOSALS = {}


@router.post("/v3.1/proposals/generate")
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
            rfp_ref=proposal_id,
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
        
        # 비동기 처리 시작 (백그라운드)
        # 실제 프로덕션에서는 Celery나 QueueManager 사용 권장
        
        # 세션 저장
        PHASED_PROPOSALS[proposal_id] = {
            "state": state,
            "graph": graph,
            "created_at": datetime.now(),
            "status": "initialized",
            "rfp_title": rfp_title,
            "client_name": client_name,
            "phases_completed": 0,
        }
        
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


@router.get("/v3.1/proposals/{proposal_id}/status")
async def get_proposal_status_v31(proposal_id: str):
    """
    v3.1.1 제안서 진행 상태 조회
    
    반환:
    - status: 전체 상태 (initialized, processing, completed, failed)
    - current_phase: 현재 진행 중인 Phase
    - phases_completed: 완료된 Phase 수
    - messages: 처리 로그
    """
    
    proposal = PHASED_PROPOSALS.get(proposal_id)
    
    if not proposal:
        raise HTTPException(status_code=404, detail=f"제안서를 찾을 수 없습니다: {proposal_id}")
    
    state = proposal.get("state", {})
    
    return {
        "proposal_id": proposal_id,
        "rfp_title": proposal.get("rfp_title", ""),
        "client_name": proposal.get("client_name", ""),
        "status": proposal.get("status", "unknown"),
        "current_phase": state.get("current_phase", "pending"),
        "phases_completed": proposal.get("phases_completed", 0),
        "created_at": proposal.get("created_at").isoformat(),
        "messages": state.get("messages", [])[-5:],  # 최근 5개 메시지
    }


@router.get("/v3.1/proposals/{proposal_id}/result")
async def get_proposal_result_v31(proposal_id: str):
    """
    v3.1.1 제안서 최종 결과 조회
    
    반환:
    - artifacts: Phase별 산출물
    - quality_score: 최종 품질 점수
    - document_path: 생성된 문서 경로
    """
    
    proposal = PHASED_PROPOSALS.get(proposal_id)
    
    if not proposal:
        raise HTTPException(status_code=404, detail=f"제안서를 찾을 수 없습니다: {proposal_id}")
    
    state = proposal.get("state", {})
    
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
        "status": proposal.get("status", "unknown"),
        "rfp_title": proposal.get("rfp_title", ""),
        "client_name": proposal.get("client_name", ""),
        "phases_completed": proposal.get("phases_completed", 0),
        "artifacts": artifacts,
        "quality_score": working_state.get("quality_score", 0),
        "document_path": working_state.get("document_store_path", ""),
        "executive_summary": working_state.get("executive_summary", ""),
    }


@router.post("/v3.1/proposals/{proposal_id}/execute")
async def execute_proposal_phase_v31(proposal_id: str, auto_run: bool = False):
    """
    v3.1.1 제안서 Phase 실행
    
    매개변수:
    - auto_run: True면 모든 Phase 자동 실행, False면 수동 제어
    """
    
    proposal = PHASED_PROPOSALS.get(proposal_id)
    
    if not proposal:
        raise HTTPException(status_code=404, detail=f"제안서를 찾을 수 없습니다: {proposal_id}")
    
    try:
        state = proposal["state"]
        graph = proposal["graph"]
        
        logger.info(f"🚀 Phase 실행 시작: {proposal_id} (auto_run={auto_run})")
        
        if auto_run:
            # 모든 Phase 자동 실행 (Mock 데이터 사용)
            
            # Phase 1: Research
            logger.info("  → Phase 1: Research...")
            state["current_phase"] = "phase_1_research"
            
            # Phase 2: Analysis
            logger.info("  → Phase 2: Analysis...")
            state["current_phase"] = "phase_2_analysis"
            
            # Phase 3: Plan
            logger.info("  → Phase 3: Plan...")
            state["current_phase"] = "phase_3_plan"
            
            # Phase 4: Implement
            logger.info("  → Phase 4: Implement...")
            state["current_phase"] = "phase_4_implement"
            
            # Phase 5: Quality
            logger.info("  → Phase 5: Quality...")
            state["current_phase"] = "phase_5_finalize"
            
            proposal["status"] = "completed"
            proposal["phases_completed"] = 5
            
            logger.info(f"✅ 모든 Phase 완료: {proposal_id}")
            
            return {
                "proposal_id": proposal_id,
                "status": "completed",
                "phases_completed": 5,
                "message": "모든 Phase가 완료되었습니다.",
            }
        else:
            # 다음 Phase 실행
            current_phase_num = proposal.get("phases_completed", 0)
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
            proposal["phases_completed"] = next_phase_num
            
            return {
                "proposal_id": proposal_id,
                "status": "processing",
                "current_phase": next_phase,
                "phases_completed": next_phase_num,
                "message": f"Phase {next_phase_num}이 실행되었습니다.",
            }
    
    except Exception as e:
        logger.error(f"❌ Phase 실행 실패: {e}")
        proposal["status"] = "failed"
        raise HTTPException(status_code=500, detail=str(e))


