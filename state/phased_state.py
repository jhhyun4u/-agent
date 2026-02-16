"""
Phase 기반 Supervisor State 정의 (v3.1.1)

PhasedSupervisorState는 기존 v3.0 SupervisorState를 Phase 경계 개념으로 확장.
각 Phase 완료 후 Artifact로 압축하여 다음 Phase LLM 프롬프트에 전달.
"""

from typing import TypedDict, Optional, Literal, Annotated, Any
from typing_extensions import NotRequired
from langgraph.graph.message import add_messages


class PhasedSupervisorState(TypedDict):
    """
    Phase 기반으로 재설계된 Supervisor State (v3.1.1)
    
    핵심 원칙:
    1. Phase별로 작업 영역 격리 (phase_working_state = {} 로 Phase 경계에서 비움)
    2. 각 Phase 산출물을 Artifact로 압축 (8K~15K 토큰)
    3. Phase 경계에서 컨텍스트 예산 관리 (최대 45K/Phase)
    4. HITL 게이트는 interrupt() 로 구현 (자동/조건부/필수)
    """

    # ── Phase 관리 ──
    current_phase: Literal[
        "phase_1_research",
        "phase_2_analysis",
        "phase_3_plan",
        "phase_4_implement",
        "phase_5_critique",
        "phase_5_revise",
        "phase_5_finalize",
        "completed",
        "error",
    ]

    # ── Phase Artifact 저장소 ──
    # 각 Phase 완료 시 생성, 다음 Phase의 LLM 프롬프트에 전달
    phase_artifact_1: NotRequired[Optional[dict]]  # Research 산출물 (~8K tok)
    phase_artifact_2: NotRequired[Optional[dict]]  # Analysis 산출물 (~10K tok)
    phase_artifact_3: NotRequired[Optional[dict]]  # Plan 산출물 (~12K tok)
    phase_artifact_4: NotRequired[Optional[dict]]  # Implement 산출물 (~15K tok)

    # ── 현재 Phase 작업 영역 ──
    # C-2: phase_working_state = {} 로 비워도 Python 메모리는 해방되지 않음.
    # 대용량 원본(RFP 200p 등)은 State가 아닌 MCP(document_store)에만 저장.
    # 이 필드의 비움은 "다음 Phase의 LLM 프롬프트에 이전 데이터를 넣지 않는다"는
    # 컨텍스트 격리 목적.
    phase_working_state: dict  # Phase 별 임시 작업 공간

    # ── v3.0 호환: Sub-agent 공유 저장소 (M-1 Fix) ──
    # Sub-agent가 최종 결과를 기록하는 전체 데이터의 원본.
    # Artifact는 "다음 Phase LLM 프롬프트용 압축본"이고,
    # proposal_state는 "전체 데이터의 원본"으로 두 가지가 공존.
    # Phase 경계에서 비우지 않음 (Sub-agent 인터페이스 호환).
    proposal_state: dict  # v3.0 ProposalState 호환

    # ── HITL 기록 ──
    hitl_decisions: list[dict]  # 각 게이트 판단 이력
    hitl_human_inputs: dict[int, dict]  # {gate_id: human_input}

    # ── Supervisor 메타 (v3.0 계승) ──
    workflow_plan: list[str]
    skipped_steps: list[dict]
    dynamic_decisions: list[dict]
    agent_status: dict[str, str]  # {agent_name: status}
    errors: list[dict]  # 에러 이력
    retry_count: dict[str, int]

    # ── 설정 ──
    express_mode: bool  # 긴급 모드 (HITL 일부 자동 통과)
    
    # ── LangGraph 메시지 ──
    messages: Annotated[list, add_messages]


def initialize_phased_supervisor_state(
    rfp_document_ref: Optional[str] = None,
    company_profile: Optional[str] = None,
    express_mode: bool = False,
) -> PhasedSupervisorState:
    """
    PhasedSupervisorState 초기화
    
    Args:
        rfp_document_ref: RFP 문서 참조 경로 (MCP document_store)
        company_profile: 회사 기본 정보
        express_mode: 긴급 모드 활성화 여부
    
    Returns:
        초기화된 PhasedSupervisorState
    """
    return {
        "current_phase": "phase_1_research",
        "phase_artifact_1": None,
        "phase_artifact_2": None,
        "phase_artifact_3": None,
        "phase_artifact_4": None,
        "phase_working_state": {
            "rfp_document_ref": rfp_document_ref,
            "company_profile": company_profile,
        },
        "proposal_state": {
            "rfp_document_ref": rfp_document_ref,
            "company_profile": company_profile,
        },
        "hitl_decisions": [],
        "hitl_human_inputs": {},
        "workflow_plan": [],
        "skipped_steps": [],
        "dynamic_decisions": [],
        "agent_status": {},
        "errors": [],
        "retry_count": {},
        "express_mode": express_mode,
        "messages": [],
    }
