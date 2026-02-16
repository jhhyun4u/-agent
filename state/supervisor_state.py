"""
Supervisor 오케스트레이터 상태 스키마.

v3.0: Multi-Agent 아키텍처
- ProposalState (v2.0 호환): 제안서 전체 상태
- SupervisorState: Supervisor 전용 메타 필드
"""

from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from .proposal_state import ProposalState


class SupervisorState(TypedDict):
    """Supervisor 에이전트의 완전한 상태"""

    # ═══ 제안서 데이터 (v2.0 호환) ═══
    proposal_state: ProposalState
    """전체 제안서 상태. Sub-agent 결과는 여기에 병합됨."""

    # ═══ Supervisor 메타 필드 ═══
    current_phase: Literal[
        "initialization",       # 초기화
        "rfp_analysis",         # RFP 분석 진행 중
        "strategy_development", # 전략 수립 진행 중
        "hitl_strategy",        # 전략 HITL 대기
        "section_generation",   # 섹션 생성 진행 중
        "quality_review",       # 품질 검토 루프
        "hitl_final",           # 최종 HITL 대기
        "document_finalization",# 문서 최종화
        "completed",            # 완료
        "error",                # 에러 상태
    ]

    # ═══ 동적 워크플로우 ═══
    workflow_plan: list[str]
    """Supervisor가 결정한 실행 계획 (단계 리스트)"""

    skipped_steps: list[dict]
    """건너뛴 단계 및 사유 [{step, reason}]"""

    dynamic_decisions: list[dict]
    """동적 판단 이력 [{decision, rationale, timestamp}]"""

    # ═══ Sub-agent 상태 추적 ═══
    agent_status: dict[str, Literal["pending", "running", "completed", "failed"]]
    """Sub-agent 상태 {agent_name: status}"""

    agent_outputs: dict[str, dict]
    """Sub-agent 출력 결과 {agent_name: output_dict}"""

    # ═══ 에러 관리 ═══
    errors: list[dict]
    """발생한 에러 [{node, error_type, message, timestamp, fatal}]"""

    retry_count: dict[str, int]
    """Sub-agent별 재시도 횟수 {agent_name: count}"""

    # ═══ 메시지 히스토리 ═══
    messages: Annotated[list[dict], "add_messages"]
    """에이전트 간 메시지 히스토리 (LangChain add_messages 패턴)"""

    # ═══ 모니터링 ═══
    checkpoints: list[dict]
    """체크포인트 정보 (시간, 단계, 상태)"""


class WorkflowPlan(BaseModel):
    """Supervisor의 워크플로우 계획"""

    steps: list[str] = Field(description="실행할 단계 순서")
    rationale: str = Field(description="계획 수립의 근거")
    skip_reasons: dict[str, str] = Field(
        default_factory=dict,
        description="건너뛰는 단계 {step: reason}"
    )


class AgentStatusUpdate(BaseModel):
    """Sub-agent 상태 업데이트"""

    agent_name: str
    status: Literal["pending", "running", "completed", "failed"]
    output: dict | None = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class DynamicDecision(BaseModel):
    """Supervisor의 동적 판단 기록"""

    decision: str = Field(description="판단 항목")
    rationale: str = Field(description="판단 근거")
    phase: str = Field(description="판단 시점의 phase")
    timestamp: datetime = Field(default_factory=datetime.now)


def initialize_supervisor_state(proposal_state: ProposalState) -> SupervisorState:
    """Supervisor State 초기화"""
    return {
        "proposal_state": proposal_state,
        "current_phase": "initialization",
        "workflow_plan": [],
        "skipped_steps": [],
        "dynamic_decisions": [],
        "agent_status": {
            "rfp_analysis": "pending",
            "strategy": "pending",
            "section_generation": "pending",
            "quality": "pending",
            "document": "pending",
        },
        "agent_outputs": {},
        "errors": [],
        "retry_count": {},
        "messages": [],
        "checkpoints": [],
    }
