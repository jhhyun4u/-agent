"""산출물 도메인 응답 스키마."""

from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    """GET /{proposal_id}/artifacts/{step} 응답."""

    step: str
    artifact: dict | list | None = None
    message: str | None = None
    error: str | None = None


class ArtifactSaveResponse(BaseModel):
    """PUT /{proposal_id}/artifacts/{step} 응답."""

    saved: bool
    step: str | None = None
    message: str | None = None
    error: str | None = None


class DiffMeta(BaseModel):
    change_source: str | None = None
    created_at: str | None = None
    created_by: str | None = None


class ArtifactDiffResponse(BaseModel):
    """GET /{proposal_id}/artifacts/{step}/diff 응답."""

    step: str | None = None
    old_version: str | None = None
    new_version: str | None = None
    old_content: dict | str | None = None
    new_content: dict | str | None = None
    old_meta: DiffMeta | None = None
    new_meta: DiffMeta | None = None
    diff: dict | None = None
    message: str | None = None


class SectionRegenerateResponse(BaseModel):
    """POST .../sections/{section_id}/regenerate 응답."""

    regenerated: bool
    section_id: str | None = None
    section_title: str | None = None
    message: str | None = None
    error: str | None = None


class AiAssistResponse(BaseModel):
    """POST /{proposal_id}/ai-assist 응답."""

    suggestion: str = ""
    explanation: str | None = None
    mode: str = ""
    original_length: int | None = None
    suggestion_length: int | None = None
    error: str | None = None


class ComplianceStats(BaseModel):
    total: int = 0
    met: int = 0
    unmet: int = 0
    unchecked: int = 0
    compliance_rate: float = 0.0


class ComplianceMatrixResponse(BaseModel):
    """GET /{proposal_id}/compliance 응답."""

    items: list[dict] = []
    stats: ComplianceStats = ComplianceStats()


class ComplianceCheckResponse(BaseModel):
    """POST /{proposal_id}/compliance/check 응답."""

    message: str
    checked: int = 0


class CostSheetDraftResponse(BaseModel):
    """GET /{proposal_id}/cost-sheet/draft 응답."""

    project_name: str | None = None
    client: str | None = None
    proposer_name: str | None = None
    cost_standard: str | None = None
    labor_breakdown: list[dict] = []
    labor_total: int = 0
    expense_items: list[dict] = []
    expense_total: int = 0
    overhead_rate: float = 0.0
    overhead_total: int = 0
    profit_rate: float = 0.0
    profit_total: int = 0
    total_cost: int = 0
    budget_narrative: list[str] = []
