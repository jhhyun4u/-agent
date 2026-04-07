# Design: pydantic-schema-refinement

> Plan 참조: `docs/01-plan/features/pydantic-schema-refinement.plan.md`

## 1. 설계 원칙

1. **기존 API 계약 유지**: `return {dict}` 키 구조를 그대로 Pydantic 모델로 옮긴다. 프론트엔드 Breaking change 금지.
2. **점진 적용**: Phase A→B→C 순서, 각 Phase 완료 시 서버 기동 + 빌드 검증.
3. **Generic 재사용**: 반복 패턴은 `Generic[T]` 공통 모델로 흡수.
4. **Supabase dict 호환**: DB에서 반환하는 row dict를 `model_validate(row)` 또는 `**row`로 변환.
5. **Optional 표기 통일**: Python 3.11+ `X | None` 스타일. `Optional` import 제거.

---

## 2. 파일 구조

```
app/models/
├── __init__.py              # 기존 (변경 없음)
├── common.py                # [신규] 공통 응답 모델 (Generic)
├── types.py                 # [신규] 공유 Literal 타입 모듈
├── auth_schemas.py          # [신규] CurrentUser + 인증 응답
├── proposal_schemas.py      # [신규] 제안서 도메인 응답
├── workflow_schemas.py      # [신규] 워크플로 도메인 응답
├── artifact_schemas.py      # [신규] 산출물 도메인 응답
├── notification_schemas.py  # [신규] 알림 도메인 응답
├── analytics_schemas.py     # [신규] 분석 도메인 응답
├── performance_schemas.py   # [신규] 성과 도메인 응답
├── admin_schemas.py         # [신규] 관리자 도메인 응답
├── schemas.py               # [수정] Literal 타입 참조 전환
├── user_schemas.py          # [수정] Optional→|None, Literal 전환
├── bid_schemas.py           # [수정] RecommendationsResponse 정형화
├── phase_schemas.py         # [수정] datetime 통일
├── stream_schemas.py        # (변경 없음, 이미 양호)
└── bidding/pricing/models.py# [수정] datetime.utcnow → datetime.now(UTC)
```

---

## 3. Phase A — 기반 인프라

### 3-1. `app/models/types.py` (공유 Literal 타입)

```python
"""공유 Literal 타입 — 여러 스키마에서 import하여 사용."""

from typing import Literal

# ── 사용자/조직 ──
UserRole = Literal["member", "lead", "director", "executive", "admin"]
UserStatus = Literal["active", "inactive", "suspended"]

# ── 제안서 ──
ProposalStatus = Literal[
    "initialized", "processing", "searching", "analyzing", "strategizing",
    "submitted", "presented", "won", "lost", "no_go", "on_hold",
    "expired", "abandoned", "retrospect", "completed",
]
ProposalResult = Literal["won", "lost", "void"]

# ── 범위/필터 ──
ScopeType = Literal["team", "division", "org"]
ImpactLevel = Literal["high", "medium", "low"]
Granularity = Literal["monthly", "quarterly", "yearly"]

# ── 교훈 ──
LessonCategory = Literal["strategy", "pricing", "team", "technical", "process", "other"]

# ── Q&A ──
QACategory = Literal[
    "technical", "management", "pricing", "experience", "team", "general"
]
EvaluatorReaction = Literal["positive", "neutral", "negative"]
```

### 3-2. `app/models/common.py` (공통 응답 모델)

```python
"""공통 재사용 응답 모델."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StatusResponse(BaseModel):
    """단순 상태 응답. return {"status": "ok"} 대체."""
    status: Literal["ok", "error"] = "ok"
    message: str = ""


class ItemsResponse(BaseModel, Generic[T]):
    """목록 응답 (페이지네이션 없음). return {"items": [...], "total": N} 대체."""
    items: list[T]
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 목록 응답."""
    items: list[T]
    total: int
    page: int = 1
    per_page: int = 20


class DeleteResponse(BaseModel):
    """삭제 확인 응답."""
    status: Literal["ok"] = "ok"
    deleted_id: str
```

### 3-3. `app/models/auth_schemas.py` (CurrentUser)

```python
"""인증 관련 스키마."""

from datetime import datetime

from pydantic import BaseModel

from app.models.types import UserRole, UserStatus


class CurrentUser(BaseModel):
    """JWT 인증 후 반환되는 사용자 정보.

    deps.py의 get_current_user() 반환 타입.
    DB users 테이블의 SELECT * 결과와 호환.
    """
    id: str
    email: str
    name: str
    role: UserRole
    org_id: str | None = None
    team_id: str | None = None
    division_id: str | None = None
    status: UserStatus = "active"
    azure_ad_oid: str | None = None
    notification_settings: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AuthMessageResponse(BaseModel):
    """인증 관련 메시지 응답."""
    message: str
```

### 3-4. `deps.py` 변경 사항

```python
# Before
async def get_current_user(...) -> dict:
    ...
    return profile.data          # dict

# After
from app.models.auth_schemas import CurrentUser

async def get_current_user(...) -> CurrentUser:
    ...
    return CurrentUser(**profile.data)  # 모델 인스턴스

# _get_dev_user도 동일하게 CurrentUser 반환
async def _get_dev_user() -> CurrentUser:
    ...
    return CurrentUser(id=..., email=..., ...)

# require_role, require_project_access 내부의
# user["role"] → user.role
# user["id"]   → user.id
# user.get("team_id") → user.team_id
```

**전환 시 전수 검색 대상 패턴:**
- `user["` → `user.` (dict 인덱싱 → 속성 접근)
- `user.get("` → `user.` (get 호출 → 속성 접근, None 기본값은 모델에서 처리)
- `user[` → 동적 키 접근 확인

### 3-5. `user_schemas.py` 수정 사항

```python
# Before
from typing import Optional
role: str = Field(default="member", pattern="^(member|lead|...)$")
team_id: Optional[str] = None

# After
from app.models.types import UserRole
role: UserRole = "member"
team_id: str | None = None
```

변경 목록:
- `Optional[X]` → `X | None` (전체 파일)
- `UserCreate.role`, `UserUpdate.role` → `UserRole` Literal 타입
- `ParticipantAdd.role_in_project` → `Literal["member", "section_lead"]`
- `import Optional` 제거

### 3-6. `schemas.py` 수정 사항

- `QA_CATEGORIES` → `from app.models.types import QACategory`로 대체
- `QARecordResponse.category: str` → `QACategory`
- `QARecordResponse.evaluator_reaction: str | None` → `EvaluatorReaction | None`
- `QARecordResponse.created_at: str` → `datetime`
- `QASearchResult` 동일 적용

### 3-7. `bid_schemas.py` 수정 — `RecommendationsResponse` 정형화

```python
# Before
class RecommendationsResponse(BaseModel):
    data: dict  # {recommended: [...], excluded: [...]}
    meta: RecommendationsMeta

# After
class RecommendationsData(BaseModel):
    recommended: list[RecommendedBid]
    excluded: list[ExcludedBid]

class RecommendationsResponse(BaseModel):
    data: RecommendationsData
    meta: RecommendationsMeta
```

### 3-8. `phase_schemas.py` / `pricing/models.py` datetime 통일

```python
# Before
created_at: datetime = Field(default_factory=datetime.now)     # phase_schemas
created_at: datetime = Field(default_factory=datetime.utcnow)  # pricing/models

# After (둘 다)
from datetime import UTC
created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

---

## 4. Phase B — 도메인 Response 모델

### 4-1. `app/models/proposal_schemas.py`

```python
"""제안서 도메인 응답 스키마."""

from datetime import datetime
from pydantic import BaseModel
from app.models.types import ProposalStatus, ProposalResult, ImpactLevel, LessonCategory


class ProposalListItem(BaseModel):
    """GET /api/proposals 목록 아이템."""
    id: str
    title: str | None = None
    status: ProposalStatus
    owner_id: str | None = None
    team_id: str | None = None
    rfp_filename: str | None = None
    current_phase: str | None = None
    bid_amount: int | None = None
    created_at: datetime
    updated_at: datetime


class ProposalDetail(ProposalListItem):
    """GET /api/proposals/{id} 상세."""
    division_id: str | None = None
    org_id: str | None = None
    rfp_content: str | None = None
    rfp_content_truncated: bool = False
    phases_completed: int = 0
    failed_phase: str | None = None
    storage_path_docx: str | None = None
    storage_path_pptx: str | None = None
    storage_path_hwpx: str | None = None
    storage_path_rfp: str | None = None
    win_result: str | None = None
    notes: str | None = None


class ProposalCreateResponse(BaseModel):
    """POST /api/proposals 응답."""
    proposal_id: str
    title: str | None = None
    status: str = "initialized"
    entry_point: str
    bid_no: str | None = None
    mode: str | None = None


class ProposalResultResponse(BaseModel):
    """GET /api/proposals/{id}/result 응답."""
    id: str
    proposal_id: str
    result: ProposalResult
    final_price: int | None = None
    competitor_count: int | None = None
    ranking: int | None = None
    tech_score: float | None = None
    price_score: float | None = None
    total_score: float | None = None
    feedback_notes: str | None = None
    won_by: str | None = None
    created_at: datetime | None = None


class LessonResponse(BaseModel):
    """교훈 응답."""
    id: str
    proposal_id: str
    category: LessonCategory
    title: str
    description: str
    impact: ImpactLevel
    action_items: list[str] = []
    applicable_domains: list[str] = []
    created_at: datetime | None = None
    created_by: str | None = None
```

### 4-2. `app/models/workflow_schemas.py`

```python
"""워크플로 도메인 응답 스키마."""

from datetime import datetime
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
    current_step: str
    interrupted: bool = False
    streams_status: dict | None = None


class WorkflowStateResponse(BaseModel):
    """GET /{proposal_id}/state 응답."""
    proposal_id: str
    current_step: str
    positioning: str | None = None
    approval: dict = {}
    has_pending_interrupt: bool = False
    next_nodes: list[str] = []
    token_summary: TokenSummary = TokenSummary()
    streams_status: dict | None = None
    error: str | None = None


class WorkflowResumeResponse(BaseModel):
    """POST /{proposal_id}/resume 응답."""
    proposal_id: str
    current_step: str
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
    section_id: str
    locked_by: str
    locked_at: str
    expires_at: str


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
```

### 4-3. `app/models/artifact_schemas.py`

```python
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
    mode: str
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
```

### 4-4. `app/models/notification_schemas.py`

```python
"""알림 도메인 응답 스키마."""

from datetime import datetime
from pydantic import BaseModel


class NotificationItem(BaseModel):
    """알림 단건."""
    id: str
    user_id: str
    type: str
    title: str
    body: str | None = None
    link: str | None = None
    is_read: bool = False
    created_at: datetime


class NotificationListResponse(BaseModel):
    """GET /api/notifications 응답."""
    items: list[NotificationItem] = []
    unread_count: int = 0


class NotificationSettingsResponse(BaseModel):
    """GET /api/notifications/settings 응답."""
    teams: bool = True
    in_app: bool = True
```

### 4-5. `app/models/analytics_schemas.py`

```python
"""분석 도메인 응답 스키마."""

from pydantic import BaseModel


# ── 하위 아이템 모델 ──

class FailureReasonItem(BaseModel):
    reason: str
    count: int
    percentage: float


class PositioningItem(BaseModel):
    positioning: str
    total: int
    won: int
    win_rate: float


class MonthlyTrendItem(BaseModel):
    month: str
    submitted: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float | None = None


class WinRateItem(BaseModel):
    period: str
    total: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float = 0.0


class TeamPerformanceItem(BaseModel):
    team_id: str
    total: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float = 0.0


class CompetitorItem(BaseModel):
    competitor: str
    encounters: int = 0
    won_against: int = 0
    lost_to: int = 0


class ClientWinRateItem(BaseModel):
    client: str
    total: int = 0
    won: int = 0
    win_rate: float = 0.0
    won_amount: int = 0


# ── 응답 모델 ──

class FailureReasonsResponse(BaseModel):
    period: str | None = None
    scope: str
    total_failed: int = 0
    reasons: list[FailureReasonItem] = []


class PositioningWinRateResponse(BaseModel):
    period: str | None = None
    scope: str
    positionings: list[PositioningItem] = []


class MonthlyTrendsResponse(BaseModel):
    scope: str
    from_date: str | None = None
    to_date: str | None = None
    data: list[MonthlyTrendItem] = []


class WinRateResponse(BaseModel):
    granularity: str
    scope: str
    data: list[WinRateItem] = []


class TeamPerformanceResponse(BaseModel):
    period: str | None = None
    scope: str
    teams: list[TeamPerformanceItem] = []


class CompetitorResponse(BaseModel):
    period: str | None = None
    scope: str
    competitors: list[CompetitorItem] = []


class ClientWinRateResponse(BaseModel):
    period: str | None = None
    scope: str
    clients: list[ClientWinRateItem] = []
```

### 4-6. `app/models/performance_schemas.py`

```python
"""성과 도메인 응답 스키마."""

from pydantic import BaseModel


class IndividualPerformance(BaseModel):
    """GET /api/performance/individual/{user_id} 응답."""
    user_id: str
    total_proposals: int = 0
    completed: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    avg_duration_days: float | None = None


class TeamQuarterPerformance(BaseModel):
    team_id: str
    quarters: list[dict] = []
    total_proposals: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    avg_tech_score: float | None = None


class DivisionTeamStat(BaseModel):
    team_id: str
    total: int = 0
    won: int = 0
    amount: int = 0
    win_rate: float = 0.0


class DivisionPerformance(BaseModel):
    """GET /api/performance/division/{div_id} 응답."""
    division_id: str
    total_proposals: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    teams: list[DivisionTeamStat] = []


class PositioningStat(BaseModel):
    total: int = 0
    won: int = 0
    win_rate: float = 0.0
    total_amount: int = 0


class CompanyPerformance(BaseModel):
    """GET /api/performance/company 응답."""
    by_positioning: dict[str, PositioningStat] = {}
    total_proposals: int = 0


class TrendItem(BaseModel):
    period: str
    submitted: int = 0
    won: int = 0
    lost: int = 0
    amount: int = 0


class PerformanceTrends(BaseModel):
    """GET /api/performance/trends 응답."""
    period: str  # monthly | quarterly | yearly
    data: list[TrendItem] = []


class MyProjectsDashboard(BaseModel):
    """GET /api/dashboard/my-projects 응답."""
    created: list[dict] = []
    participating: list[dict] = []


class TeamDashboard(BaseModel):
    """GET /api/dashboard/team 응답."""
    team_id: str
    proposals: list[dict] = []
    step_distribution: dict[str, int] = {}
    total: int = 0
```

### 4-7. `app/models/admin_schemas.py`

```python
"""관리자 도메인 응답 스키마."""

from pydantic import BaseModel


class UserStats(BaseModel):
    total: int = 0
    active: int = 0
    by_role: dict[str, int] = {}


class ProposalStats(BaseModel):
    total: int = 0
    by_status: dict[str, int] = {}


class SystemStatsResponse(BaseModel):
    """GET /api/admin/stats 응답."""
    users: UserStats = UserStats()
    proposals: ProposalStats = ProposalStats()


class RoleUpdateResponse(BaseModel):
    """PUT /api/admin/users/{user_id}/role 응답."""
    status: str = "ok"
    user_id: str
    role: str


class StatusUpdateResponse(BaseModel):
    """PUT /api/admin/users/{user_id}/status 응답."""
    status: str = "ok"
    user_id: str
    user_status: str


class DivisionTeamDashboardItem(BaseModel):
    team_id: str
    total: int = 0
    running: int = 0
    won: int = 0
    win_rate: float = 0.0
    total_amount: int = 0


class DivisionDashboardResponse(BaseModel):
    """GET /api/dashboard/division 응답."""
    division_id: str
    teams: dict[str, DivisionTeamDashboardItem] = {}
    pending_approvals: list[dict] = []


class MonthlyTrendItem(BaseModel):
    month: str
    submitted: int = 0
    won: int = 0
    amount: int = 0


class PositioningStat(BaseModel):
    won: int = 0
    total: int = 0
    win_rate: float = 0.0


class KpiSummary(BaseModel):
    total_proposals: int = 0
    running: int = 0
    won: int = 0
    decided: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0


class ExecutiveDashboardResponse(BaseModel):
    """GET /api/dashboard/executive 응답."""
    kpi: KpiSummary = KpiSummary()
    by_positioning: dict[str, PositioningStat] = {}
    monthly_trends: list[MonthlyTrendItem] = []


class VersionItem(BaseModel):
    checkpoint_id: str
    step: str
    next: list[str] = []
    has_sections: bool = False
    has_strategy: bool = False
    has_plan: bool = False


class ProposalVersionsResponse(BaseModel):
    """GET /api/proposals/{proposal_id}/versions 응답."""
    proposal_id: str
    versions: list[VersionItem] = []


class TimeTravelResponse(BaseModel):
    """GET /api/proposals/{proposal_id}/time-travel/{checkpoint_id} 응답."""
    proposal_id: str
    checkpoint_id: str
    current_step: str
    positioning: str | None = None
    mode: str | None = None
    has_rfp_analysis: bool = False
    has_go_no_go: bool = False
    has_strategy: bool = False
    has_plan: bool = False
    sections_count: int = 0
    slides_count: int = 0
    compliance_count: int = 0
    next_nodes: list[str] = []


class ReopenResponse(BaseModel):
    status: str = "ok"
    proposal_id: str
    new_status: str = "draft"
```

---

## 5. Phase C — 라우트 적용 패턴

### 5-1. 적용 전략

각 라우트 파일에서 다음 패턴으로 전환:

```python
# ── Pattern 1: dict 반환 → 모델 반환 ──

# Before
@router.get("")
async def list_proposals(...):
    ...
    return {"items": result.data or [], "total": len(result.data or [])}

# After
@router.get("", response_model=ItemsResponse[ProposalListItem])
async def list_proposals(...):
    ...
    items = [ProposalListItem(**row) for row in (result.data or [])]
    return ItemsResponse(items=items, total=len(items))


# ── Pattern 2: StatusResponse ──

# Before
return {"status": "ok"}

# After (response_model=StatusResponse)
return StatusResponse()


# ── Pattern 3: raw DB row ──

# Before
return res.data  # dict

# After (response_model=ProposalDetail)
return ProposalDetail(**res.data)


# ── Pattern 4: user dict → CurrentUser ──

# Before
async def some_route(user: dict = Depends(get_current_user)):
    team_id = user.get("team_id")

# After
async def some_route(user: CurrentUser = Depends(get_current_user)):
    team_id = user.team_id
```

### 5-2. 라우트별 적용 매핑

| 라우트 파일 | 엔드포인트 수 | response_model 적용 대상 | 스키마 파일 |
|-------------|-------------|------------------------|------------|
| `routes_proposal.py` | 4 | 4/4 | `proposal_schemas.py` + `common.py` |
| `routes_workflow.py` | 16 | 14/16 (SSE 제외) | `workflow_schemas.py` |
| `routes_artifacts.py` | 13 | 9/13 (바이너리 다운로드 제외) | `artifact_schemas.py` |
| `routes_notification.py` | 5 | 5/5 | `notification_schemas.py` |
| `routes_analytics.py` | 7 | 7/7 | `analytics_schemas.py` |
| `routes_performance.py` | 14 | 14/14 | `performance_schemas.py` + `common.py` |
| `routes_admin.py` | 12 | 11/12 (CSV 제외) | `admin_schemas.py` + `common.py` |
| `routes_auth.py` | 3 | 3/3 | `auth_schemas.py` |
| `routes_kb.py` | 34 | 20+/34 | `common.py` (ItemsResponse) |
| `routes_users.py` | 22 | 15+/22 | `user_schemas.py` + `common.py` |
| `routes_qa.py` | 5 | 5/5 | `schemas.py` (기존) |
| `routes_streams.py` | 3 | 3/3 | `stream_schemas.py` (기존, 이미 적용) |
| `routes_submission_docs.py` | 13 | 13/13 | `stream_schemas.py` (기존, 이미 적용) |
| **합계** | ~151 핵심 | ~123 적용 | |

**제외 대상 (Out-of-Scope):**
- `routes_v31.py` (레거시, 제거 예정)
- `routes_prompt_evolution.py` (내부 도구)
- 바이너리 다운로드 엔드포인트 (Response 객체 반환)
- SSE 스트리밍 엔드포인트 (StreamingResponse)

### 5-3. `CurrentUser` 전환 대상 파일

`user: dict = Depends(get_current_user)` 패턴 사용 파일 전수:

| 파일 | `user["key"]` 횟수 (예상) |
|------|-------------------------|
| `routes_proposal.py` | ~5 |
| `routes_workflow.py` | ~8 |
| `routes_artifacts.py` | ~6 |
| `routes_notification.py` | ~3 |
| `routes_admin.py` | ~4 |
| `routes_performance.py` | ~10 |
| `routes_kb.py` | ~8 |
| `routes_users.py` | ~6 |
| `routes_calendar.py` | ~3 |
| `routes_bids.py` | ~5 |
| `routes_team.py` | ~10 |
| `routes_bid_submission.py` | ~3 |
| `routes_streams.py` | ~2 |
| `routes_submission_docs.py` | ~4 |
| `routes_qa.py` | ~3 |
| `deps.py` (내부) | ~8 |
| **합계** | ~88 |

모든 `user["X"]` → `user.X`, `user.get("X")` → `user.X` 전환.

---

## 6. 마이그레이션 안전 체크리스트

### Phase A 완료 검증
- [ ] `uv run python -c "from app.models.common import StatusResponse, ItemsResponse, PaginatedResponse"` 성공
- [ ] `uv run python -c "from app.models.auth_schemas import CurrentUser"` 성공
- [ ] `uv run python -c "from app.models.types import UserRole, ProposalStatus"` 성공
- [ ] `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` 기동 성공
- [ ] `grep -rn 'user\["' app/api/ app/services/` 결과 0건

### Phase B 완료 검증
- [ ] 모든 신규 스키마 파일 import 성공
- [ ] `uv run pytest` 기존 테스트 통과

### Phase C 완료 검증
- [ ] `/docs` OpenAPI에서 핵심 엔드포인트 응답 스키마 표시
- [ ] `grep -rn 'return {' app/api/routes_proposal.py app/api/routes_workflow.py app/api/routes_artifacts.py` 결과 0건
- [ ] 프론트엔드 `npm run build` 에러 0건

---

## 7. 영향 범위 요약

| 구분 | 파일 수 | 변경 유형 |
|------|---------|----------|
| 신규 스키마 | 10 | `common.py`, `types.py`, `auth_schemas.py`, `proposal_schemas.py`, `workflow_schemas.py`, `artifact_schemas.py`, `notification_schemas.py`, `analytics_schemas.py`, `performance_schemas.py`, `admin_schemas.py` |
| 수정 스키마 | 4 | `schemas.py`, `user_schemas.py`, `bid_schemas.py`, `phase_schemas.py` |
| 수정 deps | 1 | `deps.py` |
| 수정 라우트 | ~15 | `routes_proposal.py` ~ `routes_qa.py` (핵심 라우트) |
| 수정 pricing | 1 | `bidding/pricing/models.py` (datetime 통일) |
| **총 변경 파일** | **~31** | |
