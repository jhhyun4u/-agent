"""워크플로 도메인 응답 스키마."""

from pydantic import BaseModel


class TokenSummary(BaseModel):
    total_cost_usd: float = 0.0
    nodes_tracked: int = 0


class TokenUsageByNode(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class TokenUsageTotal(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    nodes_executed: int = 0


class WorkflowStartResponse(BaseModel):
    """POST /{proposal_id}/start 응답."""

    proposal_id: str
    status: str = "running"
    current_step: str = ""
    interrupted: bool = False
    streams_status: dict | None = None


class WorkflowStateResponse(BaseModel):
    """GET /{proposal_id}/state 응답."""

    proposal_id: str
    current_step: str = ""
    positioning: str | None = None
    approval: dict = {}
    has_pending_interrupt: bool = False
    next_nodes: list[str] = []
    token_summary: TokenSummary = TokenSummary()
    streams_status: dict | None = None
    dynamic_sections: list[str] = []
    error: str | None = None


class WorkflowResumeResponse(BaseModel):
    """POST /{proposal_id}/resume 응답."""

    proposal_id: str
    current_step: str = ""
    interrupted: bool = False
    streams_status: dict | None = None


class WorkflowHistoryStep(BaseModel):
    step: str
    next: list[str] = []
    config: dict = {}


class WorkflowHistoryResponse(BaseModel):
    """GET /{proposal_id}/history 응답."""

    proposal_id: str
    history: list[WorkflowHistoryStep] = []
    error: str | None = None


class TokenUsageResponse(BaseModel):
    """GET /{proposal_id}/token-usage 응답."""

    proposal_id: str
    by_node: dict[str, TokenUsageByNode] = {}
    total: TokenUsageTotal = TokenUsageTotal()


class SectionLockResponse(BaseModel):
    """POST /{proposal_id}/sections/{section_id}/lock 응답."""

    locked: bool = True
    section_id: str = ""
    locked_by: str = ""
    locked_at: str = ""
    expires_at: str = ""


class SectionUnlockResponse(BaseModel):
    released: bool


class AiStatusResponse(BaseModel):
    """GET /{proposal_id}/ai-status 응답."""

    proposal_id: str
    status: str = "idle"
    step: str | None = None
    progress: float | None = None
    message: str | None = None
    started_at: str | None = None
    heartbeat_at: str | None = None


class AiActionResponse(BaseModel):
    """POST ai-abort / ai-retry 응답."""

    proposal_id: str
    status: str | None = None
    step: str | None = None
    retried_step: str | None = None
    current_step: str | None = None
    message: str | None = None
    error: str | None = None


class GotoResponse(BaseModel):
    """POST /{proposal_id}/goto/{step} 응답."""

    success: bool
    proposal_id: str | None = None
    restored_step: str | None = None
    message: str | None = None
    error: str | None = None


class ImpactResponse(BaseModel):
    """GET /{proposal_id}/impact/{step} 응답."""

    step: str
    step_number: int | None = None
    downstream_nodes: list[str] = []
    downstream_count: int = 0
    affected_steps: list[int] = []
    message: str | None = None
    error: str | None = None


# ── Phase 2: Unified State System Responses ──


class TimelineEntry(BaseModel):
    """proposal_timelines 테이블 항목 (상태 전환 기록)."""

    id: str
    proposal_id: str
    event_type: str  # 'status_change', 'phase_change', 'approval', 'review', 'ai_status'
    from_status: str | None = None
    to_status: str | None = None
    from_phase: str | None = None
    to_phase: str | None = None
    triggered_by: str | None = None
    actor_type: str | None = None  # 'user', 'system', 'ai', 'workflow'
    trigger_reason: str | None = None
    notes: str | None = None
    metadata: dict | None = None
    created_at: str


class EnhancedWorkflowStateResponse(BaseModel):
    """Enhanced GET /{proposal_id}/state 응답 (3-layer state)."""

    proposal_id: str
    # Layer 1: Business Status (proposals.status)
    business_status: str = ""
    # Layer 2: Workflow Phase (proposals.current_phase)
    workflow_phase: str = ""
    # Layer 3: AI Runtime Status (latest ai_task_logs entry)
    ai_status: dict = {}
    # Timestamps
    timestamps: dict = {
        "created_at": None,
        "started_at": None,
        "last_activity_at": None,
        "completed_at": None,
    }
    # Recent transitions
    recent_transitions: list[TimelineEntry] = []
    # Legacy fields (backward compatibility)
    current_step: str = ""
    positioning: str | None = None
    approval: dict = {}
    has_pending_interrupt: bool = False
    next_nodes: list[str] = []
    token_summary: TokenSummary = TokenSummary()
    streams_status: dict | None = None
    error: str | None = None


class StateHistoryResponse(BaseModel):
    """GET /{proposal_id}/state-history 응답 (전체 상태 전환 기록)."""

    proposal_id: str
    total_events: int = 0
    history: list[TimelineEntry] = []
    pagination: dict = {
        "limit": 50,
        "offset": 0,
        "has_more": False,
    }
    error: str | None = None
